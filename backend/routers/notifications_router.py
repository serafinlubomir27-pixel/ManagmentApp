"""Notifications endpoints — mounted at /notifications prefix.

GET   /notifications                    — current user's notifications (last 20)
PATCH /notifications/{id}/read          — mark one as read
PATCH /notifications/read-all           — mark all as read
POST  /notifications/check-deadlines    — scan tasks and create deadline warnings
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.deps import get_current_user
from repositories import notification_repo

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
def get_notifications(
    current_user: dict = Depends(get_current_user),
):
    """Vráti posledných 20 notifikácií aktuálneho používateľa (neprečítané ako prvé)."""
    return notification_repo.get_user_notifications(user_id=current_user["id"], limit=20)


@router.patch("/notifications/read-all")
def mark_all_read(
    current_user: dict = Depends(get_current_user),
):
    """Označí všetky notifikácie aktuálneho používateľa ako prečítané."""
    count = notification_repo.mark_all_read(user_id=current_user["id"])
    return {"detail": f"Označených {count} notifikácií ako prečítaných"}


@router.patch("/notifications/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Označí konkrétnu notifikáciu ako prečítanú."""
    notification_repo.mark_read(
        notification_id=notification_id,
        user_id=current_user["id"],
    )
    return {"detail": "Notifikácia označená ako prečítaná"}


@router.post("/notifications/check-deadlines")
def check_deadlines(
    current_user: dict = Depends(get_current_user),
):
    """Interný endpoint: prechádza úlohy a vytvára deadline_warning notifikácie."""
    created = notification_repo.check_and_create_deadline_notifications(days_ahead=[1, 3, 7])
    return {"detail": f"Vytvorených {created} nových notifikácií o deadlinoch"}
