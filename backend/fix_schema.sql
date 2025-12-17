-- CRITICAL: Fix expected_completion_time column type
-- This resolves the "invalid input syntax for type timestamp: 100" error.

BEGIN;

-- 1. Drop the incorrect TIMESTAMP column (if exists)
ALTER TABLE tasks DROP COLUMN IF EXISTS expected_completion_time;

-- 2. Add the correct INTEGER column (minutes)
ALTER TABLE tasks ADD COLUMN expected_completion_time INTEGER;

-- 3. Ensure other critical columns exist and are correct types
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS project_id INTEGER;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;

COMMIT;
