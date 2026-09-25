import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/lib/api'
import { useAuthStore } from './authStore'

vi.mock('@/lib/api', () => ({
  apiClient: {
    post: vi.fn(),
    defaults: { headers: { common: {} } },
  },
}))

describe('MAX launch authentication', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    useAuthStore.setState({ user: null, token: null })
    vi.clearAllMocks()
  })

  it('sends initData to the backend and applies its verified role and session', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        user: { id: 77, email: 'admin@example.test', role: 'admin', full_name: 'Admin' },
        tokens: { access: 'access-fixture' },
        max: { start_param: 'home' },
      },
    })

    const result = await useAuthStore.getState().completeMaxLaunch('signed-initdata-fixture')

    expect(apiClient.post).toHaveBeenCalledWith('/max/launch/', { initData: 'signed-initdata-fixture' })
    expect(result).toEqual({ startParam: 'home', role: 'admin' })
    expect(useAuthStore.getState().user?.role).toBe('admin')
    expect(useAuthStore.getState().token).toBe('access-fixture')
  })

  it('propagates backend binding errors to the launch UI', async () => {
    const bindingError = { response: { data: { detail: 'Account binding conflict' } } }
    vi.mocked(apiClient.post).mockRejectedValueOnce(bindingError)

    await expect(useAuthStore.getState().completeMaxLaunch('signed-initdata-fixture'))
      .rejects.toBe(bindingError)
  })

  it('suppresses automatic MAX login after an explicit logout', () => {
    useAuthStore.getState().logout()

    expect(sessionStorage.getItem('max-launch-suppressed')).toBe('true')
    expect(sessionStorage.getItem('max-launch-pending')).toBeNull()
  })

  it('does not let an in-flight MAX response restore the previous account after logout', async () => {
    let resolveLaunch: ((value: any) => void) | undefined
    vi.mocked(apiClient.post).mockImplementation((url: string) => {
      if (url === '/max/launch/') {
        return new Promise((resolve) => { resolveLaunch = resolve }) as any
      }
      return Promise.resolve({
        data: {
          access: 'new-account-access',
          user: { id: 88, email: 'second@example.test', role: 'student', full_name: 'Second Student' },
        },
      }) as any
    })

    const pendingLaunch = useAuthStore.getState().completeMaxLaunch('signed-context-fixture')
    useAuthStore.getState().logout()
    resolveLaunch?.({
      data: {
        user: { id: 77, email: 'first@example.test', role: 'student', full_name: 'First Student' },
        tokens: { access: 'old-account-access' },
        max: {},
      },
    })

    await expect(pendingLaunch).rejects.toMatchObject({ code: 'auth_state_changed' })
    expect(useAuthStore.getState().user).toBeNull()
    expect(useAuthStore.getState().token).toBeNull()
  })
})
