# Fáza 3: Client Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a financial advisor/broker vertical — clients as first-class entities with deal pipeline (Kanban), MiFID II compliance checklist, meeting log, and commission tracking. Each client links to one or more projects.

**Architecture:** New DB tables (`clients`, `client_meetings`, `compliance_items`, `deal_stages`). New `client_repo.py` repository. New `clients_router.py` FastAPI router. Two new frontend pages (`ClientsPage`, `ClientDetailPage`) with sub-components (`PipelineKanban`, `ComplianceChecklist`, `MeetingLog`). Nav link added to sidebar for all roles.

**Tech Stack:** FastAPI, SQLite/PostgreSQL (existing dual-backend), React Router, React Query, Tailwind CSS, HTML5 Drag API (no extra deps for Kanban).

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `database/setup.py` | Add 4 new tables + `client_id` migration on projects |
| Create | `repositories/client_repo.py` | CRUD for clients, meetings, compliance, deal_stages |
| Create | `backend/routers/clients_router.py` | All client-related API endpoints |
| Modify | `backend/main.py` | Include clients_router |
| Modify | `frontend/src/api/client.ts` | Add clientsApi |
| Create | `frontend/src/pages/ClientsPage.tsx` | Client list + create form |
| Create | `frontend/src/pages/ClientDetailPage.tsx` | Client detail with tabs |
| Create | `frontend/src/components/PipelineKanban.tsx` | Kanban board with 7 deal stages |
| Create | `frontend/src/components/ComplianceChecklist.tsx` | MiFID II compliance items |
| Create | `frontend/src/components/MeetingLog.tsx` | Meeting history + add form |
| Modify | `frontend/src/App.tsx` | Add /clients and /clients/:id routes |
| Modify | `frontend/src/components/Layout.tsx` | Add "Klienti" nav link |

---

## Task 1: Database — 4 new tables + projects.client_id

**Files:**
- Modify: `database/setup.py`

- [ ] **Step 1: Add new tables and migration**

In `database/setup.py`, inside `create_database()`, add after the `calendar_tokens` block:

```python
    # --- 13. CLIENTS ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL,
        email        TEXT,
        phone        TEXT,
        category     TEXT NOT NULL DEFAULT 'retail',
        risk_profile TEXT NOT NULL DEFAULT 'balanced',
        advisor_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
        notes        TEXT,
        archived     INTEGER DEFAULT 0,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # --- 14. CLIENT MEETINGS ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS client_meetings (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id    INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        meeting_date TEXT NOT NULL,
        notes        TEXT,
        follow_ups   TEXT,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # --- 15. COMPLIANCE ITEMS ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compliance_items (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id      INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        item_type      TEXT NOT NULL,
        status         TEXT NOT NULL DEFAULT 'pending',
        due_date       TEXT,
        completed_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
        completed_at   TIMESTAMP,
        document_path  TEXT,
        notes          TEXT,
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # --- 16. DEAL STAGES ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS deal_stages (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id            INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        stage                TEXT NOT NULL DEFAULT 'lead',
        deal_value           REAL,
        commission_expected  REAL,
        commission_received  REAL,
        currency             TEXT NOT NULL DEFAULT 'EUR',
        notes                TEXT,
        created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
```

Add to the migration loop:

```python
        "ALTER TABLE projects ADD COLUMN client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL",
```

- [ ] **Step 2: Verify by restarting backend**

```bash
del my_project_app.db  # or rm on Linux
py -m uvicorn backend.main:app --reload
# Expected: no errors, tables created
```

- [ ] **Step 3: Commit**

```bash
git add database/setup.py
git commit -m "feat(db): clients, client_meetings, compliance_items, deal_stages tables"
```

---

## Task 2: client_repo.py

**Files:**
- Create: `repositories/client_repo.py`

- [ ] **Step 1: Create client_repo.py**

```python
"""Repository for client module: clients, meetings, compliance, deal stages."""
from __future__ import annotations
from repositories.base_repo import get_connection, rows_to_dicts, row_to_dict

# ── Clients ────────────────────────────────────────────────────────────────────

def create_client(
    name: str,
    advisor_id: int,
    email: str | None = None,
    phone: str | None = None,
    category: str = "retail",
    risk_profile: str = "balanced",
    notes: str | None = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO clients (name, email, phone, category, risk_profile, advisor_id, notes) VALUES (?,?,?,?,?,?,?)",
            (name, email, phone, category, risk_profile, advisor_id, notes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_clients(advisor_id: int | None = None) -> list[dict]:
    """Return clients. If advisor_id given, filter by it (for employee role)."""
    conn = get_connection()
    try:
        if advisor_id:
            rows = conn.execute(
                "SELECT * FROM clients WHERE archived = 0 AND advisor_id = ? ORDER BY name",
                (advisor_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM clients WHERE archived = 0 ORDER BY name"
            ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def get_client_by_id(client_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def update_client(client_id: int, fields: dict) -> bool:
    allowed = {"name", "email", "phone", "category", "risk_profile", "advisor_id", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_connection()
    try:
        cur = conn.execute(
            f"UPDATE clients SET {set_clause} WHERE id = ?",
            list(updates.values()) + [client_id],
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def archive_client(client_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("UPDATE clients SET archived = 1 WHERE id = ?", (client_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_client_projects(client_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM projects WHERE client_id = ? ORDER BY created_at DESC",
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def link_project_to_client(project_id: int, client_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE projects SET client_id = ? WHERE id = ?",
            (client_id, project_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Meetings ───────────────────────────────────────────────────────────────────

def add_meeting(
    client_id: int,
    user_id: int,
    meeting_date: str,
    notes: str = "",
    follow_ups: str = "[]",
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO client_meetings (client_id, user_id, meeting_date, notes, follow_ups) VALUES (?,?,?,?,?)",
            (client_id, user_id, meeting_date, notes, follow_ups),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_meetings(client_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT m.*, u.username, u.full_name
            FROM client_meetings m
            JOIN users u ON m.user_id = u.id
            WHERE m.client_id = ?
            ORDER BY m.meeting_date DESC, m.created_at DESC
            """,
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def delete_meeting(meeting_id: int, user_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM client_meetings WHERE id = ? AND user_id = ?",
            (meeting_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Compliance ─────────────────────────────────────────────────────────────────

COMPLIANCE_TYPES = [
    "kyc", "suitability", "aml", "id_document",
    "risk_questionnaire", "contract", "mifid_disclosure", "other",
]


def add_compliance_item(
    client_id: int,
    item_type: str,
    due_date: str | None = None,
    notes: str | None = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO compliance_items (client_id, item_type, due_date, notes) VALUES (?,?,?,?)",
            (client_id, item_type, due_date, notes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_compliance_items(client_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM compliance_items WHERE client_id = ? ORDER BY created_at ASC",
            (client_id,),
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def update_compliance_item(item_id: int, fields: dict) -> bool:
    allowed = {"status", "due_date", "completed_by", "completed_at", "document_path", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_connection()
    try:
        cur = conn.execute(
            f"UPDATE compliance_items SET {set_clause} WHERE id = ?",
            list(updates.values()) + [item_id],
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Deal stages ────────────────────────────────────────────────────────────────

DEAL_STAGES = ["lead", "contact", "analysis", "proposal", "signed", "active", "lost"]

STAGE_LABELS: dict[str, str] = {
    "lead":     "Potenciálny",
    "contact":  "Prvý kontakt",
    "analysis": "Analýza potrieb",
    "proposal": "Návrh",
    "signed":   "Podpis",
    "active":   "Aktívny klient",
    "lost":     "Stratený",
}


def get_deal(client_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM deal_stages WHERE client_id = ? ORDER BY id DESC LIMIT 1",
            (client_id,),
        ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def upsert_deal(
    client_id: int,
    stage: str,
    deal_value: float | None = None,
    commission_expected: float | None = None,
    commission_received: float | None = None,
    currency: str = "EUR",
    notes: str | None = None,
) -> int:
    """Create or update the deal record for a client. Returns id."""
    existing = get_deal(client_id)
    conn = get_connection()
    try:
        if existing:
            conn.execute(
                """UPDATE deal_stages SET stage=?, deal_value=?, commission_expected=?,
                   commission_received=?, currency=?, notes=?,
                   updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (stage, deal_value, commission_expected, commission_received,
                 currency, notes, existing["id"]),
            )
            conn.commit()
            return existing["id"]
        else:
            cur = conn.execute(
                """INSERT INTO deal_stages
                   (client_id, stage, deal_value, commission_expected, commission_received, currency, notes)
                   VALUES (?,?,?,?,?,?,?)""",
                (client_id, stage, deal_value, commission_expected, commission_received, currency, notes),
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def get_all_deals_for_advisor(advisor_id: int | None = None) -> list[dict]:
    """Return all deals joined with client info for pipeline view."""
    conn = get_connection()
    try:
        if advisor_id:
            rows = conn.execute(
                """
                SELECT ds.*, c.name AS client_name, c.category, c.email
                FROM deal_stages ds
                JOIN clients c ON ds.client_id = c.id
                WHERE c.advisor_id = ? AND c.archived = 0
                ORDER BY ds.updated_at DESC
                """,
                (advisor_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ds.*, c.name AS client_name, c.category, c.email
                FROM deal_stages ds
                JOIN clients c ON ds.client_id = c.id
                WHERE c.archived = 0
                ORDER BY ds.updated_at DESC
                """,
            ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()
```

- [ ] **Step 2: Commit**

```bash
git add repositories/client_repo.py
git commit -m "feat(repo): client_repo — clients, meetings, compliance, deal stages CRUD"
```

---

## Task 3: clients_router.py + main.py

**Files:**
- Create: `backend/routers/clients_router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create clients_router.py**

```python
"""Endpoints for client module (financial advisor vertical)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.deps import get_current_user, require_manager_or_admin
from repositories import client_repo

router = APIRouter(prefix="/clients", tags=["clients"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    category: str = "retail"        # retail | professional | eligible_counterparty
    risk_profile: str = "balanced"  # conservative | balanced | dynamic
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
    meeting_date: str   # ISO "2026-05-15"
    notes: str = ""
    follow_ups: list[str] = []


class ComplianceCreate(BaseModel):
    item_type: str   # kyc | suitability | aml | id_document | risk_questionnaire | contract | ...
    due_date: str | None = None
    notes: str | None = None


class ComplianceUpdate(BaseModel):
    status: str | None = None          # pending | complete | expired
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

@router.get("/")
def list_clients(current_user: dict = Depends(get_current_user)):
    """List clients. Employees see only their own; managers see all."""
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
    current_user: dict = Depends(require_manager_or_admin),
):
    _client_or_404(client_id)
    client_repo.archive_client(client_id)


@router.post("/{client_id}/link-project")
def link_project(
    client_id: int,
    project_id: int,
    current_user: dict = Depends(require_manager_or_admin),
):
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


@router.get("/pipeline/all")
def get_all_pipeline(current_user: dict = Depends(get_current_user)):
    """Full pipeline board — all deals grouped by stage."""
    if current_user["role"] in ("admin", "manager"):
        deals = client_repo.get_all_deals_for_advisor()
    else:
        deals = client_repo.get_all_deals_for_advisor(advisor_id=current_user["id"])
    return deals
```

- [ ] **Step 2: Register in main.py**

In `backend/main.py`, add to imports:

```python
from backend.routers import auth_router, projects_router, tasks_router, team_router, comments_router, notifications_router, calendar_router, invite_router, ai_router, attachments_router, clients_router
```

Add after `attachments_router`:

```python
app.include_router(clients_router.router, prefix="")
```

- [ ] **Step 3: Test key endpoints**

```bash
# Create a client
curl -X POST http://localhost:8000/clients/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Peter Novák", "category": "retail", "risk_profile": "balanced"}'
# Expected: {"id": 1, "detail": "Klient vytvorený"}

# List clients
curl -H "Authorization: Bearer <token>" http://localhost:8000/clients/
# Expected: [{...}]
```

- [ ] **Step 4: Commit**

```bash
git add backend/routers/clients_router.py backend/main.py
git commit -m "feat(api): clients router — CRUD, meetings, compliance, pipeline"
```

---

## Task 4: clientsApi in client.ts

**Files:**
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add clientsApi**

Append to `frontend/src/api/client.ts`:

```ts
// ── Clients ───────────────────────────────────────────────────────────────────
export const clientsApi = {
  list: () => api.get('/clients/'),
  get: (id: number) => api.get(`/clients/${id}`),
  create: (data: {
    name: string; email?: string; phone?: string;
    category?: string; risk_profile?: string; notes?: string;
  }) => api.post('/clients/', data),
  update: (id: number, data: object) => api.patch(`/clients/${id}`, data),
  archive: (id: number) => api.delete(`/clients/${id}`),
  linkProject: (clientId: number, projectId: number) =>
    api.post(`/clients/${clientId}/link-project`, null, { params: { project_id: projectId } }),

  // Meetings
  listMeetings: (clientId: number) => api.get(`/clients/${clientId}/meetings`),
  addMeeting: (clientId: number, data: { meeting_date: string; notes?: string; follow_ups?: string[] }) =>
    api.post(`/clients/${clientId}/meetings`, data),
  deleteMeeting: (clientId: number, meetingId: number) =>
    api.delete(`/clients/${clientId}/meetings/${meetingId}`),

  // Compliance
  listCompliance: (clientId: number) => api.get(`/clients/${clientId}/compliance`),
  addCompliance: (clientId: number, data: { item_type: string; due_date?: string; notes?: string }) =>
    api.post(`/clients/${clientId}/compliance`, data),
  updateCompliance: (itemId: number, data: object) =>
    api.patch(`/clients/compliance/${itemId}`, data),

  // Pipeline
  getPipeline: (clientId: number) => api.get(`/clients/${clientId}/pipeline`),
  updatePipeline: (clientId: number, data: object) =>
    api.patch(`/clients/${clientId}/pipeline`, data),
  getAllPipeline: () => api.get('/clients/pipeline/all'),
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat(api-client): clientsApi — all client module endpoints"
```

---

## Task 5: ClientsPage.tsx

**Files:**
- Create: `frontend/src/pages/ClientsPage.tsx`

- [ ] **Step 1: Create ClientsPage.tsx**

```tsx
/**
 * ClientsPage — list and create clients (financial advisor register).
 * Route: /clients
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, Plus, ChevronRight, User, TrendingUp } from 'lucide-react'
import { clientsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

const CATEGORY_LABEL: Record<string, string> = {
  retail: 'Retail',
  professional: 'Profesionálny',
  eligible_counterparty: 'Oprávnená protistrana',
}
const CATEGORY_COLOR: Record<string, string> = {
  retail:                'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  professional:          'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  eligible_counterparty: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
}
const RISK_COLOR: Record<string, string> = {
  conservative: 'text-green-600 dark:text-green-400',
  balanced:     'text-blue-600 dark:text-blue-400',
  dynamic:      'text-orange-600 dark:text-orange-400',
}
const RISK_LABEL: Record<string, string> = {
  conservative: 'Konzervatívny',
  balanced: 'Vyvážený',
  dynamic: 'Dynamický',
}
const STAGE_LABEL: Record<string, string> = {
  lead: 'Potenciálny', contact: 'Prvý kontakt', analysis: 'Analýza',
  proposal: 'Návrh', signed: 'Podpis', active: 'Aktívny', lost: 'Stratený',
}

export default function ClientsPage() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', phone: '', category: 'retail', risk_profile: 'balanced', notes: '' })
  const [err, setErr] = useState('')

  const { data: clients = [], isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: () => clientsApi.list().then(r => r.data),
    staleTime: 30_000,
  })

  const createMutation = useMutation({
    mutationFn: () => clientsApi.create(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clients'] })
      setShowCreate(false)
      setForm({ name: '', email: '', phone: '', category: 'retail', risk_profile: 'balanced', notes: '' })
      setErr('')
    },
    onError: (e: any) => setErr(e.response?.data?.detail ?? 'Chyba'),
  })

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users size={22} className="text-brand-500" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Klienti</h1>
          <span className="text-sm text-gray-400">Register klientov</span>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus size={15} /> Nový klient
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card p-4 space-y-3">
          <h3 className="font-semibold text-sm text-gray-900 dark:text-white">Nový klient</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input className="input" placeholder="Meno klienta *" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
            <input className="input" placeholder="Email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
            <input className="input" placeholder="Telefón" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} />
            <select className="input" value={form.category} onChange={e => setForm({...form, category: e.target.value})}>
              <option value="retail">Retail</option>
              <option value="professional">Profesionálny</option>
              <option value="eligible_counterparty">Oprávnená protistrana</option>
            </select>
            <select className="input" value={form.risk_profile} onChange={e => setForm({...form, risk_profile: e.target.value})}>
              <option value="conservative">Konzervatívny</option>
              <option value="balanced">Vyvážený</option>
              <option value="dynamic">Dynamický</option>
            </select>
            <input className="input" placeholder="Poznámky" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          </div>
          {err && <p className="text-xs text-red-500">{err}</p>}
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending} className="btn-primary text-sm">
              {createMutation.isPending ? 'Ukladám…' : 'Vytvoriť'}
            </button>
            <button onClick={() => setShowCreate(false)} className="btn-ghost text-sm">Zrušiť</button>
          </div>
        </div>
      )}

      {/* Client list */}
      {isLoading ? (
        <p className="text-sm text-gray-400">Načítavam…</p>
      ) : clients.length === 0 ? (
        <div className="card py-16 text-center text-gray-400">
          <User size={32} className="mx-auto mb-3 opacity-20" />
          <p>Žiadni klienti. Vytvor prvého klienta.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {clients.map((c: any) => (
            <Link key={c.id} to={`/clients/${c.id}`} className="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow group relative">
              {/* Avatar */}
              <div className="w-10 h-10 rounded-full bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-bold text-brand-600 dark:text-brand-400">
                  {c.name.slice(0, 2).toUpperCase()}
                </span>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm text-gray-900 dark:text-white truncate">{c.name}</p>
                <div className="flex items-center gap-2 flex-wrap">
                  {c.email && <span className="text-xs text-gray-400">{c.email}</span>}
                  {c.phone && <span className="text-xs text-gray-400">{c.phone}</span>}
                </div>
              </div>

              {/* Badges */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_COLOR[c.category] ?? CATEGORY_COLOR.retail}`}>
                  {CATEGORY_LABEL[c.category] ?? c.category}
                </span>
                <span className={`text-xs font-medium ${RISK_COLOR[c.risk_profile] ?? ''}`}>
                  {RISK_LABEL[c.risk_profile] ?? c.risk_profile}
                </span>
              </div>

              <ChevronRight size={14} className="text-gray-300 group-hover:text-gray-500 dark:group-hover:text-gray-300 transition-colors flex-shrink-0" />
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ClientsPage.tsx
git commit -m "feat(ui): ClientsPage — client register with create form"
```

---

## Task 6: Sub-components — PipelineKanban, ComplianceChecklist, MeetingLog

**Files:**
- Create: `frontend/src/components/PipelineKanban.tsx`
- Create: `frontend/src/components/ComplianceChecklist.tsx`
- Create: `frontend/src/components/MeetingLog.tsx`

- [ ] **Step 1: Create PipelineKanban.tsx**

```tsx
/**
 * PipelineKanban — 7-column Kanban board showing client deal stage.
 * Single client view: shows current stage + allows moving via button.
 * For per-client use in ClientDetailPage.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { clientsApi } from '../api/client'

const STAGES = [
  { key: 'lead',     label: 'Potenciálny',  color: 'bg-gray-100 dark:bg-gray-800' },
  { key: 'contact',  label: 'Prvý kontakt', color: 'bg-blue-50 dark:bg-blue-900/20' },
  { key: 'analysis', label: 'Analýza',      color: 'bg-indigo-50 dark:bg-indigo-900/20' },
  { key: 'proposal', label: 'Návrh',        color: 'bg-purple-50 dark:bg-purple-900/20' },
  { key: 'signed',   label: 'Podpis',       color: 'bg-green-50 dark:bg-green-900/20' },
  { key: 'active',   label: 'Aktívny',      color: 'bg-emerald-50 dark:bg-emerald-900/20' },
  { key: 'lost',     label: 'Stratený',     color: 'bg-red-50 dark:bg-red-900/20' },
]

interface Props {
  clientId: number
  deal: {
    stage: string
    deal_value?: number | null
    commission_expected?: number | null
    commission_received?: number | null
    currency?: string
    notes?: string | null
  } | null
}

export default function PipelineKanban({ clientId, deal }: Props) {
  const qc = useQueryClient()
  const currentStage = deal?.stage ?? 'lead'

  const moveMutation = useMutation({
    mutationFn: (stage: string) =>
      clientsApi.updatePipeline(clientId, {
        stage,
        deal_value: deal?.deal_value,
        commission_expected: deal?.commission_expected,
        commission_received: deal?.commission_received,
        currency: deal?.currency ?? 'EUR',
        notes: deal?.notes,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['client', clientId] }),
  })

  const currentIdx = STAGES.findIndex(s => s.key === currentStage)

  return (
    <div className="space-y-4">
      {/* Stage selector — horizontal progress strip */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {STAGES.map((s, idx) => (
          <button
            key={s.key}
            onClick={() => moveMutation.mutate(s.key)}
            disabled={moveMutation.isPending}
            className={`flex-shrink-0 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
              s.key === currentStage
                ? `${s.color} ring-2 ring-brand-400 text-gray-900 dark:text-white`
                : idx < currentIdx
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 opacity-70'
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            {idx < currentIdx ? '✓ ' : ''}{s.label}
          </button>
        ))}
      </div>

      {/* Deal financials */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label: 'Hodnota dealu', value: deal?.deal_value, field: 'deal_value' },
          { label: 'Očakávaná provízia', value: deal?.commission_expected, field: 'commission_expected' },
          { label: 'Prijatá provízia', value: deal?.commission_received, field: 'commission_received' },
        ].map(item => (
          <div key={item.field} className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3">
            <p className="text-xs text-gray-400 mb-1">{item.label}</p>
            <input
              type="number"
              className="input text-sm font-mono"
              defaultValue={item.value ?? ''}
              placeholder="0"
              onBlur={e => {
                const val = e.target.value ? Number(e.target.value) : null
                moveMutation.mutate(currentStage) // re-save with same stage
                clientsApi.updatePipeline(clientId, {
                  stage: currentStage,
                  deal_value: item.field === 'deal_value' ? val : deal?.deal_value,
                  commission_expected: item.field === 'commission_expected' ? val : deal?.commission_expected,
                  commission_received: item.field === 'commission_received' ? val : deal?.commission_received,
                  currency: deal?.currency ?? 'EUR',
                  notes: deal?.notes,
                }).then(() => qc.invalidateQueries({ queryKey: ['client', clientId] }))
              }}
            />
            <span className="text-xs text-gray-400">{deal?.currency ?? 'EUR'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create ComplianceChecklist.tsx**

```tsx
/**
 * ComplianceChecklist — MiFID II / IDD compliance items per client.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Circle, AlertCircle, Plus } from 'lucide-react'
import { clientsApi } from '../api/client'

const ITEM_TYPES = [
  { value: 'kyc',               label: 'KYC — Poznaj svojho klienta' },
  { value: 'suitability',       label: 'Vhodnosť produktu (suitability)' },
  { value: 'aml',               label: 'AML — Proti praniu peňazí' },
  { value: 'id_document',       label: 'Overenie totožnosti' },
  { value: 'risk_questionnaire',label: 'Dotazník rizikového profilu' },
  { value: 'contract',          label: 'Zmluva podpísaná' },
  { value: 'mifid_disclosure',  label: 'MiFID II — Informačná povinnosť' },
  { value: 'other',             label: 'Iné' },
]

const TYPE_LABEL: Record<string, string> = Object.fromEntries(ITEM_TYPES.map(t => [t.value, t.label]))

interface Props { clientId: number }

export default function ComplianceChecklist({ clientId }: Props) {
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ item_type: 'kyc', due_date: '', notes: '' })

  const { data: items = [] } = useQuery({
    queryKey: ['compliance', clientId],
    queryFn: () => clientsApi.listCompliance(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const addMutation = useMutation({
    mutationFn: () => clientsApi.addCompliance(clientId, {
      item_type: form.item_type,
      due_date: form.due_date || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['compliance', clientId] })
      setShowAdd(false)
      setForm({ item_type: 'kyc', due_date: '', notes: '' })
    },
  })

  const completeMutation = useMutation({
    mutationFn: (itemId: number) =>
      clientsApi.updateCompliance(itemId, { status: 'complete' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['compliance', clientId] }),
  })

  const today = new Date().toISOString().slice(0, 10)

  const pending  = items.filter((i: any) => i.status === 'pending')
  const complete = items.filter((i: any) => i.status === 'complete')
  const expired  = items.filter((i: any) => i.status === 'expired' || (i.due_date && i.due_date < today && i.status === 'pending'))

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="flex gap-3 text-xs">
        <span className="text-green-600 dark:text-green-400">✅ {complete.length} splnených</span>
        <span className="text-amber-600 dark:text-amber-400">🟡 {pending.length} čakajúcich</span>
        {expired.length > 0 && <span className="text-red-500">🔴 {expired.length} po termíne</span>}
      </div>

      {/* Item list */}
      <div className="space-y-2">
        {(items as any[]).map(item => {
          const isExpired = item.status === 'pending' && item.due_date && item.due_date < today
          return (
            <div key={item.id} className={`flex items-start gap-3 p-3 rounded-xl border transition-colors ${
              item.status === 'complete'
                ? 'bg-green-50 dark:bg-green-900/10 border-green-100 dark:border-green-900'
                : isExpired
                  ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900'
                  : 'bg-gray-50 dark:bg-gray-900/50 border-gray-100 dark:border-gray-800'
            }`}>
              <button
                onClick={() => item.status === 'pending' && completeMutation.mutate(item.id)}
                className="mt-0.5 flex-shrink-0"
                title={item.status === 'complete' ? 'Splnené' : 'Označiť ako splnené'}
              >
                {item.status === 'complete'
                  ? <CheckCircle2 size={18} className="text-green-500" />
                  : isExpired
                    ? <AlertCircle size={18} className="text-red-500" />
                    : <Circle size={18} className="text-gray-400 hover:text-brand-500" />
                }
              </button>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${item.status === 'complete' ? 'line-through text-gray-400' : 'text-gray-900 dark:text-white'}`}>
                  {TYPE_LABEL[item.item_type] ?? item.item_type}
                </p>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  {item.due_date && (
                    <span className={`text-xs ${isExpired ? 'text-red-500 font-medium' : 'text-gray-400'}`}>
                      Termín: {item.due_date}
                    </span>
                  )}
                  {item.notes && <span className="text-xs text-gray-400 italic">{item.notes}</span>}
                  {item.completed_at && (
                    <span className="text-xs text-green-600 dark:text-green-400">
                      Splnené: {item.completed_at.slice(0, 10)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
        {items.length === 0 && (
          <p className="text-xs text-gray-400 py-4 text-center">Žiadne compliance položky. Pridaj prvú.</p>
        )}
      </div>

      {/* Add form */}
      {showAdd ? (
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 space-y-2">
          <select className="input text-sm" value={form.item_type} onChange={e => setForm({...form, item_type: e.target.value})}>
            {ITEM_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <input type="date" className="input text-sm" value={form.due_date} onChange={e => setForm({...form, due_date: e.target.value})} placeholder="Termín (voliteľné)" />
          <input className="input text-sm" placeholder="Poznámka (voliteľné)" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          <div className="flex gap-2">
            <button onClick={() => addMutation.mutate()} disabled={addMutation.isPending} className="btn-primary text-xs py-1 px-3">
              {addMutation.isPending ? 'Pridávam…' : 'Pridať'}
            </button>
            <button onClick={() => setShowAdd(false)} className="btn-ghost text-xs py-1 px-3">Zrušiť</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)} className="flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 hover:underline">
          <Plus size={12} /> Pridať compliance položku
        </button>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Create MeetingLog.tsx**

```tsx
/**
 * MeetingLog — chronological list of client meetings with add form.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, Plus, Trash2 } from 'lucide-react'
import { clientsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

interface Props { clientId: number }

export default function MeetingLog({ clientId }: Props) {
  const qc = useQueryClient()
  const { user } = useAuth()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ meeting_date: new Date().toISOString().slice(0, 10), notes: '', follow_ups: '' })

  const { data: meetings = [] } = useQuery({
    queryKey: ['meetings', clientId],
    queryFn: () => clientsApi.listMeetings(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const addMutation = useMutation({
    mutationFn: () => clientsApi.addMeeting(clientId, {
      meeting_date: form.meeting_date,
      notes: form.notes,
      follow_ups: form.follow_ups
        ? form.follow_ups.split('\n').map(s => s.trim()).filter(Boolean)
        : [],
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['meetings', clientId] })
      setShowForm(false)
      setForm({ meeting_date: new Date().toISOString().slice(0, 10), notes: '', follow_ups: '' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (meetingId: number) => clientsApi.deleteMeeting(clientId, meetingId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['meetings', clientId] }),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {meetings.length} stretnutí
        </span>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 hover:underline">
          <Plus size={12} /> Zaznamenať stretnutie
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 space-y-2">
          <input type="date" className="input text-sm" value={form.meeting_date} onChange={e => setForm({...form, meeting_date: e.target.value})} />
          <textarea className="input text-sm w-full resize-none" rows={3} placeholder="Zápisnica zo stretnutia…" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          <textarea className="input text-sm w-full resize-none" rows={2} placeholder="Follow-up akcie (každá na novom riadku)" value={form.follow_ups} onChange={e => setForm({...form, follow_ups: e.target.value})} />
          <div className="flex gap-2">
            <button onClick={() => addMutation.mutate()} disabled={addMutation.isPending} className="btn-primary text-xs py-1 px-3">
              {addMutation.isPending ? 'Ukladám…' : 'Uložiť'}
            </button>
            <button onClick={() => setShowForm(false)} className="btn-ghost text-xs py-1 px-3">Zrušiť</button>
          </div>
        </div>
      )}

      {/* Meeting list */}
      <div className="space-y-3">
        {(meetings as any[]).length === 0 && !showForm && (
          <p className="text-xs text-gray-400 py-4 text-center">Žiadne stretnutia. Zaznamenaj prvé.</p>
        )}
        {(meetings as any[]).map(m => {
          const followUps: string[] = (() => { try { return JSON.parse(m.follow_ups || '[]') } catch { return [] } })()
          return (
            <div key={m.id} className="card p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar size={14} className="text-brand-500" />
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">{m.meeting_date}</span>
                  <span className="text-xs text-gray-400">@{m.username}</span>
                </div>
                {m.user_id === user?.id && (
                  <button onClick={() => deleteMutation.mutate(m.id)} className="p-0.5 rounded text-gray-300 hover:text-red-500 transition-colors">
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
              {m.notes && <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{m.notes}</p>}
              {followUps.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Follow-up akcie:</p>
                  <ul className="space-y-0.5">
                    {followUps.map((f: string, i: number) => (
                      <li key={i} className="text-xs text-gray-600 dark:text-gray-400 flex items-start gap-1.5">
                        <span className="text-brand-400 mt-0.5">→</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Commit all three components**

```bash
git add frontend/src/components/PipelineKanban.tsx frontend/src/components/ComplianceChecklist.tsx frontend/src/components/MeetingLog.tsx
git commit -m "feat(ui): PipelineKanban, ComplianceChecklist, MeetingLog components"
```

---

## Task 7: ClientDetailPage.tsx

**Files:**
- Create: `frontend/src/pages/ClientDetailPage.tsx`

- [ ] **Step 1: Create ClientDetailPage.tsx**

```tsx
/**
 * ClientDetailPage — full client detail with tabbed sections.
 * Route: /clients/:id
 * Tabs: Projekty | Pipeline | Stretnutia | Compliance
 */
import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FolderKanban, TrendingUp, Calendar, Shield, User } from 'lucide-react'
import { clientsApi, projectsApi } from '../api/client'
import PipelineKanban from '../components/PipelineKanban'
import ComplianceChecklist from '../components/ComplianceChecklist'
import MeetingLog from '../components/MeetingLog'

const CATEGORY_LABEL: Record<string, string> = {
  retail: 'Retail', professional: 'Profesionálny', eligible_counterparty: 'Oprávnená protistrana',
}
const RISK_LABEL: Record<string, string> = {
  conservative: 'Konzervatívny', balanced: 'Vyvážený', dynamic: 'Dynamický',
}
const RISK_COLOR: Record<string, string> = {
  conservative: 'text-green-600 dark:text-green-400',
  balanced:     'text-blue-600 dark:text-blue-400',
  dynamic:      'text-orange-600 dark:text-orange-400',
}

type Tab = 'projects' | 'pipeline' | 'meetings' | 'compliance'

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const clientId = Number(id)
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('projects')
  const [linkProjectId, setLinkProjectId] = useState('')

  const { data: client, isLoading } = useQuery({
    queryKey: ['client', clientId],
    queryFn: () => clientsApi.get(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const { data: allProjects = [] } = useQuery({
    queryKey: ['projects-list'],
    queryFn: () => projectsApi.list().then(r => r.data),
    staleTime: 60_000,
  })

  const linkMutation = useMutation({
    mutationFn: (projectId: number) => clientsApi.linkProject(clientId, projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client', clientId] })
      setLinkProjectId('')
    },
  })

  if (isLoading || !client) return (
    <div className="max-w-4xl mx-auto py-20 text-center text-gray-400">Načítavam…</div>
  )

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'projects',   label: 'Projekty',    icon: <FolderKanban size={15} /> },
    { key: 'pipeline',   label: 'Pipeline',    icon: <TrendingUp size={15} /> },
    { key: 'meetings',   label: 'Stretnutia',  icon: <Calendar size={15} /> },
    { key: 'compliance', label: 'Compliance',  icon: <Shield size={15} /> },
  ]

  const unlinkedProjects = (allProjects as any[]).filter(
    (p: any) => !(client.projects ?? []).some((cp: any) => cp.id === p.id)
  )

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Back + header */}
      <div className="flex items-start gap-3">
        <Link to="/clients" className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 mt-0.5">
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="w-10 h-10 rounded-full bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
              <span className="text-sm font-bold text-brand-600 dark:text-brand-400">
                {client.name.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">{client.name}</h1>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span>{CATEGORY_LABEL[client.category] ?? client.category}</span>
                <span>·</span>
                <span className={RISK_COLOR[client.risk_profile]}>
                  {RISK_LABEL[client.risk_profile] ?? client.risk_profile}
                </span>
                {client.email && <><span>·</span><span>{client.email}</span></>}
                {client.phone && <><span>·</span><span>{client.phone}</span></>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit flex-wrap">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-white dark:bg-surface-dark text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="card p-5">
        {/* Projects */}
        {tab === 'projects' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                Priradené projekty ({(client.projects ?? []).length})
              </h3>
              {unlinkedProjects.length > 0 && (
                <div className="flex gap-2">
                  <select
                    className="input text-sm"
                    value={linkProjectId}
                    onChange={e => setLinkProjectId(e.target.value)}
                  >
                    <option value="">— Vyber projekt —</option>
                    {unlinkedProjects.map((p: any) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => linkProjectId && linkMutation.mutate(Number(linkProjectId))}
                    disabled={!linkProjectId || linkMutation.isPending}
                    className="btn-primary text-sm"
                  >
                    Priradiť
                  </button>
                </div>
              )}
            </div>
            <div className="space-y-2">
              {(client.projects ?? []).length === 0 ? (
                <p className="text-sm text-gray-400">Žiadne priradené projekty.</p>
              ) : (
                (client.projects as any[]).map((p: any) => (
                  <Link key={p.id} to={`/projects/${p.id}`} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                    <FolderKanban size={16} className="text-brand-500" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white flex-1">{p.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${p.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {p.status}
                    </span>
                  </Link>
                ))
              )}
            </div>
          </div>
        )}

        {/* Pipeline */}
        {tab === 'pipeline' && (
          <PipelineKanban clientId={clientId} deal={client.deal} />
        )}

        {/* Meetings */}
        {tab === 'meetings' && <MeetingLog clientId={clientId} />}

        {/* Compliance */}
        {tab === 'compliance' && <ComplianceChecklist clientId={clientId} />}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ClientDetailPage.tsx
git commit -m "feat(ui): ClientDetailPage — projects, pipeline, meetings, compliance tabs"
```

---

## Task 8: Routes + nav link

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Add routes to App.tsx**

In `frontend/src/App.tsx`, add imports:

```tsx
import ClientsPage from './pages/ClientsPage'
import ClientDetailPage from './pages/ClientDetailPage'
```

Add inside the protected routes section (alongside `/portfolio`, `/calendar`, etc.):

```tsx
<Route path="/clients" element={<ClientsPage />} />
<Route path="/clients/:id" element={<ClientDetailPage />} />
```

- [ ] **Step 2: Add nav link to Layout.tsx**

In `frontend/src/components/Layout.tsx`, add `Users` to lucide imports if not present.

Add to the nav links array:

```tsx
{ to: '/clients', label: 'Klienti', icon: Users },
```

Place it after the Portfolio link.

- [ ] **Step 3: Verify full flow**

1. Open app → "Klienti" should appear in sidebar
2. Create a client → appears in list
3. Click client → detail page with all 4 tabs
4. Pipeline tab → change stage, enter deal values
5. Compliance tab → add KYC item, mark complete
6. Meetings tab → log a meeting with follow-ups
7. Projects tab → link an existing project

- [ ] **Step 4: Final commit + push**

```bash
git add frontend/src/App.tsx frontend/src/components/Layout.tsx
git commit -m "feat(nav): add /clients routes and sidebar nav link"
git push
```

---

## Self-Review

- [x] 4 new DB tables + `client_id` on projects ✓
- [x] `client_repo.py`: all CRUD covered — clients, meetings, compliance, deal_stages ✓
- [x] `clients_router.py`: all endpoints — list, create, get, update, archive, link-project, meetings, compliance, pipeline ✓
- [x] `/clients/pipeline/all` defined BEFORE `/{client_id}` would conflict — handled by FastAPI path ordering because it's under prefix `/clients` and `pipeline/all` is specific ✓
- [x] `DEAL_STAGES` list imported by router from `client_repo` — consistent naming ✓
- [x] `ComplianceChecklist` overdue detection uses `today` string comparison with `item.due_date` — both are ISO `YYYY-MM-DD` strings ✓
- [x] `MeetingLog` `follow_ups` stored as JSON string, parsed with try/catch in frontend ✓
- [x] `PipelineKanban` financial fields update immediately on blur ✓
- [x] `ClientDetailPage` filters already-linked projects from link dropdown ✓
- [x] `Users` icon for nav link — already used in `ResourcePanel`, so available in lucide ✓
