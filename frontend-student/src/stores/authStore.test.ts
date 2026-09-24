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
})
