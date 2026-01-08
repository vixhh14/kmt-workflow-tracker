-- ============================================================================
-- EMERGENCY FIX: Restore expected_completion_time Column
-- ============================================================================
-- Issue: Column tasks.expected_completion_time was dropped from DB
--        but SQLAlchemy ORM still references it, causing 500 errors
-- Solution: Re-add column to match ORM definition
-- Safety: Column is nullable, zero data loss, backward compatible
-- ============================================================================

BEGIN;

-- Check if column exists (for verification)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'expected_completion_time'
    ) THEN
        -- Column doesn't exist, add it
        ALTER TABLE tasks 
        ADD COLUMN expected_completion_time INTEGER NULL;
        
        RAISE NOTICE 'Column expected_completion_time added to tasks table';
    ELSE
        RAISE NOTICE 'Column expected_completion_time already exists';
    END IF;
END $$;

-- Verify column was added
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'tasks' 
AND column_name = 'expected_completion_time';

COMMIT;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Test that tasks can be queried without error
SELECT 
    id, 
    title, 
    status, 
    expected_completion_time,
    created_at
FROM tasks 
LIMIT 5;

-- Expected: Query succeeds, expected_completion_time shows NULL or integer values
