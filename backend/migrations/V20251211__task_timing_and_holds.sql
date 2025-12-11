BEGIN;

-- 1. Add columns to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_start_time TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_end_time TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS total_held_seconds BIGINT DEFAULT 0;

-- 2. Create task_holds table
CREATE TABLE IF NOT EXISTS task_holds (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR NOT NULL REFERENCES tasks(id),
    user_id VARCHAR REFERENCES users(user_id),
    hold_reason TEXT,
    hold_started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    hold_ended_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 3. Create reschedule_requests table
CREATE TABLE IF NOT EXISTS reschedule_requests (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR NOT NULL REFERENCES tasks(id),
    requested_by VARCHAR REFERENCES users(user_id),
    requested_for_date TIMESTAMP WITH TIME ZONE,
    reason TEXT,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 4. Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_actual_start ON tasks(actual_start_time);
CREATE INDEX IF NOT EXISTS idx_task_holds_task_id ON task_holds(task_id);
CREATE INDEX IF NOT EXISTS idx_task_holds_user_id ON task_holds(user_id);
CREATE INDEX IF NOT EXISTS idx_reschedule_requests_task_id ON reschedule_requests(task_id);

COMMIT;
