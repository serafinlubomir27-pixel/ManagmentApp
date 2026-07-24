# Nodus

**Projektový manažment na kritickej ceste.** Multi-tenant SaaS s matematickým jadrom —
CPM (Critical Path Method) a PERT — ktoré väčšina cenovo dostupných nástrojov (Trello,
ClickUp, Asana, Monday) neponúka.

Backend: FastAPI + PostgreSQL (Supabase) / SQLite. Frontend: React + Vite + TypeScript + Tailwind (PWA).

---

## Funkcie

- **CPM engine** — kritická cesta, ES/EF/LS/LF, celková rezerva (float), detekcia cyklov, health score
- **PERT** — pravdepodobnostné plánovanie (trojbodový odhad, pravdepodobnosť splnenia termínu)
- **Vizualizácie** — Gantt, interaktívny sieťový diagram, resource management (over-allocation)
- **Multi-tenancy** — izolácia dát medzi organizáciami; self-signup, pozvánky, reset hesla
- **Plány** — free / starter / team / enterprise s vynútenými limitmi
- **Ďalšie** — komentáre, prílohy s viditeľnosťou, kalendár (iCal feed), notifikácie,
  AI parser (popis projektu → úlohy), klientsky modul pre finančných poradcov (MiFID II)

## Architektúra

Striktné vrstvy — prezentácia → business logika → repozitáre → DB:

```
backend/     FastAPI app, routery, JWT auth, rate limiting
  deps.py    object-level + org autorizácia (choke point)
logic/       čistá business logika (cpm_engine, pert_engine, plans, mailer, passwords…)
repositories/ len SQL; dual backend SQLite/PostgreSQL (base_repo.py)
database/    setup.py (SQLite) + migrations/*.sql (PostgreSQL)
frontend/    React + Vite + Tailwind PWA
tests/       pytest (117 testov)
```

## Lokálny vývoj

**Backend** (Python 3.11+):

```bash
pip install -r requirements.txt
export APP_AUTH_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
python -m uvicorn backend.main:app --reload   # http://127.0.0.1:8000  (Swagger: /docs)
```

SQLite sa vytvorí automaticky pri štarte (`DB_BACKEND=sqlite`, default) vrátane lokálneho
admina (`admin` / `admin123` — **len dev**). Konfigurácia cez `.env` (viď `.env.example`).

**Frontend** (Node 18+):

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxy /api → :8000)
```

**Testy:**

```bash
python -m pytest -q          # backend
cd frontend && npx tsc --noEmit   # frontend typecheck
```

## Nasadenie (Supabase + Railway)

1. **Supabase — spusti migrácie v SQL Editore V PORADÍ:**
   `supabase_schema.sql` → `migrations/002…008` (005 = RLS, 006 = chýbajúce tabuľky,
   007 = multi-tenancy, 008 = e-mail + reset). Migrácie sú idempotentné.
2. **Railway (backend)** — nastav premenné prostredia:
   - `DB_BACKEND=postgres`, `DATABASE_URL=…` (Supabase connection string)
   - `APP_AUTH_KEY` — **povinné** (min. 32 náhodných znakov; bez neho sa app zámerne nespustí)
   - `CORS_ORIGINS` — URL frontendu
   - `RESEND_API_KEY`, `MAIL_FROM`, `APP_BASE_URL` — pre e-maily (voliteľné; bez nich sa e-maily preskočia)
3. **Prvý admin** (default admin z prod schémy bol odstránený):
   ```bash
   ADMIN_USERNAME=admin ADMIN_PASSWORD='silne-heslo' python scripts/create_admin.py
   ```
   (Alebo jednoducho použi verejný self-signup na `/signup`.)
4. **Frontend** — build (`npm run build`) a nasaď `dist/` (Surge / Netlify / Vercel).
   Nastav `VITE_API_URL` na URL backendu.

## Konfigurácia (kľúčové env premenné)

| Premenná | Účel |
|---|---|
| `DB_BACKEND` | `sqlite` (default) alebo `postgres` |
| `DATABASE_URL` | PostgreSQL/Supabase connection string |
| `APP_AUTH_KEY` | JWT podpisový kľúč — povinný v produkcii |
| `RATE_LIMIT_ENABLED` | `0` vypne rate limiting (default zapnuté) |
| `RESEND_API_KEY` | e-maily cez Resend (bez neho no-op) |

## Licencia

Proprietárne. © Ľubomír Serafín.
