import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '@/lib/api'
import { queryClient } from '@/lib/queryClient'

interface User {
  id: number
  email: string
  name: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  completeMaxLaunch: (initData: string) => Promise<{ startParam?: string; role: string }>
  logout: () => void
  checkAuth: () => void
}

const normalizeUser = (user: any) => ({
  ...user,
  name: user.full_name || user.name || user.email,
})

function updateSession(set: (state: Partial<AuthState>) => void, get: () => AuthState, token: string, user: User) {
  if (get().user?.id !== user.id) queryClient.clear()
  set({ token, user })
  localStorage.setItem('adminToken', token)
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,

      login: async (email: string, password: string) => {
        const response = await apiClient.post('/v1/accounts/login/', { email, password })
        const token = response.data.access
        const user = normalizeUser(response.data.user)
        updateSession(set, get, token, user)
      },

      register: async (email: string, password: string, name: string) => {
        const [firstName, ...lastNameParts] = name.trim().split(' ')
        const response = await apiClient.post('/v1/accounts/register/', {
          email,
          password,
          password2: password,
          first_name: firstName || name,
          last_name: lastNameParts.join(' '),
          role: 'student',
        })
        const token = response.data.tokens.access
        const user = normalizeUser(response.data.user)
        updateSession(set, get, token, user)
      },

      completeMaxLaunch: async (initData: string) => {
        const response = await apiClient.post('/max/launch/', { initData })
        const token = response.data.tokens.access
        const user = normalizeUser(response.data.user)
        updateSession(set, get, token, user)
        return { startParam: response.data.max?.start_param, role: user.role }
      },

      logout: () => {
        queryClient.clear()
        set({ user: null, token: null })
        localStorage.removeItem('adminToken')
        sessionStorage.removeItem('max-launch-processed')
        sessionStorage.removeItem('max-launch-pending')
        delete apiClient.defaults.headers.common['Authorization']
      },

      checkAuth: () => {
        const token = get().token
        if (token) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
