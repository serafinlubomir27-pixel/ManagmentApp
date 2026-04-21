"""Repository for comment-related SQL operations."""
from __future__ import annotations

from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


def get_comments_for_task(task_id: int) -> list[dict]:
    """Return all comments for a task, newest first, with author name."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.id, c.task_id, c.user_id, u.full_name AS author_name,
                   c.content, c.created_at
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.task_id = ?
            ORDER BY c.created_at ASC
            """,
            (task_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def create_comment(task_id: int, user_id: int, content: str) -> dict:
    """Insert a new comment and return it with author name."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO comments (task_id, user_id, content)
            VALUES (?, ?, ?)
            """,
            (task_id, user_id, content),
        )
        conn.commit()
        new_id = cursor.lastrowid

        # Fetch the inserted comment with author name
        cursor2 = conn.cursor()
        cursor2.execute(
            """
            SELECT c.id, c.task_id, c.user_id, u.full_name AS author_name,
                   c.content, c.created_at
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = ?
            """,
            (new_id,),
        )
        return row_to_dict(cursor2.fetchone()) or {}
    finally:
        conn.close()


def delete_comment(comment_id: int, user_id: int) -> bool:
    """Delete a comment only if it belongs to the given user. Returns True if deleted."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM comments WHERE id = ? AND user_id = ?",
            (comment_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
