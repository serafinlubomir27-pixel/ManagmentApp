"""AI endpoints — natural language project parsing + dependency suggestions.

POST /ai/parse-project          — parse description → task list (dry run, no DB changes)
POST /projects/{id}/ai-generate — parse description + create tasks in project
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_manager_or_admin
from repositories import task_repo, project_repo
from logic import ai_parser, cpm_manager

router = APIRouter(tags=["ai"])


class ParseProjectRequest(BaseModel):
    description: str
    max_tasks: int = 15


class GenerateTasksRequest(BaseModel):
    description: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/ai/parse-project")
def parse_project_description(
    body: ParseProjectRequest,
    current_user: dict = Depends(get_current_user),
):
    """Parse natural language project description → task list (preview, no DB changes).
    Uses OpenAI GPT-4o-mini if OPENAI_API_KEY is set, else heuristic fallback.
    """
    if len(body.description.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Popis projektu je príliš krátky (min. 10 znakov)",
        )

    result = ai_parser.parse_project(body.description)
    # Limit tasks if requested
    result["tasks"] = result["tasks"][:body.max_tasks]
    return result


@router.post("/projects/{project_id}/ai-generate", status_code=status.HTTP_201_CREATED)
def generate_tasks_from_ai(
    project_id: int,
    body: GenerateTasksRequest,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Parse description + create all tasks in the project with dependencies.
    Returns list of created task ids.
    """
    p = project_repo.get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Projekt nenájdený")

    if len(body.description.strip()) < 10:
        raise HTTPException(status_code=400, detail="Popis projektu je príliš krátky")

    result = ai_parser.parse_project(body.description)
    tasks_data = result["tasks"]

    if not tasks_data:
        raise HTTPException(status_code=400, detail="AI neextrahoval žiadne úlohy")

    # Create tasks and track name → id mapping for dependency resolution
    name_to_id: dict[str, int] = {}
    created_ids: list[int] = []

    for t in tasks_data:
        task_id = task_repo.create_task(
            project_id=project_id,
            name=t["name"],
            assigned_to=None,
            created_by=current_user["id"],
        )
        task_repo.update_task_fields(task_id, {
            "duration": t["duration"],
            "description": t.get("description", ""),
            "priority": t.get("priority", "medium"),
        })
        name_to_id[t["name"]] = task_id
        created_ids.append(task_id)

    # Add dependencies
    deps_added = 0
    for t in tasks_data:
        task_id = name_to_id.get(t["name"])
        if not task_id:
            continue
        for dep_name in (t.get("dependencies") or []):
            dep_id = name_to_id.get(dep_name)
            if dep_id and dep_id != task_id:
                task_repo.add_dependency(task_id, dep_id)
                deps_added += 1

    # Recalculate CPM
    try:
        cpm_manager.recalculate(project_id)
    except Exception:
        pass

    return {
        "created_tasks": len(created_ids),
        "dependencies_added": deps_added,
        "task_ids": created_ids,
        "source": result.get("source", "unknown"),
        "detail": f"Vytvorených {len(created_ids)} úloh s {deps_added} závislosťami",
    }
