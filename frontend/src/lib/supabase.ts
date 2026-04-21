import { createClient } from '@supabase/supabase-js'

// Supabase Realtime client — používa sa LEN pre WebSocket subscriptions
// (CRUD operácie stále idú cez náš FastAPI backend)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL ?? ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ?? ''

export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey, {
      realtime: {
        params: { eventsPerSecond: 10 },
      },
    })
  : null

// Helper: je Realtime dostupné?
export const isRealtimeEnabled = () => !!supabase
