-- Create machine_runtime_logs table
CREATE TABLE IF NOT EXISTS machine_runtime_logs (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR NOT NULL REFERENCES machines(id),
    task_id VARCHAR NOT NULL REFERENCES tasks(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'Asia/Kolkata')
);

-- Create user_work_logs table
CREATE TABLE IF NOT EXISTS user_work_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    task_id VARCHAR NOT NULL REFERENCES tasks(id),
    machine_id VARCHAR REFERENCES machines(id), -- Nullable in case task has no machine
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'Asia/Kolkata')
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS ix_machine_runtime_logs_date ON machine_runtime_logs (date);
CREATE INDEX IF NOT EXISTS ix_machine_runtime_logs_machine_id ON machine_runtime_logs (machine_id);
CREATE INDEX IF NOT EXISTS ix_machine_runtime_logs_task_id ON machine_runtime_logs (task_id);

CREATE INDEX IF NOT EXISTS ix_user_work_logs_date ON user_work_logs (date);
CREATE INDEX IF NOT EXISTS ix_user_work_logs_user_id ON user_work_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_user_work_logs_task_id ON user_work_logs (task_id);
