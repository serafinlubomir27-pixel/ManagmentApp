/**
 * ClientDetailPage — full client detail with tabbed sections.
 * Route: /clients/:id
 * Tabs: Projekty | Pipeline | Stretnutia | Compliance
 */
import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FolderKanban, TrendingUp, Calendar, Shield } from 'lucide-react'
import { clientsApi, projectsApi } from '../api/client'
import PipelineKanban from '../components/PipelineKanban'
import ComplianceChecklist from '../components/ComplianceChecklist'
import MeetingLog from '../components/MeetingLog'

const CATEGORY_LABEL: Record<string, string> = {
  retail: 'Retail', professional: 'Profesionálny', eligible_counterparty: 'Oprávnená protistrana',
}
const RISK_LABEL: Record<string, string> = {
  conservative: 'Konzervatívny', balanced: 'Vyvážený', dynamic: 'Dynamický',
}
const RISK_COLOR: Record<string, string> = {
  conservative: 'text-green-600 dark:text-green-400',
  balanced:     'text-blue-600 dark:text-blue-400',
  dynamic:      'text-orange-600 dark:text-orange-400',
}

type Tab = 'projects' | 'pipeline' | 'meetings' | 'compliance'

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const clientId = Number(id)
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('projects')
  const [linkProjectId, setLinkProjectId] = useState('')

  const { data: client, isLoading } = useQuery({
    queryKey: ['client', clientId],
    queryFn: () => clientsApi.get(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const { data: allProjects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list().then(r => r.data),
    staleTime: 60_000,
  })

  const linkMutation = useMutation({
    mutationFn: (projectId: number) => clientsApi.linkProject(clientId, projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client', clientId] })
      setLinkProjectId('')
    },
  })

  if (isLoading || !client) return (
    <div className="max-w-4xl mx-auto py-20 text-center text-gray-400">Načítavam…</div>
  )

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'projects',   label: 'Projekty',    icon: <FolderKanban size={15} /> },
    { key: 'pipeline',   label: 'Pipeline',    icon: <TrendingUp size={15} /> },
    { key: 'meetings',   label: 'Stretnutia',  icon: <Calendar size={15} /> },
    { key: 'compliance', label: 'Compliance',  icon: <Shield size={15} /> },
  ]

  const linkedProjectIds = new Set((client.projects ?? []).map((p: any) => p.id))
  const unlinkedProjects = (allProjects as any[]).filter((p: any) => !linkedProjectIds.has(p.id))

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Link to="/clients" className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 mt-0.5">
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="w-10 h-10 rounded-full bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center">
              <span className="text-sm font-bold text-brand-600 dark:text-brand-400">
                {client.name.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">{client.name}</h1>
              <div className="flex items-center gap-2 text-xs text-gray-400 flex-wrap">
                <span>{CATEGORY_LABEL[client.category] ?? client.category}</span>
                <span>·</span>
                <span className={RISK_COLOR[client.risk_profile]}>
                  {RISK_LABEL[client.risk_profile] ?? client.risk_profile}
                </span>
                {client.email && <><span>·</span><span>{client.email}</span></>}
                {client.phone && <><span>·</span><span>{client.phone}</span></>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit flex-wrap">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-white dark:bg-surface-dark text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="card p-5">
        {/* Projects */}
        {tab === 'projects' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                Priradené projekty ({(client.projects ?? []).length})
              </h3>
              {unlinkedProjects.length > 0 && (
                <div className="flex gap-2">
                  <select
                    className="input text-sm"
                    value={linkProjectId}
                    onChange={e => setLinkProjectId(e.target.value)}
                  >
                    <option value="">— Vyber projekt —</option>
                    {unlinkedProjects.map((p: any) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => linkProjectId && linkMutation.mutate(Number(linkProjectId))}
                    disabled={!linkProjectId || linkMutation.isPending}
                    className="btn-primary text-sm"
                  >
                    Priradiť
                  </button>
                </div>
              )}
            </div>
            <div className="space-y-2">
              {(client.projects ?? []).length === 0 ? (
                <p className="text-sm text-gray-400">Žiadne priradené projekty.</p>
              ) : (
                (client.projects as any[]).map((p: any) => (
                  <Link key={p.id} to={`/projects/${p.id}`} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                    <FolderKanban size={16} className="text-brand-500" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white flex-1">{p.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${p.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {p.status}
                    </span>
                  </Link>
                ))
              )}
            </div>
          </div>
        )}

        {tab === 'pipeline' && (
          <PipelineKanban clientId={clientId} deal={client.deal} />
        )}

        {tab === 'meetings' && <MeetingLog clientId={clientId} />}

        {tab === 'compliance' && <ComplianceChecklist clientId={clientId} />}
      </div>
    </div>
  )
}
