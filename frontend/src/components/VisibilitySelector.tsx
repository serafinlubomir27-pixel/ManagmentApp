/**
 * VisibilitySelector — three-level visibility picker for file attachments.
 * Values: 'team' | 'managers' | 'private'
 */
interface Props {
  value: 'team' | 'managers' | 'private'
  onChange: (v: 'team' | 'managers' | 'private') => void
  className?: string
}

const OPTIONS = [
  { value: 'team' as const,     label: '👥 Celý tím',     desc: 'Všetci v projekte' },
  { value: 'managers' as const, label: '👔 Manažéri',     desc: 'Admin + manažér' },
  { value: 'private' as const,  label: '🔒 Len ja',       desc: 'Súkromné' },
]

const BADGE: Record<string, string> = {
  team:     'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  managers: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  private:  'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
}

export function VisibilityBadge({ value, onClick }: { value: string; onClick?: () => void }) {
  const opt = OPTIONS.find(o => o.value === value) ?? OPTIONS[0]
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-opacity ${BADGE[value]} ${onClick ? 'cursor-pointer hover:opacity-80' : 'cursor-default'}`}
      title={opt.desc}
    >
      {opt.label}
    </button>
  )
}

export default function VisibilitySelector({ value, onChange, className = '' }: Props) {
  return (
    <div className={`flex gap-1 flex-wrap ${className}`}>
      {OPTIONS.map(opt => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          title={opt.desc}
          className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
            value === opt.value
              ? `${BADGE[opt.value]} border-current`
              : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:border-gray-300'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
