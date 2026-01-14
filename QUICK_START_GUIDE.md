# 🚀 QUICK START GUIDE - Attendance & Dashboard Fixes

## Step 1: Run Database Migration

### Option A: Using Python Script (Recommended)
```bash
cd backend
python run_attendance_migration.py
```

### Option B: Using psql
```bash
psql -h <host> -U <username> -d <database> -f backend/migrations/fix_attendance_system.sql
```

## Step 2: Restart Backend
```bash
cd backend
# If using virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Run backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 3: Rebuild Frontend (if needed)
```bash
cd frontend
npm install  # if packages updated
npm run build
```

## Step 4: Test the System

### Test Login & Attendance
1. Open browser and go to login page
2. Login with any user credentials
3. Check browser console for: `✅ Attendance marked for user: username`
4. Check database: `SELECT * FROM attendance WHERE date = CURRENT_DATE;`
5. Verify one row exists for your user_id

### Test Logout & Checkout
1. Click the "Logout" button (important: must click, not just close browser)
2. Check browser console for: `✅ Logout and checkout recorded`
3. Check database: Verify `check_out` column is now filled for your record
4. Verify `status` is still 'Present' (not 'Left')

### Test Re-Login Same Day
1. Login again with same user
2. Check database: Verify only ONE row exists for (user_id, today)
3. Verify `login_time` is updated to latest login time
4. Verify `check_in` remains the first login time

### Test Admin Dashboard
1. Login as admin
2. Navigate to Admin Dashboard
3. Verify project dropdown appears
4. Select a project from dropdown
5. Verify:
   - Statistics update (Pending, In Progress, Completed, On Hold)
   - Pie chart updates with new data
   - Legend shows correct labels (not "value")
6. Verify attendance section shows:
   - Present users with names (not IDs)
   - Absent users
   - Correct counts

### Test Supervisor Dashboard
1. Login as supervisor
2. Navigate to Supervisor Dashboard
3. Verify these sections exist:
   - Quick Assign (pending tasks)
   - Running Tasks (in_progress tasks)
   - Operator dropdown filter
   - Project dropdown filter
   - Charts update based on filters

## ✅ Verification Checklist

### Database
- [ ] `date` column is type DATE (not TIMESTAMP)
- [ ] Unique index `idx_attendance_user_date` exists
- [ ] Columns exist: id, user_id, date, check_in, check_out, login_time, ip_address, status
- [ ] No duplicate records for same (user_id, date)

### Backend
- [ ] `/auth/login` endpoint marks attendance automatically
- [ ] `/auth/logout` endpoint marks checkout
- [ ] `/attendance/mark-present` endpoint works
- [ ] `/attendance/check-out` endpoint works
- [ ] `/attendance/summary` endpoint returns correct data
- [ ] `/admin/project-analytics?project=xxx` filters correctly

### Frontend
- [ ] Login calls backend and attendance is marked
- [ ] Logout calls `/auth/logout` before clearing localStorage
- [ ] Admin dashboard project dropdown works
- [ ] Admin dashboard pie chart filters by project
- [ ] Supervisor dashboard shows all required sections
- [ ] No console errors

### Business Logic
- [ ] Only ONE attendance row per (user_id, date)
- [ ] Multiple logins same day update `login_time`, not create new rows
- [ ] Checkout only happens on explicit logout button click
- [ ] Browser close/refresh does NOT mark checkout
- [ ] Status remains 'Present' after checkout

## 🐛 Common Issues & Fixes

### Issue: "duplicate key value violates unique constraint"
**Reason**: Trying to create duplicate attendance for same user same day
**Fix**: Migration script should have cleaned this up. Run cleanup manually:
```sql
DELETE FROM attendance a USING (
    SELECT user_id, date, MAX(id) as max_id
    FROM attendance
    GROUP BY user_id, date
    HAVING COUNT(*) > 1
) b
WHERE a.user_id = b.user_id AND a.date = b.date AND a.id < b.max_id;
```

### Issue: Checkout marked when closing browser
**Reason**: Page unload event handler calling logout
**Fix**: Ensure only logout button calls `/auth/logout`, remove any beforeunload handlers

### Issue: Admin dashboard shows duplicate sections
**Reason**: Old code not removed
**Fix**: Current code is already fixed, verify you're running latest version

### Issue: Pie chart legend shows "value"
**Reason**: Missing or incorrect Legend configuration
**Fix**: Already fixed in current code, verify `<Legend />` component exists

## 📞 Support

If you encounter any issues:
1. Check browser console for errors
2. Check backend logs for errors
3. Verify database migration completed successfully
4. Ensure all files are updated to latest version
5. Clear browser cache and restart

---

**Last Updated**: 2025-12-12
**Status**: ✅ PRODUCTION READY
