"""Organizácia — plán, využitie a limity.

GET   /organization        — info o vlastnej organizácii (plán, usage, limity)
PATCH /organization/plan   — zmena plánu (zatiaľ manuálne; seam pre budúci billing)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_admin, current_org_id
from repositories import org_repo, user_repo, project_repo
from logic import plans

router = APIRouter(prefix="/organization", tags=["organization"])


@router.get("")
def get_organization(current_user: dict = Depends(get_current_user)):
    org_id = current_org_id(current_user)
    org = org_repo.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organizácia nenájdená")
    plan = org.get("plan") or "free"
    return {
        "id": org["id"],
        "name": org["name"],
        "slug": org["slug"],
        "plan": plan,
        "plan_label": plans.PLAN_LABELS.get(plan, plan),
        "usage": {
            "users": user_repo.count_users_for_org(org_id),
            "projects": project_repo.count_projects_for_org(org_id),
        },
        "limits": {
            "max_users": plans.user_limit(plan),
            "max_projects": plans.project_limit(plan),
        },
    }


class ChangePlanRequest(BaseModel):
    plan: str


@router.patch("/plan")
def change_plan(body: ChangePlanRequest, current_user: dict = Depends(require_admin)):
    """Zmena plánu organizácie. Zatiaľ manuálne (bez platby) — miesto pre napojenie billingu."""
    if body.plan not in plans.PLAN_LIMITS:
        raise HTTPException(status_code=400, detail=f"Neplatný plán. Platné: {list(plans.PLAN_LIMITS)}")
    org_repo.update_plan(current_org_id(current_user), body.plan)
    return {"detail": f"Plán zmenený na {plans.PLAN_LABELS.get(body.plan, body.plan)}"}


# ── GDPR — práva dotknutej osoby ────────────────────────────────────────────

@router.get("/export")
def export_data(current_user: dict = Depends(require_admin)):
    """GDPR právo na prístup/prenositeľnosť — kompletný export dát organizácie (JSON).
    Len admin (obsahuje dáta celej organizácie). Heslá a tokeny sa neexportujú."""
    return org_repo.export_organization(current_org_id(current_user))


class DeleteOrgRequest(BaseModel):
    confirm: str  # musí byť presný názov organizácie


@router.post("/delete")
def delete_organization(body: DeleteOrgRequest, current_user: dict = Depends(require_admin)):
    """GDPR právo na výmaz — NENÁVRATNE zmaže organizáciu a všetky jej dáta.

    Vyžaduje potvrdenie presným názvom organizácie (ochrana proti omylu). Len admin.
    (POST nie DELETE, aby sa dal poslať potvrdzovací názov v tele.)
    """
    org_id = current_org_id(current_user)
    org = org_repo.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organizácia nenájdená")
    if body.confirm.strip() != org["name"]:
        raise HTTPException(status_code=400, detail="Potvrdenie sa nezhoduje s názvom organizácie")
    org_repo.delete_organization_cascade(org_id)
    return {"detail": "Organizácia a všetky jej dáta boli nenávratne zmazané."}
