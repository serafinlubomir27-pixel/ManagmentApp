/**
 * MeetingLog — chronological list of client meetings with add form.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, Plus, Trash2 } from 'lucide-react'
import { clientsApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

interface Props { clientId: number }

export default function MeetingLog({ clientId }: Props) {
  const qc = useQueryClient()
  const { user } = useAuth()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ meeting_date: new Date().toISOString().slice(0, 10), notes: '', follow_ups: '' })

  const { data: meetings = [] } = useQuery({
    queryKey: ['meetings', clientId],
    queryFn: () => clientsApi.listMeetings(clientId).then(r => r.data),
    staleTime: 30_000,
  })

  const addMutation = useMutation({
    mutationFn: () => clientsApi.addMeeting(clientId, {
      meeting_date: form.meeting_date,
      notes: form.notes,
      follow_ups: form.follow_ups
        ? form.follow_ups.split('\n').map(s => s.trim()).filter(Boolean)
        : [],
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['meetings', clientId] })
      setShowForm(false)
      setForm({ meeting_date: new Date().toISOString().slice(0, 10), notes: '', follow_ups: '' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (meetingId: number) => clientsApi.deleteMeeting(clientId, meetingId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['meetings', clientId] }),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {(meetings as any[]).length} stretnutí
        </span>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 hover:underline">
          <Plus size={12} /> Zaznamenať stretnutie
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 space-y-2">
          <input type="date" className="input text-sm" value={form.meeting_date} onChange={e => setForm({...form, meeting_date: e.target.value})} />
          <textarea className="input text-sm w-full resize-none" rows={3} placeholder="Zápisnica…" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          <textarea className="input text-sm w-full resize-none" rows={2} placeholder="Follow-up akcie (každá na novom riadku)" value={form.follow_ups} onChange={e => setForm({...form, follow_ups: e.target.value})} />
          <div className="flex gap-2">
            <button onClick={() => addMutation.mutate()} disabled={addMutation.isPending} className="btn-primary text-xs py-1 px-3">
              {addMutation.isPending ? 'Ukladám…' : 'Uložiť'}
            </button>
            <button onClick={() => setShowForm(false)} className="btn-ghost text-xs py-1 px-3">Zrušiť</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {(meetings as any[]).length === 0 && !showForm && (
          <p className="text-xs text-gray-400 py-4 text-center">Žiadne stretnutia.</p>
        )}
        {(meetings as any[]).map(m => {
          const followUps: string[] = (() => { try { return JSON.parse(m.follow_ups || '[]') } catch { return [] } })()
          return (
            <div key={m.id} className="card p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar size={14} className="text-brand-500" />
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">{m.meeting_date}</span>
                  <span className="text-xs text-gray-400">@{m.username}</span>
                </div>
                {m.user_id === user?.id && (
                  <button onClick={() => deleteMutation.mutate(m.id)} className="p-0.5 rounded text-gray-300 hover:text-red-500 transition-colors">
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
              {m.notes && <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{m.notes}</p>}
              {followUps.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Follow-up akcie:</p>
                  <ul className="space-y-0.5">
                    {followUps.map((f: string, i: number) => (
                      <li key={i} className="text-xs text-gray-600 dark:text-gray-400 flex items-start gap-1.5">
                        <span className="text-brand-400 mt-0.5">→</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
