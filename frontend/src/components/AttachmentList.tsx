/**
 * AttachmentList — reusable list of file attachments with visibility badges.
 * Used in AttachmentSidebar (project files) and TaskDetailModal (task files).
 */
import { Trash2, FileText, FileSpreadsheet, Image, File } from 'lucide-react'
import { VisibilityBadge } from './VisibilitySelector'

export interface AttachmentItem {
  id: number
  file_name: string
  file_path: string
  file_size?: number | null
  visibility: 'team' | 'managers' | 'private'
  uploaded_at: string
  uploaded_by_username: string
  task_name?: string   // only for unified view
}

interface Props {
  attachments: AttachmentItem[]
  onDelete?: (id: number) => void
  onVisibilityChange?: (id: number, v: 'team' | 'managers' | 'private') => void
  showTaskTag?: boolean
}

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return <Image size={14} />
  if (['xls', 'xlsx', 'csv'].includes(ext)) return <FileSpreadsheet size={14} />
  if (['doc', 'docx', 'pdf', 'txt'].includes(ext)) return <FileText size={14} />
  return <File size={14} />
}

function formatBytes(bytes?: number | null): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

export default function AttachmentList({ attachments, onDelete, onVisibilityChange, showTaskTag }: Props) {
  if (attachments.length === 0) {
    return <p className="text-xs text-gray-400 py-2">Žiadne prílohy</p>
  }

  return (
    <div className="space-y-1">
      {attachments.map(att => (
        <div key={att.id} className="flex items-center gap-2 group p-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50">
          <span className="text-gray-400 flex-shrink-0">{fileIcon(att.file_name)}</span>
          <a
            href={att.file_path}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 dark:text-brand-400 hover:underline truncate flex-1 min-w-0"
            title={att.file_name}
          >
            {att.file_name}
          </a>
          {showTaskTag && att.task_name && (
            <span className="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded flex-shrink-0">
              {att.task_name}
            </span>
          )}
          {formatBytes(att.file_size) && (
            <span className="text-xs text-gray-400 flex-shrink-0">{formatBytes(att.file_size)}</span>
          )}
          <VisibilityBadge
            value={att.visibility}
            onClick={onVisibilityChange ? () => {
              const order: Array<'team' | 'managers' | 'private'> = ['team', 'managers', 'private']
              const next = order[(order.indexOf(att.visibility) + 1) % 3]
              onVisibilityChange(att.id, next)
            } : undefined}
          />
          {onDelete && (
            <button
              onClick={() => onDelete(att.id)}
              className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-gray-300 hover:text-red-500 transition-all flex-shrink-0"
              title="Zmazať"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
