-- Create tables for tracking Machine Runtime and User Working Time
-- This is necessary for the Daily Machine Reports and User Activity Reports features.

BEGIN;

-- 1. Create Machine Runtime Logs Table
CREATE TABLE IF NOT EXISTS machine_runtime_logs (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR REFERENCES machines(id),
    task_id VARCHAR REFERENCES tasks(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_machine_runtime_logs_date ON machine_runtime_logs(date);
CREATE INDEX IF NOT EXISTS idx_machine_runtime_logs_machine_id ON machine_runtime_logs(machine_id);
CREATE INDEX IF NOT EXISTS idx_machine_runtime_logs_task_id ON machine_runtime_logs(task_id);

-- 2. Create User Work Logs Table
CREATE TABLE IF NOT EXISTS user_work_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    task_id VARCHAR REFERENCES tasks(id),
    machine_id VARCHAR REFERENCES machines(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_work_logs_date ON user_work_logs(date);
CREATE INDEX IF NOT EXISTS idx_user_work_logs_user_id ON user_work_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_work_logs_task_id ON user_work_logs(task_id);

COMMIT;
