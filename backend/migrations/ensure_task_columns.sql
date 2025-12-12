-- Migration to ensure all task columns exist
-- Safe to run multiple times - uses IF NOT EXISTS

-- Add actual_start_time column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='actual_start_time'
    ) THEN
        ALTER TABLE tasks ADD COLUMN actual_start_time TIMESTAMP;
    END IF;
END $$;

-- Add actual_end_time column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='actual_end_time'
    ) THEN
        ALTER TABLE tasks ADD COLUMN actual_end_time TIMESTAMP;
    END IF;
END $$;

-- Add total_held_seconds column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='total_held_seconds'
    ) THEN
        ALTER TABLE tasks ADD COLUMN total_held_seconds BIGINT DEFAULT 0;
    END IF;
END $$;

-- Add expected_completion_time column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='expected_completion_time'
    ) THEN
        ALTER TABLE tasks ADD COLUMN expected_completion_time VARCHAR(255);
    END IF;
END $$;

-- Add started_at column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='started_at'
    ) THEN
        ALTER TABLE tasks ADD COLUMN started_at TIMESTAMP;
    END IF;
END $$;

-- Add completed_at column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='completed_at'
    ) THEN
        ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP;
    END IF;
END $$;

-- Add total_duration_seconds column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='total_duration_seconds'
    ) THEN
        ALTER TABLE tasks ADD COLUMN total_duration_seconds INTEGER DEFAULT 0;
    END IF;
END $$;

-- Add hold_reason column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='hold_reason'
    ) THEN
        ALTER TABLE tasks ADD COLUMN hold_reason TEXT;
    END IF;
END $$;

-- Add denial_reason column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='denial_reason'
    ) THEN
        ALTER TABLE tasks ADD COLUMN denial_reason TEXT;
    END IF;
END $$;

-- Create index on assigned_to for faster operator queries
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);

-- Create index on status for faster filtering
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Update any NULL values to defaults
UPDATE tasks SET total_duration_seconds = 0 WHERE total_duration_seconds IS NULL;
UPDATE tasks SET total_held_seconds = 0 WHERE total_held_seconds IS NULL;
UPDATE tasks SET status = 'pending' WHERE status IS NULL OR status = '';
UPDATE tasks SET priority = 'medium' WHERE priority IS NULL OR priority = '';
