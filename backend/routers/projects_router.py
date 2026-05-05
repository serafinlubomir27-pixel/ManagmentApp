"""GET/POST /projects  +  GET/PATCH/DELETE /projects/{id}"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_manager_or_admin
from repositories import project_repo, task_repo

router = APIRouter(prefix="/projects", tags=["projects"])


# ── Pydantic modely ─────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    status: str = "active"
    is_template: bool = False


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


# ── Endpointy ───────────────────────────────────────────────────────────────

@router.get("/")
def list_projects(current_user: dict = Depends(get_current_user)):
    """Zoznam projektov pre prihláseného používateľa."""
    return project_repo.get_user_projects(current_user["id"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vytvoriť nový projekt. Vyžaduje manager alebo admin."""
    project_id = project_repo.create_project(
        user_id=current_user["id"],
        name=body.name,
        description=body.description,
        status=body.status,
        is_template=body.is_template,
    )
    return {"id": project_id, "detail": "Projekt vytvorený"}


@router.get("/{project_id}")
def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Detail jedného projektu."""
    project = project_repo.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenájdený")
    return project


@router.patch("/{project_id}")
def update_project(
    project_id: int,
    body: ProjectUpdate,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Aktualizovať stav / názov projektu."""
    project = project_repo.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenájdený")
    if body.status:
        project_repo.update_project_status(project_id, body.status)
    return {"detail": "Projekt aktualizovaný"}


@router.get("/templates/list")
def list_templates(current_user: dict = Depends(get_current_user)):
    """Šablóny projektov vlastnené aktuálnym používateľom."""
    return project_repo.get_templates(current_user["id"])


@router.get("/portfolio/overview")
def get_portfolio_overview(current_user: dict = Depends(get_current_user)):
    """Portfolio overview — aggregated health data across all user's projects."""
    from collections import defaultdict
    from datetime import date

    projects = project_repo.get_user_projects(current_user["id"])
    if not projects:
        return {"projects": [], "summary": {"total": 0, "active": 0, "at_risk": 0, "completed": 0}}

    today = date.today().isoformat()
    enriched = []
    total_tasks_all = 0
    total_completed_all = 0
    at_risk_count = 0

    for p in projects:
        tasks = task_repo.get_tasks_for_project_with_cpm(p["id"])
        total = len(tasks)
        completed = sum(1 for t in tasks if t["status"] == "completed")
        in_progress = sum(1 for t in tasks if t["status"] == "in_progress")
        blocked = sum(1 for t in tasks if t["status"] == "blocked")
        critical = sum(1 for t in tasks if t.get("is_critical"))

        # Overdue tasks
        overdue = sum(
            1 for t in tasks
            if t.get("due_date") and t["due_date"] <= today and t["status"] != "completed"
        )

        progress = completed / total if total > 0 else 0.0

        # Health score (0-100):
        # - 40 pts: progress (% completed)
        # - 30 pts: no blocked tasks
        # - 30 pts: no overdue tasks
        health = round(
            40 * progress +
            30 * (max(0, 1 - blocked / max(total, 1))) +
            30 * (max(0, 1 - overdue / max(total, 1)))
        )

        # CPM duration
        project_duration = max((t.get("ef") or 0 for t in tasks), default=0)

        is_at_risk = (overdue > 0 or blocked > 0 or health < 50) and p["status"] == "active"
        if is_at_risk:
            at_risk_count += 1

        total_tasks_all += total
        total_completed_all += completed

        enriched.append({
            **p,
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "blocked_tasks": blocked,
            "critical_tasks": critical,
            "overdue_tasks": overdue,
            "progress": round(progress, 3),
            "health_score": health,
            "project_duration": project_duration,
            "is_at_risk": is_at_risk,
        })

    # Sort: at-risk first, then by health ascending (worst first)
    enriched.sort(key=lambda p: (not p["is_at_risk"], p["health_score"]))

    return {
        "projects": enriched,
        "summary": {
            "total": len(projects),
            "active": sum(1 for p in projects if p["status"] == "active"),
            "completed": sum(1 for p in projects if p["status"] == "completed"),
            "at_risk": at_risk_count,
            "total_tasks": total_tasks_all,
            "total_completed": total_completed_all,
            "overall_progress": round(total_completed_all / total_tasks_all, 3) if total_tasks_all > 0 else 0.0,
        },
    }
