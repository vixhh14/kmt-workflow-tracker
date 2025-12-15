-- Global Timezone Setting
ALTER DATABASE "workflow_db" SET timezone TO 'Asia/Kolkata';

-- Convert all existing DateTime columns to TIMESTAMPTZ (Aware)
-- We explicitly interpret existing data as UTC because it was stored using datetime.utcnow()
-- which is naive but practically UTC.
-- This conversion ensures the exact moment in time is preserved.

-- Users
ALTER TABLE users 
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

-- Units
ALTER TABLE units ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Machine Categories
ALTER TABLE machine_categories ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- User Approvals
ALTER TABLE user_approvals 
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN approved_at TYPE TIMESTAMPTZ USING approved_at AT TIME ZONE 'UTC';

-- User Machines
ALTER TABLE user_machines ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Machines
ALTER TABLE machines 
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

-- Tasks
-- Note: 'due_date' is stored as String, so we don't alter it.
ALTER TABLE tasks 
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN started_at TYPE TIMESTAMPTZ USING started_at AT TIME ZONE 'UTC',
  ALTER COLUMN completed_at TYPE TIMESTAMPTZ USING completed_at AT TIME ZONE 'UTC',
  ALTER COLUMN actual_start_time TYPE TIMESTAMPTZ USING actual_start_time AT TIME ZONE 'UTC',
  ALTER COLUMN actual_end_time TYPE TIMESTAMPTZ USING actual_end_time AT TIME ZONE 'UTC';

-- Task Holds
ALTER TABLE task_holds 
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN hold_started_at TYPE TIMESTAMPTZ USING hold_started_at AT TIME ZONE 'UTC',
  ALTER COLUMN hold_ended_at TYPE TIMESTAMPTZ USING hold_ended_at AT TIME ZONE 'UTC';

-- Reschedule Requests
ALTER TABLE reschedule_requests 
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN requested_for_date TYPE TIMESTAMPTZ USING requested_for_date AT TIME ZONE 'UTC';

-- Task Time Logs
ALTER TABLE task_time_logs ALTER COLUMN timestamp TYPE TIMESTAMPTZ USING timestamp AT TIME ZONE 'UTC';

-- Planning Tasks
ALTER TABLE planning_tasks ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

-- Outsource Items
ALTER TABLE outsource_items 
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC',
  ALTER COLUMN follow_up_time TYPE TIMESTAMPTZ USING follow_up_time AT TIME ZONE 'UTC';

-- Attendance
-- Note: 'date' is stored as Date, so we leave it.
ALTER TABLE attendance 
  ALTER COLUMN check_in TYPE TIMESTAMPTZ USING check_in AT TIME ZONE 'UTC',
  ALTER COLUMN check_out TYPE TIMESTAMPTZ USING check_out AT TIME ZONE 'UTC',
  ALTER COLUMN login_time TYPE TIMESTAMPTZ USING login_time AT TIME ZONE 'UTC';

-- Subtasks
ALTER TABLE subtasks 
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
