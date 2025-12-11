import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { User, Lock, LogIn, Eye, EyeOff, AlertCircle, Server } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth(); // Use login from context
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showColdStartWarning, setShowColdStartWarning] = useState(false);

  useEffect(() => {
    let timer;
    if (loading) {
      // If loading takes more than 3 seconds, show cold start warning
      timer = setTimeout(() => {
        setShowColdStartWarning(true);
      }, 3000);
    } else {
      setShowColdStartWarning(false);
    }
    return () => clearTimeout(timer);
  }, [loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setShowColdStartWarning(false);

    console.log('🔍 Attempting login with:', username);

    try {
      // Use login from AuthContext
      const result = await login(username, password);

      if (result.success) {
        console.log('✅ Login success:', result.user);

        // Redirect based on role
        const role = result.user.role;
        const dashboardRoutes = {
          admin: '/dashboard/admin',
          operator: '/dashboard/operator',
          supervisor: '/dashboard/supervisor',
          planning: '/dashboard/planning',
        };

        const targetPath = dashboardRoutes[role] || '/';
        navigate(targetPath);
      } else {
        throw new Error(result.error);
      }

    } catch (err) {
      console.error('❌ Login failed:', err);
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
      setShowColdStartWarning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 sm:p-8">
        <div className="text-center mb-6 sm:mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 bg-blue-100 rounded-full mb-4">
            <LogIn className="text-blue-600" size={28} />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Welcome Back</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-2">Sign in to your account</p>
        </div>

        {error && (
          <div className="mb-4 p-3 sm:p-4 bg-red-50 border-l-4 border-red-500 rounded-lg animate-fade-in">
            <div className="flex items-start">
              <AlertCircle className="text-red-500 mt-0.5 mr-3 flex-shrink-0" size={20} />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">Login Failed</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {showColdStartWarning && (
          <div className="mb-4 p-3 sm:p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded-lg animate-fade-in">
            <div className="flex items-start">
              <Server className="text-yellow-500 mt-0.5 mr-3 flex-shrink-0" size={20} />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-800">Server Waking Up...</p>
                <p className="text-sm text-yellow-700 mt-1">
                  The backend is hosted on a free tier and may take up to 60 seconds to wake up. Please wait...
                </p>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 sm:mb-2">
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
                className="block w-full pl-10 pr-3 py-2.5 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-base sm:text-sm"
                placeholder="Enter username"
                disabled={loading}
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 sm:mb-2">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="text-gray-400" size={20} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-10 py-2.5 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-base sm:text-sm"
                placeholder="Enter password"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none"
                disabled={loading}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            <div className="flex justify-end mt-1">
              <a href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-800 transition-colors">
                Forgot Password?
              </a>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2.5 sm:py-3 rounded-lg font-semibold hover:bg-blue-700 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center shadow-md hover:shadow-lg transform active:scale-[0.98] text-base sm:text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {showColdStartWarning ? 'Still waiting...' : 'Signing in...'}
              </>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <a href="/signup" className="text-blue-600 hover:text-blue-800 font-semibold transition-colors">
              Sign Up
            </a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
