from repositories import task_repo, project_repo, activity_repo


def get_dashboard_stats(user_id):
    """Vráti počty projektov, úloh a posledné aktivity"""
    stats = {
        "projects_count": 0,
        "tasks_count": 0,
        "critical_count": 0,
        "recent_activity": [],
    }

    try:
        stats["projects_count"] = project_repo.count_active_projects_for_user(user_id)
        stats["tasks_count"] = task_repo.count_incomplete_tasks_for_user(user_id)
        stats["recent_activity"] = activity_repo.get_recent_activity_for_user(user_id, limit=5)
    except Exception as e:
        print(f"Chyba stats: {e}")

    return stats


def get_task_status_breakdown(user_id):
    """Returns dict: {pending: N, in_progress: N, completed: N, blocked: N}
    for tasks assigned to or created by user_id."""
    defaults = {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0}
    try:
        breakdown = task_repo.get_status_breakdown_for_user(user_id)
        defaults.update(breakdown)
    except Exception as e:
        print(f"Chyba get_task_status_breakdown: {e}")
    return defaults
