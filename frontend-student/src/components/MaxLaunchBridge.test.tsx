import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MaxLaunchBridge } from '@/App'
import { apiClient } from '@/lib/api'
import { queryClient } from '@/lib/queryClient'
import { useAuthStore } from '@/stores/authStore'

const { post } = vi.hoisted(() => ({ post: vi.fn() }))

vi.mock('@/lib/api', () => ({
  apiClient: { post, defaults: { headers: { common: {} } } },
}))

function RouteControls() {
  const navigate = useNavigate()
  const location = useLocation()
  return (
    <>
      <button onClick={() => { useAuthStore.getState().logout(); navigate('/login') }}>Выйти</button>
      <output data-testid="path">{location.pathname}</output>
    </>
  )
}

describe('MAX startup and logout navigation', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    queryClient.clear()
    useAuthStore.setState({ user: null, token: null })
    vi.clearAllMocks()
    window.WebApp = { initData: 'signed-context-fixture' }
    post.mockResolvedValue({
      data: {
        user: { id: 77, email: 'student@example.test', role: 'student', full_name: 'Student' },
        tokens: { access: 'student-session-fixture' },
        max: {},
      },
    })
  })

  it('does not restart automatic MAX login when logout navigates to /login', async () => {
    render(
      <MemoryRouter initialEntries={['/home']}>
        <MaxLaunchBridge />
        <RouteControls />
      </MemoryRouter>,
    )

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    fireEvent.click(screen.getByRole('button', { name: 'Выйти' }))

    expect(screen.getByTestId('path')).toHaveTextContent('/login')
    expect(sessionStorage.getItem('max-launch-suppressed')).toBe('true')
    await new Promise((resolve) => setTimeout(resolve, 20))
    expect(post).toHaveBeenCalledTimes(1)
  })
})
