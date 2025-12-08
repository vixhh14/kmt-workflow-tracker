# Deployment Fix Guide - KMT Workflow Tracker

## 🛠 Fix Summary

### Issues Identified & Fixed:

1. **URL Mismatch Fixed**: Frontend now consistently uses `https://kmt-workflow-backend.onrender.com`
2. **CORS Configuration Fixed**: Backend now uses centralized CORS config with all necessary origins
3. **Preview URL Support**: Added Vercel preview URL to CORS whitelist
4. **Keep-Alive**: Backend already has `/health` endpoint for monitoring services

---

## ⚙️ Deployment Steps

### Step 1: Deploy Backend to Render

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "fix: CORS configuration and API setup"
   git push origin main
   ```

2. **In Render Dashboard** (https://dashboard.render.com):
   - Go to your backend service
   - Check that the service name matches: `kmt-workflow-backend`
   - Verify your live URL is: `https://kmt-workflow-backend.onrender.com`
   - If URL is different, update all files accordingly

3. **Set Environment Variables in Render**:
   ```
   DATABASE_URL=sqlite:///./workflow.db
   SECRET_KEY=<your-secret-key>
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

4. **Redeploy** the service (Manual Deploy or push to trigger auto-deploy)

5. **Test the backend**:
   - Visit: `https://kmt-workflow-backend.onrender.com/health`
   - Should return: `{"status": "ok"}`

---

### Step 2: Deploy Frontend to Vercel

1. **In Vercel Dashboard** (https://vercel.com/dashboard):
   - Go to your project: `kmt-workflow-tracker`
   - Navigate to **Settings** → **Environment Variables**

2. **Add/Update Environment Variable**:
   ```
   Name: VITE_API_URL
   Value: https://kmt-workflow-backend.onrender.com
   Environments: ✅ Production, ✅ Preview, ✅ Development
   ```

3. **Clear Build Cache & Redeploy**:
   - Go to **Deployments** tab
   - Click the **...** menu on the latest deployment
   - Select **Redeploy**
   - ✅ Check "Clear Build Cache"
   - Click **Redeploy**

4. **Wait for deployment** to complete (usually 1-2 minutes)

---

### Step 3: Set Up Keep-Alive (Prevent Render Sleep)

Free-tier Render services sleep after 15 minutes of inactivity.

**Option A: Use UptimeRobot (Free)**
1. Go to https://uptimerobot.com and create account
2. Add New Monitor:
   - Monitor Type: HTTP(s)
   - Friendly Name: KMT Backend
   - URL: `https://kmt-workflow-backend.onrender.com/health`
   - Monitoring Interval: 5 minutes
3. Save monitor

**Option B: Use cron-job.org (Free)**
1. Go to https://cron-job.org and create account
2. Create new cron job:
   - URL: `https://kmt-workflow-backend.onrender.com/health`
   - Schedule: Every 10 minutes
3. Save and enable

---

## 📋 Environment Variables Reference

### Frontend (.env / Vercel Dashboard)
```env
VITE_API_URL=https://kmt-workflow-backend.onrender.com
```

### Backend (.env / Render Dashboard)
```env
DATABASE_URL=sqlite:///./workflow.db
SECRET_KEY=<generate-secure-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BACKEND_CORS_ORIGINS=https://kmt-workflow-tracker.vercel.app,http://localhost:3000,http://localhost:5173
```

---

## 🧪 Testing Checklist

### After Deployment, verify:

- [ ] **Backend Health Check**
  - Visit: `https://kmt-workflow-backend.onrender.com/health`
  - Expected: `{"status": "ok"}`

- [ ] **Backend Root Endpoint**
  - Visit: `https://kmt-workflow-backend.onrender.com/`
  - Expected: `{"message": "Workflow Tracker API running", "version": "1.0.0", "status": "healthy"}`

- [ ] **Frontend Loads**
  - Visit: `https://kmt-workflow-tracker.vercel.app`
  - Expected: Login page displays without console errors

- [ ] **Login Works**
  - Open browser DevTools (F12) → Network tab
  - Try logging in with demo credentials
  - Check that request goes to `https://kmt-workflow-backend.onrender.com/auth/login`
  - No CORS errors in Console tab

- [ ] **Console Check**
  - Open DevTools → Console
  - Should see:
    ```
    🚀 API Service Initialized
    📍 Mode: production
    🔗 Base URL: https://kmt-workflow-backend.onrender.com
    ```

- [ ] **Test from Mobile/Different Network**
  - Access the app from your phone or different device
  - Login should work without issues

---

## 🔧 Troubleshooting

### "Cannot connect to server" Error:
1. Check if backend is awake: visit `/health` endpoint
2. Wait 30-60 seconds (Render cold start)
3. Check browser console for specific error

### CORS Error:
1. Verify the frontend URL is in CORS whitelist
2. Check `config.py` includes your Vercel URL
3. Redeploy backend after CORS changes

### 404 on Login:
1. Check the request URL in Network tab
2. Verify `VITE_API_URL` is set correctly
3. Ensure no trailing slash in the URL

### Render Backend Sleeping:
1. Set up keep-alive monitoring (see Step 3)
2. First request after sleep takes 30-60 seconds
3. Consider upgrading to paid tier for always-on

---

## 📝 Files Changed

1. `frontend/src/api/axios.js` - Consistent API URL configuration
2. `frontend/.env` - Updated backend URL
3. `frontend/.env.production` - Production environment template
4. `backend/app/main.py` - Fixed CORS to use centralized config
5. `backend/app/core/config.py` - Added all required CORS origins
