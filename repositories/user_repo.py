"""Repository for all user / auth / hierarchy SQL."""
from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


def get_by_username_and_password(username, password):
    """Return the user row as a dict if credentials match, else None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_by_username(username):
    """Return a user dict by username, or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_username_by_id(user_id):
    """Return the username string for a given user id, or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row["username"] if row else None
    finally:
        conn.close()


def get_team_by_manager(manager_id):
    """Return list of user dicts whose manager_id matches."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, full_name, role, username FROM users WHERE manager_id = ?",
            (manager_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def create_user(username, password, full_name, role, manager_id):
    """Insert a new user.  Returns (True, 'ok') or (False, error_message)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role, manager_id) VALUES (?, ?, ?, ?, ?)",
            (username, password, full_name, role, manager_id),
        )
        conn.commit()
        return True, "Uzivatel vytvoreny"
    except Exception as exc:
        # Re-raise IntegrityError info as a plain string so callers don't need sqlite3
        return False, str(exc)
    finally:
        conn.close()


def username_exists(username):
    """Return True if the username is already taken."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
    finally:
        conn.close()
