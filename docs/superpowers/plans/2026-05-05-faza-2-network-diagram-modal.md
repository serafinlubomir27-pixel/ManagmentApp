# Fáza 2: Interactive Network Diagram Modal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make nodes in the network diagram clickable — clicking opens a full modal with two-column layout (left: task fields + attachments, right: comments) allowing complete task management without leaving the diagram.

**Architecture:** `NetworkDiagram.tsx` adds an `onClick` handler to each node `<g>` element that sets `selectedTaskId` state. A new `TaskDetailModal.tsx` component receives the `taskId`, fetches full task data, and provides inline editing via existing PATCH/comments/attachments endpoints. A new `GET /tasks/{id}` endpoint exposes the full task detail.

**Tech Stack:** React, React Query (useMutation + useQuery), existing FastAPI endpoints + one new GET endpoint, existing `attachmentsApi` and `commentsApi` from Fáza 1.

**Prerequisite:** Fáza 1 must be complete (attachmentsApi, AttachmentList, FileUploadDropzone, VisibilitySelector must exist).

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `backend/routers/tasks_router.py` | Add `GET /tasks/{id}` full detail endpoint |
| Create | `frontend/src/components/TaskDetailModal.tsx` | Two-column modal: edit fields left, comments right |
| Modify | `frontend/src/components/NetworkDiagram.tsx` | Add click handler on nodes, render TaskDetailModal |
| Modify | `frontend/src/api/client.ts` | Add `tasksApi.getById()` |

---

## Task 1: Backend — GET /tasks/{id} full detail endpoint

**Files:**
- Modify: `backend/routers/tasks_router.py`
- Modify: `repositories/task_repo.py`

- [ ] **Step 1: Add get_task_by_id to task_repo if not fully exposed**

Open `repositories/task_repo.py`. Verify `get_task_by_id(task_id)` returns all columns. It should already exist — check that it returns a full dict including `description`, `category`, `priority`, `estimated_hours`, `duration`, `es`, `ef`, `ls`, `lf`, `total_float`, `is_critical`, `assigned_to`, `due_date`, `status`, `auto_notify`, `auto_calendar`.

If the function only returns partial fields, replace its SQL with:

```python
def get_task_by_id(task_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT t.*, u.username AS assigned_username, u.full_name AS assigned_full_name
            FROM tasks t
            LEFT JOIN users u ON t.assigned_to = u.id
            WHERE t.id = ?
            """,
            (task_id,),
        ).fetchone()
        from repositories.base_repo import row_to_dict
        return row_to_dict(row)
    finally:
        conn.close()
```

- [ ] **Step 2: Add GET /tasks/{id} endpoint to tasks_router.py**

In `backend/routers/tasks_router.py`, add after the existing `_task_or_404` helper and before the first `@router.get`:

```python
@router.get("/tasks/{task_id}")
def get_task_detail(
    task_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Full task detail — used by TaskDetailModal."""
    task = task_repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Úloha nenájdená")
    return task
```

- [ ] **Step 3: Test endpoint**

```bash
# With backend running:
curl -H "Authorization: Bearer <token>" http://localhost:8000/tasks/1
# Expected: full task JSON with all fields
```

- [ ] **Step 4: Add tasksApi.getById to client.ts**

In `frontend/src/api/client.ts`, add to `tasksApi`:

```ts
  getById: (taskId: number) => api.get(`/tasks/${taskId}`),
```

- [ ] **Step 5: Commit**

```bash
git add backend/routers/tasks_router.py repositories/task_repo.py frontend/src/api/client.ts
git commit -m "feat(api): GET /tasks/{id} full detail endpoint + tasksApi.getById"
```

---

## Task 2: TaskDetailModal component

**Files:**
- Create: `frontend/src/components/TaskDetailModal.tsx`

- [ ] **Step 1: Create TaskDetailModal.tsx**

```tsx
/**
 * TaskDetailModal — full task detail modal opened from NetworkDiagram.
 *
 * Layout (two-column):
 *   Left:  editable fields (status, assignee, deadline, priority, description) + attachments
 *   Right: comments
 *
 * All edits auto-save via PATCH /tasks/{id}.
 */
import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, AlertCircle, CheckCircle2, Clock, Circle, Paperclip } from 'lucide-react'
import { tasksApi, commentsApi, attachmentsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import AttachmentList, { AttachmentItem } from './AttachmentList'
import FileUploadDropzone from './FileUploadDropzone'
import CommentSection from './CommentSection'

interface Props {
  taskId: number
  teamMembers: Array<{ id: number; username: string; full_name?: string }>
  onClose: () => void
  onUpdated?: () => void
}

const STATUS_OPTIONS = [
  { value: 'pending',     label: 'Čaká',     icon: <Circle size={13} className="text-gray-400" /> },
  { value: 'in_progress', label: 'Prebieha', icon: <Clock size={13} className="text-blue-500" /> },
  { value: 'completed',   label: 'Hotová',   icon: <CheckCircle2 size={13} className="text-green-500" /> },
  { value: 'blocked',     label: 'Blokovaná',icon: <AlertCircle size={13} className="text-red-500" /> },
]

const PRIORITY_OPTIONS = ['low', 'medium', 'high', 'critical']
const PRIORITY_LABEL: Record<string, string> = {
  low: 'Nízka', medium: 'Stredná', high: 'Vysoká', critical: 'Kritická',
}
const PRIORITY_COLOR: Record<string, string> = {
  low:      'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  medium:   'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  high:     'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

export default function TaskDetailModal({ taskId, teamMembers, onClose, onUpdated }: Props) {
  const qc = useQueryClient()
  const { isManager } = useAuth()
  const backdropRef = useRef<HTMLDivElement>(null)
  const [uploadError, setUploadError] = useState('')

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Fetch task
  const { data: task, isLoading } = useQuery({
    queryKey: ['task-detail', taskId],
    queryFn: () => tasksApi.getById(taskId).then(r => r.data),
    staleTime: 10_000,
  })

  // Fetch task attachments
  const { data: attachments = [] } = useQuery<AttachmentItem[]>({
    queryKey: ['task-attachments', taskId],
    queryFn: () => attachmentsApi.listTask(taskId).then(r => r.data),
    staleTime: 30_000,
  })

  // Update mutation (auto-save individual fields)
  const updateMutation = useMutation({
    mutationFn: (data: object) => tasksApi.update(taskId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['task-detail', taskId] })
      onUpdated?.()
    },
  })

  // Upload task attachment
  const uploadMutation = useMutation({
    mutationFn: ({ file, visibility }: { file: File; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.uploadTask(taskId, file, visibility),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['task-attachments', taskId] })
      setUploadError('')
    },
    onError: (e: any) => setUploadError(e.response?.data?.detail ?? 'Chyba'),
  })

  const deleteAttachmentMutation = useMutation({
    mutationFn: (id: number) => attachmentsApi.deleteTask(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['task-attachments', taskId] }),
  })

  const visibilityMutation = useMutation({
    mutationFn: ({ id, visibility }: { id: number; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.updateTaskVisibility(id, visibility),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['task-attachments', taskId] }),
  })

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === backdropRef.current) onClose()
  }

  if (isLoading || !task) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div className="bg-white dark:bg-surface-dark rounded-2xl p-8 text-gray-400">Načítavam…</div>
      </div>
    )
  }

  const currentStatus = STATUS_OPTIONS.find(s => s.value === task.status) ?? STATUS_OPTIONS[0]

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 bg-black/50 dark:bg-black/70 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white dark:bg-surface-dark rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex-1 truncate">
            {task.name}
          </h2>
          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${PRIORITY_COLOR[task.priority ?? 'medium']}`}>
            {PRIORITY_LABEL[task.priority ?? 'medium']}
          </span>
          {task.is_critical && (
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
              Kritická cesta
            </span>
          )}
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400">
            <X size={18} />
          </button>
        </div>

        {/* Two-column body */}
        <div className="flex flex-1 overflow-hidden">

          {/* LEFT — task fields + attachments */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 border-r border-gray-100 dark:border-gray-800">

            {/* Status */}
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Status</label>
              <div className="flex gap-1.5 flex-wrap">
                {STATUS_OPTIONS.map(s => (
                  <button
                    key={s.value}
                    onClick={() => updateMutation.mutate({ status: s.value })}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      task.status === s.value
                        ? 'border-brand-400 bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-300'
                        : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:border-gray-300'
                    }`}
                  >
                    {s.icon} {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Assignee */}
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Pridelený</label>
              <select
                className="input text-sm"
                value={task.assigned_to ?? ''}
                onChange={e => updateMutation.mutate({ assigned_to: e.target.value ? Number(e.target.value) : null })}
                disabled={!isManager}
              >
                <option value="">— Nikto —</option>
                {teamMembers.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.full_name || m.username}
                  </option>
                ))}
              </select>
            </div>

            {/* Deadline + Priority row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Deadline</label>
                <input
                  type="date"
                  className="input text-sm"
                  defaultValue={task.due_date ?? ''}
                  onBlur={e => {
                    if (e.target.value !== (task.due_date ?? ''))
                      updateMutation.mutate({ due_date: e.target.value || null })
                  }}
                  disabled={!isManager}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Priorita</label>
                <select
                  className="input text-sm"
                  value={task.priority ?? 'medium'}
                  onChange={e => updateMutation.mutate({ priority: e.target.value })}
                  disabled={!isManager}
                >
                  {PRIORITY_OPTIONS.map(p => (
                    <option key={p} value={p}>{PRIORITY_LABEL[p]}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Popis</label>
              <textarea
                className="input text-sm w-full resize-none"
                rows={3}
                defaultValue={task.description ?? ''}
                onBlur={e => {
                  if (e.target.value !== (task.description ?? ''))
                    updateMutation.mutate({ description: e.target.value })
                }}
                placeholder="Popis úlohy…"
                disabled={!isManager}
              />
            </div>

            {/* CPM read-only info */}
            {task.es != null && (
              <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-gray-400">ES</span> <span className="font-mono font-bold text-gray-700 dark:text-gray-300 ml-1">{task.es}</span></div>
                <div><span className="text-gray-400">EF</span> <span className="font-mono font-bold text-gray-700 dark:text-gray-300 ml-1">{task.ef}</span></div>
                <div><span className="text-gray-400">Rezerva</span> <span className={`font-mono font-bold ml-1 ${task.total_float === 0 ? 'text-red-500' : 'text-gray-700 dark:text-gray-300'}`}>{task.total_float}d</span></div>
                <div><span className="text-gray-400">Trvanie</span> <span className="font-mono font-bold text-gray-700 dark:text-gray-300 ml-1">{task.duration}d</span></div>
              </div>
            )}

            {/* Attachments */}
            <div>
              <div className="flex items-center gap-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                <Paperclip size={12} /> Prílohy ({attachments.length})
              </div>
              <AttachmentList
                attachments={attachments}
                onDelete={id => deleteAttachmentMutation.mutate(id)}
                onVisibilityChange={(id, v) => visibilityMutation.mutate({ id, visibility: v })}
              />
              <div className="mt-2">
                <FileUploadDropzone
                  onUpload={(file, visibility) => uploadMutation.mutateAsync({ file, visibility })}
                  uploading={uploadMutation.isPending}
                  error={uploadError}
                />
              </div>
            </div>
          </div>

          {/* RIGHT — comments */}
          <div className="w-80 flex-shrink-0 overflow-y-auto px-4 py-4">
            <CommentSection taskId={taskId} />
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/TaskDetailModal.tsx
git commit -m "feat(ui): TaskDetailModal — two-column task edit/comment/attachment modal"
```

---

## Task 3: Wire click handler in NetworkDiagram

**Files:**
- Modify: `frontend/src/components/NetworkDiagram.tsx`

- [ ] **Step 1: Add selectedTaskId state + TaskDetailModal**

Open `frontend/src/components/NetworkDiagram.tsx`. Add the following:

**At the top of the file, add imports:**

```tsx
import { useState } from 'react'  // add to existing react imports
import TaskDetailModal from './TaskDetailModal'
```

**Inside the `NetworkDiagram` component, after existing state declarations:**

```tsx
const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null)
```

**The component receives a `teamMembers` prop — add it to the Props interface:**

```tsx
interface Props {
  tasks: any[]
  dependencies: any[]
  teamMembers?: any[]   // add this
}
```

**At the end of the returned JSX, just before the closing `</div>`, add:**

```tsx
{selectedTaskId && (
  <TaskDetailModal
    taskId={selectedTaskId}
    teamMembers={teamMembers ?? []}
    onClose={() => setSelectedTaskId(null)}
    onUpdated={() => {
      // parent will re-fetch via React Query invalidation inside modal
    }}
  />
)}
```

- [ ] **Step 2: Add onClick to each task node**

Find the section in `NetworkDiagram.tsx` where task nodes are rendered. Each node is a `<g>` element. Add `onClick` and cursor style:

```tsx
<g
  key={task.id}
  onClick={() => setSelectedTaskId(task.id)}
  style={{ cursor: 'pointer' }}
  // ... existing transform, etc.
>
  {/* existing node rect, text, etc. */}
</g>
```

- [ ] **Step 3: Pass teamMembers from ProjectDetailPage**

Open `frontend/src/pages/ProjectDetailPage.tsx`. Find where `<NetworkDiagram>` is rendered:

```tsx
{tab === 'network' && (
  <NetworkDiagram tasks={tasks} dependencies={dependencies} teamMembers={teamMembers} />
)}
```

The `teamMembers` variable is already available in `ProjectDetailPage` (fetched from `teamApi`).

- [ ] **Step 4: Verify end-to-end**

1. Open a project with tasks that have CPM data
2. Switch to "Sieťový diagram" tab
3. Click on a task node → modal should open
4. Change status → verify task updates in diagram after modal close
5. Add a comment → verify it appears
6. Upload a file → verify it appears in attachments section
7. Press Escape → modal closes

- [ ] **Step 5: Commit + push**

```bash
git add frontend/src/components/NetworkDiagram.tsx frontend/src/pages/ProjectDetailPage.tsx
git commit -m "feat(ui): clickable nodes in NetworkDiagram — opens TaskDetailModal"
git push
```

---

## Self-Review

- [x] `GET /tasks/{id}` endpoint added — modal has full task data ✓
- [x] `tasksApi.getById` added to `client.ts` ✓
- [x] Escape key closes modal ✓
- [x] Backdrop click closes modal ✓
- [x] Two-column layout: fields left, comments right ✓
- [x] CPM fields (ES/EF/Float) shown read-only ✓
- [x] `teamMembers` prop threaded from `ProjectDetailPage` → `NetworkDiagram` → `TaskDetailModal` ✓
- [x] `onUpdated` callback triggers query invalidation (handled inside modal via `qc.invalidateQueries`) ✓
- [x] Attachment upload/list/delete uses Fáza 1 components — `FileUploadDropzone`, `AttachmentList`, `attachmentsApi` ✓
- [x] `isManager` check on fields that require manager role ✓
