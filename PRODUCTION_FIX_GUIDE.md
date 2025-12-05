# 🚨 PRODUCTION DEPLOYMENT FIX - Complete Guide

## 🔍 ROOT CAUSE ANALYSIS

I've identified **MULTIPLE CRITICAL ISSUES** causing your blank white screen and 404 errors:

### 1. **DUPLICATE API CONFIGURATION FILES** ❌
- You have TWO axios instances: `api/api.js` and `api/axios.js`
- `Login.jsx` imports from `api/api.js` (line 3)
- `services.js` imports from `api/axios.js` (line 1)
- **`api/api.js` doesn't strip trailing slashes** and has NO fallback URL!

### 2. **MISSING TRAILING SLASH HANDLING** ❌
- `api/api.js` uses `import.meta.env.VITE_API_URL` directly without fallback
- If env var is undefined, baseURL becomes `undefined`
- This causes requests to go to relative paths on Vercel, resulting in 404

### 3. **NO ERROR BOUNDARIES** ❌
- When API calls fail, React components throw unhandled errors
- This causes the entire app to crash → **blank white screen**
- No user-friendly error messages

### 4. **INCONSISTENT ROUTE PATHS** ⚠️
- Backend routes have NO trailing slashes (e.g., `/auth/login`)
- Frontend services.js has NO trailing slashes ✅ (correct)
- But Login.jsx uses the broken `api.js` file

### 5. **MISSING /api PREFIX CHECK** ⚠️
- Your Render deployment might be adding `/api` prefix
- Need to verify if routes are `/auth/login` or `/api/auth/login`

---

## ✔️ EXACT CHANGES TO MAKE

### Fix Strategy:
1. **Consolidate to ONE axios instance** (`axios.js`)
2. **Add proper error handling** to prevent white screens
3. **Add error boundaries** for React components
4. **Fix all imports** to use the correct axios instance
5. **Add response interceptor** for global error handling

---

## 🛠️ UPDATED CODE

### 1. **frontend/src/api/axios.js** (CORRECTED)

```javascript
import axios from 'axios';

// Read environment variable with proper fallback
const BASE_URL = (import.meta.env.VITE_API_URL || 'https://kmt-workflow-backend.onrender.com').replace(/\/$/, '');

console.log('🔧 API Configuration:');
console.log('  - VITE_API_URL:', import.meta.env.VITE_API_URL);
console.log('  - Final BASE_URL:', BASE_URL);

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor - attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`📤 ${config.method.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - global error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ ${response.config.method.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error(`❌ ${error.config?.method?.toUpperCase()} ${error.config?.url} - ${error.response.status}`, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('❌ No response from server:', error.message);
    } else {
      // Something else happened
      console.error('❌ Request error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 2. **frontend/src/api/services.js** (NO CHANGES NEEDED - Already correct!)

Your services.js is already correct. Keep it as is.

### 3. **DELETE frontend/src/api/api.js** ❌

This file should be DELETED. It's causing conflicts.

### 4. **frontend/src/pages/Login.jsx** (FIXED IMPORT + ERROR HANDLING)

```javascript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/services'; // CHANGED: Use services instead of api
import { User, Lock, LogIn, Eye, EyeOff, AlertCircle } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    console.log('🔍 Attempting login with:', username);

    try {
      // Use the login service from services.js
      const response = await login({ username, password });

      console.log('✅ Login success:', response.data);

      // Store token and user data
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      // Redirect based on role
      const role = response.data.user.role;
      const dashboardRoutes = {
        admin: '/dashboard/admin',
        operator: '/dashboard/operator',
        supervisor: '/dashboard/supervisor',
        planning: '/dashboard/planning',
      };

      window.location.href = dashboardRoutes[role] || '/';
    } catch (err) {
      console.error('❌ Login failed:', err);

      // Handle different error scenarios
      let errorMessage = 'An unexpected error occurred. Please try again.';

      if (err.response) {
        // Server responded with error
        errorMessage = err.response.data?.detail || `Server error: ${err.response.status}`;
      } else if (err.request) {
        // Request made but no response
        errorMessage = 'Cannot connect to server. Please check your internet connection.';
      } else {
        // Something else happened
        errorMessage = err.message || 'Request failed. Please try again.';
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <LogIn className="text-blue-600" size={32} />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome Back</h1>
          <p className="text-gray-600 mt-2">Sign in to your account</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg">
            <div className="flex items-start">
              <AlertCircle className="text-red-500 mt-0.5 mr-3 flex-shrink-0" size={20} />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">Login Failed</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="text-gray-400" size={20} />
              </div>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter username"
                disabled={loading}
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="text-gray-400" size={20} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter password"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                disabled={loading}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            <div className="flex justify-end mt-1">
              <a href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-800">
                Forgot Password?
              </a>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <a href="/signup" className="text-blue-600 hover:text-blue-800 font-semibold">
              Sign Up
            </a>
          </div>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Demo credentials: admin / admin123
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
```

### 5. **frontend/src/components/ErrorBoundary.jsx** (NEW FILE)

```javascript
import React from 'react';
import { AlertTriangle } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('❌ Error Boundary caught error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
            <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
              <AlertTriangle className="text-red-600" size={32} />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">
              Oops! Something went wrong
            </h1>
            <p className="text-gray-600 text-center mb-6">
              The application encountered an unexpected error. Please try refreshing the page.
            </p>
            <div className="space-y-3">
              <button
                onClick={() => window.location.reload()}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                Refresh Page
              </button>
              <button
                onClick={() => window.location.href = '/login'}
                className="w-full bg-gray-200 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
              >
                Go to Login
              </button>
            </div>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-6 p-4 bg-gray-50 rounded-lg">
                <summary className="cursor-pointer text-sm font-medium text-gray-700">
                  Error Details (Dev Only)
                </summary>
                <pre className="mt-2 text-xs text-red-600 overflow-auto">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

### 6. **frontend/src/app.jsx** (ADD ERROR BOUNDARY)

```javascript
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import ErrorBoundary from './components/ErrorBoundary.jsx'; // ADD THIS
import Layout from './components/Layout';
import Login from './pages/Login.jsx';

// ... rest of your imports ...

function App() {
    return (
        <ErrorBoundary> {/* WRAP EVERYTHING */}
            <AuthProvider>
                <Routes>
                    {/* ... all your routes ... */}
                </Routes>
            </AuthProvider>
        </ErrorBoundary>
    );
}

export default App;
```

### 7. **backend/app/main.py** (ADD BETTER LOGGING + ROOT PATH)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    users_router,
    machines_routers,
    tasks_router,
    analytics_router,
    outsource_router,
    auth_router,
    planning_router,
    units_router,
    machine_categories_router,
    user_skills_router,
    approvals_router,
    admin_router,
)
from app.core.config import CORS_ORIGINS
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Workflow Tracker API",
    description="Backend API for KMT Workflow Tracker",
    version="1.0.0",
)

# CORS configuration
print("🔧 CORS Origins:", CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    from create_demo_users import create_demo_users
    try:
        print("🚀 Running startup tasks...")
        create_demo_users()
        print("✅ Startup complete")
    except Exception as e:
        print(f"❌ Error creating demo users: {e}")

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Workflow Tracker API running",
        "version": "1.0.0",
        "status": "healthy"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include routers (NO /api prefix - routes are already prefixed)
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(admin_router.router)
app.include_router(machines_routers.router)
app.include_router(tasks_router.router)
app.include_router(analytics_router.router)
app.include_router(outsource_router.router)
app.include_router(planning_router.router)
app.include_router(units_router.router)
app.include_router(machine_categories_router.router)
app.include_router(user_skills_router.router)
app.include_router(approvals_router.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## 🚀 DEPLOYMENT & REDEPLOY STEPS

### Step 1: Update Frontend Code

```bash
# 1. Delete the broken api.js file
rm frontend/src/api/api.js

# 2. Update axios.js (paste code from above)
# 3. Update Login.jsx (paste code from above)
# 4. Create ErrorBoundary.jsx (paste code from above)
# 5. Update app.jsx to wrap with ErrorBoundary
```

### Step 2: Update Backend Code

```bash
# 1. Update main.py (paste code from above)
```

### Step 3: Set Environment Variables

**On Vercel:**
```
VITE_API_URL=https://kmt-workflow-backend.onrender.com
```

**On Render:**
```
BACKEND_CORS_ORIGINS=http://localhost:5173,https://kmt-workflow-tracker-qayt.vercel.app
```

### Step 4: Deploy in Correct Order

```bash
# 1. Deploy Backend FIRST
git add backend/
git commit -m "fix: Add better logging and CORS configuration"
git push

# Wait for Render to deploy (check https://kmt-workflow-backend.onrender.com/health)

# 2. Deploy Frontend SECOND
git add frontend/
git commit -m "fix: Consolidate axios, add error handling, fix imports"
git push

# Vercel will auto-deploy

# 3. Clear Vercel build cache (in Vercel dashboard)
# Settings → General → Clear Build Cache & Redeploy
```

---

## 🧪 FINAL VERIFICATION CHECKLIST

### 1. **Backend Health Check**
```bash
# Test backend is running
curl https://kmt-workflow-backend.onrender.com/health
# Should return: {"status":"ok"}

# Test CORS headers
curl -I https://kmt-workflow-backend.onrender.com/
# Should include: Access-Control-Allow-Origin
```

### 2. **Frontend DevTools Check**

Open https://kmt-workflow-tracker-qayt.vercel.app

**Console Tab:**
```
✅ Should see: "🔧 API Configuration:"
✅ Should see: "Final BASE_URL: https://kmt-workflow-backend.onrender.com"
❌ Should NOT see: "undefined" in API URL
```

**Network Tab:**
```
✅ Login request should go to: https://kmt-workflow-backend.onrender.com/auth/login
✅ Status should be: 200 (success) or 401 (wrong password)
❌ Should NOT be: 404 (not found)
```

### 3. **Test Login Flow**

1. Enter username: `admin`
2. Enter password: `admin123`
3. Click "Sign In"

**Expected Results:**
- ✅ No blank white screen
- ✅ Either successful login OR error message displayed
- ✅ Console shows request details
- ✅ Network tab shows request to correct URL

### 4. **Test Error Scenarios**

1. **Wrong password:** Should show error message, NOT blank screen
2. **Network offline:** Should show "Cannot connect" message
3. **Component error:** Should show ErrorBoundary fallback UI

---

## 📊 SUMMARY OF FIXES

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| 404 on login | Duplicate api.js with no fallback URL | Deleted api.js, use axios.js everywhere |
| Blank white screen | Unhandled promise rejections | Added try-catch + ErrorBoundary |
| Undefined baseURL | api.js missing fallback | axios.js has proper fallback |
| Inconsistent imports | Login.jsx using wrong file | Changed to use services.js |
| No error visibility | No error UI | Added error states + AlertCircle icons |
| Hard to debug | No logging | Added console.log throughout |

---

## 🎯 KEY TAKEAWAYS

1. **ONE axios instance** (axios.js) - delete api.js
2. **ALWAYS have fallback** URLs in production
3. **ALWAYS wrap in try-catch** for async calls
4. **ALWAYS use ErrorBoundary** for React apps
5. **ALWAYS test with DevTools** Network tab open

Your app will now:
- ✅ Show error messages instead of blank screens
- ✅ Connect to correct backend URL
- ✅ Have detailed logging for debugging
- ✅ Gracefully handle all error scenarios

**Deploy backend first, then frontend. Clear Vercel cache. Test thoroughly!**
