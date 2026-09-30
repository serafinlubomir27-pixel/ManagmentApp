/**
 * EmptyState — prázdna obrazovka s vysvetlením a ďalším krokom.
 *
 * Doteraz väčšina miest napísala len sivé „Žiadne úlohy". To je pravdivé, ale
 * nepomôže — používateľ nevie, či je niečo rozbité, alebo len ešte nič nezaložil.
 * Preto ikona, veta o tom, čo sem patrí, a tam, kde to dáva zmysel, aj tlačidlo.
 */
import clsx from 'clsx'

interface Props {
  icon?: React.ReactNode
  title: string
  /** Jedna veta: čo sem patrí a prečo. Nie návod na dve obrazovky. */
  hint?: string
  /** Text tlačidla; bez `onAction` sa nevykreslí. */
  actionLabel?: string
  onAction?: () => void
  /** Vlastný obsah namiesto tlačidla — napr. odkaz na inú obrazovku. */
  action?: React.ReactNode
  /** `inline` pre bloky vnútri kariet, kde by plná výška vyzerala prehnane. */
  size?: 'inline' | 'full'
  className?: string
}

export default function EmptyState({
  icon, title, hint, actionLabel, onAction, action, size = 'full', className,
}: Props) {
  const full = size === 'full'

  return (
    <div className={clsx('text-center', full ? 'py-12 px-6' : 'py-6 px-4', className)}>
      {icon && (
        <div className={clsx(
          'mx-auto mb-3 flex items-center justify-center rounded-2xl',
          'bg-gray-100 dark:bg-gray-800/60 text-gray-400 dark:text-gray-500',
          full ? 'w-12 h-12' : 'w-9 h-9',
        )}>
          {icon}
        </div>
      )}

      <p className={clsx(
        'font-medium text-gray-700 dark:text-gray-300',
        full ? 'text-sm' : 'text-xs',
      )}>
        {title}
      </p>

      {hint && (
        <p className={clsx(
          'mx-auto mt-1 text-gray-400 dark:text-gray-500',
          full ? 'text-xs max-w-sm' : 'text-xs max-w-xs',
        )}>
          {hint}
        </p>
      )}

      {(action || (actionLabel && onAction)) && (
        <div className="mt-3">
          {action ?? (
            <button onClick={onAction} className="btn-primary text-xs py-1.5 px-3">
              {actionLabel}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
