-- QUICK DEPLOYMENT SCRIPT
-- Run this in psql or pgAdmin to apply all fixes at once

\echo '========================================='
\echo 'PRODUCTION STABILIZATION - QUICK DEPLOY'
\echo '========================================='

-- 1. Normalize soft deletes (NULL → false)
\echo 'Step 1: Normalizing soft delete flags...'
UPDATE users SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE projects SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE machines SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE filing_tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE fabrication_tasks SET is_deleted = false WHERE is_deleted IS NULL;

-- 2. Create operators view
\echo 'Step 2: Creating operators view...'
CREATE OR REPLACE VIEW operators_view AS
SELECT 
    user_id AS id,
    user_id,
    username,
    email,
    full_name,
    contact_number,
    COALESCE(is_deleted, false) AS is_deleted
FROM users
WHERE COALESCE(is_deleted, false) = false
  AND approval_status = 'approved'
  AND LOWER(role) = 'operator';

-- 3. Create unified tasks view
\echo 'Step 3: Creating unified tasks view...'
CREATE OR REPLACE VIEW tasks_unified_view AS
SELECT 
    id::text AS id,
    'general' AS task_type,
    title,
    project_id,
    status,
    priority,
    assigned_to,
    machine_id,
    due_date,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at
FROM tasks
WHERE COALESCE(is_deleted, false) = false

UNION ALL

SELECT 
    id::text AS id,
    'filing' AS task_type,
    part_item AS title,
    project_id,
    status,
    priority,
    assigned_to,
    machine_id,
    due_date,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at
FROM filing_tasks
WHERE COALESCE(is_deleted, false) = false

UNION ALL

SELECT 
    id::text AS id,
    'fabrication' AS task_type,
    part_item AS title,
    project_id,
    status,
    priority,
    assigned_to,
    machine_id,
    due_date,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at
FROM fabrication_tasks
WHERE COALESCE(is_deleted, false) = false;

-- 4. Verify results
\echo 'Step 4: Verification...'
\echo 'Task counts by type:'
SELECT task_type, COUNT(*) FROM tasks_unified_view GROUP BY task_type;

\echo 'Active operators:'
SELECT COUNT(*) AS operator_count FROM operators_view;

\echo 'Soft delete normalization:'
SELECT 
    'users' AS table_name, 
    COUNT(*) FILTER (WHERE is_deleted IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE is_deleted = true) AS deleted_count,
    COUNT(*) FILTER (WHERE is_deleted = false) AS active_count
FROM users
UNION ALL
SELECT 
    'tasks',
    COUNT(*) FILTER (WHERE is_deleted IS NULL),
    COUNT(*) FILTER (WHERE is_deleted = true),
    COUNT(*) FILTER (WHERE is_deleted = false)
FROM tasks
UNION ALL
SELECT 
    'filing_tasks',
    COUNT(*) FILTER (WHERE is_deleted IS NULL),
    COUNT(*) FILTER (WHERE is_deleted = true),
    COUNT(*) FILTER (WHERE is_deleted = false)
FROM filing_tasks
UNION ALL
SELECT 
    'fabrication_tasks',
    COUNT(*) FILTER (WHERE is_deleted IS NULL),
    COUNT(*) FILTER (WHERE is_deleted = true),
    COUNT(*) FILTER (WHERE is_deleted = false)
FROM fabrication_tasks;

\echo '========================================='
\echo 'DEPLOYMENT COMPLETE!'
\echo 'Next: Restart backend server'
\echo '========================================='
