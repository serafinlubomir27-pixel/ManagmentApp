/**
 * ComplianceChecklist — MiFID II / IDD compliance items per client.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Circle, AlertCircle, Plus } from 'lucide-react'
import { clientsApi } from '../api/client'

const ITEM_TYPES = [
  { value: 'kyc',               label: 'KYC — Poznaj svojho klienta' },
  { value: 'suitability',       label: 'Vhodnosť produktu (suitability)' },
  { value: 'aml',               label: 'AML — Proti praniu peňazí' },
  { value: 'id_document',       label: 'Overenie totožnosti' },
  { value: 'risk_questionnaire',label: 'Dotazník rizikového profilu' },
  { value: 'contract',          label: 'Zmluva podpísaná' },
  { value: 'mifid_disclosure',  label: 'MiFID II — Informačná povinnosť' },
  { value: 'other',             label: 'Iné' },
]

const TYPE_LABEL: Record<string, string> = Object.fromEntries(ITEM_TYPES.map(t => [t.value, t.label]))

interface Props { clientId: number }

export default function ComplianceChecklist({ clientId }: Props) {
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ item_type: 'kyc', due_date: '', notes: '' })

  const { data: items = [] } = useQuery({
    queryKey: ['compliance', clientId],
    queryFn: () => clientsApi.listCompliance(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const addMutation = useMutation({
    mutationFn: () => clientsApi.addCompliance(clientId, {
      item_type: form.item_type,
      due_date: form.due_date || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['compliance', clientId] })
      setShowAdd(false)
      setForm({ item_type: 'kyc', due_date: '', notes: '' })
    },
  })

  const completeMutation = useMutation({
    mutationFn: (itemId: number) =>
      clientsApi.updateCompliance(itemId, { status: 'complete' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['compliance', clientId] }),
  })

  const today = new Date().toISOString().slice(0, 10)

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="flex gap-3 text-xs">
        <span className="text-green-600 dark:text-green-400">✅ {(items as any[]).filter((i: any) => i.status === 'complete').length} splnených</span>
        <span className="text-amber-600 dark:text-amber-400">🟡 {(items as any[]).filter((i: any) => i.status === 'pending').length} čakajúcich</span>
      </div>

      {/* Item list */}
      <div className="space-y-2">
        {(items as any[]).map(item => {
          const isExpired = item.status === 'pending' && item.due_date && item.due_date < today
          return (
            <div key={item.id} className={`flex items-start gap-3 p-3 rounded-xl border transition-colors ${
              item.status === 'complete'
                ? 'bg-green-50 dark:bg-green-900/10 border-green-100 dark:border-green-900'
                : isExpired
                  ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900'
                  : 'bg-gray-50 dark:bg-gray-900/50 border-gray-100 dark:border-gray-800'
            }`}>
              <button
                onClick={() => item.status === 'pending' && completeMutation.mutate(item.id)}
                className="mt-0.5 flex-shrink-0"
              >
                {item.status === 'complete'
                  ? <CheckCircle2 size={18} className="text-green-500" />
                  : isExpired
                    ? <AlertCircle size={18} className="text-red-500" />
                    : <Circle size={18} className="text-gray-400 hover:text-brand-500" />
                }
              </button>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${item.status === 'complete' ? 'line-through text-gray-400' : 'text-gray-900 dark:text-white'}`}>
                  {TYPE_LABEL[item.item_type] ?? item.item_type}
                </p>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  {item.due_date && (
                    <span className={`text-xs ${isExpired ? 'text-red-500 font-medium' : 'text-gray-400'}`}>
                      Termín: {item.due_date}
                    </span>
                  )}
                  {item.notes && <span className="text-xs text-gray-400 italic">{item.notes}</span>}
                  {item.completed_at && (
                    <span className="text-xs text-green-600 dark:text-green-400">
                      Splnené: {item.completed_at.slice(0, 10)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
        {items.length === 0 && (
          <p className="text-xs text-gray-400 py-4 text-center">Žiadne compliance položky.</p>
        )}
      </div>

      {/* Add form */}
      {showAdd ? (
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 space-y-2">
          <select className="input text-sm" value={form.item_type} onChange={e => setForm({...form, item_type: e.target.value})}>
            {ITEM_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <input type="date" className="input text-sm" value={form.due_date} onChange={e => setForm({...form, due_date: e.target.value})} />
          <input className="input text-sm" placeholder="Poznámka" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          <div className="flex gap-2">
            <button onClick={() => addMutation.mutate()} disabled={addMutation.isPending} className="btn-primary text-xs py-1 px-3">
              {addMutation.isPending ? 'Pridávam…' : 'Pridať'}
            </button>
            <button onClick={() => setShowAdd(false)} className="btn-ghost text-xs py-1 px-3">Zrušiť</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)} className="flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 hover:underline">
          <Plus size={12} /> Pridať compliance položku
        </button>
      )}
    </div>
  )
}
