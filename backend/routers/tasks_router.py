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
    duration_optimistic: int | None = None
    duration_pessimistic: int | None = None


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
    duration_optimistic: int | None = None
    duration_pessimistic: int | None = None


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
    return task_repo.get_all_dependencies_for_project(project_id)


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


@router.get("/projects/{project_id}/pert")
def get_pert_analysis(
    project_id: int,
    deadline: int | None = None,
    current_user: dict = Depends(get_current_user),
):
    """PERT analýza projektu — pravdepodobnostné CPM."""
    from logic.pert_engine import calculate_pert
    from logic.cpm_engine import CPMTask

    _project_or_404(project_id)
    tasks = task_repo.get_tasks_with_pert(project_id)
    deps = task_repo.get_all_dependencies_for_project(project_id)

    if not tasks:
        return {"pert_tasks": [], "project_expected_duration": 0, "project_std_dev": 0,
                "probability_by_deadline": {}, "critical_path_ids": []}

    dep_map: dict[int, list[int]] = {}
    for d in deps:
        dep_map.setdefault(d["task_id"], []).append(d["depends_on_task_id"])

    cpm_tasks = [
        CPMTask(
            id=t["id"],
            name=t["name"],
            duration=t["duration"],
            dependencies=dep_map.get(t["id"], []),
            delay_days=t.get("delay_days", 0),
            status=t.get("status", "pending"),
        )
        for t in tasks
    ]

    pert_data = {}
    for t in tasks:
        a = t.get("duration_optimistic") or t["duration"]
        b = t.get("duration_pessimistic") or t["duration"]
        m = t["duration"]
        if a != m or b != m:
            pert_data[t["id"]] = (float(a), float(m), float(b))

    result = calculate_pert(cpm_tasks, pert_data, deadline)

    return {
        "pert_tasks": [
            {
                "task_id": pt.task_id,
                "name": pt.name,
                "duration_optimistic": pt.duration_optimistic,
                "duration_likely": pt.duration_likely,
                "duration_pessimistic": pt.duration_pessimistic,
                "pert_expected": pt.pert_expected,
                "pert_std_dev": pt.pert_std_dev,
                "pert_variance": pt.pert_variance,
                "is_critical": pt.is_critical,
            }
            for pt in result.pert_tasks
        ],
        "critical_path_ids": result.critical_path_ids,
        "project_expected_duration": result.project_expected_duration,
        "project_std_dev": result.project_std_dev,
        "project_variance": result.project_variance,
        "probability_by_deadline": result.probability_by_deadline,
        "cpm_duration": result.cpm_result.project_duration,
    }


@router.get("/projects/{project_id}/resources")
def get_resource_allocation(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Resource allocation — vyťaženosť členov tímu v čase (podľa CPM ES/EF)."""
    _project_or_404(project_id)
    tasks = task_repo.get_tasks_for_project_with_cpm(project_id)

    # Filtrovanie — len priradené úlohy s platným CPM rozpisem
    assigned = [
        t for t in tasks
        if t.get("assigned_to") and t.get("ef", 0) > t.get("es", 0)
    ]

    if not assigned:
        return {"people": [], "project_duration": 0, "over_allocated_days": 0}

    project_duration = max(t["ef"] for t in tasks if t.get("ef"))

    # Skupiny podľa osoby
    from collections import defaultdict
    person_tasks: dict[int, list[dict]] = defaultdict(list)
    person_info: dict[int, dict] = {}

    for t in assigned:
        uid = t["assigned_to"]
        person_tasks[uid].append(t)
        if uid not in person_info:
            person_info[uid] = {
                "user_id": uid,
                "username": t.get("assigned_username") or f"user_{uid}",
            }

    people = []
    total_over_allocated_days = 0

    for uid, p_tasks in person_tasks.items():
        # Day-by-day load: day → list of task names
        day_load: dict[int, list[str]] = defaultdict(list)
        for t in p_tasks:
            for day in range(t["es"], t["ef"]):
                day_load[day].append(t["name"])

        over_days = [d for d, names in day_load.items() if len(names) > 1]
        total_over_allocated_days += len(over_days)

        # Task summary per person
        task_summary = [
            {
                "id": t["id"],
                "name": t["name"],
                "es": t["es"],
                "ef": t["ef"],
                "duration": t["duration"],
                "status": t["status"],
                "is_critical": t["is_critical"],
            }
            for t in sorted(p_tasks, key=lambda x: x["es"])
        ]

        # Daily load array (0..project_duration-1)
        daily = [len(day_load.get(d, [])) for d in range(project_duration)]

        people.append({
            **person_info[uid],
            "tasks": task_summary,
            "task_count": len(p_tasks),
            "over_allocated_days": len(over_days),
            "peak_load": max(daily) if daily else 0,
            "daily_load": daily,
        })

    # Zoraď podľa mena
    people.sort(key=lambda p: p["username"])

    return {
        "people": people,
        "project_duration": project_duration,
        "over_allocated_days": total_over_allocated_days,
        "total_assigned_tasks": len(assigned),
    }
