"""Repository for all user / auth / hierarchy SQL."""
from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts
from logic.passwords import verify_password, hash_password, needs_rehash


def get_by_username_and_password(username, password):
    """Return the user row as a dict if credentials match, else None.

    Podporuje bcrypt aj staré SHA-256 heslá. Ak sa prihlási používateľ so starým
    SHA-256 hashom, heslo sa transparentne prehashuje na bcrypt (migrácia pri logine).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = row_to_dict(cursor.fetchone())
        if not row or not verify_password(password, row.get("password") or ""):
            return None
        if needs_rehash(row["password"]):
            new_hash = hash_password(password)
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, row["id"]))
            conn.commit()
            row["password"] = new_hash
        return row
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


def create_user(username, password, full_name, role, manager_id, organization_id, email=None):
    """Insert a new user into an organization. Returns (True, 'ok') or (False, error_message).

    organization_id je povinné — používateľ bez organizácie by obišiel izoláciu dát.
    email je voliteľný (login identita); ak je NULL, používateľ sa prihlasuje cez username.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role, manager_id, organization_id, email)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, password, full_name, role, manager_id, organization_id, email),
        )
        conn.commit()
        return True, "Uzivatel vytvoreny"
    except Exception as exc:
        # Re-raise IntegrityError info as a plain string so callers don't need sqlite3
        return False, str(exc)
    finally:
        conn.close()


def get_by_email(email):
    """Return a user dict by e-mail (case-insensitive), or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_by_login_and_password(login, password):
    """Verify credentials by e-mail OR username. Returns user dict or None.

    Podporuje starých používateľov (login cez username) aj nových (login cez e-mail).
    Migrácia SHA-256 -> bcrypt prebehne rovnako ako v get_by_username_and_password.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE lower(email) = lower(?) OR username = ?",
            (login, login),
        )
        row = row_to_dict(cursor.fetchone())
        if not row or not verify_password(password, row.get("password") or ""):
            return None
        if needs_rehash(row["password"]):
            new_hash = hash_password(password)
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, row["id"]))
            conn.commit()
            row["password"] = new_hash
        return row
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


def get_all_users(organization_id: int) -> list[dict]:
    """Return all users OF THE GIVEN ORGANIZATION (for admin views).

    organization_id je povinné — predtým tento dopyt vracal používateľov naprieč
    všetkými organizáciami, čo je pri multi-tenancy únik dát.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, full_name, role, manager_id, organization_id, created_at"
            " FROM users WHERE organization_id = ? ORDER BY role, username",
            (organization_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def update_password(user_id: int, hashed_password: str) -> None:
    """Update the hashed password for a user."""
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
    finally:
        conn.close()


def update_user_role(user_id: int, role: str) -> None:
    """Update the role of a user (admin only operation)."""
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
    finally:
        conn.close()


def update_user_manager(user_id: int, manager_id: int | None) -> None:
    """Assign or remove a manager for a user."""
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET manager_id = ? WHERE id = ?", (manager_id, user_id))
        conn.commit()
    finally:
        conn.close()


def update_user_profile(user_id: int, fields: dict) -> None:
    """Update profile fields: full_name, bio, avatar_color, timezone."""
    allowed = {"full_name", "bio", "avatar_color", "timezone"}
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return
    set_clause = ", ".join(f"{k} = ?" for k in safe)
    conn = get_connection()
    try:
        conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?",
            (*safe.values(), user_id),
        )
        conn.commit()
    finally:
        conn.close()


def count_users_for_org(organization_id: int) -> int:
    """Počet používateľov organizácie — pre vynútenie limitov plánu."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE organization_id = ?", (organization_id,))
        return cursor.fetchone()["cnt"]
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    """Return full user dict by id, or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()
