"""Endpoints for file attachments on tasks and projects."""
from __future__ import annotations

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from backend.deps import get_current_user
from repositories import attachment_repo, project_repo, task_repo

router = APIRouter(tags=["attachments"])

# ── Upload directory ───────────────────────────────────────────────────────────

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(_PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_VISIBILITY = {"team", "managers", "private"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _save_file(upload: UploadFile) -> tuple[str, str, int, str]:
    """Save uploaded file to UPLOAD_DIR. Returns (unique_name, url_path, size, mime)."""
    ext = os.path.splitext(upload.filename or "file")[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, unique_name)
    size = 0
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
        size = f.tell()
    return unique_name, f"/uploads/{unique_name}", size, upload.content_type or "application/octet-stream"


# ── Project attachments ────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_project_attachment(
    project_id: int,
    file: UploadFile = File(...),
    visibility: str = Form("team"),
    current_user: dict = Depends(get_current_user),
):
    if not project_repo.get_project_by_id(project_id):
        raise HTTPException(404, "Projekt nenájdený")
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")

    _, url_path, size, mime = _save_file(file)
    att_id = attachment_repo.add_project_attachment(
        project_id=project_id,
        user_id=current_user["id"],
        file_name=file.filename or "file",
        file_path=url_path,
        file_size=size,
        mime_type=mime,
        visibility=visibility,
    )
    return {"id": att_id, "detail": "Súbor nahraný"}


@router.get("/projects/{project_id}/attachments")
def list_project_attachments(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    if not project_repo.get_project_by_id(project_id):
        raise HTTPException(404, "Projekt nenájdený")
    return attachment_repo.get_project_attachments(
        project_id, current_user["role"], current_user["id"]
    )


@router.get("/projects/{project_id}/all-attachments")
def list_all_project_attachments(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Combined view: project files + all task files in one response."""
    if not project_repo.get_project_by_id(project_id):
        raise HTTPException(404, "Projekt nenájdený")
    return attachment_repo.get_all_attachments_for_project(
        project_id, current_user["role"], current_user["id"]
    )


@router.patch("/project-attachments/{attachment_id}/visibility")
def update_project_attachment_visibility(
    attachment_id: int,
    visibility: str,
    current_user: dict = Depends(get_current_user),
):
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")
    updated = attachment_repo.update_project_attachment_visibility(
        attachment_id, visibility, current_user["id"]
    )
    if not updated:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    return {"detail": "Viditeľnosť aktualizovaná"}


@router.delete("/project-attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_attachment(
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
):
    file_path = attachment_repo.delete_project_attachment(
        attachment_id, current_user["id"], current_user["role"]
    )
    if file_path is None:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    # Remove physical file
    abs_path = os.path.join(_PROJECT_ROOT, file_path.lstrip("/"))
    if os.path.exists(abs_path):
        os.remove(abs_path)


# ── Task attachments ───────────────────────────────────────────────────────────

@router.post("/tasks/{task_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_task_attachment(
    task_id: int,
    file: UploadFile = File(...),
    visibility: str = Form("team"),
    current_user: dict = Depends(get_current_user),
):
    if not task_repo.get_task_by_id(task_id):
        raise HTTPException(404, "Úloha nenájdená")
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")

    _, url_path, size, mime = _save_file(file)
    att_id = attachment_repo.add_task_attachment(
        task_id=task_id,
        user_id=current_user["id"],
        file_name=file.filename or "file",
        file_path=url_path,
        file_size=size,
        mime_type=mime,
        visibility=visibility,
    )
    return {"id": att_id, "detail": "Súbor nahraný"}


@router.get("/tasks/{task_id}/attachments")
def list_task_attachments(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    if not task_repo.get_task_by_id(task_id):
        raise HTTPException(404, "Úloha nenájdená")
    return attachment_repo.get_task_attachments(
        task_id, current_user["role"], current_user["id"]
    )


@router.patch("/task-attachments/{attachment_id}/visibility")
def update_task_attachment_visibility(
    attachment_id: int,
    visibility: str,
    current_user: dict = Depends(get_current_user),
):
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")
    updated = attachment_repo.update_task_attachment_visibility(
        attachment_id, visibility, current_user["id"]
    )
    if not updated:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    return {"detail": "Viditeľnosť aktualizovaná"}


@router.delete("/task-attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_attachment(
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
):
    file_path = attachment_repo.delete_task_attachment(
        attachment_id, current_user["id"], current_user["role"]
    )
    if file_path is None:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    abs_path = os.path.join(_PROJECT_ROOT, file_path.lstrip("/"))
    if os.path.exists(abs_path):
        os.remove(abs_path)
