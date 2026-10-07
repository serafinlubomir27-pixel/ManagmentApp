import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  FolderKanban, AlertTriangle, CalendarClock, CheckCircle2, ArrowRight,
  Ban, Flame, Sparkles, Plus,
} from 'lucide-react'
import { api, calendarApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { SkeletonCards, SkeletonList, Skeleton } from '../components/Skeleton'
import EmptyState from '../components/EmptyState'

const DAYS = ['Nedeľa', 'Pondelok', 'Utorok', 'Streda', 'Štvrtok', 'Piatok', 'Sobota']
const MONTHS = ['januára', 'februára', 'marca', 'apríla', 'mája', 'júna',
  'júla', 'augusta', 'septembra', 'októbra', 'novembra', 'decembra']

function formatDate(d: Date) {
  return `${DAYS[d.getDay()]}, ${d.getDate()}. ${MONTHS[d.getMonth()]} ${d.getFullYear()}`
}

/** Koľko dní do termínu. Záporné = po termíne. */
function daysUntil(iso: string): number {
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const due = new Date(iso); due.setHours(0, 0, 0, 0)
  return Math.round((due.getTime() - today.getTime()) / 86_400_000)
}

/** Slovenčina skloňuje podľa počtu: 1 deň, 2–4 dni, 5+ dní. */
function days(n: number): string {
  if (n === 1) return 'deň'
  if (n >= 2 && n <= 4) return 'dni'
  return 'dní'
}

function relativeDay(n: number): string {
  if (n < -1) return `${Math.abs(n)} ${days(Math.abs(n))} po termíne`
  if (n === -1) return 'včera'
  if (n === 0) return 'dnes'
  if (n === 1) return 'zajtra'
  return `o ${n} ${days(n)}`
}

interface PortfolioProject {
  id: number
  name: string
  status: string
  total_tasks: number
  completed_tasks: number
  blocked_tasks: number
  critical_tasks: number
  overdue_tasks: number
  progress: number
  health_score: number
  project_duration: number
  is_at_risk: boolean
}

interface CalendarTask {
  id: number
  name: string
  status: string
  due_date: string
  priority: string
  project_id: number
  project_name: string
}

export default function DashboardPage() {
  const { user, isManager } = useAuth()

  const { data: portfolio, isLoading } = useQuery<{
    projects: PortfolioProject[]
    summary: { total: number; active: number; at_risk: number; completed: number }
  }>({
    queryKey: ['portfolio'],
    queryFn: () => api.get('/projects/portfolio/overview').then(r => r.data),
  })

  const { data: calendar, isLoading: loadingCal } = useQuery<{ tasks: CalendarTask[] }>({
    queryKey: ['calendar-tasks'],
    queryFn: () => calendarApi.myTasks().then(r => r.data),
  })

  const projects = portfolio?.projects ?? []
  const active = projects.filter(p => p.status === 'active')

  const overdueTotal = projects.reduce((s, p) => s + p.overdue_tasks, 0)
  const blockedTotal = projects.reduce((s, p) => s + p.blocked_tasks, 0)
  const atRisk = projects.filter(p => p.is_at_risk)

  // Nasledujúcich 14 dní plus všetko, čo je už po termíne.
  const upcoming = (calendar?.tasks ?? [])
    .filter(t => t.status !== 'completed')
    .map(t => ({ ...t, days: daysUntil(t.due_date) }))
    .filter(t => t.days <= 14)
    .sort((a, b) => a.days - b.days)
    .slice(0, 6)

  const allClear = !isLoading && projects.length > 0
    && overdueTotal === 0 && blockedTotal === 0 && atRisk.length === 0

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* ── Pozdrav ──────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Ahoj, {user?.full_name?.split(' ')[0] ?? user?.username} 👋
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">{formatDate(new Date())}</p>
        </div>
        {isManager && projects.length > 0 && (
          <Link to="/projects" className="btn-outline text-sm">
            <Plus size={15} /> Nový projekt
          </Link>
        )}
      </div>

      {/* ── Čo potrebuje pozornosť ───────────────────────────────────────── */}
      {isLoading ? (
        <SkeletonCards count={3} />
      ) : allClear ? (
        <div className="card p-5 flex items-center gap-4">
          <div className="w-11 h-11 rounded-control bg-green-50 dark:bg-green-500/10 flex items-center justify-center shrink-0">
            <CheckCircle2 className="text-green-500" size={22} />
          </div>
          <div>
            <p className="font-medium text-gray-900 dark:text-white">Všetko beží podľa plánu</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Žiadne úlohy po termíne, nič blokované, žiadny projekt v riziku.
            </p>
          </div>
        </div>
      ) : projects.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 stagger">
          <SignalCard
            icon={<AlertTriangle size={22} />}
            value={overdueTotal}
            label="úloh po termíne"
            tone={overdueTotal > 0 ? 'danger' : 'calm'}
            to="/calendar"
          />
          <SignalCard
            icon={<Ban size={22} />}
            value={blockedTotal}
            label="blokovaných úloh"
            tone={blockedTotal > 0 ? 'warn' : 'calm'}
            to="/projects"
          />
          <SignalCard
            icon={<Flame size={22} />}
            value={atRisk.length}
            label="projektov v riziku"
            tone={atRisk.length > 0 ? 'danger' : 'calm'}
            to="/portfolio"
          />
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-5 items-start">
        {/* ── Projekty s postupom ────────────────────────────────────────── */}
        <section className="lg:col-span-2 card">
          <header className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-white/[0.06]">
            <h2 className="font-semibold text-gray-900 dark:text-white">Moje projekty</h2>
            {projects.length > 0 && (
              <Link to="/portfolio" className="text-xs text-brand-500 hover:text-brand-600 font-medium">
                Portfólio <ArrowRight size={12} className="inline -mt-0.5" />
              </Link>
            )}
          </header>

          {isLoading ? (
            <SkeletonList rows={3} />
          ) : projects.length === 0 ? (
            <EmptyState
              icon={<FolderKanban size={20} />}
              title="Zatiaľ žiadne projekty"
              hint="Projekt je priečinok na úlohy a závislosti. Z nich sa počíta kritická cesta."
              action={
                <Link to="/projects" className="btn-primary text-xs py-1.5 px-3">
                  <Sparkles size={13} /> Vytvoriť prvý projekt
                </Link>
              }
            />
          ) : (
            <ul className="divide-y divide-gray-100 dark:divide-white/[0.06] stagger">
              {(active.length > 0 ? active : projects).slice(0, 6).map(p => (
                <li key={p.id}>
                  <Link
                    to={`/projects/${p.id}`}
                    className="block px-5 py-4 transition duration-fast ease-out
                               hover:bg-gray-50 dark:hover:bg-white/[0.03] group"
                  >
                    <div className="flex items-center gap-3">
                      <p className="font-medium text-sm text-gray-900 dark:text-white truncate
                                    group-hover:text-brand-600 dark:group-hover:text-brand-400
                                    transition-colors duration-fast">
                        {p.name}
                      </p>
                      {p.is_at_risk && (
                        <span className="badge bg-red-50 text-red-600 dark:bg-red-500/15 dark:text-red-400 shrink-0">
                          v riziku
                        </span>
                      )}
                      <span className="ml-auto text-xs tabular-nums text-gray-400 shrink-0">
                        {p.completed_tasks}/{p.total_tasks}
                      </span>
                    </div>

                    <div className="mt-2.5 h-1.5 rounded-full bg-gray-100 dark:bg-white/[0.08] overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-[width] duration-slow ease-out ${
                          p.is_at_risk ? 'bg-red-400' : 'bg-brand-500'
                        }`}
                        style={{ width: `${Math.round(p.progress * 100)}%` }}
                      />
                    </div>

                    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-400">
                      <span>{Math.round(p.progress * 100)} % hotovo</span>
                      {p.critical_tasks > 0 && (
                        <span className="text-red-500/80">{p.critical_tasks} kritických</span>
                      )}
                      {p.overdue_tasks > 0 && (
                        <span className="text-red-500">{p.overdue_tasks} po termíne</span>
                      )}
                      {p.blocked_tasks > 0 && (
                        <span className="text-amber-500">{p.blocked_tasks} blokovaných</span>
                      )}
                      {p.project_duration > 0 && <span>{p.project_duration} {p.project_duration === 1 ? "deň" : p.project_duration <= 4 ? "dni" : "dní"} podľa CPM</span>}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* ── Blížiace sa termíny ────────────────────────────────────────── */}
        <section className="card">
          <header className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-white/[0.06]">
            <h2 className="font-semibold text-gray-900 dark:text-white">Blížiace sa termíny</h2>
            <Link to="/calendar" className="text-xs text-brand-500 hover:text-brand-600 font-medium">
              Kalendár <ArrowRight size={12} className="inline -mt-0.5" />
            </Link>
          </header>

          {loadingCal ? (
            <div className="p-5 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-2.5 w-1/2" />
                </div>
              ))}
            </div>
          ) : upcoming.length === 0 ? (
            <EmptyState
              icon={<CalendarClock size={20} />}
              title="Nič na najbližšie dva týždne"
              hint="Termíny úloh sa objavia tu, len čo ich nastavíš."
              size="inline"
            />
          ) : (
            <ul className="divide-y divide-gray-100 dark:divide-white/[0.06]">
              {upcoming.map(t => (
                <li key={t.id}>
                  <Link
                    to={`/projects/${t.project_id}`}
                    className="flex items-start gap-3 px-5 py-3 transition duration-fast ease-out
                               hover:bg-gray-50 dark:hover:bg-white/[0.03]"
                  >
                    <span
                      className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                        t.days < 0 ? 'bg-red-500' : t.days <= 2 ? 'bg-amber-500' : 'bg-gray-300 dark:bg-gray-600'
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-gray-900 dark:text-white truncate">{t.name}</p>
                      <p className="text-xs text-gray-400 truncate">{t.project_name}</p>
                    </div>
                    <span
                      className={`text-xs shrink-0 ${
                        t.days < 0 ? 'text-red-500 font-medium'
                          : t.days <= 2 ? 'text-amber-500'
                          : 'text-gray-400'
                      }`}
                    >
                      {relativeDay(t.days)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}

function SignalCard({ icon, value, label, tone, to }: {
  icon: React.ReactNode
  value: number
  label: string
  tone: 'danger' | 'warn' | 'calm'
  to: string
}) {
  const tones = {
    danger: 'bg-red-50 dark:bg-red-500/10 text-red-500',
    warn:   'bg-amber-50 dark:bg-amber-500/10 text-amber-500',
    calm:   'bg-gray-100 dark:bg-white/[0.06] text-gray-400',
  }
  return (
    <Link to={to} className="card-interactive p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-control flex items-center justify-center shrink-0 ${tones[tone]}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className={`text-2xl font-bold tabular-nums ${
          tone === 'calm' ? 'text-gray-400' : 'text-gray-900 dark:text-white'
        }`}>
          {value}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{label}</p>
      </div>
    </Link>
  )
}
