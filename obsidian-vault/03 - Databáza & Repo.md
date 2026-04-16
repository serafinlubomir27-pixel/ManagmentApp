# 🗄️ Databáza & Repository Pattern

#databaza #sqlite #repository #sql

## Databázový súbor

`my_project_app.db` — SQLite, uložený v root priečinku projektu.
Inicializovaný pri štarte cez `database/setup.py → create_database()`.

## Tabuľky

### users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,       -- SHA-256 hash
    full_name TEXT,
    role TEXT DEFAULT 'employee', -- admin | manager | employee
    manager_id INTEGER,           -- FK na users.id (hierarchia)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### projects
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active', -- active | completed | archived
    is_template BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### tasks
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending', -- pending | in_progress | completed | blocked
    assigned_to INTEGER,
    created_by INTEGER,
    due_date TEXT,
    priority TEXT DEFAULT 'medium',
    estimated_hours REAL,
    -- CPM polia (migrácia):
    duration INTEGER DEFAULT 1,
    delay_days INTEGER DEFAULT 0,
    es INTEGER DEFAULT 0,
    ef INTEGER DEFAULT 0,
    ls INTEGER DEFAULT 0,
    lf INTEGER DEFAULT 0,
    total_float INTEGER DEFAULT 0,
    is_critical BOOLEAN DEFAULT 0,
    category TEXT DEFAULT 'Other',
    notes TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### task_dependencies
```sql
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    type TEXT DEFAULT 'finish_to_start'
)
```

### Ostatné tabuľky
- `activity_logs` — história zmien (kto, čo, kedy)
- `task_attachments` — prílohy k úlohám
- `task_comments` — komentáre k úlohám

## CPM tabuľky

Polia `es, ef, ls, lf, total_float, is_critical` boli pridané **migráciou**:

```python
# Bezpečná migrácia — try/except (SQLite nemá ADD COLUMN IF NOT EXISTS)
for column_sql in ["ALTER TABLE tasks ADD COLUMN duration INTEGER DEFAULT 1", ...]:
    try:
        cursor.execute(column_sql)
    except Exception:
        pass  # stĺpec už existuje
```

## Repository Pattern

### Štruktúra

```
repositories/
├── base_repo.py       ← DB connection, row_to_dict(), rows_to_dicts()
├── task_repo.py       ← všetok SQL pre úlohy
├── user_repo.py       ← autentifikácia, tím, hierachia
├── project_repo.py    ← projekty, šablóny
├── activity_repo.py   ← logy aktivít
└── file_repo.py       ← prílohy
```

### base_repo.py — kľúčové

```python
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # ← prístup podľa mena stĺpca
    return conn

def rows_to_dicts(rows):
    return [dict(r) for r in rows]  # ← vždy vrátime plain dict
```

> ⚠️ Všetky repo funkcie vracajú `dict` / `list[dict]`, nie tuple! Pozri [[07 - Bugy & Opravy#KeyError 0]].

## Kľúčové repo funkcie

### task_repo.py

| Funkcia | Popis |
|---------|-------|
| `get_tasks_for_project_with_cpm(pid)` | Všetky úlohy s CPM poľami |
| `update_task_full(...)` | Update všetkých polí vrátane CPM |
| `update_task_cpm_fields(...)` | Uloží výsledky CPM výpočtu |
| `add_dependency(task_id, dep_id)` | Pridá závislosť |
| `remove_dependency(task_id, dep_id)` | Odstráni závislosť |
| `get_all_dependencies_for_project(pid)` | Všetky závislosti projektu |
| `get_workload_for_user(uid)` | Štatistiky záťaže člena tímu |
| `get_tasks_assigned_to_user(uid)` | Úlohy priradené užívateľovi |

### user_repo.py

| Funkcia | Popis |
|---------|-------|
| `get_by_username_and_password(u, p)` | Login (hashuje SHA-256) |
| `get_team_by_manager(mid)` | Tím manažéra |
| `create_user(...)` | Nový člen tímu |
| `update_password(uid, hashed)` | Zmena hesla |
| `get_all_users()` | Všetci užívatelia (admin view) |

## Heslá

Uložené ako **SHA-256 hash** (nie plaintext).

```python
import hashlib
hashed = hashlib.sha256(password.encode()).hexdigest()
# výsledok: 64-znakový hex string
```

Migrácia existujúcich plaintext hesiel:
```python
# V setup.py pri každom štarte:
plain_users = cursor.execute(
    "SELECT id, password FROM users WHERE length(password) != 64"
).fetchall()
for uid, pwd in plain_users:
    hashed = hashlib.sha256(pwd.encode()).hexdigest()
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, uid))
```

## Súvisiace

- [[01 - Architektúra#Repository Pattern]]
- [[02 - CPM Engine]]
- [[07 - Bugy & Opravy]]
- [[08 - Roadmap v2.0#PostgreSQL Supabase]]
