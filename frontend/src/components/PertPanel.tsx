/**
 * PertPanel — PERT analýza projektu
 * Zobrazuje pravdepodobnostné odhadovanie trvania projektu (a/m/b → E, σ, P).
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { TrendingUp, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react'

interface PertTask {
  task_id: number
  name: string
  duration_optimistic: number
  duration_likely: number
  duration_pessimistic: number
  pert_expected: number
  pert_std_dev: number
  pert_variance: number
  is_critical: boolean
}

interface PertResult {
  pert_tasks: PertTask[]
  critical_path_ids: number[]
  project_expected_duration: number
  project_std_dev: number
  project_variance: number
  probability_by_deadline: Record<string, number>
  cpm_duration: number
}

interface ProbGaugeProps {
  probability: number  // 0-1
}

function ProbGauge({ probability }: ProbGaugeProps) {
  const pct = Math.round(probability * 100)
  const r = 54
  const circumference = 2 * Math.PI * r
  const arc = circumference * 0.75  // 270° arc
  const offset = arc - (arc * probability)

  const color = pct >= 80 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444'
  const label = pct >= 80 ? 'Vysoká' : pct >= 50 ? 'Stredná' : 'Nízka'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="140" height="110" viewBox="0 0 140 110">
        {/* Background arc */}
        <circle
          cx="70" cy="80" r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="12"
          strokeDasharray={`${arc} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform="rotate(135 70 80)"
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Foreground arc */}
        <circle
          cx="70" cy="80" r={r}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={`${arc} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(135 70 80)"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        <text x="70" y="76" textAnchor="middle" fontSize="22" fontWeight="700" fill={color}>{pct}%</text>
        <text x="70" y="94" textAnchor="middle" fontSize="11" fill="currentColor" className="fill-gray-500">{label}</text>
      </svg>
      <p className="text-xs text-gray-500 dark:text-gray-400">pravdepodobnosť dokončenia</p>
    </div>
  )
}

interface Props {
  projectId: number
}

export default function PertPanel({ projectId }: Props) {
  const [deadline, setDeadline] = useState<number>(30)

  const { data, isLoading, error } = useQuery<PertResult>({
    queryKey: ['pert', projectId, deadline],
    queryFn: () => api.get(`/projects/${projectId}/pert?deadline=${deadline}`).then(r => r.data),
    staleTime: 30_000,
  })

  if (isLoading) {
    return <div className="py-12 text-center text-gray-400 text-sm">Počítam PERT analýzu…</div>
  }
  if (error || !data) {
    return <div className="py-12 text-center text-red-400 text-sm">Chyba pri načítaní PERT dát</div>
  }
  if (data.pert_tasks.length === 0) {
    return (
      <div className="py-12 text-center text-gray-400 text-sm">
        <TrendingUp size={32} className="mx-auto mb-3 opacity-30" />
        <p>Pridaj úlohy s PERT odhadmi (optimistický / pesimistický)</p>
      </div>
    )
  }

  const prob = data.probability_by_deadline[String(deadline)] ??
               data.probability_by_deadline[deadline] ?? 0

  const hasPertData = data.pert_tasks.some(t => t.duration_optimistic !== t.duration_likely || t.duration_pessimistic !== t.duration_likely)

  return (
    <div className="space-y-5">
      {/* PERT info banner if no tasks have a/b set */}
      {!hasPertData && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl px-4 py-3 flex items-start gap-2">
          <AlertTriangle size={15} className="text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-amber-700 dark:text-amber-400">
            Žiadna úloha nemá nastavené optimistické/pesimistické odhady.
            Pridaj ich pri vytváraní/editácii úlohy pre presnejšiu PERT analýzu.
            Aktuálne sa používa <code className="bg-amber-100 dark:bg-amber-900/40 px-1 rounded">a = m = b = trvanie</code>.
          </p>
        </div>
      )}

      {/* Top row: gauge + stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Gauge + deadline input */}
        <div className="card p-5 flex flex-col items-center gap-3">
          <ProbGauge probability={prob} />
          <div className="flex items-center gap-2 w-full max-w-xs">
            <label className="text-xs text-gray-500 whitespace-nowrap">Deadline (dni):</label>
            <input
              type="number"
              min={1}
              className="input text-sm flex-1"
              value={deadline}
              onChange={(e) => setDeadline(Number(e.target.value))}
            />
          </div>
        </div>

        {/* Project stats */}
        <div className="card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Projektu štatistiky</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500 flex items-center gap-1.5">
                <Clock size={13} /> CPM trvanie
              </span>
              <span className="font-mono text-sm font-medium text-gray-900 dark:text-white">
                {data.cpm_duration}d
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500 flex items-center gap-1.5">
                <TrendingUp size={13} /> PERT očakávané (E)
              </span>
              <span className="font-mono text-sm font-medium text-blue-600 dark:text-blue-400">
                {data.project_expected_duration}d
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">Štand. odchýlka (σ)</span>
              <span className="font-mono text-sm font-medium text-gray-700 dark:text-gray-300">
                ±{data.project_std_dev}d
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">90% interval</span>
              <span className="font-mono text-sm text-gray-600 dark:text-gray-400">
                {Math.max(0, Math.round(data.project_expected_duration - 1.645 * data.project_std_dev))}d — {Math.round(data.project_expected_duration + 1.645 * data.project_std_dev)}d
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Probability table */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Pravdepodobnosť dokončenia podľa termínu</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900/50">
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Deadline</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Pravdepodobnosť</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {Object.entries(data.probability_by_deadline)
                .map(([d, p]) => [Number(d), p] as [number, number])
                .sort((a, b) => a[0] - b[0])
                .map(([d, p]) => {
                  const pct = Math.round(p * 100)
                  return (
                    <tr key={d} className={d === deadline ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}>
                      <td className="px-4 py-2 font-mono font-medium text-gray-900 dark:text-white">
                        {d}d {d === deadline && <span className="text-blue-500 text-xs">← aktuálny</span>}
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 max-w-24">
                            <div
                              className={`h-1.5 rounded-full ${pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="font-mono text-xs text-gray-700 dark:text-gray-300">{pct}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-2">
                        {pct >= 80 ? (
                          <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-xs">
                            <CheckCircle2 size={12} /> Reálny termín
                          </span>
                        ) : pct >= 50 ? (
                          <span className="text-amber-600 dark:text-amber-400 text-xs">Rizikový termín</span>
                        ) : (
                          <span className="text-red-600 dark:text-red-400 text-xs">Nereálny termín</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      </div>

      {/* PERT tasks table */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">PERT odhady úloh</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900/50">
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Úloha</th>
                <th className="text-center px-3 py-2 text-xs font-medium text-gray-500">a (opt.)</th>
                <th className="text-center px-3 py-2 text-xs font-medium text-gray-500">m (pravd.)</th>
                <th className="text-center px-3 py-2 text-xs font-medium text-gray-500">b (pes.)</th>
                <th className="text-center px-3 py-2 text-xs font-medium text-blue-600 dark:text-blue-400">E</th>
                <th className="text-center px-3 py-2 text-xs font-medium text-gray-500">σ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {data.pert_tasks.map(t => (
                <tr key={t.task_id} className={t.is_critical ? 'bg-red-50/40 dark:bg-red-900/10' : ''}>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-1.5">
                      {t.is_critical && <span className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />}
                      <span className="font-medium text-gray-900 dark:text-white text-xs">{t.name}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-center font-mono text-xs text-green-700 dark:text-green-400">{t.duration_optimistic}d</td>
                  <td className="px-3 py-2 text-center font-mono text-xs text-gray-700 dark:text-gray-300">{t.duration_likely}d</td>
                  <td className="px-3 py-2 text-center font-mono text-xs text-red-700 dark:text-red-400">{t.duration_pessimistic}d</td>
                  <td className="px-3 py-2 text-center font-mono text-xs font-semibold text-blue-600 dark:text-blue-400">{t.pert_expected}d</td>
                  <td className="px-3 py-2 text-center font-mono text-xs text-gray-500">±{t.pert_std_dev}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
