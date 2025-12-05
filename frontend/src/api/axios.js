import axios from 'axios';

// Get API URL from environment variables
const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  // Fallback for development if env var is missing
  if (!envUrl) {
    if (import.meta.env.DEV) {
      return 'http://localhost:8000';
    }
    // Fallback for production - REPLACE THIS WITH YOUR ACTUAL RENDER URL IF ENV VAR FAILS
    return 'https://kmt-workflow-backend.onrender.com';
  }
  return envUrl;
};

const BASE_URL = getBaseUrl().replace(/\/$/, '');

console.log('🚀 API Service Initialized');
console.log('📍 Mode:', import.meta.env.MODE);
console.log('🔗 Base URL:', BASE_URL);

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