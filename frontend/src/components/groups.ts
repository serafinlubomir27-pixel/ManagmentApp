/**
 * Etapy — spoločné typy a farby.
 *
 * Databáza drží len názov farby, nie hex. Vzhľad sa rieši tu, takže zmena
 * palety neznamená prepisovanie údajov.
 */

export interface TaskGroup {
  id: number
  project_id: number
  name: string
  color: GroupColor
  sort_order: number
  total_tasks: number
  completed_tasks: number
  critical_tasks: number
  progress: number
  done: boolean
  start_day: number | null
  end_day: number | null
}

export type GroupColor = 'brand' | 'violet' | 'emerald' | 'amber' | 'rose' | 'cyan'

export const GROUP_COLORS: GroupColor[] = ['brand', 'violet', 'emerald', 'amber', 'rose', 'cyan']

/** Trieda pre farebný prúžok vľavo od etapy a pre bodku pri úlohe. */
export const groupAccent: Record<GroupColor, string> = {
  brand:   'bg-brand-500',
  violet:  'bg-violet-500',
  emerald: 'bg-emerald-500',
  amber:   'bg-amber-500',
  rose:    'bg-rose-500',
  cyan:    'bg-cyan-500',
}

/** Jemné pozadie hlavičky etapy. */
export const groupTint: Record<GroupColor, string> = {
  brand:   'bg-brand-50 dark:bg-brand-500/10',
  violet:  'bg-violet-50 dark:bg-violet-500/10',
  emerald: 'bg-emerald-50 dark:bg-emerald-500/10',
  amber:   'bg-amber-50 dark:bg-amber-500/10',
  rose:    'bg-rose-50 dark:bg-rose-500/10',
  cyan:    'bg-cyan-50 dark:bg-cyan-500/10',
}

/** Hex pre SVG (sieťový diagram) — Tailwind triedy sa tam nedajú použiť na výplň oblasti. */
export const groupHex: Record<GroupColor, string> = {
  brand:   '#4B7FFF',
  violet:  '#8b5cf6',
  emerald: '#10b981',
  amber:   '#f59e0b',
  rose:    '#f43f5e',
  cyan:    '#06b6d4',
}

/** Slovenčina skloňuje podľa počtu: 1 úloha, 2–4 úlohy, 5+ úloh. */
export function taskCount(n: number): string {
  if (n === 1) return '1 úloha'
  if (n >= 2 && n <= 4) return `${n} úlohy`
  return `${n} úloh`
}

/** Aj prídavné meno sa musí zhodovať: 1 vybraná, 2–4 vybrané, 5+ vybraných. */
export function selectedCount(n: number): { count: string; adjective: string } {
  if (n === 1) return { count: '1 úloha', adjective: 'vybraná' }
  if (n >= 2 && n <= 4) return { count: `${n} úlohy`, adjective: 'vybrané' }
  return { count: `${n} úloh`, adjective: 'vybraných' }
}
