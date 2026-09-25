import axios, { AxiosError } from 'axios'
import { resolveApiBaseUrl } from './apiBase'

export const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(import.meta.env.VITE_API_URL, window.location.href),
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const persisted = localStorage.getItem('auth-storage')
  if (persisted) {
    try {
      const token = JSON.parse(persisted)?.state?.token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch {
      localStorage.removeItem('auth-storage')
    }
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<any>) => {
    const detail = error.response?.data?.detail
    const message = error.response?.data?.message || error.response?.data?.error
    if (typeof detail === 'string') {
      error.message = detail
    } else if (message) {
      error.message = String(message)
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage')
    }
    return Promise.reject(error)
  },
)
