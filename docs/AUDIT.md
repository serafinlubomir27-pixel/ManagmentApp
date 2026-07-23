# Nodus (ManagmentApp) — Audit kódu

**Dátum:** 2026-07-22
**Rozsah:** celý backend (FastAPI + repozitáre + logika), frontend (React), DB schémy (SQLite + Postgres/Supabase)
**Cieľ:** čo treba dokončiť a opraviť, aby bola platforma **plne funkčná a konkurencieschopná** (a bezpečne nasaditeľná).

---

## Zhrnutie (verdikt)

Jadro projektu je **reálne solídne** — čistá vrstvová architektúra, otestovaný CPM/PERT engine (64/64 unit testov prechádza), pekná šírka funkcií, nasadené na Surge + Railway + Supabase. **Nie je to vaporware.**

ALE medzi tým, čo bakalárka označuje ✅, a „plne funkčná a bezpečná platforma" je **vážna priepasť v dvoch oblastiach**:

1. **Bezpečnosť / autorizácia** — takmer žiadny endpoint nekontroluje *vlastníctvo* dát. Ktokoľvek prihlásený vie čítať/meniť cudzie projekty, úlohy a **citlivé klientske dáta (MiFID II, provízie, PII)** len uhádnutím ID. Navyše verejná registrácia dovoľuje stať sa adminom.
2. **Nasadenie / úplnosť** — produkčná Postgres schéma **nemá 7 tabuliek**, ktoré má SQLite. Celý klientský modul (Fáza 3), prílohy projektov (Fáza 1), time tracking a pozvánky sú na Supabase **rozbité** (chýbajúce tabuľky), aj keď lokálne bežia.

Poradie riešenia: **P0 (kritické) → P1 (vysoké) → P2 (lesk/konkurencieschopnosť)**.

> **Stav opráv (2026-07-23):** Fáza 0 — autorizačný balík **hotový v kóde** (P0-1 ✅, P0-2 ✅, P0-3 ✅ migrácia napísaná). Pridaných 15 authz regresných testov (`tests/test_authz.py`), celá sada **79/79 prechádza**. **Zostáva manuálny krok:** spustiť `database/migrations/005_enable_rls.sql` v Supabase SQL Editore. Ďalej: P0-4 (chýbajúce prod tabuľky), P0-5/6/7 (hardening).

---

## Čo funguje dobre (zachovať) ✅

- **Architektúra**: striktná separácia UI → logika → repozitáre → DB. Repository Pattern reálne umožňuje dual backend.
- **CPM engine** (`logic/cpm_engine.py`) — čistý, bez závislostí, 34 testov. Detekcia cyklov, Kahn topo-sort, forward/backward pass, float, health score.
- **PERT engine** (`logic/pert_engine.py`) — pravdepodobnostné plánovanie cez `NormalDist`.
- **Dual DB backend** (`repositories/base_repo.py`) — abstrakcia SQLite/Postgres funguje.
- **Šírka funkcií**: projekty, úlohy, tím, kalendár (iCal feed), notifikácie, prílohy s viditeľnosťou, AI parser, resource management, klientsky modul.

---

## P0 — Kritické (blokery nasadenia s reálnymi dátami)

| # | Nález | Súbor | Dopad |
|---|-------|-------|-------|
| P0-1 | Verejná registrácia s ľubovoľnou rolou → okamžitý admin | `backend/routers/auth_router.py:59` | Privilege escalation |
| P0-2 | Chýba kontrola vlastníctva (BOLA/IDOR) naprieč endpointmi | viď nižšie | Únik/zmena cudzích dát |
| P0-3 | Žiadne RLS na Supabase + anon key vo frontende | `database/supabase_schema.sql` | Priamy bypass backendu |
| P0-4 | Produkčná Postgres schéma nemá 7 tabuliek | `database/supabase_schema.sql` | Fázy 1–3 rozbité v prode |
| P0-5 | Heslá = holé SHA-256 bez soli | `repositories/user_repo.py:9` | Rainbow-table útok |
| P0-6 | Hardcoded fallback JWT secret | `backend/auth.py:11` | Falšovateľné tokeny |
| P0-7 | Default účet admin / admin123 | `database/setup.py`, `supabase_schema.sql` | Známe prihlásenie |

### P0-1 — Verejná registrácia = admin takeover
`POST /auth/register` je **neautentifikovaný** a dôveruje poľu `role` z tela requestu (default `employee`, ale nič nebráni poslať `role: "admin"`).
```python
# auth_router.py:59
@router.post("/register", ...)
def register(req: RegisterRequest):   # RegisterRequest.role: str = "employee"
    ...
    user_repo.create_user(req.username, hashed, req.full_name, req.role, ...)  # rola bez validácie
```
**Fix:** buď zrušiť verejnú registráciu úplne (onboarding len cez `/invites/{token}/accept`, ktorý rolu berie z pozvánky — to je urobené správne), alebo natvrdo `role="employee"` na serveri a ignorovať vstup.

### P0-2 — Broken Object-Level Authorization (IDOR) — systémové
Endpointy overujú len *existenciu* objektu (`_or_404`), nie že patrí prihlásenému používateľovi. `list_*` sú väčšinou správne scopované cez `current_user["id"]`, ale prístup **priamo cez ID** nie je. Postihnuté:

- **Projekty**: `GET/PATCH /projects/{id}` — `projects_router.py:52`, `:64`
- **Úlohy**: `GET/PATCH/DELETE /tasks/{id}`, `GET /projects/{id}/tasks`, dependencies, `GET /projects/{id}/pert|risk-score|resources|time-summary` — `tasks_router.py:49` (`_project_or_404` len existencia), `:108`, `:120`, `:150`
- **Komentáre**: `GET/POST /tasks/{id}/comments` — `comments_router.py:22`
- **Prílohy**: `POST/GET /projects/{id}/attachments`, `/tasks/{id}/attachments` — `attachments_router.py:46`, `:69`
- **Klienti (NAJCITLIVEJŠIE — financie + PII + MiFID II)**: `GET/PATCH /clients/{id}`, meetings, compliance, pipeline — `clients_router.py:65` (`_client_or_404` len existencia), `:108`, `:116`. `PATCH /clients/compliance/{item_id}` (`:213`) nemá **žiadnu** väzbu na klienta/vlastníka.
- **Tím**: `GET /team/{user_id}/workload` — `team_router.py:38` (ktokoľvek vidí vyťaženie kohokoľvek).

**Fix:** centrálny helper autorizácie, napr. `deps.py`:
```python
def assert_project_access(user, project_id):  # owner OR assignee OR admin
    ...
def assert_client_access(user, client_id):     # advisor_id == user OR manager/admin
    ...
```
a aplikovať ako dependency na každý endpoint s `{id}`. Model vlastníctva už existuje: projekt má `user_id` (owner) + viditeľnosť cez `tasks.assigned_to` (viď `project_repo.get_user_projects`).

### P0-3 — Žiadne RLS + anon key vo frontende = bypass backendu
`database/supabase_schema.sql` **neobsahuje žiadne RLS policies** (potvrdené). Frontend zároveň nesie `VITE_SUPABASE_ANON_KEY` a hovorí so Supabase priamo (Realtime — `frontend/src/lib/supabase.ts`, `hooks/useRealtimeProject.ts`). Ak sú tabuľky bez RLS, **anon key vie cez Supabase PostgREST/Realtime čítať a zapisovať do VŠETKÝCH tabuliek priamo**, úplne mimo FastAPI autorizácie. Kým toto platí, opravy P0-2 nič neriešia pre klienta, ktorý ide priamo na Supabase.
**Fix:** zapnúť RLS na všetkých tabuľkách + policies (alebo Realtime obmedziť a anon key nepoužívať na dátový prístup). Toto treba spraviť **súčasne** s P0-2.

### P0-4 — Produkčná schéma nemá 7 tabuliek → Fázy 1–3 rozbité v prode
`supabase_schema.sql` + migrácie definujú len: `users, projects, tasks, task_dependencies, task_comments, task_attachments, activity_logs, comments, notifications, calendar_tokens`.
SQLite `setup.py` navyše vytvára: **`time_logs, invite_tokens, project_attachments, clients, client_meetings, compliance_items, deal_stages`** — tie v Postgres schéme ani v žiadnej migrácii **nie sú**.
Keďže prod beží na Supabase (Postgres), tieto features hádžu „relation does not exist": pozvánky, time tracking, prílohy projektov a **celý klientsky modul (Fáza 3)**.
**Fix:** dopísať Postgres migrácie (`005_*.sql` …) pre všetkých 7 tabuliek so správnymi FK/ENUM/indexmi, spustiť na Supabase.

### P0-5 — Slabé hashovanie hesiel
`hashlib.sha256(password)` bez soli (`user_repo.py:9`, aj v `auth_router` register/change-password). Zraniteľné na rainbow tables, rýchle na bruteforce.
**Fix:** `passlib` s `bcrypt` alebo `argon2`. Migrácia: pri najbližšom úspešnom logine re-hashnúť (viď existujúci plaintext→sha256 upgrade v `setup.py` ako vzor).

### P0-6 — Hardcoded fallback JWT secret
```python
# backend/auth.py:11
SECRET_KEY = os.environ.get("APP_AUTH_KEY") or "change-me-in-production-use-32-chars!"
```
Ak `APP_AUTH_KEY` na Railway nie je nastavený, tokeny sú falšovateľné ktokoľvek, kto pozná default.
**Fix:** fail-fast — ak `DB_BACKEND=postgres` (prod) a `APP_AUTH_KEY` chýba, vyhoď výnimku pri štarte.

### P0-7 — Default admin/admin123
Seed účet v schéme aj `setup.py`.
**Fix:** vynútiť zmenu hesla pri prvom logine, alebo generovať náhodné heslo a vypísať do logu len raz.

---

## P1 — Vysoké (korektnosť, robustnosť, chýbajúce funkcie)

- **P1-1 — Rate limiting na `/auth/login`** chýba → bruteforce. Pridať `slowapi` alebo obdobu.
- **P1-2 — `/notifications/check-deadlines`** je volateľný **hocijakým** používateľom a skenuje **všetky** úlohy globálne (`notifications_router.py:48`). Malo by byť naplánované (cron / Supabase Edge Function) alebo admin-only.
- **P1-3 — E-mailové notifikácie** (bakalárka „budúca práca v3.x") nie sú implementované. Pre konkurencieschopnosť dôležité.
- **P1-4 — `update_project` je neúplný CRUD** — `PATCH /projects/{id}` ignoruje `name`/`description`, mení len `status` (`projects_router.py:74`). Chýba aj `DELETE /projects/{id}`.
- **P1-5 — AI parser**: bez `OPENAI_API_KEY` ticho spadne na slabú heuristiku (`logic/ai_parser.py`). Používa externý GPT-4o-mini. Zvážiť: (a) jasne komunikovať zdroj vo frontende, (b) `max_tasks` sa neaplikuje v `/ai-generate` (len v dry-run), (c) možnosť použiť Claude ako alternatívu.
- **P1-6 — iCal DTEND bug**: `_build_ical` počíta „next day" pre due dni ≥28 nesprávne (skočí na 1. nasledujúceho mesiaca) — `calendar_router.py:61`. Nahradiť `due_dt + timedelta(days=1)`.
- **P1-7 — Tiché `except: pass`** okolo CPM prepočtov (`tasks_router.py` viackrát) skrýva reálne chyby. Aspoň logovať.
- **P1-8 — Krehký SQL preklad** v `_PgCursorWrapper.execute` (`base_repo.py:55`): slepé `sql.replace("?", "%s")` pokazí každý literálny `?`/`%` v hodnotách/`LIKE`. `RETURNING id` auto-append predpokladá stĺpec `id` v každej tabuľke.
- **P1-9 — Duplicitné comment tabuľky**: `task_comments` (legacy) aj `comments` (nová) existujú súčasne — tech-debt, riziko nekonzistencie.
- **P1-10 — Token v `localStorage`** (`api/client.ts:12`, `AuthContext.tsx`) → čitateľný XSS-om. Zvážiť httpOnly cookie + CSRF, alebo aspoň prísne CSP a audit XSS sinkov.

---

## P2 — Stredné (lesk, testy, konkurencieschopnosť)

- **Testy len pre CPM + staré SQLite repo** (64). **Žiadne** integračné/authz testy pre FastAPI vrstvu — pridať `pytest` + `httpx.AsyncClient`, hlavne regresné testy na IDOR.
- **Žiadne CI** (GitHub Actions) — pridať lint + testy na push.
- **Žiadny root `README.md`** (len HTML bakalárka) — pridať pre GitHub prezentáciu.
- **Bez pagination/limitov** na list endpointoch, bez observability (len `print`), bez error trackingu (Sentry).
- **Konkurencieschopnosť**: mobilná responzivita, onboarding flow, landing page, integrácie (Slack/GitHub/Teams), i18n (SK/EN prepínač), accessibility.
- **Verzný drift**: bakalárka uvádza React 19, `package.json` má React 18.3.1 — kozmetika, ale zosúladiť s realitou.

---

## Odporúčaná Fáza 0 (poradie opráv)

1. **Sekvenčný balík autorizácie** (P0-1, P0-2, P0-3) — spraviť **naraz**, lebo sa dopĺňajú: zrušiť/uzavrieť register → centrálny `assert_*_access` na všetky endpointy → zapnúť RLS na Supabase. Bez všetkých troch nie je dátový model chránený.
2. **Doplniť produkčnú schému** (P0-4) — migrácie pre 7 chýbajúcich tabuliek, over na Supabase, že Fázy 1–3 reálne bežia.
3. **Hardening prihlasovania** (P0-5, P0-6, P0-7) — bcrypt + migrácia, JWT fail-fast, preč s default heslom.
4. **Regresné authz testy** (P2) — aby sa IDOR už nevrátil.

Až po Fáze 0 má zmysel ísť na dokončenie funkcií (e-mail notifikácie, AI, CRUD medzery) a potom na konkurenčný lesk.

---

*Poznámka k tajomstvám: `.env` a `*.db` sú správne v `.gitignore`; v repozitári nie sú commitnuté žiadne reálne kľúče (len placeholdery v `.env.example` a docs). ✅*
