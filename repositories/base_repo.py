"""Base repository — dual-mode database connection.

Supports two backends controlled by the DB_BACKEND environment variable:

  DB_BACKEND=sqlite   (default) — local SQLite file, no setup required
  DB_BACKEND=postgres            — PostgreSQL via DATABASE_URL (Supabase or any PG host)

Usage:
  Copy .env.example to .env and set DB_BACKEND + DATABASE_URL.

All repos call get_connection() and receive a connection object that exposes
the same interface regardless of backend:
  - .cursor()       — returns a cursor
  - .execute()      — shorthand execute on connection
  - .commit()       — commit transaction
  - .close()        — close (no-op for pooled PG connections)

Row access: both backends return rows accessible by column name (dict-like).
Use row_to_dict() / rows_to_dicts() to convert to plain dicts.
"""
from __future__ import annotations

import os
import sqlite3

# Load .env if present (optional — app works without it for SQLite mode)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — use system env vars or defaults

# ── Backend selection ──────────────────────────────────────────────────────

_BACKEND = os.environ.get("DB_BACKEND", "sqlite").strip().lower()

# ── SQLite path ────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, os.environ.get("SQLITE_PATH", "my_project_app.db"))


# ── PostgreSQL connection wrapper ──────────────────────────────────────────

class _PgCursorWrapper:
    """Wraps a psycopg2 cursor so column values are accessible by name (like sqlite3.Row)."""

    def __init__(self, cursor):
        self._cur = cursor
        self._columns: list[str] = []
        self._last_id = None

    def execute(self, sql: str, params=None):
        # Translate SQLite ? placeholders to psycopg2 %s
        pg_sql = sql.replace("?", "%s")
        # Auto-append RETURNING id for INSERT statements so lastrowid works
        stripped_upper = pg_sql.strip().upper()
        if stripped_upper.startswith("INSERT") and "RETURNING" not in stripped_upper:
            pg_sql = pg_sql.rstrip().rstrip(";") + " RETURNING id"
        if params is None:
            self._cur.execute(pg_sql)
        else:
            self._cur.execute(pg_sql, params)
        if self._cur.description:
            self._columns = [d[0] for d in self._cur.description]
            # Capture the inserted id immediately so lastrowid works after commit
            if self._columns == ["id"]:
                row = self._cur.fetchone()
                self._last_id = row[0] if row else None
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return dict(zip(self._columns, row))

    def fetchall(self):
        rows = self._cur.fetchall()
        return [dict(zip(self._columns, r)) for r in rows]

    @property
    def lastrowid(self):
        return self._last_id

    @property
    def rowcount(self):
        return self._cur.rowcount


class _PgConnectionWrapper:
    """Wraps a psycopg2 connection so it behaves like sqlite3 for our repos.

    Key adaptations:
    - cursor() returns a _PgCursorWrapper
    - execute() is a shorthand that creates a cursor, executes, returns cursor
    - RETURNING id clause added automatically for INSERT to support lastrowid
    - close() is kept as-is (psycopg2 connections should be closed)
    """

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _PgCursorWrapper(self._conn.cursor())

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def rollback(self):
        self._conn.rollback()


def _get_pg_connection() -> _PgConnectionWrapper:
    """Create a new psycopg2 connection to PostgreSQL."""
    import psycopg2
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to your .env file.\n"
            "See .env.example for the format."
        )
    raw = psycopg2.connect(db_url)
    raw.autocommit = False
    return _PgConnectionWrapper(raw)


# ── SQLite row wrapper ─────────────────────────────────────────────────────

class _SqliteCursorWrapper:
    """Thin wrapper around sqlite3 cursor that stores lastrowid properly."""

    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor()

    def execute(self, sql: str, params=None):
        if params is None:
            self._cur.execute(sql)
        else:
            self._cur.execute(sql, params)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount


class _SqliteConnectionWrapper:
    """Wraps sqlite3 connection with the same interface as _PgConnectionWrapper."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _SqliteCursorWrapper(self._conn)

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def rollback(self):
        self._conn.rollback()


def _get_sqlite_connection() -> _SqliteConnectionWrapper:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return _SqliteConnectionWrapper(conn)


# ── Public API ─────────────────────────────────────────────────────────────

def get_connection():
    """Return a database connection for the configured backend.

    SQLite:   lightweight, file-based, no config needed
    Postgres: requires DATABASE_URL in environment / .env
    """
    if _BACKEND == "postgres":
        return _get_pg_connection()
    return _get_sqlite_connection()


def get_backend() -> str:
    """Return the active backend name: 'sqlite' or 'postgres'."""
    return _BACKEND


def row_to_dict(row) -> dict | None:
    """Convert a row to a plain dict (handles None, sqlite3.Row, and plain dict)."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)


def rows_to_dicts(rows) -> list[dict]:
    """Convert a list of rows to a list of plain dicts."""
    result = []
    for r in rows:
        if isinstance(r, dict):
            result.append(r)
        else:
            result.append(dict(r))
    return result
