# Design: Interactive Network Diagram + File Attachments + Client Module

**Date:** 2026-05-05  
**Status:** Approved  
**Scope:** Three phased features for ManagmentApp v3.x

---

## Overview

Three feature areas implemented in dependency order:

1. **Fáza 1 — File Attachments** (task + project level, with visibility)
2. **Fáza 2 — Interactive Network Diagram** (click node → task modal)
3. **Fáza 3–4 — Client Module** (financial advisor/broker vertical)

Registration improvements noted as separate follow-up.

---

## Fáza 1 — File Attachments

### Problem
Files can only be attached to tasks today (`task_attachments` table exists). No project-level files. No visibility control. No unified attachment overview.

### Design Decisions
- **Placement:** Attachment sidebar panel to the right of the task list in `ProjectDetailPage`
- **Visibility levels:** Three — `team` (all project members) / `managers` (admin + manager roles) / `private` (only uploader)
- **Unified view:** `GET /projects/{id}/all-attachments` returns both project-level and task-level attachments with source tag
- **Storage:** `uploads/` directory (local dev, served via FastAPI StaticFiles); Supabase Storage in production

### Data Model

```sql
-- Add visibility to existing task_attachments
ALTER TABLE task_attachments ADD COLUMN visibility TEXT DEFAULT 'team'

-- New table for project-level files
CREATE TABLE project_attachments (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  file_name   TEXT NOT NULL,
  file_path   TEXT NOT NULL,
  file_size   INTEGER,
  mime_type   TEXT,
  visibility  TEXT DEFAULT 'team',  -- 'team' | 'managers' | 'private'
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/attachments` | Upload file (multipart), field: `visibility` |
| GET | `/projects/{id}/attachments` | List project files (filtered by caller's role) |
| GET | `/projects/{id}/all-attachments` | Project files + all task files combined |
| DELETE | `/project-attachments/{id}` | Owner or manager only |
| POST | `/tasks/{id}/attachments` | Upload task file |
| GET | `/tasks/{id}/attachments` | List task files |
| DELETE | `/task-attachments/{id}` | Owner or manager only |

**Visibility filtering logic:**
- `team` → visible to all project members
- `managers` → visible only to users with role `manager` or `admin`
- `private` → visible only to the uploader (`user_id`)

### Frontend Components

**`FileUploadDropzone.tsx`**
- Drag & drop zone + file picker button
- `VisibilitySelector` embedded (three-level picker: 👥 Tím / 👔 Manažéri / 🔒 Len ja)
- Shows upload progress, error handling

**`AttachmentSidebar.tsx`**
- Rendered to the right of task list in `ProjectDetailPage` (only on `tasks` tab)
- Shows project-level files with colored visibility badges
- Badge is clickable → changes visibility inline (PATCH call)
- "+ Nahrať" button opens `FileUploadDropzone`

**`AttachmentList.tsx`** (shared component)
- Used in both sidebar and task modal
- Rows: icon | filename | size | date | visibility badge | delete button

**`ProjectDetailPage.tsx`** changes:
- Task list area becomes flex row: `[task list flex-1] [AttachmentSidebar w-64]`
- Only shown on `tasks` tab

---

## Fáza 2 — Interactive Network Diagram Modal

### Problem
Nodes in `NetworkDiagram.tsx` are visual only. To edit a task, user must navigate away to the task list. No way to act on a task in context of the diagram.

### Design Decision
**Click node → modal overlay** (full-screen dimmed backdrop, modal centered).  
**Two-column layout** inside modal: left = task info + files, right = comments.

### Interaction
- Click on any node → `TaskDetailModal` opens with that task's data
- Escape key or backdrop click → closes modal
- Changes save immediately (optimistic updates), `tasks` query invalidated on close
- No navigation away from diagram

### `TaskDetailModal.tsx` Layout

```
┌─────────────────────────────────────────────────────┐
│ [Task name]                    [Priority badge] [✕] │
├──────────────────────────┬──────────────────────────┤
│ LEFT COLUMN              │ RIGHT COLUMN             │
│                          │                          │
│ Status      [dropdown]   │ Komentáre (N)            │
│ Pridelený   [select]     │ ┌────────────────────┐   │
│ Deadline    [date]       │ │ @Jana: text...     │   │
│ Trvanie     [number]     │ │ @Peter: reply...   │   │
│ Priorita    [select]     │ └────────────────────┘   │
│                          │ [textarea + Odoslať]     │
│ Popis                    │                          │
│ [textarea]               │ ─────────────────────    │
│                          │ Súbory (N)               │
│ CPM info (read-only)     │ [AttachmentList]         │
│ ES/EF/Float/Critical     │ [FileUploadDropzone]     │
│                          │                          │
│ Čas: N.Nh / Xh estimate  │                          │
└──────────────────────────┴──────────────────────────┘
```

### Implementation Notes
- `NetworkDiagram.tsx`: add `onClick` to each node `<g>` element → `setSelectedTaskId(task.id)`
- `TaskDetailModal` receives `taskId` prop, fetches full task data via `GET /tasks/{id}` (new endpoint needed) or reuse from parent `tasks` array
- All edits use existing `PATCH /tasks/{id}` endpoint
- Comments use existing `GET/POST /tasks/{id}/comments`
- Files use `GET/POST/DELETE /tasks/{id}/attachments`

---

## Fáza 3 — Client Module (Financial Advisors)

### Problem
No support for client-centric workflows needed by financial advisors/brokers (MiFID II compliance, onboarding pipelines, meeting logs, commission tracking).

### Design Decision
`Client` is a **first-class entity** (own DB table), not a project tag. One client can have multiple projects (onboarding, annual review, new product, etc.).

### Data Model

```sql
CREATE TABLE clients (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  email        TEXT,
  phone        TEXT,
  category     TEXT DEFAULT 'retail',
  -- 'retail' | 'professional' | 'eligible_counterparty'
  risk_profile TEXT DEFAULT 'balanced',
  -- 'conservative' | 'balanced' | 'dynamic'
  advisor_id   INTEGER REFERENCES users(id),
  notes        TEXT,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

ALTER TABLE projects ADD COLUMN client_id INTEGER REFERENCES clients(id)

CREATE TABLE client_meetings (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id    INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  user_id      INTEGER NOT NULL REFERENCES users(id),
  meeting_date TEXT NOT NULL,
  notes        TEXT,
  follow_ups   TEXT,  -- JSON array of follow-up action strings
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

CREATE TABLE compliance_items (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id      INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  item_type      TEXT NOT NULL,
  -- 'kyc' | 'suitability' | 'aml' | 'id_document' | 'risk_questionnaire' | 'contract'
  status         TEXT DEFAULT 'pending',
  -- 'pending' | 'complete' | 'expired'
  due_date       TEXT,
  completed_by   INTEGER REFERENCES users(id),
  completed_at   TIMESTAMP,
  document_path  TEXT
)

CREATE TABLE deal_stages (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id           INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  stage               TEXT DEFAULT 'lead',
  -- 'lead' | 'contact' | 'analysis' | 'proposal' | 'signed' | 'active' | 'lost'
  deal_value          REAL,
  commission_expected REAL,
  commission_received REAL,
  currency            TEXT DEFAULT 'EUR',
  notes               TEXT,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### API (new router: `clients_router.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/clients` | List (filtered by advisor_id for employees; all for managers) |
| POST | `/clients` | Create client |
| GET | `/clients/{id}` | Detail + linked projects |
| PATCH | `/clients/{id}` | Update |
| DELETE | `/clients/{id}` | Soft delete (set archived flag) |
| GET | `/clients/{id}/meetings` | Meeting log |
| POST | `/clients/{id}/meetings` | Log new meeting |
| GET | `/clients/{id}/compliance` | Compliance checklist |
| POST | `/clients/{id}/compliance` | Add item |
| PATCH | `/compliance-items/{id}` | Mark complete / update |
| GET | `/clients/{id}/pipeline` | Deal stage info |
| PATCH | `/clients/{id}/pipeline` | Update stage, values |

### Frontend Pages & Components

**`ClientsPage.tsx`** (`/clients`)
- Table/card list of clients: name, category badge, risk profile, advisor, linked projects count, deal stage
- Filter by: advisor, category, stage
- "+ Nový klient" button (managers only)
- Nav link added to `Layout.tsx` sidebar

**`ClientDetailPage.tsx`** (`/clients/{id}`)
- Header: name, category, risk profile, advisor
- Tabs: Projekty | Pipeline | Stretnutia | Compliance | Dokumenty
- **Projekty tab:** linked projects list + "Priradiť projekt" button
- **Pipeline tab:** `PipelineKanban.tsx` — Kanban columns per stage, drag to move
- **Stretnutia tab:** `MeetingLog.tsx` — chronological list + add meeting form
- **Compliance tab:** `ComplianceChecklist.tsx` — item list with status, due date, document upload
- **Dokumenty tab:** `AttachmentList.tsx` scoped to client

**`PipelineKanban.tsx`**
- 7 columns: Lead → Prvý kontakt → Analýza → Návrh → Podpis → Aktívny → Stratený
- Client card shows: name, deal value, expected commission
- Drag & drop via HTML5 drag API (no extra deps)

**`ComplianceChecklist.tsx`**
- Predefined item types (KYC, suitability, AML, ID document, risk questionnaire, contract)
- Status badge: 🟡 Pending / ✅ Complete / 🔴 Expired
- Document upload per item
- Due date with countdown / overdue warning

---

## Fáza 4 — PDF Reports & Commission Dashboard

### Client PDF Report
- `GET /clients/{id}/report.pdf` — generates PDF with: client info, compliance status, linked projects CPM summary, meeting history
- Library: `reportlab` (Python, no external service needed)

### Commission Dashboard
- `GET /me/commissions` — per-advisor summary: expected vs received, by month/quarter/year
- Shown in `ClientsPage` sidebar or dedicated `/commissions` route

---

## Implementation Order (within each phase)

**Fáza 1:**
1. DB migration (project_attachments table + visibility column on task_attachments)
2. File upload infrastructure (uploads/ dir, FastAPI StaticFiles)
3. `attachment_repo.py` + API endpoints
4. `FileUploadDropzone.tsx` + `AttachmentList.tsx` + `VisibilitySelector.tsx`
5. `AttachmentSidebar.tsx` + integrate into `ProjectDetailPage`
6. Add attachment upload to existing task expanded row

**Fáza 2:**
1. `GET /tasks/{id}` full detail endpoint (if not exists)
2. `TaskDetailModal.tsx` (two-column, all sections)
3. Click handler in `NetworkDiagram.tsx`

**Fáza 3:**
1. DB migration (clients, client_meetings, compliance_items, deal_stages)
2. `client_repo.py` + `clients_router.py`
3. `ClientsPage.tsx` + nav link
4. `ClientDetailPage.tsx` with all tabs
5. `PipelineKanban.tsx`
6. `ComplianceChecklist.tsx`
7. `MeetingLog.tsx`

**Fáza 4:**
1. `reportlab` PDF generation
2. Commission dashboard

---

## Open Items
- **Registrácia** — needs fixing (separate task, after this spec)
- File storage in production: confirm Supabase Storage bucket setup
- MiFID II compliance item types: confirm complete list with domain expert (Peter Drvar)
- PDF report template: design needed before implementation
