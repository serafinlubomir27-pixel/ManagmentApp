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
