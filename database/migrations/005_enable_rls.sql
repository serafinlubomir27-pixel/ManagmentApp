-- ============================================================================
-- 005_enable_rls.sql  —  P0-3: Row Level Security na Supabase
-- ============================================================================
-- Problém: tabuľky nemali RLS a frontend nesie Supabase anon key. Bez RLS vie
-- ktokoľvek s anon key čítať a zapisovať do VŠETKÝCH tabuliek priamo cez Supabase
-- PostgREST / Realtime — úplne mimo FastAPI autorizácie.
--
-- Riešenie: zapnúť RLS na všetkých tabuľkách v schéme public a odobrať priame
-- práva rolám `anon` a `authenticated`. Žiadne policies = žiaden priamy prístup
-- pre tieto role (deny-all). Backend sa pripája ako rola `postgres` (owner), ktorá
-- RLS obchádza, takže FastAPI funguje ďalej bez zmeny.
--
-- Idempotentné — dá sa spustiť opakovane (aj po pridaní nových tabuliek v P0-4).
-- SPUSTI v Supabase Dashboard → SQL Editor.
-- ----------------------------------------------------------------------------

DO $$
DECLARE
    r RECORD;
    has_anon boolean := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon');
    has_auth boolean := EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated');
BEGIN
    FOR r IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', r.tablename);
        IF has_anon THEN
            EXECUTE format('REVOKE ALL ON public.%I FROM anon;', r.tablename);
        END IF;
        IF has_auth THEN
            EXECUTE format('REVOKE ALL ON public.%I FROM authenticated;', r.tablename);
        END IF;
    END LOOP;
END $$;

-- ── Overenie (nepovinné — spusti samostatne, mala by vrátiť rowsecurity = true) ──
--   SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- ── Dôsledok na Realtime ─────────────────────────────────────────────────────
-- Supabase Realtime (postgres_changes) prestane doručovať zmeny anon klientovi
-- (nemá SELECT policy). Frontend to znesie — hook `useRealtimeProject` je no-op
-- keď supabase klient nie je nakonfigurovaný a ignoruje CHANNEL_ERROR. V aktuálnom
-- produkčnom builde navyše VITE_SUPABASE_ANON_KEY nie je nastavený, takže Realtime
-- je aj tak vypnutý → táto migrácia nemá žiadny dopad na súčasnú produkciu.
-- Živú cross-client synchronizáciu vieme neskôr vrátiť cez Supabase Auth JWT
-- + per-user RLS policies, alebo backend-relayed WebSocket (P1 follow-up).
