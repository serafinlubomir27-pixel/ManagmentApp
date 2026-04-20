"""GET/POST /projects/{id}/tasks  +  PATCH/DELETE /tasks/{id}"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_manager_or_admin
from repositories import task_repo, project_repo
from logic import cpm_manager

router = APIRouter(tags=["tasks"])


# ── Pydantic modely ─────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    name: str
    assigned_to: int | None = None
    due_date: str | None = None          # ISO 8601: "2026-05-01"
    priority: str = "medium"
    estimated_hours: float | None = None
    duration: int = 1
    description: str = ""
    category: str = ""


class TaskUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    assigned_to: int | None = None
    due_date: str | None = None
    priority: str | None = None
    duration: int | None = None
    delay_days: int | None = None
    description: str | None = None
    category: str | None = None


# ── Pomocná funkcia ──────────────────────────────────────────────────────────

def _project_or_404(project_id: int):
    p = project_repo.get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenájdený")
    return p


def _task_or_404(task_id: int):
    t = task_repo.get_task_status_and_name(task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Úloha nenájdená")
    return t


# ── Endpointy ───────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/tasks")
def list_tasks(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Zoznam úloh projektu vrátane CPM polí."""
    _project_or_404(project_id)
    return task_repo.get_tasks_for_project_with_cpm(project_id)


@router.post("/projects/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    body: TaskCreate,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vytvoriť úlohu v projekte. Po vytvorení spustí CPM prepočet."""
    _project_or_404(project_id)
    task_id = task_repo.create_task(
        project_id=project_id,
        name=body.name,
        assigned_to=body.assigned_to,
        created_by=current_user["id"],
        due_date=body.due_date,
    )
    # Aktualizuj ďalšie polia ak sú zadané
    if any([body.priority != "medium", body.duration != 1, body.description, body.category, body.estimated_hours]):
        task_repo.update_task_fields(task_id, {
            "priority": body.priority,
            "duration": body.duration,
            "description": body.description,
            "category": body.category,
            "estimated_hours": body.estimated_hours,
        })
    # CPM prepočet
    try:
        cpm_manager.recalculate(project_id)
    except Exception:
        pass  # CPM chyba neblokuje odpoveď
    return {"id": task_id, "detail": "Úloha vytvorená"}


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    body: TaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Aktualizovať úlohu (status, assignee, dátumy...). Spustí CPM prepočet."""
    _task_or_404(task_id)

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return {"detail": "Nič na aktualizáciu"}

    if "status" in updates:
        task_repo.update_task_status(task_id, updates.pop("status"))

    if updates:
        task_repo.update_task_fields(task_id, updates)

    # CPM prepočet — zistíme project_id z task
    task = task_repo.get_task_by_id(task_id)
    if task:
        try:
            cpm_manager.recalculate(task["project_id"])
        except Exception:
            pass

    return {"detail": "Úloha aktualizovaná"}


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vymazať úlohu."""
    _task_or_404(task_id)
    task_repo.delete_task(task_id)


@router.get("/projects/{project_id}/dependencies")
def get_project_dependencies(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Všetky závislosti úloh v projekte (pre sieťový diagram)."""
    _project_or_404(project_id)
    return task_repo.get_project_dependencies(project_id)


@router.get("/tasks/{task_id}/dependencies")
def get_dependencies(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Zoznam závislostí úlohy."""
    _task_or_404(task_id)
    return task_repo.get_dependencies(task_id)


@router.post("/tasks/{task_id}/dependencies", status_code=status.HTTP_201_CREATED)
def add_dependency(
    task_id: int,
    depends_on: int,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Pridať závislosť úlohy."""
    _task_or_404(task_id)
    task_repo.add_dependency(task_id, depends_on)
    task = task_repo.get_task_by_id(task_id)
    if task:
        try:
            cpm_manager.recalculate(task["project_id"])
        except Exception:
            pass
    return {"detail": "Závislosť pridaná"}
