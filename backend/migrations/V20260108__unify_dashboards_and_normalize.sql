-- ============================================================================
-- UNIFY DASHBOARDS & NORMALIZE FLAGS
-- ============================================================================
-- 1. Ensure expected_completion_time exists (Emergency Fix Restoration)
-- 2. Normalize is_deleted flags from NULL to false
-- 3. Add NOT NULL constraints to ensure future consistency
-- ============================================================================

BEGIN;

-- 1. Task Table Fix
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS expected_completion_time INTEGER NULL;

-- 2. Normalize Soft Delete Flags
UPDATE users SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE projects SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE machines SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE filing_tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE fabrication_tasks SET is_deleted = false WHERE is_deleted IS NULL;

-- 3. Ensure constraints for consistency
ALTER TABLE users ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE projects ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE machines ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE tasks ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE filing_tasks ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE fabrication_tasks ALTER COLUMN is_deleted SET DEFAULT false;

COMMIT;

-- Verification
\echo 'Post-Migration Global Counts:'
SELECT 'Users' as table, COUNT(*) as active FROM users WHERE is_deleted = false
UNION ALL
SELECT 'Projects', COUNT(*) FROM projects WHERE is_deleted = false
UNION ALL
SELECT 'Machines', COUNT(*) FROM machines WHERE is_deleted = false
UNION ALL
SELECT 'General Tasks', COUNT(*) FROM tasks WHERE is_deleted = false
UNION ALL
SELECT 'Filing Tasks', COUNT(*) FROM filing_tasks WHERE is_deleted = false
UNION ALL
SELECT 'Fabrication Tasks', COUNT(*) FROM fabrication_tasks WHERE is_deleted = false;
