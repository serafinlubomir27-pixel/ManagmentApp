/**
 * NetworkDiagram — interaktívny CPM sieťový diagram.
 * - Zoom kolieskom myši
 * - Pan (ťahanie myšou)
 * - Tlačidlá +/- a Fit (prispôsob celú schému)
 */
import { useRef, useState, useCallback, useEffect } from 'react'
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

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
}

interface Dependency {
  task_id: number
  depends_on_task_id: number
}

interface Props {
  tasks: Task[]
  dependencies: Dependency[]
}

const NODE_W = 164
const NODE_H = 76
const H_GAP = 90
const V_GAP = 44
const PAD = 48

// ── Layout: rozmiestni uzly do stĺpcov podľa ES ─────────────────────────────
function computeLayout(tasks: Task[]) {
  const columns = new Map<number, Task[]>()
  for (const t of tasks) {
    const col = t.es ?? 0
    if (!columns.has(col)) columns.set(col, [])
    columns.get(col)!.push(t)
  }
  const sortedCols = Array.from(columns.keys()).sort((a, b) => a - b)
  const positions = new Map<number, { x: number; y: number }>()
  let xCursor = PAD
  for (const col of sortedCols) {
    const colTasks = columns.get(col)!
    let yCursor = PAD
    for (const t of colTasks) {
      positions.set(t.id, { x: xCursor, y: yCursor })
      yCursor += NODE_H + V_GAP
    }
    xCursor += NODE_W + H_GAP
  }
  const maxX = xCursor - H_GAP + PAD
  const maxY = Math.max(...Array.from(positions.values()).map(p => p.y)) + NODE_H + PAD
  return { positions, maxX, maxY }
}

export default function NetworkDiagram({ tasks, dependencies }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const dragging = useRef(false)
  const lastMouse = useRef({ x: 0, y: 0 })

  const valid = tasks.filter(t => t.es != null)
  if (valid.length === 0) {
    return (
      <div className="py-10 text-center text-gray-400 text-sm">
        CPM dáta nie sú dostupné — pridaj úlohy a závislosti
      </div>
    )
  }

  const { positions, maxX, maxY } = computeLayout(valid)
  const taskMap = new Map(valid.map(t => [t.id, t]))

  // ── Fit to screen ──────────────────────────────────────────────────────────
  const fitToScreen = useCallback(() => {
    if (!containerRef.current) return
    const { width, height } = containerRef.current.getBoundingClientRect()
    const scaleX = (width - 32) / maxX
    const scaleY = (height - 32) / maxY
    const newZoom = Math.min(scaleX, scaleY, 1)
    setZoom(newZoom)
    setPan({ x: 0, y: 0 })
  }, [maxX, maxY])

  useEffect(() => { fitToScreen() }, [fitToScreen])

  // ── Zoom koliesko ──────────────────────────────────────────────────────────
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setZoom(z => Math.min(Math.max(z * delta, 0.15), 3))
  }, [])

  // ── Pan myšou ─────────────────────────────────────────────────────────────
  const handleMouseDown = (e: React.MouseEvent) => {
    dragging.current = true
    lastMouse.current = { x: e.clientX, y: e.clientY }
  }
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging.current) return
    const dx = e.clientX - lastMouse.current.x
    const dy = e.clientY - lastMouse.current.y
    lastMouse.current = { x: e.clientX, y: e.clientY }
    setPan(p => ({ x: p.x + dx, y: p.y + dy }))
  }
  const handleMouseUp = () => { dragging.current = false }

  // ── Šípky ─────────────────────────────────────────────────────────────────
  const arrows = dependencies
    .filter(d => positions.has(d.depends_on_task_id) && positions.has(d.task_id))
    .map(d => {
      const from = positions.get(d.depends_on_task_id)!
      const to = positions.get(d.task_id)!
      const x1 = from.x + NODE_W
      const y1 = from.y + NODE_H / 2
      const x2 = to.x
      const y2 = to.y + NODE_H / 2
      const isCrit = taskMap.get(d.depends_on_task_id)?.is_critical && taskMap.get(d.task_id)?.is_critical
      return { x1, y1, x2, y2, isCrit }
    })

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-dark overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 dark:border-gray-800">
        <span className="text-xs text-gray-400 mr-2">
          Zoom: {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={() => setZoom(z => Math.min(z * 1.2, 3))}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
          title="Priblíž"
        >
          <ZoomIn size={16} />
        </button>
        <button
          onClick={() => setZoom(z => Math.max(z * 0.8, 0.15))}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
          title="Oddiaľ"
        >
          <ZoomOut size={16} />
        </button>
        <button
          onClick={fitToScreen}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
          title="Prispôsob obrazovke"
        >
          <Maximize2 size={16} />
        </button>
        <div className="flex gap-1 ml-4 text-xs text-gray-400">
          <span className="inline-flex items-center gap-1">
            <span className="w-3 h-3 rounded border-2 border-red-500 inline-block" /> Kritická
          </span>
          <span className="inline-flex items-center gap-1 ml-3">
            <span className="w-3 h-3 rounded border-2 border-brand-500 inline-block" /> Normálna
          </span>
          <span className="ml-3 hidden sm:inline">
            ES = Early Start | EF = Early Finish | R = Rezerva
          </span>
        </div>
        <span className="ml-auto text-xs text-gray-300 dark:text-gray-600 hidden sm:inline">
          🖱 ťahaj pre posun · koliesko pre zoom
        </span>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        className="w-full overflow-hidden cursor-grab active:cursor-grabbing"
        style={{ height: '520px' }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          width={maxX}
          height={maxY}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: '0 0',
            transition: dragging.current ? 'none' : 'transform 0.05s',
          }}
          className="font-sans select-none"
        >
          <defs>
            <marker id="arr-n" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill="#9ca3af" />
            </marker>
            <marker id="arr-c" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill="#ef4444" />
            </marker>
            {/* Drop shadow filter */}
            <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.10" />
            </filter>
          </defs>

          {/* Šípky */}
          {arrows.map((a, i) => {
            const cx1 = a.x1 + H_GAP * 0.45
            const cx2 = a.x2 - H_GAP * 0.45
            return (
              <path
                key={i}
                d={`M${a.x1},${a.y1} C${cx1},${a.y1} ${cx2},${a.y2} ${a.x2},${a.y2}`}
                fill="none"
                stroke={a.isCrit ? '#ef4444' : '#9ca3af'}
                strokeWidth={a.isCrit ? 2.5 : 1.5}
                strokeDasharray={a.isCrit ? undefined : undefined}
                markerEnd={a.isCrit ? 'url(#arr-c)' : 'url(#arr-n)'}
                opacity={0.85}
              />
            )
          })}

          {/* Uzly */}
          {valid.map(t => {
            const pos = positions.get(t.id)!
            const border = t.is_critical ? '#ef4444' : '#4B7FFF'
            const headerFill = t.is_critical ? '#fff5f5' : '#f0f4ff'
            const short = t.name.length > 20 ? t.name.slice(0, 19) + '…' : t.name

            return (
              <g key={t.id} transform={`translate(${pos.x},${pos.y})`} filter="url(#shadow)">
                {/* Telo */}
                <rect width={NODE_W} height={NODE_H} rx={10}
                  fill="white" stroke={border} strokeWidth={t.is_critical ? 2.5 : 1.5} />

                {/* Header */}
                <rect width={NODE_W} height={28} rx={10} fill={headerFill} />
                <rect y={18} width={NODE_W} height={10} fill={headerFill} />

                {/* ES */}
                <text x={10} y={19} fontSize={13} fontWeight={700} fill={border}>{t.es}</text>
                {/* Názov */}
                <text x={NODE_W / 2} y={19} textAnchor="middle" fontSize={10}
                  fill={t.is_critical ? '#b91c1c' : '#374151'}>{short}</text>
                {/* EF */}
                <text x={NODE_W - 10} y={19} textAnchor="end" fontSize={13} fontWeight={700} fill={border}>{t.ef}</text>

                {/* Oddeľovač */}
                <line x1={0} y1={28} x2={NODE_W} y2={28} stroke={border} strokeWidth={1} opacity={0.3} />
                <line x1={NODE_W / 2} y1={28} x2={NODE_W / 2} y2={NODE_H} stroke={border} strokeWidth={1} opacity={0.15} />

                {/* LS */}
                <text x={10} y={56} fontSize={13} fontWeight={600} fill="#6b7280">{t.ls}</text>
                {/* Float */}
                <text x={NODE_W / 2} y={56} textAnchor="middle" fontSize={11}
                  fill={t.total_float === 0 ? '#ef4444' : '#f59e0b'}
                  fontWeight={600}>
                  R: {t.total_float}d
                </text>
                {/* LF */}
                <text x={NODE_W - 10} y={56} textAnchor="end" fontSize={13} fontWeight={600} fill="#6b7280">{t.lf}</text>

                {/* Malé popisky */}
                <text x={10} y={70} fontSize={8} fill="#d1d5db">ES / LS</text>
                <text x={NODE_W / 2} y={70} textAnchor="middle" fontSize={8} fill="#d1d5db">Rezerva</text>
                <text x={NODE_W - 10} y={70} textAnchor="end" fontSize={8} fill="#d1d5db">EF / LF</text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
