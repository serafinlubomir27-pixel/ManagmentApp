/**
 * PipelineKanban — stage selector + financial fields for a single client's deal.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { clientsApi } from '../api/client'

const STAGES = [
  { key: 'lead',     label: 'Potenciálny',  color: 'bg-gray-100 dark:bg-gray-800' },
  { key: 'contact',  label: 'Prvý kontakt', color: 'bg-blue-50 dark:bg-blue-900/20' },
  { key: 'analysis', label: 'Analýza',      color: 'bg-indigo-50 dark:bg-indigo-900/20' },
  { key: 'proposal', label: 'Návrh',        color: 'bg-purple-50 dark:bg-purple-900/20' },
  { key: 'signed',   label: 'Podpis',       color: 'bg-green-50 dark:bg-green-900/20' },
  { key: 'active',   label: 'Aktívny',      color: 'bg-emerald-50 dark:bg-emerald-900/20' },
  { key: 'lost',     label: 'Stratený',     color: 'bg-red-50 dark:bg-red-900/20' },
]

interface Props {
  clientId: number
  deal: {
    stage: string
    deal_value?: number | null
    commission_expected?: number | null
    commission_received?: number | null
    currency?: string
    notes?: string | null
  } | null
}

export default function PipelineKanban({ clientId, deal }: Props) {
  const qc = useQueryClient()
  const currentStage = deal?.stage ?? 'lead'

  const moveMutation = useMutation({
    mutationFn: (stage: string) =>
      clientsApi.updatePipeline(clientId, {
        stage,
        deal_value: deal?.deal_value,
        commission_expected: deal?.commission_expected,
        commission_received: deal?.commission_received,
        currency: deal?.currency ?? 'EUR',
        notes: deal?.notes,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['client', clientId] }),
  })

  const currentIdx = STAGES.findIndex(s => s.key === currentStage)

  const updateFinancials = (field: string, val: number | null) => {
    clientsApi.updatePipeline(clientId, {
      stage: currentStage,
      deal_value: field === 'deal_value' ? val : deal?.deal_value,
      commission_expected: field === 'commission_expected' ? val : deal?.commission_expected,
      commission_received: field === 'commission_received' ? val : deal?.commission_received,
      currency: deal?.currency ?? 'EUR',
      notes: deal?.notes,
    }).then(() => qc.invalidateQueries({ queryKey: ['client', clientId] }))
  }

  return (
    <div className="space-y-4">
      {/* Stage selector */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {STAGES.map((s, idx) => (
          <button
            key={s.key}
            onClick={() => moveMutation.mutate(s.key)}
            disabled={moveMutation.isPending}
            className={`flex-shrink-0 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
              s.key === currentStage
                ? `${s.color} ring-2 ring-brand-400 text-gray-900 dark:text-white`
                : idx < currentIdx
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 opacity-70'
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            {idx < currentIdx ? '✓ ' : ''}{s.label}
          </button>
        ))}
      </div>

      {/* Financials */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label: 'Hodnota dealu', field: 'deal_value', value: deal?.deal_value },
          { label: 'Očakávaná provízia', field: 'commission_expected', value: deal?.commission_expected },
          { label: 'Prijatá provízia', field: 'commission_received', value: deal?.commission_received },
        ].map(item => (
          <div key={item.field} className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3">
            <p className="text-xs text-gray-400 mb-1">{item.label}</p>
            <input
              type="number"
              className="input text-sm font-mono"
              defaultValue={item.value ?? ''}
              placeholder="0"
              onBlur={e => {
                const val = e.target.value ? Number(e.target.value) : null
                updateFinancials(item.field, val)
              }}
            />
            <span className="text-xs text-gray-400">{deal?.currency ?? 'EUR'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
