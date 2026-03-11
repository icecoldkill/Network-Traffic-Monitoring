import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth tokens
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// API endpoints
export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/login', credentials),
  register: (userData: { email: string; password: string; name: string }) =>
    api.post('/auth/register', userData),
  me: () => api.get('/auth/me'),
};

export const dashboardAPI = {
  getMetrics: () => api.get('/dashboard/metrics'),
  getTraffic: (timeRange: string) =>
    api.get(`/dashboard/traffic?range=${timeRange}`),
  getSecurityEvents: (filters = {}) =>
    api.get('/dashboard/security-events', { params: filters }),
  exportReport: (format: 'pdf' | 'csv' = 'pdf') =>
    api.get(`/dashboard/export?format=${format}`, { responseType: 'blob' }),
};
