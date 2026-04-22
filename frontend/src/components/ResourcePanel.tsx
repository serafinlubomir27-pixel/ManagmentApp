/**
 * ResourcePanel — Resource Management
 * Zobrazuje vyťaženosť členov tímu v čase na základe CPM ES/EF hodnôt.
 * Detekuje over-allocation (paralelné úlohy tej istej osoby).
 */
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { Users, AlertTriangle, CheckCircle2, BarChart2 } from 'lucide-react'

interface TaskAlloc {
  id: number
  name: string
  es: number
  ef: number
  duration: number
  status: string
  is_critical: boolean
}

interface PersonAlloc {
  user_id: number
  username: string
  tasks: TaskAlloc[]
  task_count: number
  over_allocated_days: number
  peak_load: number
  daily_load: number[]
}

interface ResourceResult {
  people: PersonAlloc[]
  project_duration: number
  over_allocated_days: number
  total_assigned_tasks: number
}

const STATUS_COLOR: Record<string, string> = {
  pending:     'bg-gray-300 dark:bg-gray-600',
  in_progress: 'bg-blue-400',
  completed:   'bg-green-400',
  blocked:     'bg-red-400',
}

function getInitials(name: string) {
  return name.split(/[\s_]/).map(n => n[0]).slice(0, 2).join('').toUpperCase()
}

/** Mini Gantt bar for one person's tasks */
function PersonTimeline({ person, totalDays }: { person: PersonAlloc; totalDays: number }) {
  if (totalDays === 0) return null
  const cellW = Math.max(8, Math.min(24, Math.floor(560 / totalDays)))

  return (
    <div className="relative" style={{ height: 28 }}>
      {/* Background grid — over-allocated days in amber */}
      <div className="absolute inset-0 flex">
        {person.daily_load.map((load, day) => (
          <div
            key={day}
            style={{ width: cellW, minWidth: cellW, height: 28 }}
            className={
              load > 1
                ? 'bg-amber-100 dark:bg-amber-900/30 border-r border-amber-200 dark:border-amber-800'
                : 'border-r border-gray-100 dark:border-gray-800/50'
            }
          />
        ))}
      </div>

      {/* Task bars */}
      {person.tasks.map(t => {
        const left = t.es * cellW
        const width = Math.max(cellW, (t.ef - t.es) * cellW - 2)
        return (
          <div
            key={t.id}
            title={`${t.name} (deň ${t.es}–${t.ef})`}
            style={{ left, width, top: 4, height: 20, position: 'absolute' }}
            className={`rounded-sm text-white text-[9px] flex items-center px-1 overflow-hidden truncate
              ${t.is_critical ? 'bg-red-500' : STATUS_COLOR[t.status] ?? 'bg-blue-400'}`}
          >
            {width > 30 ? t.name : ''}
          </div>
        )
      })}
    </div>
  )
}

interface Props {
  projectId: number
}

export default function ResourcePanel({ projectId }: Props) {
  const { data, isLoading, error } = useQuery<ResourceResult>({
    queryKey: ['resources', projectId],
    queryFn: () => api.get(`/projects/${projectId}/resources`).then(r => r.data),
    staleTime: 30_000,
  })

  if (isLoading) {
    return <div className="py-12 text-center text-gray-400 text-sm">Načítavam resource data…</div>
  }
  if (error || !data) {
    return <div className="py-12 text-center text-red-400 text-sm">Chyba pri načítaní zdrojov</div>
  }
  if (data.people.length === 0) {
    return (
      <div className="py-12 text-center text-gray-400 text-sm">
        <Users size={32} className="mx-auto mb-3 opacity-30" />
        <p>Žiadne priradené úlohy s CPM dátami</p>
        <p className="text-xs mt-1 text-gray-300">Pridaj závislosti medzi úlohami pre výpočet ES/EF</p>
      </div>
    )
  }

  const overAllocPeople = data.people.filter(p => p.over_allocated_days > 0)

  return (
    <div className="space-y-5">

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{data.people.length}</p>
          <p className="text-xs text-gray-500 mt-1">Členov tímu</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{data.total_assigned_tasks}</p>
          <p className="text-xs text-gray-500 mt-1">Priradených úloh</p>
        </div>
        <div className={`card p-4 text-center ${data.over_allocated_days > 0 ? 'border-amber-200 dark:border-amber-800' : ''}`}>
          <p className={`text-2xl font-bold ${data.over_allocated_days > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-900 dark:text-white'}`}>
            {data.over_allocated_days}
          </p>
          <p className="text-xs text-gray-500 mt-1">Over-alloc. dní</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{data.project_duration}d</p>
          <p className="text-xs text-gray-500 mt-1">Trvanie projektu</p>
        </div>
      </div>

      {/* Over-allocation warning */}
      {overAllocPeople.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl px-4 py-3 flex items-start gap-2">
          <AlertTriangle size={15} className="text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-700 dark:text-amber-400">
            <strong>Over-allocation detekovaná</strong> —{' '}
            {overAllocPeople.map(p => p.username).join(', ')} má súbežné úlohy.
            <span className="block text-xs mt-0.5 text-amber-600 dark:text-amber-500">
              Žlté bunky v grafe označujú dni s viacerými úlohami naraz.
            </span>
          </div>
        </div>
      )}

      {/* Timeline legend */}
      <div className="flex items-center gap-4 flex-wrap text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-red-500 inline-block" /> Kritická</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-blue-400 inline-block" /> Prebieha</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-green-400 inline-block" /> Hotová</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-gray-300 dark:bg-gray-600 inline-block" /> Čaká</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-amber-100 dark:bg-amber-900/40 border border-amber-300 inline-block" /> Over-alloc.</span>
      </div>

      {/* Resource timeline per person */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
          <BarChart2 size={15} className="text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Vyťaženosť tímu v čase</h3>
          <span className="text-xs text-gray-400 ml-auto">deň 0 → {data.project_duration}</span>
        </div>

        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {data.people.map(person => (
            <div key={person.user_id} className="px-4 py-3 flex items-center gap-4">
              {/* Avatar + meno */}
              <div className="flex items-center gap-2 w-28 flex-shrink-0">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0
                  ${person.over_allocated_days > 0 ? 'bg-amber-500' : 'bg-blue-500'}`}>
                  {getInitials(person.username)}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-900 dark:text-white truncate">@{person.username}</p>
                  <p className="text-[10px] text-gray-400">{person.task_count} úloh</p>
                </div>
              </div>

              {/* Timeline */}
              <div className="flex-1 overflow-x-auto">
                <PersonTimeline person={person} totalDays={data.project_duration} />
              </div>

              {/* Status badge */}
              <div className="flex-shrink-0 w-20 text-right">
                {person.over_allocated_days > 0 ? (
                  <span className="text-xs text-amber-600 dark:text-amber-400 flex items-center justify-end gap-1">
                    <AlertTriangle size={11} /> {person.over_allocated_days}d
                  </span>
                ) : (
                  <span className="text-xs text-green-600 dark:text-green-400 flex items-center justify-end gap-1">
                    <CheckCircle2 size={11} /> OK
                  </span>
                )}
                <span className="text-[10px] text-gray-400">peak: {person.peak_load}x</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Per-person task breakdown */}
      <div className="space-y-3">
        {data.people.map(person => (
          <div key={person.user_id} className="card overflow-hidden">
            <div className="px-4 py-2.5 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold
                ${person.over_allocated_days > 0 ? 'bg-amber-500' : 'bg-blue-500'}`}>
                {getInitials(person.username)}
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">@{person.username}</span>
              {person.over_allocated_days > 0 && (
                <span className="badge bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 text-xs ml-1">
                  {person.over_allocated_days} over-alloc. dní
                </span>
              )}
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400">
                  <th className="text-left px-4 py-2 font-medium">Úloha</th>
                  <th className="text-center px-3 py-2 font-medium">ES</th>
                  <th className="text-center px-3 py-2 font-medium">EF</th>
                  <th className="text-center px-3 py-2 font-medium">Trvanie</th>
                  <th className="text-left px-3 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {person.tasks.map(t => (
                  <tr key={t.id} className={t.is_critical ? 'bg-red-50/40 dark:bg-red-900/10' : ''}>
                    <td className="px-4 py-2 font-medium text-gray-900 dark:text-white flex items-center gap-1.5">
                      {t.is_critical && <span className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />}
                      {t.name}
                    </td>
                    <td className="px-3 py-2 text-center font-mono text-gray-600 dark:text-gray-400">d{t.es}</td>
                    <td className="px-3 py-2 text-center font-mono text-gray-600 dark:text-gray-400">d{t.ef}</td>
                    <td className="px-3 py-2 text-center font-mono text-gray-600 dark:text-gray-400">{t.duration}d</td>
                    <td className="px-3 py-2">
                      <span className={`inline-block w-2 h-2 rounded-full mr-1 ${STATUS_COLOR[t.status] ?? 'bg-gray-300'}`} />
                      {t.status}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  )
}
