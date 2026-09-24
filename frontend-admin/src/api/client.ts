import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  let token = localStorage.getItem('adminToken');
  if (!token) {
    try {
      token = JSON.parse(localStorage.getItem('auth-storage') || '{}')?.state?.token || null;
    } catch {
      token = null;
    }
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('adminToken');
      localStorage.removeItem('auth-storage');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export default api;
