# Navigation Debug Guide

## Issue: Users Tab Not Visible for Planning Role

### Current Configuration ✅

**Layout.jsx (Lines 24-27)**:
```javascript
...(user?.role === 'admin' || user?.role === 'planning'
    ? [{ path: '/workflow-tracker', label: 'Users', icon: Users }]
    : []),
```

**App.jsx (Line 65)**:
```javascript
<Route path="workflow-tracker" element={
    <ProtectedRoute allowedRoles={['admin', 'planning']}>
        <WorkflowTracker />
    </ProtectedRoute>
} />
```

### Expected Behavior
- ✅ Admin users should see "Users" tab
- ✅ Planning users should see "Users" tab
- ❌ Operator users should NOT see "Users" tab
- ❌ Supervisor users should NOT see "Users" tab

### Troubleshooting Steps

1. **Clear Browser Cache**:
   - Press `Ctrl + Shift + Delete`
   - Clear cached images and files
   - Reload the application

2. **Check User Role in Console**:
   - Open browser DevTools (F12)
   - Go to Console tab
   - Type: `localStorage.getItem('user')`
   - Verify the role is 'planning'

3. **Force Logout and Login**:
   - Log out completely
   - Close all browser tabs
   - Open a new tab
   - Log in with planning credentials

4. **Verify JWT Token**:
   - In DevTools Console, type:
     ```javascript
     JSON.parse(localStorage.getItem('user'))
     ```
   - Check if `role` field shows 'planning'

5. **Check for JavaScript Errors**:
   - Open DevTools Console
   - Look for any red error messages
   - Refresh the page and check again

### Manual Verification

If the issue persists, manually verify by:

1. **Add Debug Logging** to Layout.jsx:
   ```javascript
   console.log('Current user role:', user?.role);
   console.log('Nav items:', navItems);
   ```

2. **Check Route Access**:
   - Manually navigate to: `http://localhost:5173/workflow-tracker`
   - If it loads, the route is working
   - If redirected to unauthorized, there's a permission issue

### Possible Causes

1. ✅ **Configuration is correct** - The code already allows planning users
2. ⚠️ **Cached user data** - Old user object in localStorage
3. ⚠️ **Token not refreshed** - User logged in before role was updated
4. ⚠️ **Role mismatch** - User's role in database is not 'planning'

### Quick Fix

If you need immediate access, you can:

1. **Temporarily allow all roles** (for testing):
   ```javascript
   // In Layout.jsx, change line 25 to:
   ...(user?.role ? [{ path: '/workflow-tracker', label: 'Users', icon: Users }] : []),
   ```

2. **After testing, revert back to**:
   ```javascript
   ...(user?.role === 'admin' || user?.role === 'planning'
       ? [{ path: '/workflow-tracker', label: 'Users', icon: Users }]
       : []),
   ```

### Next Steps

If the issue persists after trying the above:
1. Share a screenshot of the sidebar when logged in as planning user
2. Share the output of `localStorage.getItem('user')` from the console
3. Check the database to confirm the user's role is set to 'planning'
