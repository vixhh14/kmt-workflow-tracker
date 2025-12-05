# 🚀 DEPLOYMENT CHECKLIST - Production Fix

## ✅ Files Changed

### Frontend:
- ✅ `frontend/src/api/axios.js` - **CRITICAL**: Updated to handle VITE_API_URL robustly.
- ✅ `frontend/src/pages/Login.jsx` - Added "Server Waking Up" warning and better error handling.
- ✅ `frontend/src/components/ProtectedRoute.jsx` - Added proper loading spinner.
- ✅ `frontend/vercel.json` - Fixed rewrite rule for SPA routing (`/index.html`).

### Backend:
- ✅ `backend/app/core/config.py` - Updated CORS origins to include localhost and Vercel domains.

## 📋 PRE-DEPLOYMENT STEPS

### 1. Verify Environment Variables

**Vercel (Frontend):**
- Go to: https://vercel.com/your-project/settings/environment-variables
- Ensure: `VITE_API_URL` is set to your Render Backend URL (e.g., `https://kmt-workflow-backend.onrender.com`)
- **IMPORTANT**: Do NOT include a trailing slash `/` at the end.

**Render (Backend):**
- Go to: https://dashboard.render.com/your-service/env
- Ensure: `BACKEND_CORS_ORIGINS` includes your Vercel URL.
- Example: `http://localhost:5173,https://kmt-workflow-tracker-qayt.vercel.app,https://your-custom-domain.com`

## 🚀 DEPLOYMENT ORDER

### Step 1: Deploy Backend FIRST ⚠️
```bash
# Commit backend changes
git add backend/
git commit -m "fix: Update CORS settings for production"
git push

# Wait for Render to deploy (check logs)
# Test: curl https://kmt-workflow-backend.onrender.com/health
# Should return: {"status":"ok"}
```

### Step 2: Deploy Frontend SECOND
```bash
# Commit frontend changes
git add frontend/
git commit -m "fix: Update API URL handling, Login UX, and Vercel routing"
git push

# Vercel will auto-deploy
```

### Step 3: Clear Vercel Build Cache (If needed)
1. Go to Vercel Dashboard
2. Settings → General
3. Click "Clear Build Cache & Redeploy" if you see old cached behavior.

## 🧪 VERIFICATION STEPS

### 1. Backend Health Check
```bash
# Test backend is running
curl https://kmt-workflow-backend.onrender.com/health
# Expected: {"status":"ok"}
```

### 2. Frontend Login Test
1. Open your Vercel URL.
2. Open DevTools (F12) -> Console.
3. You should see: `🚀 API Service Initialized` and `🔗 Base URL: ...`
4. Try to login.
5. If the backend is sleeping, you should see the "Server Waking Up..." message.

## 🐛 TROUBLESHOOTING

### Issue: 404 on Login
- Check `VITE_API_URL` in Vercel.
- Check Network tab in DevTools to see the request URL.

### Issue: CORS Error
- Check `BACKEND_CORS_ORIGINS` in Render.
- Ensure your Vercel URL matches exactly (https vs http, trailing slash).

### Issue: 404 on Refresh
- This is fixed by the `vercel.json` update. If it persists, check Vercel settings.

---

**Last Updated:** 2025-12-03
**Status:** Ready for deployment
