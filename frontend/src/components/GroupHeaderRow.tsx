/**
 * GroupHeaderRow — hlavička etapy v tabuľke úloh.
 *
 * Nesie to, čo chce manažér vidieť na jeden pohľad: ako ďaleko je etapa,
 * koľko má úloh a či v nej niečo horí. Zbalenie je najdôležitejšie tlačidlo
 * na riadku, preto je úplne vľavo a klik funguje na celej hlavičke.
 */
import { useState } from 'react'
import { ChevronDown, ChevronRight, Check, Pencil, Trash2, X } from 'lucide-react'
import { TaskGroup, groupAccent, groupTint, taskCount } from './groups'

interface Props {
  group: TaskGroup
  collapsed: boolean
  canEdit: boolean
  onToggle: () => void
  onRename: (name: string) => void
  onDelete: () => void
}

export default function GroupHeaderRow({
  group, collapsed, canEdit, onToggle, onRename, onDelete,
}: Props) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(group.name)

  const pct = Math.round(group.progress * 100)

  const commit = () => {
    const name = draft.trim()
    if (name && name !== group.name) onRename(name)
    else setDraft(group.name)
    setEditing(false)
  }

  return (
    <tr className={`${groupTint[group.color]} border-y border-gray-200 dark:border-white/[0.08]`}>
      <td colSpan={5} className="p-0">
        <div className="flex items-center gap-3 pl-0 pr-4 py-2.5">
          {/* farebný prúžok — etapa sa dá rozoznať aj periférne */}
          <span className={`w-1 self-stretch rounded-r ${groupAccent[group.color]}`} />

          <button
            onClick={onToggle}
            className="flex items-center gap-2 min-w-0 text-left group/btn"
            aria-expanded={!collapsed}
          >
            <span className="text-gray-400 group-hover/btn:text-gray-600 dark:group-hover/btn:text-gray-200
                             transition-colors duration-fast">
              {collapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
            </span>

            {editing ? null : (
              <span className="font-semibold text-sm text-gray-900 dark:text-white truncate">
                {group.name}
              </span>
            )}

            {group.done && (
              <span className="badge bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400 shrink-0">
                <Check size={11} className="mr-0.5" /> Hotová
              </span>
            )}
          </button>

          {editing && (
            <span className="flex items-center gap-1">
              <input
                autoFocus
                className="input py-1 text-sm w-48"
                value={draft}
                onChange={e => setDraft(e.target.value)}
                onBlur={commit}
                onKeyDown={e => {
                  if (e.key === 'Enter') commit()
                  if (e.key === 'Escape') { setDraft(group.name); setEditing(false) }
                }}
              />
              <button onClick={() => { setDraft(group.name); setEditing(false) }}
                      className="p-1 text-gray-400 hover:text-gray-600" aria-label="Zrušiť">
                <X size={14} />
              </button>
            </span>
          )}

          <span className="text-xs text-gray-500 dark:text-gray-400 shrink-0">
            {taskCount(group.total_tasks)}
          </span>

          {group.critical_tasks > 0 && (
            <span className="text-xs text-red-500 shrink-0 hidden sm:inline">
              {group.critical_tasks} kritických
            </span>
          )}

          {/* postup — vždy na rovnakom mieste, nech sa dajú etapy porovnať očami */}
          <div className="ml-auto flex items-center gap-2 shrink-0">
            <div className="w-24 sm:w-32 h-1.5 rounded-full bg-white/70 dark:bg-black/25 overflow-hidden">
              <div
                className={`h-full rounded-full transition-[width] duration-slow ease-out ${groupAccent[group.color]}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-xs tabular-nums text-gray-500 dark:text-gray-400 w-10 text-right">
              {pct} %
            </span>

            {canEdit && !editing && (
              <span className="flex items-center gap-0.5 ml-1">
                <button
                  onClick={() => { setDraft(group.name); setEditing(true) }}
                  className="p-1.5 rounded-control text-gray-400 hover:text-gray-700 dark:hover:text-gray-200
                             hover:bg-white/60 dark:hover:bg-white/10 transition duration-fast"
                  title="Premenovať etapu"
                >
                  <Pencil size={13} />
                </button>
                <button
                  onClick={onDelete}
                  className="p-1.5 rounded-control text-gray-400 hover:text-red-500
                             hover:bg-white/60 dark:hover:bg-white/10 transition duration-fast"
                  title="Zrušiť etapu (úlohy ostanú)"
                >
                  <Trash2 size={13} />
                </button>
              </span>
            )}
          </div>
        </div>
      </td>
    </tr>
  )
}
