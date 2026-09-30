/**
 * ClientCrm — časová os interakcií s klientom a naplánované úlohy.
 *
 * Dopĺňa to, čo modul dovtedy nevedel: čo sa s klientom dialo a čo sa má stať
 * ďalej. Úlohy sú zámerne oddelené od projektových — nemajú trvanie ani
 * závislosti a do výpočtu kritickej cesty nevstupujú.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Phone, Mail, Users, FileText, StickyNote, MoreHorizontal,
  Plus, Trash2, Check, Circle, CalendarClock,
} from 'lucide-react'
import { clientsApi } from '../api/client'
import { SkeletonLines } from './Skeleton'

interface Props {
  clientId: number
}

interface Activity {
  id: number
  activity_type: string
  subject: string
  body: string
  occurred_at: string
  username: string
  full_name: string | null
}

interface ClientTask {
  id: number
  title: string
  due_date: string | null
  priority: string
  done: boolean
  assignee_name: string | null
  assignee_username: string | null
}

const ACTIVITY_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  call:     { label: 'Hovor',      icon: <Phone size={13} />,           color: 'text-blue-500' },
  email:    { label: 'E-mail',     icon: <Mail size={13} />,            color: 'text-violet-500' },
  meeting:  { label: 'Stretnutie', icon: <Users size={13} />,           color: 'text-green-600' },
  document: { label: 'Dokument',   icon: <FileText size={13} />,        color: 'text-amber-600' },
  note:     { label: 'Poznámka',   icon: <StickyNote size={13} />,      color: 'text-gray-400' },
  other:    { label: 'Iné',        icon: <MoreHorizontal size={13} />,  color: 'text-gray-400' },
}

const PRIORITY_LABEL: Record<string, string> = {
  low: 'Nízka', medium: 'Stredná', high: 'Vysoká', critical: 'Kritická',
}
const PRIORITY_COLOR: Record<string, string> = {
  low:      'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  medium:   'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  high:     'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

function formatDate(value: string | null): string {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('sk-SK', { day: 'numeric', month: 'numeric', year: 'numeric' })
}

function isOverdue(due: string | null): boolean {
  if (!due) return false
  const d = new Date(due)
  if (Number.isNaN(d.getTime())) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return d < today
}

export default function ClientCrm({ clientId }: Props) {
  const qc = useQueryClient()
  const [actForm, setActForm] = useState({ activity_type: 'call', subject: '', body: '' })
  const [taskForm, setTaskForm] = useState({ title: '', due_date: '', priority: 'medium' })
  const [error, setError] = useState('')

  const { data: activities = [], isLoading: loadingActs } = useQuery<Activity[]>({
    queryKey: ['client-activities', clientId],
    queryFn: () => clientsApi.listActivities(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const { data: tasks = [], isLoading: loadingTasks } = useQuery<ClientTask[]>({
    queryKey: ['client-tasks', clientId],
    queryFn: () => clientsApi.listClientTasks(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const refreshActs = () => qc.invalidateQueries({ queryKey: ['client-activities', clientId] })
  const refreshTasks = () => qc.invalidateQueries({ queryKey: ['client-tasks', clientId] })

  const addActivity = useMutation({
    mutationFn: () => clientsApi.addActivity(clientId, actForm),
    onSuccess: () => {
      refreshActs()
      setActForm({ activity_type: actForm.activity_type, subject: '', body: '' })
      setError('')
    },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Nepodarilo sa zapísať'),
  })

  const removeActivity = useMutation({
    mutationFn: (id: number) => clientsApi.deleteActivity(clientId, id),
    onSuccess: refreshActs,
  })

  const addTask = useMutation({
    mutationFn: () => clientsApi.addClientTask(clientId, {
      title: taskForm.title,
      due_date: taskForm.due_date || null,
      priority: taskForm.priority,
    }),
    onSuccess: () => {
      refreshTasks()
      setTaskForm({ title: '', due_date: '', priority: 'medium' })
      setError('')
    },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Nepodarilo sa vytvoriť úlohu'),
  })

  const toggleTask = useMutation({
    mutationFn: ({ id, done }: { id: number; done: boolean }) =>
      clientsApi.setClientTaskDone(clientId, id, done),
    onSuccess: refreshTasks,
  })

  const removeTask = useMutation({
    mutationFn: (id: number) => clientsApi.deleteClientTask(clientId, id),
    onSuccess: refreshTasks,
  })

  const open = tasks.filter(t => !t.done)
  const done = tasks.filter(t => t.done)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

      {/* ── Naplánované úlohy ─────────────────────────────────────────── */}
      <section className="card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <CalendarClock size={15} className="text-brand-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Naplánované úlohy</h3>
          {open.length > 0 && (
            <span className="badge bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400 text-xs">
              {open.length} otvorených
            </span>
          )}
        </div>

        <div className="flex gap-2 flex-wrap">
          <input
            className="input text-sm flex-1 min-w-40"
            placeholder="Čo treba urobiť?"
            value={taskForm.title}
            onChange={e => setTaskForm({ ...taskForm, title: e.target.value })}
            onKeyDown={e => { if (e.key === 'Enter' && taskForm.title.trim()) addTask.mutate() }}
          />
          <input
            type="date"
            className="input text-sm w-36"
            value={taskForm.due_date}
            onChange={e => setTaskForm({ ...taskForm, due_date: e.target.value })}
          />
          <select
            className="input text-sm w-28"
            value={taskForm.priority}
            onChange={e => setTaskForm({ ...taskForm, priority: e.target.value })}
          >
            {Object.entries(PRIORITY_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <button
            onClick={() => addTask.mutate()}
            disabled={!taskForm.title.trim() || addTask.isPending}
            className="btn-primary text-sm px-3 disabled:opacity-50"
          >
            <Plus size={15} />
          </button>
        </div>

        {loadingTasks ? (
          <SkeletonLines rows={3} />
        ) : tasks.length === 0 ? (
          <p className="text-xs text-gray-400 py-4 text-center">
            Zatiaľ žiadne úlohy. Naplánuj prvý krok voči klientovi.
          </p>
        ) : (
          <div className="space-y-1">
            {[...open, ...done].map(t => (
              <div key={t.id} className="flex items-center gap-2 text-sm group py-1">
                <button
                  onClick={() => toggleTask.mutate({ id: t.id, done: !t.done })}
                  className="flex-shrink-0 text-gray-400 hover:text-green-500 transition-colors"
                  title={t.done ? 'Označiť ako nesplnené' : 'Označiť ako hotové'}
                >
                  {t.done
                    ? <Check size={15} className="text-green-500" />
                    : <Circle size={15} />}
                </button>
                <span className={`flex-1 min-w-0 truncate ${
                  t.done ? 'line-through text-gray-400' : 'text-gray-900 dark:text-white'
                }`}>
                  {t.title}
                </span>
                {t.due_date && (
                  <span className={`text-xs flex-shrink-0 ${
                    !t.done && isOverdue(t.due_date) ? 'text-red-500 font-medium' : 'text-gray-400'
                  }`}>
                    {formatDate(t.due_date)}
                  </span>
                )}
                {!t.done && (
                  <span className={`badge text-xs flex-shrink-0 ${PRIORITY_COLOR[t.priority]}`}>
                    {PRIORITY_LABEL[t.priority] ?? t.priority}
                  </span>
                )}
                <button
                  onClick={() => removeTask.mutate(t.id)}
                  className="opacity-0 group-hover:opacity-100 p-0.5 text-gray-300 hover:text-red-500 transition-all flex-shrink-0"
                  title="Zmazať"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Časová os interakcií ──────────────────────────────────────── */}
      <section className="card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <StickyNote size={15} className="text-brand-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">História interakcií</h3>
          {activities.length > 0 && (
            <span className="text-xs text-gray-400">({activities.length})</span>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex gap-2">
            <select
              className="input text-sm w-32"
              value={actForm.activity_type}
              onChange={e => setActForm({ ...actForm, activity_type: e.target.value })}
            >
              {Object.entries(ACTIVITY_META).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
            <input
              className="input text-sm flex-1"
              placeholder="Čoho sa to týkalo?"
              value={actForm.subject}
              onChange={e => setActForm({ ...actForm, subject: e.target.value })}
            />
          </div>
          <textarea
            className="input text-sm w-full resize-none"
            rows={2}
            placeholder="Podrobnosti (voliteľné)"
            value={actForm.body}
            onChange={e => setActForm({ ...actForm, body: e.target.value })}
          />
          <button
            onClick={() => addActivity.mutate()}
            disabled={!actForm.subject.trim() || addActivity.isPending}
            className="btn-primary text-sm w-full disabled:opacity-50"
          >
            {addActivity.isPending ? 'Ukladám…' : 'Zaznamenať'}
          </button>
        </div>

        {error && <p className="text-xs text-red-500">{error}</p>}

        {loadingActs ? (
          <SkeletonLines rows={4} />
        ) : activities.length === 0 ? (
          <p className="text-xs text-gray-400 py-4 text-center">
            Zatiaľ žiadne záznamy. Každý hovor či e-mail sa tu objaví v časovej osi.
          </p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {activities.map(a => {
              const meta = ACTIVITY_META[a.activity_type] ?? ACTIVITY_META.other
              return (
                <div key={a.id} className="flex gap-2.5 group">
                  <span className={`mt-0.5 flex-shrink-0 ${meta.color}`}>{meta.icon}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {a.subject || meta.label}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatDate(a.occurred_at)} · @{a.username}
                      </span>
                    </div>
                    {a.body && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 whitespace-pre-wrap">
                        {a.body}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => removeActivity.mutate(a.id)}
                    className="opacity-0 group-hover:opacity-100 p-0.5 text-gray-300 hover:text-red-500 transition-all flex-shrink-0 self-start"
                    title="Zmazať záznam"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
