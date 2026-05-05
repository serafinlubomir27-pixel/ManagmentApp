"""Repository for calendar token management."""
from __future__ import annotations

import uuid

from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


def get_token_for_user(user_id: int) -> str | None:
    """Return the calendar token for a user, or None if not set."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT token FROM calendar_tokens WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        d = row_to_dict(row)
        return d["token"] if d else None
    finally:
        conn.close()


def get_user_id_for_token(token: str) -> int | None:
    """Return user_id for a calendar token, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id FROM calendar_tokens WHERE token = ?",
            (token,),
        ).fetchone()
        if row is None:
            return None
        d = row_to_dict(row)
        return d["user_id"] if d else None
    finally:
        conn.close()


def create_or_replace_token(user_id: int) -> str:
    """Generate (or regenerate) a calendar token for a user. Returns the new token."""
    new_token = str(uuid.uuid4())
    conn = get_connection()
    try:
        # Try INSERT first; if conflict on user_id, UPDATE
        existing = conn.execute(
            "SELECT id FROM calendar_tokens WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE calendar_tokens SET token = ? WHERE user_id = ?",
                (new_token, user_id),
            )
        else:
            conn.execute(
                "INSERT INTO calendar_tokens (user_id, token) VALUES (?, ?)",
                (user_id, new_token),
            )
        conn.commit()
        return new_token
    finally:
        conn.close()
