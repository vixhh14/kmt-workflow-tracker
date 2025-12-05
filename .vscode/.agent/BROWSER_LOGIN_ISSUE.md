# Browser Login Issue - Troubleshooting Guide

## Issue: Cannot log into non-admin dashboards in Antigravity extended browser

## Possible Causes & Solutions

### 1. LocalStorage Issues
**Problem:** Extended browser might have restrictions on localStorage
**Solution:** Add fallback authentication

```javascript
// Check if localStorage is working
try {
    localStorage.setItem('test', '1');
    localStorage.removeItem('test');
    console.log('✅ LocalStorage available');
} catch (e) {
    console.error('❌ LocalStorage blocked:', e);
}
```

### 2. CORS or Cookie Issues
**Problem:** Browser security settings blocking cross-origin requests
**Solution:** Already configured in backend, but verify:

```python
# backend/app/main.py (lines 36-42)
allow_origins=["http://localhost:5173", "https://kmt-workflow-tracker-qayt.vercel.app"]
allow_credentials=True
```

### 3. Navigation/Routing Problem
**Problem:** Role-based routing might not be working correctly
**Debug:** Add console logging to Dashboard.jsx

```javascript
// frontend/src/pages/Dashboard.jsx
console.log('Current user:', user);
console.log('User role:', user?.role);
console.log('Redirecting to:', `/dashboard/${user.role}`);
```

### 4. Token Expiration or Invalid Format
**Problem:** JWT token might be malformed or expired
**Debug:** Check token in browser:

```javascript
// In browser console
const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user'));
console.log('Token:', token);
console.log('User:', user);
```

## Quick Fix: Test in Incognito/Private Mode

1. Open an incognito/private window
2. Navigate to the application
3. Try logging in as different users
4. Check if it works

## Manual Testing Steps

### Test each role:
1. **Admin**: username: `admin`, password: `admin123`
2. **Operator**: Create test user or use existing
3. **Supervisor**: Create test user or use existing
4. **Planning**: Create test user or use existing

### For each role, verify:
- [ ] Login succeeds
- [ ] Correct dashboard redirects
- [ ] No "unauthorized" errors
- [ ] Navigation items are correct for role
- [ ] Can access allowed pages
- [ ] Cannot access restricted pages

## Browser-Specific Fix

If the issue persists only in Antigravity extended browser:

### Option 1: Clear All Browser Data
1. Open browser settings
2. Clear all cookies, cache, and localStorage
3. Restart browser
4. Try logging in again

### Option 2: Disable Extensions
1. Disable all browser extensions
2. Restart browser
3. Try logging in again

### Option 3: Use Different Browser
- Test in Chrome, Firefox, or Edge
- If it works there, the issue is browser-specific

## Emergency Workaround: Direct URL Access

If login works but redirect fails, manually navigate to:
- Admin: `https://kmt-workflow-tracker-qayt.vercel.app/dashboard/admin`
- Operator: `https://kmt-workflow-tracker-qayt.vercel.app/dashboard/operator`
- Supervisor: `https://kmt-workflow-tracker-qayt.vercel.app/dashboard/supervisor`
- Planning: `https://kmt-workflow-tracker-qayt.vercel.app/dashboard/planning`

## Check Backend Logs

If using Render, check logs for authentication errors:
1. Go to https://dashboard.render.com/
2. Click your backend service
3. Click "Logs"
4. Look for login attempts and any errors

## Next Steps

If none of the above work:
1. Test in a different browser
2. Check if localStorage is blocked by browser policy
3. Verify the backend is returning correct user role
4. Check network tab for failed requests
