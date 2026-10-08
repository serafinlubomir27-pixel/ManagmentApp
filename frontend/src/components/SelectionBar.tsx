/**
 * SelectionBar — lišta, ktorá vyjde zdola, keď je niečo vybrané.
 *
 * Zámerne nie je dialóg. Výber úloh a ich zoskupenie je jedna plynulá akcia:
 * označíš, pomenuješ, hotovo. Dialóg by prekryl práve to, čo si vybral.
 */
import { useEffect, useRef, useState } from 'react'
import { Layers, X, FolderOpen } from 'lucide-react'
import { TaskGroup, selectedCount } from './groups'

interface Props {
  count: number
  /** Existujúce etapy — vybrané úlohy sa dajú pridať aj do niektorej z nich. */
  groups: TaskGroup[]
  anyGrouped: boolean
  busy?: boolean
  onGroup: (name: string) => void
  onAddToGroup: (groupId: number) => void
  onUngroup: () => void
  onClear: () => void
}

export default function SelectionBar({
  count, groups, anyGrouped, busy, onGroup, onAddToGroup, onUngroup, onClear,
}: Props) {
  const [naming, setNaming] = useState(false)
  const [name, setName] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (naming) inputRef.current?.focus()
  }, [naming])

  // Escape ruší výber — očakávaná skratka, keď sa niečo označí omylom.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      if (naming) { setNaming(false); setName('') }
      else onClear()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [naming, onClear])

  const submit = () => {
    const n = name.trim()
    if (!n) return
    onGroup(n)
    setName('')
    setNaming(false)
  }

  return (
    <div
      role="status"
      className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40 animate-fade-up
                 flex items-center gap-2 px-3 py-2.5 rounded-modal
                 bg-white dark:bg-surface-raised-dark
                 border border-gray-200 dark:border-white/[0.12] shadow-overlay"
    >
      <span className="text-sm font-medium text-gray-900 dark:text-white px-1 whitespace-nowrap">
        {selectedCount(count).count}{' '}
        <span className="text-gray-400 font-normal">{selectedCount(count).adjective}</span>
      </span>

      <span className="w-px h-6 bg-gray-200 dark:bg-white/10" />

      {naming ? (
        <>
          <input
            ref={inputRef}
            className="input py-1.5 w-52 text-sm"
            placeholder="Názov etapy…"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') submit() }}
          />
          <button onClick={submit} disabled={!name.trim() || busy} className="btn-primary text-sm py-1.5 px-3">
            {busy ? 'Vytváram…' : 'Vytvoriť'}
          </button>
          <button onClick={() => { setNaming(false); setName('') }} className="btn-ghost text-sm py-1.5 px-2">
            Späť
          </button>
        </>
      ) : (
        <>
          <button onClick={() => setNaming(true)} disabled={busy} className="btn-primary text-sm py-1.5 px-3">
            <Layers size={15} /> Zoskupiť do etapy
          </button>

          {groups.length > 0 && (
            <div className="relative group/add">
              <button className="btn-outline text-sm py-1.5 px-3" disabled={busy}>
                <FolderOpen size={15} /> Pridať do…
              </button>
              {/* Rozbalí sa nahor — lišta sedí pri spodnom okraji okna. */}
              <div className="absolute bottom-full left-0 mb-2 hidden group-hover/add:block
                              min-w-[12rem] max-h-60 overflow-y-auto overlay p-1">
                {groups.map(g => (
                  <button
                    key={g.id}
                    onClick={() => onAddToGroup(g.id)}
                    className="w-full text-left px-3 py-2 rounded-control text-sm truncate
                               text-gray-700 dark:text-gray-200
                               hover:bg-gray-100 dark:hover:bg-white/[0.06]
                               transition duration-fast"
                  >
                    {g.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {anyGrouped && (
            <button onClick={onUngroup} disabled={busy} className="btn-ghost text-sm py-1.5 px-3">
              Vyradiť z etapy
            </button>
          )}
        </>
      )}

      <span className="w-px h-6 bg-gray-200 dark:bg-white/10" />

      <button
        onClick={onClear}
        className="p-1.5 rounded-control text-gray-400 hover:text-gray-700 dark:hover:text-gray-200
                   hover:bg-gray-100 dark:hover:bg-white/[0.06] transition duration-fast"
        title="Zrušiť výber (Esc)"
      >
        <X size={16} />
      </button>
    </div>
  )
}
