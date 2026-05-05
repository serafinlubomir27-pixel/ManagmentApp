-- Migration 004: calendar_tokens table for iCal feed
-- Each user can have one calendar token (UUID) for their personal iCal feed.
-- The token acts as authentication for the public .ics endpoint.

CREATE TABLE IF NOT EXISTS calendar_tokens (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT    NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calendar_tokens_token ON calendar_tokens(token);
CREATE INDEX IF NOT EXISTS idx_calendar_tokens_user  ON calendar_tokens(user_id);
