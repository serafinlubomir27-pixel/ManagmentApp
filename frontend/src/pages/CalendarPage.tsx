/**
 * CalendarPage — Monthly calendar with task due dates
 * Shows all tasks with due_date for the current user (assigned or in their projects).
 * Color-coded by status, overdue tasks highlighted in red.
 */
import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronLeft, ChevronRight, CalendarDays,
  CheckCircle2, Clock, AlertCircle, Circle, Link2, RefreshCw, Copy, Check,
} from 'lucide-react'
import { api } from '../api/client'

interface CalendarTask {
  id: number
  name: string
  status: string
  due_date: string          // "YYYY-MM-DD"
  project_name: string
  assigned_to: number | null
  project_owner: number
}

// Weekday headers starting Monday (Slovak)
const WEEKDAYS = ['Po', 'Ut', 'St', 'Št', 'Pi', 'So', 'Ne']
const MONTHS_SK = [
  'Január', 'Február', 'Marec', 'Apríl', 'Máj', 'Jún',
  'Júl', 'August', 'September', 'Október', 'November', 'December',
]

// Shift JS Sunday-based weekday to Monday-based (0=Mon … 6=Sun)
function weekdayMon(date: Date): number {
  return (date.getDay() + 6) % 7
}

const STATUS_STYLES: Record<string, { dot: string; text: string; bg: string }> = {
  pending:     { dot: 'bg-gray-400',  text: 'text-gray-700 dark:text-gray-300',  bg: 'bg-gray-100 dark:bg-gray-800' },
  in_progress: { dot: 'bg-blue-500',  text: 'text-blue-700 dark:text-blue-300',  bg: 'bg-blue-50 dark:bg-blue-900/30' },
  completed:   { dot: 'bg-green-500', text: 'text-green-700 dark:text-green-300', bg: 'bg-green-50 dark:bg-green-900/30' },
  blocked:     { dot: 'bg-red-500',   text: 'text-red-700 dark:text-red-300',     bg: 'bg-red-50 dark:bg-red-900/20' },
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  completed:   <CheckCircle2 size={12} className="text-green-500" />,
  in_progress: <Clock size={12} className="text-blue-500" />,
  blocked:     <AlertCircle size={12} className="text-red-500" />,
  pending:     <Circle size={12} className="text-gray-400" />,
}

function statusStyle(s: string) {
  return STATUS_STYLES[s] ?? STATUS_STYLES.pending
}

function isOverdue(dueDateStr: string, status: string) {
  if (status === 'completed') return false
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const due = new Date(dueDateStr)
  return due < today
}

// Build calendar grid: array of 6×7 or 5×7 Date | null cells
function buildCalendarGrid(year: number, month: number): (Date | null)[] {
  const firstDay = new Date(year, month, 1)
  const lastDay  = new Date(year, month + 1, 0)
  const startOffset = weekdayMon(firstDay) // 0=Mon, empty cells before first
  const totalCells  = Math.ceil((startOffset + lastDay.getDate()) / 7) * 7
  const grid: (Date | null)[] = []
  for (let i = 0; i < totalCells; i++) {
    const dayNum = i - startOffset + 1
    if (dayNum < 1 || dayNum > lastDay.getDate()) {
      grid.push(null)
    } else {
      grid.push(new Date(year, month, dayNum))
    }
  }
  return grid
}

function toYMD(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export default function CalendarPage() {
  const today = new Date()
  const [viewYear, setViewYear]   = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth())
  const [selectedDay, setSelectedDay] = useState<string | null>(null)

  const { data, isLoading } = useQuery<{ tasks: CalendarTask[] }>({
    queryKey: ['calendar-tasks'],
    queryFn: () => api.get('/me/calendar').then(r => r.data),
    staleTime: 60_000,
  })

  const tasks = data?.tasks ?? []

  // Index tasks by due_date string
  const tasksByDate = useMemo(() => {
    const map: Record<string, CalendarTask[]> = {}
    for (const t of tasks) {
      if (!t.due_date) continue
      const key = t.due_date.slice(0, 10)
      if (!map[key]) map[key] = []
      map[key].push(t)
    }
    return map
  }, [tasks])

  const grid = useMemo(
    () => buildCalendarGrid(viewYear, viewMonth),
    [viewYear, viewMonth],
  )

  function prevMonth() {
    if (viewMonth === 0) { setViewYear(y => y - 1); setViewMonth(11) }
    else setViewMonth(m => m - 1)
    setSelectedDay(null)
  }
  function nextMonth() {
    if (viewMonth === 11) { setViewYear(y => y + 1); setViewMonth(0) }
    else setViewMonth(m => m + 1)
    setSelectedDay(null)
  }
  function goToday() {
    setViewYear(today.getFullYear())
    setViewMonth(today.getMonth())
    setSelectedDay(toYMD(today))
  }

  const selectedTasks = selectedDay ? (tasksByDate[selectedDay] ?? []) : []

  // Count tasks in this month (for stats)
  const monthStart = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-01`
  const monthEnd   = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${new Date(viewYear, viewMonth + 1, 0).getDate()}`
  const monthTasks = tasks.filter(t => t.due_date >= monthStart && t.due_date <= monthEnd)
  const overdueMonthTasks = monthTasks.filter(t => isOverdue(t.due_date, t.status))
  const completedMonthTasks = monthTasks.filter(t => t.status === 'completed')

  return (
    <div className="max-w-6xl mx-auto space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CalendarDays size={22} className="text-brand-500" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Kalendár úloh</h1>
        </div>
        <button
          onClick={goToday}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          Dnes
        </button>
      </div>

      {/* iCal feed panel */}
      <ICalPanel />

      {/* Month stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{monthTasks.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Úloh tento mesiac</p>
        </div>
        <div className={`card p-3 text-center ${overdueMonthTasks.length > 0 ? 'border-red-200 dark:border-red-800' : ''}`}>
          <p className={`text-2xl font-bold ${overdueMonthTasks.length > 0 ? 'text-red-500' : 'text-gray-900 dark:text-white'}`}>
            {overdueMonthTasks.length}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">Po termíne</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{completedMonthTasks.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Dokončené</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Calendar grid */}
        <div className="lg:col-span-2 card overflow-hidden">
          {/* Month navigation */}
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
            <button
              onClick={prevMonth}
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <ChevronLeft size={18} className="text-gray-500" />
            </button>
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">
              {MONTHS_SK[viewMonth]} {viewYear}
            </h2>
            <button
              onClick={nextMonth}
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <ChevronRight size={18} className="text-gray-500" />
            </button>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 border-b border-gray-100 dark:border-gray-800">
            {WEEKDAYS.map(d => (
              <div key={d} className="py-2 text-center text-xs font-medium text-gray-400 dark:text-gray-500">
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          {isLoading ? (
            <div className="py-20 text-center text-sm text-gray-400">Načítavam…</div>
          ) : (
            <div className="grid grid-cols-7">
              {grid.map((date, idx) => {
                if (!date) {
                  return <div key={`empty-${idx}`} className="min-h-[72px] border-b border-r border-gray-50 dark:border-gray-800/50" />
                }
                const ymd = toYMD(date)
                const dayTasks = tasksByDate[ymd] ?? []
                const isToday = ymd === toYMD(today)
                const isSelected = ymd === selectedDay
                const hasOverdue = dayTasks.some(t => isOverdue(t.due_date, t.status))

                return (
                  <div
                    key={ymd}
                    onClick={() => setSelectedDay(isSelected ? null : ymd)}
                    className={`min-h-[72px] p-1.5 border-b border-r border-gray-50 dark:border-gray-800/50 cursor-pointer transition-colors
                      ${isSelected ? 'bg-brand-50 dark:bg-brand-500/10' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'}`}
                  >
                    {/* Day number */}
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`text-xs font-semibold w-6 h-6 flex items-center justify-center rounded-full
                          ${isToday ? 'bg-brand-500 text-white' : 'text-gray-700 dark:text-gray-300'}
                          ${hasOverdue && !isToday ? 'text-red-500 dark:text-red-400' : ''}`}
                      >
                        {date.getDate()}
                      </span>
                      {dayTasks.length > 0 && (
                        <span className="text-[10px] text-gray-400">{dayTasks.length}</span>
                      )}
                    </div>

                    {/* Task dots / chips */}
                    <div className="space-y-0.5">
                      {dayTasks.slice(0, 3).map(t => {
                        const over = isOverdue(t.due_date, t.status)
                        const s = over ? 'blocked' : t.status
                        const st = statusStyle(s)
                        return (
                          <div
                            key={t.id}
                            className={`flex items-center gap-1 px-1 py-0.5 rounded text-[9px] truncate ${st.bg} ${st.text}`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${st.dot}`} />
                            <span className="truncate">{t.name}</span>
                          </div>
                        )
                      })}
                      {dayTasks.length > 3 && (
                        <div className="text-[9px] text-gray-400 pl-1">+{dayTasks.length - 3} ďalších</div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Side panel — selected day details OR upcoming */}
        <div className="space-y-4">
          {selectedDay ? (
            <div className="card overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                  {new Date(selectedDay + 'T12:00:00').toLocaleDateString('sk-SK', {
                    weekday: 'long', day: 'numeric', month: 'long',
                  })}
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">{selectedTasks.length} úloh</p>
              </div>
              {selectedTasks.length === 0 ? (
                <div className="py-8 text-center text-sm text-gray-400">Žiadne úlohy</div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {selectedTasks.map(t => {
                    const over = isOverdue(t.due_date, t.status)
                    const s = over ? 'blocked' : t.status
                    const st = statusStyle(s)
                    return (
                      <div key={t.id} className={`px-4 py-3 ${over ? 'bg-red-50/50 dark:bg-red-900/10' : ''}`}>
                        <div className="flex items-start gap-2">
                          <span className="mt-0.5 flex-shrink-0">{STATUS_ICON[s] ?? STATUS_ICON.pending}</span>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium truncate ${st.text}`}>{t.name}</p>
                            <p className="text-xs text-gray-400 mt-0.5 truncate">{t.project_name}</p>
                            {over && (
                              <span className="inline-block mt-1 text-[10px] bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-1.5 py-0.5 rounded-full">
                                Po termíne
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            /* Upcoming tasks — next 14 days */
            <UpcomingPanel tasks={tasks} today={today} />
          )}

          {/* Legend */}
          <div className="card p-3 space-y-1.5">
            <p className="text-xs font-medium text-gray-500 mb-2">Legenda</p>
            {Object.entries(STATUS_STYLES).map(([status, s]) => (
              <div key={status} className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                <span className={`w-2.5 h-2.5 rounded-full ${s.dot}`} />
                <span>
                  {{ pending: 'Čaká', in_progress: 'Prebieha', completed: 'Hotová', blocked: 'Blokovaná / Po termíne' }[status]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── iCal feed panel ───────────────────────────────────────────────────────────
function ICalPanel() {
  const queryClient = useQueryClient()
  const [copied, setCopied] = useState(false)

  const { data } = useQuery<{ token: string | null }>({
    queryKey: ['calendar-token'],
    queryFn: () => api.get('/me/calendar-token').then(r => r.data),
    staleTime: Infinity,
  })

  const generateMutation = useMutation({
    mutationFn: () => api.post('/me/calendar-token').then(r => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['calendar-token'] }),
  })

  const token = data?.token
  const baseUrl = import.meta.env.VITE_API_URL ?? window.location.origin + '/api'
  const icalUrl = token ? `${baseUrl}/calendar/${token}.ics` : null

  async function copyUrl() {
    if (!icalUrl) return
    await navigator.clipboard.writeText(icalUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div className="card px-4 py-3 flex flex-col sm:flex-row items-start sm:items-center gap-3">
      <div className="flex items-center gap-2 flex-shrink-0">
        <Link2 size={15} className="text-brand-500" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">iCal Feed</span>
      </div>
      <div className="flex-1 min-w-0">
        {icalUrl ? (
          <div className="flex items-center gap-2">
            <input
              readOnly
              value={icalUrl}
              className="flex-1 min-w-0 text-xs bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 font-mono text-gray-600 dark:text-gray-400 truncate"
            />
            <button
              onClick={copyUrl}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition-colors flex-shrink-0"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? 'Skopírované!' : 'Kopírovať'}
            </button>
            <button
              onClick={() => generateMutation.mutate()}
              title="Regenerovať token (zneplatní starý link)"
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0"
            >
              <RefreshCw size={13} className={generateMutation.isPending ? 'animate-spin' : ''} />
            </button>
          </div>
        ) : (
          <p className="text-xs text-gray-400">Vygeneruj odkaz pre import do Google / Apple Calendar / Outlook</p>
        )}
      </div>
      {!icalUrl && (
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="px-3 py-1.5 text-xs rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition-colors flex-shrink-0"
        >
          {generateMutation.isPending ? 'Generujem…' : 'Generovať iCal link'}
        </button>
      )}
      {icalUrl && (
        <p className="text-[10px] text-gray-400 whitespace-nowrap">
          Pridaj do Google Calendar cez „Iné kalendáre → z URL"
        </p>
      )}
    </div>
  )
}

// ── Upcoming tasks panel ──────────────────────────────────────────────────────
function UpcomingPanel({ tasks, today }: { tasks: CalendarTask[]; today: Date }) {
  const todayYMD = toYMD(today)
  const future = new Date(today)
  future.setDate(future.getDate() + 14)
  const futureYMD = toYMD(future)

  const upcoming = tasks
    .filter(t => t.due_date >= todayYMD && t.due_date <= futureYMD && t.status !== 'completed')
    .sort((a, b) => a.due_date.localeCompare(b.due_date))

  const overdue = tasks
    .filter(t => t.due_date < todayYMD && t.status !== 'completed')
    .sort((a, b) => a.due_date.localeCompare(b.due_date))

  return (
    <div className="space-y-3">
      {overdue.length > 0 && (
        <div className="card overflow-hidden border-red-200 dark:border-red-800">
          <div className="px-4 py-2.5 border-b border-red-100 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
            <h3 className="text-xs font-semibold text-red-700 dark:text-red-400 flex items-center gap-1.5">
              <AlertCircle size={13} /> Po termíne ({overdue.length})
            </h3>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-48 overflow-y-auto">
            {overdue.map(t => (
              <TaskRow key={t.id} task={t} overdue />
            ))}
          </div>
        </div>
      )}

      <div className="card overflow-hidden">
        <div className="px-4 py-2.5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-xs font-semibold text-gray-700 dark:text-gray-300">
            Najbližších 14 dní {upcoming.length > 0 ? `(${upcoming.length})` : ''}
          </h3>
        </div>
        {upcoming.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-400">
            <CalendarDays size={28} className="mx-auto mb-2 opacity-30" />
            Žiadne blížiace sa termíny
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-72 overflow-y-auto">
            {upcoming.map(t => (
              <TaskRow key={t.id} task={t} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function TaskRow({ task, overdue = false }: { task: CalendarTask; overdue?: boolean }) {
  const daysUntil = Math.round(
    (new Date(task.due_date + 'T12:00:00').getTime() - new Date().setHours(0, 0, 0, 0)) / 86_400_000,
  )

  const s = statusStyle(overdue ? 'blocked' : task.status)

  return (
    <div className={`px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${overdue ? 'bg-red-50/30 dark:bg-red-900/5' : ''}`}>
      <span>{STATUS_ICON[overdue ? 'blocked' : task.status] ?? STATUS_ICON.pending}</span>
      <div className="flex-1 min-w-0">
        <p className={`text-xs font-medium truncate ${s.text}`}>{task.name}</p>
        <p className="text-[10px] text-gray-400 truncate">{task.project_name}</p>
      </div>
      <span className={`text-[10px] font-mono flex-shrink-0 ${overdue ? 'text-red-500' : daysUntil === 0 ? 'text-amber-500 font-bold' : 'text-gray-400'}`}>
        {overdue ? `−${Math.abs(daysUntil)}d` : daysUntil === 0 ? 'Dnes!' : `+${daysUntil}d`}
      </span>
    </div>
  )
}
