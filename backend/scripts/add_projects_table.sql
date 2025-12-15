-- Add Projects Table
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR PRIMARY KEY,
    project_name VARCHAR NOT NULL,
    work_order_number VARCHAR,
    client_name VARCHAR,
    project_code VARCHAR UNIQUE,
    created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'Asia/Kolkata')
);

CREATE INDEX IF NOT EXISTS ix_projects_project_id ON projects (project_id);
CREATE INDEX IF NOT EXISTS ix_projects_project_name ON projects (project_name);
CREATE INDEX IF NOT EXISTS ix_projects_project_code ON projects (project_code);

-- Add Project FK to Tasks
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS project_id VARCHAR;

-- Note: We are not enforcing FK constraint strictly on existing data immediately to avoid errors if bad data exists, 
-- but ideally we should. Since 'tasks' might have 'project' string column, we leave it nullable.
-- Attempt to add constraint:
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_tasks_project_id'
    ) THEN
        ALTER TABLE tasks 
        ADD CONSTRAINT fk_tasks_project_id 
        FOREIGN KEY (project_id) 
        REFERENCES projects (project_id) 
        ON DELETE SET NULL;
    END IF;
END $$;
