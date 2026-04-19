import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, FolderKanban, ChevronRight, Search } from 'lucide-react'
import { projectsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

export default function ProjectsPage() {
  const { isManager } = useAuth()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', status: 'active' })
  const [err, setErr] = useState('')

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: () => projectsApi.create(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      setShowCreate(false)
      setForm({ name: '', description: '', status: 'active' })
    },
    onError: (e: any) => setErr(e.response?.data?.detail ?? 'Chyba'),
  })

  const filtered = projects.filter((p: any) =>
    p.name.toLowerCase().includes(search.toLowerCase()),
  )

  const statusColor: Record<string, string> = {
    active:    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    archived:  'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  }
  const statusLabel: Record<string, string> = {
    active: 'Aktívny', completed: 'Dokončený', archived: 'Archivovaný',
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Hlavička */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Projekty</h1>
        {isManager && (
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Nový projekt
          </button>
        )}
      </div>

      {/* Vyhľadávanie */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          className="input pl-9"
          placeholder="Hľadaj projekt…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Formulár na vytvorenie */}
      {showCreate && (
        <div className="card p-5 space-y-3">
          <h3 className="font-semibold text-gray-900 dark:text-white">Nový projekt</h3>
          <input
            className="input"
            placeholder="Názov projektu *"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <input
            className="input"
            placeholder="Popis (voliteľné)"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          {err && <p className="text-sm text-red-500">{err}</p>}
          <div className="flex gap-2 justify-end">
            <button className="btn-ghost" onClick={() => setShowCreate(false)}>Zrušiť</button>
            <button
              className="btn-primary"
              onClick={() => createMutation.mutate()}
              disabled={!form.name || createMutation.isPending}
            >
              {createMutation.isPending ? 'Vytváram…' : 'Vytvoriť'}
            </button>
          </div>
        </div>
      )}

      {/* Zoznam */}
      <div className="card divide-y divide-gray-100 dark:divide-gray-800">
        {isLoading ? (
          <div className="py-12 text-center text-gray-400 text-sm">Načítavam…</div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">
            {search ? 'Žiadne výsledky' : 'Žiadne projekty'}
          </div>
        ) : (
          filtered.map((p: any) => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group"
            >
              <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                <FolderKanban size={20} className="text-brand-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 dark:text-white text-sm">{p.name}</p>
                {p.description && (
                  <p className="text-xs text-gray-400 truncate mt-0.5">{p.description}</p>
                )}
              </div>
              <span className={`badge ${statusColor[p.status] ?? statusColor.active}`}>
                {statusLabel[p.status] ?? p.status}
              </span>
              <ChevronRight size={16} className="text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 flex-shrink-0" />
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
