/**
 * NetworkDiagram — CPM sieťový diagram (AON — Activity On Node).
 * Každá úloha je uzol so 6 poliami: ES | Názov | EF
 *                                    LS | Float  | LF
 * Šípky znázorňujú závislosti. Kritická cesta je červená.
 */

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

const NODE_W = 160
const NODE_H = 72
const H_GAP = 80
const V_GAP = 40

export default function NetworkDiagram({ tasks, dependencies }: Props) {
  const valid = tasks.filter((t) => t.es != null)
  if (valid.length === 0) {
    return (
      <div className="py-10 text-center text-gray-400 text-sm">
        CPM dáta nie sú dostupné — pridaj úlohy a závislosti
      </div>
    )
  }

  // ── Layout: zoraď úlohy do stĺpcov podľa ES hodnoty ──────────────────────
  const columns = new Map<number, Task[]>()
  for (const t of valid) {
    const col = t.es
    if (!columns.has(col)) columns.set(col, [])
    columns.get(col)!.push(t)
  }
  const sortedCols = Array.from(columns.keys()).sort((a, b) => a - b)

  // Vypočítaj pozície uzlov
  const positions = new Map<number, { x: number; y: number }>()
  let xCursor = 40
  for (const col of sortedCols) {
    const colTasks = columns.get(col)!
    const colH = colTasks.length * NODE_H + (colTasks.length - 1) * V_GAP
    let yCursor = 40
    for (const t of colTasks) {
      positions.set(t.id, { x: xCursor, y: yCursor })
      yCursor += NODE_H + V_GAP
    }
    xCursor += NODE_W + H_GAP
  }

  const maxX = xCursor - H_GAP + 40
  const maxY = Math.max(...Array.from(positions.values()).map((p) => p.y)) + NODE_H + 40

  // ── Kresli šípky ─────────────────────────────────────────────────────────
  const taskMap = new Map(valid.map((t) => [t.id, t]))

  const arrows = dependencies
    .filter((d) => positions.has(d.depends_on_task_id) && positions.has(d.task_id))
    .map((d) => {
      const from = positions.get(d.depends_on_task_id)!
      const to = positions.get(d.task_id)!
      const x1 = from.x + NODE_W
      const y1 = from.y + NODE_H / 2
      const x2 = to.x
      const y2 = to.y + NODE_H / 2
      const isCritical =
        taskMap.get(d.depends_on_task_id)?.is_critical &&
        taskMap.get(d.task_id)?.is_critical
      return { x1, y1, x2, y2, isCritical }
    })

  return (
    <div className="overflow-auto rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-dark">
      <svg width={maxX} height={maxY} className="font-sans select-none">
        <defs>
          <marker id="arrow-normal" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#9ca3af" />
          </marker>
          <marker id="arrow-critical" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#ef4444" />
          </marker>
        </defs>

        {/* Šípky */}
        {arrows.map((a, i) => {
          const cx1 = a.x1 + H_GAP * 0.4
          const cx2 = a.x2 - H_GAP * 0.4
          return (
            <path
              key={i}
              d={`M${a.x1},${a.y1} C${cx1},${a.y1} ${cx2},${a.y2} ${a.x2},${a.y2}`}
              fill="none"
              stroke={a.isCritical ? '#ef4444' : '#9ca3af'}
              strokeWidth={a.isCritical ? 2 : 1.5}
              markerEnd={a.isCritical ? 'url(#arrow-critical)' : 'url(#arrow-normal)'}
            />
          )
        })}

        {/* Uzly */}
        {valid.map((t) => {
          const pos = positions.get(t.id)!
          const borderColor = t.is_critical ? '#ef4444' : '#4B7FFF'
          const headerBg = t.is_critical ? '#fef2f2' : '#eff6ff'
          const headerBgDark = t.is_critical ? 'rgba(239,68,68,0.15)' : 'rgba(75,127,255,0.15)'
          const shortName = t.name.length > 18 ? t.name.slice(0, 17) + '…' : t.name

          return (
            <g key={t.id} transform={`translate(${pos.x}, ${pos.y})`}>
              {/* Rámček */}
              <rect
                width={NODE_W}
                height={NODE_H}
                rx={8}
                fill="white"
                stroke={borderColor}
                strokeWidth={t.is_critical ? 2 : 1.5}
              />

              {/* Horný riadok: ES | Názov | EF */}
              <rect width={NODE_W} height={24} rx={8} fill={headerBg} />
              <rect y={16} width={NODE_W} height={8} fill={headerBg} />

              {/* ES */}
              <text x={10} y={16} fontSize={12} fontWeight={700} fill={borderColor}>
                {t.es}
              </text>

              {/* Názov */}
              <text x={NODE_W / 2} y={16} textAnchor="middle" fontSize={10} fill="#374151">
                {shortName}
              </text>

              {/* EF */}
              <text x={NODE_W - 10} y={16} textAnchor="end" fontSize={12} fontWeight={700} fill={borderColor}>
                {t.ef}
              </text>

              {/* Oddeľovač */}
              <line x1={0} y1={24} x2={NODE_W} y2={24} stroke={borderColor} strokeWidth={1} opacity={0.4} />
              <line x1={NODE_W / 2} y1={24} x2={NODE_W / 2} y2={NODE_H} stroke={borderColor} strokeWidth={1} opacity={0.25} />

              {/* Dolný riadok: LS | Float | LF */}
              <text x={10} y={54} fontSize={12} fontWeight={600} fill="#6b7280">
                {t.ls}
              </text>
              <text x={NODE_W / 2} y={54} textAnchor="middle" fontSize={10} fill={t.total_float === 0 ? '#ef4444' : '#f59e0b'}>
                R: {t.total_float}d
              </text>
              <text x={NODE_W - 10} y={54} textAnchor="end" fontSize={12} fontWeight={600} fill="#6b7280">
                {t.lf}
              </text>

              {/* Popis polí (malý text) */}
              <text x={10} y={68} fontSize={8} fill="#d1d5db">ES</text>
              <text x={NODE_W / 2} y={68} textAnchor="middle" fontSize={8} fill="#d1d5db">Rezerva</text>
              <text x={NODE_W - 10} y={68} textAnchor="end" fontSize={8} fill="#d1d5db">EF</text>
            </g>
          )
        })}

        {/* Legenda */}
        <g transform={`translate(40, ${maxY - 24})`}>
          <rect width={12} height={12} rx={2} fill="none" stroke="#ef4444" strokeWidth={2} />
          <text x={16} y={10} fontSize={10} fill="#9ca3af">Kritická úloha</text>
          <rect x={110} width={12} height={12} rx={2} fill="none" stroke="#4B7FFF" strokeWidth={1.5} />
          <text x={126} y={10} fontSize={10} fill="#9ca3af">Normálna úloha</text>
          <text x={250} y={10} fontSize={10} fill="#9ca3af">ES = Early Start | EF = Early Finish | R = Rezerva (float)</text>
        </g>
      </svg>
    </div>
  )
}
