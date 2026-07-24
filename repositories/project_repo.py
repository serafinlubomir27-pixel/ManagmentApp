"""Repository for all project-related SQL."""
from repositories.base_repo import get_connection, row_to_dict, rows_to_dicts


def get_user_projects(user_id):
    """Return projects owned by user_id OR where user_id has an assigned task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT p.id, p.name, p.description, p.status, p.created_at
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


def create_project(user_id, name, description, organization_id, status="active", is_template=False):
    """Insert a new project into an organization and return its id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (user_id, name, description, status, is_template, organization_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, description, status, bool(is_template), organization_id),
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
            "SELECT id, name, description FROM projects WHERE user_id = ? AND is_template = TRUE",
            (user_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def update_project_status(project_id: int, new_status: str) -> None:
    """Update the status of a project."""
    conn = get_connection()
    try:
        conn.execute("UPDATE projects SET status = ? WHERE id = ?", (new_status, project_id))
        conn.commit()
    finally:
        conn.close()


def update_project_fields(project_id: int, fields: dict) -> bool:
    """Update allowed project fields (name, description, status). Returns True if a row changed."""
    allowed = {"name", "description", "status"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_connection()
    try:
        cur = conn.execute(
            f"UPDATE projects SET {set_clause} WHERE id = ?",
            list(updates.values()) + [project_id],
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def user_has_access(user_id, project_id) -> bool:
    """True if the user owns the project OR has a task assigned in it.

    Used for object-level authorization (IDOR ochrana). Admin sa kontroluje
    zvlášť vo vrstve deps — tu ide čisto o vzťah user ↔ projekt.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM projects WHERE id = ? AND user_id = ? LIMIT 1",
            (project_id, user_id),
        )
        if cursor.fetchone() is not None:
            return True
        cursor.execute(
            "SELECT 1 FROM tasks WHERE project_id = ? AND assigned_to = ? LIMIT 1",
            (project_id, user_id),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def delete_project(project_id: int) -> bool:
    """Zmaž projekt a všetky závislé záznamy (manuálny cascade).

    SQLite má vo výdefaulte vypnuté FK enforcement a schéma má nekonzistentné
    ON DELETE pravidlá, takže deti mažeme explicitne, nech neostanú siroty.
    Vráti True, ak sa projekt reálne zmazal.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tasks WHERE project_id = ?", (project_id,))
        task_ids = [row["id"] for row in cur.fetchall()]

        if task_ids:
            ph = ",".join("?" for _ in task_ids)
            conn.execute(
                f"DELETE FROM task_dependencies WHERE task_id IN ({ph}) OR depends_on_task_id IN ({ph})",
                task_ids + task_ids,
            )
            for table in ("comments", "task_comments", "task_attachments", "time_logs", "activity_logs"):
                conn.execute(f"DELETE FROM {table} WHERE task_id IN ({ph})", task_ids)
            conn.execute(f"DELETE FROM notifications WHERE task_id IN ({ph})", task_ids)

        conn.execute("DELETE FROM notifications WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM project_attachments WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        deleted = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return deleted.rowcount > 0
    finally:
        conn.close()


def count_projects_for_org(organization_id) -> int:
    """Počet reálnych projektov organizácie (bez šablón) — pre vynútenie limitov plánu."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM projects WHERE organization_id = ? AND is_template = 0",
            (organization_id,),
        )
        return cursor.fetchone()["cnt"]
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
