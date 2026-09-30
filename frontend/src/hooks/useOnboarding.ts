import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '../api/client'

const KEY = 'nodus.onboarding.v1'

/** Prístup k localStorage musí zniesť súkromné okno aj zakázané úložisko. */
function seen(userId: number): boolean {
  try {
    return localStorage.getItem(`${KEY}.${userId}`) === 'done'
  } catch {
    return true   // radšej nič neukázať, než padnúť
  }
}

function markSeen(userId: number) {
  try {
    localStorage.setItem(`${KEY}.${userId}`, 'done')
  } catch {
    /* nevadí — uvedenie sa najbližšie ukáže znova */
  }
}

/**
 * Rozhodne, či ukázať uvedenie.
 *
 * Ukáže sa len tomu, kto ešte nemá ani jeden projekt. Kto sa prihlási na novom
 * zariadení a projekty už má, uvedenie nepotrebuje — len sa mu ticho odloží.
 */
export function useOnboarding(userId: number | undefined) {
  const [open, setOpen] = useState(false)

  const { data: projects, isSuccess } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list().then(r => r.data),
    enabled: userId !== undefined,
  })

  useEffect(() => {
    if (userId === undefined || !isSuccess) return
    if (seen(userId)) return

    if (projects && projects.length > 0) {
      markSeen(userId)      // skúsený používateľ na novom zariadení
      return
    }
    setOpen(true)
  }, [userId, isSuccess, projects])

  const close = () => {
    if (userId !== undefined) markSeen(userId)
    setOpen(false)
  }

  /** Na opätovné spustenie z Nastavení. */
  const reopen = () => setOpen(true)

  return { open, close, reopen }
}
