/**
 * TimeLogSection — log and view time entries for a task.
 * Shown in the expanded task row in ProjectDetailPage.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Clock, Plus, Trash2, AlertCircle } from 'lucide-react'
import { api } from '../api/client'

interface TimeLog {
  id: number
  hours: number
  log_date: string
  note: string | null
  username: string
  full_name: string
  created_at: string
}

interface Props {
  taskId: number
  estimatedHours?: number | null
}

function toYMD(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export default function TimeLogSection({ taskId, estimatedHours }: Props) {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ hours: '', log_date: toYMD(new Date()), note: '' })
  const [err, setErr] = useState('')

  const { data, isLoading } = useQuery<{ logs: TimeLog[]; total_hours: number }>({
    queryKey: ['time-logs', taskId],
    queryFn: () => api.get(`/tasks/${taskId}/time`).then(r => r.data),
    staleTime: 30_000,
  })

  const logMutation = useMutation({
    mutationFn: () => api.post(`/tasks/${taskId}/time`, {
      hours: Number(form.hours),
      log_date: form.log_date,
      note: form.note,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['time-logs', taskId] })
      setShowForm(false)
      setForm({ hours: '', log_date: toYMD(new Date()), note: '' })
      setErr('')
    },
    onError: (e: any) => setErr(e.response?.data?.detail ?? 'Chyba'),
  })

  const deleteMutation = useMutation({
    mutationFn: (logId: number) => api.delete(`/time-logs/${logId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['time-logs', taskId] }),
  })

  const handleLog = () => {
    setErr('')
    const h = Number(form.hours)
    if (!h || h <= 0) { setErr('Zadaj kladný počet hodín'); return }
    if (!form.log_date) { setErr('Zadaj dátum'); return }
    logMutation.mutate()
  }

  const total = data?.total_hours ?? 0
  const estimated = estimatedHours ?? null
  const overBudget = estimated !== null && total > estimated

  return (
    <div className="space-y-3">
      {/* Header + stats */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400">
          <Clock size={12} /> Time tracking
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className={`font-mono font-bold ${overBudget ? 'text-red-500' : 'text-gray-700 dark:text-gray-300'}`}>
            {total.toFixed(1)}h logged
          </span>
          {estimated !== null && (
            <span className="text-gray-400">
              / {estimated}h estimate
              {overBudget && <span className="text-red-500 ml-1 flex items-center gap-0.5 inline-flex"><AlertCircle size={9} /> Over budget!</span>}
            </span>
          )}
        </div>

        {/* Progress bar */}
        {estimated !== null && estimated > 0 && (
          <div className="flex-1 min-w-20 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${overBudget ? 'bg-red-500' : 'bg-brand-500'}`}
              style={{ width: `${Math.min(100, (total / estimated) * 100).toFixed(0)}%` }}
            />
          </div>
        )}

        <button
          onClick={() => setShowForm(!showForm)}
          className="ml-auto flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 hover:underline"
        >
          <Plus size={11} /> Zaznamenať čas
        </button>
      </div>

      {/* Log form */}
      {showForm && (
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 space-y-2">
          <div className="flex gap-2 flex-wrap">
            <input
              type="number"
              step="0.5"
              min="0.5"
              className="input text-sm w-24"
              placeholder="Hodiny"
              value={form.hours}
              onChange={e => setForm({ ...form, hours: e.target.value })}
            />
            <input
              type="date"
              className="input text-sm flex-1 min-w-32"
              value={form.log_date}
              onChange={e => setForm({ ...form, log_date: e.target.value })}
            />
            <input
              className="input text-sm flex-1 min-w-40"
              placeholder="Poznámka (voliteľné)"
              value={form.note}
              onChange={e => setForm({ ...form, note: e.target.value })}
            />
          </div>
          {err && <p className="text-xs text-red-500">{err}</p>}
          <div className="flex gap-2">
            <button
              onClick={handleLog}
              disabled={logMutation.isPending}
              className="btn-primary text-xs py-1 px-3"
            >
              {logMutation.isPending ? 'Ukladám…' : 'Uložiť'}
            </button>
            <button onClick={() => setShowForm(false)} className="btn-ghost text-xs py-1 px-3">
              Zrušiť
            </button>
          </div>
        </div>
      )}

      {/* Log list */}
      {isLoading ? (
        <p className="text-xs text-gray-400">Načítavam…</p>
      ) : (data?.logs ?? []).length > 0 ? (
        <div className="space-y-1">
          {(data?.logs ?? []).slice(0, 8).map(log => (
            <div key={log.id} className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 group">
              <span className="font-mono text-gray-900 dark:text-white w-10 text-right">{log.hours}h</span>
              <span className="text-gray-300 dark:text-gray-700">·</span>
              <span className="text-gray-400">{log.log_date}</span>
              <span className="text-gray-300 dark:text-gray-700">·</span>
              <span>@{log.username}</span>
              {log.note && <span className="text-gray-400 italic truncate flex-1">— {log.note}</span>}
              <button
                onClick={() => deleteMutation.mutate(log.id)}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-gray-300 hover:text-red-500 transition-all ml-auto flex-shrink-0"
                title="Zmazať záznam"
              >
                <Trash2 size={10} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-400">Žiadne záznamy</p>
      )}
    </div>
  )
}
