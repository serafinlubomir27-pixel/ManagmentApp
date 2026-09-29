-- CRM rozšírenie klientskeho modulu.
--
-- Doterajší modul vedel, kto je klient, v akej fáze je obchod a čo treba doložiť
-- kvôli compliance. Nevedel však, čo sa s klientom dialo a čo sa má stať ďalej.
-- Tieto dve tabuľky dopĺňajú práve to: záznam interakcií a naplánované úlohy.
--
-- Spustiť: py database/migrate.py

-- ── História interakcií ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS client_activities (
    id              BIGSERIAL PRIMARY KEY,
    client_id       BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    activity_type   TEXT NOT NULL DEFAULT 'note',
    subject         TEXT NOT NULL DEFAULT '',
    body            TEXT NOT NULL DEFAULT '',
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_client_activities_client
    ON client_activities (client_id, occurred_at DESC);

-- ── Naplánované úlohy ku klientovi ───────────────────────────────────────────
-- Zámerne oddelené od tabuľky tasks: tá patrí projektom a vstupuje do výpočtu
-- kritickej cesty. Úloha ku klientovi nemá trvanie ani závislosti a do
-- harmonogramu projektu nepatrí.
CREATE TABLE IF NOT EXISTS client_tasks (
    id              BIGSERIAL PRIMARY KEY,
    client_id       BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    assigned_to     BIGINT REFERENCES users(id),
    created_by      BIGINT NOT NULL REFERENCES users(id),
    title           TEXT NOT NULL,
    due_date        DATE,
    priority        TEXT NOT NULL DEFAULT 'medium',
    done            BOOLEAN NOT NULL DEFAULT FALSE,
    done_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_client_tasks_client
    ON client_tasks (client_id, done, due_date);
CREATE INDEX IF NOT EXISTS idx_client_tasks_assignee
    ON client_tasks (assigned_to, done, due_date);

-- ── História posunov v obchode ───────────────────────────────────────────────
-- deal_stages drží iba aktuálnu fázu. Bez histórie sa nedá zistiť, ako dlho
-- obchod v ktorej fáze stál.
CREATE TABLE IF NOT EXISTS deal_stage_history (
    id              BIGSERIAL PRIMARY KEY,
    client_id       BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    from_stage      TEXT,
    to_stage        TEXT NOT NULL,
    changed_by      BIGINT NOT NULL REFERENCES users(id),
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_deal_stage_history_client
    ON deal_stage_history (client_id, changed_at DESC);
