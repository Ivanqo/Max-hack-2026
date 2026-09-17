import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '@/lib/api'

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
  completeMaxLaunch: (initData: string) => Promise<string | undefined>
  logout: () => void
  checkAuth: () => void
}

const normalizeUser = (user: any) => ({
  ...user,
  name: user.full_name || user.name || user.email,
})

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,

      login: async (email: string, password: string) => {
        const response = await apiClient.post('/v1/accounts/login/', { email, password })
        const token = response.data.access
        const user = normalizeUser(response.data.user)
        set({ token, user })
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
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
        set({ token, user })
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
      },

      completeMaxLaunch: async (initData: string) => {
        const response = await apiClient.post('/max/launch/', { initData })
        const token = response.data.tokens.access
        const user = normalizeUser(response.data.user)
        set({ token, user })
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
        return response.data.max?.start_param
      },

      logout: () => {
        set({ user: null, token: null })
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
