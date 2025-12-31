-- NORMALIZE_DATA_AND_ROLES.SQL
-- Senior Engineer: Ensuring data consistency and role normalization

-- 1. Ensure all standard entities are active and visible
UPDATE projects SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE machines SET is_deleted = false WHERE is_deleted IS NULL;
UPDATE users SET is_deleted = false WHERE is_deleted IS NULL;

-- 2. Activate all machines (default to active if status is null)
UPDATE machines SET status = 'active' WHERE status IS NULL;

-- 3. Normalize roles to lowercase
UPDATE users SET role = LOWER(role);

-- 4. Verify/Fix critical roles (Ensure they exist in lowercase)
-- Admin, Supervisor, Planning, Operator, Fab_Master, File_Master
-- No changes needed if they are already standard.

COMMIT;
