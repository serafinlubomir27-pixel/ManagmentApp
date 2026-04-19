"""GET /team  +  tímová hierarchia, workload."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_admin, require_manager_or_admin
from repositories import user_repo, task_repo
from logic.hierarchy import get_full_tree

router = APIRouter(prefix="/team", tags=["team"])


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    manager_id: int | None = None


@router.get("/")
def get_my_team(current_user: dict = Depends(get_current_user)):
    """Priami podriadení aktuálneho používateľa."""
    return user_repo.get_team_by_manager(current_user["id"])


@router.get("/all")
def get_all_users(current_user: dict = Depends(require_admin)):
    """Všetci používatelia v systéme. Len pre admin."""
    return user_repo.get_all_users()


@router.get("/tree")
def get_hierarchy_tree(current_user: dict = Depends(require_manager_or_admin)):
    """Celý strom hierarchie pod aktuálnym manažérom/adminom (BFS)."""
    return get_full_tree(current_user["id"])


@router.get("/{user_id}/workload")
def get_workload(
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Vyťaženie používateľa — počty úloh podľa statusu."""
    user = user_repo.get_username_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Používateľ nenájdený")
    return task_repo.get_workload_for_user(user_id)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    current_user: dict = Depends(require_admin),
):
    """Aktualizovať rolu alebo manažéra používateľa. Len admin."""
    user = user_repo.get_username_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Používateľ nenájdený")
    if body.role:
        user_repo.update_user_role(user_id, body.role)
    if body.manager_id is not None:
        user_repo.update_user_manager(user_id, body.manager_id)
    return {"detail": "Používateľ aktualizovaný"}
