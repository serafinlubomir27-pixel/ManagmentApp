"""Endpoints for client module (financial advisor vertical)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, assert_client_access, current_org_id
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


# ── Clients CRUD ───────────────────────────────────────────────────────────────
# Poznámka: prístup ku konkrétnemu klientovi rieši assert_client_access z backend.deps
# (admin/manager vidia všetkých, inak len advisor daného klienta).

@router.get("/pipeline/all")
def get_all_pipeline(current_user: dict = Depends(get_current_user)):
    """Full pipeline board — all deals grouped by stage (v rámci vlastnej organizácie)."""
    org_id = current_org_id(current_user)
    if current_user["role"] in ("admin", "manager"):
        return client_repo.get_all_deals_for_advisor(org_id)
    return client_repo.get_all_deals_for_advisor(org_id, advisor_id=current_user["id"])


@router.get("/")
def list_clients(current_user: dict = Depends(get_current_user)):
    org_id = current_org_id(current_user)
    if current_user["role"] in ("admin", "manager"):
        return client_repo.get_clients(org_id)
    return client_repo.get_clients(org_id, advisor_id=current_user["id"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    current_user: dict = Depends(get_current_user),
):
    client_id = client_repo.create_client(
        name=body.name,
        advisor_id=current_user["id"],
        organization_id=current_org_id(current_user),
        email=body.email,
        phone=body.phone,
        category=body.category,
        risk_profile=body.risk_profile,
        notes=body.notes,
    )
    return {"id": client_id, "detail": "Klient vytvorený"}


@router.get("/{client_id}")
def get_client(client_id: int, current_user: dict = Depends(get_current_user)):
    c = assert_client_access(client_id, current_user)
    projects = client_repo.get_client_projects(client_id)
    deal = client_repo.get_deal(client_id)
    return {**c, "projects": projects, "deal": deal}


@router.patch("/{client_id}")
def update_client(
    client_id: int,
    body: ClientUpdate,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
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
    assert_client_access(client_id, current_user)
    client_repo.archive_client(client_id)


@router.post("/{client_id}/link-project")
def link_project(
    client_id: int,
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("admin", "manager"):
        raise HTTPException(403, "Len manažér môže priraďovať projekty")
    assert_client_access(client_id, current_user)
    client_repo.link_project_to_client(project_id, client_id)
    return {"detail": "Projekt priradený ku klientovi"}


# ── Meetings ───────────────────────────────────────────────────────────────────

@router.get("/{client_id}/meetings")
def list_meetings(client_id: int, current_user: dict = Depends(get_current_user)):
    assert_client_access(client_id, current_user)
    return client_repo.get_meetings(client_id)


@router.post("/{client_id}/meetings", status_code=status.HTTP_201_CREATED)
def add_meeting(
    client_id: int,
    body: MeetingCreate,
    current_user: dict = Depends(get_current_user),
):
    import json
    assert_client_access(client_id, current_user)
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
    assert_client_access(client_id, current_user)
    return client_repo.get_compliance_items(client_id)


@router.post("/{client_id}/compliance", status_code=status.HTTP_201_CREATED)
def add_compliance(
    client_id: int,
    body: ComplianceCreate,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
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
    item = client_repo.get_compliance_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Compliance položka nenájdená")
    assert_client_access(item["client_id"], current_user)
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
    assert_client_access(client_id, current_user)
    return client_repo.get_deal(client_id) or {}


@router.patch("/{client_id}/pipeline")
def update_pipeline(
    client_id: int,
    body: DealUpdate,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
    if body.stage not in client_repo.DEAL_STAGES:
        raise HTTPException(400, f"Neplatná fáza. Platné: {client_repo.DEAL_STAGES}")

    # Pôvodnú fázu treba zistiť pred zápisom, inak sa posun nedá zaznamenať.
    previous = client_repo.get_deal(client_id)
    old_stage = (previous or {}).get("stage")

    client_repo.upsert_deal(
        client_id=client_id,
        stage=body.stage,
        deal_value=body.deal_value,
        commission_expected=body.commission_expected,
        commission_received=body.commission_received,
        currency=body.currency,
        notes=body.notes,
    )

    if old_stage != body.stage:
        client_repo.add_stage_change(client_id, old_stage, body.stage, current_user["id"])
        client_repo.add_activity(
            client_id=client_id,
            user_id=current_user["id"],
            activity_type="note",
            subject="Zmena fázy obchodu",
            body=f"{old_stage or 'nezadaná'} → {body.stage}",
        )
    return {"detail": "Pipeline aktualizovaná"}


# ── CRM: história interakcií ──────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    activity_type: str = "note"
    subject: str = ""
    body: str = ""
    occurred_at: str | None = None


@router.get("/{client_id}/activities")
def list_activities(client_id: int, current_user: dict = Depends(get_current_user)):
    """Časová os interakcií s klientom — hovory, e-maily, stretnutia, poznámky."""
    assert_client_access(client_id, current_user)
    return client_repo.get_activities(client_id)


@router.post("/{client_id}/activities", status_code=status.HTTP_201_CREATED)
def add_activity(
    client_id: int,
    body: ActivityCreate,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
    if body.activity_type not in client_repo.ACTIVITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Neznámy typ interakcie. Povolené: {', '.join(client_repo.ACTIVITY_TYPES)}",
        )
    activity_id = client_repo.add_activity(
        client_id=client_id,
        user_id=current_user["id"],
        activity_type=body.activity_type,
        subject=body.subject,
        body=body.body,
        occurred_at=body.occurred_at,
    )
    return {"id": activity_id, "detail": "Interakcia zaznamenaná"}


@router.delete("/{client_id}/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    client_id: int,
    activity_id: int,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
    if not client_repo.delete_activity(activity_id, current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Záznam sa nenašiel alebo nepatrí tebe",
        )


# ── CRM: naplánované úlohy ku klientovi ───────────────────────────────────────

class ClientTaskCreate(BaseModel):
    title: str
    due_date: str | None = None
    priority: str = "medium"
    assigned_to: int | None = None


class ClientTaskUpdate(BaseModel):
    done: bool


@router.get("/{client_id}/tasks")
def list_client_tasks(client_id: int, current_user: dict = Depends(get_current_user)):
    """Úlohy naplánované ku klientovi. Nesúvisia s harmonogramom projektu."""
    assert_client_access(client_id, current_user)
    return client_repo.get_client_tasks(client_id)


@router.post("/{client_id}/tasks", status_code=status.HTTP_201_CREATED)
def add_client_task(
    client_id: int,
    body: ClientTaskCreate,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
    if not body.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Názov úlohy je povinný")
    task_id = client_repo.add_client_task(
        client_id=client_id,
        created_by=current_user["id"],
        title=body.title.strip(),
        due_date=body.due_date,
        priority=body.priority,
        assigned_to=body.assigned_to,
    )
    return {"id": task_id, "detail": "Úloha vytvorená"}


@router.patch("/{client_id}/tasks/{task_id}")
def update_client_task(
    client_id: int,
    task_id: int,
    body: ClientTaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
    if not client_repo.set_client_task_done(task_id, body.done):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Úloha sa nenašla")
    return {"detail": "Hotovo" if body.done else "Označené ako nesplnené"}


@router.delete("/{client_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client_task(
    client_id: int,
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    assert_client_access(client_id, current_user)
    if not client_repo.delete_client_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Úloha sa nenašla")


@router.get("/tasks/upcoming")
def upcoming_tasks(current_user: dict = Depends(get_current_user)):
    """Nesplnené úlohy naprieč všetkými klientmi poradcu."""
    advisor = None if current_user.get("role") == "admin" else current_user["id"]
    return client_repo.get_upcoming_client_tasks(current_org_id(current_user), advisor)


# ── CRM: história posunov obchodu ─────────────────────────────────────────────

@router.get("/{client_id}/stage-history")
def stage_history(client_id: int, current_user: dict = Depends(get_current_user)):
    """Kedy obchod prešiel do ktorej fázy — podklad pre dĺžku obchodného cyklu."""
    assert_client_access(client_id, current_user)
    return client_repo.get_stage_history(client_id)
