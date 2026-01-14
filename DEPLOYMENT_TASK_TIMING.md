# Deployment Instructions: Task Timing & Performance

## 1. SQL Migration
Since we cannot run migrations automatically on the remote DB, you must apply the following SQL manually.

**Backup Recommendation:**
Before running this, backup your database:
```bash
pg_dump "your_connection_string" > backup_before_timing_fix.sql
```

**Run this SQL (via Render Shell or SQL Client):**
```sql
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
```

## 2. Deployment
The backend code has been updated to use these new tables.
1. Push the changes (Git commands provided below).
2. Render will auto-deploy.
3. **IMPORTANT**: The backend might fail to start or error out on task actions if the SQL migration above is not applied first. Apply the SQL immediately after pushing.

## 3. Verification
1. Login as Operator.
2. Start a task -> Verify `actual_start_time` is set (check DB or API response).
3. Click "Hold Task" -> Select reason -> Verify `task_holds` entry created.
4. Resume Task -> Verify `hold_ended_at` is set.
5. Complete Task -> Verify `actual_end_time` and `total_duration_seconds` are correct.
6. Login as Admin -> Check `/admin/performance` endpoint (or new UI if added) for monthly stats.

## 4. Frontend Changes
- Operator Dashboard:
  - "Deny" button replaced with "Hold Task".
  - Added "Request Reschedule" button.
  - "Tool not available" added to hold reasons.
  - Live timer uses actual start times.
