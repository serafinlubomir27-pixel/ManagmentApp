"""GET/POST /projects/{id}/tasks  +  PATCH/DELETE /tasks/{id}"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_manager_or_admin
from repositories import task_repo, project_repo, time_repo
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
    auto_notify: bool = True
    auto_calendar: bool = True


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
    auto_notify: bool | None = None
    auto_calendar: bool | None = None


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
    # Aktualizuj ďalšie polia
    task_repo.update_task_fields(task_id, {
        "priority": body.priority,
        "duration": body.duration,
        "description": body.description,
        "category": body.category,
        "estimated_hours": body.estimated_hours,
        "auto_notify": body.auto_notify,
        "auto_calendar": body.auto_calendar,
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


@router.get("/projects/{project_id}/risk-score")
def get_risk_score(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Composite AI risk score (0-100) for a project.

    Components:
      - PERT schedule uncertainty (40 %): 1 – P(finish by CPM deadline)
      - Overdue task ratio (35 %): overdue / total
      - Resource over-allocation (25 %): over-allocated days / project duration
    """
    from collections import defaultdict
    from datetime import date
    from logic.pert_engine import calculate_pert
    from logic.cpm_engine import CPMTask

    _project_or_404(project_id)
    tasks = task_repo.get_tasks_for_project_with_cpm(project_id)

    if not tasks:
        return {"risk_score": 0, "level": "none", "components": {}, "meta": {}}

    today = date.today().isoformat()
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "completed")

    # ── Component 1: Overdue ratio ────────────────────────────────────────────
    overdue = sum(
        1 for t in tasks
        if t.get("due_date") and t["due_date"] <= today and t["status"] != "completed"
    )
    overdue_ratio = overdue / total if total > 0 else 0.0

    # ── Component 2: Resource over-allocation ─────────────────────────────────
    project_duration = max((t.get("ef") or 0 for t in tasks), default=1) or 1

    assigned = [
        t for t in tasks
        if t.get("assigned_to") and (t.get("ef") or 0) > (t.get("es") or 0)
    ]
    day_load: dict[int, list] = defaultdict(list)
    for t in assigned:
        for day in range(t["es"], t["ef"]):
            day_load[day].append(t["id"])

    over_allocated_days = sum(1 for v in day_load.values() if len(v) > 1)
    resource_ratio = min(1.0, over_allocated_days / project_duration)

    # ── Component 3: PERT schedule uncertainty ────────────────────────────────
    pert_tasks_raw = task_repo.get_tasks_with_pert(project_id)
    deps = task_repo.get_all_dependencies_for_project(project_id)

    dep_map: dict[int, list[int]] = {}
    for d in deps:
        dep_map.setdefault(d["task_id"], []).append(d["depends_on_task_id"])

    cpm_tasks_list = [
        CPMTask(
            id=t["id"],
            name=t["name"],
            duration=t["duration"],
            dependencies=dep_map.get(t["id"], []),
            delay_days=t.get("delay_days", 0),
            status=t.get("status", "pending"),
        )
        for t in pert_tasks_raw
    ]

    pert_data: dict[int, tuple[float, float, float]] = {}
    for t in pert_tasks_raw:
        a = t.get("duration_optimistic") or t["duration"]
        b = t.get("duration_pessimistic") or t["duration"]
        m = t["duration"]
        if a != m or b != m:
            pert_data[t["id"]] = (float(a), float(m), float(b))

    pert_risk = 0.3          # default: moderate uncertainty
    pert_details: dict = {}

    if cpm_tasks_list:
        try:
            result = calculate_pert(cpm_tasks_list, pert_data, None)
            E = result.project_expected_duration
            sigma = result.project_std_dev
            cpm_dur = result.cpm_result.project_duration

            # P(T ≤ CPM duration) — risk is 1 minus that
            if sigma > 0:
                from statistics import NormalDist
                prob_on_time = NormalDist(mu=E, sigma=sigma).cdf(cpm_dur)
            else:
                prob_on_time = 1.0 if cpm_dur >= E else 0.0

            pert_risk = 1.0 - prob_on_time
            pert_details = {
                "expected_duration": round(E, 2),
                "std_dev": round(sigma, 2),
                "cpm_duration": cpm_dur,
                "prob_on_time": round(prob_on_time, 4),
            }
        except Exception:
            pass  # keep default

    # ── Composite weighted score ──────────────────────────────────────────────
    raw = 0.40 * pert_risk + 0.35 * overdue_ratio + 0.25 * resource_ratio
    risk_score = min(100, round(raw * 100))

    if risk_score < 25:
        level = "low"
    elif risk_score < 50:
        level = "medium"
    elif risk_score < 75:
        level = "high"
    else:
        level = "critical"

    return {
        "risk_score": risk_score,
        "level": level,
        "components": {
            "pert_risk": round(pert_risk, 4),
            "overdue_ratio": round(overdue_ratio, 4),
            "resource_ratio": round(resource_ratio, 4),
            "overdue_tasks": overdue,
            "over_allocated_days": over_allocated_days,
            **pert_details,
        },
        "meta": {
            "total_tasks": total,
            "completed_tasks": completed,
            "project_duration": project_duration,
        },
    }


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


@router.get("/tasks/{task_id}/time")
def get_time_logs(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Return all time logs for a task."""
    _task_or_404(task_id)
    logs = time_repo.get_time_logs_for_task(task_id)
    total = time_repo.get_total_logged_hours(task_id)
    return {"logs": logs, "total_hours": total}


class TimeLogCreate(BaseModel):
    hours: float
    log_date: str       # ISO "2026-05-10"
    note: str = ""


@router.post("/tasks/{task_id}/time", status_code=status.HTTP_201_CREATED)
def log_time(
    task_id: int,
    body: TimeLogCreate,
    current_user: dict = Depends(get_current_user),
):
    """Log time spent on a task."""
    _task_or_404(task_id)
    if body.hours <= 0:
        raise HTTPException(status_code=400, detail="Hodiny musia byť kladné číslo")
    log_id = time_repo.log_time(task_id, current_user["id"], body.hours, body.log_date, body.note)
    return {"id": log_id, "detail": "Čas zaznamenaný"}


@router.delete("/time-logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_time_log(
    log_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete own time log entry."""
    deleted = time_repo.delete_time_log(log_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Záznam nenájdený alebo nie je tvoj")


@router.get("/projects/{project_id}/time-summary")
def get_project_time_summary(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Time tracking summary per task for a project (estimated vs logged)."""
    _project_or_404(project_id)
    return time_repo.get_time_summary_for_project(project_id)


@router.get("/me/calendar")
def get_my_calendar_tasks(
    current_user: dict = Depends(get_current_user),
):
    """Všetky úlohy s due_date pre aktuálneho používateľa (priradené alebo v jeho projektoch)."""
    tasks = task_repo.get_tasks_with_due_dates(current_user["id"])
    return {"tasks": tasks}


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
