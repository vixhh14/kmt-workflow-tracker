
-- RECOVERY & MIGRATION SCRIPT
-- RUN THIS IN YOUR POSTGRESQL DATABASE TOOL (pgAdmin / psql)
-- This script safely aligns your database schema with the backend code.

BEGIN;

-- 1. FIX USERS TABLE
-- Ensure 'user_id' is the primary key column name
DO $$ 
BEGIN 
  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='users' AND column_name='id') THEN
    ALTER TABLE users RENAME COLUMN id TO user_id;
  END IF;
END $$;

-- 2. FIX MACHINES TABLE
-- Ensure 'machine_name' is used instead of 'name'
DO $$ 
BEGIN 
  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='machines' AND column_name='name') THEN
    ALTER TABLE machines RENAME COLUMN name TO machine_name;
  END IF;
END $$;

-- Ensure is_deleted exists
ALTER TABLE machines ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
UPDATE machines SET is_deleted = FALSE WHERE is_deleted IS NULL;

-- 3. FIX PROJECTS TABLE
-- Ensure project_id exists. If 'id' is used, rename it.
DO $$ 
BEGIN 
  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='projects' AND column_name='id') THEN
    ALTER TABLE projects RENAME COLUMN id TO project_id;
  END IF;
END $$;

-- Ensure is_deleted exists
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
UPDATE projects SET is_deleted = FALSE WHERE is_deleted IS NULL;

-- 4. FIX TASKS TABLE (Structure)
-- We enforce UUID string for ID compatibility.
-- Add necessary columns if missing.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_start_time TIMESTAMPTZ;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_end_time TIMESTAMPTZ;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS total_held_seconds BIGINT DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS machine_id VARCHAR;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS project_id INTEGER;

-- Fix duration column types if they drifted
-- We primarily use total_duration_seconds (Integer)
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS total_duration_seconds INTEGER DEFAULT 0;

-- Ensure is_deleted
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
UPDATE tasks SET is_deleted = FALSE WHERE is_deleted IS NULL;

-- 5. ATTENDANCE TABLE
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS date DATE;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_in TIMESTAMPTZ;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_out TIMESTAMPTZ;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS login_time TIMESTAMPTZ;

-- 6. INDEXES (Performance)
CREATE INDEX IF NOT EXISTS idx_tasks_is_deleted ON tasks(is_deleted);
CREATE INDEX IF NOT EXISTS idx_projects_is_deleted ON projects(is_deleted);
CREATE INDEX IF NOT EXISTS idx_machines_is_deleted ON machines(is_deleted);

COMMIT;

-- VERIFICATION QUERY
SELECT 
    (SELECT COUNT(*) FROM tasks WHERE is_deleted = FALSE) as active_tasks,
    (SELECT COUNT(*) FROM projects WHERE is_deleted = FALSE) as active_projects,
    (SELECT COUNT(*) FROM machines WHERE is_deleted = FALSE) as active_machines;
