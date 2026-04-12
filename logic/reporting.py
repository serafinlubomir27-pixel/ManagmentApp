from repositories import project_repo, task_repo


def get_project_report(user_id):
    """Return a list of dicts with project info and associated task details for reporting."""
    try:
        projects = project_repo.get_projects_for_reporting(user_id)
        tasks = task_repo.get_tasks_with_project_for_user(user_id)
        return {"projects": projects, "tasks": tasks}
    except Exception as e:
        print(f"Chyba get_project_report: {e}")
        return {"projects": [], "tasks": []}
