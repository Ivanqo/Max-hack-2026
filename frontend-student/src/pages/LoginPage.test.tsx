import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginPage from './LoginPage'
import { apiClient } from '@/lib/api'
import { queryClient } from '@/lib/queryClient'
import { useAuthStore } from '@/stores/authStore'

const { post, loginMock } = vi.hoisted(() => ({ post: vi.fn(), loginMock: vi.fn() }))

vi.mock('@/lib/api', () => ({
  apiClient: { post, defaults: { headers: { common: {} } } },
}))

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ login: loginMock }),
}))

describe('login after MAX account switch', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    queryClient.clear()
    useAuthStore.setState({ user: null, token: null })
    vi.clearAllMocks()
    loginMock.mockImplementation((email: string, password: string) =>
      useAuthStore.getState().login(email, password),
    )
    window.WebApp = { initData: 'signed-context-fixture' }
    post.mockImplementation((url: string) => {
      if (url === '/v1/accounts/login/') {
        return Promise.resolve({
          data: {
            access: 'login-session-fixture',
            user: { id: 88, email: 'student@example.test', role: 'student', full_name: 'Student' },
          },
        })
      }
      return Promise.resolve({
        data: {
          user: { id: 88, email: 'student@example.test', role: 'student', full_name: 'Student' },
          tokens: { access: 'linked-session-fixture' },
          max: {},
        },
      })
    })
  })

  it('sends the live signed Bridge context after password login and routes using the backend role', async () => {
    sessionStorage.setItem('max-launch-suppressed', 'true')
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/home" element={<p>Студенческий интерфейс</p>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByPlaceholderText('student@demo.local'), { target: { value: 'student@example.test' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'fixture-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Войти' }))

    await screen.findByText('Студенческий интерфейс')
    await waitFor(() => expect(post).toHaveBeenNthCalledWith(2, '/max/launch/', { initData: 'signed-context-fixture' }))
    expect(sessionStorage.getItem('max-launch-suppressed')).toBeNull()
    expect(useAuthStore.getState().user?.role).toBe('student')
  })

  it('prefers the current Bridge context over an older context retained for login', async () => {
    sessionStorage.setItem('max-launch-pending', 'older-context-fixture')
    window.WebApp = { initData: 'fresh-context-fixture' }
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/home" element={<p>Студенческий интерфейс</p>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByPlaceholderText('student@demo.local'), { target: { value: 'student@example.test' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'fixture-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Войти' }))

    await screen.findByText('Студенческий интерфейс')
    await waitFor(() => expect(post).toHaveBeenNthCalledWith(2, '/max/launch/', { initData: 'fresh-context-fixture' }))
  })

  it('waits briefly when the bridge object arrives after the login form is submitted', async () => {
    window.WebApp = {}
    window.setTimeout(() => { window.WebApp = { initData: 'delayed-context-fixture' } }, 10)
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/home" element={<p>Студенческий интерфейс</p>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByPlaceholderText('student@demo.local'), { target: { value: 'student@example.test' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'fixture-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Войти' }))

    await screen.findByText('Студенческий интерфейс')
    await waitFor(() => expect(post).toHaveBeenNthCalledWith(2, '/max/launch/', { initData: 'delayed-context-fixture' }))
  })

  it('explains that a rejected MAX context needs a fresh app launch', async () => {
    post.mockImplementationOnce(() => Promise.resolve({
      data: {
        access: 'login-session-fixture',
        user: { id: 88, email: 'student@example.test', role: 'student', full_name: 'Student' },
      },
    })).mockRejectedValueOnce({
      response: { status: 400, data: { detail: 'Invalid MAX launch context.' } },
    })
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/home" element={<p>Студенческий интерфейс</p>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByPlaceholderText('student@demo.local'), { target: { value: 'student@example.test' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'fixture-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Войти' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Закройте Mini App и откройте его заново из MAX')
    expect(screen.queryByText('Студенческий интерфейс')).toBeNull()
  })
})
