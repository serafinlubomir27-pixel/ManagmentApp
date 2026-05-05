"""Repository for time tracking logs."""
from __future__ import annotations
from repositories.base_repo import get_connection, rows_to_dicts


def log_time(task_id: int, user_id: int, hours: float, log_date: str, note: str = "") -> int:
    """Insert a time log entry. Returns new id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO time_logs (task_id, user_id, hours, log_date, note) VALUES (?, ?, ?, ?, ?)",
            (task_id, user_id, hours, log_date, note or None),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_time_logs_for_task(task_id: int) -> list[dict]:
    """Return all time logs for a task with username."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT tl.id, tl.hours, tl.log_date, tl.note, tl.created_at,
                   u.username, u.full_name
            FROM time_logs tl
            JOIN users u ON tl.user_id = u.id
            WHERE tl.task_id = ?
            ORDER BY tl.log_date DESC, tl.created_at DESC
            """,
            (task_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def get_total_logged_hours(task_id: int) -> float:
    """Return total logged hours for a task."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(hours), 0) AS total FROM time_logs WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        from repositories.base_repo import row_to_dict
        d = row_to_dict(row)
        return float(d["total"]) if d else 0.0
    finally:
        conn.close()


def delete_time_log(log_id: int, user_id: int) -> bool:
    """Delete a time log (only own entries). Returns True if deleted."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM time_logs WHERE id = ? AND user_id = ?",
            (log_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_time_summary_for_project(project_id: int) -> list[dict]:
    """Return time summary (total_hours, estimated_hours) per task for a project."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.name, t.estimated_hours,
                   COALESCE(SUM(tl.hours), 0) AS logged_hours
            FROM tasks t
            LEFT JOIN time_logs tl ON tl.task_id = t.id
            WHERE t.project_id = ?
            GROUP BY t.id
            ORDER BY t.sort_order, t.id
            """,
            (project_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()
