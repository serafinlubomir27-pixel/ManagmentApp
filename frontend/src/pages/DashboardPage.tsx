import { useQuery } from '@tanstack/react-query'
import { FolderKanban, CheckSquare, Clock, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { projectsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

const DAYS = ['Nedeľa', 'Pondelok', 'Utorok', 'Streda', 'Štvrtok', 'Piatok', 'Sobota']
const MONTHS = ['januára', 'februára', 'marca', 'apríla', 'mája', 'júna',
  'júla', 'augusta', 'septembra', 'októbra', 'novembra', 'decembra']

function formatDate(d: Date) {
  return `${DAYS[d.getDay()]}, ${d.getDate()}. ${MONTHS[d.getMonth()]} ${d.getFullYear()}`
}

const STATUS_COLOR: Record<string, string> = {
  active:    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  archived:  'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}
const STATUS_LABEL: Record<string, string> = {
  active: 'Aktívny', completed: 'Dokončený', archived: 'Archivovaný',
}

export default function DashboardPage() {
  const { user } = useAuth()
  const today = new Date()

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list().then((r) => r.data),
  })

  const active    = projects.filter((p: any) => p.status === 'active').length
  const completed = projects.filter((p: any) => p.status === 'completed').length
  const total     = projects.length

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Pozdrav */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Ahoj, {user?.full_name?.split(' ')[0]} 👋
        </h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
          {formatDate(today)}
        </p>
      </div>

      {/* Stat karty */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={<FolderKanban size={22} />}
          label="Aktívne projekty"
          value={active}
          iconBg="bg-brand-50 dark:bg-brand-500/10"
          iconColor="text-brand-500"
        />
        <StatCard
          icon={<CheckSquare size={22} />}
          label="Dokončené projekty"
          value={completed}
          iconBg="bg-green-50 dark:bg-green-500/10"
          iconColor="text-green-500"
        />
        <StatCard
          icon={<Clock size={22} />}
          label="Projekty celkom"
          value={total}
          iconBg="bg-orange-50 dark:bg-orange-500/10"
          iconColor="text-orange-500"
        />
      </div>

      {/* Posledné projekty */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900 dark:text-white">Moje projekty</h2>
          <Link to="/projects" className="text-xs text-brand-500 hover:text-brand-600 dark:hover:text-brand-400 font-medium">
            Zobraziť všetky →
          </Link>
        </div>

        {projects.length === 0 ? (
          <div className="py-8 text-center">
            <FolderKanban size={32} className="mx-auto text-gray-300 dark:text-gray-700 mb-2" />
            <p className="text-sm text-gray-400">Zatiaľ žiadne projekty</p>
            <Link to="/projects" className="text-xs text-brand-500 mt-1 inline-block">Vytvoriť prvý projekt →</Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {projects.slice(0, 6).map((p: any) => (
              <Link
                key={p.id}
                to={`/projects/${p.id}`}
                className="flex items-center gap-3 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 -mx-2 px-2 rounded-lg transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                  <FolderKanban size={15} className="text-brand-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{p.name}</p>
                  {p.description && (
                    <p className="text-xs text-gray-400 truncate">{p.description}</p>
                  )}
                </div>
                <span className={`badge flex-shrink-0 ${STATUS_COLOR[p.status] ?? STATUS_COLOR.active}`}>
                  {STATUS_LABEL[p.status] ?? p.status}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* CPM info karta */}
      {active > 0 && (
        <div className="card p-5 border-l-4 border-l-brand-500">
          <div className="flex items-start gap-3">
            <AlertCircle size={18} className="text-brand-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">CPM Analýza aktívna</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Kritická cesta sa automaticky prepočítava po každej zmene úloh. Otvor projekt a pozri záložku CPM.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, label, value, iconBg, iconColor }: {
  icon: React.ReactNode
  label: string
  value: number
  iconBg: string
  iconColor: string
}) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg}`}>
        <span className={iconColor}>{icon}</span>
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      </div>
    </div>
  )
}
