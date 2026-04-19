"""Repository for all task-related SQL."""
from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


def get_tasks_for_project(project_id):
    """Return list of task dicts (with assigned username) for a project."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.id, t.name, t.status, t.due_date, u.username
            FROM tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE t.project_id = ?
            ORDER BY t.created_at DESC
            """,
            (project_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def create_task(project_id, name, assigned_to, created_by, due_date=None):
    """Insert a new task row and return its new id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (project_id, name, assigned_to, created_by, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, name, assigned_to, created_by, due_date),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_task_status_and_name(task_id):
    """Return dict with 'status' and 'name' for a task, or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT status, name FROM tasks WHERE id = ?", (task_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_task_status(task_id, new_status):
    """Set the status column for a task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    finally:
        conn.close()


def add_comment(task_id, user_id, content):
    """Insert a task comment row."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO task_comments (task_id, user_id, content) VALUES (?, ?, ?)",
            (task_id, user_id, content),
        )
        conn.commit()
    finally:
        conn.close()


def get_task_comments(task_id):
    """Return list of comment dicts (content, created_at, username) for a task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.content, c.created_at, u.username
            FROM task_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.task_id = ?
            ORDER BY c.created_at ASC
            """,
            (task_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def count_incomplete_tasks_for_user(user_id):
    """Return the number of tasks assigned to user_id that are not completed."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM tasks WHERE assigned_to = ? AND status != 'completed'",
            (user_id,),
        )
        return cursor.fetchone()["cnt"]
    finally:
        conn.close()


def get_status_breakdown_for_user(user_id):
    """Return dict {status: count} for tasks assigned_to or created_by user_id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT status, COUNT(*) AS cnt
            FROM tasks
            WHERE assigned_to = ? OR created_by = ?
            GROUP BY status
            """,
            (user_id, user_id),
        )
        rows = cursor.fetchall()
        return {row["status"]: row["cnt"] for row in rows}
    finally:
        conn.close()


def get_tasks_for_template(template_project_id):
    """Return task dicts for a template project."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_id, name, description, status, assigned_to,
                   created_by, due_date, priority, estimated_hours
            FROM tasks WHERE project_id = ?
            """,
            (template_project_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def create_task_from_template(project_id, name, description, assigned_to, created_by, due_date=None):
    """Insert a task copied from a template; returns new id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (project_id, name, description, assigned_to, created_by, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, name, description, assigned_to, created_by, due_date),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_workload_for_user(user_id: int) -> dict:
    """Return workload stats: total, pending, in_progress, completed, overdue counts."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks WHERE assigned_to = ? GROUP BY status",
            (user_id,),
        ).fetchall()
        dicts = rows_to_dicts(rows)
        total = sum(r["cnt"] for r in dicts)
        pending = next((r["cnt"] for r in dicts if r["status"] == "pending"), 0)
        in_progress = next((r["cnt"] for r in dicts if r["status"] == "in_progress"), 0)
        completed = next((r["cnt"] for r in dicts if r["status"] == "completed"), 0)
        blocked = next((r["cnt"] for r in dicts if r["status"] == "blocked"), 0)
        return {
            "total": total, "pending": pending, "in_progress": in_progress,
            "completed": completed, "blocked": blocked,
            "progress": completed / total if total > 0 else 0.0,
        }
    finally:
        conn.close()


def get_tasks_assigned_to_user(user_id: int) -> list[dict]:
    """Return all tasks assigned to a user with project name."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.name, t.status, t.due_date, t.duration,
                   t.is_critical, t.category, p.name AS project_name
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            WHERE t.assigned_to = ?
            ORDER BY t.status, t.name
            """,
            (user_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def get_tasks_with_due_dates(user_id: int) -> list:
    """Returns all tasks with due_date set, for user (assigned_to OR project owner)"""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.name, t.status, t.due_date, t.assigned_to,
                   p.name as project_name, p.user_id as project_owner
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            WHERE t.due_date IS NOT NULL AND t.due_date != ''
              AND (t.assigned_to = ? OR p.user_id = ?)
            ORDER BY t.due_date
            """,
            (user_id, user_id),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def get_status_breakdown_for_project(project_id: int) -> dict:
    """Return dict with total, completed and progress (0.0-1.0) for a project."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks WHERE project_id = ? GROUP BY status",
            (project_id,)
        ).fetchall()
        dicts = rows_to_dicts(rows)
        total = sum(r["cnt"] for r in dicts)
        completed = next((r["cnt"] for r in dicts if r["status"] == "completed"), 0)
        return {"total": total, "completed": completed, "progress": completed / total if total > 0 else 0.0}
    finally:
        conn.close()


def get_tasks_with_project_for_user(user_id):
    """Return task+project rows for reporting (tasks in user's projects)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.id, t.name AS task_name, t.status, t.due_date,
                   p.name AS project_name, u.username AS assigned_username
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE p.user_id = ?
            ORDER BY p.name, t.name
            """,
            (user_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CPM / dependency helpers
# ---------------------------------------------------------------------------

def get_task_dependencies(task_id: int) -> list[dict]:
    """Get all dependencies for a task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task_id, depends_on_task_id, type FROM task_dependencies WHERE task_id = ?",
            (task_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_all_dependencies_for_project(project_id: int) -> list[dict]:
    """Get all dependency records for all tasks in a project."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT d.id, d.task_id, d.depends_on_task_id, d.type
            FROM task_dependencies d
            JOIN tasks t ON d.task_id = t.id
            WHERE t.project_id = ?
            """,
            (project_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def add_dependency(task_id: int, depends_on_task_id: int) -> bool:
    """Add a dependency. Returns True on success."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO task_dependencies (task_id, depends_on_task_id) VALUES (?, ?)",
            (task_id, depends_on_task_id),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def remove_dependency(task_id: int, depends_on_task_id: int) -> bool:
    """Remove a dependency."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM task_dependencies WHERE task_id = ? AND depends_on_task_id = ?",
            (task_id, depends_on_task_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()


def update_task_cpm_fields(
    task_id: int, es: int, ef: int, ls: int, lf: int, total_float: int, is_critical: bool
) -> None:
    """Update CPM calculation results for a task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET es = ?, ef = ?, ls = ?, lf = ?, total_float = ?, is_critical = ?
            WHERE id = ?
            """,
            (es, ef, ls, lf, total_float, int(is_critical), task_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_task_full(
    task_id: int,
    name: str,
    description: str,
    duration: int,
    delay_days: int,
    category: str,
    status: str,
    notes: str,
    assigned_to: int | None,
) -> None:
    """Full update of a task with all fields including new CPM-related ones."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET name = ?, description = ?, duration = ?, delay_days = ?,
                category = ?, status = ?, notes = ?, assigned_to = ?
            WHERE id = ?
            """,
            (name, description, duration, delay_days, category, status, notes, assigned_to, task_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_tasks_for_project_with_cpm(project_id: int) -> list[dict]:
    """Get all tasks for a project including CPM fields and assigned username."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.id, t.name, t.description, t.status, t.due_date,
                   t.priority, t.estimated_hours,
                   t.duration, t.delay_days, t.es, t.ef, t.ls, t.lf,
                   t.total_float, t.is_critical, t.category, t.notes,
                   t.sort_order, t.assigned_to, t.created_by,
                   u.username AS assigned_username
            FROM tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE t.project_id = ?
            ORDER BY t.sort_order, t.created_at
            """,
            (project_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_task_by_id(task_id: int) -> dict | None:
    """Return full task row as dict, or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def update_task_fields(task_id: int, fields: dict) -> None:
    """Update arbitrary task fields. Keys must match column names."""
    if not fields:
        return
    allowed = {
        "name", "description", "status", "due_date", "priority",
        "estimated_hours", "duration", "delay_days", "category",
        "notes", "sort_order", "assigned_to",
    }
    safe = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not safe:
        return
    set_clause = ", ".join(f"{k} = ?" for k in safe)
    conn = get_connection()
    try:
        conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?",
            (*safe.values(), task_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_task(task_id: int) -> None:
    """Delete a task and its dependencies."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM task_dependencies WHERE task_id = ? OR depends_on_task_id = ?", (task_id, task_id))
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()


def get_dependencies(task_id: int) -> list[dict]:
    """Return dependency list for a task (alias for get_task_dependencies)."""
    return get_task_dependencies(task_id)
