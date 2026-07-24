"""Repository for password-reset tokens.

Rovnaký tvar ako invite_repo (token + expirácia + mark_used), len pre reset hesla.
Tokeny sú jednorazové a krátkodobé (default 1 h — viď schéma).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from repositories.base_repo import get_connection, row_to_dict


def create_reset(user_id: int) -> str:
    """Create a password-reset token for a user. Returns the token string."""
    token = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO password_resets (user_id, token) VALUES (?, ?)",
            (user_id, token),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def get_reset(token: str) -> dict | None:
    """Return the reset row (user_id, expires_at, used_at) or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, user_id, token, expires_at, used_at, created_at FROM password_resets WHERE token = ?",
            (token,),
        ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def mark_used(token: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE password_resets SET used_at = ? WHERE token = ?",
            (datetime.now(timezone.utc).isoformat(), token),
        )
        conn.commit()
    finally:
        conn.close()
