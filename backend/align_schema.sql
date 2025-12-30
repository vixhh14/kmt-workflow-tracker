-- ALIGN_SCHEMA_V4.SQL
-- Senior Engineer: Alining Database Schema for Workflow Tracker

-- 1. EXTEND FILING_TASKS TABLE
DO $$ 
BEGIN 
    -- Add work_order_number if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='filing_tasks' AND column_name='work_order_number') THEN
        ALTER TABLE filing_tasks ADD COLUMN work_order_number VARCHAR;
    END IF;

    -- Add is_deleted flag for soft delete
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='filing_tasks' AND column_name='is_deleted') THEN
        ALTER TABLE filing_tasks ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add assigned_by to track creator
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='filing_tasks' AND column_name='assigned_by') THEN
        ALTER TABLE filing_tasks ADD COLUMN assigned_by VARCHAR;
    END IF;

    -- Ensure quality constraints
    ALTER TABLE filing_tasks ALTER COLUMN quantity SET DEFAULT 1;
    ALTER TABLE filing_tasks ALTER COLUMN status SET DEFAULT 'Pending';
END $$;

-- 2. EXTEND FABRICATION_TASKS TABLE
DO $$ 
BEGIN 
    -- Add work_order_number if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='fabrication_tasks' AND column_name='work_order_number') THEN
        ALTER TABLE fabrication_tasks ADD COLUMN work_order_number VARCHAR;
    END IF;

    -- Add is_deleted flag for soft delete
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='fabrication_tasks' AND column_name='is_deleted') THEN
        ALTER TABLE fabrication_tasks ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add assigned_by to track creator
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='fabrication_tasks' AND column_name='assigned_by') THEN
        ALTER TABLE fabrication_tasks ADD COLUMN assigned_by VARCHAR;
    END IF;

    -- Ensure quality constraints
    ALTER TABLE fabrication_tasks ALTER COLUMN quantity SET DEFAULT 1;
    ALTER TABLE fabrication_tasks ALTER COLUMN status SET DEFAULT 'Pending';
END $$;

-- 3. ENSURE TASKS TABLE IS ALIGNED
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='work_order_number') THEN
        ALTER TABLE tasks ADD COLUMN work_order_number VARCHAR;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='is_deleted') THEN
        ALTER TABLE tasks ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- 4. BACKFILL DATA
UPDATE filing_tasks SET work_order_number = 'FIL-' || id WHERE work_order_number IS NULL;
UPDATE fabrication_tasks SET work_order_number = 'FAB-' || id WHERE work_order_number IS NULL;
UPDATE tasks SET work_order_number = 'TASK-' || id WHERE work_order_number IS NULL;

-- 5. VERIFY FOREIGN KEYS
-- Note: These assume the target tables 'projects', 'machines', and 'users' have columns 'project_id', 'id', and 'user_id' respectively.
DO $$ 
BEGIN
    -- Filing FKs
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_filing_project') THEN
        ALTER TABLE filing_tasks ADD CONSTRAINT fk_filing_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL;
    END IF;
    
    -- Fabrication FKs
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fabrication_project') THEN
        ALTER TABLE fabrication_tasks ADD CONSTRAINT fk_fabrication_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL;
    END IF;
END $$;

COMMIT;
