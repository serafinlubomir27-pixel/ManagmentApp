import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, Send, MessageSquare } from 'lucide-react'
import { commentsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

interface Comment {
  id: number
  task_id: number
  user_id: number
  author_name: string
  content: string
  created_at: string
}

interface Props {
  taskId: number
}

function timeAgo(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diffMs = now - then
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return 'práve teraz'
  if (diffMin < 60) return `pred ${diffMin} min`
  if (diffHour < 24) return `pred ${diffHour} hod`
  if (diffDay === 1) return 'včera'
  return `pred ${diffDay} dňami`
}

function initials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export default function CommentSection({ taskId }: Props) {
  const qc = useQueryClient()
  const { user } = useAuth()
  const [text, setText] = useState('')

  const { data: comments = [], isLoading } = useQuery<Comment[]>({
    queryKey: ['comments', taskId],
    queryFn: () => commentsApi.list(taskId).then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (content: string) => commentsApi.create(taskId, content),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['comments', taskId] })
      setText('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (commentId: number) => commentsApi.delete(commentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['comments', taskId] }),
  })

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!trimmed || createMutation.isPending) return
    createMutation.mutate(trimmed)
  }

  return (
    <div className="space-y-3 pt-3 border-t border-gray-100 dark:border-gray-800">
      {/* Header */}
      <div className="flex items-center gap-2">
        <MessageSquare size={15} className="text-gray-400" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Komentáre {comments.length > 0 && `(${comments.length})`}
        </span>
      </div>

      {/* Comment list */}
      {isLoading ? (
        <p className="text-xs text-gray-400 py-2">Načítavam…</p>
      ) : comments.length === 0 ? (
        <p className="text-xs text-gray-400 py-2 italic">
          Zatiaľ žiadne komentáre. Buď prvý!
        </p>
      ) : (
        <div className="space-y-3">
          {comments.map((c) => (
            <div key={c.id} className="flex gap-2.5">
              {/* Avatar */}
              <div className="w-7 h-7 rounded-full bg-brand-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5">
                {initials(c.author_name || '?')}
              </div>
              {/* Bubble */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                    {c.author_name}
                  </span>
                  <span className="text-xs text-gray-400">{timeAgo(c.created_at)}</span>
                </div>
                <div className="flex items-start gap-1.5 group">
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed flex-1 break-words">
                    {c.content}
                  </p>
                  {/* Delete — only for own comments */}
                  {user && c.user_id === user.id && (
                    <button
                      onClick={() => deleteMutation.mutate(c.id)}
                      disabled={deleteMutation.isPending}
                      className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0"
                      title="Zmazať komentár"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Input form */}
      <div className="flex gap-2 pt-1">
        <textarea
          className="input flex-1 resize-none text-sm py-2 min-h-[36px] max-h-28"
          placeholder="Napíš komentár…"
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit()
            }
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || createMutation.isPending}
          className="btn-primary px-3 flex items-center gap-1.5 text-sm self-end disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={14} />
        </button>
      </div>
      {createMutation.isError && (
        <p className="text-xs text-red-500">Nepodarilo sa odoslať komentár.</p>
      )}
    </div>
  )
}
