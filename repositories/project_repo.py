"""Repository for all project-related SQL."""
from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


def get_user_projects(user_id):
    """Return projects owned by user_id OR where user_id has an assigned task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT p.id, p.name, p.description, p.status
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            WHERE p.user_id = ?
               OR t.assigned_to = ?
            ORDER BY p.created_at DESC
            """,
            (user_id, user_id),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def create_project(user_id, name, description, status="active", is_template=False):
    """Insert a new project and return its id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (user_id, name, description, status, is_template)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, description, status, 1 if is_template else 0),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def count_active_projects_for_user(user_id):
    """Return count of active projects where user is owner or has a task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(DISTINCT p.id) AS cnt
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            WHERE (p.user_id = ? OR t.assigned_to = ?)
              AND p.status = 'active'
            """,
            (user_id, user_id),
        )
        return cursor.fetchone()["cnt"]
    finally:
        conn.close()


def get_templates(user_id):
    """Return projects marked as templates owned by user_id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description FROM projects WHERE user_id = ? AND is_template = 1",
            (user_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def get_project_by_id(project_id):
    """Return a single project dict or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        return row_to_dict(cursor.fetchone())
    finally:
        conn.close()


def get_projects_for_reporting(user_id):
    """Return active projects owned by user_id for report generation."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, description, status, created_at
            FROM projects
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()
