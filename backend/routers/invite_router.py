"""Team invitation system.

POST   /invites           — create new invite token (manager/admin only)
GET    /invites           — list my invite tokens
DELETE /invites/{id}      — revoke an invite
GET    /invites/{token}/info — public: get invite info (role, valid/expired)
POST   /invites/{token}/accept — public: register via invite link
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_manager_or_admin
from repositories import invite_repo, user_repo

router = APIRouter(tags=["invites"])


# ── Pydantic models ──────────────────────────────────────────────────────────

class CreateInviteRequest(BaseModel):
    role: str = "employee"  # employee | manager


class AcceptInviteRequest(BaseModel):
    username: str
    password: str
    full_name: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _validate_invite(token: str) -> dict:
    """Get invite or raise 404/410."""
    invite = invite_repo.get_invite(token)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pozvánka neexistuje")
    if invite.get("used_by"):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Pozvánka bola už použitá")
    # Check expiry (expires_at can be string or datetime depending on backend)
    expires_raw = invite.get("expires_at")
    if expires_raw:
        try:
            if isinstance(expires_raw, str):
                # Normalize ISO string — remove trailing Z or offset for naive parse
                exp_str = expires_raw.replace("Z", "+00:00")
                try:
                    expires_dt = datetime.fromisoformat(exp_str)
                except ValueError:
                    expires_dt = datetime.fromisoformat(expires_raw[:19])
                    expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            else:
                expires_dt = expires_raw
            # Make timezone-aware comparison
            now = datetime.now(timezone.utc)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            if now > expires_dt:
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="Pozvánka vypršala")
        except HTTPException:
            raise
        except Exception:
            pass  # If we can't parse expiry, allow it
    return invite


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/invites", status_code=status.HTTP_201_CREATED)
def create_invite(
    body: CreateInviteRequest,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Create a new invite link (valid 7 days)."""
    if body.role not in ("employee", "manager"):
        raise HTTPException(status_code=400, detail="Rola musí byť 'employee' alebo 'manager'")
    token = invite_repo.create_invite(current_user["id"], body.role)
    return {"token": token, "detail": "Pozvánka vytvorená"}


@router.get("/invites")
def list_invites(current_user: dict = Depends(require_manager_or_admin)):
    """List invite tokens created by the current user."""
    return invite_repo.list_invites_by_creator(current_user["id"])


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invite(
    invite_id: int,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Revoke an invite token."""
    deleted = invite_repo.delete_invite(invite_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Pozvánka nenájdená alebo nemáš právo na zmazanie")


@router.get("/invites/{token}/info")
def get_invite_info(token: str):
    """Public endpoint — check if invite is valid and return role."""
    invite = _validate_invite(token)
    return {
        "valid": True,
        "role": invite["role"],
        "expires_at": invite["expires_at"],
    }


@router.post("/invites/{token}/accept", status_code=status.HTTP_201_CREATED)
def accept_invite(token: str, body: AcceptInviteRequest):
    """Register a new user via invite link."""
    invite = _validate_invite(token)

    # Validate input
    username = body.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Používateľské meno musí mať aspoň 3 znaky")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Heslo musí mať aspoň 6 znakov")
    if user_repo.username_exists(username):
        raise HTTPException(status_code=409, detail=f"Používateľ '{username}' už existuje")

    hashed = hashlib.sha256(body.password.encode()).hexdigest()
    ok, msg = user_repo.create_user(username, hashed, body.full_name.strip(), invite["role"], None)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Get the newly created user's id to mark invite as used
    new_user = user_repo.get_by_username(username)
    if new_user:
        invite_repo.mark_used(token, new_user["id"])

    return {"detail": "Účet bol vytvorený! Teraz sa môžeš prihlásiť."}
