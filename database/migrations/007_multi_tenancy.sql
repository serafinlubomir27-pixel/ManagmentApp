-- ============================================================================
-- 007_multi_tenancy.sql  —  M1: multi-tenancy (izolácia organizácií)
-- ============================================================================
-- Aplikácia bola single-tenant: jedna spoločná tabuľka používateľov, admin videl
-- všetko, projekty boli scopované len vlastníkom. Dve firmy nemohli bezpečne
-- používať jedno nasadenie.
--
-- Model: `organizations` je koreň. organization_id nesú tri koreňové entity —
-- users, projects, clients (+ invite_tokens, aby pozvánka pridávala do správnej org).
-- Zvyšok (tasks, comments, attachments, time_logs, deals…) dedí príslušnosť cez FK
-- na project/client/task, takže sa ich netreba dotýkať.
--
-- Izolácia sa vynucuje v aplikačnej vrstve — backend/deps.py (assert_* helpery).
--
-- Idempotentné. SPUSTI v Supabase SQL Editore PO 006_missing_tables.sql.
-- Po tejto migrácii spusti (znova) 005_enable_rls.sql, nech RLS pokryje aj `organizations`.
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS organizations (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    slug       TEXT UNIQUE NOT NULL,
    plan       TEXT NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── organization_id na koreňových entitách ──────────────────────────────────
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE invite_tokens
    ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE CASCADE;

-- ── Backfill: existujúce dáta spadnú do jednej "Default" organizácie ────────
INSERT INTO organizations (name, slug, plan)
SELECT 'Default', 'default', 'free'
WHERE NOT EXISTS (SELECT 1 FROM organizations);

UPDATE users         SET organization_id = (SELECT id FROM organizations ORDER BY id LIMIT 1) WHERE organization_id IS NULL;
UPDATE projects      SET organization_id = (SELECT id FROM organizations ORDER BY id LIMIT 1) WHERE organization_id IS NULL;
UPDATE clients       SET organization_id = (SELECT id FROM organizations ORDER BY id LIMIT 1) WHERE organization_id IS NULL;
UPDATE invite_tokens SET organization_id = (SELECT id FROM organizations ORDER BY id LIMIT 1) WHERE organization_id IS NULL;

-- ── Indexy (každý dopyt bude filtrovať podľa organizácie) ───────────────────
CREATE INDEX IF NOT EXISTS idx_users_org    ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_clients_org  ON clients(organization_id);
CREATE INDEX IF NOT EXISTS idx_invites_org  ON invite_tokens(organization_id);

-- ── Overenie (spusti samostatne — nemalo by vrátiť žiadny riadok) ──────────
--   SELECT 'users' t, count(*) FROM users WHERE organization_id IS NULL
--   UNION ALL SELECT 'projects', count(*) FROM projects WHERE organization_id IS NULL
--   UNION ALL SELECT 'clients',  count(*) FROM clients  WHERE organization_id IS NULL;
