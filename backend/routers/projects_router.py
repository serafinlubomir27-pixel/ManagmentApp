"""GET/POST /projects  +  GET/PATCH/DELETE /projects/{id}"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_manager_or_admin
from repositories import project_repo

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
