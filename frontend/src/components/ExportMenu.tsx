/**
 * ExportMenu — stiahnutie projektu ako PDF report, CSV alebo Excel.
 */
import { useEffect, useRef, useState } from 'react'
import { Download, FileText, FileSpreadsheet, Table2, Loader2 } from 'lucide-react'
import { exportApi, ExportFormat } from '../api/client'

interface Props {
  projectId: number
  projectName: string
}

const OPTIONS: Array<{ format: ExportFormat; label: string; hint: string; icon: React.ReactNode }> = [
  {
    format: 'pdf',
    label: 'PDF report',
    hint: 'Súhrn, Ganttov diagram a kritická cesta',
    icon: <FileText size={15} className="text-red-500" />,
  },
  {
    format: 'xlsx',
    label: 'Excel (.xlsx)',
    hint: 'Úlohy s filtrami + hárok súhrnu',
    icon: <FileSpreadsheet size={15} className="text-green-600" />,
  },
  {
    format: 'csv',
    label: 'CSV',
    hint: 'Surové dáta pre ďalšie spracovanie',
    icon: <Table2 size={15} className="text-blue-500" />,
  },
]

/** Chybová odpoveď pri `responseType: 'blob'` príde ako Blob, nie ako JSON. */
async function readError(err: any): Promise<string> {
  const data = err?.response?.data
  if (data instanceof Blob) {
    try {
      const parsed = JSON.parse(await data.text())
      if (parsed?.detail) return parsed.detail
    } catch { /* nebol JSON */ }
  }
  return data?.detail ?? 'Export zlyhal. Skús to znova.'
}

export default function ExportMenu({ projectId, projectName }: Props) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState<ExportFormat | null>(null)
  const [error, setError] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const handle = async (format: ExportFormat) => {
    setBusy(format)
    setError('')
    try {
      await exportApi.download(projectId, format, projectName)
      setOpen(false)
    } catch (err) {
      setError(await readError(err))
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        title="Exportovať projekt"
        className="btn-ghost flex items-center gap-2 text-sm border border-gray-200 dark:border-gray-700"
      >
        <Download size={14} /> Export
      </button>

      {open && (
        <div className="absolute right-0 mt-1.5 w-64 bg-white dark:bg-surface-dark border border-gray-100 dark:border-gray-800 rounded-xl shadow-lg z-20 overflow-hidden">
          {OPTIONS.map(opt => (
            <button
              key={opt.format}
              onClick={() => handle(opt.format)}
              disabled={busy !== null}
              className="w-full flex items-start gap-3 px-3 py-2.5 text-left hover:bg-gray-50 dark:hover:bg-gray-800/60 disabled:opacity-50 transition-colors"
            >
              <span className="mt-0.5 flex-shrink-0">
                {busy === opt.format
                  ? <Loader2 size={15} className="animate-spin text-gray-400" />
                  : opt.icon}
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-medium text-gray-900 dark:text-white">{opt.label}</span>
                <span className="block text-xs text-gray-400">{opt.hint}</span>
              </span>
            </button>
          ))}

          {error && (
            <p className="px-3 py-2 text-xs text-red-500 border-t border-gray-100 dark:border-gray-800">
              {error}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
