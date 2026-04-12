import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "my_project_app.db")


def get_connection():
    """Return a sqlite3 connection with row_factory set to sqlite3.Row so all
    results can be accessed both by index and by column name, and converted to
    plain dicts easily."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    """Convert a sqlite3.Row (or None) to a plain dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows):
    """Convert a list of sqlite3.Row objects to a list of plain dicts."""
    return [dict(r) for r in rows]
