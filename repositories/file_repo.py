"""Repository for task_attachments table."""
from repositories.base_repo import get_connection, rows_to_dicts


def add_attachment(task_id, file_name, file_path, uploaded_by):
    """Insert a file attachment record."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO task_attachments (task_id, file_name, file_path, uploaded_by)
            VALUES (?, ?, ?, ?)
            """,
            (task_id, file_name, file_path, uploaded_by),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_attachments_for_task(task_id):
    """Return list of attachment dicts for a task."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, file_name, file_path, uploaded_by, uploaded_at FROM task_attachments WHERE task_id = ?",
            (task_id,),
        )
        return rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def delete_attachment(attachment_id) -> "str | None":
    """Delete a specific attachment record by id. Returns the file_path or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_path FROM task_attachments WHERE id = ?", (attachment_id,)
        )
        row = cursor.fetchone()
        file_path = row["file_path"] if row else None
        cursor.execute("DELETE FROM task_attachments WHERE id = ?", (attachment_id,))
        conn.commit()
        return file_path
    finally:
        conn.close()
