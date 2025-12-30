import axios from 'axios';

// Production Render Backend URL - MUST match your actual Render deployment
const PRODUCTION_BACKEND_URL = 'https://kmt-backend.onrender.com';

// Get API URL from environment variables
const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL;

  // Use environment variable if set
  if (envUrl) {
    return envUrl.trim().replace(/\/$/, ''); // Trim spaces and remove trailing slash
  }

  // Fallback for development
  if (import.meta.env.DEV) {
    return 'http://localhost:8000';
  }

  // Production fallback
  return PRODUCTION_BACKEND_URL;
};

const BASE_URL = getBaseUrl();

console.log('🚀 API Service Initialized');
console.log('📍 Mode:', import.meta.env.MODE);
console.log('🔗 Base URL:', BASE_URL);

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // Increased timeout for Render cold starts
});

// Request interceptor - attach token
api.interceptors.request.use(
  (config) => {
    // Get fresh token from localStorage
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token.trim()}`;
    }

    if (import.meta.env.DEV) {
      console.log(`📤 ${config.method.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - global error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const status = error.response?.status;

    // Handle 401 Unauthorized (Expired or Invalid Token)
    if (status === 401) {
      console.warn('🔒 Session expired or invalid. Redirecting to login...');
      localStorage.removeItem('token');
      localStorage.removeItem('user');

      // Redirect to login only if not already on login/signup pages
      const path = window.location.pathname;
      if (path !== '/login' && path !== '/signup') {
        window.location.href = '/login?expired=true';
      }
    }

    if (!error.response) {
      console.error('🚨 Network Error - Check CORS or Server Status');
    }

    return Promise.reject(error);
  }
);


export default api;