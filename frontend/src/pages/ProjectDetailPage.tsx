import { useState, Fragment } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Plus, CheckCircle2, Circle, Clock, AlertCircle, Trash2, Search, BarChart2, List, Network, TrendingUp, Users, ChevronDown, ChevronUp } from 'lucide-react'
import { projectsApi, tasksApi, teamApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import GanttChart from '../components/GanttChart'
import NetworkDiagram from '../components/NetworkDiagram'
import CommentSection from '../components/CommentSection'
import PertPanel from '../components/PertPanel'
import ResourcePanel from '../components/ResourcePanel'
import { useRealtimeProject } from '../hooks/useRealtimeProject'

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending:     <Circle size={15} className="text-gray-400" />,
  in_progress: <Clock size={15} className="text-blue-500" />,
  completed:   <CheckCircle2 size={15} className="text-green-500" />,
  blocked:     <AlertCircle size={15} className="text-red-500" />,
}
const STATUS_LABEL: Record<string, string> = {
  pending: 'Čaká', in_progress: 'Prebieha', completed: 'Hotová', blocked: 'Blokovaná',
}
const PRIORITY_COLOR: Record<string, string> = {
  low:      'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  medium:   'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  high:     'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const qc = useQueryClient()
  const { isManager } = useAuth()

  const [tab, setTab] = useState<'tasks' | 'gantt' | 'network' | 'pert' | 'resources'>('tasks')
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null)

  // Supabase Realtime — live aktualizácie úloh a komentárov
  useRealtimeProject(projectId)
  const [newTask, setNewTask] = useState({
    name: '', due_date: '', priority: 'medium', duration: 1, assigned_to: '',
    duration_optimistic: '' as number | '', duration_pessimistic: '' as number | '',
  })
  const [createErr, setCreateErr] = useState('')

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId).then((r) => r.data),
  })

  const { data: dependencies = [] } = useQuery({
    queryKey: ['dependencies', projectId],
    queryFn: () => tasksApi.getProjectDependencies(projectId).then((r) => r.data),
  })

  const { data: teamMembers = [] } = useQuery({
    queryKey: ['team-all'],
    queryFn: () => teamApi.all().then((r) => r.data).catch(() => teamApi.myTeam().then((r) => r.data)),
  })

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => tasksApi.list(projectId).then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: () => tasksApi.create(projectId, {
      ...newTask,
      assigned_to: newTask.assigned_to ? Number(newTask.assigned_to) : null,
      duration_optimistic: newTask.duration_optimistic !== '' ? Number(newTask.duration_optimistic) : null,
      duration_pessimistic: newTask.duration_pessimistic !== '' ? Number(newTask.duration_pessimistic) : null,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks', projectId] })
      setShowCreate(false)
      setNewTask({ name: '', due_date: '', priority: 'medium', duration: 1, assigned_to: '', duration_optimistic: '', duration_pessimistic: '' })
    },
    onError: (e: any) => setCreateErr(e.response?.data?.detail ?? 'Chyba'),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: number; status: string }) =>
      tasksApi.update(taskId, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks', projectId] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (taskId: number) => tasksApi.delete(taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks', projectId] }),
  })

  const filtered = tasks.filter((t: any) =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    (t.assigned_username ?? '').toLowerCase().includes(search.toLowerCase()),
  )

  const criticalCount = tasks.filter((t: any) => t.is_critical).length

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Späť + názov */}
      <div className="flex items-center gap-3">
        <Link to="/projects" className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500">
          <ArrowLeft size={18} />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">{project?.name ?? '…'}</h1>
          {project?.description && (
            <p className="text-sm text-gray-400">{project.description}</p>
          )}
        </div>
      </div>

      {/* CPM info */}
      {criticalCount > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl px-4 py-3 flex items-center gap-2">
          <AlertCircle size={16} className="text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700 dark:text-red-400">
            <strong>{criticalCount} kritických úloh</strong> — oneskorenie predĺži celý projekt
          </p>
        </div>
      )}

      {/* Záložky */}
      <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit flex-wrap">
        <button
          onClick={() => setTab('tasks')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            tab === 'tasks'
              ? 'bg-white dark:bg-surface-dark text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <List size={15} /> Úlohy
        </button>
        <button
          onClick={() => setTab('gantt')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            tab === 'gantt'
              ? 'bg-white dark:bg-surface-dark text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <BarChart2 size={15} /> Gantt
        </button>
        <button
          onClick={() => setTab('network')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            tab === 'network'
              ? 'bg-white dark:bg-surface-dark text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Network size={15} /> Sieťový diagram
        </button>
        <button
          onClick={() => setTab('pert')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            tab === 'pert'
              ? 'bg-white dark:bg-surface-dark text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <TrendingUp size={15} /> PERT
        </button>
        <button
          onClick={() => setTab('resources')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            tab === 'resources'
              ? 'bg-white dark:bg-surface-dark text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Users size={15} /> Zdroje
        </button>
      </div>

      {/* Toolbar (len pre záložku Úlohy) */}
      {tab === 'tasks' && (
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9 text-sm"
            placeholder="Hľadaj úlohu…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {isManager && (
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus size={15} /> Nová úloha
          </button>
        )}
      </div>
      )}

      {/* Gantt záložka */}
      {tab === 'gantt' && (
        <GanttChart tasks={tasks} />
      )}

      {/* Sieťový diagram */}
      {tab === 'network' && (
        <NetworkDiagram tasks={tasks} dependencies={dependencies} />
      )}

      {/* PERT analýza */}
      {tab === 'pert' && (
        <PertPanel projectId={projectId} />
      )}

      {/* Resource Management */}
      {tab === 'resources' && (
        <ResourcePanel projectId={projectId} />
      )}

      {/* Formulár */}
      {tab === 'tasks' && showCreate && (
        <div className="card p-4 space-y-3">
          <h3 className="font-semibold text-sm text-gray-900 dark:text-white">Nová úloha</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              className="input"
              placeholder="Názov úlohy *"
              value={newTask.name}
              onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
            />
            <input
              type="date"
              className="input"
              value={newTask.due_date}
              onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
            />
            <select
              className="input"
              value={newTask.priority}
              onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
            >
              <option value="low">Nízka priorita</option>
              <option value="medium">Stredná priorita</option>
              <option value="high">Vysoká priorita</option>
              <option value="critical">Kritická</option>
            </select>
            <input
              type="number"
              className="input"
              min={1}
              placeholder="Trvanie m (dni) *"
              value={newTask.duration}
              onChange={(e) => setNewTask({ ...newTask, duration: Number(e.target.value) })}
            />
            <select
              className="input"
              value={newTask.assigned_to}
              onChange={(e) => setNewTask({ ...newTask, assigned_to: e.target.value })}
            >
              <option value="">— Nepriradené —</option>
              {teamMembers.map((m: any) => (
                <option key={m.id} value={m.id}>{m.full_name} (@{m.username})</option>
              ))}
            </select>
          </div>

          {/* PERT sekcia */}
          <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1.5">
              <TrendingUp size={12} /> PERT odhady (voliteľné)
            </p>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="number"
                className="input text-sm"
                min={1}
                placeholder="Optimistické a (dni)"
                value={newTask.duration_optimistic}
                onChange={(e) => setNewTask({ ...newTask, duration_optimistic: e.target.value === '' ? '' : Number(e.target.value) })}
              />
              <input
                type="number"
                className="input text-sm"
                min={1}
                placeholder="Pesimistické b (dni)"
                value={newTask.duration_pessimistic}
                onChange={(e) => setNewTask({ ...newTask, duration_pessimistic: e.target.value === '' ? '' : Number(e.target.value) })}
              />
            </div>
          </div>

          {createErr && <p className="text-sm text-red-500">{createErr}</p>}
          <div className="flex gap-2 justify-end">
            <button className="btn-ghost text-sm" onClick={() => setShowCreate(false)}>Zrušiť</button>
            <button
              className="btn-primary text-sm"
              onClick={() => createMutation.mutate()}
              disabled={!newTask.name || createMutation.isPending}
            >
              {createMutation.isPending ? 'Vytváram…' : 'Vytvoriť'}
            </button>
          </div>
        </div>
      )}

      {/* Tabuľka úloh */}
      {tab === 'tasks' && <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
              <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-400">Úloha</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-400 hidden sm:table-cell">Priradený</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-400">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-400 hidden md:table-cell">CPM</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {isLoading ? (
              <tr><td colSpan={5} className="py-8 text-center text-gray-400">Načítavam…</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={5} className="py-8 text-center text-gray-400">Žiadne úlohy</td></tr>
            ) : (
              filtered.map((t: any) => (
                <Fragment key={t.id}>
                  <tr
                    className={`cursor-pointer ${t.is_critical ? 'bg-red-50/50 dark:bg-red-900/10' : 'hover:bg-gray-50 dark:hover:bg-gray-900/30'}`}
                    onClick={() => setExpandedTaskId(expandedTaskId === t.id ? null : t.id)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {t.is_critical && (
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                        )}
                        <span className="font-medium text-gray-900 dark:text-white">{t.name}</span>
                        {expandedTaskId === t.id
                          ? <ChevronUp size={13} className="text-gray-400 flex-shrink-0" />
                          : <ChevronDown size={13} className="text-gray-300 flex-shrink-0" />
                        }
                      </div>
                      <span className={`badge mt-1 ${PRIORITY_COLOR[t.priority] ?? PRIORITY_COLOR.medium}`}>
                        {t.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400 hidden sm:table-cell">
                      {t.assigned_username ?? '—'}
                    </td>
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      {isManager ? (
                        <select
                          className="text-xs border border-gray-200 dark:border-gray-700 rounded-lg px-2 py-1 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300"
                          value={t.status}
                          onChange={(e) => updateStatusMutation.mutate({ taskId: t.id, status: e.target.value })}
                        >
                          {Object.entries(STATUS_LABEL).map(([v, l]) => (
                            <option key={v} value={v}>{l}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
                          {STATUS_ICONS[t.status]} {STATUS_LABEL[t.status]}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      {t.es != null ? (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          ES {t.es} — EF {t.ef} | Float {t.total_float}d
                          {t.duration_optimistic && (
                            <span className="ml-1 text-blue-400">PERT ✓</span>
                          )}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      {isManager && (
                        <button
                          onClick={() => { if (confirm('Zmazať úlohu?')) deleteMutation.mutate(t.id) }}
                          className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 size={15} />
                        </button>
                      )}
                    </td>
                  </tr>
                  {expandedTaskId === t.id && (
                    <tr className="bg-gray-50/50 dark:bg-gray-900/20">
                      <td colSpan={5} className="px-6 py-4">
                        <CommentSection taskId={t.id} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>}
    </div>
  )
}
