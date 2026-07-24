"""Autentifikácia — login, signup (nová organizácia), reset hesla, správa profilu."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from pydantic import BaseModel

from backend.auth import create_access_token
from backend.ratelimit import limiter
from backend.deps import (
    get_current_user,
    require_manager_or_admin,
    current_org_id,
    assert_can_add_user,
)
from logic.passwords import hash_password
from logic import mailer
from repositories import user_repo, org_repo, password_reset_repo

router = APIRouter(prefix="/auth", tags=["auth"])


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email or ""))


def _unique_username(email: str) -> str:
    """Odvodí interný username z e-mailu (username je globálne unikátny, e-mail je identita)."""
    base = re.sub(r"[^a-z0-9_.-]", "", email.split("@")[0].lower()) or "user"
    candidate = base
    n = 2
    while user_repo.username_exists(candidate):
        candidate = f"{base}{n}"
        n += 1
    return candidate


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
    email: str | None = None


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    """Prihlásenie cez e-mail ALEBO username + heslo (OAuth2 form). Vráti JWT."""
    user = user_repo.get_by_login_and_password(form.username, form.password)
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
        "org_id": user.get("organization_id"),
    })
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
    )


# ── Self-serve signup (nová organizácia + jej prvý admin) ────────────────────

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str
    organization_name: str


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def signup(request: Request, req: SignupRequest):
    """Verejná registrácia: založí NOVÚ organizáciu a v nej prvého používateľa ako admina.

    E-mail je login identita (globálne unikátny). Rovno vráti JWT, aby bol používateľ
    po registrácii prihlásený.
    """
    if not _valid_email(req.email):
        raise HTTPException(status_code=400, detail="Neplatný e-mail")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Heslo musí mať aspoň 8 znakov")
    if not req.organization_name.strip():
        raise HTTPException(status_code=400, detail="Názov organizácie je povinný")
    if user_repo.get_by_email(req.email):
        raise HTTPException(status_code=409, detail="Účet s týmto e-mailom už existuje")

    org_id = org_repo.create_organization(
        req.organization_name.strip(), org_repo.unique_slug(req.organization_name)
    )
    username = _unique_username(req.email)
    ok, msg = user_repo.create_user(
        username, hash_password(req.password), req.full_name.strip(), "admin", None, org_id,
        email=req.email.lower(),
    )
    if not ok:
        # Kompenzácia — signup nie je jedna transakcia, tak po zlyhaní usera
        # zmažeme práve vytvorenú organizáciu, nech neostane osirelá.
        org_repo.delete_organization(org_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user = user_repo.get_by_email(req.email)
    token = create_access_token({
        "id": user["id"], "username": user["username"],
        "role": user["role"], "org_id": org_id,
    })
    return TokenResponse(
        access_token=token, user_id=user["id"], username=user["username"],
        full_name=user["full_name"], role=user["role"],
    )


# ── Reset hesla (e-mailom) ───────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/forgot-password")
@limiter.limit("5/hour")
def forgot_password(request: Request, req: ForgotPasswordRequest):
    """Pošle e-mail s odkazom na reset hesla. Kvôli ochrane pred enumeráciou vždy
    vráti rovnakú odpoveď, bez ohľadu na to, či účet existuje."""
    user = user_repo.get_by_email(req.email) if _valid_email(req.email) else None
    if user:
        token = password_reset_repo.create_reset(user["id"])
        mailer.send_password_reset(req.email, token)
    return {"detail": "Ak účet s týmto e-mailom existuje, poslali sme naň odkaz na reset hesla."}


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
@limiter.limit("10/hour")
def reset_password(request: Request, req: ResetPasswordRequest):
    """Nastaví nové heslo podľa jednorazového resetovacieho tokenu."""
    from datetime import datetime, timezone

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Heslo musí mať aspoň 8 znakov")

    reset = password_reset_repo.get_reset(req.token)
    if not reset or reset.get("used_at"):
        raise HTTPException(status_code=400, detail="Neplatný alebo použitý odkaz")

    expires_raw = reset.get("expires_at")
    try:
        exp = datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            raise HTTPException(status_code=400, detail="Odkaz na reset vypršal")
    except HTTPException:
        raise
    except Exception:
        pass  # neparsovateľná expirácia — radšej povoliť než zamknúť

    user_repo.update_password(reset["user_id"], hash_password(req.new_password))
    password_reset_repo.mark_used(req.token)
    return {"detail": "Heslo bolo zmenené. Teraz sa môžeš prihlásiť."}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Vytvorenie používateľa. CHRÁNENÉ — len manager/admin.

    Onboarding externých používateľov ide cez /invites/{token}/accept (rola z pozvánky).
    Predtým bol tento endpoint verejný a bral ľubovoľnú rolu → ktokoľvek sa vedel
    spraviť adminom (privilege escalation). Teraz:
      - manager smie vytvárať len 'employee' a automaticky ich priradí pod seba,
      - iba admin smie vytvárať 'manager' alebo 'admin'.
    """
    requested_role = req.role if req.role in ("employee", "manager", "admin") else "employee"
    if requested_role in ("manager", "admin") and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Len admin môže vytvárať používateľov s rolou manager alebo admin",
        )
    if user_repo.username_exists(req.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Používateľ '{req.username}' už existuje",
        )
    if req.email and not _valid_email(req.email):
        raise HTTPException(status_code=400, detail="Neplatný e-mail")
    if req.email and user_repo.get_by_email(req.email):
        raise HTTPException(status_code=409, detail="Účet s týmto e-mailom už existuje")
    assert_can_add_user(current_user)
    manager_id = current_user["id"] if current_user.get("role") == "manager" else req.manager_id
    hashed = hash_password(req.password)
    # Nový používateľ vždy patrí do organizácie toho, kto ho vytvára.
    ok, msg = user_repo.create_user(
        req.username, hashed, req.full_name, requested_role, manager_id, current_org_id(current_user),
        email=(req.email.lower() if req.email else None),
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"detail": "Používateľ vytvorený"}


class MeResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    email: str | None = None
    bio: str | None = None
    avatar_color: str = "#6366f1"
    timezone: str = "Europe/Bratislava"


@router.get("/me", response_model=MeResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Vráti info o prihlásenom používateľovi vrátane profilu."""
    user = user_repo.get_by_username(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="Používateľ nenájdený")
    return MeResponse(
        id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        email=user.get("email"),
        bio=user.get("bio"),
        avatar_color=user.get("avatar_color") or "#6366f1",
        timezone=user.get("timezone") or "Europe/Bratislava",
    )


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    bio: str | None = None
    avatar_color: str | None = None
    timezone: str | None = None


@router.patch("/me/profile")
def update_profile(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    """Aktualizácia profilu — meno, bio, farba avatara, timezone."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return {"detail": "Nič na aktualizáciu"}
    user_repo.update_user_profile(current_user["id"], updates)
    return {"detail": "Profil aktualizovaný"}


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
    new_hashed = hash_password(body.new_password)
    user_repo.update_password(current_user["id"], new_hashed)
    return {"detail": "Heslo bolo zmenené"}
