---
description: Verification steps for Dropdowns and Quick Assign Logic Fixes
---

# Verification Steps

## 1. Dropdowns and Placeholders
Verify that the following dropdowns have correct placeholders (`-- Select X --`) and are disabled/hidden once opened:
- **Tasks Page**:
  - Project
  - Assign To (Should exclude Admin/Planning)
  - Assigned By (Should exclude Operators)
- **Machines Page**:
  - Unit
  - Category
- **Operational Tasks (Filing/Fabrication)**:
  - Project
  - Assign To (Should exclude irrelevant roles)
- **User Approvals**:
  - Unit Assignment

## 2. Quick Assign Logic
- Go to **Supervisor Dashboard** -> **Quick Assign**.
- Select a pending task.
- Click "Assign Task".
- Verify that the button changes to "Assigning..." and is disabled.
- Verify that after success, the modal closes and the task lists updates.
- Verify that no "false error" (Partial Success) popup appears if the assignment was successful. [Note: If an error persists, ensure backend is running correctly].

## 3. Role Filtering
- CHECK `Tasks.jsx` "Assign To": Confirm Admin and Planning users are NOT listed.
- CHECK `Tasks.jsx` "Assigned By": Confirm Operators are NOT listed (only Admin, Supervisor, Planning).

## 4. Run Normalization (Backend)
- Run `python backend/ensure_masters.py` to ensure File/Fab masters exist.
- Run `python backend/run_normalization.py` to fix any database inconsistencies (Machine status, etc).

## 5. Restart Backend
- Recommendation: Restart the backend server to ensure all schema changes and master users are loaded correctly.
