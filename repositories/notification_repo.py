"""Repository for notification-related SQL operations."""
from __future__ import annotations

from datetime import date, timedelta

from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


def get_user_notifications(user_id: int, limit: int = 20) -> list[dict]:
    """Return user's notifications — unread first, then by date desc."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, type, title, message, task_id, project_id,
                   is_read, created_at
            FROM notifications
            WHERE user_id = ?
            ORDER BY is_read ASC, created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def mark_read(notification_id: int, user_id: int) -> bool:
    """Mark a single notification as read. Returns True if updated."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
            (notification_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def mark_all_read(user_id: int) -> int:
    """Mark all notifications for a user as read. Returns count updated."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def create_notification(
    user_id: int,
    type: str,
    title: str,
    message: str,
    task_id: int | None = None,
    project_id: int | None = None,
) -> dict:
    """Insert a notification and return it."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notifications (user_id, type, title, message, task_id, project_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, type, title, message, task_id, project_id),
        )
        conn.commit()
        new_id = cursor.lastrowid

        cursor2 = conn.cursor()
        cursor2.execute(
            "SELECT id, user_id, type, title, message, task_id, project_id, is_read, created_at FROM notifications WHERE id = ?",
            (new_id,),
        )
        return row_to_dict(cursor2.fetchone()) or {}
    finally:
        conn.close()


def check_and_create_deadline_notifications(days_ahead: list[int] | None = None) -> int:
    """Scan tasks with upcoming due_date and create deadline_warning notifications.

    Skips tasks where a warning for the same day-threshold already exists.
    Returns the number of new notifications created.
    """
    if days_ahead is None:
        days_ahead = [1, 3, 7]

    conn = get_connection()
    created = 0
    try:
        cursor = conn.cursor()
        # Fetch tasks with a due_date and an assigned user, not yet completed
        cursor.execute(
            """
            SELECT t.id AS task_id, t.name, t.due_date, t.project_id,
                   t.assigned_to AS user_id, p.name AS project_name
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            WHERE t.assigned_to IS NOT NULL
              AND t.due_date IS NOT NULL
              AND t.status NOT IN ('completed')
            """,
        )
        tasks = rows_to_dicts(cursor.fetchall())

        today = date.today()

        for task in tasks:
            try:
                due = date.fromisoformat(str(task["due_date"])[:10])
            except (ValueError, TypeError):
                continue

            days_left = (due - today).days

            for threshold in days_ahead:
                if days_left != threshold:
                    continue

                # Check if a notification for this task + threshold already exists
                chk = conn.cursor()
                chk.execute(
                    """
                    SELECT id FROM notifications
                    WHERE user_id = ?
                      AND task_id = ?
                      AND type = 'deadline_warning'
                      AND title LIKE ?
                    LIMIT 1
                    """,
                    (task["user_id"], task["task_id"], f"%{threshold} d%"),
                )
                if row_to_dict(chk.fetchone()):
                    continue  # Already notified for this threshold

                if threshold == 1:
                    days_label = "zajtra"
                else:
                    days_label = f"za {threshold} dní"

                notif = create_notification(
                    user_id=task["user_id"],
                    type="deadline_warning",
                    title=f"Blížiaci sa termín ({threshold} d)",
                    message=(
                        f"Úloha „{task['name']}\" v projekte „{task['project_name']}\" "
                        f"má termín {days_label} ({due.isoformat()})."
                    ),
                    task_id=task["task_id"],
                    project_id=task["project_id"],
                )
                if notif:
                    created += 1

    finally:
        conn.close()

    return created
