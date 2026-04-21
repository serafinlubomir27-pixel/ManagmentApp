import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { supabase, isRealtimeEnabled } from '../lib/supabase'

/**
 * Subscribuje sa na Supabase Realtime zmeny pre daný projekt.
 * Keď sa zmení tasks/comments tabuľka → invaliduje TanStack Query cache
 * → UI sa automaticky refreshne bez reload.
 *
 * Fallback: ak VITE_SUPABASE_URL nie je nastavené, tichý no-op.
 */
export function useRealtimeProject(projectId: number | null) {
  const queryClient = useQueryClient()
  const channelRef = useRef<ReturnType<NonNullable<typeof supabase>['channel']> | null>(null)

  useEffect(() => {
    if (!projectId || !isRealtimeEnabled() || !supabase) return

    const channelName = `project-${projectId}`

    // Cleanup predchádzajúceho kanálu
    if (channelRef.current) {
      supabase.removeChannel(channelRef.current)
    }

    const channel = supabase
      .channel(channelName)
      // Sleduj zmeny v tasks kde project_id = projectId
      .on(
        'postgres_changes',
        {
          event: '*', // INSERT, UPDATE, DELETE
          schema: 'public',
          table: 'tasks',
          filter: `project_id=eq.${projectId}`,
        },
        (payload) => {
          console.log('[Realtime] tasks change:', payload.eventType)
          // Invaliduj queries pre tento projekt
          queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
          queryClient.invalidateQueries({ queryKey: ['project', projectId] })
        }
      )
      // Sleduj zmeny v komentároch (ak task patrí tomuto projektu)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'comments',
        },
        (payload) => {
          console.log('[Realtime] comments change:', payload.eventType)
          // Invaliduj komentáre — nevieme presne ktorú task, invalidujeme všetky
          queryClient.invalidateQueries({ queryKey: ['comments'] })
        }
      )
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log(`[Realtime] Subscribed to ${channelName}`)
        }
      })

    channelRef.current = channel

    return () => {
      if (supabase && channelRef.current) {
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
      }
    }
  }, [projectId, queryClient])
}

/**
 * Globálny hook — subscribuje na notifikácie pre aktuálneho usera.
 * Používa sa v Layout.tsx.
 */
export function useRealtimeNotifications(userId: number | null) {
  const queryClient = useQueryClient()
  const channelRef = useRef<ReturnType<NonNullable<typeof supabase>['channel']> | null>(null)

  useEffect(() => {
    if (!userId || !isRealtimeEnabled() || !supabase) return

    if (channelRef.current) {
      supabase.removeChannel(channelRef.current)
    }

    const channel = supabase
      .channel(`notifications-user-${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log('[Realtime] New notification:', payload.new)
          queryClient.invalidateQueries({ queryKey: ['notifications'] })
        }
      )
      .subscribe()

    channelRef.current = channel

    return () => {
      if (supabase && channelRef.current) {
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
      }
    }
  }, [userId, queryClient])
}
