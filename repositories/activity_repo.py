"""Repository for activity_logs table."""
from repositories.base_repo import get_connection, rows_to_dicts


def log_activity(task_id, user_id, user_name, action, old_value=None, new_value=None):
    """Insert a row into activity_logs."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activity_logs (task_id, user_id, user_name, action, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, user_id, user_name, action, old_value, new_value),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_activity_for_user(user_id, limit=5):
    """Return recent activity log dicts for projects/tasks visible to user_id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT al.user_name, al.action, al.new_value, al.created_at
            FROM activity_logs al
            JOIN tasks t ON al.task_id = t.id
            JOIN projects p ON t.project_id = p.id
            WHERE p.user_id = ?
               OR t.assigned_to = ?
            ORDER BY al.created_at DESC
            LIMIT ?
            """,
            (user_id, user_id, limit),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()
