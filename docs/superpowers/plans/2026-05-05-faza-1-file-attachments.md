# Fáza 1: File Attachments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add file attachments to projects (not just tasks), with three-level visibility control (team / managers / private), sidebar panel in ProjectDetailPage, and unified attachment view.

**Architecture:** New `attachment_repo.py` handles both task and project attachments. A new `attachments_router.py` exposes upload/list/delete endpoints with multipart form data. Files are saved to `uploads/` directory (served as FastAPI StaticFiles at `/uploads`). Frontend adds `AttachmentSidebar` alongside the task list, plus reusable `FileUploadDropzone`, `VisibilitySelector`, and `AttachmentList` components.

**Tech Stack:** FastAPI UploadFile + python-multipart, FastAPI StaticFiles, React Query, axios multipart, Tailwind CSS

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `repositories/attachment_repo.py` | CRUD for task_attachments (with visibility) + project_attachments |
| Modify | `repositories/file_repo.py` | Add visibility param to add_attachment(); add delete_task_attachment_by_owner() |
| Create | `backend/routers/attachments_router.py` | Upload / list / delete endpoints for both task and project attachments |
| Modify | `backend/main.py` | Mount /uploads StaticFiles, include attachments_router |
| Modify | `database/setup.py` | Add project_attachments table + visibility migration on task_attachments |
| Create | `frontend/src/components/VisibilitySelector.tsx` | Three-level visibility picker (team/managers/private) |
| Create | `frontend/src/components/FileUploadDropzone.tsx` | Drag & drop upload with visibility selector |
| Create | `frontend/src/components/AttachmentList.tsx` | Reusable file list rows with badges |
| Create | `frontend/src/components/AttachmentSidebar.tsx` | Sidebar panel showing project files |
| Modify | `frontend/src/api/client.ts` | Add attachmentsApi |
| Modify | `frontend/src/pages/ProjectDetailPage.tsx` | Add AttachmentSidebar next to task list |

---

## Task 1: Database — project_attachments table + visibility migration

**Files:**
- Modify: `database/setup.py`

- [ ] **Step 1: Add project_attachments table and visibility migration to setup.py**

Open `database/setup.py` and add inside `create_database()`, after the existing `time_logs` table block:

```python
    # --- 12. PROJECT ATTACHMENTS ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_attachments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER NOT NULL,
        user_id     INTEGER NOT NULL,
        file_name   TEXT NOT NULL,
        file_path   TEXT NOT NULL,
        file_size   INTEGER,
        mime_type   TEXT,
        visibility  TEXT NOT NULL DEFAULT 'team',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
```

Then add to the migration block (the `for column_sql in [...]` loop):

```python
        "ALTER TABLE task_attachments ADD COLUMN visibility TEXT NOT NULL DEFAULT 'team'",
```

- [ ] **Step 2: Verify migration runs cleanly**

Delete `my_project_app.db` if it exists and restart the backend — `setup.py` runs on startup:

```bash
# In project root:
del my_project_app.db   # Windows
# or: rm my_project_app.db  (Linux/Mac)
py -m uvicorn backend.main:app --reload
```

Expected in console: `[DB] Databaza uspesne skontrolovana/vytvorena!` with no errors.

- [ ] **Step 3: Commit**

```bash
git add database/setup.py
git commit -m "feat(db): add project_attachments table + visibility column on task_attachments"
```

---

## Task 2: attachment_repo.py — repository layer

**Files:**
- Create: `repositories/attachment_repo.py`

- [ ] **Step 1: Create the repository**

Create `repositories/attachment_repo.py` with full content:

```python
"""Repository for project_attachments and task_attachments (with visibility)."""
from __future__ import annotations
from repositories.base_repo import get_connection, rows_to_dicts


# ── Visibility helper ──────────────────────────────────────────────────────────

def _visibility_filter(user_role: str, user_id: int) -> tuple[str, list]:
    """Return SQL WHERE clause fragment and params for visibility filtering."""
    if user_role in ("admin", "manager"):
        # Managers see team + managers; not private of others
        return "(visibility IN ('team', 'managers') OR user_id = ?)", [user_id]
    # Regular employees: see team files + their own private
    return "(visibility = 'team' OR user_id = ?)", [user_id]


# ── Project attachments ────────────────────────────────────────────────────────

def add_project_attachment(
    project_id: int,
    user_id: int,
    file_name: str,
    file_path: str,
    file_size: int | None,
    mime_type: str | None,
    visibility: str = "team",
) -> int:
    """Insert a project attachment. Returns new id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO project_attachments
                (project_id, user_id, file_name, file_path, file_size, mime_type, visibility)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, user_id, file_name, file_path, file_size, mime_type, visibility),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_project_attachments(
    project_id: int,
    user_role: str,
    user_id: int,
) -> list[dict]:
    """Return project attachments visible to the requesting user."""
    vis_clause, vis_params = _visibility_filter(user_role, user_id)
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT pa.id, pa.file_name, pa.file_path, pa.file_size, pa.mime_type,
                   pa.visibility, pa.uploaded_at,
                   u.username AS uploaded_by_username
            FROM project_attachments pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = ? AND {vis_clause}
            ORDER BY pa.uploaded_at DESC
            """,
            [project_id] + vis_params,
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def update_project_attachment_visibility(
    attachment_id: int,
    visibility: str,
    user_id: int,
) -> bool:
    """Update visibility. Returns True if updated (only owner can change)."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE project_attachments SET visibility = ? WHERE id = ? AND user_id = ?",
            (visibility, attachment_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_project_attachment(attachment_id: int, user_id: int, user_role: str) -> str | None:
    """Delete project attachment. Owner or manager can delete. Returns file_path or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT file_path, user_id FROM project_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
        if not row:
            return None
        r = dict(row)
        if r["user_id"] != user_id and user_role not in ("admin", "manager"):
            return None  # not authorized
        conn.execute("DELETE FROM project_attachments WHERE id = ?", (attachment_id,))
        conn.commit()
        return r["file_path"]
    finally:
        conn.close()


# ── Task attachments (with visibility) ────────────────────────────────────────

def add_task_attachment(
    task_id: int,
    user_id: int,
    file_name: str,
    file_path: str,
    file_size: int | None,
    mime_type: str | None,
    visibility: str = "team",
) -> int:
    """Insert a task attachment with visibility. Returns new id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO task_attachments (task_id, file_name, file_path, uploaded_by, visibility)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, file_name, file_path, user_id, visibility),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_task_attachments(
    task_id: int,
    user_role: str,
    user_id: int,
) -> list[dict]:
    """Return task attachments visible to the requesting user."""
    vis_clause, vis_params = _visibility_filter(user_role, user_id)
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT ta.id, ta.file_name, ta.file_path, ta.visibility, ta.uploaded_at,
                   u.username AS uploaded_by_username
            FROM task_attachments ta
            JOIN users u ON ta.uploaded_by = u.id
            WHERE ta.task_id = ? AND {vis_clause}
            ORDER BY ta.uploaded_at DESC
            """,
            [task_id] + vis_params,
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def delete_task_attachment(attachment_id: int, user_id: int, user_role: str) -> str | None:
    """Delete task attachment. Owner or manager. Returns file_path or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT file_path, uploaded_by FROM task_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
        if not row:
            return None
        r = dict(row)
        if r["uploaded_by"] != user_id and user_role not in ("admin", "manager"):
            return None
        conn.execute("DELETE FROM task_attachments WHERE id = ?", (attachment_id,))
        conn.commit()
        return r["file_path"]
    finally:
        conn.close()


def update_task_attachment_visibility(
    attachment_id: int,
    visibility: str,
    user_id: int,
) -> bool:
    """Update task attachment visibility (owner only). Returns True if updated."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE task_attachments SET visibility = ? WHERE id = ? AND uploaded_by = ?",
            (visibility, attachment_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Unified view ───────────────────────────────────────────────────────────────

def get_all_attachments_for_project(
    project_id: int,
    user_role: str,
    user_id: int,
) -> dict:
    """Return project attachments + all task attachments for a project."""
    project_files = get_project_attachments(project_id, user_role, user_id)
    vis_clause, vis_params = _visibility_filter(user_role, user_id)
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT ta.id, ta.file_name, ta.file_path, ta.visibility, ta.uploaded_at,
                   u.username AS uploaded_by_username,
                   t.id AS task_id, t.name AS task_name
            FROM task_attachments ta
            JOIN tasks t ON ta.task_id = t.id
            JOIN users u ON ta.uploaded_by = u.id
            WHERE t.project_id = ? AND {vis_clause}
            ORDER BY ta.uploaded_at DESC
            """,
            [project_id] + vis_params,
        ).fetchall()
        task_files = rows_to_dicts(rows)
    finally:
        conn.close()
    return {"project_files": project_files, "task_files": task_files}
```

- [ ] **Step 2: Commit**

```bash
git add repositories/attachment_repo.py
git commit -m "feat(repo): attachment_repo with visibility filtering for project + task files"
```

---

## Task 3: attachments_router.py — API endpoints

**Files:**
- Create: `backend/routers/attachments_router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create attachments_router.py**

Create `backend/routers/attachments_router.py`:

```python
"""Endpoints for file attachments on tasks and projects."""
from __future__ import annotations

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse

from backend.deps import get_current_user
from repositories import attachment_repo, project_repo, task_repo

router = APIRouter(tags=["attachments"])

# ── Upload directory ───────────────────────────────────────────────────────────

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(_PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_VISIBILITY = {"team", "managers", "private"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _save_file(upload: UploadFile) -> tuple[str, str, int, str]:
    """Save uploaded file to UPLOAD_DIR. Returns (unique_name, url_path, size, mime)."""
    ext = os.path.splitext(upload.filename or "file")[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, unique_name)
    size = 0
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
        size = f.tell()
    return unique_name, f"/uploads/{unique_name}", size, upload.content_type or "application/octet-stream"


# ── Project attachments ────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_project_attachment(
    project_id: int,
    file: UploadFile = File(...),
    visibility: str = Form("team"),
    current_user: dict = Depends(get_current_user),
):
    if not project_repo.get_project_by_id(project_id):
        raise HTTPException(404, "Projekt nenájdený")
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")

    _, url_path, size, mime = _save_file(file)
    att_id = attachment_repo.add_project_attachment(
        project_id=project_id,
        user_id=current_user["id"],
        file_name=file.filename or "file",
        file_path=url_path,
        file_size=size,
        mime_type=mime,
        visibility=visibility,
    )
    return {"id": att_id, "detail": "Súbor nahraný"}


@router.get("/projects/{project_id}/attachments")
def list_project_attachments(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    if not project_repo.get_project_by_id(project_id):
        raise HTTPException(404, "Projekt nenájdený")
    return attachment_repo.get_project_attachments(
        project_id, current_user["role"], current_user["id"]
    )


@router.get("/projects/{project_id}/all-attachments")
def list_all_project_attachments(
    project_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Combined view: project files + all task files in one response."""
    if not project_repo.get_project_by_id(project_id):
        raise HTTPException(404, "Projekt nenájdený")
    return attachment_repo.get_all_attachments_for_project(
        project_id, current_user["role"], current_user["id"]
    )


@router.patch("/project-attachments/{attachment_id}/visibility")
def update_project_attachment_visibility(
    attachment_id: int,
    visibility: str,
    current_user: dict = Depends(get_current_user),
):
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")
    updated = attachment_repo.update_project_attachment_visibility(
        attachment_id, visibility, current_user["id"]
    )
    if not updated:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    return {"detail": "Viditeľnosť aktualizovaná"}


@router.delete("/project-attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_attachment(
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
):
    file_path = attachment_repo.delete_project_attachment(
        attachment_id, current_user["id"], current_user["role"]
    )
    if file_path is None:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    # Remove physical file
    abs_path = os.path.join(_PROJECT_ROOT, file_path.lstrip("/"))
    if os.path.exists(abs_path):
        os.remove(abs_path)


# ── Task attachments ───────────────────────────────────────────────────────────

@router.post("/tasks/{task_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_task_attachment(
    task_id: int,
    file: UploadFile = File(...),
    visibility: str = Form("team"),
    current_user: dict = Depends(get_current_user),
):
    if not task_repo.get_task_status_and_name(task_id):
        raise HTTPException(404, "Úloha nenájdená")
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")

    _, url_path, size, mime = _save_file(file)
    att_id = attachment_repo.add_task_attachment(
        task_id=task_id,
        user_id=current_user["id"],
        file_name=file.filename or "file",
        file_path=url_path,
        file_size=size,
        mime_type=mime,
        visibility=visibility,
    )
    return {"id": att_id, "detail": "Súbor nahraný"}


@router.get("/tasks/{task_id}/attachments")
def list_task_attachments(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    if not task_repo.get_task_status_and_name(task_id):
        raise HTTPException(404, "Úloha nenájdená")
    return attachment_repo.get_task_attachments(
        task_id, current_user["role"], current_user["id"]
    )


@router.patch("/task-attachments/{attachment_id}/visibility")
def update_task_attachment_visibility(
    attachment_id: int,
    visibility: str,
    current_user: dict = Depends(get_current_user),
):
    if visibility not in ALLOWED_VISIBILITY:
        raise HTTPException(400, "Neplatná viditeľnosť")
    updated = attachment_repo.update_task_attachment_visibility(
        attachment_id, visibility, current_user["id"]
    )
    if not updated:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    return {"detail": "Viditeľnosť aktualizovaná"}


@router.delete("/task-attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_attachment(
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
):
    file_path = attachment_repo.delete_task_attachment(
        attachment_id, current_user["id"], current_user["role"]
    )
    if file_path is None:
        raise HTTPException(404, "Príloha nenájdená alebo nemáš oprávnenie")
    abs_path = os.path.join(_PROJECT_ROOT, file_path.lstrip("/"))
    if os.path.exists(abs_path):
        os.remove(abs_path)
```

- [ ] **Step 2: Register router + static files in main.py**

Open `backend/main.py`. Add to the imports line:

```python
from backend.routers import auth_router, projects_router, tasks_router, team_router, comments_router, notifications_router, calendar_router, invite_router, ai_router, attachments_router
```

Add after the existing `app.include_router(ai_router.router, prefix="")` line:

```python
app.include_router(attachments_router.router, prefix="")
```

Also add static file serving — add after the middleware block:

```python
from fastapi.staticfiles import StaticFiles
import os as _os
_uploads_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "uploads")
_os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")
```

- [ ] **Step 3: Install python-multipart if missing**

```bash
pip install python-multipart
```

Check `requirements.txt` — add `python-multipart` if not present.

- [ ] **Step 4: Test endpoint manually**

Start backend and test upload:

```bash
py -m uvicorn backend.main:app --reload
# In another terminal:
curl -X POST http://localhost:8000/projects/1/attachments \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@test.txt" \
  -F "visibility=team"
# Expected: {"id": 1, "detail": "Súbor nahraný"}
```

- [ ] **Step 5: Commit**

```bash
git add backend/routers/attachments_router.py backend/main.py
git commit -m "feat(api): file attachment endpoints for projects + tasks with visibility"
```

---

## Task 4: Frontend — VisibilitySelector + AttachmentList components

**Files:**
- Create: `frontend/src/components/VisibilitySelector.tsx`
- Create: `frontend/src/components/AttachmentList.tsx`

- [ ] **Step 1: Create VisibilitySelector.tsx**

```tsx
/**
 * VisibilitySelector — three-level visibility picker for file attachments.
 * Values: 'team' | 'managers' | 'private'
 */
interface Props {
  value: 'team' | 'managers' | 'private'
  onChange: (v: 'team' | 'managers' | 'private') => void
  className?: string
}

const OPTIONS = [
  { value: 'team' as const,     label: '👥 Celý tím',     desc: 'Všetci v projekte' },
  { value: 'managers' as const, label: '👔 Manažéri',     desc: 'Admin + manažér' },
  { value: 'private' as const,  label: '🔒 Len ja',       desc: 'Súkromné' },
]

const BADGE: Record<string, string> = {
  team:     'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  managers: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  private:  'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
}

export function VisibilityBadge({ value, onClick }: { value: string; onClick?: () => void }) {
  const opt = OPTIONS.find(o => o.value === value) ?? OPTIONS[0]
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-opacity ${BADGE[value]} ${onClick ? 'cursor-pointer hover:opacity-80' : 'cursor-default'}`}
      title={opt.desc}
    >
      {opt.label}
    </button>
  )
}

export default function VisibilitySelector({ value, onChange, className = '' }: Props) {
  return (
    <div className={`flex gap-1 flex-wrap ${className}`}>
      {OPTIONS.map(opt => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          title={opt.desc}
          className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
            value === opt.value
              ? `${BADGE[opt.value]} border-current`
              : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:border-gray-300'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Create AttachmentList.tsx**

```tsx
/**
 * AttachmentList — reusable list of file attachments with visibility badges.
 * Used in AttachmentSidebar (project files) and TaskDetailModal (task files).
 */
import { Trash2, FileText, FileSpreadsheet, Image, File } from 'lucide-react'
import { VisibilityBadge } from './VisibilitySelector'

export interface AttachmentItem {
  id: number
  file_name: string
  file_path: string
  file_size?: number | null
  visibility: 'team' | 'managers' | 'private'
  uploaded_at: string
  uploaded_by_username: string
  task_name?: string   // only for unified view
}

interface Props {
  attachments: AttachmentItem[]
  onDelete?: (id: number) => void
  onVisibilityChange?: (id: number, v: 'team' | 'managers' | 'private') => void
  showTaskTag?: boolean
}

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return <Image size={14} />
  if (['xls', 'xlsx', 'csv'].includes(ext)) return <FileSpreadsheet size={14} />
  if (['doc', 'docx', 'pdf', 'txt'].includes(ext)) return <FileText size={14} />
  return <File size={14} />
}

function formatBytes(bytes?: number | null): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

export default function AttachmentList({ attachments, onDelete, onVisibilityChange, showTaskTag }: Props) {
  if (attachments.length === 0) {
    return <p className="text-xs text-gray-400 py-2">Žiadne prílohy</p>
  }

  return (
    <div className="space-y-1">
      {attachments.map(att => (
        <div key={att.id} className="flex items-center gap-2 group p-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50">
          <span className="text-gray-400 flex-shrink-0">{fileIcon(att.file_name)}</span>
          <a
            href={att.file_path}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 dark:text-brand-400 hover:underline truncate flex-1 min-w-0"
            title={att.file_name}
          >
            {att.file_name}
          </a>
          {showTaskTag && att.task_name && (
            <span className="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded flex-shrink-0">
              {att.task_name}
            </span>
          )}
          {formatBytes(att.file_size) && (
            <span className="text-xs text-gray-400 flex-shrink-0">{formatBytes(att.file_size)}</span>
          )}
          <VisibilityBadge
            value={att.visibility}
            onClick={onVisibilityChange ? () => {
              const order: Array<'team' | 'managers' | 'private'> = ['team', 'managers', 'private']
              const next = order[(order.indexOf(att.visibility) + 1) % 3]
              onVisibilityChange(att.id, next)
            } : undefined}
          />
          {onDelete && (
            <button
              onClick={() => onDelete(att.id)}
              className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-gray-300 hover:text-red-500 transition-all flex-shrink-0"
              title="Zmazať"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/VisibilitySelector.tsx frontend/src/components/AttachmentList.tsx
git commit -m "feat(ui): VisibilitySelector + AttachmentList reusable components"
```

---

## Task 5: Frontend — FileUploadDropzone component

**Files:**
- Create: `frontend/src/components/FileUploadDropzone.tsx`

- [ ] **Step 1: Create FileUploadDropzone.tsx**

```tsx
/**
 * FileUploadDropzone — drag & drop file upload with visibility selector.
 * Calls onUpload(file, visibility) when user submits.
 */
import { useState, useRef, DragEvent } from 'react'
import { Upload, X } from 'lucide-react'
import VisibilitySelector from './VisibilitySelector'

interface Props {
  onUpload: (file: File, visibility: 'team' | 'managers' | 'private') => Promise<void>
  uploading?: boolean
  error?: string
}

export default function FileUploadDropzone({ onUpload, uploading, error }: Props) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [visibility, setVisibility] = useState<'team' | 'managers' | 'private'>('team')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) setSelectedFile(file)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) setSelectedFile(file)
  }

  const handleSubmit = async () => {
    if (!selectedFile) return
    await onUpload(selectedFile, visibility)
    setSelectedFile(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="space-y-2">
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-brand-400 bg-brand-50 dark:bg-brand-900/10'
            : 'border-gray-200 dark:border-gray-700 hover:border-brand-300 dark:hover:border-brand-600'
        }`}
      >
        <input ref={inputRef} type="file" className="hidden" onChange={handleFileChange} />
        <Upload size={18} className="mx-auto mb-1 text-gray-400" />
        {selectedFile ? (
          <p className="text-xs text-gray-700 dark:text-gray-300 font-medium">{selectedFile.name}</p>
        ) : (
          <p className="text-xs text-gray-400">Pretiahni súbor alebo klikni</p>
        )}
      </div>

      {/* Visibility + submit */}
      {selectedFile && (
        <div className="space-y-2">
          <div>
            <p className="text-xs text-gray-500 mb-1">Kto vidí súbor:</p>
            <VisibilitySelector value={visibility} onChange={setVisibility} />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={handleSubmit}
              disabled={uploading}
              className="btn-primary text-xs py-1 px-3"
            >
              {uploading ? 'Nahrávam…' : 'Nahrať'}
            </button>
            <button
              onClick={() => { setSelectedFile(null); if (inputRef.current) inputRef.current.value = '' }}
              className="btn-ghost text-xs py-1 px-3"
            >
              <X size={12} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/FileUploadDropzone.tsx
git commit -m "feat(ui): FileUploadDropzone with drag & drop and visibility selector"
```

---

## Task 6: Frontend — API client + AttachmentSidebar

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/components/AttachmentSidebar.tsx`

- [ ] **Step 1: Add attachmentsApi to client.ts**

Add at the end of `frontend/src/api/client.ts`:

```ts
// ── Attachments ───────────────────────────────────────────────────────────────
export const attachmentsApi = {
  // Project attachments
  uploadProject: (projectId: number, file: File, visibility: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('visibility', visibility)
    return api.post(`/projects/${projectId}/attachments`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  listProject: (projectId: number) =>
    api.get(`/projects/${projectId}/attachments`),
  listAll: (projectId: number) =>
    api.get(`/projects/${projectId}/all-attachments`),
  deleteProject: (id: number) =>
    api.delete(`/project-attachments/${id}`),
  updateProjectVisibility: (id: number, visibility: string) =>
    api.patch(`/project-attachments/${id}/visibility`, null, { params: { visibility } }),

  // Task attachments
  uploadTask: (taskId: number, file: File, visibility: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('visibility', visibility)
    return api.post(`/tasks/${taskId}/attachments`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  listTask: (taskId: number) =>
    api.get(`/tasks/${taskId}/attachments`),
  deleteTask: (id: number) =>
    api.delete(`/task-attachments/${id}`),
  updateTaskVisibility: (id: number, visibility: string) =>
    api.patch(`/task-attachments/${id}/visibility`, null, { params: { visibility } }),
}
```

- [ ] **Step 2: Create AttachmentSidebar.tsx**

```tsx
/**
 * AttachmentSidebar — shows project-level file attachments in a sidebar panel
 * next to the task list in ProjectDetailPage.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Paperclip } from 'lucide-react'
import { attachmentsApi } from '../api/client'
import AttachmentList, { AttachmentItem } from './AttachmentList'
import FileUploadDropzone from './FileUploadDropzone'

interface Props {
  projectId: number
}

export default function AttachmentSidebar({ projectId }: Props) {
  const qc = useQueryClient()
  const [uploadError, setUploadError] = useState('')

  const { data: attachments = [], isLoading } = useQuery<AttachmentItem[]>({
    queryKey: ['project-attachments', projectId],
    queryFn: () => attachmentsApi.listProject(projectId).then(r => r.data),
    staleTime: 30_000,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, visibility }: { file: File; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.uploadProject(projectId, file, visibility),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project-attachments', projectId] })
      setUploadError('')
    },
    onError: (e: any) => setUploadError(e.response?.data?.detail ?? 'Chyba pri nahrávaní'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => attachmentsApi.deleteProject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project-attachments', projectId] }),
  })

  const visibilityMutation = useMutation({
    mutationFn: ({ id, visibility }: { id: number; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.updateProjectVisibility(id, visibility),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project-attachments', projectId] }),
  })

  return (
    <div className="w-64 flex-shrink-0 border-l border-gray-100 dark:border-gray-800 pl-4 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Paperclip size={14} className="text-gray-400" />
        <span className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
          Prílohy projektu
        </span>
        {attachments.length > 0 && (
          <span className="text-xs text-gray-400">({attachments.length})</span>
        )}
      </div>

      {/* File list */}
      {isLoading ? (
        <p className="text-xs text-gray-400">Načítavam…</p>
      ) : (
        <AttachmentList
          attachments={attachments}
          onDelete={id => deleteMutation.mutate(id)}
          onVisibilityChange={(id, v) => visibilityMutation.mutate({ id, visibility: v })}
        />
      )}

      {/* Upload */}
      <FileUploadDropzone
        onUpload={(file, visibility) => uploadMutation.mutateAsync({ file, visibility })}
        uploading={uploadMutation.isPending}
        error={uploadError}
      />
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/components/AttachmentSidebar.tsx
git commit -m "feat(ui): AttachmentSidebar + attachmentsApi for project file management"
```

---

## Task 7: Integrate AttachmentSidebar into ProjectDetailPage

**Files:**
- Modify: `frontend/src/pages/ProjectDetailPage.tsx`

- [ ] **Step 1: Add import**

At the top of `ProjectDetailPage.tsx`, add to the component imports:

```tsx
import AttachmentSidebar from '../components/AttachmentSidebar'
```

- [ ] **Step 2: Wrap task list + sidebar in flex row**

Find the section in `ProjectDetailPage.tsx` where the task list is rendered (inside `{tab === 'tasks' && ...}`). Wrap the entire tasks tab content (form + task list) alongside the sidebar:

```tsx
{tab === 'tasks' && (
  <div className="flex gap-4 items-start">
    {/* Task list — takes remaining space */}
    <div className="flex-1 min-w-0 space-y-3">
      {/* existing: showCreate form, filtered task rows — keep as-is */}
      {showCreate && ( /* ... existing create form ... */ )}
      {isLoading ? (
        <p className="text-sm text-gray-400">Načítavam…</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-gray-400">Žiadne úlohy</p>
      ) : (
        <div className="space-y-2">
          {filtered.map((task: any) => (
            /* existing task row JSX */
          ))}
        </div>
      )}
    </div>

    {/* Attachment sidebar */}
    <AttachmentSidebar projectId={projectId} />
  </div>
)}
```

Note: The exact restructuring depends on the current JSX. The key change is: everything already in `tab === 'tasks'` goes inside `<div className="flex-1 min-w-0 space-y-3">` and `<AttachmentSidebar projectId={projectId} />` is added as a sibling.

- [ ] **Step 3: Verify layout renders**

Start frontend dev server:

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173`, navigate to a project, check that:
- Task list is still full-width but with right margin
- Attachment sidebar appears to the right
- "+ Nahrať" dropzone is visible
- Upload works end-to-end (file appears in sidebar after upload)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ProjectDetailPage.tsx
git commit -m "feat(ui): integrate AttachmentSidebar alongside task list in ProjectDetailPage"
```

---

## Task 8: Add task attachment upload inside expanded task row

**Files:**
- Modify: `frontend/src/pages/ProjectDetailPage.tsx`

- [ ] **Step 1: Add task attachment section in expanded row**

In `ProjectDetailPage.tsx`, find the expanded task row section (the section that shows `TimeLogSection`, subscription toggles, and `CommentSection`). Add task attachments between TimeLogSection and CommentSection:

```tsx
{expandedTaskId === task.id && (
  <div className="px-4 pb-4 space-y-4 border-t border-gray-100 dark:border-gray-800 mt-2 pt-3">
    {/* Time tracking */}
    <TimeLogSection taskId={task.id} estimatedHours={task.estimated_hours} />

    {/* Task attachments */}
    <TaskAttachmentSection taskId={task.id} />

    {/* Subscription toggles */}
    {/* ... existing toggles ... */}

    {/* Comments */}
    <CommentSection taskId={task.id} />
  </div>
)}
```

- [ ] **Step 2: Create inline TaskAttachmentSection**

Add this component inline at the top of `ProjectDetailPage.tsx` (before the main export) or as a separate file `frontend/src/components/TaskAttachmentSection.tsx`:

```tsx
function TaskAttachmentSection({ taskId }: { taskId: number }) {
  const qc = useQueryClient()
  const [uploadError, setUploadError] = useState('')

  const { data: attachments = [] } = useQuery<AttachmentItem[]>({
    queryKey: ['task-attachments', taskId],
    queryFn: () => attachmentsApi.listTask(taskId).then(r => r.data),
    staleTime: 30_000,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, visibility }: { file: File; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.uploadTask(taskId, file, visibility),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['task-attachments', taskId] })
      setUploadError('')
    },
    onError: (e: any) => setUploadError(e.response?.data?.detail ?? 'Chyba'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => attachmentsApi.deleteTask(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['task-attachments', taskId] }),
  })

  const visibilityMutation = useMutation({
    mutationFn: ({ id, visibility }: { id: number; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.updateTaskVisibility(id, visibility),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['task-attachments', taskId] }),
  })

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400">
        <Paperclip size={12} /> Prílohy úlohy
      </div>
      <AttachmentList
        attachments={attachments}
        onDelete={id => deleteMutation.mutate(id)}
        onVisibilityChange={(id, v) => visibilityMutation.mutate({ id, visibility: v })}
      />
      <FileUploadDropzone
        onUpload={(file, visibility) => uploadMutation.mutateAsync({ file, visibility })}
        uploading={uploadMutation.isPending}
        error={uploadError}
      />
    </div>
  )
}
```

Add missing imports to `ProjectDetailPage.tsx`:

```tsx
import { Paperclip } from 'lucide-react'
import AttachmentList, { AttachmentItem } from '../components/AttachmentList'
import FileUploadDropzone from '../components/FileUploadDropzone'
import { attachmentsApi } from '../api/client'
```

- [ ] **Step 3: Verify**

Open a project, expand a task row, confirm attachment upload/list/delete works inside the expanded row.

- [ ] **Step 4: Final commit + push**

```bash
git add frontend/src/pages/ProjectDetailPage.tsx
git commit -m "feat(ui): task attachment upload/list inside expanded task row"
git push
```

---

## Self-Review Checklist

- [x] DB migration: `project_attachments` table + `visibility` on `task_attachments` ✓
- [x] Visibility filtering: team/managers/private logic in `_visibility_filter()` ✓  
- [x] File storage: `uploads/` dir created on startup, served at `/uploads` ✓
- [x] All endpoints: upload, list, delete, update-visibility for both project + task ✓
- [x] `VisibilitySelector` + `VisibilityBadge` both exported from same file — `AttachmentList` imports `{ VisibilityBadge }` correctly ✓
- [x] `AttachmentItem` interface exported from `AttachmentList.tsx` so `TaskAttachmentSection` can import it ✓
- [x] `python-multipart` required for FastAPI file upload ✓
- [x] Physical file deletion on `DELETE` endpoint ✓
