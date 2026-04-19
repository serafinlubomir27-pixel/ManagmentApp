import { useQuery } from '@tanstack/react-query'
import { FolderKanban, CheckSquare, AlertCircle, Clock } from 'lucide-react'
import { projectsApi, tasksApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { format, isAfter, isBefore, addDays } from 'date-fns'

export default function DashboardPage() {
  const { user } = useAuth()
  const today = new Date()

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list().then((r) => r.data),
  })

  // Počítame štatistiky
  const activeProjects = projects.filter((p: any) => p.status === 'active').length

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Pozdrav */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Ahoj, {user?.full_name?.split(' ')[0]} 👋
        </h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
          {format(today, 'EEEE, d. MMMM yyyy')}
        </p>
      </div>

      {/* Stat karty */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={<FolderKanban className="text-brand-500" size={22} />}
          label="Aktívne projekty"
          value={activeProjects}
          color="bg-brand-50 dark:bg-brand-500/10"
        />
        <StatCard
          icon={<CheckSquare className="text-green-500" size={22} />}
          label="Projekty celkom"
          value={projects.length}
          color="bg-green-50 dark:bg-green-500/10"
        />
        <StatCard
          icon={<Clock className="text-orange-500" size={22} />}
          label="Ukončené projekty"
          value={projects.filter((p: any) => p.status === 'completed').length}
          color="bg-orange-50 dark:bg-orange-500/10"
        />
      </div>

      {/* Posledné projekty */}
      <div className="card p-5">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Moje projekty</h2>
        {projects.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">Zatiaľ žiadne projekty</p>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {projects.slice(0, 8).map((p: any) => (
              <ProjectRow key={p.id} project={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }: {
  icon: React.ReactNode; label: string; value: number; color: string
}) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      </div>
    </div>
  )
}

function ProjectRow({ project }: { project: any }) {
  const statusColor: Record<string, string> = {
    active:    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    archived:  'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  }
  const statusLabel: Record<string, string> = {
    active: 'Aktívny', completed: 'Dokončený', archived: 'Archivovaný',
  }

  return (
    <div className="flex items-center gap-3 py-3">
      <div className="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center">
        <FolderKanban size={16} className="text-brand-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{project.name}</p>
        {project.description && (
          <p className="text-xs text-gray-400 truncate">{project.description}</p>
        )}
      </div>
      <span className={`badge ${statusColor[project.status] ?? statusColor.active}`}>
        {statusLabel[project.status] ?? project.status}
      </span>
    </div>
  )
}
