"""Comments endpoints — mounted at /tasks prefix.

GET    /tasks/{task_id}/comments   — list comments for a task
POST   /tasks/{task_id}/comments   — create comment (auth required)
DELETE /comments/{comment_id}      — delete own comment (auth required)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user
from repositories import comment_repo, task_repo

router = APIRouter(tags=["comments"])


class CommentCreate(BaseModel):
    content: str


def _task_or_404(task_id: int):
    t = task_repo.get_task_status_and_name(task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Úloha nenájdená")
    return t


@router.get("/tasks/{task_id}/comments")
def list_comments(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Zoznam komentárov pre danú úlohu."""
    _task_or_404(task_id)
    return comment_repo.get_comments_for_task(task_id)


@router.post("/tasks/{task_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(
    task_id: int,
    body: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    """Pridať komentár k úlohe."""
    _task_or_404(task_id)
    if not body.content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Komentár nesmie byť prázdny")
    comment = comment_repo.create_comment(
        task_id=task_id,
        user_id=current_user["id"],
        content=body.content.strip(),
    )
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Zmazať vlastný komentár."""
    deleted = comment_repo.delete_comment(
        comment_id=comment_id,
        user_id=current_user["id"],
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Komentár neexistuje alebo nie je váš",
        )
