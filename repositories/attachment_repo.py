"""Repository for project_attachments and task_attachments (with visibility)."""
from __future__ import annotations
from repositories.base_repo import get_connection, rows_to_dicts


# ── Visibility helper ──────────────────────────────────────────────────────────

def _visibility_filter(user_role: str, user_id: int) -> tuple[str, list]:
    """Return SQL WHERE clause fragment and params for visibility filtering."""
    if user_role in ("admin", "manager"):
        # Managers see team + managers; not private of others
        return "(visibility IN ('team', 'managers') OR user_id = ?)", [user_id]
    # Regular employees: see team files + their own private
    return "(visibility = 'team' OR user_id = ?)", [user_id]


# ── Project attachments ────────────────────────────────────────────────────────

def add_project_attachment(
    project_id: int,
    user_id: int,
    file_name: str,
    file_path: str,
    file_size: int | None,
    mime_type: str | None,
    visibility: str = "team",
) -> int:
    """Insert a project attachment. Returns new id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO project_attachments
                (project_id, user_id, file_name, file_path, file_size, mime_type, visibility)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, user_id, file_name, file_path, file_size, mime_type, visibility),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_project_attachments(
    project_id: int,
    user_role: str,
    user_id: int,
) -> list[dict]:
    """Return project attachments visible to the requesting user."""
    vis_clause, vis_params = _visibility_filter(user_role, user_id)
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT pa.id, pa.file_name, pa.file_path, pa.file_size, pa.mime_type,
                   pa.visibility, pa.uploaded_at,
                   u.username AS uploaded_by_username
            FROM project_attachments pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = ? AND {vis_clause}
            ORDER BY pa.uploaded_at DESC
            """,
            [project_id] + vis_params,
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def update_project_attachment_visibility(
    attachment_id: int,
    visibility: str,
    user_id: int,
) -> bool:
    """Update visibility. Returns True if updated (only owner can change)."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE project_attachments SET visibility = ? WHERE id = ? AND user_id = ?",
            (visibility, attachment_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_project_attachment(attachment_id: int, user_id: int, user_role: str) -> str | None:
    """Delete project attachment. Owner or manager can delete. Returns file_path or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT file_path, user_id FROM project_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
        if not row:
            return None
        r = dict(row)
        if r["user_id"] != user_id and user_role not in ("admin", "manager"):
            return None  # not authorized
        conn.execute("DELETE FROM project_attachments WHERE id = ?", (attachment_id,))
        conn.commit()
        return r["file_path"]
    finally:
        conn.close()


# ── Task attachments (with visibility) ────────────────────────────────────────

def add_task_attachment(
    task_id: int,
    user_id: int,
    file_name: str,
    file_path: str,
    file_size: int | None,
    mime_type: str | None,
    visibility: str = "team",
) -> int:
    """Insert a task attachment with visibility. Returns new id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO task_attachments (task_id, file_name, file_path, uploaded_by, visibility)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, file_name, file_path, user_id, visibility),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_task_attachments(
    task_id: int,
    user_role: str,
    user_id: int,
) -> list[dict]:
    """Return task attachments visible to the requesting user."""
    vis_clause, vis_params = _visibility_filter(user_role, user_id)
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT ta.id, ta.file_name, ta.file_path, ta.visibility, ta.uploaded_at,
                   u.username AS uploaded_by_username
            FROM task_attachments ta
            JOIN users u ON ta.uploaded_by = u.id
            WHERE ta.task_id = ? AND {vis_clause}
            ORDER BY ta.uploaded_at DESC
            """,
            [task_id] + vis_params,
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def delete_task_attachment(attachment_id: int, user_id: int, user_role: str) -> str | None:
    """Delete task attachment. Owner or manager. Returns file_path or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT file_path, uploaded_by FROM task_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
        if not row:
            return None
        r = dict(row)
        if r["uploaded_by"] != user_id and user_role not in ("admin", "manager"):
            return None
        conn.execute("DELETE FROM task_attachments WHERE id = ?", (attachment_id,))
        conn.commit()
        return r["file_path"]
    finally:
        conn.close()


def update_task_attachment_visibility(
    attachment_id: int,
    visibility: str,
    user_id: int,
) -> bool:
    """Update task attachment visibility (owner only). Returns True if updated."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE task_attachments SET visibility = ? WHERE id = ? AND uploaded_by = ?",
            (visibility, attachment_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Unified view ───────────────────────────────────────────────────────────────

def get_all_attachments_for_project(
    project_id: int,
    user_role: str,
    user_id: int,
) -> dict:
    """Return project attachments + all task attachments for a project."""
    project_files = get_project_attachments(project_id, user_role, user_id)
    vis_clause, vis_params = _visibility_filter(user_role, user_id)
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT ta.id, ta.file_name, ta.file_path, ta.visibility, ta.uploaded_at,
                   u.username AS uploaded_by_username,
                   t.id AS task_id, t.name AS task_name
            FROM task_attachments ta
            JOIN tasks t ON ta.task_id = t.id
            JOIN users u ON ta.uploaded_by = u.id
            WHERE t.project_id = ? AND {vis_clause}
            ORDER BY ta.uploaded_at DESC
            """,
            [project_id] + vis_params,
        ).fetchall()
        task_files = rows_to_dicts(rows)
    finally:
        conn.close()
    return {"project_files": project_files, "task_files": task_files}
