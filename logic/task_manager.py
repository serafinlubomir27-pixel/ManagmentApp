from repositories import task_repo, user_repo, activity_repo


def get_tasks_for_project(project_id):
    """Vráti všetky úlohy pre konkrétny projekt aj s menom človeka, ktorý ju má na starosti"""
    try:
        return task_repo.get_tasks_for_project(project_id)
    except Exception as e:
        print(f"Chyba: {e}")
        return []


def add_task(project_id, name, assigned_to, created_by, due_date=None):
    """Vytvorí úlohu a zapíše to do Activity Logu"""
    try:
        new_task_id = task_repo.create_task(project_id, name, assigned_to, created_by, due_date)
        user_name = user_repo.get_username_by_id(created_by) or str(created_by)
        activity_repo.log_activity(new_task_id, created_by, user_name, "Vytvoril ulohu", new_value=name)
        return True
    except Exception as e:
        print(f"Chyba pri vytváraní úlohy: {e}")
        return False


def update_task_status(task_id, new_status, user_id):
    """Zmení stav úlohy a zapíše to do histórie"""
    try:
        old_data = task_repo.get_task_status_and_name(task_id)
        if not old_data:
            return False
        old_status = old_data["status"]

        task_repo.update_task_status(task_id, new_status)

        user_name = user_repo.get_username_by_id(user_id) or str(user_id)
        activity_repo.log_activity(task_id, user_id, user_name, "Zmena statusu", old_value=old_status, new_value=new_status)
        return True
    except Exception as e:
        print(f"Chyba status: {e}")
        return False


def add_comment(task_id, user_id, content):
    """Pridá komentár k úlohe"""
    try:
        task_repo.add_comment(task_id, user_id, content)
        return True
    except Exception as e:
        print(f"Chyba komentár: {e}")
        return False


def get_task_comments(task_id):
    """Načíta históriu chatu pre úlohu"""
    try:
        return task_repo.get_task_comments(task_id)
    except Exception as e:
        print(e)
        return []
