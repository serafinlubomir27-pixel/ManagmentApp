-- ============================================================================
-- 006_missing_tables.sql  —  P0-4: doplnenie prod (Postgres/Supabase) schémy
-- ============================================================================
-- Tieto tabuľky a stĺpce existovali len v SQLite (database/setup.py), ale NIE
-- v Postgres schéme ani v migráciách 001–005. Na nasadenom Supabase preto celý
-- klientsky modul (Fáza 3), prílohy projektov (Fáza 1), time tracking a pozvánky
-- padali na "relation/column does not exist".
--
-- Idempotentné (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS). Bezpečné spustiť viackrát.
-- SPUSTI v Supabase Dashboard → SQL Editor (PO 005_enable_rls.sql alebo pred ním —
-- 005 je idempotentné a zachytí aj tieto nové tabuľky pri opätovnom spustení).
--
-- Pozn. k typom: `archived` je SMALLINT (nie BOOLEAN), lebo repozitáre porovnávajú
-- `WHERE archived = 0` / `SET archived = 1` — funguje rovnako na SQLite aj Postgrese.
-- ----------------------------------------------------------------------------

-- ── 1. time_logs (time tracking) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS time_logs (
    id         BIGSERIAL PRIMARY KEY,
    task_id    BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hours      NUMERIC(6,2) NOT NULL,
    log_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    note       TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_time_logs_task_id ON time_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_time_logs_user_id ON time_logs(user_id);

-- ── 2. invite_tokens (team invitations) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS invite_tokens (
    id         BIGSERIAL PRIMARY KEY,
    token      TEXT NOT NULL UNIQUE,
    role       user_role NOT NULL DEFAULT 'employee',
    created_by BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    used_by    BIGINT REFERENCES users(id) ON DELETE SET NULL,
    used_at    TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_invite_tokens_token   ON invite_tokens(token);
CREATE INDEX IF NOT EXISTS idx_invite_tokens_creator ON invite_tokens(created_by);

-- ── 3. project_attachments (Fáza 1 — prílohy na úrovni projektu) ────────────
CREATE TABLE IF NOT EXISTS project_attachments (
    id          BIGSERIAL PRIMARY KEY,
    project_id  BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name   TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    file_size   BIGINT,
    mime_type   TEXT,
    visibility  TEXT NOT NULL DEFAULT 'team',
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_project_attachments_project ON project_attachments(project_id);

-- ── 4. clients (Fáza 3 — register klientov pre finančných poradcov) ─────────
CREATE TABLE IF NOT EXISTS clients (
    id           BIGSERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT,
    phone        TEXT,
    category     TEXT NOT NULL DEFAULT 'retail',
    risk_profile TEXT NOT NULL DEFAULT 'balanced',
    advisor_id   BIGINT REFERENCES users(id) ON DELETE SET NULL,
    notes        TEXT,
    archived     SMALLINT NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_clients_advisor  ON clients(advisor_id);
CREATE INDEX IF NOT EXISTS idx_clients_archived ON clients(archived);

-- ── 5. client_meetings ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS client_meetings (
    id           BIGSERIAL PRIMARY KEY,
    client_id    BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meeting_date TEXT NOT NULL,
    notes        TEXT,
    follow_ups   TEXT,           -- JSON pole (json.dumps), preto TEXT nie JSONB
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_client_meetings_client ON client_meetings(client_id);

-- ── 6. compliance_items (MiFID II checklist) ────────────────────────────────
CREATE TABLE IF NOT EXISTS compliance_items (
    id             BIGSERIAL PRIMARY KEY,
    client_id      BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    item_type      TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
    due_date       TEXT,
    completed_by   BIGINT REFERENCES users(id) ON DELETE SET NULL,
    completed_at   TIMESTAMPTZ,
    document_path  TEXT,
    notes          TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_compliance_items_client ON compliance_items(client_id);

-- ── 7. deal_stages (obchodný pipeline) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS deal_stages (
    id                   BIGSERIAL PRIMARY KEY,
    client_id            BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    stage                TEXT NOT NULL DEFAULT 'lead',
    deal_value           NUMERIC(14,2),
    commission_expected  NUMERIC(14,2),
    commission_received  NUMERIC(14,2),
    currency             TEXT NOT NULL DEFAULT 'EUR',
    notes                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_deal_stages_client ON deal_stages(client_id);

-- ── Chýbajúce stĺpce v existujúcich tabuľkách ───────────────────────────────
-- (SQLite ich pridáva cez ALTER v setup.py; Postgres ich nemal.)

-- tasks: subscription flags (auto_notify / auto_calendar)
ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS auto_notify   BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS auto_calendar BOOLEAN NOT NULL DEFAULT TRUE;

-- users: profilové polia (čítané v /auth/me, zapisované v /auth/me/profile)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS bio          TEXT,
    ADD COLUMN IF NOT EXISTS avatar_color TEXT DEFAULT '#6366f1',
    ADD COLUMN IF NOT EXISTS timezone     TEXT DEFAULT 'Europe/Bratislava';

-- projects: default subscription flags + väzba na klienta (Fáza 3)
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS default_auto_notify   BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS default_auto_calendar BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS client_id BIGINT REFERENCES clients(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_projects_client_id ON projects(client_id);

-- task_attachments: viditeľnosť príloh (Fáza 1)
ALTER TABLE task_attachments
    ADD COLUMN IF NOT EXISTS visibility TEXT NOT NULL DEFAULT 'team';

-- ── Overenie (spusti samostatne — malo by vrátiť 7 nových tabuliek) ─────────
--   SELECT tablename FROM pg_tables WHERE schemaname='public'
--     AND tablename IN ('time_logs','invite_tokens','project_attachments',
--                       'clients','client_meetings','compliance_items','deal_stages')
--   ORDER BY tablename;
