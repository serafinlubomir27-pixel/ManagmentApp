/**
 * GroupSuggestion — tichý tip, že projekt by sa už hodilo rozdeliť na etapy.
 *
 * Ukáže sa až nad hranicou, kde sa zoznam naozaj stáva neprehľadným. Pri
 * projekte so šiestimi úlohami by to bola otravná otázka. Dá sa odmietnuť
 * a späť sa nepýta — odmietnutie si pamätá prehliadač, lebo je to vec
 * konkrétneho človeka, nie projektu.
 */
import { Layers, X } from 'lucide-react'

interface Props {
  /** Koľko úloh nie je zaradených do žiadnej etapy. */
  ungrouped: number
  onDismiss: () => void
}

export default function GroupSuggestion({ ungrouped, onDismiss }: Props) {
  return (
    <div className="card p-4 flex items-start gap-3 animate-fade-up border-l-4 border-l-brand-500">
      <div className="w-9 h-9 rounded-control bg-brand-50 dark:bg-brand-500/10
                      flex items-center justify-center shrink-0">
        <Layers size={17} className="text-brand-500" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900 dark:text-white">
          Rozdeliť projekt na etapy?
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">
          Projekt má {ungrouped} nezaradených úloh. Označ tie, ktoré patria k sebe,
          a zlúč ich do etapy — zoznam sa dá potom zbaliť a hneď vidno, ako ďaleko
          jednotlivé etapy sú. Na výpočet kritickej cesty to nemá vplyv.
        </p>
      </div>

      <button
        onClick={onDismiss}
        className="p-1.5 rounded-control text-gray-400 hover:text-gray-700 dark:hover:text-gray-200
                   hover:bg-gray-100 dark:hover:bg-white/[0.06] transition duration-fast shrink-0"
        aria-label="Zavrieť tip"
      >
        <X size={15} />
      </button>
    </div>
  )
}
