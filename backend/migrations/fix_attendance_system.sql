-- =====================================================
-- ATTENDANCE SYSTEM FIX - Database Migration
-- =====================================================
-- This script fixes the attendance table schema to support
-- proper attendance tracking with unique constraints

-- Add missing columns if they don't exist
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_in TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_out TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS login_time TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS ip_address VARCHAR(255);
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Present';

-- Convert date column to proper DATE type (from TIMESTAMP or VARCHAR)
-- First, create a temporary column
ALTER TABLE attendance ADD COLUMN IF NOT EXISTS date_temp DATE;

-- Copy converted data to temp column
UPDATE attendance SET date_temp = date::date WHERE date_temp IS NULL;

-- Drop old date column and rename temp
ALTER TABLE attendance DROP COLUMN IF EXISTS date CASCADE;
ALTER TABLE attendance RENAME COLUMN date_temp TO date;

-- Set default for date column
ALTER TABLE attendance ALTER COLUMN date SET DEFAULT CURRENT_DATE;

-- Create unique index for (user_id, date) to prevent duplicates
-- Drop existing index if it exists
DROP INDEX IF EXISTS idx_attendance_user_date;

-- Create new unique index
CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, date);

-- Add foreign key constraint if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_attendance_user_id'
    ) THEN
        ALTER TABLE attendance 
        ADD CONSTRAINT fk_attendance_user_id 
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Clean up any duplicate records (keep the latest one)
DELETE FROM attendance a USING (
    SELECT user_id, date, MAX(id) as max_id
    FROM attendance
    GROUP BY user_id, date
    HAVING COUNT(*) > 1
) b
WHERE a.user_id = b.user_id 
  AND a.date = b.date 
  AND a.id < b.max_id;

-- Update any NULL statuses to 'Present'
UPDATE attendance SET status = 'Present' WHERE status IS NULL;

-- Ensure all existing records have proper timestamps
UPDATE attendance SET check_in = login_time WHERE check_in IS NULL AND login_time IS NOT NULL;
UPDATE attendance SET login_time = check_in WHERE login_time IS NULL AND check_in IS NOT NULL;
