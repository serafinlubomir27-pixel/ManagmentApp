import { BarChart2 } from 'lucide-react'
import EmptyState from './EmptyState'
import { TaskGroup, groupHex } from './groups'

/**
 * GanttChart — jednoduchý Gantt diagram kreslený cez SVG.
 * Zobrazuje úlohy ako horizontálne pruhy podľa ES/EF hodnôt z CPM.
 * Kritické úlohy sú červené, ostatné modré.
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
  status: string
  group_id?: number | null
}

interface GanttChartProps {
  tasks: Task[]
  groups?: TaskGroup[]
}

const BAR_HEIGHT = 28
const BAR_GAP = 10
const ROW_HEIGHT = BAR_HEIGHT + BAR_GAP
const DAY_WIDTH = 36
// Stĺpec s názvami bol pevných 200 px a názov sa orezal po 22 znakoch, takže
// z „Elektroinštalácia a rozvody" ostalo „Elektroinštalácia a r…". Šírka sa
// teraz odvíja od najdlhšieho názvu, v rozumných medziach.
const LABEL_MIN = 150
const LABEL_MAX = 300
const CHAR_W = 6.6        // priemerná šírka znaku Inter pri 12 px, s rezervou
const LABEL_PAD = 16
const PADDING_TOP = 40
const PADDING_BOTTOM = 20

export default function GanttChart({ tasks, groups = [] }: GanttChartProps) {
  const filtered = tasks.filter((t) => t.es != null && t.ef != null && t.ef > t.es)

  // Úlohy sa zoradia podľa etáp, aby bol pruh etapy súvislý. Nezaradené idú
  // nakoniec — v zozname úloh je to rovnako, nech sa pohľady zhodujú.
  const order = new Map(groups.map((g, i) => [g.id, i]))
  const validTasks = [...filtered].sort((a, b) => {
    const ga = a.group_id != null ? order.get(a.group_id) ?? 1e6 : 1e6
    const gb = b.group_id != null ? order.get(b.group_id) ?? 1e6 : 1e6
    return ga - gb
  })

  if (validTasks.length === 0) {
    return (
      <EmptyState
        icon={<BarChart2 size={20} />}
        title="Gantt sa zatiaľ nedá zostaviť"
        hint="Pridaj úlohy s trvaním a nastav medzi nimi závislosti — z nich vyjdú termíny aj kritická cesta."
      />
    )
  }

  const maxDay = Math.max(...validTasks.map((t) => t.lf ?? t.ef))
  const totalDays = maxDay + 2

  const longest = Math.max(...validTasks.map((t) => t.name.length))
  const LABEL_WIDTH = Math.min(LABEL_MAX, Math.max(LABEL_MIN, longest * CHAR_W + LABEL_PAD))
  // Koľko znakov sa do stĺpca ešte zmestí; zvyšok sa oreže a celý názov
  // ostane dostupný cez natívny tooltip.
  const maxChars = Math.floor((LABEL_WIDTH - LABEL_PAD) / CHAR_W)

  const svgWidth = LABEL_WIDTH + totalDays * DAY_WIDTH + 20
  // Zoznam riadkov na vykreslenie: hlavička etapy, potom jej úlohy.
  // Výška sa počíta priebežne, lebo hlavička je nižšia než riadok úlohy.
  const GROUP_H = 24
  type Row =
    | { kind: 'group'; group: TaskGroup; y: number }
    | { kind: 'task'; task: Task; y: number; group: TaskGroup | null }

  const byId = new Map(groups.map(g => [g.id, g]))
  const rows: Row[] = []
  let cursor = PADDING_TOP
  let lastGroup: number | null | undefined = undefined

  for (const task of validTasks) {
    const gid = task.group_id ?? null
    if (gid !== lastGroup) {
      lastGroup = gid
      const g = gid != null ? byId.get(gid) : undefined
      if (g) {
        rows.push({ kind: 'group', group: g, y: cursor })
        cursor += GROUP_H
      }
    }
    rows.push({ kind: 'task', task, y: cursor, group: gid != null ? byId.get(gid) ?? null : null })
    cursor += ROW_HEIGHT
  }

  const svgHeight = cursor + PADDING_BOTTOM

  // Dni na osi X
  const dayTicks = Array.from({ length: totalDays + 1 }, (_, i) => i)

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-dark">
      <svg
        width={svgWidth}
        height={svgHeight}
        className="font-sans text-xs select-none"
      >
        {/* Pozadie riadkov (zebra) */}
        {rows.map((r, i) => r.kind === 'task' && (
          <rect
            key={`zebra-${i}`}
            x={0} y={r.y} width={svgWidth} height={ROW_HEIGHT}
            // rgba(0,0,0,0.02) bolo v tmavom režime neviditeľné
            className={i % 2 === 0 ? 'fill-transparent' : 'fill-black/[0.025] dark:fill-white/[0.04]'}
          />
        ))}

        {/* Hlavičky etáp — rovnaké poradie aj farby ako v zozname úloh. */}
        {rows.map((r, i) => r.kind === 'group' && (
          <g key={`group-${r.group.id}`}>
            <rect
              x={0} y={r.y + 2} width={svgWidth} height={GROUP_H - 4} rx={4}
              fill={groupHex[r.group.color]} fillOpacity={0.08}
            />
            <rect x={0} y={r.y + 2} width={3} height={GROUP_H - 4} rx={1.5}
                  fill={groupHex[r.group.color]} />
            <text
              x={10} y={r.y + GROUP_H / 2 + 4}
              fontSize={11} fontWeight={600}
              fill={groupHex[r.group.color]}
            >
              {r.group.name}
              {r.group.done ? ' ✓' : ` · ${Math.round(r.group.progress * 100)} %`}
            </text>
          </g>
        ))}

        {/* Vertikálne mriežkové čiary */}
        {dayTicks.map((d) => (
          <line
            key={d}
            x1={LABEL_WIDTH + d * DAY_WIDTH}
            y1={PADDING_TOP - 10}
            x2={LABEL_WIDTH + d * DAY_WIDTH}
            y2={svgHeight - PADDING_BOTTOM}
            stroke="rgba(156,163,175,0.3)"
            strokeWidth={1}
          />
        ))}

        {/* Osa X — čísla dní */}
        {dayTicks.filter((d) => d % 2 === 0).map((d) => (
          <text
            key={d}
            x={LABEL_WIDTH + d * DAY_WIDTH + DAY_WIDTH / 2}
            y={PADDING_TOP - 14}
            textAnchor="middle"
            fill="rgb(156,163,175)"
            fontSize={11}
          >
            {d}
          </text>
        ))}
        <text
          x={LABEL_WIDTH + 4}
          y={PADDING_TOP - 24}
          fill="rgb(156,163,175)"
          fontSize={10}
        >
          Deň →
        </text>

        {/* Úlohy */}
        {rows.map(r => {
          if (r.kind !== 'task') return null
          const task = r.task
          const y = r.y
          const barX = LABEL_WIDTH + task.es * DAY_WIDTH
          const barW = Math.max((task.ef - task.es) * DAY_WIDTH, 4)
          const floatW = task.total_float > 0 ? task.total_float * DAY_WIDTH : 0

          // Hotová úloha má prednosť pred kritickou. Doteraz vyhrávala
          // kritickosť, takže dokončená etapa mala všetky pruhy červené a
          // vyzerala ako problém, hoci na nej už nie je čo riešiť. Že úloha
          // leží na kritickej ceste, ostáva vidieť podľa bodky pred pruhom.
          const barColor = task.status === 'completed'
            ? '#22c55e'   // zelená — hotová
            : task.is_critical
            ? '#ef4444'   // červená — kritická
            : '#4B7FFF'   // modrá — normálna

          const floatColor = 'rgba(251,191,36,0.35)'  // žltá — rezerva

          return (
            <g key={task.id}>
              {/* Farba etapy — spojí riadok s hlavičkou, aj keď je mimo dohľadu */}
              {r.group && (
                <rect
                  x={2} y={y + ROW_HEIGHT / 2 - 6} width={3} height={12} rx={1.5}
                  fill={groupHex[r.group.color]}
                />
              )}

              {/* Popis úlohy */}
              <text
                x={LABEL_WIDTH - 8}
                y={y + ROW_HEIGHT / 2 + 4}
                textAnchor="end"
                fill="rgb(75,85,99)"
                fontSize={12}
                className="dark:fill-gray-300"
              >
                {task.name.length > maxChars
                  ? task.name.slice(0, maxChars - 1).trimEnd() + '…'
                  : task.name}
                <title>{task.name}</title>
              </text>

              {/* Float / rezerva (LS→LF) */}
              {floatW > 0 && (
                <rect
                  x={barX + barW}
                  y={y + 6}
                  width={floatW}
                  height={BAR_HEIGHT - 12}
                  rx={3}
                  fill={floatColor}
                />
              )}

              {/* Hlavný pruh */}
              <rect
                x={barX}
                y={y + 4}
                width={barW}
                height={BAR_HEIGHT - 8}
                rx={4}
                fill={barColor}
                opacity={task.status === 'completed' ? 0.7 : 1}
              />

              {/* ES a EF hodnoty vo vnútri pruhu */}
              {barW > 40 && (
                <text
                  x={barX + barW / 2}
                  y={y + ROW_HEIGHT / 2 + 4}
                  textAnchor="middle"
                  fill="white"
                  fontSize={10}
                  fontWeight={600}
                >
                  {task.es}–{task.ef}
                </text>
              )}

              {/* Kritická značka */}
              {task.is_critical && (
                <circle
                  cx={barX - 8}
                  cy={y + ROW_HEIGHT / 2}
                  r={3}
                  fill="#ef4444"
                />
              )}
            </g>
          )
        })}

        {/* Legenda */}
        <g transform={`translate(${LABEL_WIDTH}, ${svgHeight - 16})`}>
          <rect x={0} y={-8} width={12} height={10} rx={2} fill="#ef4444" />
          <text x={16} y={0} fill="rgb(156,163,175)" fontSize={10}>Kritická</text>
          <rect x={70} y={-8} width={12} height={10} rx={2} fill="#4B7FFF" />
          <text x={86} y={0} fill="rgb(156,163,175)" fontSize={10}>Normálna</text>
          <rect x={156} y={-8} width={12} height={10} rx={2} fill="#22c55e" />
          <text x={172} y={0} fill="rgb(156,163,175)" fontSize={10}>Hotová</text>
          <rect x={222} y={-8} width={12} height={10} rx={2} fill="rgba(251,191,36,0.5)" />
          <text x={238} y={0} fill="rgb(156,163,175)" fontSize={10}>Rezerva</text>
        </g>
      </svg>
    </div>
  )
}
