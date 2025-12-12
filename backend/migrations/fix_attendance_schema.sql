-- Complete attendance table schema fix
-- Safe to run multiple times

-- Add missing columns if they don't exist
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_in TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_out TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS login_time TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS ip_address VARCHAR(100);
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS status VARCHAR(50);

-- Ensure date column is proper DATE type
ALTER TABLE attendance ALTER COLUMN date TYPE DATE USING date::date;

-- Create unique index to prevent duplicate attendance per user per day
DROP INDEX IF EXISTS idx_attendance_user_date;
CREATE UNIQUE INDEX idx_attendance_user_date ON attendance(user_id, date);

-- Create additional indexes for performance
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);

-- Set default values for existing rows
UPDATE attendance SET status = 'Present' WHERE status IS NULL AND (check_in IS NOT NULL OR login_time IS NOT NULL);
UPDATE attendance SET status = 'Absent' WHERE status IS NULL;

-- Add constraint to ensure valid status values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'attendance_status_check'
    ) THEN
        ALTER TABLE attendance ADD CONSTRAINT attendance_status_check 
        CHECK (status IN ('Present', 'Absent', 'Left', 'Late'));
    END IF;
END $$;

COMMIT;
