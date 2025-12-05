# 🚀 Production Deployment Guide

## Today's Changes Summary

### Backend Changes (API Server on Render)
1. ✅ **New Subtask Model** (`backend/app/models/models_db.py`)
   - Added `Subtask` table with fields: id, task_id, title, status, notes, timestamps

2. ✅ **New Subtasks Router** (`backend/app/routers/subtasks_router.py`)
   - `GET /subtasks/{task_id}` - Get all subtasks for a task
   - `POST /subtasks/` - Create subtask (admin/planning/supervisor only)
   - `PUT /subtasks/{subtask_id}` - Update status & notes (admin/planning/supervisor only)
   - `DELETE /subtasks/{subtask_id}` - Delete subtask (admin/planning/supervisor only)

3. ✅ **Updated Dependencies** (`backend/app/core/dependencies.py`)
   - Added `get_current_active_user()` function
   - Fixed authentication flow

4. ✅ **Registered Router** (`backend/app/main.py`)
   - Added subtasks_router to the application

### Frontend Changes (UI on Vercel)
1. ✅ **New Subtask Component** (`frontend/src/components/Subtask.jsx`)
   - Role-based UI (operators see read-only, others can edit)
   - Inline editing with status dropdown and notes textarea
   - Responsive design with Tailwind CSS

2. ✅ **Updated Services** (`frontend/src/api/services.js`)
   - Added subtask API endpoints

3. ✅ **Updated Tasks Page** (`frontend/src/pages/Tasks.jsx`)
   - Added expand/collapse for subtasks
   - Integrated Subtask component

4. ✅ **Updated Operator Dashboard** (`frontend/src/pages/dashboards/OperatorDashboard.jsx`)
   - Added subtask viewing capability

5. ✅ **Fixed Navigation** (`frontend/src/components/Layout.jsx`)
   - Users tab now visible for planning role

---

## 📋 Deployment Steps

### Step 1: Commit and Push Changes

```bash
# Check what's changed
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add subtask feature with role-based permissions and fix planning navigation"

# Push to main branch
git push origin main
```

### Step 2: Deploy Frontend to Vercel

**Option A: Automatic (if GitHub integration is enabled)**
- Vercel will automatically detect the push
- Build will start automatically
- Wait 2-3 minutes for completion
- Check: https://kmt-workflow-tracker-qayt.vercel.app/

**Option B: Manual via Vercel Dashboard**
1. Go to: https://vercel.com/dashboard
2. Find your project: `kmt-workflow-tracker`
3. Click **"Deployments"** tab
4. Click **"Redeploy"** button
5. Select latest commit
6. Click **"Redeploy"**

**Option C: Vercel CLI**
```bash
cd frontend
vercel --prod
```

### Step 3: Deploy Backend to Render

**Important: Database Migration Required!**

Since we added a new `Subtask` model, the database schema needs to be updated.

**Option A: Automatic Deployment**
1. Go to: https://dashboard.render.com/
2. Find your backend service
3. If connected to Git, it should auto-deploy after push
4. Click **"Manual Deploy"** > **"Deploy latest commit"** if needed

**Option B: Run Migration on Render**

After deployment, you need to create the new table:

1. Go to Render Dashboard
2. Click on your backend service
3. Go to **"Shell"** tab
4. Run:
   ```bash
   python
   ```
   Then:
   ```python
   from app.core.database import engine, Base
   from app.models.models_db import Subtask
   Base.metadata.create_all(bind=engine)
   exit()
   ```

**OR** 

If you have a migration script:
```bash
cd backend
python -c "from app.core.database import Base, engine; from app.models.models_db import Subtask; Base.metadata.create_all(bind=engine)"
```

### Step 4: Verify Deployment

**Frontend Checks:**
1. ✅ Navigate to: https://kmt-workflow-tracker-qayt.vercel.app/
2. ✅ Log in as planning user
3. ✅ Check if "Users" tab appears in sidebar
4. ✅ Go to Tasks page
5. ✅ Click chevron icon to expand a task
6. ✅ Verify subtasks section appears

**Backend Checks:**
1. ✅ Test API: `GET https://your-backend.onrender.com/subtasks/{task_id}`
2. ✅ Check logs for any errors
3. ✅ Verify database table was created

**Role-Based Testing:**
- **As Operator**: Should see subtasks (read-only, no edit controls)
- **As Planning**: Should see subtasks with edit controls
- **As Supervisor**: Should see subtasks with edit controls
- **As Admin**: Should see subtasks with edit controls + Users tab

---

## 🔧 Troubleshooting

### Frontend Not Updating
1. Clear browser cache: `Ctrl + Shift + Delete`
2. Hard refresh: `Ctrl + Shift + R`
3. Clear localStorage and login again
4. Check Vercel build logs for errors

### Backend Not Working
1. Check Render deployment logs
2. Verify environment variables are set
3. Check if database migration ran successfully
4. Test API endpoints with Postman/curl

### Database Issues
If subtasks endpoint returns 500 error:
- The `subtasks` table might not exist
- Run the migration command in Render Shell
- Check backend logs for SQL errors

---

## ✅ Expected Behavior After Deployment

1. **All Users**:
   - Can expand/collapse tasks to view subtasks
   - See subtask title, status badges, and notes

2. **Operators**:
   - Read-only view of subtasks
   - No edit buttons, no add form
   - Status shown as colored badges
   - Notes shown in read-only container

3. **Admin/Planning/Supervisor**:
   - Can add new subtasks
   - Can edit status (dropdown)
   - Can edit notes (textarea)
   - Can delete subtasks
   - Save button for each subtask

4. **Planning Users Specifically**:
   - Now see "Users" tab in navigation (previously missing)
   - Can access /workflow-tracker page

---

## 📞 Need Help?

If deployment fails or features don't work as expected:
1. Check browser console for errors (F12)
2. Check Render logs for backend errors
3. Verify environment variables match between local and production
4. Test API endpoints directly to isolate frontend vs backend issues

**Backend URL:** Check your Render dashboard for the exact URL
**Frontend URL:** https://kmt-workflow-tracker-qayt.vercel.app/
