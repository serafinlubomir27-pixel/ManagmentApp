"""Repository for team invite tokens."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from repositories.base_repo import get_connection, row_to_dict


def create_invite(created_by: int, role: str = "employee") -> str:
    """Create a new invite token. Returns the token string."""
    token = str(uuid.uuid4())
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO invite_tokens (token, role, created_by) VALUES (?, ?, ?)",
            (token, role, created_by),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def get_invite(token: str) -> dict | None:
    """Get invite token info, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT id, token, role, created_by, used_by, used_at, expires_at, created_at
               FROM invite_tokens WHERE token = ?""",
            (token,),
        ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def mark_used(token: str, user_id: int) -> None:
    """Mark an invite token as used by a user."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE invite_tokens SET used_by = ?, used_at = ? WHERE token = ?",
            (user_id, datetime.now(timezone.utc).isoformat(), token),
        )
        conn.commit()
    finally:
        conn.close()


def list_invites_by_creator(user_id: int) -> list[dict]:
    """List all invite tokens created by a user."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT i.id, i.token, i.role, i.used_by, i.used_at, i.expires_at, i.created_at,
                      u.username AS used_by_username
               FROM invite_tokens i
               LEFT JOIN users u ON i.used_by = u.id
               WHERE i.created_by = ?
               ORDER BY i.created_at DESC
               LIMIT 20""",
            (user_id,),
        ).fetchall()
        from repositories.base_repo import rows_to_dicts
        return rows_to_dicts(rows)
    finally:
        conn.close()


def delete_invite(invite_id: int, user_id: int) -> bool:
    """Delete an invite token (only by its creator). Returns True if deleted."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM invite_tokens WHERE id = ? AND created_by = ?",
            (invite_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
