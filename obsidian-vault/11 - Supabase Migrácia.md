# ☁️ Supabase Migrácia (v1.2)

#supabase #postgresql #cloud #migrácia #backend

Implementácia duálneho databázového backendu — lokálny SQLite aj Supabase PostgreSQL cez rovnaké repozitáre.

---

## Architektúra

```
DB_BACKEND=sqlite   →  _SqliteConnectionWrapper  →  sqlite3 (lokálny súbor)
DB_BACKEND=postgres →  _PgConnectionWrapper      →  psycopg2 → Supabase
```

Všetky repozitáre volajú `get_connection()` z `base_repo.py` — nepoznajú konkrétny backend.

---

## Súbory

| Súbor | Čo robí |
|-------|---------|
| `repositories/base_repo.py` | Duálny backend engine |
| `database/supabase_schema.sql` | PostgreSQL schema (ENUMy, tabuľky, indexy, seed) |
| `database/migrate_to_supabase.py` | Jednorazová migrácia dát SQLite → Supabase |
| `.env.example` | Šablóna pre `.env` konfiguráciu |

---

## Konfigurácia

1. Skopírovať `.env.example` → `.env`
2. Nastaviť `DB_BACKEND=postgres`
3. Nastaviť `DATABASE_URL=postgresql://postgres.[ref]:[pwd]@[host]:6543/postgres`

Supabase URL nájdeš v: **Settings → Database → Connection string → URI (Transaction mode)**

---

## base_repo.py — kľúčové časti

### Placeholder preklad

```python
# _PgCursorWrapper.execute():
pg_sql = sql.replace("?", "%s")   # SQLite → psycopg2 syntax
```

### Auto-RETURNING id

```python
# Pre INSERT bez RETURNING — wrapper automaticky pridá RETURNING id
if stripped_upper.startswith("INSERT") and "RETURNING" not in stripped_upper:
    pg_sql = pg_sql.rstrip(";") + " RETURNING id"
# Po execute uloží id do self._last_id
if self._columns == ["id"]:
    row = self._cur.fetchone()
    self._last_id = row[0] if row else None
```

Vďaka tomu repozitáre môžu volať `cursor.lastrowid` rovnako ako pri SQLite — bez zmeny kódu.

### Row factory

```python
# fetchone() / fetchall() vracajú dict — rovnako ako sqlite3.Row
def fetchone(self):
    row = self._cur.fetchone()
    return dict(zip(self._columns, row)) if row else None
```

---

## PostgreSQL Schema

**Súbor:** `database/supabase_schema.sql`

### ENUM typy

```sql
CREATE TYPE user_role    AS ENUM ('admin', 'manager', 'employee');
CREATE TYPE project_status AS ENUM ('active', 'completed', 'archived');
CREATE TYPE task_status  AS ENUM ('pending', 'in_progress', 'completed', 'blocked');
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE dep_type     AS ENUM ('finish_to_start', 'start_to_start', 'finish_to_finish');
```

### Tabuľky (7)

`users` → `projects` → `tasks` → `task_dependencies` → `task_comments` → `task_attachments` → `activity_logs`

### Seed

```sql
INSERT INTO users (username, password, full_name, role)
VALUES ('admin', '240be518...', 'Hlavný Admin', 'admin')
ON CONFLICT (username) DO NOTHING;
```

SHA-256("admin123") = `240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a`

---

## Migrácia dát

```bash
# 1. Nastav .env s DATABASE_URL (postgres)
# 2. Spusti:
py database/migrate_to_supabase.py
```

Skript kopíruje tabuľky v poradí závislostí (foreign keys), používa `ON CONFLICT DO NOTHING` — bezpečné opakovanie.

---

## Kompatibilita — opravené rozdiely

| Problém | SQLite | PostgreSQL | Riešenie |
|---------|--------|------------|----------|
| Placeholder | `?` | `%s` | Auto-replace v `_PgCursorWrapper` |
| INSERT lastrowid | `cursor.lastrowid` | `RETURNING id` | Auto-append v wrapper |
| Boolean hodnoty | `1` / `0` | `TRUE` / `FALSE` | `bool(is_template)`, `is_template = TRUE` |
| Row factory | `sqlite3.Row` | tuple | Dict wrapper v oboch |

---

## Inštalácia závislostí

```bash
pip install psycopg2-binary python-dotenv
# alebo:
pip install -r requirements.txt
```

`requirements.txt` aktualizovaný o:
- `psycopg2-binary>=2.9.0`
- `python-dotenv>=1.0.0`

**Poznámka:** `supabase` SDK (Python) bol vynechaný — vyžaduje `pyiceberg` s Microsoft Visual C++ 14.0. `psycopg2-binary` je dostatočný pre všetky operácie.

---

## Súvisiace

- [[03 - Databáza & Repo]]
- [[01 - Architektúra]]
- [[08 - Roadmap v2.0]]
- [[07 - Bugy & Opravy]]
