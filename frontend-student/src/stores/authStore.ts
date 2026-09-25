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

let authRevision = 0

function staleAuthRequestError() {
  const error = new Error('Authentication changed while MAX launch was being checked.')
  Object.assign(error, { code: 'auth_state_changed' })
  return error
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,

      login: async (email: string, password: string) => {
        const revision = ++authRevision
        const response = await apiClient.post('/v1/accounts/login/', { email, password })
        if (revision !== authRevision) throw staleAuthRequestError()
        const token = response.data.access
        const user = normalizeUser(response.data.user)
        updateSession(set, get, token, user)
      },

      register: async (email: string, password: string, name: string) => {
        const revision = ++authRevision
        const [firstName, ...lastNameParts] = name.trim().split(' ')
        const response = await apiClient.post('/v1/accounts/register/', {
          email,
          password,
          password2: password,
          first_name: firstName || name,
          last_name: lastNameParts.join(' '),
          role: 'student',
        })
        if (revision !== authRevision) throw staleAuthRequestError()
        const token = response.data.tokens.access
        const user = normalizeUser(response.data.user)
        updateSession(set, get, token, user)
      },

      completeMaxLaunch: async (initData: string) => {
        const revision = authRevision
        const response = await apiClient.post('/max/launch/', { initData })
        if (revision !== authRevision) throw staleAuthRequestError()
        const token = response.data.tokens.access
        const user = normalizeUser(response.data.user)
        updateSession(set, get, token, user)
        return { startParam: response.data.max?.start_param, role: user.role }
      },

      logout: () => {
        authRevision += 1
        sessionStorage.setItem('max-launch-suppressed', 'true')
        queryClient.clear()
        set({ user: null, token: null })
        localStorage.removeItem('adminToken')
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
