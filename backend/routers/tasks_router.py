"""GET/POST /projects/{id}/tasks  +  PATCH/DELETE /tasks/{id}"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import (
    get_current_user,
    require_manager_or_admin,
    assert_project_access,
    assert_task_access,
)
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


# ── Validácia trvania ───────────────────────────────────────────────────────

def _validate_schedule(duration: int | None,
                       optimistic: int | None,
                       pessimistic: int | None) -> None:
    """Skontroluje trvanie a trojbodový odhad pred zápisom.

    `pert_engine` počíta σ = (b − a) / 6 a nič si neoveruje — je to čistá funkcia
    a kontrola vstupu patrí na hranicu API. Bez nej stačí zadať pesimistický odhad
    menší než optimistický a σ vyjde záporná, čo potichu rozbije celú analýzu.
    """
    if duration is not None and duration < 1:
        raise HTTPException(status_code=400, detail="Trvanie musí byť aspoň 1 deň")

    for label, value in (("Optimistický", optimistic), ("Pesimistický", pessimistic)):
        if value is not None and value < 1:
            raise HTTPException(status_code=400, detail=f"{label} odhad musí byť aspoň 1 deň")

    if optimistic is not None and pessimistic is not None and optimistic > pessimistic:
        raise HTTPException(
            status_code=400,
            detail="Optimistický odhad nemôže byť väčší než pesimistický",
        )
    if duration is not None:
        if optimistic is not None and optimistic > duration:
            raise HTTPException(
                status_code=400,
                detail="Optimistický odhad nemôže byť väčší než najpravdepodobnejšie trvanie",
            )
        if pessimistic is not None and pessimistic < duration:
            raise HTTPException(
                status_code=400,
                detail="Pesimistický odhad nemôže byť menší než najpravdepodobnejšie trvanie",
            )


# ── Endpointy ───────────────────────────────────────────────────────────────
# Poznámka: prístup ku konkrétnemu projektu/úlohe rieši assert_project_access /
# assert_task_access z backend.deps (kontrolujú vlastníctvo, nie len existenciu).

@router.get("/projects/{project_id}/tasks")
def list_tasks(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Zoznam úloh projektu vrátane CPM polí."""
    assert_project_access(project_id, current_user)
    return task_repo.get_tasks_for_project_with_cpm(project_id)


@router.post("/projects/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    body: TaskCreate,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vytvoriť úlohu v projekte. Po vytvorení spustí CPM prepočet."""
    assert_project_access(project_id, current_user)
    _validate_schedule(body.duration, body.duration_optimistic, body.duration_pessimistic)
    task_id = task_repo.create_task(
        project_id=project_id,
        name=body.name,
        assigned_to=body.assigned_to,
        created_by=current_user["id"],
        due_date=body.due_date,
    )
    # Aktualizuj ďalšie polia.
    # duration_optimistic/pessimistic sem musia patriť tiež — formulár na vytvorenie
    # úlohy ich posiela a bez nich by sa ticho zahodili, takže PERT by nemal z čoho
    # počítať, kým používateľ úlohu znova neotvorí a neuloží.
    task_repo.update_task_fields(task_id, {
        "priority": body.priority,
        "duration": body.duration,
        "description": body.description,
        "category": body.category,
        "estimated_hours": body.estimated_hours,
        "duration_optimistic": body.duration_optimistic,
        "duration_pessimistic": body.duration_pessimistic,
        "auto_notify": body.auto_notify,
        "auto_calendar": body.auto_calendar,
    })
    cpm_manager.recalculate(project_id)  # loguje chyby interne, nezhodí request
    return {"id": task_id, "detail": "Úloha vytvorená"}


@router.post("/projects/{project_id}/recalculate-cpm")
def recalculate_cpm(
    project_id: int,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vynúti prepočet CPM pre celý projekt — užitočné po hromadných zmenách alebo
    po importe starých dát (ktoré mohli mať zastaralé CPM hodnoty)."""
    assert_project_access(project_id, current_user)
    result = cpm_manager.recalculate(project_id)
    if result is None:
        return {"ok": False, "detail": "CPM prepočet zlyhal — pozri logy servera"}
    return {
        "ok": True,
        "detail": "CPM bolo prepočítané",
        "project_duration": result.project_duration,
        "critical_tasks": len(result.critical_path),
        "is_valid": result.is_valid,
    }


@router.get("/tasks/{task_id}")
def get_task_detail(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Full task detail — used by TaskDetailModal."""
    return assert_task_access(task_id, current_user)


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    body: TaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Aktualizovať úlohu (status, assignee, dátumy, trvanie...). Spustí CPM prepočet."""
    assert_task_access(task_id, current_user)

    sent = body.model_dump(exclude_unset=True)
    updates = {k: v for k, v in sent.items() if v is not None}

    # Odhady sa musia dať aj odstrániť. Pri nich preto rozlišujeme „neposlané"
    # od „poslané ako null" — pri ostatných poliach ostáva pôvodné správanie,
    # kde None znamená „nemeň".
    clears = [k for k in ("duration_optimistic", "duration_pessimistic")
              if k in sent and sent[k] is None]

    if not updates and not clears:
        return {"detail": "Nič na aktualizáciu"}

    current = task_repo.get_task_by_id(task_id)
    if not current:
        raise HTTPException(status_code=404, detail="Úloha neexistuje")

    # Trvanie a odhady prepisujú harmonogram celého projektu, nielen jednu úlohu —
    # meniť ich smie len manažér alebo admin. Ostatné polia ostávajú ako doteraz.
    schedule_fields = {"duration", "duration_optimistic", "duration_pessimistic"}
    if schedule_fields & (updates.keys() | set(clears)) and current_user.get("role") not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trvanie úlohy môže meniť len manager alebo admin",
        )

    # Validuj proti VÝSLEDNÉMU stavu — pri čiastočnej zmene (napr. len pesimistický
    # odhad) sa musí porovnať s hodnotami, ktoré už v úlohe sú.
    def _effective(field: str):
        if field in clears:
            return None
        return updates.get(field, current.get(field))

    _validate_schedule(
        _effective("duration"),
        _effective("duration_optimistic"),
        _effective("duration_pessimistic"),
    )

    if "status" in updates:
        task_repo.update_task_status(task_id, updates.pop("status"))

    if updates:
        task_repo.update_task_fields(task_id, updates)

    if clears:
        task_repo.clear_task_fields(task_id, clears)

    # CPM prepočet — es/ef/ls/lf/total_float/is_critical sú uložené v DB, takže po
    # zmene trvania ich treba prepísať. PERT, rizikové skóre aj Gantt sa počítajú
    # až pri čítaní, tie sa dotiahnu samy.
    cpm_manager.recalculate(current["project_id"])

    return {"detail": "Úloha aktualizovaná"}


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vymazať úlohu."""
    assert_task_access(task_id, current_user)
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

    assert_project_access(project_id, current_user)
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
    assert_project_access(project_id, current_user)
    return task_repo.get_all_dependencies_for_project(project_id)


@router.get("/tasks/{task_id}/dependencies")
def get_dependencies(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Zoznam závislostí úlohy."""
    assert_task_access(task_id, current_user)
    return task_repo.get_dependencies(task_id)


@router.post("/tasks/{task_id}/dependencies", status_code=status.HTTP_201_CREATED)
def add_dependency(
    task_id: int,
    depends_on: int,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Pridať závislosť úlohy."""
    assert_task_access(task_id, current_user)
    task_repo.add_dependency(task_id, depends_on)
    task = task_repo.get_task_by_id(task_id)
    if task:
        cpm_manager.recalculate(task["project_id"])
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

    assert_project_access(project_id, current_user)
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
    assert_task_access(task_id, current_user)
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
    assert_task_access(task_id, current_user)
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
    assert_project_access(project_id, current_user)
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
    assert_project_access(project_id, current_user)
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
