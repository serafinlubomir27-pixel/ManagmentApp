-- ============================================================================
-- 008_email_and_resets.sql  —  M2: e-mailová identita + reset hesla
-- ============================================================================
-- Self-signup potrebuje globálne unikátnu identitu a spôsob resetu hesla.
-- Riešenie: e-mail ako login identita (username ostáva ako display / legacy).
-- Existujúci používatelia majú email = NULL a prihlasujú sa naďalej cez username;
-- noví (signup / pozvánka) dostanú e-mail a vedia si resetnúť heslo.
--
-- Idempotentné. SPUSTI v Supabase SQL Editore PO 007_multi_tenancy.sql.
-- ----------------------------------------------------------------------------

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email TEXT;

-- E-mail unikátny len keď je vyplnený (viaceré NULL sú OK).
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
    ON users(email) WHERE email IS NOT NULL;

CREATE TABLE IF NOT EXISTS password_resets (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '1 hour'),
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);
