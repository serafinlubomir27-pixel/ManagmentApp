import { BarChart2 } from 'lucide-react'
import EmptyState from './EmptyState'

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
}

interface GanttChartProps {
  tasks: Task[]
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

export default function GanttChart({ tasks }: GanttChartProps) {
  const validTasks = tasks.filter((t) => t.es != null && t.ef != null && t.ef > t.es)

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
  const svgHeight = PADDING_TOP + validTasks.length * ROW_HEIGHT + PADDING_BOTTOM

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
        {validTasks.map((_, i) => (
          <rect
            key={i}
            x={0}
            y={PADDING_TOP + i * ROW_HEIGHT}
            width={svgWidth}
            height={ROW_HEIGHT}
            // rgba(0,0,0,0.02) bolo v tmavom režime neviditeľné
            className={i % 2 === 0 ? 'fill-transparent' : 'fill-black/[0.025] dark:fill-white/[0.04]'}
          />
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
        {validTasks.map((task, i) => {
          const y = PADDING_TOP + i * ROW_HEIGHT
          const barX = LABEL_WIDTH + task.es * DAY_WIDTH
          const barW = Math.max((task.ef - task.es) * DAY_WIDTH, 4)
          const floatW = task.total_float > 0 ? task.total_float * DAY_WIDTH : 0

          const barColor = task.is_critical
            ? '#ef4444'   // červená — kritická
            : task.status === 'completed'
            ? '#22c55e'   // zelená — hotová
            : '#4B7FFF'   // modrá — normálna

          const floatColor = 'rgba(251,191,36,0.35)'  // žltá — rezerva

          return (
            <g key={task.id}>
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
