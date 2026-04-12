from repositories import file_repo


def add_attachment(task_id, file_name, file_path, uploaded_by):
    """Attach a file record to a task."""
    try:
        return file_repo.add_attachment(task_id, file_name, file_path, uploaded_by)
    except Exception as e:
        print(f"Chyba add_attachment: {e}")
        return False


def get_attachments_for_task(task_id):
    """Return list of attachment dicts for a task."""
    try:
        return file_repo.get_attachments_for_task(task_id)
    except Exception as e:
        print(f"Chyba get_attachments_for_task: {e}")
        return []


def delete_attachment(attachment_id):
    """Remove an attachment record."""
    try:
        return file_repo.delete_attachment(attachment_id)
    except Exception as e:
        print(f"Chyba delete_attachment: {e}")
        return False
