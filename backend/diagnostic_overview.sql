-- ============================================================================
-- EMERGENCY DIAGNOSTIC: Check Operations Overview Data
-- ============================================================================
-- Purpose: Verify why Operations Overview shows zeros
-- ============================================================================

\echo '========================================='
\echo 'DIAGNOSTIC: Operations Overview Data'
\echo '========================================='
\echo ''

-- 1. Check Projects
\echo '1. PROJECTS:'
SELECT 
    COUNT(*) AS total_projects,
    COUNT(*) FILTER (WHERE is_deleted = false) AS active_projects,
    COUNT(*) FILTER (WHERE is_deleted = true) AS deleted_projects
FROM projects;

\echo ''
\echo 'Project Details:'
SELECT project_id, project_name, project_code, is_deleted, created_at 
FROM projects 
ORDER BY created_at DESC 
LIMIT 10;

\echo ''
\echo '========================================='

-- 2. Check Tasks (General)
\echo '2. GENERAL TASKS (tasks table):'
SELECT 
    COUNT(*) AS total_tasks,
    COUNT(*) FILTER (WHERE is_deleted = false) AS active_tasks,
    COUNT(*) FILTER (WHERE is_deleted = true) AS deleted_tasks,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'pending') AS pending,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'in_progress') AS in_progress,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'completed') AS completed
FROM tasks;

\echo ''
\echo 'Task Details:'
SELECT id, title, status, priority, assigned_to, is_deleted, created_at 
FROM tasks 
ORDER BY created_at DESC 
LIMIT 10;

\echo ''
\echo '========================================='

-- 3. Check Filing Tasks
\echo '3. FILING TASKS (filing_tasks table):'
SELECT 
    COUNT(*) AS total_filing,
    COUNT(*) FILTER (WHERE is_deleted = false) AS active_filing,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'pending') AS pending,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'in progress') AS in_progress,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'completed') AS completed
FROM filing_tasks;

\echo ''
\echo 'Filing Task Details:'
SELECT id, part_item, status, priority, assigned_to, is_deleted, created_at 
FROM filing_tasks 
ORDER BY created_at DESC 
LIMIT 10;

\echo ''
\echo '========================================='

-- 4. Check Fabrication Tasks
\echo '4. FABRICATION TASKS (fabrication_tasks table):'
SELECT 
    COUNT(*) AS total_fabrication,
    COUNT(*) FILTER (WHERE is_deleted = false) AS active_fabrication,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'pending') AS pending,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'in progress') AS in_progress,
    COUNT(*) FILTER (WHERE is_deleted = false AND LOWER(status) = 'completed') AS completed
FROM fabrication_tasks;

\echo ''
\echo 'Fabrication Task Details:'
SELECT id, part_item, status, priority, assigned_to, is_deleted, created_at 
FROM fabrication_tasks 
ORDER BY created_at DESC 
LIMIT 10;

\echo ''
\echo '========================================='

-- 5. AGGREGATE SUMMARY
\echo '5. AGGREGATE SUMMARY (What dashboard should show):'
SELECT 
    (SELECT COUNT(*) FROM projects WHERE is_deleted = false) AS total_projects,
    (
        (SELECT COUNT(*) FROM tasks WHERE is_deleted = false) +
        (SELECT COUNT(*) FROM filing_tasks WHERE is_deleted = false) +
        (SELECT COUNT(*) FROM fabrication_tasks WHERE is_deleted = false)
    ) AS total_tasks,
    (
        (SELECT COUNT(*) FROM tasks WHERE is_deleted = false AND LOWER(status) = 'pending') +
        (SELECT COUNT(*) FROM filing_tasks WHERE is_deleted = false AND LOWER(status) = 'pending') +
        (SELECT COUNT(*) FROM fabrication_tasks WHERE is_deleted = false AND LOWER(status) = 'pending')
    ) AS total_pending,
    (
        (SELECT COUNT(*) FROM tasks WHERE is_deleted = false AND LOWER(status) = 'in_progress') +
        (SELECT COUNT(*) FROM filing_tasks WHERE is_deleted = false AND LOWER(status) = 'in progress') +
        (SELECT COUNT(*) FROM fabrication_tasks WHERE is_deleted = false AND LOWER(status) = 'in progress')
    ) AS total_in_progress;

\echo ''
\echo '========================================='
\echo 'DIAGNOSTIC COMPLETE'
\echo '========================================='
