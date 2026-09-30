/**
 * ScheduleFields — úprava trvania úlohy a trojbodového odhadu.
 *
 * Je to samostatný komponent, lebo tie isté polia potrebuje tabuľka úloh aj
 * detail úlohy zo sieťového diagramu, a obe musia po zmene obnoviť rovnakú
 * sadu odvodených pohľadov (kritická cesta, PERT, rizikové skóre, zdroje).
 */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AlertCircle, Check } from 'lucide-react'
import { tasksApi } from '../api/client'
import { useScheduleRefresh } from '../hooks/useScheduleRefresh'

interface Props {
  taskId: number
  projectId: number
  duration: number
  optimistic?: number | null
  pessimistic?: number | null
  /** Trvanie mení harmonogram celého projektu — pre nemanažérov len na čítanie. */
  disabled?: boolean
}

type Field = 'duration' | 'duration_optimistic' | 'duration_pessimistic'

export default function ScheduleFields({
  taskId, projectId, duration, optimistic, pessimistic, disabled,
}: Props) {
  const refresh = useScheduleRefresh(projectId)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  // Lokálny stav, aby sa dalo písať; po príchode nových dát zo servera sa zrovná.
  const [draft, setDraft] = useState({
    duration: String(duration),
    duration_optimistic: optimistic != null ? String(optimistic) : '',
    duration_pessimistic: pessimistic != null ? String(pessimistic) : '',
  })

  useEffect(() => {
    setDraft({
      duration: String(duration),
      duration_optimistic: optimistic != null ? String(optimistic) : '',
      duration_pessimistic: pessimistic != null ? String(pessimistic) : '',
    })
  }, [duration, optimistic, pessimistic])

  const mutation = useMutation({
    mutationFn: (data: object) => tasksApi.update(taskId, data),
    onSuccess: () => {
      setError('')
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
      refresh(taskId)
    },
    onError: (e: any) => {
      // Server odmietol nezmyselnú kombináciu — vráť polia na uložený stav,
      // nech používateľ nevidí hodnotu, ktorá v databáze nie je.
      setError(e.response?.data?.detail ?? 'Nepodarilo sa uložiť')
      setDraft({
        duration: String(duration),
        duration_optimistic: optimistic != null ? String(optimistic) : '',
        duration_pessimistic: pessimistic != null ? String(pessimistic) : '',
      })
    },
  })

  const commit = (field: Field, raw: string) => {
    const stored = field === 'duration' ? duration
      : field === 'duration_optimistic' ? optimistic : pessimistic

    if (raw.trim() === '') {
      if (field === 'duration') {           // trvanie je povinné, nedá sa zmazať
        setDraft(d => ({ ...d, duration: String(duration) }))
        return
      }
      if (stored == null) return            // prázdne aj predtým — netreba nič
      mutation.mutate({ [field]: null })    // explicitné null = zmaž odhad
      return
    }

    const value = Number(raw)
    if (!Number.isInteger(value) || value === stored) {
      setDraft(d => ({ ...d, [field]: stored != null ? String(stored) : '' }))
      return
    }
    mutation.mutate({ [field]: value })
  }

  const cls = 'w-16 text-sm border border-gray-300 dark:border-gray-700 rounded-lg px-2 py-1 ' +
    'bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 ' +
    'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent ' +
    'disabled:opacity-60 disabled:cursor-not-allowed'

  const field = (name: Field, label: string, hint: string) => (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-500 dark:text-gray-400" title={hint}>{label}</span>
      <input
        type="number"
        min={1}
        className={cls}
        value={draft[name]}
        disabled={disabled || mutation.isPending}
        onChange={e => setDraft(d => ({ ...d, [name]: e.target.value }))}
        onBlur={e => commit(name, e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }}
      />
    </label>
  )

  return (
    <div className="space-y-2">
      <div className="flex items-end gap-4 flex-wrap">
        {field('duration', 'Trvanie (dni)', 'Najpravdepodobnejšie trvanie — vstupuje do kritickej cesty')}
        <span className="text-gray-300 dark:text-gray-700 pb-1.5">|</span>
        {field('duration_optimistic', 'Optimistický', 'Odhad a — najkratšie možné trvanie')}
        {field('duration_pessimistic', 'Pesimistický', 'Odhad b — najdlhšie možné trvanie')}

        {mutation.isPending && (
          <span className="text-xs text-gray-400 pb-1.5">Ukladám…</span>
        )}
        {saved && !mutation.isPending && (
          <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 pb-1.5">
            <Check size={12} /> Prepočítané
          </span>
        )}
      </div>

      {error && (
        <p className="flex items-center gap-1.5 text-xs text-red-500">
          <AlertCircle size={12} /> {error}
        </p>
      )}

      {!disabled && (
        <p className="text-xs text-gray-400">
          Zmena trvania prepočíta kritickú cestu, rezervy aj PERT celého projektu.
          Odhady nechaj prázdne, ak s nimi nepracuješ.
        </p>
      )}
    </div>
  )
}
