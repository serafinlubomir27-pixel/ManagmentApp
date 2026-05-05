/**
 * ClientsPage — list and create clients (financial advisor register).
 * Route: /clients
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, Plus, ChevronRight, User } from 'lucide-react'
import { clientsApi } from '../api/client'

const CATEGORY_LABEL: Record<string, string> = {
  retail: 'Retail',
  professional: 'Profesionálny',
  eligible_counterparty: 'Oprávnená protistrana',
}
const CATEGORY_COLOR: Record<string, string> = {
  retail:                'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  professional:          'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  eligible_counterparty: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
}
const RISK_COLOR: Record<string, string> = {
  conservative: 'text-green-600 dark:text-green-400',
  balanced:     'text-blue-600 dark:text-blue-400',
  dynamic:      'text-orange-600 dark:text-orange-400',
}
const RISK_LABEL: Record<string, string> = {
  conservative: 'Konzervatívny',
  balanced: 'Vyvážený',
  dynamic: 'Dynamický',
}

export default function ClientsPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', phone: '', category: 'retail', risk_profile: 'balanced', notes: '' })
  const [err, setErr] = useState('')

  const { data: clients = [], isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: () => clientsApi.list().then(r => r.data),
    staleTime: 30_000,
  })

  const createMutation = useMutation({
    mutationFn: () => clientsApi.create(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clients'] })
      setShowCreate(false)
      setForm({ name: '', email: '', phone: '', category: 'retail', risk_profile: 'balanced', notes: '' })
      setErr('')
    },
    onError: (e: any) => setErr(e.response?.data?.detail ?? 'Chyba'),
  })

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users size={22} className="text-brand-500" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Klienti</h1>
          <span className="text-sm text-gray-400">Register klientov</span>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus size={15} /> Nový klient
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card p-4 space-y-3">
          <h3 className="font-semibold text-sm text-gray-900 dark:text-white">Nový klient</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input className="input" placeholder="Meno klienta *" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
            <input className="input" placeholder="Email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
            <input className="input" placeholder="Telefón" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} />
            <select className="input" value={form.category} onChange={e => setForm({...form, category: e.target.value})}>
              <option value="retail">Retail</option>
              <option value="professional">Profesionálny</option>
              <option value="eligible_counterparty">Oprávnená protistrana</option>
            </select>
            <select className="input" value={form.risk_profile} onChange={e => setForm({...form, risk_profile: e.target.value})}>
              <option value="conservative">Konzervatívny</option>
              <option value="balanced">Vyvážený</option>
              <option value="dynamic">Dynamický</option>
            </select>
            <input className="input" placeholder="Poznámky" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          </div>
          {err && <p className="text-xs text-red-500">{err}</p>}
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending} className="btn-primary text-sm">
              {createMutation.isPending ? 'Ukladám…' : 'Vytvoriť'}
            </button>
            <button onClick={() => setShowCreate(false)} className="btn-ghost text-sm">Zrušiť</button>
          </div>
        </div>
      )}

      {/* Client list */}
      {isLoading ? (
        <p className="text-sm text-gray-400">Načítavam…</p>
      ) : clients.length === 0 ? (
        <div className="card py-16 text-center text-gray-400">
          <User size={32} className="mx-auto mb-3 opacity-20" />
          <p>Žiadni klienti. Vytvor prvého klienta.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {clients.map((c: any) => (
            <Link key={c.id} to={`/clients/${c.id}`} className="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow group">
              {/* Avatar */}
              <div className="w-10 h-10 rounded-full bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-bold text-brand-600 dark:text-brand-400">
                  {c.name.slice(0, 2).toUpperCase()}
                </span>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm text-gray-900 dark:text-white truncate">{c.name}</p>
                <div className="flex items-center gap-2 flex-wrap">
                  {c.email && <span className="text-xs text-gray-400">{c.email}</span>}
                  {c.phone && <span className="text-xs text-gray-400">{c.phone}</span>}
                </div>
              </div>

              {/* Badges */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_COLOR[c.category] ?? CATEGORY_COLOR.retail}`}>
                  {CATEGORY_LABEL[c.category] ?? c.category}
                </span>
                <span className={`text-xs font-medium ${RISK_COLOR[c.risk_profile] ?? ''}`}>
                  {RISK_LABEL[c.risk_profile] ?? c.risk_profile}
                </span>
              </div>

              <ChevronRight size={14} className="text-gray-300 group-hover:text-gray-500 dark:group-hover:text-gray-300 transition-colors flex-shrink-0" />
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
