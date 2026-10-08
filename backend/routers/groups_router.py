"""Etapy projektu — GET/POST /projects/{id}/groups + PATCH/DELETE /groups/{id}

Skupina je prehľadová vrstva nad úlohami. Do CPM nevstupuje, takže žiadny
z týchto endpointov nespúšťa prepočet harmonogramu — zmena zaradenia úlohy
do etapy jej trvanie ani závislosti nemení.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import (
    get_current_user,
    require_manager_or_admin,
    assert_project_access,
)
from repositories import group_repo

router = APIRouter(tags=["groups"])


class GroupCreate(BaseModel):
    name: str
    task_ids: list[int] = []


class GroupUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TaskIds(BaseModel):
    task_ids: list[int]


def _assert_group_access(group_id: int, current_user: dict) -> dict:
    """Skupina nemá vlastné organization_id — príslušnosť dedí cez projekt."""
    group = group_repo.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Etapa nenájdená")
    assert_project_access(group["project_id"], current_user)
    return group


@router.get("/projects/{project_id}/groups")
def list_groups(project_id: int, current_user: dict = Depends(get_current_user)):
    """Etapy projektu aj s odvodeným postupom."""
    assert_project_access(project_id, current_user)
    return group_repo.get_groups_for_project(project_id)


@router.post("/projects/{project_id}/groups", status_code=status.HTTP_201_CREATED)
def create_group(
    project_id: int,
    body: GroupCreate,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Založí etapu a rovno do nej zaradí vybrané úlohy."""
    assert_project_access(project_id, current_user)
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Etapa musí mať názov")
    group_id = group_repo.create_group(project_id, body.name, body.task_ids)
    return {"id": group_id, "detail": "Etapa vytvorená"}


@router.patch("/groups/{group_id}")
def update_group(
    group_id: int,
    body: GroupUpdate,
    current_user: dict = Depends(require_manager_or_admin),
):
    _assert_group_access(group_id, current_user)
    if body.name is not None:
        if not body.name.strip():
            raise HTTPException(status_code=400, detail="Etapa musí mať názov")
        group_repo.rename_group(group_id, body.name)
    if body.color is not None:
        if body.color not in group_repo.PALETTE:
            raise HTTPException(
                status_code=400,
                detail=f"Neplatná farba. Platné: {', '.join(group_repo.PALETTE)}",
            )
        group_repo.set_color(group_id, body.color)
    return {"detail": "Etapa upravená"}


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Zruší etapu. Úlohy ostávajú, len sa vrátia medzi nezaradené."""
    _assert_group_access(group_id, current_user)
    group_repo.delete_group(group_id)


@router.post("/groups/{group_id}/tasks")
def add_tasks(
    group_id: int,
    body: TaskIds,
    current_user: dict = Depends(require_manager_or_admin),
):
    group = _assert_group_access(group_id, current_user)
    group_repo.assign_tasks(group["project_id"], group_id, body.task_ids)
    return {"detail": "Úlohy zaradené"}


@router.post("/projects/{project_id}/groups/ungroup")
def ungroup_tasks(
    project_id: int,
    body: TaskIds,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vyradí úlohy z ich etáp bez toho, aby etapy zanikli."""
    assert_project_access(project_id, current_user)
    group_repo.remove_tasks(project_id, body.task_ids)
    return {"detail": "Úlohy vyradené z etapy"}
