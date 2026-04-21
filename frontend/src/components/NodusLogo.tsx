interface Props {
  variant?: 'icon' | 'wordmark'
  size?: number
}

export default function NodusLogo({ variant = 'icon', size = 32 }: Props) {
  const icon = (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Nodus logo"
    >
      <rect width="64" height="64" rx="16" fill="#0D1B4B"/>
      <circle cx="10" cy="32" r="5" fill="#4B7FFF"/>
      <circle cx="27" cy="18" r="5" fill="white"/>
      <circle cx="44" cy="18" r="5" fill="white"/>
      <circle cx="27" cy="46" r="5" fill="#4B7FFF" fillOpacity="0.5"/>
      <circle cx="54" cy="32" r="5" fill="#4B7FFF"/>
      <line x1="15" y1="29" x2="22" y2="21" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <line x1="32" y1="18" x2="39" y2="18" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <line x1="49" y1="21" x2="51" y2="27" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <line x1="15" y1="35" x2="22" y2="43" stroke="#4B7FFF" strokeWidth="1.5" strokeDasharray="3 2" strokeLinecap="round" opacity="0.7"/>
      <line x1="32" y1="46" x2="49" y2="37" stroke="#4B7FFF" strokeWidth="1.5" strokeDasharray="3 2" strokeLinecap="round" opacity="0.7"/>
      <circle cx="10" cy="32" r="8" fill="#4B7FFF" fillOpacity="0.2"/>
      <circle cx="54" cy="32" r="8" fill="#4B7FFF" fillOpacity="0.2"/>
    </svg>
  )

  if (variant === 'icon') {
    return icon
  }

  const fontSize = Math.round(size * 0.65)

  return (
    <div className="flex items-center gap-2" style={{ lineHeight: 1 }}>
      {icon}
      <span
        style={{
          fontSize,
          fontWeight: 800,
          letterSpacing: '-0.02em',
          lineHeight: 1,
        }}
      >
        <span style={{ color: '#4B7FFF' }}>N</span>
        <span className="text-gray-900 dark:text-white">odus</span>
      </span>
    </div>
  )
}
