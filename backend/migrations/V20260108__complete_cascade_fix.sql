-- ============================================================================
-- PRODUCTION FIX: Complete Database Consistency & Cascade Strategy
-- ============================================================================
-- Purpose: Fix ALL foreign key relationships, implement CASCADE deletes,
--          eliminate orphaned records, ensure DB is single source of truth
-- Strategy: Hard delete with CASCADE (Option A - Preferred)
-- Safety: Controlled cleanup with verification queries
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: AUDIT CURRENT FOREIGN KEYS
-- ============================================================================
\echo '========================================='
\echo 'STEP 1: Auditing current foreign keys...'
\echo '========================================='

-- List all foreign keys for review
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- STEP 2: DROP EXISTING FOREIGN KEYS (To rebuild with CASCADE)
-- ============================================================================
\echo '========================================='
\echo 'STEP 2: Dropping existing foreign keys...'
\echo '========================================='

-- Tasks table foreign keys
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_machine_id_fkey CASCADE;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_project_id_fkey CASCADE;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_assigned_to_fkey CASCADE;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_assigned_by_fkey CASCADE;

-- Filing tasks foreign keys
ALTER TABLE filing_tasks DROP CONSTRAINT IF EXISTS filing_tasks_project_id_fkey CASCADE;
ALTER TABLE filing_tasks DROP CONSTRAINT IF EXISTS filing_tasks_machine_id_fkey CASCADE;
ALTER TABLE filing_tasks DROP CONSTRAINT IF EXISTS filing_tasks_assigned_by_fkey CASCADE;

-- Fabrication tasks foreign keys
ALTER TABLE fabrication_tasks DROP CONSTRAINT IF EXISTS fabrication_tasks_project_id_fkey CASCADE;
ALTER TABLE fabrication_tasks DROP CONSTRAINT IF EXISTS fabrication_tasks_machine_id_fkey CASCADE;
ALTER TABLE fabrication_tasks DROP CONSTRAINT IF EXISTS fabrication_tasks_assigned_by_fkey CASCADE;

-- Subtasks foreign key
ALTER TABLE subtasks DROP CONSTRAINT IF EXISTS subtasks_task_id_fkey CASCADE;

-- Task holds foreign key
ALTER TABLE task_holds DROP CONSTRAINT IF EXISTS task_holds_task_id_fkey CASCADE;
ALTER TABLE task_holds DROP CONSTRAINT IF EXISTS task_holds_user_id_fkey CASCADE;

-- Task time logs foreign key
ALTER TABLE task_time_logs DROP CONSTRAINT IF EXISTS task_time_logs_task_id_fkey CASCADE;

-- Reschedule requests foreign key
ALTER TABLE reschedule_requests DROP CONSTRAINT IF EXISTS reschedule_requests_task_id_fkey CASCADE;
ALTER TABLE reschedule_requests DROP CONSTRAINT IF EXISTS reschedule_requests_requested_by_fkey CASCADE;

-- Machine runtime logs foreign keys
ALTER TABLE machine_runtime_logs DROP CONSTRAINT IF EXISTS machine_runtime_logs_machine_id_fkey CASCADE;
ALTER TABLE machine_runtime_logs DROP CONSTRAINT IF EXISTS machine_runtime_logs_task_id_fkey CASCADE;

-- User work logs foreign keys
ALTER TABLE user_work_logs DROP CONSTRAINT IF EXISTS user_work_logs_user_id_fkey CASCADE;
ALTER TABLE user_work_logs DROP CONSTRAINT IF EXISTS user_work_logs_task_id_fkey CASCADE;
ALTER TABLE user_work_logs DROP CONSTRAINT IF EXISTS user_work_logs_machine_id_fkey CASCADE;

-- Attendance foreign key
ALTER TABLE attendance DROP CONSTRAINT IF EXISTS attendance_user_id_fkey CASCADE;

-- User machines foreign keys
ALTER TABLE user_machines DROP CONSTRAINT IF EXISTS user_machines_user_id_fkey CASCADE;
ALTER TABLE user_machines DROP CONSTRAINT IF EXISTS user_machines_machine_id_fkey CASCADE;

-- Planning tasks foreign key
ALTER TABLE planning_tasks DROP CONSTRAINT IF EXISTS planning_tasks_task_id_fkey CASCADE;

-- Outsource items foreign key
ALTER TABLE outsource_items DROP CONSTRAINT IF EXISTS outsource_items_task_id_fkey CASCADE;

-- ============================================================================
-- STEP 3: RECREATE FOREIGN KEYS WITH CASCADE DELETE
-- ============================================================================
\echo '========================================='
\echo 'STEP 3: Creating CASCADE foreign keys...'
\echo '========================================='

-- Tasks table foreign keys (CASCADE on project/machine delete, SET NULL on user delete)
ALTER TABLE tasks 
    ADD CONSTRAINT tasks_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(project_id) 
    ON DELETE CASCADE;

ALTER TABLE tasks 
    ADD CONSTRAINT tasks_machine_id_fkey 
    FOREIGN KEY (machine_id) REFERENCES machines(id) 
    ON DELETE SET NULL;

-- Note: assigned_to can be manual text, so no FK constraint
-- Note: assigned_by should preserve history, so SET NULL
ALTER TABLE tasks 
    ADD CONSTRAINT tasks_assigned_by_fkey 
    FOREIGN KEY (assigned_by) REFERENCES users(user_id) 
    ON DELETE SET NULL;

-- Filing tasks foreign keys
ALTER TABLE filing_tasks 
    ADD CONSTRAINT filing_tasks_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(project_id) 
    ON DELETE CASCADE;

ALTER TABLE filing_tasks 
    ADD CONSTRAINT filing_tasks_machine_id_fkey 
    FOREIGN KEY (machine_id) REFERENCES machines(id) 
    ON DELETE SET NULL;

ALTER TABLE filing_tasks 
    ADD CONSTRAINT filing_tasks_assigned_by_fkey 
    FOREIGN KEY (assigned_by) REFERENCES users(user_id) 
    ON DELETE SET NULL;

-- Fabrication tasks foreign keys
ALTER TABLE fabrication_tasks 
    ADD CONSTRAINT fabrication_tasks_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(project_id) 
    ON DELETE CASCADE;

ALTER TABLE fabrication_tasks 
    ADD CONSTRAINT fabrication_tasks_machine_id_fkey 
    FOREIGN KEY (machine_id) REFERENCES machines(id) 
    ON DELETE SET NULL;

ALTER TABLE fabrication_tasks 
    ADD CONSTRAINT fabrication_tasks_assigned_by_fkey 
    FOREIGN KEY (assigned_by) REFERENCES users(user_id) 
    ON DELETE SET NULL;

-- Subtasks (CASCADE when parent task deleted)
ALTER TABLE subtasks 
    ADD CONSTRAINT subtasks_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE CASCADE;

-- Task holds (CASCADE when task deleted)
ALTER TABLE task_holds 
    ADD CONSTRAINT task_holds_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE CASCADE;

ALTER TABLE task_holds 
    ADD CONSTRAINT task_holds_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(user_id) 
    ON DELETE CASCADE;

-- Task time logs (CASCADE when task deleted)
ALTER TABLE task_time_logs 
    ADD CONSTRAINT task_time_logs_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE CASCADE;

-- Reschedule requests (CASCADE when task deleted)
ALTER TABLE reschedule_requests 
    ADD CONSTRAINT reschedule_requests_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE CASCADE;

ALTER TABLE reschedule_requests 
    ADD CONSTRAINT reschedule_requests_requested_by_fkey 
    FOREIGN KEY (requested_by) REFERENCES users(user_id) 
    ON DELETE CASCADE;

-- Machine runtime logs (CASCADE when task deleted, SET NULL when machine deleted)
ALTER TABLE machine_runtime_logs 
    ADD CONSTRAINT machine_runtime_logs_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE CASCADE;

ALTER TABLE machine_runtime_logs 
    ADD CONSTRAINT machine_runtime_logs_machine_id_fkey 
    FOREIGN KEY (machine_id) REFERENCES machines(id) 
    ON DELETE SET NULL;

-- User work logs (CASCADE when task/user deleted, SET NULL when machine deleted)
ALTER TABLE user_work_logs 
    ADD CONSTRAINT user_work_logs_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE CASCADE;

ALTER TABLE user_work_logs 
    ADD CONSTRAINT user_work_logs_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(user_id) 
    ON DELETE CASCADE;

ALTER TABLE user_work_logs 
    ADD CONSTRAINT user_work_logs_machine_id_fkey 
    FOREIGN KEY (machine_id) REFERENCES machines(id) 
    ON DELETE SET NULL;

-- Attendance (CASCADE when user deleted)
ALTER TABLE attendance 
    ADD CONSTRAINT attendance_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(user_id) 
    ON DELETE CASCADE;

-- User machines (CASCADE when user or machine deleted)
ALTER TABLE user_machines 
    ADD CONSTRAINT user_machines_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(user_id) 
    ON DELETE CASCADE;

ALTER TABLE user_machines 
    ADD CONSTRAINT user_machines_machine_id_fkey 
    FOREIGN KEY (machine_id) REFERENCES machines(id) 
    ON DELETE CASCADE;

-- Planning tasks (CASCADE when task deleted)
ALTER TABLE planning_tasks 
    ADD CONSTRAINT planning_tasks_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE CASCADE;

-- Outsource items (SET NULL when task deleted to preserve history)
ALTER TABLE outsource_items 
    ADD CONSTRAINT outsource_items_task_id_fkey 
    FOREIGN KEY (task_id) REFERENCES tasks(id) 
    ON DELETE SET NULL;

-- ============================================================================
-- STEP 4: NORMALIZE SOFT DELETE FLAGS (NULL → false)
-- ============================================================================
\echo '========================================='
\echo 'STEP 4: Normalizing soft delete flags...'
\echo '========================================='

UPDATE users SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE projects SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE machines SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE filing_tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE fabrication_tasks SET is_deleted = false WHERE is_deleted IS NULL;

-- Set NOT NULL constraints
ALTER TABLE users ALTER COLUMN is_deleted SET NOT NULL;
ALTER TABLE users ALTER COLUMN is_deleted SET DEFAULT false;

ALTER TABLE projects ALTER COLUMN is_deleted SET NOT NULL;
ALTER TABLE projects ALTER COLUMN is_deleted SET DEFAULT false;

ALTER TABLE machines ALTER COLUMN is_deleted SET NOT NULL;
ALTER TABLE machines ALTER COLUMN is_deleted SET DEFAULT false;

ALTER TABLE tasks ALTER COLUMN is_deleted SET NOT NULL;
ALTER TABLE tasks ALTER COLUMN is_deleted SET DEFAULT false;

ALTER TABLE filing_tasks ALTER COLUMN is_deleted SET NOT NULL;
ALTER TABLE filing_tasks ALTER COLUMN is_deleted SET DEFAULT false;

ALTER TABLE fabrication_tasks ALTER COLUMN is_deleted SET NOT NULL;
ALTER TABLE fabrication_tasks ALTER COLUMN is_deleted SET DEFAULT false;

-- ============================================================================
-- STEP 5: CLEAN UP ORPHANED RECORDS
-- ============================================================================
\echo '========================================='
\echo 'STEP 5: Cleaning orphaned records...'
\echo '========================================='

-- Find and report orphaned tasks (for manual review before cleanup)
CREATE TEMP TABLE orphaned_tasks_temp AS
SELECT id, 'tasks' AS source_table, project_id, assigned_to, machine_id
FROM tasks
WHERE (project_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM projects WHERE project_id = tasks.project_id))
   OR (machine_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM machines WHERE id = tasks.machine_id));

CREATE TEMP TABLE orphaned_filing_temp AS
SELECT id, 'filing_tasks' AS source_table, project_id, assigned_to, machine_id
FROM filing_tasks
WHERE (project_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM projects WHERE project_id = filing_tasks.project_id))
   OR (machine_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM machines WHERE id = filing_tasks.machine_id));

CREATE TEMP TABLE orphaned_fabrication_temp AS
SELECT id, 'fabrication_tasks' AS source_table, project_id, assigned_to, machine_id
FROM fabrication_tasks
WHERE (project_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM projects WHERE project_id = fabrication_tasks.project_id))
   OR (machine_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM machines WHERE id = fabrication_tasks.machine_id));

-- Report orphaned records
\echo 'Orphaned tasks found:'
SELECT source_table, COUNT(*) FROM orphaned_tasks_temp GROUP BY source_table
UNION ALL
SELECT source_table, COUNT(*) FROM orphaned_filing_temp GROUP BY source_table
UNION ALL
SELECT source_table, COUNT(*) FROM orphaned_fabrication_temp GROUP BY source_table;

-- Clean orphaned task holds (tasks that don't exist)
DELETE FROM task_holds 
WHERE task_id NOT IN (SELECT id FROM tasks);

-- Clean orphaned machine runtime logs
DELETE FROM machine_runtime_logs 
WHERE task_id NOT IN (SELECT id FROM tasks);

-- Clean orphaned user work logs
DELETE FROM user_work_logs 
WHERE task_id NOT IN (SELECT id FROM tasks);

-- Clean orphaned task time logs
DELETE FROM task_time_logs 
WHERE task_id NOT IN (SELECT id FROM tasks);

-- ============================================================================
-- STEP 6: VERIFICATION QUERIES
-- ============================================================================
\echo '========================================='
\echo 'STEP 6: Verification...'
\echo '========================================='

-- Verify foreign keys are recreated
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('tasks', 'filing_tasks', 'fabrication_tasks', 'task_holds', 'machine_runtime_logs')
ORDER BY tc.table_name, kcu.column_name;

-- Verify soft delete normalization
SELECT 
    'users' AS table_name,
    COUNT(*) FILTER (WHERE is_deleted IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE is_deleted = true) AS deleted_count,
    COUNT(*) FILTER (WHERE is_deleted = false) AS active_count
FROM users
UNION ALL
SELECT 'tasks', 
    COUNT(*) FILTER (WHERE is_deleted IS NULL),
    COUNT(*) FILTER (WHERE is_deleted = true),
    COUNT(*) FILTER (WHERE is_deleted = false)
FROM tasks
UNION ALL
SELECT 'filing_tasks',
    COUNT(*) FILTER (WHERE is_deleted IS NULL),
    COUNT(*) FILTER (WHERE is_deleted = true),
    COUNT(*) FILTER (WHERE is_deleted = false)
FROM filing_tasks
UNION ALL
SELECT 'fabrication_tasks',
    COUNT(*) FILTER (WHERE is_deleted IS NULL),
    COUNT(*) FILTER (WHERE is_deleted = true),
    COUNT(*) FILTER (WHERE is_deleted = false)
FROM fabrication_tasks;

-- Verify no orphaned records remain
SELECT 'Orphaned task holds' AS check_type, COUNT(*) AS count
FROM task_holds WHERE task_id NOT IN (SELECT id FROM tasks)
UNION ALL
SELECT 'Orphaned machine logs', COUNT(*)
FROM machine_runtime_logs WHERE task_id NOT IN (SELECT id FROM tasks)
UNION ALL
SELECT 'Orphaned user logs', COUNT(*)
FROM user_work_logs WHERE task_id NOT IN (SELECT id FROM tasks);

\echo '========================================='
\echo 'CASCADE FOREIGN KEYS APPLIED SUCCESSFULLY!'
\echo 'Database is now consistent and ready.'
\echo '========================================='

COMMIT;
