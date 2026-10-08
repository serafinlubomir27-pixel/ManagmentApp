-- Zoskupovanie úloh do etáp.
--
-- Pri projekte s dvadsiatimi úlohami sa v zozname stratí aj ten, kto ho písal.
-- Skupina je priečinok: manažér označí úlohy, pomenuje etapu a môže ju zbaliť.
--
-- DÔLEŽITÉ: skupina NEVSTUPUJE do výpočtu kritickej cesty. CPM ďalej pracuje
-- výhradne s jednotlivými úlohami a ich závislosťami. Skupina nemá vlastné
-- trvanie ani väzby — jej postup a rozsah sa odvodzujú z detí pri čítaní.
-- Keby skupina vystupovala ako jeden uzol, výpočet by prestal byť správny.
--
-- Spustiť: py database/migrate.py

CREATE TABLE IF NOT EXISTS task_groups (
    id          BIGSERIAL PRIMARY KEY,
    project_id  BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    -- Farba sa prideľuje automaticky z palety, aby sa etapy dali rozlíšiť
    -- v zozname, v Gante aj v sieťovom diagrame.
    color       TEXT NOT NULL DEFAULT 'brand',
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_task_groups_project
    ON task_groups (project_id, sort_order);

-- Úloha patrí najviac do jednej skupiny. Zrušenie skupiny úlohy nemaže —
-- ON DELETE SET NULL ich len vráti medzi nezaradené.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS group_id BIGINT
    REFERENCES task_groups(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tasks_group ON tasks (group_id);
