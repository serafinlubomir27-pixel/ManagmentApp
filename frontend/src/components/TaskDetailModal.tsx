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
import { tasksApi, attachmentsApi } from '../api/client'
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
