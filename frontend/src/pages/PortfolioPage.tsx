/**
 * PortfolioPage — Cross-project overview with health scoring.
 * Shows all projects with progress, health score, risk indicators.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  LayoutGrid, AlertTriangle, CheckCircle2, TrendingUp,
  FolderKanban, ChevronRight, Flame, Clock, Shield,
} from 'lucide-react'
import { api } from '../api/client'
import RiskScoreWidget from '../components/RiskScoreWidget'

interface ProjectHealth {
  id: number
  name: string
  description: string | null
  status: string
  total_tasks: number
  completed_tasks: number
  in_progress_tasks: number
  blocked_tasks: number
  critical_tasks: number
  overdue_tasks: number
  progress: number
  health_score: number
  project_duration: number
  is_at_risk: boolean
}

interface PortfolioData {
  projects: ProjectHealth[]
  summary: {
    total: number
    active: number
    completed: number
    at_risk: number
    total_tasks: number
    total_completed: number
    overall_progress: number
  }
}

function HealthBadge({ score }: { score: number }) {
  if (score >= 75) return (
    <span className="flex items-center gap-1 text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded-full">
      <Shield size={10} /> {score}
    </span>
  )
  if (score >= 50) return (
    <span className="flex items-center gap-1 text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-2 py-0.5 rounded-full">
      <Clock size={10} /> {score}
    </span>
  )
  return (
    <span className="flex items-center gap-1 text-xs text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-2 py-0.5 rounded-full">
      <Flame size={10} /> {score}
    </span>
  )
}

function ProgressBar({ value, color = 'bg-brand-500' }: { value: number; color?: string }) {
  return (
    <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
      <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  )
}

const STATUS_COLOR: Record<string, string> = {
  active:    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  archived:  'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}
const STATUS_LABEL: Record<string, string> = {
  active: 'Aktívny', completed: 'Dokončený', archived: 'Archivovaný',
}

export default function PortfolioPage() {
  const { data, isLoading } = useQuery<PortfolioData>({
    queryKey: ['portfolio'],
    queryFn: () => api.get('/projects/portfolio/overview').then(r => r.data),
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto py-20 text-center text-gray-400">
        <LayoutGrid size={32} className="mx-auto mb-3 opacity-30" />
        Načítavam portfolio…
      </div>
    )
  }

  if (!data || data.projects.length === 0) {
    return (
      <div className="max-w-5xl mx-auto space-y-5">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Portfolio</h1>
        <div className="card py-20 text-center text-gray-400">
          <LayoutGrid size={40} className="mx-auto mb-3 opacity-20" />
          <p>Žiadne projekty v portfóliu</p>
        </div>
      </div>
    )
  }

  const { summary, projects } = data
  const atRiskProjects = projects.filter(p => p.is_at_risk)

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <LayoutGrid size={22} className="text-brand-500" />
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">Portfolio</h1>
        <span className="text-sm text-gray-400">Prehľad všetkých projektov</span>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{summary.total}</p>
          <p className="text-xs text-gray-500 mt-1">Celkom projektov</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">{summary.active}</p>
          <p className="text-xs text-gray-500 mt-1">Aktívnych</p>
        </div>
        <div className={`card p-4 text-center ${summary.at_risk > 0 ? 'border-red-200 dark:border-red-800' : ''}`}>
          <p className={`text-3xl font-bold ${summary.at_risk > 0 ? 'text-red-500' : 'text-gray-900 dark:text-white'}`}>
            {summary.at_risk}
          </p>
          <p className="text-xs text-gray-500 mt-1">Rizikových</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-brand-600 dark:text-brand-400">
            {Math.round(summary.overall_progress * 100)}%
          </p>
          <p className="text-xs text-gray-500 mt-1">Celkový postup</p>
        </div>
      </div>

      {/* Overall progress bar */}
      <div className="card p-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">Celkový postup</span>
          <span className="text-gray-500">{summary.total_completed} / {summary.total_tasks} úloh</span>
        </div>
        <ProgressBar value={summary.overall_progress} />
      </div>

      {/* At-risk warning */}
      {atRiskProjects.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertTriangle size={15} className="text-red-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-red-700 dark:text-red-400">
              <strong>Rizikové projekty ({atRiskProjects.length})</strong> —{' '}
              {atRiskProjects.map(p => p.name).join(', ')}
              <p className="text-xs mt-0.5 text-red-500">
                Majú blokované úlohy, meškajúce termíny alebo nízke health skóre.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Project grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {projects.map(p => (
          <Link
            key={p.id}
            to={`/projects/${p.id}`}
            className={`card p-5 hover:shadow-md transition-shadow group ${
              p.is_at_risk ? 'border-red-200 dark:border-red-900' : ''
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  p.is_at_risk ? 'bg-red-50 dark:bg-red-900/20' : 'bg-brand-50 dark:bg-brand-500/10'
                }`}>
                  <FolderKanban size={18} className={p.is_at_risk ? 'text-red-500' : 'text-brand-500'} />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-sm text-gray-900 dark:text-white truncate">{p.name}</p>
                  {p.description && (
                    <p className="text-xs text-gray-400 truncate">{p.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <HealthBadge score={p.health_score} />
                <span className={`badge text-xs ${STATUS_COLOR[p.status] ?? STATUS_COLOR.active}`}>
                  {STATUS_LABEL[p.status] ?? p.status}
                </span>
              </div>
            </div>

            {/* Progress */}
            <div className="space-y-1.5 mb-3">
              <div className="flex justify-between text-xs text-gray-500">
                <span>{p.completed_tasks} / {p.total_tasks} úloh</span>
                <span>{Math.round(p.progress * 100)}%</span>
              </div>
              <ProgressBar
                value={p.progress}
                color={p.progress >= 0.75 ? 'bg-green-500' : p.progress >= 0.4 ? 'bg-brand-500' : 'bg-amber-500'}
              />
            </div>

            {/* Stats row */}
            <div className="flex items-center gap-3 text-xs text-gray-500">
              {p.in_progress_tasks > 0 && (
                <span className="flex items-center gap-1 text-blue-500">
                  <Clock size={10} /> {p.in_progress_tasks} beží
                </span>
              )}
              {p.critical_tasks > 0 && (
                <span className="flex items-center gap-1 text-red-500">
                  <TrendingUp size={10} /> {p.critical_tasks} kritických
                </span>
              )}
              {p.blocked_tasks > 0 && (
                <span className="flex items-center gap-1 text-amber-500">
                  <AlertTriangle size={10} /> {p.blocked_tasks} blokovaných
                </span>
              )}
              {p.overdue_tasks > 0 && (
                <span className="flex items-center gap-1 text-red-500 font-medium">
                  <Flame size={10} /> {p.overdue_tasks} po termíne
                </span>
              )}
              {p.blocked_tasks === 0 && p.overdue_tasks === 0 && p.total_tasks > 0 && (
                <span className="flex items-center gap-1 text-green-500">
                  <CheckCircle2 size={10} /> Na čase
                </span>
              )}
              {p.project_duration > 0 && (
                <span className="text-gray-400">{p.project_duration}d CPM</span>
              )}
              <span className="ml-auto" onClick={e => e.preventDefault()}>
                <RiskScoreWidget projectId={p.id} variant="compact" />
              </span>
            </div>

            <ChevronRight size={14} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-300 group-hover:text-gray-500 dark:group-hover:text-gray-300 transition-colors" />
          </Link>
        ))}
      </div>

      {/* Legend */}
      <div className="card p-4 space-y-3">
        <div>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Health skóre (0-100)</p>
          <div className="flex flex-wrap gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1.5"><Shield size={11} className="text-green-500" />75-100 — Výborný</span>
            <span className="flex items-center gap-1.5"><Clock size={11} className="text-amber-500" />50-74 — Priemerný</span>
            <span className="flex items-center gap-1.5"><Flame size={11} className="text-red-500" />0-49 — Rizikový</span>
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">AI Risk skóre (0-100) — PERT + meškanie + konflikty zdrojov</p>
          <div className="flex flex-wrap gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1.5 text-green-600 dark:text-green-400">● 0-24 — Nízke</span>
            <span className="flex items-center gap-1.5 text-yellow-600 dark:text-yellow-400">● 25-49 — Stredné</span>
            <span className="flex items-center gap-1.5 text-orange-600 dark:text-orange-400">● 50-74 — Vysoké</span>
            <span className="flex items-center gap-1.5 text-red-600 dark:text-red-400">● 75-100 — Kritické</span>
          </div>
        </div>
      </div>
    </div>
  )
}
