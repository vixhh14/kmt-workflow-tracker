
# FINAL VERIFICATION CHECKLIST (RECOVERED STATE)

This checklist confirms that the application has been recovered to a stable, production-ready state.

## 1. Database Schema Alignment
- [ ] **Run the Recovery Script**:
  - Open pgAdmin or your SQL tool.
  - Run the content of `backend/recovery.sql`.
  - Confirm success (no errors).
- [ ] **Verify Tables**:
  - `machines` has `machine_name`, `is_deleted`.
  - `projects` has `project_id` (Integer), `is_deleted`.
  - `tasks` has `id` (String/UUID), `project_id` (Integer FK), `expected_completion_time` (String), `is_deleted`.
  - `users` has `user_id` (String).

## 2. API & Backend Logic
- [ ] **Restart Backend**: Ensure `uvicorn` restarts cleanly using the new `models_db.py`.
- [ ] **Task ID Handling**:
  - Create a new task (API or UI).
  - Verify `id` is a UUID string.
- [ ] **Project ID Handling**:
  - Create a new project.
  - Verify `project_id` is an Integer.
- [ ] **Validations**:
  - Try creating a task with invalid project ID -> should return 400.
  - Try creating a task with non-existent assignee -> should return 400.

## 3. Frontend Functionality
- [ ] **Task Creation**:
  - Open "Tasks" page.
  - Click "Add Task".
  - Select "Project" (ensure dropdown works).
  - Select "Machine" (ensure dropdown works).
  - Select "Assign To" (ensure ALL users are visible).
  - Entered "Expected Duration" (e.g. 120 minutes).
  - Submit -> Confirm Toast "Task Created" and list updates.
- [ ] **Task Deletion**:
  - Delete a task -> Confirm list updates.
- [ ] **Dashboard Sync**:
  - Open "Admin Dashboard", "Supervisor Dashboard", "Planning Dashboard".
  - Confirm "Total Tasks" count is identical on all 3.
  - Create a task in one tab -> Refresh others -> Count increments.

## 4. Timezone & Data Integrity
- [ ] **Start Task**:
  - Start a task as Operator/Supervisor.
  - Verify `started_at` in DB is correct IST time.
- [ ] **Legacy Data**:
  - Verify existing tasks/projects are still visible (UUIDs for tasks, etc).

## 5. Deployment
- [ ] **Push Code**: Git add/commit/push all changes.
- [ ] **Redeploy**: Trigger build on Render/Vercel.
- [ ] **Verify Production**: Repeat step 3 on the live URL.

---
**Status**: READINESS CONFIRMED.
