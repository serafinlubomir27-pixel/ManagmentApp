/**
 * NetworkDiagram — sieťový diagram CPM.
 *
 * Plátno, nie obrázok v rámčeku: bodková mriežka, ovládanie pláva nad plochou,
 * uzly sa dajú chytiť a presunúť. Koliesko približuje k miestu, kde je kurzor.
 *
 * Rozmiestnenie sa počíta z ES. Keď si ho používateľ poprehadzuje, posuny sa
 * pamätajú v prehliadači — je to osobný pracovný pohľad, nie vlastnosť projektu,
 * takže kolegom sa diagram nepremiestni pod rukami.
 */
import { useRef, useState, useCallback, useEffect, useMemo } from 'react'
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Network } from 'lucide-react'
import TaskDetailModal from './TaskDetailModal'
import EmptyState from './EmptyState'
import { TaskGroup, groupHex } from './groups'
import { useScheduleRefresh } from '../hooks/useScheduleRefresh'

interface Task {
  id: number
  name: string
  es: number
  ef: number
  ls: number
  lf: number
  total_float: number
  is_critical: boolean
  duration: number
  group_id?: number | null
}

interface Dependency {
  task_id: number
  depends_on_task_id: number
}

interface Props {
  projectId: number
  tasks: Task[]
  dependencies: Dependency[]
  groups?: TaskGroup[]
  teamMembers?: Array<{ id: number; username: string; full_name?: string }>
}

const NODE_W = 172
const NODE_H = 80
const H_GAP = 96
const V_GAP = 48
const PAD = 56
const MIN_ZOOM = 0.2
const MAX_ZOOM = 2.5

type Offsets = Record<number, { dx: number; dy: number }>

const storageKey = (projectId: number) => `nodus.network.layout.${projectId}`

function loadOffsets(projectId: number): Offsets {
  try {
    return JSON.parse(localStorage.getItem(storageKey(projectId)) ?? '{}')
  } catch {
    return {}   // súkromné okno alebo zakázané úložisko — len sa nič nepamätá
  }
}

function saveOffsets(projectId: number, offsets: Offsets) {
  try {
    localStorage.setItem(storageKey(projectId), JSON.stringify(offsets))
  } catch { /* nevadí */ }
}

/** Základné rozmiestnenie: stĺpec podľa ES, v stĺpci pod sebou. */
function computeLayout(tasks: Task[]) {
  const columns = new Map<number, Task[]>()
  for (const t of tasks) {
    const col = t.es ?? 0
    if (!columns.has(col)) columns.set(col, [])
    columns.get(col)!.push(t)
  }
  const positions = new Map<number, { x: number; y: number }>()
  let xCursor = PAD
  for (const col of Array.from(columns.keys()).sort((a, b) => a - b)) {
    let yCursor = PAD
    for (const t of columns.get(col)!) {
      positions.set(t.id, { x: xCursor, y: yCursor })
      yCursor += NODE_H + V_GAP
    }
    xCursor += NODE_W + H_GAP
  }
  return positions
}

export default function NetworkDiagram({ projectId, tasks, dependencies, groups = [], teamMembers }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const refresh = useScheduleRefresh(projectId)

  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [smooth, setSmooth] = useState(false)
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null)
  const [hoverId, setHoverId] = useState<number | null>(null)
  const [offsets, setOffsets] = useState<Offsets>(() => loadOffsets(projectId))

  // Ťahanie: buď plátno (pan), alebo konkrétny uzol.
  const drag = useRef<
    | { kind: 'pan'; lastX: number; lastY: number }
    | { kind: 'node'; id: number; lastX: number; lastY: number; moved: boolean }
    | null
  >(null)

  // Zoom a pan čítajú obslužné rutiny mimo Reactu, preto si ich držíme aj v refe.
  const view = useRef({ zoom: 1, pan: { x: 0, y: 0 } })
  useEffect(() => { view.current = { zoom, pan } }, [zoom, pan])

  const valid = useMemo(() => tasks.filter(t => t.es != null), [tasks])

  const basePositions = useMemo(() => computeLayout(valid), [valid])

  /** Rozmiestnenie po započítaní ručných posunov. */
  const positions = useMemo(() => {
    const out = new Map<number, { x: number; y: number }>()
    basePositions.forEach((p, id) => {
      const o = offsets[id]
      out.set(id, o ? { x: p.x + o.dx, y: p.y + o.dy } : p)
    })
    return out
  }, [basePositions, offsets])

  const bounds = useMemo(() => {
    const pts = Array.from(positions.values())
    if (pts.length === 0) return { w: 1, h: 1 }
    return {
      w: Math.max(...pts.map(p => p.x)) + NODE_W + PAD,
      h: Math.max(...pts.map(p => p.y)) + NODE_H + PAD,
    }
  }, [positions])


  const taskMap = useMemo(() => new Map(valid.map(t => [t.id, t])), [valid])

  // Etapa sa v sieti kreslí ako obálka okolo svojich uzlov. Graf sa tým nemení —
  // je to len rámec, aby bolo vidieť, čo patrí k sebe. Keď používateľ uzly
  // poprehadzuje, obálka sa roztiahne za nimi.
  const regions = useMemo(() => {
    const PAD_R = 22
    return groups.map(g => {
      const pts = valid
        .filter(t => t.group_id === g.id)
        .map(t => positions.get(t.id))
        .filter(Boolean) as Array<{ x: number; y: number }>
      if (pts.length === 0) return null
      const x = Math.min(...pts.map(p => p.x)) - PAD_R
      const y = Math.min(...pts.map(p => p.y)) - PAD_R - 14   // miesto na názov
      return {
        id: g.id, name: g.name, hex: groupHex[g.color] ?? groupHex.brand,
        done: g.done,
        x, y,
        w: Math.max(...pts.map(p => p.x)) + NODE_W + PAD_R - x,
        h: Math.max(...pts.map(p => p.y)) + NODE_H + PAD_R - y,
      }
    }).filter(Boolean) as Array<{
      id: number; name: string; hex: string; done: boolean
      x: number; y: number; w: number; h: number
    }>
  }, [groups, valid, positions])

  const fitToScreen = useCallback(() => {
    const el = containerRef.current
    if (!el) return
    const { width, height } = el.getBoundingClientRect()
    const next = Math.min((width - 48) / bounds.w, (height - 48) / bounds.h, 1)
    setSmooth(true)
    setZoom(next)
    setPan({
      x: (width - bounds.w * next) / 2,
      y: (height - bounds.h * next) / 2,
    })
  }, [bounds])

  // Prispôsob len pri prvom vykreslení projektu. Pôvodne to bežalo pri každej
  // zmene údajov, takže pri úprave úlohy odskočil pohľad naspäť a používateľ
  // prišiel o priblíženie, ktoré si nastavil.
  const fittedFor = useRef<number | null>(null)
  useEffect(() => {
    if (valid.length === 0) return
    if (fittedFor.current === projectId) return
    fittedFor.current = projectId
    fitToScreen()
  }, [projectId, valid.length, fitToScreen])

  // Koliesko. React onWheel je passive, preventDefault by sa ignoroval, preto
  // natívny listener. Približuje sa k bodu pod kurzorom — doteraz sa škálovalo
  // od ľavého horného rohu, takže si musel po každom priblížení doposúvať.
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      const rect = el.getBoundingClientRect()
      const mx = e.clientX - rect.left
      const my = e.clientY - rect.top

      const { zoom: z, pan: p } = view.current
      const factor = e.deltaY > 0 ? 0.88 : 1.14
      const next = Math.min(Math.max(z * factor, MIN_ZOOM), MAX_ZOOM)
      if (next === z) return

      // Bod pod kurzorom v súradniciach obsahu musí ostať na mieste.
      const cx = (mx - p.x) / z
      const cy = (my - p.y) / z
      setSmooth(false)
      setZoom(next)
      setPan({ x: mx - cx * next, y: my - cy * next })
    }

    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [])

  const zoomBy = (factor: number) => {
    const el = containerRef.current
    if (!el) return
    const { width, height } = el.getBoundingClientRect()
    const { zoom: z, pan: p } = view.current
    const next = Math.min(Math.max(z * factor, MIN_ZOOM), MAX_ZOOM)
    // Tlačidlom sa približuje k stredu plochy, nie k rohu.
    const cx = (width / 2 - p.x) / z
    const cy = (height / 2 - p.y) / z
    setSmooth(true)
    setZoom(next)
    setPan({ x: width / 2 - cx * next, y: height / 2 - cy * next })
  }

  // ── Ťahanie ────────────────────────────────────────────────────────────────
  const onPointerDownCanvas = (e: React.PointerEvent) => {
    if (e.button !== 0) return
    drag.current = { kind: 'pan', lastX: e.clientX, lastY: e.clientY }
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }

  const onPointerDownNode = (e: React.PointerEvent, id: number) => {
    if (e.button !== 0) return
    e.stopPropagation()
    drag.current = { kind: 'node', id, lastX: e.clientX, lastY: e.clientY, moved: false }
    ;(e.currentTarget.closest('[data-canvas]') as HTMLElement)?.setPointerCapture(e.pointerId)
  }

  const onPointerMove = (e: React.PointerEvent) => {
    const d = drag.current
    if (!d) return
    const dx = e.clientX - d.lastX
    const dy = e.clientY - d.lastY
    d.lastX = e.clientX
    d.lastY = e.clientY

    if (d.kind === 'pan') {
      setSmooth(false)
      setPan(p => ({ x: p.x + dx, y: p.y + dy }))
      return
    }

    // Pohyb myši o d pixelov na obrazovke je d/zoom v súradniciach obsahu.
    if (Math.abs(dx) > 0 || Math.abs(dy) > 0) d.moved = true
    const z = view.current.zoom
    setOffsets(prev => {
      const cur = prev[d.id] ?? { dx: 0, dy: 0 }
      return { ...prev, [d.id]: { dx: cur.dx + dx / z, dy: cur.dy + dy / z } }
    })
  }

  const onPointerUp = (e: React.PointerEvent) => {
    const d = drag.current
    drag.current = null
    if (!d) return
    try { (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId) } catch { /* ignoruj */ }

    if (d.kind === 'node') {
      if (d.moved) setOffsets(prev => { saveOffsets(projectId, prev); return prev })
      else setSelectedTaskId(d.id)   // klik bez posunu = otvor detail
    }
  }

  const resetLayout = () => {
    setOffsets({})
    saveOffsets(projectId, {})
    fitToScreen()
  }

  const hasManualLayout = Object.keys(offsets).length > 0

  // ── Šípky ──────────────────────────────────────────────────────────────────
  const arrows = useMemo(() => dependencies
    .filter(d => positions.has(d.depends_on_task_id) && positions.has(d.task_id))
    .map(d => {
      const from = positions.get(d.depends_on_task_id)!
      const to = positions.get(d.task_id)!
      const crit = !!taskMap.get(d.depends_on_task_id)?.is_critical
        && !!taskMap.get(d.task_id)?.is_critical
      const touched = hoverId === d.task_id || hoverId === d.depends_on_task_id
      return {
        key: `${d.depends_on_task_id}-${d.task_id}`,
        x1: from.x + NODE_W, y1: from.y + NODE_H / 2,
        x2: to.x,            y2: to.y + NODE_H / 2,
        crit, touched,
      }
    }), [dependencies, positions, taskMap, hoverId])

  // Prázdny stav ide až tu — hooky sa nesmú volať podmienene. Predtým bol
  // `return` nad nimi, takže pridanie prvej úlohy menilo počet hookov a React
  // spadol na „Rendered more hooks than during the previous render".
  if (valid.length === 0) {
    return (
      <EmptyState
        icon={<Network size={20} />}
        title="Sieť sa zatiaľ nedá zostaviť"
        hint="Pridaj úlohy a nastav medzi nimi závislosti — z nich vznikne sieť aj kritická cesta."
      />
    )
  }

  const btn = 'p-2 rounded-control text-gray-500 dark:text-gray-400 transition duration-fast ease-out ' +
    'hover:bg-gray-100 dark:hover:bg-white/[0.08] hover:text-gray-900 dark:hover:text-white ' +
    'disabled:opacity-40 disabled:pointer-events-none'

  return (
    <>
      <div className="relative">
        <div
          ref={containerRef}
          data-canvas
          onPointerDown={onPointerDownCanvas}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          className="relative w-full h-[min(72vh,660px)] overflow-hidden rounded-card
                     cursor-grab active:cursor-grabbing touch-none
                     bg-gray-50 dark:bg-[#0c1223]
                     border border-gray-200 dark:border-white/[0.07]"
          style={{
            // Bodková mriežka posúva a škáluje sa spolu s obsahom, takže plocha
            // pôsobí ako plátno, nie ako obrázok v rámčeku.
            backgroundImage: 'radial-gradient(currentColor 1px, transparent 1px)',
            backgroundSize: `${24 * zoom}px ${24 * zoom}px`,
            backgroundPosition: `${pan.x}px ${pan.y}px`,
            color: 'rgb(148 163 184 / 0.28)',
          }}
        >
          <svg
            width={bounds.w}
            height={bounds.h}
            className="font-sans select-none absolute top-0 left-0"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: '0 0',
              transition: smooth ? 'transform 180ms cubic-bezier(0.22, 1, 0.36, 1)' : 'none',
            }}
          >
            <defs>
              <marker id="arrow-normal" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
                <path d="M0,0 L0,6 L8,3 z" className="fill-gray-400" />
              </marker>
              <marker id="arrow-critical" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
                <path d="M0,0 L0,6 L8,3 z" fill="#ef4444" />
              </marker>
            </defs>

            {/* Obálky etáp — pod šípkami aj uzlami, aby nič neprekryli. */}
            {regions.map(r => (
              <g key={`region-${r.id}`} style={{ pointerEvents: 'none' }}>
                <rect
                  x={r.x} y={r.y} width={r.w} height={r.h} rx={16}
                  fill={r.hex} fillOpacity={0.06}
                  stroke={r.hex} strokeOpacity={0.35} strokeWidth={1.5}
                  strokeDasharray="6 4"
                />
                <text
                  x={r.x + 12} y={r.y + 15}
                  fontSize={11} fontWeight={600} fill={r.hex} fillOpacity={0.9}
                >
                  {r.name}{r.done ? ' ✓' : ''}
                </text>
              </g>
            ))}

            {arrows.map(a => {
              const c1 = a.x1 + H_GAP * 0.5
              const c2 = a.x2 - H_GAP * 0.5
              return (
                <path
                  key={a.key}
                  d={`M${a.x1},${a.y1} C${c1},${a.y1} ${c2},${a.y2} ${a.x2},${a.y2}`}
                  fill="none"
                  stroke={a.crit ? '#ef4444' : 'currentColor'}
                  className={a.crit ? '' : 'text-gray-400 dark:text-gray-600'}
                  strokeWidth={a.crit ? 2.5 : 1.5}
                  markerEnd={a.crit ? 'url(#arrow-critical)' : 'url(#arrow-normal)'}
                  opacity={hoverId === null ? 0.85 : a.touched ? 1 : 0.25}
                  style={{ transition: 'opacity 120ms' }}
                />
              )
            })}

            {valid.map(t => {
              const pos = positions.get(t.id)!
              const dim = hoverId !== null && hoverId !== t.id
                && !arrows.some(a => a.touched && a.key.split('-').includes(String(t.id)))
              const short = t.name.length > 21 ? t.name.slice(0, 20) + '…' : t.name

              return (
                <g
                  key={t.id}
                  transform={`translate(${pos.x},${pos.y})`}
                  onPointerDown={e => onPointerDownNode(e, t.id)}
                  onPointerEnter={() => setHoverId(t.id)}
                  onPointerLeave={() => setHoverId(null)}
                  className="cursor-grab active:cursor-grabbing"
                  opacity={dim ? 0.35 : 1}
                  style={{ transition: 'opacity 120ms' }}
                >
                  <title>{t.name}</title>

                  <rect
                    width={NODE_W} height={NODE_H} rx={12}
                    className={`fill-white dark:fill-surface-raised-dark ${
                      t.is_critical ? 'stroke-red-500' : 'stroke-brand-500'
                    }`}
                    strokeWidth={t.is_critical ? 2.5 : 1.5}
                  />

                  {/* hlavička */}
                  <path
                    d={`M0,12 A12,12 0 0 1 12,0 L${NODE_W - 12},0 A12,12 0 0 1 ${NODE_W},12 L${NODE_W},30 L0,30 Z`}
                    className={t.is_critical
                      ? 'fill-red-50 dark:fill-red-500/15'
                      : 'fill-brand-50 dark:fill-brand-500/15'}
                  />

                  <text x={10} y={20} fontSize={13} fontWeight={700}
                    className={t.is_critical ? 'fill-red-500' : 'fill-brand-500'}>{t.es}</text>
                  <text x={NODE_W / 2} y={20} textAnchor="middle" fontSize={10}
                    className={t.is_critical
                      ? 'fill-red-700 dark:fill-red-300'
                      : 'fill-gray-700 dark:fill-gray-200'}>{short}</text>
                  <text x={NODE_W - 10} y={20} textAnchor="end" fontSize={13} fontWeight={700}
                    className={t.is_critical ? 'fill-red-500' : 'fill-brand-500'}>{t.ef}</text>

                  <line x1={0} y1={30} x2={NODE_W} y2={30}
                    className={t.is_critical ? 'stroke-red-500' : 'stroke-brand-500'}
                    strokeWidth={1} opacity={0.3} />
                  <line x1={NODE_W / 2} y1={30} x2={NODE_W / 2} y2={NODE_H}
                    className="stroke-gray-300 dark:stroke-white/10" strokeWidth={1} />

                  <text x={10} y={58} fontSize={13} fontWeight={600}
                    className="fill-gray-500 dark:fill-gray-400">{t.ls}</text>
                  <text x={NODE_W / 2} y={58} textAnchor="middle" fontSize={11} fontWeight={600}
                    className={t.total_float === 0 ? 'fill-red-500' : 'fill-amber-500'}>
                    R: {t.total_float}d
                  </text>
                  <text x={NODE_W - 10} y={58} textAnchor="end" fontSize={13} fontWeight={600}
                    className="fill-gray-500 dark:fill-gray-400">{t.lf}</text>

                  <text x={10} y={72} fontSize={8} className="fill-gray-300 dark:fill-gray-600">ES / LS</text>
                  <text x={NODE_W / 2} y={72} textAnchor="middle" fontSize={8}
                    className="fill-gray-300 dark:fill-gray-600">Rezerva</text>
                  <text x={NODE_W - 10} y={72} textAnchor="end" fontSize={8}
                    className="fill-gray-300 dark:fill-gray-600">EF / LF</text>
                </g>
              )
            })}
          </svg>

          {/* Ovládanie pláva nad plochou — nie je to lišta, ktorá diagram odreže. */}
          <div className="absolute top-3 right-3 flex items-center gap-0.5 p-1
                          rounded-control bg-white/85 dark:bg-surface-raised-dark/85 backdrop-blur
                          border border-gray-200 dark:border-white/[0.1] shadow-card">
            <span className="px-2 text-xs tabular-nums text-gray-400 select-none">
              {Math.round(zoom * 100)}%
            </span>
            <button onClick={() => zoomBy(1.2)} className={btn} title="Priblížiť" disabled={zoom >= MAX_ZOOM}>
              <ZoomIn size={16} />
            </button>
            <button onClick={() => zoomBy(1 / 1.2)} className={btn} title="Oddialiť" disabled={zoom <= MIN_ZOOM}>
              <ZoomOut size={16} />
            </button>
            <button onClick={fitToScreen} className={btn} title="Prispôsobiť obrazovke">
              <Maximize2 size={16} />
            </button>
            {hasManualLayout && (
              <button onClick={resetLayout} className={btn} title="Vrátiť pôvodné rozmiestnenie">
                <RotateCcw size={16} />
              </button>
            )}
          </div>

          <div className="absolute bottom-3 left-3 flex flex-wrap items-center gap-x-4 gap-y-1 px-3 py-1.5
                          rounded-control bg-white/85 dark:bg-surface-raised-dark/85 backdrop-blur
                          border border-gray-200 dark:border-white/[0.1] shadow-card
                          text-xs text-gray-500 dark:text-gray-400 select-none">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm border-2 border-red-500" /> Kritická
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm border-2 border-brand-500" /> Bežná
            </span>
            <span className="hidden sm:inline text-gray-400 dark:text-gray-500">
              ES/LS · Rezerva · EF/LF
            </span>
          </div>

          <p className="absolute bottom-3 right-3 text-xs text-gray-400 dark:text-gray-600 select-none hidden md:block">
            Ťahaj úlohu pre presun · plochu pre posun · koliesko približuje ku kurzoru
          </p>
        </div>
      </div>

      {selectedTaskId !== null && (
        <TaskDetailModal
          taskId={selectedTaskId}
          teamMembers={teamMembers ?? []}
          onClose={() => setSelectedTaskId(null)}
          onUpdated={() => refresh(selectedTaskId)}
        />
      )}
    </>
  )
}
