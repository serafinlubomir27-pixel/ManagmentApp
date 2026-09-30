/**
 * Skeleton — zástupné tvary počas načítavania.
 *
 * Nahrádzajú text „Načítavam…". Rozdiel nie je v rýchlosti, ale v tom, že
 * používateľ vidí, aký tvar obsahu príde, a stránka pri dokreslení neposkočí.
 * Má to význam najmä preto, že backend beží na bezplatnej úrovni a po nečinnosti
 * sa budí približne pol minúty.
 *
 * Animácia je pod `motion-safe`, takže sa vypne tým, kto má v systéme nastavené
 * obmedzenie pohybu.
 */
import clsx from 'clsx'

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={clsx(
        'motion-safe:animate-pulse rounded bg-gray-200/80 dark:bg-gray-800',
        className,
      )}
    />
  )
}

/** Obal, ktorý oznámi čítačkám obrazovky, že sa načítava. */
export function SkeletonBlock({ label = 'Načítava sa', children }: {
  label?: string
  children: React.ReactNode
}) {
  return (
    <div role="status" aria-label={label} aria-busy="true">
      {children}
    </div>
  )
}

/** Riadky tabuľky — `cols` musí sedieť s počtom stĺpcov, inak sa rozbije mriežka. */
export function SkeletonTableRows({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r}>
          {Array.from({ length: cols }).map((_, c) => (
            <td key={c} className="px-4 py-3.5">
              <Skeleton className={clsx('h-3.5', c === 0 ? 'w-44' : 'w-20')} />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}

/** Zoznam s ikonou vľavo a dvoma riadkami textu — projekty, klienti, tím. */
export function SkeletonList({ rows = 4, className }: { rows?: number; className?: string }) {
  return (
    <SkeletonBlock>
      <div className={clsx('divide-y divide-gray-100 dark:divide-gray-800', className)}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 px-5 py-4">
            <Skeleton className="w-10 h-10 rounded-xl flex-shrink-0" />
            <div className="flex-1 min-w-0 space-y-2">
              <Skeleton className="h-3.5 w-1/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-5 w-16 rounded-full flex-shrink-0" />
          </div>
        ))}
      </div>
    </SkeletonBlock>
  )
}

/** Karty so súhrnnými číslami. */
export function SkeletonCards({ count = 3 }: { count?: number }) {
  return (
    <SkeletonBlock>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="card p-5 flex items-center gap-4">
            <Skeleton className="w-11 h-11 rounded-xl flex-shrink-0" />
            <div className="space-y-2">
              <Skeleton className="h-6 w-10" />
              <Skeleton className="h-3 w-28" />
            </div>
          </div>
        ))}
      </div>
    </SkeletonBlock>
  )
}

/** Plocha pre graf — Gantt, burndown, sieťový diagram. */
export function SkeletonChart({ height = 'h-64' }: { height?: string }) {
  return (
    <SkeletonBlock>
      <div className="card p-5 space-y-3">
        <Skeleton className="h-3.5 w-40" />
        <Skeleton className={clsx('w-full', height)} />
      </div>
    </SkeletonBlock>
  )
}

/** Niekoľko riadkov textu rôznej dĺžky — komentáre, časová os. */
export function SkeletonLines({ rows = 3 }: { rows?: number }) {
  const widths = ['w-11/12', 'w-4/5', 'w-2/3', 'w-3/4', 'w-1/2']
  return (
    <SkeletonBlock>
      <div className="space-y-2.5 py-1">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className={clsx('h-3', widths[i % widths.length])} />
        ))}
      </div>
    </SkeletonBlock>
  )
}
