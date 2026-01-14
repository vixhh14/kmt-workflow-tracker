# Final Fix Verification Checklist

## 1. Database Schema Fix (Critical)
- [ ] Run the migration script on the live database:
  ```sql
  -- Run content of backend/fix_schema.sql via Render Dashboard or psql
  ALTER TABLE tasks DROP COLUMN IF EXISTS expected_completion_time;
  ALTER TABLE tasks ADD COLUMN expected_completion_time INTEGER;
  ```
- [ ] Verify `expected_completion_time` is now an INTEGER column.

## 2. Backend Deployment
- [ ] Push changes to GitHub:
  - `backend/app/models/models_db.py` (Column type updated)
  - `backend/app/schemas/task_schema.py` (Pydantic type updated to int)
  - `backend/app/routers/tasks_router.py` (Logic updated)
- [ ] Wait for Render to build and deploy.
- [ ] Verify logs show no startup errors.

## 3. Frontend Deployment
- [ ] Push changes to GitHub:
  - `frontend/src/pages/dashboards/AdminDashboard.jsx` (StatCard fixed)
  - `frontend/src/pages/Tasks.jsx` (Already fixed locally to send Minutes as number)
- [ ] Wait for Vercel to rebuild.

## 4. Functional Testing
- [ ] **Task Creation**: Go to "Tasks" page. Create a new task. Enter "100" in "Expected Duration (Minutes)". Click Create. Success?
- [ ] **Admin Dashboard**: Load Admin Dashboard.
  - Fix: Check if "ReferenceError: StatCard is not defined" is gone.
  - Verify "Total Projects" matches Planning Dashboard.
- [ ] **Supervisor Dashboard**: Verify "Overall Task Statistics" -> "Total Tasks" logic matches Overview.
- [ ] **Timezone**: Start a task. Check DB `started_at` is in IST (approx +5:30 from UTC).

## 5. Unified Analytics
- [ ] Verified that Admin, Planning, and Supervisor dashboards all consume `getProjectOverviewStats` for the "Total Projects" count.

**Status**: Ready for Deployment.
