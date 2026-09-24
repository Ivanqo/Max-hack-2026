import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  let sharedToken: string | null = null;
  try {
    sharedToken = JSON.parse(localStorage.getItem('auth-storage') || '{}')?.state?.token || null;
  } catch {
    sharedToken = null;
  }
  const token = sharedToken || localStorage.getItem('adminToken');
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
      window.dispatchEvent(new Event('unipath-auth-invalidated'));
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export default api;
