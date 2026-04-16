-- ManagmentApp — PostgreSQL / Supabase Schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New query)
-- Safe to run multiple times (uses IF NOT EXISTS / CREATE OR REPLACE).

-- ============================================================
-- ENUM types
-- ============================================================

DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('admin', 'manager', 'employee');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE project_status AS ENUM ('active', 'completed', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'blocked');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE dep_type AS ENUM ('finish_to_start', 'start_to_start', 'finish_to_finish');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================
-- TABLES
-- ============================================================

-- 1. users
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,          -- SHA-256 hex (64 chars)
    full_name   TEXT,
    role        user_role NOT NULL DEFAULT 'employee',
    manager_id  BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. projects
CREATE TABLE IF NOT EXISTS projects (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    status      project_status NOT NULL DEFAULT 'active',
    is_template BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. tasks
CREATE TABLE IF NOT EXISTS tasks (
    id              BIGSERIAL PRIMARY KEY,
    project_id      BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    description     TEXT,
    status          task_status NOT NULL DEFAULT 'pending',
    assigned_to     BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_by      BIGINT REFERENCES users(id) ON DELETE SET NULL,
    due_date        DATE,
    priority        task_priority NOT NULL DEFAULT 'medium',
    estimated_hours NUMERIC(6,2),
    duration        INTEGER NOT NULL DEFAULT 1 CHECK (duration >= 1),
    delay_days      INTEGER NOT NULL DEFAULT 0 CHECK (delay_days >= 0),
    es              INTEGER NOT NULL DEFAULT 0,
    ef              INTEGER NOT NULL DEFAULT 0,
    ls              INTEGER NOT NULL DEFAULT 0,
    lf              INTEGER NOT NULL DEFAULT 0,
    total_float     INTEGER NOT NULL DEFAULT 0,
    is_critical     BOOLEAN NOT NULL DEFAULT FALSE,
    category        TEXT NOT NULL DEFAULT 'Other',
    notes           TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. task_dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    id                  BIGSERIAL PRIMARY KEY,
    task_id             BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id  BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    type                dep_type NOT NULL DEFAULT 'finish_to_start',
    UNIQUE(task_id, depends_on_task_id)
);

-- 5. task_comments
CREATE TABLE IF NOT EXISTS task_comments (
    id         BIGSERIAL PRIMARY KEY,
    task_id    BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. task_attachments
CREATE TABLE IF NOT EXISTS task_attachments (
    id          BIGSERIAL PRIMARY KEY,
    task_id     BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    file_name   TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    uploaded_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. activity_logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id         BIGSERIAL PRIMARY KEY,
    task_id    BIGINT REFERENCES tasks(id) ON DELETE SET NULL,
    user_id    BIGINT REFERENCES users(id) ON DELETE SET NULL,
    user_name  TEXT,
    action     TEXT,
    old_value  TEXT,
    new_value  TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES (performance)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_tasks_project_id   ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to  ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status       ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date     ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_projects_user_id   ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status    ON projects(status);
CREATE INDEX IF NOT EXISTS idx_users_manager_id   ON users(manager_id);
CREATE INDEX IF NOT EXISTS idx_comments_task_id   ON task_comments(task_id);
CREATE INDEX IF NOT EXISTS idx_deps_task_id       ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_logs_task_id       ON activity_logs(task_id);

-- ============================================================
-- SEED: default admin user (password: admin123)
-- SHA-256("admin123") = 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a
-- ============================================================

INSERT INTO users (username, password, full_name, role)
VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a', 'Hlavný Admin', 'admin')
ON CONFLICT (username) DO NOTHING;
