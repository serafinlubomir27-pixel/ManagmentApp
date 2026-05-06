# 👔 Fáza 3 — Klientský modul (Finanční poradcovia)

#klienti #mifid #fintech #pipeline #compliance #faza3

## Problém

ManagmentApp v2.0 neriešil klientsky orientované pracovné postupy pre finančných poradcov a maklérov:
- Žiadny register klientov
- Žiadna MiFID II / AML compliance kontrola
- Žiadne sledovanie obchodného pipline
- Žiadne logy stretnutí s klientmi

## Riešenie

`Client` je **prvotriedna entita** (vlastná DB tabuľka), nie len tag na projekte. Jeden klient môže mať viacero projektov (onboarding, ročný review, nový produkt...).

---

## Dátový model

```sql
CREATE TABLE clients (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  email        TEXT,
  phone        TEXT,
  category     TEXT DEFAULT 'retail',
    -- 'retail' | 'professional' | 'eligible_counterparty'
  risk_profile TEXT DEFAULT 'balanced',
    -- 'conservative' | 'balanced' | 'dynamic'
  advisor_id   INTEGER REFERENCES users(id),
  notes        TEXT,
  archived     INTEGER DEFAULT 0,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Projekty linkované ku klientovi
ALTER TABLE projects ADD COLUMN client_id INTEGER REFERENCES clients(id)

CREATE TABLE client_meetings (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id    INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  user_id      INTEGER NOT NULL REFERENCES users(id),
  meeting_date TEXT NOT NULL,
  notes        TEXT,
  follow_ups   TEXT,  -- JSON pole stringov (follow-up akcie)
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

CREATE TABLE compliance_items (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id      INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  item_type      TEXT NOT NULL,
    -- 'kyc' | 'suitability' | 'aml' | 'id_document' | 'risk_questionnaire' | 'contract'
  status         TEXT DEFAULT 'pending',
    -- 'pending' | 'complete' | 'expired'
  due_date       TEXT,
  completed_by   INTEGER REFERENCES users(id),
  completed_at   TIMESTAMP,
  document_path  TEXT
)

CREATE TABLE deal_stages (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id           INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  stage               TEXT DEFAULT 'lead',
    -- 'lead'|'contact'|'analysis'|'proposal'|'signed'|'active'|'lost'
  deal_value          REAL,
  commission_expected REAL,
  commission_received REAL,
  currency            TEXT DEFAULT 'EUR',
  notes               TEXT,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## API (clients_router.py)

| Metóda | Endpoint | Popis | Prístup |
|--------|----------|-------|---------|
| GET | `/clients` | Zoznam klientov | manager = všetci; employee = vlastní |
| POST | `/clients` | Vytvorenie klienta | manager+ |
| GET | `/clients/{id}` | Detail + linkované projekty | — |
| PATCH | `/clients/{id}` | Aktualizácia | manager+ |
| DELETE | `/clients/{id}` | Soft delete (archived=1) | manager+ |
| GET | `/clients/{id}/meetings` | Log stretnutí | — |
| POST | `/clients/{id}/meetings` | Zápis stretnutia | — |
| DELETE | `/clients/{id}/meetings/{mid}` | Zmazanie stretnutia | vlastník |
| GET | `/clients/{id}/compliance` | Compliance checklist | — |
| POST | `/clients/{id}/compliance` | Pridanie položky | — |
| PATCH | `/compliance-items/{id}` | Označenie ako complete | — |
| GET | `/clients/{id}/pipeline` | Deal stage info | — |
| PATCH | `/clients/{id}/pipeline` | Update stage + hodnoty | — |
| GET | `/clients/pipeline/all` | Všetky dealy (advisor pohľad) | — |
| POST | `/clients/{id}/link-project` | Priradenie projektu | manager+ |

> ⚠️ `/clients/pipeline/all` musí byť definovaný **pred** `/{client_id}` — inak FastAPI routuje "all" ako `client_id`.

---

## Frontend

### ClientsPage (`/clients`)

- Tabuľka klientov: meno, kategória (badge), risk profil, poradca, počet projektov, fáza dealu
- Filter podľa poradcu, kategórie, fázy
- Vytvorenie nového klienta (formulár, len manažér)
- Nav link v sidebar: `Klienti` (ikona Users)

### ClientDetailPage (`/clients/:id`)

**4 záložky:**

| Záložka | Obsah |
|---------|-------|
| Projekty | Zoznam linkovaných projektov + tlačidlo "Priradiť projekt" |
| Pipeline | `PipelineKanban` — 7-fázový selector s finančnými poliami |
| Stretnutia | `MeetingLog` — chronologický zoznam + formulár |
| Compliance | `ComplianceChecklist` — MiFID II položky so statusom |

### PipelineKanban.tsx

7 fáz dealu (horizontálny selector):
```
Lead → Prvý kontakt → Analýza → Návrh → Podpis → Aktívny → Stratený
```
- Finančné polia: `Hodnota dealu`, `Plánovaná provízia`, `Prijatá provízia`
- Uloženie pri `onBlur` (nie pri každom stlačení klávesu)
- Checkmark na dokončených fázach

### ComplianceChecklist.tsx

Predefinované typy položiek (MiFID II / IDD / AML):
- KYC (Know Your Customer)
- Suitability Assessment
- AML (Anti-Money Laundering)
- ID dokument
- Rizikový dotazník
- Zmluva

Status systém:
- 🟡 **Pending** — čaká na dokončenie
- ✅ **Complete** — dokončené (s dátumom a zodpovednou osobou)
- 🔴 **Expired** — status `pending` + `due_date` < dnešok

### MeetingLog.tsx

- Chronologický zoznam stretnutí (najnovšie hore)
- Follow-up akcie uložené ako JSON pole v DB, parsované s try/catch
- Zmazať môže len autor stretnutia
- Formulár: dátum, poznámky, follow-up akcie (textarea)

---

## MiFID II kontext

**MiFID II** (Markets in Financial Instruments Directive II) je európska regulácia pre finančné trhy. Pre poradcov vyžaduje:

| Požiadavka | Riešenie v Nodus |
|-----------|-----------------|
| Kategorizácia klienta (retail/profesionálny) | `category` pole v `clients` tabuľke |
| Suitability assessment | Compliance item `risk_questionnaire` |
| KYC dokumentácia | Compliance item `kyc` + `id_document` |
| AML kontrola | Compliance item `aml` |
| Audit trail | `completed_by` + `completed_at` v `compliance_items` |
| Rizikový profil | `risk_profile` pole (conservative/balanced/dynamic) |

---

## Súvisiace

- [[00 - Prehľad projektu]]
- [[12 - v2.0 Web Aplikácia]]
- [[13 - Prílohy & Sieťový Diagram]]
- [[03 - Databáza & Repo]]
