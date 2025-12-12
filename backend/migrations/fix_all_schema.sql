-- Complete schema migration to fix all datetime and column issues
--Safe to run multiple times

-- Fix attendance table columns
DO $$ 
BEGIN
    -- Add check_in column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='attendance' AND column_name='check_in') THEN
        ALTER TABLE attendance ADD COLUMN check_in TIMESTAMPTZ;
    END IF;
    
    -- Add check_out column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='attendance' AND column_name='check_out') THEN
        ALTER TABLE attendance ADD COLUMN check_out TIMESTAMPTZ;
    END IF;
    
    -- Add login_time column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='attendance' AND column_name='login_time') THEN
        ALTER TABLE attendance ADD COLUMN login_time TIMESTAMPTZ DEFAULT NOW();
    END IF;
    
    -- Add status column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='attendance' AND column_name='status') THEN
        ALTER TABLE attendance ADD COLUMN status VARCHAR(50) DEFAULT 'present';
    END IF;
    
    -- Add ip_address column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='attendance' AND column_name='ip_address') THEN
        ALTER TABLE attendance ADD COLUMN ip_address VARCHAR(100);
    END IF;
END $$;

-- Fix tasks table - ensure all columns exist and are timezone-aware
DO $$ 
BEGIN
    -- started_at
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='started_at') THEN
        ALTER TABLE tasks ADD COLUMN started_at TIMESTAMPTZ;
    END IF;
    
    -- completed_at
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='completed_at' AND column_name='completed_at') THEN
        ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMPTZ;
    END IF;
    
    -- actual_start_time
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='actual_start_time') THEN
        ALTER TABLE tasks ADD COLUMN actual_start_time TIMESTAMPTZ;
    END IF;
    
    -- actual_end_time
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='actual_end_time') THEN
        ALTER TABLE tasks ADD COLUMN actual_end_time TIMESTAMPTZ;
    END IF;
    
    -- total_duration_seconds
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='total_duration_seconds') THEN
        ALTER TABLE tasks ADD COLUMN total_duration_seconds INTEGER DEFAULT 0;
    END IF;
    
    -- total_held_seconds
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='total_held_seconds') THEN
        ALTER TABLE tasks ADD COLUMN total_held_seconds BIGINT DEFAULT 0;
    END IF;
    
    -- hold_reason
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='hold_reason') THEN
        ALTER TABLE tasks ADD COLUMN hold_reason TEXT;
    END IF;
    
    -- denial_reason
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='denial_reason') THEN
        ALTER TABLE tasks ADD COLUMN denial_reason TEXT;
    END IF;
    
    -- expected_completion_time
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='expected_completion_time') THEN
        ALTER TABLE tasks ADD COLUMN expected_completion_time VARCHAR(255);
    END IF;
END $$;

-- Convert existing datetime columns to timezone-aware (if not already)
ALTER TABLE tasks ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project);
CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_check_in ON attendance(check_in);

-- Set defaults for null values
UPDATE tasks SET total_duration_seconds = 0 WHERE total_duration_seconds IS NULL;
UPDATE tasks SET total_held_seconds = 0 WHERE total_held_seconds IS NULL;
UPDATE tasks SET status = 'pending' WHERE status IS NULL OR status = '';
UPDATE tasks SET priority = 'medium' WHERE priority IS NULL OR priority = '';
UPDATE attendance SET status = 'present' WHERE status IS NULL;

COMMIT;
