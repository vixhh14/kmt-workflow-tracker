# Git Commands for Deployment

## Step 1: Commit All Changes

```bash
# Navigate to project root
cd d:\KMT\workflow_tracker2

# Add all changes
git add .

# Commit with message
git commit -m "Add subtask feature with role-based permissions and fix navigation"

# Push to remote repository
git push origin main
```

## Step 2: Frontend Deployment (Vercel)

**If Vercel is connected to your Git repository:**
- Just push to main branch (Step 1 above)
- Vercel will automatically detect and deploy
- Wait 2-3 minutes
- Check: https://kmt-workflow-tracker-qayt.vercel.app/

**If you need manual deployment:**
```bash
# Navigate to frontend folder
cd frontend

# Deploy to Vercel (requires Vercel CLI installed)
vercel --prod
```

## Step 3: Backend Deployment (Render)

**If Render is connected to your Git repository:**
- Just push to main branch (Step 1 above)
- Render will automatically detect and deploy
- Wait 3-5 minutes
- Check deployment logs in Render dashboard

**After backend deploys, run database migration:**

1. Go to Render Dashboard: https://dashboard.render.com/
2. Click on your backend service
3. Go to "Shell" tab
4. Run this command:

```bash
python -c "from app.core.database import Base, engine; from app.models.models_db import Subtask; Base.metadata.create_all(bind=engine)"
```

## Alternative: Run Git Commands in Sequence

```bash
# From project root
git add .
git commit -m "Add subtask feature and fix navigation"
git push origin main
```

## Verify Deployment

**Frontend (Vercel):**
```bash
# Check Vercel deployment status
vercel ls

# Or visit dashboard
# https://vercel.com/dashboard
```

**Backend (Render):**
- Visit: https://dashboard.render.com/
- Check "Events" tab for deployment status
- Check "Logs" tab for any errors

## If Git Push Requires Authentication

If prompted for credentials:
```bash
# Set up credential helper (one-time setup)
git config --global credential.helper wincred

# Then push again
git push origin main
```

## Quick Deployment Checklist

- [ ] Run `git add .`
- [ ] Run `git commit -m "message"`
- [ ] Run `git push origin main`
- [ ] Wait for Vercel auto-deployment (2-3 min)
- [ ] Wait for Render auto-deployment (3-5 min)
- [ ] Run database migration on Render Shell
- [ ] Test frontend: https://kmt-workflow-tracker-qayt.vercel.app/
- [ ] Clear browser cache and test
- [ ] Log in as different roles to verify permissions

## Testing Commands

**Test if changes are committed:**
```bash
git status
git log --oneline -5
```

**Test if push succeeded:**
```bash
git log origin/main -1
```
