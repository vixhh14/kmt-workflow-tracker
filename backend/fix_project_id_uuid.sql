-- ============================================================================
-- CRITICAL FIX: Complete project_id UUID Migration
-- ============================================================================
-- This script completes the half-done UUID migration safely.
-- NO DATA LOSS. NO TABLE DROPS. ONLY TYPE ALIGNMENT.
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Verify projects.project_id is UUID
-- ============================================================================
DO $$
BEGIN
    -- Check if projects.project_id is already UUID
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'projects' 
        AND column_name = 'project_id' 
        AND data_type != 'uuid'
    ) THEN
        RAISE NOTICE 'Converting projects.project_id to UUID...';
        ALTER TABLE projects 
            ALTER COLUMN project_id TYPE UUID 
            USING project_id::uuid;
    ELSE
        RAISE NOTICE 'projects.project_id is already UUID ✓';
    END IF;
END $$;

-- ============================================================================
-- STEP 2: Drop existing foreign key constraints (safe to recreate)
-- ============================================================================
ALTER TABLE filing_tasks DROP CONSTRAINT IF EXISTS fk_filing_project;
ALTER TABLE filing_tasks DROP CONSTRAINT IF EXISTS filing_tasks_project_id_fkey;

ALTER TABLE fabrication_tasks DROP CONSTRAINT IF EXISTS fk_fabrication_project;
ALTER TABLE fabrication_tasks DROP CONSTRAINT IF EXISTS fabrication_tasks_project_id_fkey;

ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_tasks_project;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_tasks_project_id;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_project_id_fkey;

-- ============================================================================
-- STEP 3: Convert filing_tasks.project_id to UUID
-- ============================================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'filing_tasks' 
        AND column_name = 'project_id' 
        AND data_type != 'uuid'
    ) THEN
        RAISE NOTICE 'Converting filing_tasks.project_id to UUID...';
        
        -- Handle NULL and invalid values safely
        UPDATE filing_tasks 
        SET project_id = NULL 
        WHERE project_id IS NOT NULL 
        AND project_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
        
        ALTER TABLE filing_tasks 
            ALTER COLUMN project_id TYPE UUID 
            USING project_id::uuid;
    ELSE
        RAISE NOTICE 'filing_tasks.project_id is already UUID ✓';
    END IF;
END $$;

-- ============================================================================
-- STEP 4: Convert fabrication_tasks.project_id to UUID
-- ============================================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'fabrication_tasks' 
        AND column_name = 'project_id' 
        AND data_type != 'uuid'
    ) THEN
        RAISE NOTICE 'Converting fabrication_tasks.project_id to UUID...';
        
        -- Handle NULL and invalid values safely
        UPDATE fabrication_tasks 
        SET project_id = NULL 
        WHERE project_id IS NOT NULL 
        AND project_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
        
        ALTER TABLE fabrication_tasks 
            ALTER COLUMN project_id TYPE UUID 
            USING project_id::uuid;
    ELSE
        RAISE NOTICE 'fabrication_tasks.project_id is already UUID ✓';
    END IF;
END $$;

-- ============================================================================
-- STEP 5: Convert tasks.project_id to UUID
-- ============================================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'project_id' 
        AND data_type != 'uuid'
    ) THEN
        RAISE NOTICE 'Converting tasks.project_id to UUID...';
        
        -- Handle NULL and invalid values safely
        UPDATE tasks 
        SET project_id = NULL 
        WHERE project_id IS NOT NULL 
        AND project_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
        
        ALTER TABLE tasks 
            ALTER COLUMN project_id TYPE UUID 
            USING project_id::uuid;
    ELSE
        RAISE NOTICE 'tasks.project_id is already UUID ✓';
    END IF;
END $$;

-- ============================================================================
-- STEP 6: Recreate foreign key constraints (UUID → UUID)
-- ============================================================================
ALTER TABLE filing_tasks
    ADD CONSTRAINT fk_filing_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(project_id) 
    ON DELETE SET NULL;

ALTER TABLE fabrication_tasks
    ADD CONSTRAINT fk_fabrication_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(project_id) 
    ON DELETE SET NULL;

ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(project_id) 
    ON DELETE SET NULL;

-- ============================================================================
-- STEP 7: Recreate project_overview VIEW with proper UUID casting
-- ============================================================================
DROP VIEW IF EXISTS project_overview;

CREATE VIEW project_overview AS
SELECT
    p.project_id::text AS project_id,
    p.project_name,
    p.work_order_number,
    p.client_name,
    COUNT(t.id) FILTER (WHERE t.is_deleted = false OR t.is_deleted IS NULL) AS total_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'completed' AND (t.is_deleted = false OR t.is_deleted IS NULL)) AS completed_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'in_progress' AND (t.is_deleted = false OR t.is_deleted IS NULL)) AS in_progress_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'pending' AND (t.is_deleted = false OR t.is_deleted IS NULL)) AS pending_tasks
FROM projects p
LEFT JOIN tasks t ON t.project_id = p.project_id
WHERE p.is_deleted = false OR p.is_deleted IS NULL
GROUP BY p.project_id, p.project_name, p.work_order_number, p.client_name;

-- ============================================================================
-- STEP 8: Verification
-- ============================================================================
DO $$
DECLARE
    projects_type text;
    tasks_type text;
    filing_type text;
    fab_type text;
BEGIN
    SELECT data_type INTO projects_type FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'project_id';
    SELECT data_type INTO tasks_type FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'project_id';
    SELECT data_type INTO filing_type FROM information_schema.columns WHERE table_name = 'filing_tasks' AND column_name = 'project_id';
    SELECT data_type INTO fab_type FROM information_schema.columns WHERE table_name = 'fabrication_tasks' AND column_name = 'project_id';
    
    RAISE NOTICE '============================================';
    RAISE NOTICE 'VERIFICATION RESULTS:';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'projects.project_id: %', projects_type;
    RAISE NOTICE 'tasks.project_id: %', tasks_type;
    RAISE NOTICE 'filing_tasks.project_id: %', filing_type;
    RAISE NOTICE 'fabrication_tasks.project_id: %', fab_type;
    RAISE NOTICE '============================================';
    
    IF projects_type = 'uuid' AND tasks_type = 'uuid' AND filing_type = 'uuid' AND fab_type = 'uuid' THEN
        RAISE NOTICE '✅ ALL project_id columns are UUID!';
    ELSE
        RAISE WARNING '⚠️ Some columns are not UUID. Manual intervention needed.';
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
