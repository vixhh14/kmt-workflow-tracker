# Deployment Fix Instructions

## 1. Apply SQL Fixes
Since the backend cannot directly execute DDL on the remote database due to network restrictions, you must run the fix script.

**Option A: Run via Render Shell (Recommended)**
1. Go to your Render Dashboard -> Select the Backend Service -> "Shell" tab.
2. Run the following command:
   ```bash
   python backend/fix_attendance_db.py
   ```
   *This will connect to the local database (localhost inside Render) and apply the fixes.*

**Option B: Run via SQL Client**
If you have an external connection string, run these SQL commands:
```sql
-- 1. Drop default (detach old sequence)
ALTER TABLE attendance ALTER COLUMN id DROP DEFAULT;

-- 2. Drop PK
ALTER TABLE attendance DROP CONSTRAINT IF EXISTS attendance_pkey;

-- 3. Create sequence
CREATE SEQUENCE IF NOT EXISTS attendance_id_seq;

-- 4. Change to BigInt
ALTER TABLE attendance ALTER COLUMN id TYPE BIGINT;

-- 5. Set default
ALTER TABLE attendance ALTER COLUMN id SET DEFAULT nextval('attendance_id_seq');

-- 6. Sync sequence
SELECT setval('attendance_id_seq', (SELECT COALESCE(MAX(id), 0) FROM attendance) + 1, false);

-- 7. Restore PK
ALTER TABLE attendance ADD PRIMARY KEY (id);
```

## 2. Update Backend Code
The backend code has already been updated locally:
- `backend/app/models/models_db.py`: Updated `Attendance` model to use `BigInteger` and `autoincrement=True`.
- `backend/fix_attendance_db.py`: Created the fix script.

## 3. Push to GitHub
Run the following commands to push the changes:
```bash
git add backend/app/models/models_db.py backend/fix_attendance_db.py
git commit -m "Fix attendance table: BigInteger ID + AutoIncrement"
git push
```

## 4. Redeploy on Render
1. The push should trigger an automatic deployment.
2. Watch the deployment logs.
3. Once "Live", go to the Shell and run the fix script (as described in Step 1).

## 5. Verify Login
1. **Check Backend Logs**: Ensure no `UniqueViolation` errors appear.
2. **Test Login**:
   ```bash
   # Admin
   curl -X POST "https://kmt-backend.onrender.com/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=Admin&password=Admin@Demo2025!"
   ```
3. **Verify Attendance Insert**:
   - The login should succeed (200 OK).
   - The `attendance` table should have a new record with a new ID (e.g., 4, 5, etc.).
