# 🚀 Roadmap v2.0

#roadmap #v2 #cloud #saas

## Vízia

v1.0 = solidný **desktop MVP** pre freelancerov a malé tímy.
v2.0 = **cloud/SaaS** pre korporácie — PostgreSQL, REST API, web frontend.

---

## PostgreSQL / Supabase ✅

[[01 - Architektúra#Repository Pattern|Repository Pattern]] bol navrhnutý práve pre túto migráciu.

### Implementované (v1.2)

Detaily: [[11 - Supabase Migrácia]]

```
✅ base_repo.py — duálny backend (SQLite / PostgreSQL)
✅ _PgCursorWrapper — ? → %s, RETURNING id auto-append, dict rows
✅ database/supabase_schema.sql — ENUM typy, 7 tabuliek, 10 indexov
✅ database/migrate_to_supabase.py — jednorazová migrácia dát
✅ .env.example — DB_BACKEND, DATABASE_URL dokumentácia
✅ requirements.txt — psycopg2-binary, python-dotenv
✅ 64 unit testov stále prechádza
```

### Zostáva

- Vytvoriť Supabase projekt a spustiť schema (manuálny krok užívateľa)
- Row Level Security (RLS) pre multi-tenant použitie

### Supabase výhody

- PostgreSQL (production-grade)
- Vstavaná autentifikácia
- Row Level Security
- REST API zadarmo
- Real-time subscriptions (notifications!)

---

## REST API / Backend

```
FastAPI backend:
├── /auth          ← login, register, JWT
├── /projects      ← CRUD projektov
├── /tasks         ← CRUD úloh + CPM trigger
├── /dependencies  ← správa závislostí
├── /team          ← hierarchia, workload
└── /reports       ← export PDF/Excel
```

[[02 - CPM Engine|CPM Engine]] (`cpm_engine.py`) je **čistý Python bez závislostí** → môže bežať priamo na backendu.

---

## Web Frontend

Možnosti:
- **React + TypeScript** (ako pôvodný PathFlow/Lovable)
- **Next.js** — SSR pre lepší SEO a performance

Inspirácia z `lovable projekt/` — PathFlow komponenty.

---

## Team Features

Rozšírenia [[06 - Team Management|Team Management]]:

| Feature | Popis |
|---------|-------|
| Rekurzívna hierarchia | Admin vidí celý strom, nie len priamych |
| Notifikácie | E-mail / push keď je priradená úloha |
| Kapacitné plánovanie | Koľko % má kto obsadených |
| Kalendárna integrácia | Google Calendar / Outlook sync |

---

## Reporting & Export

- Export Gantt chartu do **PDF/PNG**
- Export task listu do **Excel**
- Automatické reporty manažérovi (weekly summary)
- Dashboard s KPI metrikami

---

## Ďalšie features

### Šablóny projektov
✅ **Implementované v v1.0** — `FromTemplateDialog`, `NewProjectDialog`, menu ⚙️ na kartách projektov.

### Časové sledovanie
- Stopky na úlohe (`estimated_hours` vs `actual_hours`)
- Reporty skutočného vs odhadovaného času

### Notifikácie
- Deadline upozornenia (D-3, D-1)
- Upozornenie keď dependency je dokončená

### Multi-project dashboard
- Prehľad všetkých projektov naraz
- Portfólio health score

---

## Technické dlhy v1.0 → v1.1

| Problém | Priorita | Stav |
|---------|----------|------|
| Admin vidí len priamych podriadených (nie celý strom) | Stredná | ✅ `get_full_tree()` — BFS rekurzia, toggle v TeamView |
| Žiadne unit testy | Vysoká | ✅ 64 testov — `tests/test_cpm_engine.py` + `tests/test_repositories.py` |
| matplotlib charts nie sú interaktívne (hover/click) | Nízka | 🔜 |
| Gantt nepodporuje scroll pre veľké projekty | Stredná | ✅ `tk.Canvas` viewport + CTkScrollbar (>12 úloh alebo >18" šírka) |
| Vyhľadávanie úloh v Task liste | Stredná | ✅ Live search entry — podľa názvu, assignee, kategórie |
| Notifikácie pri blížiacich sa deadlinoch | Stredná | ✅ Deadline banner na dashboarde (D-3, D-1, overdue) |
| Import/Export úloh cez CSV | Nízka | ✅ `export_tasks_csv()` + `import_tasks_csv()` v export_manager.py |

### Čo bolo vyriešené v priebehu v1.0

| Bug / Tech dlh | Riešenie |
|----------------|----------|
| `self._canvas` konflikt s CTkFrame | `_mpl_canvas` + `destroy()` override → [[07 - Bugy & Opravy#matplotlib canvas conflict]] |
| `#RRGGBBAA` farby v Tkinter | `color_blend()` funkcia v `theme.py` |
| `user_data[0]` dict/tuple | `isinstance()` defensive pattern |
| `border_color="transparent"` | Podmienečné nastavenie cez `**kwargs` |

---

## Súvisiace

- [[00 - Prehľad projektu]]
- [[01 - Architektúra]]
- [[02 - CPM Engine]]
- [[03 - Databáza & Repo]]
