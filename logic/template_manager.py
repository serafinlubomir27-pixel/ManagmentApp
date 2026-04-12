from repositories import project_repo, task_repo


def get_templates(user_id):
    """Return list of template projects for user_id."""
    try:
        return project_repo.get_templates(user_id)
    except Exception as e:
        print(f"Chyba get_templates: {e}")
        return []


def create_project_from_template(template_id, new_project_name, owner_id):
    """Copy a template project (and its tasks) into a new real project.
    Returns the new project id on success, or None on failure."""
    try:
        template = project_repo.get_project_by_id(template_id)
        if not template:
            return None

        new_project_id = project_repo.create_project(
            owner_id,
            new_project_name,
            template["description"],
            status="active",
            is_template=False,
        )

        template_tasks = task_repo.get_tasks_for_template(template_id)
        for t in template_tasks:
            task_repo.create_task_from_template(
                new_project_id,
                t["name"],
                t.get("description"),
                None,
                owner_id,
                None,
            )

        return new_project_id
    except Exception as e:
        print(f"Chyba create_project_from_template: {e}")
        return None
