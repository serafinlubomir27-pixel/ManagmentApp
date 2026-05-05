import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, UserPlus, ChevronRight, Pencil, X, Check, Link2, Copy, Trash2 } from 'lucide-react'
import { teamApi, authApi, invitesApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

const ROLE_COLOR: Record<string, string> = {
  admin:    'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  manager:  'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  employee: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}
const ROLE_LABEL: Record<string, string> = {
  admin: 'Admin', manager: 'Manažér', employee: 'Zamestnanec',
}

export default function TeamPage() {
  const { isAdmin, isManager } = useAuth()
  const qc = useQueryClient()
  const [showTree, setShowTree] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({
    username: '', password: '', full_name: '', role: 'employee', manager_id: '',
  })
  const [createErr, setCreateErr] = useState('')
  const [editId, setEditId] = useState<number | null>(null)
  const [editRole, setEditRole] = useState('')
  const [editManagerId, setEditManagerId] = useState('')

  const { data: team = [], isLoading } = useQuery({
    queryKey: ['team', showTree],
    queryFn: () =>
      showTree
        ? teamApi.tree().then((r) => r.data)
        : isAdmin
        ? teamApi.all().then((r) => r.data)
        : teamApi.myTeam().then((r) => r.data),
  })

  // Pre výber manažéra pri vytváraní/úprave
  const { data: allUsers = [] } = useQuery({
    queryKey: ['team-all-users'],
    queryFn: () => teamApi.all().then((r) => r.data),
    enabled: isAdmin,
  })

  const createMutation = useMutation({
    mutationFn: () => authApi.register({
      username: createForm.username,
      password: createForm.password,
      full_name: createForm.full_name,
      role: createForm.role,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['team'] })
      qc.invalidateQueries({ queryKey: ['team-all-users'] })
      setShowCreate(false)
      setCreateForm({ username: '', password: '', full_name: '', role: 'employee', manager_id: '' })
      setCreateErr('')
    },
    onError: (e: any) => setCreateErr(e.response?.data?.detail ?? 'Chyba pri vytváraní'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: object }) =>
      teamApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['team'] })
      setEditId(null)
    },
  })

  const handleEdit = (member: any) => {
    setEditId(member.id)
    setEditRole(member.role)
    setEditManagerId(member.manager_id?.toString() ?? '')
  }

  const handleSaveEdit = (id: number) => {
    updateMutation.mutate({
      id,
      data: {
        role: editRole,
        manager_id: editManagerId ? Number(editManagerId) : null,
      },
    })
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Hlavička */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Tím</h1>
        <div className="flex items-center gap-2">
          {isManager && (
            <button
              onClick={() => setShowTree((v) => !v)}
              className={`btn-ghost text-sm flex items-center gap-2 ${showTree ? 'text-brand-600 dark:text-brand-400' : ''}`}
            >
              <Users size={16} />
              {showTree ? 'Zobraziť priamych' : 'Celý strom'}
            </button>
          )}
          {isAdmin && (
            <button
              onClick={() => setShowCreate(true)}
              className="btn-primary text-sm flex items-center gap-2"
            >
              <UserPlus size={16} /> Nový člen
            </button>
          )}
        </div>
      </div>

      {/* Formulár — nový člen */}
      {showCreate && (
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between mb-1">
            <h3 className="font-semibold text-gray-900 dark:text-white">Nový člen tímu</h3>
            <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
              <X size={18} />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              className="input"
              placeholder="Celé meno *"
              value={createForm.full_name}
              onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
            />
            <input
              className="input"
              placeholder="Používateľské meno *"
              value={createForm.username}
              onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
            />
            <input
              type="password"
              className="input"
              placeholder="Heslo *"
              value={createForm.password}
              onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
            />
            <select
              className="input"
              value={createForm.role}
              onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
            >
              <option value="employee">Zamestnanec</option>
              <option value="manager">Manažér</option>
              <option value="admin">Admin</option>
            </select>
            <select
              className="input sm:col-span-2"
              value={createForm.manager_id}
              onChange={(e) => setCreateForm({ ...createForm, manager_id: e.target.value })}
            >
              <option value="">— Bez manažéra —</option>
              {allUsers.map((u: any) => (
                <option key={u.id} value={u.id}>{u.full_name} (@{u.username})</option>
              ))}
            </select>
          </div>
          {createErr && <p className="text-sm text-red-500">{createErr}</p>}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost text-sm" onClick={() => setShowCreate(false)}>Zrušiť</button>
            <button
              className="btn-primary text-sm"
              onClick={() => createMutation.mutate()}
              disabled={!createForm.username || !createForm.password || !createForm.full_name || createMutation.isPending}
            >
              {createMutation.isPending ? 'Vytváram…' : 'Vytvoriť'}
            </button>
          </div>
        </div>
      )}

      {/* Zoznam členov */}
      <div className="card divide-y divide-gray-100 dark:divide-gray-800">
        {isLoading ? (
          <div className="py-10 text-center text-gray-400 text-sm">Načítavam…</div>
        ) : team.length === 0 ? (
          <div className="py-10 text-center text-gray-400 text-sm">Žiadni členovia tímu</div>
        ) : (
          team.map((member: any) => (
            editId === member.id ? (
              /* Edit riadok */
              <div key={member.id} className="flex items-center gap-3 px-5 py-3.5 bg-brand-50 dark:bg-brand-500/5">
                <div className="w-9 h-9 rounded-full bg-brand-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                  {getInitials(member.full_name)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-gray-900 dark:text-white">{member.full_name}</p>
                  <p className="text-xs text-gray-400">@{member.username}</p>
                </div>
                <select
                  className="input w-36 text-xs py-1"
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value)}
                >
                  <option value="employee">Zamestnanec</option>
                  <option value="manager">Manažér</option>
                  <option value="admin">Admin</option>
                </select>
                <select
                  className="input w-44 text-xs py-1"
                  value={editManagerId}
                  onChange={(e) => setEditManagerId(e.target.value)}
                >
                  <option value="">— Bez manažéra —</option>
                  {allUsers.filter((u: any) => u.id !== member.id).map((u: any) => (
                    <option key={u.id} value={u.id}>{u.full_name}</option>
                  ))}
                </select>
                <button
                  onClick={() => handleSaveEdit(member.id)}
                  className="p-1.5 rounded-lg bg-green-500 hover:bg-green-600 text-white"
                  disabled={updateMutation.isPending}
                >
                  <Check size={14} />
                </button>
                <button
                  onClick={() => setEditId(null)}
                  className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              /* Normálny riadok */
              <MemberRow
                key={member.id}
                member={member}
                isAdmin={isAdmin}
                onEdit={() => handleEdit(member)}
              />
            )
          ))
        )}
      </div>

      {/* ── Invite links (manager/admin only) ─────────────────────────── */}
      {isManager && <InviteSection />}
    </div>
  )
}

// ── Invite Section ─────────────────────────────────────────────────────────
function InviteSection() {
  const qc = useQueryClient()
  const [role, setRole] = useState<'employee' | 'manager'>('employee')
  const [copied, setCopied] = useState<string | null>(null)

  const { data: invites = [] } = useQuery({
    queryKey: ['invites'],
    queryFn: () => invitesApi.list().then(r => r.data),
    staleTime: 30_000,
  })

  const createMutation = useMutation({
    mutationFn: () => invitesApi.create(role),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invites'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => invitesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invites'] }),
  })

  const baseUrl = window.location.origin

  async function copyLink(token: string) {
    await navigator.clipboard.writeText(`${baseUrl}/invite/${token}`)
    setCopied(token)
    setTimeout(() => setCopied(null), 2500)
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
        <Link2 size={15} className="text-brand-500" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Pozvánkové linky</h3>
        <span className="text-xs text-gray-400 ml-auto">Platné 7 dní</span>
      </div>

      <div className="px-5 py-4 space-y-4">
        {/* Create invite */}
        <div className="flex items-center gap-3">
          <select
            className="input text-sm flex-1 max-w-48"
            value={role}
            onChange={e => setRole(e.target.value as any)}
          >
            <option value="employee">Zamestnanec</option>
            <option value="manager">Manažér</option>
          </select>
          <button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            className="btn-primary text-sm flex items-center gap-2"
          >
            <UserPlus size={14} />
            {createMutation.isPending ? 'Generujem…' : 'Generovať link'}
          </button>
        </div>

        {/* Invite list */}
        {invites.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">Žiadne aktívne pozvánky</p>
        ) : (
          <div className="space-y-2">
            {invites.map((inv: any) => {
              const isUsed = !!inv.used_by
              const isExpired = new Date(inv.expires_at) < new Date()
              const url = `${baseUrl}/invite/${inv.token}`
              return (
                <div
                  key={inv.id}
                  className={`flex items-center gap-3 p-3 rounded-xl border text-sm
                    ${isUsed || isExpired
                      ? 'border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/30 opacity-60'
                      : 'border-gray-200 dark:border-gray-700'
                    }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`badge text-xs ${
                        inv.role === 'manager'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                      }`}>
                        {inv.role === 'manager' ? 'Manažér' : 'Zamestnanec'}
                      </span>
                      {isUsed && (
                        <span className="text-xs text-green-600 dark:text-green-400">
                          ✓ Použitá (@{inv.used_by_username})
                        </span>
                      )}
                      {!isUsed && isExpired && (
                        <span className="text-xs text-red-500">Vypršala</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 font-mono mt-0.5 truncate">{url}</p>
                  </div>
                  {!isUsed && !isExpired && (
                    <button
                      onClick={() => copyLink(inv.token)}
                      className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 hover:bg-brand-100 transition-colors flex-shrink-0"
                    >
                      <Copy size={11} />
                      {copied === inv.token ? 'Skopírované!' : 'Kopírovať'}
                    </button>
                  )}
                  <button
                    onClick={() => deleteMutation.mutate(inv.id)}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex-shrink-0"
                    title="Zmazať pozvánku"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function getInitials(name: string) {
  return (name ?? '?').split(' ').map((n: string) => n[0]).slice(0, 2).join('').toUpperCase()
}

function MemberRow({ member, isAdmin, onEdit }: {
  member: any; isAdmin: boolean; onEdit: () => void
}) {
  const depth = member.depth ?? 0
  return (
    <div
      className="flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50 dark:hover:bg-gray-800/40 group transition-colors"
      style={{ paddingLeft: `${20 + depth * 20}px` }}
    >
      {depth > 0 && (
        <ChevronRight size={14} className="text-gray-300 dark:text-gray-600 flex-shrink-0 -ml-2" />
      )}
      <div className="w-9 h-9 rounded-full bg-brand-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
        {getInitials(member.full_name)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-gray-900 dark:text-white">{member.full_name}</p>
        <p className="text-xs text-gray-400">@{member.username}</p>
        {member.manager_name && (
          <p className="text-xs text-gray-400">Manažér: {member.manager_name}</p>
        )}
      </div>
      <span className={`badge ${ROLE_COLOR[member.role] ?? ROLE_COLOR.employee}`}>
        {ROLE_LABEL[member.role] ?? member.role}
      </span>
      {isAdmin && (
        <button
          onClick={onEdit}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Pencil size={14} />
        </button>
      )}
    </div>
  )
}
