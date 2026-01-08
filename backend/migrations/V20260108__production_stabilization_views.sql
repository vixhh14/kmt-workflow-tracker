-- PRODUCTION STABILIZATION: Database Normalization Views
-- Purpose: Create compatibility layer for inconsistent primary keys
-- Strategy: Read-only views that normalize schema without data migration
-- Safety: Zero data loss, zero breaking changes

-- ============================================================================
-- 1. PROJECTS VIEW (Normalize project_id → id)
-- ============================================================================
CREATE OR REPLACE VIEW projects_view AS
SELECT 
    project_id::text AS id,
    project_id,
    project_name AS name,
    project_name,
    project_code,
    work_order_number,
    client_name,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at
FROM projects
WHERE COALESCE(is_deleted, false) = false;

COMMENT ON VIEW projects_view IS 'Normalized view for projects with consistent id field';

-- ============================================================================
-- 2. MACHINES VIEW (Normalize machine PK → id, machine_name → name)
-- ============================================================================
CREATE OR REPLACE VIEW machines_view AS
SELECT 
    id,
    machine_name AS name,
    machine_name,
    status,
    hourly_rate,
    last_maintenance,
    current_operator,
    category_id,
    unit_id,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at,
    updated_at
FROM machines
WHERE COALESCE(is_deleted, false) = false;

COMMENT ON VIEW machines_view IS 'Normalized view for machines with consistent naming';

-- ============================================================================
-- 3. USERS VIEW (Normalize user_id → id)
-- ============================================================================
CREATE OR REPLACE VIEW users_view AS
SELECT 
    user_id AS id,
    user_id,
    username,
    email,
    role,
    full_name,
    machine_types,
    contact_number,
    unit_id,
    approval_status,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at,
    updated_at
FROM users
WHERE COALESCE(is_deleted, false) = false
  AND approval_status = 'approved';

COMMENT ON VIEW users_view IS 'Normalized view for active approved users';

-- ============================================================================
-- 4. OPERATORS VIEW (Active operators only)
-- ============================================================================
CREATE OR REPLACE VIEW operators_view AS
SELECT 
    user_id AS id,
    user_id,
    username,
    email,
    full_name,
    contact_number,
    machine_types,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at
FROM users
WHERE COALESCE(is_deleted, false) = false
  AND approval_status = 'approved'
  AND LOWER(role) = 'operator';

COMMENT ON VIEW operators_view IS 'Active operators for dropdown population';

-- ============================================================================
-- 5. UNIFIED TASKS VIEW (Aggregate all 3 task tables)
-- ============================================================================
CREATE OR REPLACE VIEW tasks_unified_view AS
-- General Tasks
SELECT 
    id,
    'general' AS task_type,
    title,
    project,
    project_id,
    description,
    part_item,
    status,
    priority,
    assigned_to,
    machine_id,
    due_date,
    work_order_number,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at,
    started_at,
    completed_at,
    actual_start_time,
    actual_end_time,
    expected_completion_time,
    total_held_seconds
FROM tasks
WHERE COALESCE(is_deleted, false) = false

UNION ALL

-- Filing Tasks
SELECT 
    id::text AS id,
    'filing' AS task_type,
    part_item AS title,
    NULL AS project,
    project_id,
    remarks AS description,
    part_item,
    status,
    priority,
    assigned_to,
    machine_id,
    due_date,
    work_order_number,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at,
    started_at,
    completed_at,
    started_at AS actual_start_time,
    completed_at AS actual_end_time,
    NULL AS expected_completion_time,
    total_active_duration AS total_held_seconds
FROM filing_tasks
WHERE COALESCE(is_deleted, false) = false

UNION ALL

-- Fabrication Tasks
SELECT 
    id::text AS id,
    'fabrication' AS task_type,
    part_item AS title,
    NULL AS project,
    project_id,
    remarks AS description,
    part_item,
    status,
    priority,
    assigned_to,
    machine_id,
    due_date,
    work_order_number,
    COALESCE(is_deleted, false) AS is_deleted,
    created_at,
    started_at,
    completed_at,
    started_at AS actual_start_time,
    completed_at AS actual_end_time,
    NULL AS expected_completion_time,
    total_active_duration AS total_held_seconds
FROM fabrication_tasks
WHERE COALESCE(is_deleted, false) = false;

COMMENT ON VIEW tasks_unified_view IS 'Unified view of all task types for dashboard aggregation';

-- ============================================================================
-- 6. DASHBOARD OVERVIEW MATERIALIZED VIEW (Performance optimization)
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_overview_mv AS
SELECT 
    -- Task Counts
    COUNT(*) FILTER (WHERE task_type = 'general') AS general_tasks_total,
    COUNT(*) FILTER (WHERE task_type = 'filing') AS filing_tasks_total,
    COUNT(*) FILTER (WHERE task_type = 'fabrication') AS fabrication_tasks_total,
    COUNT(*) AS total_tasks,
    
    -- Status Breakdown (Case-insensitive)
    COUNT(*) FILTER (WHERE LOWER(status) = 'pending') AS pending_tasks,
    COUNT(*) FILTER (WHERE LOWER(status) IN ('in_progress', 'in progress')) AS in_progress_tasks,
    COUNT(*) FILTER (WHERE LOWER(status) = 'completed') AS completed_tasks,
    COUNT(*) FILTER (WHERE LOWER(status) IN ('on_hold', 'on hold', 'onhold')) AS on_hold_tasks,
    COUNT(*) FILTER (WHERE LOWER(status) = 'ended') AS ended_tasks,
    
    -- Priority Breakdown
    COUNT(*) FILTER (WHERE LOWER(priority) = 'high') AS high_priority_tasks,
    COUNT(*) FILTER (WHERE LOWER(priority) = 'medium') AS medium_priority_tasks,
    COUNT(*) FILTER (WHERE LOWER(priority) = 'low') AS low_priority_tasks,
    
    -- Project & Machine Counts
    COUNT(DISTINCT project_id) AS total_projects_with_tasks,
    COUNT(DISTINCT machine_id) FILTER (WHERE machine_id IS NOT NULL) AS total_machines_with_tasks,
    COUNT(DISTINCT assigned_to) FILTER (WHERE assigned_to IS NOT NULL) AS total_operators_with_tasks,
    
    -- Timestamp
    NOW() AS last_refreshed
FROM tasks_unified_view;

CREATE UNIQUE INDEX IF NOT EXISTS dashboard_overview_mv_idx ON dashboard_overview_mv ((1));

COMMENT ON MATERIALIZED VIEW dashboard_overview_mv IS 'Pre-aggregated dashboard metrics for performance';

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_dashboard_overview()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_overview_mv;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. SOFT DELETE NORMALIZATION (Fix NULL → false)
-- ============================================================================

-- Update all tables to normalize is_deleted
UPDATE users SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE projects SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE machines SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE filing_tasks SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE fabrication_tasks SET is_deleted = false WHERE is_deleted IS NULL;

-- Add NOT NULL constraints (safe after normalization)
ALTER TABLE users ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE projects ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE machines ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE tasks ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE filing_tasks ALTER COLUMN is_deleted SET DEFAULT false;
ALTER TABLE fabrication_tasks ALTER COLUMN is_deleted SET DEFAULT false;

-- ============================================================================
-- 8. ORPHANED RELATIONS CLEANUP (Safe defaults)
-- ============================================================================

-- Find and report orphaned tasks (for manual review)
CREATE OR REPLACE VIEW orphaned_tasks_report AS
SELECT 
    t.id,
    t.task_type,
    t.title,
    t.project_id,
    t.assigned_to,
    t.machine_id,
    CASE 
        WHEN t.project_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM projects WHERE project_id = t.project_id) THEN 'Missing Project'
        WHEN t.assigned_to IS NOT NULL AND NOT EXISTS (SELECT 1 FROM users WHERE user_id = t.assigned_to) THEN 'Missing User'
        WHEN t.machine_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM machines WHERE id = t.machine_id) THEN 'Missing Machine'
        ELSE 'OK'
    END AS orphan_type
FROM tasks_unified_view t
WHERE 
    (t.project_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM projects WHERE project_id = t.project_id))
    OR (t.assigned_to IS NOT NULL AND NOT EXISTS (SELECT 1 FROM users WHERE user_id = t.assigned_to))
    OR (t.machine_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM machines WHERE id = t.machine_id));

COMMENT ON VIEW orphaned_tasks_report IS 'Identifies tasks with broken foreign key references';

-- ============================================================================
-- 9. GRANT PERMISSIONS (Ensure app can read views)
-- ============================================================================

GRANT SELECT ON projects_view TO PUBLIC;
GRANT SELECT ON machines_view TO PUBLIC;
GRANT SELECT ON users_view TO PUBLIC;
GRANT SELECT ON operators_view TO PUBLIC;
GRANT SELECT ON tasks_unified_view TO PUBLIC;
GRANT SELECT ON dashboard_overview_mv TO PUBLIC;
GRANT SELECT ON orphaned_tasks_report TO PUBLIC;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Test 1: Verify projects view
-- SELECT * FROM projects_view LIMIT 5;

-- Test 2: Verify operators view
-- SELECT * FROM operators_view LIMIT 5;

-- Test 3: Verify unified tasks
-- SELECT task_type, COUNT(*) FROM tasks_unified_view GROUP BY task_type;

-- Test 4: Verify dashboard overview
-- SELECT * FROM dashboard_overview_mv;

-- Test 5: Check for orphaned tasks
-- SELECT * FROM orphaned_tasks_report;

COMMIT;
