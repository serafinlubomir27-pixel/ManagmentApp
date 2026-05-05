/**
 * RiskScoreWidget — displays the AI-computed composite risk score for a project.
 *
 * Score 0-100:
 *   0-24   → Low      (green)
 *   25-49  → Medium   (yellow)
 *   50-74  → High     (orange)
 *   75-100 → Critical (red)
 *
 * Components shown on expand:
 *   • PERT schedule uncertainty (40 %)
 *   • Overdue task ratio (35 %)
 *   • Resource over-allocation (25 %)
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronUp, ShieldAlert, TrendingUp } from 'lucide-react'
import { api } from '../api/client'

// ── Types ─────────────────────────────────────────────────────────────────────

interface RiskComponents {
  pert_risk: number
  overdue_ratio: number
  resource_ratio: number
  overdue_tasks: number
  over_allocated_days: number
  // PERT details (optional — only present when PERT data exists)
  expected_duration?: number
  std_dev?: number
  cpm_duration?: number
  prob_on_time?: number
}

interface RiskMeta {
  total_tasks: number
  completed_tasks: number
  project_duration: number
}

interface RiskData {
  risk_score: number
  level: 'none' | 'low' | 'medium' | 'high' | 'critical'
  components: RiskComponents
  meta: RiskMeta
}

interface Props {
  projectId: number
  /** compact: show only the badge (no expand); full: show gauge + breakdown */
  variant?: 'compact' | 'full'
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const LEVEL_META = {
  none:     { label: 'N/A',      bg: 'bg-gray-100 dark:bg-gray-800',  text: 'text-gray-500', ring: '#94a3b8', fill: '#94a3b8' },
  low:      { label: 'Low',      bg: 'bg-green-50 dark:bg-green-950', text: 'text-green-700 dark:text-green-400', ring: '#22c55e', fill: '#22c55e' },
  medium:   { label: 'Medium',   bg: 'bg-yellow-50 dark:bg-yellow-950', text: 'text-yellow-700 dark:text-yellow-400', ring: '#eab308', fill: '#eab308' },
  high:     { label: 'High',     bg: 'bg-orange-50 dark:bg-orange-950', text: 'text-orange-700 dark:text-orange-400', ring: '#f97316', fill: '#f97316' },
  critical: { label: 'Critical', bg: 'bg-red-50 dark:bg-red-950',    text: 'text-red-700 dark:text-red-400',    ring: '#ef4444', fill: '#ef4444' },
}

/** SVG semicircle gauge (180°) */
function Gauge({ score, level }: { score: number; level: RiskData['level'] }) {
  const meta = LEVEL_META[level]
  const R = 52          // arc radius
  const CX = 64         // center x
  const CY = 68         // center y (slightly below mid so semicircle sits nicely)
  const strokeWidth = 10

  // Arc from 180° to 0° (left to right)
  const startAngle = Math.PI          // 180°
  const endAngle   = 0               // 0°
  const clampedScore = Math.max(0, Math.min(100, score))
  const sweepAngle = startAngle - (startAngle - endAngle) * (clampedScore / 100)

  const arcX = (angle: number) => CX + R * Math.cos(angle)
  const arcY = (angle: number) => CY - R * Math.sin(angle)

  // Background arc (full semicircle)
  const bgPath = `M ${arcX(startAngle)} ${arcY(startAngle)} A ${R} ${R} 0 0 1 ${arcX(endAngle)} ${arcY(endAngle)}`
  // Filled arc (score portion)
  const fillPath = `M ${arcX(startAngle)} ${arcY(startAngle)} A ${R} ${R} 0 0 1 ${arcX(sweepAngle)} ${arcY(sweepAngle)}`

  return (
    <svg viewBox="0 0 128 80" className="w-32 h-20">
      {/* track */}
      <path d={bgPath} fill="none" stroke="#e5e7eb" strokeWidth={strokeWidth} strokeLinecap="round"
            className="dark:stroke-gray-700" />
      {/* value arc */}
      <path d={fillPath} fill="none" stroke={meta.fill} strokeWidth={strokeWidth} strokeLinecap="round" />
      {/* score text */}
      <text x={CX} y={CY + 2} textAnchor="middle" dominantBaseline="middle"
            fontSize="22" fontWeight="700" fill={meta.fill}>
        {score}
      </text>
      {/* /100 label */}
      <text x={CX} y={CY + 18} textAnchor="middle" fontSize="9" fill="#9ca3af">/100</text>
    </svg>
  )
}

/** Horizontal bar showing component contribution */
function ComponentBar({ label, value, weight, color }: {
  label: string; value: number; weight: number; color: string
}) {
  const pct = Math.round(value * 100)
  const contribution = Math.round(value * weight * 100)
  return (
    <div className="space-y-0.5">
      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>{label}</span>
        <span className="font-mono">{pct}% <span className="text-gray-300 dark:text-gray-600">→ +{contribution}pts</span></span>
      </div>
      <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function RiskScoreWidget({ projectId, variant = 'full' }: Props) {
  const [expanded, setExpanded] = useState(false)

  const { data, isLoading } = useQuery<RiskData>({
    queryKey: ['risk-score', projectId],
    queryFn: () => api.get(`/projects/${projectId}/risk-score`).then(r => r.data),
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <ShieldAlert size={14} className="animate-pulse" />
        <span>Computing risk…</span>
      </div>
    )
  }

  if (!data || data.level === 'none') return null

  const meta = LEVEL_META[data.level]

  // ── Compact badge (for portfolio cards etc.) ──────────────────────────────
  if (variant === 'compact') {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${meta.bg} ${meta.text}`}>
        <ShieldAlert size={11} />
        Risk {data.risk_score}
        <span className="font-normal opacity-70">/ {meta.label}</span>
      </span>
    )
  }

  // ── Full widget ───────────────────────────────────────────────────────────
  const { components: c } = data
  const hasPert = c.prob_on_time !== undefined

  return (
    <div className={`rounded-xl border ${meta.bg} border-opacity-40 p-4 space-y-3`}
         style={{ borderColor: meta.ring + '44' }}>
      {/* Header row */}
      <div className="flex items-start gap-4">
        {/* Gauge */}
        <Gauge score={data.risk_score} level={data.level} />

        {/* Labels */}
        <div className="flex-1 pt-1 space-y-1.5">
          <div className="flex items-center gap-2">
            <ShieldAlert size={16} style={{ color: meta.ring }} />
            <span className={`text-sm font-semibold ${meta.text}`}>
              {meta.label} Risk
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 leading-snug">
            Composite score based on PERT schedule uncertainty, overdue tasks,
            and resource conflicts.
          </p>

          {/* Quick stats */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {c.overdue_tasks > 0 && (
              <span className="text-red-500">⚠ {c.overdue_tasks} overdue</span>
            )}
            {c.over_allocated_days > 0 && (
              <span className="text-orange-500">⊕ {c.over_allocated_days} conflict days</span>
            )}
            {hasPert && (
              <span className="text-gray-500">
                <TrendingUp size={11} className="inline mr-0.5" />
                {Math.round((c.prob_on_time ?? 0.5) * 100)}% on-time prob.
              </span>
            )}
          </div>
        </div>

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 mt-1"
          title="Show breakdown"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Expandable breakdown */}
      {expanded && (
        <div className="space-y-3 pt-2 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            Component breakdown
          </p>

          <ComponentBar
            label="PERT schedule uncertainty (40%)"
            value={c.pert_risk}
            weight={40}
            color="#818cf8"
          />
          <ComponentBar
            label="Overdue tasks (35%)"
            value={c.overdue_ratio}
            weight={35}
            color="#f87171"
          />
          <ComponentBar
            label="Resource conflicts (25%)"
            value={c.resource_ratio}
            weight={25}
            color="#fb923c"
          />

          {/* PERT detail */}
          {hasPert && (
            <div className="text-xs text-gray-400 space-y-0.5 pt-1">
              <div className="font-medium text-gray-500 dark:text-gray-300 mb-1">PERT details</div>
              <div className="grid grid-cols-2 gap-x-4">
                <span>Expected duration</span>
                <span className="font-mono text-gray-600 dark:text-gray-300">{c.expected_duration}d</span>
                <span>Std deviation (σ)</span>
                <span className="font-mono text-gray-600 dark:text-gray-300">±{c.std_dev}d</span>
                <span>CPM duration</span>
                <span className="font-mono text-gray-600 dark:text-gray-300">{c.cpm_duration}d</span>
                <span>P(finish on time)</span>
                <span className="font-mono text-gray-600 dark:text-gray-300">{Math.round((c.prob_on_time ?? 0) * 100)}%</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
