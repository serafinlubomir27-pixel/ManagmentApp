/**
 * OnboardingModal — krátke uvedenie pri prvom prihlásení.
 *
 * Tri kroky, nie prehliadka rozhrania. Zmysel je vysvetliť, čím sa Nodus líši
 * od nástrojov, ktoré Ganttov diagram len nakreslia, a dať človeku možnosť
 * pozrieť si hotový výpočet bez toho, aby najprv naťukal šesť úloh.
 *
 * Že bolo uvedenie zobrazené, si pamätá prehliadač. Je to drobnosť pre pohodlie
 * — na inom zariadení sa ukáže znova a nič sa tým nepokazí.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { X, Route, Network, TrendingUp, ArrowRight, ArrowLeft } from 'lucide-react'
import { projectsApi } from '../api/client'

const STEPS = [
  {
    icon: Route,
    title: 'Vieš, ktoré úlohy rozhodujú o termíne?',
    body: 'Väčšina nástrojov ti nakreslí Ganttov diagram a tým to končí. Nodus ide ďalej — '
      + 'spočíta kritickú cestu, teda reťaz úloh, kde každý deň meškania posunie celý projekt.',
  },
  {
    icon: Network,
    title: 'Stačia úlohy a závislosti medzi nimi',
    body: 'Pri úlohe zadáš trvanie a určíš, na čom závisí. Zvyšok dopočíta Nodus sám: '
      + 'najskoršie a najneskoršie termíny, časové rezervy a to, ktoré úlohy rezervu nemajú. '
      + 'Po každej zmene trvania sa prepočíta celý harmonogram.',
  },
  {
    icon: TrendingUp,
    title: 'A keď si trvaním nie si istý',
    body: 'Doplň k úlohe optimistický a pesimistický odhad. Metóda PERT z nich spočíta '
      + 'očakávané trvanie a pravdepodobnosť, že termín stihneš — namiesto jedného čísla, '
      + 'ktoré vyzerá presnejšie, než v skutočnosti je.',
  },
]

interface Props {
  onClose: () => void
}

export default function OnboardingModal({ onClose }: Props) {
  const [step, setStep] = useState(0)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const qc = useQueryClient()

  const last = step === STEPS.length - 1
  const { icon: Icon, title, body } = STEPS[step]

  const createDemo = async () => {
    setCreating(true)
    setError('')
    try {
      const { data } = await projectsApi.createDemo()
      qc.invalidateQueries({ queryKey: ['projects'] })
      onClose()
      navigate(`/projects/${data.id}`)
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Ukážkový projekt sa nepodarilo vytvoriť.')
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
         role="dialog" aria-modal="true" aria-label="Uvedenie do Nodusu">
      <div className="bg-white dark:bg-surface-dark rounded-2xl w-full max-w-md shadow-xl">
        <div className="flex justify-end pt-3 pr-3">
          <button
            onClick={onClose}
            aria-label="Zavrieť uvedenie"
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-7 pb-6 -mt-2">
          <div className="w-11 h-11 rounded-xl bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center mb-4">
            <Icon size={20} className="text-brand-500" />
          </div>

          <h2 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h2>
          <p className="mt-2 text-sm leading-relaxed text-gray-500 dark:text-gray-400">{body}</p>

          {error && <p className="mt-3 text-xs text-red-500">{error}</p>}

          <div className="mt-6 flex items-center justify-between">
            <div className="flex gap-1.5" aria-hidden>
              {STEPS.map((_, i) => (
                <span
                  key={i}
                  className={`h-1.5 rounded-full transition-all ${
                    i === step ? 'w-5 bg-brand-500' : 'w-1.5 bg-gray-200 dark:bg-gray-700'
                  }`}
                />
              ))}
            </div>

            <div className="flex items-center gap-2">
              {step > 0 && (
                <button onClick={() => setStep(s => s - 1)} className="btn-ghost text-sm py-1.5 px-3">
                  <ArrowLeft size={14} className="inline -mt-0.5 mr-1" />Späť
                </button>
              )}
              {!last ? (
                <button onClick={() => setStep(s => s + 1)} className="btn-primary text-sm py-1.5 px-3">
                  Ďalej<ArrowRight size={14} className="inline -mt-0.5 ml-1" />
                </button>
              ) : (
                <button onClick={createDemo} disabled={creating}
                        className="btn-primary text-sm py-1.5 px-3 disabled:opacity-60">
                  {creating ? 'Pripravujem…' : 'Ukáž mi to na príklade'}
                </button>
              )}
            </div>
          </div>

          {last && !creating && (
            <button onClick={onClose}
                    className="mt-3 w-full text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              Ďakujem, začnem od seba
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
