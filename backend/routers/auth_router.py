"""POST /auth/login  — prihlásenie, vydanie JWT tokenu."""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from pydantic import BaseModel

from backend.auth import create_access_token
from repositories import user_repo

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    role: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "employee"
    manager_id: int | None = None


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Prihlásenie cez username + password (OAuth2 form). Vráti JWT."""
    user = user_repo.get_by_username_and_password(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávne meno alebo heslo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    })
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    """Registrácia nového používateľa (verejná — pre onboarding)."""
    if user_repo.username_exists(req.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Používateľ '{req.username}' už existuje",
        )
    hashed = hashlib.sha256(req.password.encode()).hexdigest()
    ok, msg = user_repo.create_user(
        req.username, hashed, req.full_name, req.role, req.manager_id
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"detail": "Používateľ vytvorený"}
