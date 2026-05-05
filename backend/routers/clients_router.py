"""Endpoints for client module (financial advisor vertical)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user
from repositories import client_repo

router = APIRouter(prefix="/clients", tags=["clients"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    category: str = "retail"
    risk_profile: str = "balanced"
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    category: str | None = None
    risk_profile: str | None = None
    advisor_id: int | None = None
    notes: str | None = None


class MeetingCreate(BaseModel):
    meeting_date: str
    notes: str = ""
    follow_ups: list[str] = []


class ComplianceCreate(BaseModel):
    item_type: str
    due_date: str | None = None
    notes: str | None = None


class ComplianceUpdate(BaseModel):
    status: str | None = None
    due_date: str | None = None
    completed_at: str | None = None
    document_path: str | None = None
    notes: str | None = None


class DealUpdate(BaseModel):
    stage: str
    deal_value: float | None = None
    commission_expected: float | None = None
    commission_received: float | None = None
    currency: str = "EUR"
    notes: str | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _client_or_404(client_id: int) -> dict:
    c = client_repo.get_client_by_id(client_id)
    if not c or c.get("archived"):
        raise HTTPException(status_code=404, detail="Klient nenájdený")
    return c


# ── Clients CRUD ───────────────────────────────────────────────────────────────

@router.get("/pipeline/all")
def get_all_pipeline(current_user: dict = Depends(get_current_user)):
    """Full pipeline board — all deals grouped by stage."""
    if current_user["role"] in ("admin", "manager"):
        deals = client_repo.get_all_deals_for_advisor()
    else:
        deals = client_repo.get_all_deals_for_advisor(advisor_id=current_user["id"])
    return deals


@router.get("/")
def list_clients(current_user: dict = Depends(get_current_user)):
    if current_user["role"] in ("admin", "manager"):
        return client_repo.get_clients()
    return client_repo.get_clients(advisor_id=current_user["id"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    current_user: dict = Depends(get_current_user),
):
    client_id = client_repo.create_client(
        name=body.name,
        advisor_id=current_user["id"],
        email=body.email,
        phone=body.phone,
        category=body.category,
        risk_profile=body.risk_profile,
        notes=body.notes,
    )
    return {"id": client_id, "detail": "Klient vytvorený"}


@router.get("/{client_id}")
def get_client(client_id: int, current_user: dict = Depends(get_current_user)):
    c = _client_or_404(client_id)
    projects = client_repo.get_client_projects(client_id)
    deal = client_repo.get_deal(client_id)
    return {**c, "projects": projects, "deal": deal}


@router.patch("/{client_id}")
def update_client(
    client_id: int,
    body: ClientUpdate,
    current_user: dict = Depends(get_current_user),
):
    _client_or_404(client_id)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    client_repo.update_client(client_id, fields)
    return {"detail": "Klient aktualizovaný"}


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_client(
    client_id: int,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("admin", "manager"):
        raise HTTPException(403, "Len manažér môže archivovať klientov")
    _client_or_404(client_id)
    client_repo.archive_client(client_id)


@router.post("/{client_id}/link-project")
def link_project(
    client_id: int,
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("admin", "manager"):
        raise HTTPException(403, "Len manažér môže priraďovať projekty")
    _client_or_404(client_id)
    client_repo.link_project_to_client(project_id, client_id)
    return {"detail": "Projekt priradený ku klientovi"}


# ── Meetings ───────────────────────────────────────────────────────────────────

@router.get("/{client_id}/meetings")
def list_meetings(client_id: int, current_user: dict = Depends(get_current_user)):
    _client_or_404(client_id)
    return client_repo.get_meetings(client_id)


@router.post("/{client_id}/meetings", status_code=status.HTTP_201_CREATED)
def add_meeting(
    client_id: int,
    body: MeetingCreate,
    current_user: dict = Depends(get_current_user),
):
    import json
    _client_or_404(client_id)
    meeting_id = client_repo.add_meeting(
        client_id=client_id,
        user_id=current_user["id"],
        meeting_date=body.meeting_date,
        notes=body.notes,
        follow_ups=json.dumps(body.follow_ups),
    )
    return {"id": meeting_id, "detail": "Stretnutie zaznamenané"}


@router.delete("/{client_id}/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    client_id: int,
    meeting_id: int,
    current_user: dict = Depends(get_current_user),
):
    deleted = client_repo.delete_meeting(meeting_id, current_user["id"])
    if not deleted:
        raise HTTPException(404, "Stretnutie nenájdené alebo nie je tvoje")


# ── Compliance ─────────────────────────────────────────────────────────────────

@router.get("/{client_id}/compliance")
def list_compliance(client_id: int, current_user: dict = Depends(get_current_user)):
    _client_or_404(client_id)
    return client_repo.get_compliance_items(client_id)


@router.post("/{client_id}/compliance", status_code=status.HTTP_201_CREATED)
def add_compliance(
    client_id: int,
    body: ComplianceCreate,
    current_user: dict = Depends(get_current_user),
):
    _client_or_404(client_id)
    item_id = client_repo.add_compliance_item(
        client_id=client_id,
        item_type=body.item_type,
        due_date=body.due_date,
        notes=body.notes,
    )
    return {"id": item_id, "detail": "Compliance položka pridaná"}


@router.patch("/compliance/{item_id}")
def update_compliance(
    item_id: int,
    body: ComplianceUpdate,
    current_user: dict = Depends(get_current_user),
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if "status" in fields and fields["status"] == "complete":
        from datetime import datetime
        fields.setdefault("completed_at", datetime.utcnow().isoformat())
        fields.setdefault("completed_by", current_user["id"])
    client_repo.update_compliance_item(item_id, fields)
    return {"detail": "Compliance aktualizovaná"}


# ── Deal pipeline ──────────────────────────────────────────────────────────────

@router.get("/{client_id}/pipeline")
def get_pipeline(client_id: int, current_user: dict = Depends(get_current_user)):
    _client_or_404(client_id)
    return client_repo.get_deal(client_id) or {}


@router.patch("/{client_id}/pipeline")
def update_pipeline(
    client_id: int,
    body: DealUpdate,
    current_user: dict = Depends(get_current_user),
):
    _client_or_404(client_id)
    if body.stage not in client_repo.DEAL_STAGES:
        raise HTTPException(400, f"Neplatná fáza. Platné: {client_repo.DEAL_STAGES}")
    client_repo.upsert_deal(
        client_id=client_id,
        stage=body.stage,
        deal_value=body.deal_value,
        commission_expected=body.commission_expected,
        commission_received=body.commission_received,
        currency=body.currency,
        notes=body.notes,
    )
    return {"detail": "Pipeline aktualizovaná"}
