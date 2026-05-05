/**
 * BurndownChart — Agile-style burndown/burnup chart
 * Shows ideal vs actual task completion over project duration.
 *
 * Uses CPM project duration (from tasks ES/EF) to set X axis.
 * Actual completion is estimated from task due_dates + status.
 */
import { useMemo } from 'react'
import { TrendingDown, CheckCircle2, Circle, Clock } from 'lucide-react'

interface Task {
  id: number
  name: string
  status: string
  due_date?: string | null
  ef?: number
  duration?: number
  is_critical?: boolean
}

interface Props {
  tasks: Task[]
}

const W = 560
const H = 240
const PAD = { top: 16, right: 24, bottom: 40, left: 44 }
const IW = W - PAD.left - PAD.right
const IH = H - PAD.top - PAD.bottom

function lerp(t: number, lo: number, hi: number): number {
  return lo + t * (hi - lo)
}

export default function BurndownChart({ tasks }: Props) {
  const total = tasks.length

  const {
    idealLine,
    actualLine,
    projectDays,
    completedCount,
    inProgressCount,
    pendingCount,
  } = useMemo(() => {
    if (total === 0) {
      return { idealLine: [], actualLine: [], projectDays: 0, completedCount: 0, inProgressCount: 0, pendingCount: 0 }
    }

    // Project duration from max EF, fallback to 30
    const maxEf = Math.max(...tasks.map(t => t.ef ?? 0), 0)
    const projectDays = maxEf > 0 ? maxEf : 30

    const completedCount = tasks.filter(t => t.status === 'completed').length
    const inProgressCount = tasks.filter(t => t.status === 'in_progress').length
    const pendingCount = tasks.filter(t => t.status === 'pending').length

    // Ideal line: linear from total to 0 over projectDays
    const idealLine: { x: number; y: number }[] = []
    for (let d = 0; d <= projectDays; d++) {
      idealLine.push({
        x: PAD.left + (d / projectDays) * IW,
        y: PAD.top + ((total - (total * d / projectDays)) / total) * IH,
      })
    }

    // Actual burndown: we estimate daily completion using due_dates or EF
    // Build a "completion schedule": when do we expect tasks to be done?
    const dayCompleted: Record<number, number> = {}
    for (const t of tasks) {
      const ef = t.ef ?? 0
      const day = ef > 0 ? ef : (t.due_date ? (() => {
        // Convert due_date to project day (days from start)
        const due = new Date(t.due_date + 'T12:00:00')
        const startGuess = new Date()
        startGuess.setDate(startGuess.getDate() - Math.floor(projectDays / 2))
        const diff = Math.round((due.getTime() - startGuess.getTime()) / 86_400_000)
        return Math.max(1, Math.min(projectDays, diff))
      })() : Math.floor(projectDays * 0.7))

      if (!dayCompleted[day]) dayCompleted[day] = 0
      dayCompleted[day]++
    }

    // Build actual line (only show up to "today" estimated as current completion rate)
    // We show: ideal everywhere, actual only for completed portion
    const todayDay = Math.round((completedCount / total) * projectDays)
    let remaining = total
    const actualLine: { x: number; y: number }[] = [
      { x: PAD.left, y: PAD.top + IH }  // Start at day 0, all remaining
    ]

    for (let d = 1; d <= todayDay; d++) {
      const completedOnDay = dayCompleted[d] ?? 0
      remaining = Math.max(0, remaining - completedOnDay)
      actualLine.push({
        x: PAD.left + (d / projectDays) * IW,
        y: PAD.top + (remaining / total) * IH,
      })
    }

    return { idealLine, actualLine, projectDays, completedCount, inProgressCount, pendingCount }
  }, [tasks, total])

  if (total === 0) {
    return (
      <div className="py-12 text-center text-gray-400 text-sm">
        <TrendingDown size={32} className="mx-auto mb-3 opacity-30" />
        <p>Žiadne úlohy na burndown chart</p>
      </div>
    )
  }

  const toPath = (pts: { x: number; y: number }[]): string => {
    if (pts.length === 0) return ''
    return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  }

  // Axis labels
  const xLabels = [0, 0.25, 0.5, 0.75, 1].map(t => ({
    x: PAD.left + t * IW,
    label: `d${Math.round(t * projectDays)}`,
  }))
  const yLabels = [0, 0.25, 0.5, 0.75, 1].map(t => ({
    y: PAD.top + t * IH,
    label: `${Math.round((1 - t) * total)}`,
  }))

  const progress = total > 0 ? Math.round((completedCount / total) * 100) : 0
  const isOnTrack = actualLine.length > 1 && idealLine.length > 0 && (() => {
    const lastActual = actualLine[actualLine.length - 1]
    // Find ideal at same x
    const ratio = (lastActual.x - PAD.left) / IW
    const idealY = PAD.top + (1 - ratio) * IH
    return lastActual.y <= idealY + 10 // within 10px = on track
  })()

  return (
    <div className="space-y-4">
      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3">
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{total}</p>
          <p className="text-xs text-gray-500 mt-0.5">Celkom</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{completedCount}</p>
          <p className="text-xs text-gray-500 mt-0.5">Hotové</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{inProgressCount}</p>
          <p className="text-xs text-gray-500 mt-0.5">Prebieha</p>
        </div>
        <div className={`card p-3 text-center ${isOnTrack ? '' : 'border-amber-200 dark:border-amber-800'}`}>
          <p className={`text-2xl font-bold ${isOnTrack ? 'text-gray-900 dark:text-white' : 'text-amber-600'}`}>
            {progress}%
          </p>
          <p className="text-xs text-gray-500 mt-0.5">Postup</p>
        </div>
      </div>

      {/* Burndown SVG */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <TrendingDown size={15} className="text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Burndown Chart</h3>
          <div className="ml-auto flex items-center gap-3 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <span className="w-6 h-0.5 bg-gray-300 dark:bg-gray-600 inline-block" style={{ borderTop: '2px dashed' }} />
              Ideál
            </span>
            <span className="flex items-center gap-1">
              <span className="w-6 h-0.5 bg-brand-500 inline-block" />
              Skutočný
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <svg width={W} height={H} className="block">
            {/* Grid lines */}
            {yLabels.map((l, i) => (
              <line key={i} x1={PAD.left} y1={l.y} x2={W - PAD.right} y2={l.y}
                stroke="currentColor" strokeWidth={0.5} className="text-gray-100 dark:text-gray-800" />
            ))}

            {/* Axes */}
            <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={H - PAD.bottom}
              stroke="currentColor" strokeWidth={1} className="text-gray-200 dark:text-gray-700" />
            <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom}
              stroke="currentColor" strokeWidth={1} className="text-gray-200 dark:text-gray-700" />

            {/* Ideal line (dashed) */}
            <path d={toPath(idealLine)} fill="none" stroke="#94a3b8" strokeWidth={1.5}
              strokeDasharray="6 4" strokeLinecap="round" />

            {/* Actual area fill */}
            {actualLine.length > 1 && (
              <path
                d={`${toPath(actualLine)} L ${actualLine[actualLine.length-1].x} ${H - PAD.bottom} L ${PAD.left} ${H - PAD.bottom} Z`}
                fill="currentColor" className="text-brand-500/10" />
            )}

            {/* Actual line */}
            {actualLine.length > 1 && (
              <path d={toPath(actualLine)} fill="none" stroke="#6366f1" strokeWidth={2.5}
                strokeLinecap="round" strokeLinejoin="round" />
            )}

            {/* Dots on actual line */}
            {actualLine.map((p, i) => (
              <circle key={i} cx={p.x} cy={p.y} r={2.5} fill="#6366f1" />
            ))}

            {/* Y axis labels */}
            {yLabels.map((l, i) => (
              <text key={i} x={PAD.left - 6} y={l.y + 4} textAnchor="end"
                fontSize={9} className="fill-gray-400">{l.label}</text>
            ))}

            {/* X axis labels */}
            {xLabels.map((l, i) => (
              <text key={i} x={l.x} y={H - PAD.bottom + 14} textAnchor="middle"
                fontSize={9} className="fill-gray-400">{l.label}</text>
            ))}

            {/* Axis titles */}
            <text x={12} y={PAD.top + IH / 2} textAnchor="middle"
              fontSize={9} className="fill-gray-400"
              transform={`rotate(-90, 12, ${PAD.top + IH / 2})`}>
              Zostatok
            </text>
            <text x={PAD.left + IW / 2} y={H - 4} textAnchor="middle"
              fontSize={9} className="fill-gray-400">
              Deň projektu
            </text>
          </svg>
        </div>

        {/* Status indicator */}
        <div className={`mt-3 text-xs flex items-center gap-1.5 ${isOnTrack ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'}`}>
          {isOnTrack
            ? <><CheckCircle2 size={12} /> Projekt beží podľa plánu</>
            : <><Clock size={12} /> Projekt zaostáva za plánovaným tempom</>
          }
        </div>
      </div>

      {/* Task status breakdown */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Stav úloh</h3>
        </div>
        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {['completed', 'in_progress', 'pending', 'blocked'].map(status => {
            const count = tasks.filter(t => t.status === status).length
            if (count === 0) return null
            const pct = Math.round((count / total) * 100)
            const label = { completed: 'Hotové', in_progress: 'Prebieha', pending: 'Čaká', blocked: 'Blokované' }[status]
            const color = { completed: 'bg-green-500', in_progress: 'bg-blue-500', pending: 'bg-gray-300 dark:bg-gray-600', blocked: 'bg-red-500' }[status]
            return (
              <div key={status} className="px-4 py-2.5 flex items-center gap-3">
                <span className="text-xs text-gray-600 dark:text-gray-400 w-20">{label}</span>
                <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="text-xs font-mono text-gray-500 w-12 text-right">{count} ({pct}%)</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
