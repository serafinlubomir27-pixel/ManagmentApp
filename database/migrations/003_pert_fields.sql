-- Migration 003: Add PERT duration fields to tasks
-- PERT = Program Evaluation and Review Technique
-- a = optimistic, m = most likely (= existing duration), b = pessimistic

ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS duration_optimistic INTEGER CHECK (duration_optimistic >= 1),
  ADD COLUMN IF NOT EXISTS duration_pessimistic INTEGER CHECK (duration_pessimistic >= 1);

-- Index for PERT queries (tasks that have PERT data set)
CREATE INDEX IF NOT EXISTS idx_tasks_pert
  ON tasks(project_id)
  WHERE duration_optimistic IS NOT NULL OR duration_pessimistic IS NOT NULL;

COMMENT ON COLUMN tasks.duration_optimistic IS 'PERT optimistic estimate (a) in days';
COMMENT ON COLUMN tasks.duration_pessimistic IS 'PERT pessimistic estimate (b) in days';
COMMENT ON COLUMN tasks.duration IS 'Most likely duration (m) — also used as CPM duration';
