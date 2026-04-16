"""One-time migration: copies all data from local SQLite to Supabase (PostgreSQL).

Usage:
  1. Set up Supabase: run database/supabase_schema.sql in Supabase SQL Editor
  2. Add DATABASE_URL to your .env file
  3. Run:  py database/migrate_to_supabase.py

The script copies tables in dependency order:
  users → projects → tasks → task_dependencies → task_comments
  → task_attachments → activity_logs

Existing rows (same id) are skipped (ON CONFLICT DO NOTHING).
"""
from __future__ import annotations

import os
import sqlite3
import sys

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    os.environ.get("SQLITE_PATH", "my_project_app.db"),
)


def _get_pg():
    import psycopg2
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL is not set. Add it to .env first.")
        sys.exit(1)
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


def _get_sqlite():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_table(sqlite_conn, pg_conn, table: str, columns: list[str],
                   conflict_col: str = "id") -> int:
    cur_sqlite = sqlite_conn.cursor()
    cur_sqlite.execute(f"SELECT {', '.join(columns)} FROM {table}")
    rows = cur_sqlite.fetchall()
    if not rows:
        return 0

    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    sql = (
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_col}) DO NOTHING"
    )

    cur_pg = pg_conn.cursor()
    count = 0
    for row in rows:
        cur_pg.execute(sql, tuple(row))
        count += 1

    pg_conn.commit()
    return count


def migrate():
    print(f"Source SQLite: {SQLITE_PATH}")
    if not os.path.exists(SQLITE_PATH):
        print("ERROR: SQLite database not found.")
        sys.exit(1)

    sqlite_conn = _get_sqlite()
    pg_conn = _get_pg()

    tables = [
        ("users", [
            "id", "username", "password", "full_name", "role",
            "manager_id", "created_at",
        ]),
        ("projects", [
            "id", "user_id", "name", "description", "status",
            "is_template", "created_at",
        ]),
        ("tasks", [
            "id", "project_id", "name", "description", "status",
            "assigned_to", "created_by", "due_date", "priority",
            "estimated_hours", "duration", "delay_days",
            "es", "ef", "ls", "lf", "total_float", "is_critical",
            "category", "notes", "sort_order", "created_at",
        ]),
        ("task_dependencies", [
            "id", "task_id", "depends_on_task_id", "type",
        ]),
        ("task_comments", [
            "id", "task_id", "user_id", "content", "created_at",
        ]),
        ("task_attachments", [
            "id", "task_id", "file_name", "file_path",
            "uploaded_by", "uploaded_at",
        ]),
        ("activity_logs", [
            "id", "task_id", "user_id", "user_name", "action",
            "old_value", "new_value", "created_at",
        ]),
    ]

    total = 0
    for table, columns in tables:
        try:
            count = _migrate_table(sqlite_conn, pg_conn, table, columns)
            print(f"  {table}: {count} rows migrated")
            total += count
        except Exception as exc:
            pg_conn.rollback()
            print(f"  {table}: ERROR — {exc}")

    sqlite_conn.close()
    pg_conn.close()
    print(f"\nDone — {total} rows total migrated to Supabase.")


if __name__ == "__main__":
    migrate()
