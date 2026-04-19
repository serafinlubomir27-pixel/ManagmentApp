import { useQuery } from '@tanstack/react-query'
import { Users, User, ChevronRight } from 'lucide-react'
import { teamApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

const ROLE_COLOR: Record<string, string> = {
  admin:    'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  manager:  'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  employee: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

export default function TeamPage() {
  const { isAdmin, isManager } = useAuth()
  const [showTree, setShowTree] = useState(false)

  const { data: team = [], isLoading } = useQuery({
    queryKey: ['team', showTree],
    queryFn: () =>
      showTree
        ? teamApi.tree().then((r) => r.data)
        : isAdmin
        ? teamApi.all().then((r) => r.data)
        : teamApi.myTeam().then((r) => r.data),
  })

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Tím</h1>
        {isManager && (
          <button
            onClick={() => setShowTree((v) => !v)}
            className={`btn-ghost text-sm flex items-center gap-2 ${showTree ? 'text-brand-600 dark:text-brand-400' : ''}`}
          >
            <Users size={16} />
            {showTree ? 'Zobraziť priamych' : 'Celý strom'}
          </button>
        )}
      </div>

      <div className="card divide-y divide-gray-100 dark:divide-gray-800">
        {isLoading ? (
          <div className="py-10 text-center text-gray-400 text-sm">Načítavam…</div>
        ) : team.length === 0 ? (
          <div className="py-10 text-center text-gray-400 text-sm">Žiadni členovia tímu</div>
        ) : (
          team.map((member: any) => (
            <MemberRow key={member.id} member={member} />
          ))
        )}
      </div>
    </div>
  )
}

function MemberRow({ member }: { member: any }) {
  const depth = member.depth ?? 0
  const initials = (member.full_name ?? member.username ?? '?')
    .split(' ')
    .map((n: string) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div
      className="flex items-center gap-4 px-5 py-3.5"
      style={{ paddingLeft: `${20 + depth * 20}px` }}
    >
      {depth > 0 && (
        <ChevronRight size={14} className="text-gray-300 dark:text-gray-600 flex-shrink-0 -ml-2" />
      )}
      <div className="w-9 h-9 rounded-full bg-brand-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
        {initials}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-gray-900 dark:text-white">{member.full_name}</p>
        <p className="text-xs text-gray-400">@{member.username}</p>
        {member.manager_name && (
          <p className="text-xs text-gray-400">Manažér: {member.manager_name}</p>
        )}
      </div>
      <span className={`badge ${ROLE_COLOR[member.role] ?? ROLE_COLOR.employee}`}>
        {member.role}
      </span>
    </div>
  )
}

// useState import fix
import { useState } from 'react'
