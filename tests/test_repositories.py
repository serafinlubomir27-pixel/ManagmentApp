"""Unit tests for repositories/ using an in-memory SQLite database.

Run with:
    py -m pytest tests/test_repositories.py -v
"""
import hashlib
import sqlite3
import pytest

import repositories.base_repo as base_repo


# ---------------------------------------------------------------------------
# In-memory DB fixture using shared-cache URI so conn.close() doesn't destroy it
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'employee',
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    is_template BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    assigned_to INTEGER,
    created_by INTEGER,
    due_date TEXT,
    priority TEXT DEFAULT 'medium',
    estimated_hours REAL,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    type TEXT DEFAULT 'finish_to_start',
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS task_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS task_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_by INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    user_id INTEGER,
    user_name TEXT,
    action TEXT,
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Unique URI per test via counter avoids cross-test contamination
class _NoCloseConn:
    """Wraps a sqlite3 connection so that .close() is a no-op.

    Repos call conn.close() in finally blocks. For in-memory DBs this destroys
    the database. This wrapper prevents that while still delegating everything else.
    """
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass  # intentional no-op

    def __getattr__(self, name):
        return getattr(self._conn, name)


@pytest.fixture
def db(monkeypatch):
    """Provide a fresh in-memory SQLite DB per test.

    Patches get_connection() to return a non-closing wrapper so repos calling
    conn.close() in finally blocks don't destroy the in-memory database.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)

    # Seed admin user
    pw = hashlib.sha256(b"admin123").hexdigest()
    conn.execute(
        "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
        ("admin", pw, "Admin User", "admin"),
    )
    conn.commit()

    def make_conn():
        wrapper = _NoCloseConn(conn)
        return wrapper

    # Repos use "from repositories.base_repo import get_connection" which creates
    # a LOCAL name in each module. Patching base_repo alone doesn't affect them.
    # We must patch each module's local reference directly.
    monkeypatch.setattr(base_repo, "get_connection", make_conn)
    monkeypatch.setattr("repositories.user_repo.get_connection", make_conn)
    monkeypatch.setattr("repositories.project_repo.get_connection", make_conn)
    monkeypatch.setattr("repositories.task_repo.get_connection", make_conn)

    yield conn

    conn.close()


def _user_id(conn, username="admin"):
    row = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    return row["id"]


def _project_id(conn, user_id, name="Test Project"):
    conn.execute(
        "INSERT INTO projects (user_id, name) VALUES (?, ?)", (user_id, name)
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM projects WHERE name=? ORDER BY id DESC LIMIT 1", (name,)
    ).fetchone()["id"]


# ---------------------------------------------------------------------------
# base_repo helpers
# ---------------------------------------------------------------------------

class TestBaseRepo:
    def test_row_to_dict_none(self):
        from repositories.base_repo import row_to_dict
        assert row_to_dict(None) is None

    def test_row_to_dict(self, db):
        row = db.execute("SELECT id, username FROM users").fetchone()
        from repositories.base_repo import row_to_dict
        d = row_to_dict(row)
        assert isinstance(d, dict)
        assert "username" in d

    def test_rows_to_dicts(self, db):
        from repositories.base_repo import rows_to_dicts
        rows = db.execute("SELECT id, username FROM users").fetchall()
        result = rows_to_dicts(rows)
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)


# ---------------------------------------------------------------------------
# user_repo
# ---------------------------------------------------------------------------

class TestUserRepo:
    def test_authenticate_correct(self, db):
        from repositories.user_repo import get_by_username_and_password
        user = get_by_username_and_password("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"

    def test_authenticate_wrong_password(self, db):
        from repositories.user_repo import get_by_username_and_password
        user = get_by_username_and_password("admin", "wrong")
        assert user is None

    def test_authenticate_nonexistent(self, db):
        from repositories.user_repo import get_by_username_and_password
        user = get_by_username_and_password("ghost", "any")
        assert user is None

    def test_get_all_users(self, db):
        from repositories.user_repo import get_all_users
        users = get_all_users()
        assert len(users) >= 1
        assert any(u["username"] == "admin" for u in users)

    def test_create_user_and_retrieve(self, db):
        from repositories.user_repo import create_user, get_all_users
        pw = hashlib.sha256(b"secret").hexdigest()
        ok, msg = create_user("alice", pw, "Alice Smith", "employee", None)
        assert ok
        users = get_all_users()
        assert any(u["username"] == "alice" for u in users)

    def test_create_user_duplicate_fails(self, db):
        from repositories.user_repo import create_user
        pw = hashlib.sha256(b"pw").hexdigest()
        ok1, _ = create_user("bob", pw, "Bob", "employee", None)
        ok2, msg = create_user("bob", pw, "Bob2", "employee", None)
        assert ok1
        assert not ok2
        assert "UNIQUE" in msg or "unique" in msg.lower()

    def test_get_by_username(self, db):
        from repositories.user_repo import get_by_username
        user = get_by_username("admin")
        assert user is not None
        assert user["role"] == "admin"

    def test_get_by_username_not_found(self, db):
        from repositories.user_repo import get_by_username
        assert get_by_username("nobody") is None

    def test_username_exists(self, db):
        from repositories.user_repo import username_exists
        assert username_exists("admin") is True
        assert username_exists("ghost") is False

    def test_update_password(self, db):
        from repositories.user_repo import update_password, get_by_username_and_password
        uid = _user_id(db)
        new_pw = hashlib.sha256(b"newpass").hexdigest()
        update_password(uid, new_pw)
        assert get_by_username_and_password("admin", "newpass") is not None
        assert get_by_username_and_password("admin", "admin123") is None

    def test_get_username_by_id(self, db):
        from repositories.user_repo import get_username_by_id
        uid = _user_id(db)
        assert get_username_by_id(uid) == "admin"

    def test_get_username_by_id_not_found(self, db):
        from repositories.user_repo import get_username_by_id
        assert get_username_by_id(9999) is None


# ---------------------------------------------------------------------------
# project_repo
# ---------------------------------------------------------------------------

class TestProjectRepo:
    def test_create_and_get_projects(self, db):
        from repositories.project_repo import create_project, get_user_projects
        uid = _user_id(db)
        create_project(uid, "Alpha", "Desc", "active")
        projects = get_user_projects(uid)
        assert any(p["name"] == "Alpha" for p in projects)

    def test_get_projects_returns_only_own(self, db):
        from repositories.project_repo import create_project, get_user_projects
        from repositories.user_repo import create_user
        pw = hashlib.sha256(b"pw").hexdigest()
        create_user("bob", pw, "Bob", "employee", None)
        bob_id = _user_id(db, "bob")
        admin_id = _user_id(db)
        create_project(admin_id, "Admin Project", "", "active")
        create_project(bob_id, "Bob Project", "", "active")
        admin_projects = get_user_projects(admin_id)
        assert all(p["name"] != "Bob Project" for p in admin_projects)

    def test_get_project_by_id(self, db):
        from repositories.project_repo import create_project, get_project_by_id
        uid = _user_id(db)
        pid = create_project(uid, "Beta", "Desc", "active")
        project = get_project_by_id(pid)
        assert project is not None
        assert project["name"] == "Beta"

    def test_get_project_by_id_not_found(self, db):
        from repositories.project_repo import get_project_by_id
        assert get_project_by_id(9999) is None

    def test_update_project_status(self, db):
        from repositories.project_repo import create_project, update_project_status, get_project_by_id
        uid = _user_id(db)
        pid = create_project(uid, "Gamma", "", "active")
        update_project_status(pid, "completed")
        project = get_project_by_id(pid)
        assert project["status"] == "completed"

    def test_count_active_projects(self, db):
        from repositories.project_repo import create_project, count_active_projects_for_user
        uid = _user_id(db)
        create_project(uid, "P1", "", "active")
        create_project(uid, "P2", "", "active")
        create_project(uid, "P3", "", "completed")
        count = count_active_projects_for_user(uid)
        assert count == 2

    def test_templates(self, db):
        from repositories.project_repo import create_project, get_templates
        uid = _user_id(db)
        create_project(uid, "Template A", "", "active", is_template=True)
        create_project(uid, "Regular", "", "active", is_template=False)
        templates = get_templates(uid)
        assert len(templates) == 1
        assert templates[0]["name"] == "Template A"


# ---------------------------------------------------------------------------
# task_repo
# ---------------------------------------------------------------------------

class TestTaskRepo:
    def test_create_and_get_tasks(self, db):
        from repositories.task_repo import create_task, get_tasks_for_project
        uid = _user_id(db)
        pid = _project_id(db, uid)
        create_task(pid, "Task 1", uid, uid)
        tasks = get_tasks_for_project(pid)
        assert len(tasks) == 1
        assert tasks[0]["name"] == "Task 1"

    def test_task_default_status_is_pending(self, db):
        from repositories.task_repo import create_task, get_tasks_for_project
        uid = _user_id(db)
        pid = _project_id(db, uid)
        create_task(pid, "My Task", uid, uid)
        tasks = get_tasks_for_project(pid)
        assert tasks[0]["status"] == "pending"

    def test_update_task_status(self, db):
        from repositories.task_repo import create_task, update_task_status, get_task_status_and_name
        uid = _user_id(db)
        pid = _project_id(db, uid)
        task_id = create_task(pid, "Task A", uid, uid)
        update_task_status(task_id, "in_progress")
        t = get_task_status_and_name(task_id)
        assert t["status"] == "in_progress"

    def test_get_task_status_not_found(self, db):
        from repositories.task_repo import get_task_status_and_name
        assert get_task_status_and_name(9999) is None

    def test_multiple_tasks_returned(self, db):
        from repositories.task_repo import create_task, get_tasks_for_project
        uid = _user_id(db)
        pid = _project_id(db, uid)
        for i in range(5):
            create_task(pid, f"Task {i}", uid, uid)
        tasks = get_tasks_for_project(pid)
        assert len(tasks) == 5

    def test_tasks_isolated_by_project(self, db):
        from repositories.task_repo import create_task, get_tasks_for_project
        uid = _user_id(db)
        pid1 = _project_id(db, uid, "Project 1")
        pid2 = _project_id(db, uid, "Project 2")
        create_task(pid1, "P1 Task", uid, uid)
        create_task(pid2, "P2 Task", uid, uid)
        assert len(get_tasks_for_project(pid1)) == 1
        assert len(get_tasks_for_project(pid2)) == 1

    def test_create_task_returns_id(self, db):
        from repositories.task_repo import create_task
        uid = _user_id(db)
        pid = _project_id(db, uid)
        task_id = create_task(pid, "ID Test", uid, uid)
        assert isinstance(task_id, int)
        assert task_id > 0

    def test_task_name_in_result(self, db):
        from repositories.task_repo import create_task, get_task_status_and_name
        uid = _user_id(db)
        pid = _project_id(db, uid)
        task_id = create_task(pid, "Named Task", uid, uid)
        t = get_task_status_and_name(task_id)
        assert t["name"] == "Named Task"
