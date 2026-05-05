/**
 * AiParserModal — Natural language → CPM tasks generator
 * Opens as a modal dialog, shows AI-parsed task preview, confirms creation.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, X, ChevronRight, CheckCircle2, AlertCircle, Loader2, Wand2 } from 'lucide-react'
import { api } from '../api/client'

interface ParsedTask {
  name: string
  duration: number
  dependencies: string[]
  description: string
  priority: string
}

interface ParseResult {
  tasks: ParsedTask[]
  source: 'openai' | 'heuristic'
}

interface Props {
  projectId: number
  onClose: () => void
  onCreated: () => void
}

const PRIORITY_COLOR: Record<string, string> = {
  low:      'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  medium:   'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  high:     'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

const EXAMPLE_PROMPTS = [
  'Webový redesign: analýza požiadaviek 3d, wireframy 4d (závisí na analýze), UI dizajn 5d (závisí na wireframoch), frontend implementácia 10d (závisí na dizajne), testovanie 3d (závisí na implementácii), spustenie 1d',
  'Mobilná aplikácia: product discovery 5 dní, UX dizajn 7 dní, backend vývoj 14 dní, mobilný frontend 12 dní (závisí na dizajne a backende), QA testovanie 5 dní, release na AppStore 2 dni',
  'Marketing kampaň: briefing tímu, kreatívna tvorba obsahu 5 dní, grafický dizajn 3 dni, copy review, naplánovanie publikácie, spustenie kampane a monitoring výsledkov',
]

export default function AiParserModal({ projectId, onClose, onCreated }: Props) {
  const [description, setDescription] = useState('')
  const [preview, setPreview] = useState<ParseResult | null>(null)
  const [step, setStep] = useState<'input' | 'preview' | 'success'>('input')

  // Parse (dry run)
  const parseMutation = useMutation({
    mutationFn: () =>
      api.post('/ai/parse-project', { description }).then(r => r.data as ParseResult),
    onSuccess: (data) => {
      setPreview(data)
      setStep('preview')
    },
  })

  // Generate (create tasks in project)
  const generateMutation = useMutation({
    mutationFn: () =>
      api.post(`/projects/${projectId}/ai-generate`, { description }).then(r => r.data),
    onSuccess: () => {
      setStep('success')
      onCreated()
    },
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-surface-dark rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-brand-500 flex items-center justify-center">
              <Sparkles size={16} className="text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">AI Generátor úloh</h2>
              <p className="text-xs text-gray-400">Opíš projekt — AI vytvorí úlohy s CPM závislosťami</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">

          {/* ── Step 1: Input ─────────────────────────────────────────── */}
          {step === 'input' && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-2">
                  Popis projektu
                </label>
                <textarea
                  className="input resize-none text-sm"
                  rows={6}
                  placeholder="Napíš popis projektu — vrátane názvov fáz, trvania (napr. '5 dní') a závislostí..."
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                />
                <p className="text-xs text-gray-400 mt-1">{description.length}/4000 znakov</p>
              </div>

              {/* Examples */}
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Príklady:</p>
                <div className="space-y-2">
                  {EXAMPLE_PROMPTS.map((ex, i) => (
                    <button
                      key={i}
                      onClick={() => setDescription(ex)}
                      className="w-full text-left text-xs text-gray-500 dark:text-gray-400 px-3 py-2 rounded-lg border border-gray-100 dark:border-gray-800 hover:border-brand-300 dark:hover:border-brand-700 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
                    >
                      <ChevronRight size={10} className="inline mr-1" />
                      {ex.slice(0, 100)}…
                    </button>
                  ))}
                </div>
              </div>

              {parseMutation.isError && (
                <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">
                  <AlertCircle size={14} />
                  {(parseMutation.error as any)?.response?.data?.detail ?? 'Chyba pri parsovaní'}
                </div>
              )}
            </div>
          )}

          {/* ── Step 2: Preview ───────────────────────────────────────── */}
          {step === 'preview' && preview && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                {preview.source === 'openai' ? (
                  <span className="flex items-center gap-1.5 text-xs bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 px-2.5 py-1 rounded-full border border-purple-200 dark:border-purple-800">
                    <Sparkles size={10} /> GPT-4o-mini
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-2.5 py-1 rounded-full">
                    <Wand2 size={10} /> Heuristika (bez API kľúča)
                  </span>
                )}
                <span className="text-sm text-gray-500">{preview.tasks.length} úloh</span>
              </div>

              <div className="space-y-2">
                {preview.tasks.map((t, i) => (
                  <div key={i} className="border border-gray-100 dark:border-gray-800 rounded-xl p-3 space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-gray-900 dark:text-white">{t.name}</span>
                      <span className="text-xs text-gray-400 font-mono">{t.duration}d</span>
                      <span className={`badge text-xs ${PRIORITY_COLOR[t.priority] ?? PRIORITY_COLOR.medium}`}>
                        {t.priority}
                      </span>
                    </div>
                    {t.dependencies.length > 0 && (
                      <p className="text-xs text-gray-400">
                        Závisí na: <span className="text-blue-500">{t.dependencies.join(', ')}</span>
                      </p>
                    )}
                    {t.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t.description}</p>
                    )}
                  </div>
                ))}
              </div>

              {generateMutation.isError && (
                <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">
                  <AlertCircle size={14} />
                  {(generateMutation.error as any)?.response?.data?.detail ?? 'Chyba pri vytváraní'}
                </div>
              )}
            </div>
          )}

          {/* ── Step 3: Success ───────────────────────────────────────── */}
          {step === 'success' && (
            <div className="py-10 text-center space-y-3">
              <CheckCircle2 size={48} className="text-green-500 mx-auto" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Úlohy vytvorené!</h3>
              <p className="text-sm text-gray-500">CPM bol automaticky prepočítaný.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
          {step === 'input' && (
            <>
              <button onClick={onClose} className="btn-ghost text-sm">Zrušiť</button>
              <button
                onClick={() => parseMutation.mutate()}
                disabled={description.trim().length < 10 || parseMutation.isPending}
                className="btn-primary text-sm flex items-center gap-2"
              >
                {parseMutation.isPending
                  ? <><Loader2 size={14} className="animate-spin" /> Parsuje AI…</>
                  : <><Sparkles size={14} /> Analyzovať</>
                }
              </button>
            </>
          )}

          {step === 'preview' && (
            <>
              <button onClick={() => setStep('input')} className="btn-ghost text-sm">
                ← Upraviť popis
              </button>
              <button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending}
                className="btn-primary text-sm flex items-center gap-2"
              >
                {generateMutation.isPending
                  ? <><Loader2 size={14} className="animate-spin" /> Vytváram…</>
                  : <><CheckCircle2 size={14} /> Vytvoriť úlohy ({preview?.tasks.length})</>
                }
              </button>
            </>
          )}

          {step === 'success' && (
            <button onClick={onClose} className="btn-primary text-sm ml-auto">
              Zatvoriť
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
