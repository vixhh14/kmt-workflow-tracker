import axios from 'axios';

// Production Render Backend URL - MUST match your actual Render deployment
const PRODUCTION_BACKEND_URL = 'https://kmt-workflow-backend.onrender.com';

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

  // Production fallback - use the hardcoded Render URL
  return PRODUCTION_BACKEND_URL;
};

const BASE_URL = getBaseUrl();

console.log('🚀 API Service Initialized');
console.log('📍 Mode:', import.meta.env.MODE);
console.log('🔗 Base URL:', BASE_URL);
console.log('📋 Env VITE_API_URL:', import.meta.env.VITE_API_URL || '(not set)');

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
    // Only log in development
    if (import.meta.env.DEV) {
      console.log(`📤 ${config.method.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Setup Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - global error handling
api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`✅ ${response.config.method.toUpperCase()} ${response.config.url} - ${response.status}`);
    }
    return response;
  },
  (error) => {
    if (!error.response) {
      console.error('🚨 Network Error - Check CORS or Server Status:', error.message);
    } else {
      if (error.response.status === 401) {
        console.warn('🔒 Unauthorized - Token might be invalid or expired');
      }
      console.error(`❌ API Error: ${error.response.status} - ${error.response.data?.detail || error.message}`);
    }
    return Promise.reject(error);
  }
);

export default api;