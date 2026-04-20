"""POST /auth/login  — prihlásenie, vydanie JWT tokenu."""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from pydantic import BaseModel

from backend.auth import create_access_token
from backend.deps import get_current_user
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


class MeResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str


@router.get("/me", response_model=MeResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Vráti info o prihlásenom používateľovi."""
    user = user_repo.get_by_username(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="Používateľ nenájdený")
    return MeResponse(**{k: user[k] for k in ("id", "username", "full_name", "role")})


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.patch("/me/password")
def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """Zmena vlastného hesla. Vyžaduje zadanie starého hesla."""
    user = user_repo.get_by_username_and_password(
        current_user["username"], body.current_password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nesprávne aktuálne heslo",
        )
    new_hashed = hashlib.sha256(body.new_password.encode()).hexdigest()
    user_repo.update_password(current_user["id"], new_hashed)
    return {"detail": "Heslo bolo zmenené"}
