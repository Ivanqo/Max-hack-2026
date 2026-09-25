import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LogIn, Sparkles } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useAuthStore } from '@/stores/authStore'
import { currentMaxInitData, maxRoleDestination } from '@/lib/maxLaunch'
import { Button, Input } from '@/ui'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const completeMaxLaunch = useAuthStore((state) => state.completeMaxLaunch)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch {
      setError('Не удалось войти. Проверьте почту и пароль.')
      setLoading(false)
      return
    }

    try {
      const pendingInitData = sessionStorage.getItem('max-launch-pending')
      // After an explicit account switch, attach the live SDK context to the
      // newly authenticated account. The server verifies its signature and
      // performs any transfer atomically.
      const initData = pendingInitData || currentMaxInitData()
      const role = initData
        ? (await completeMaxLaunch(initData)).role
        : useAuthStore.getState().user?.role
      const destination = role ? maxRoleDestination(role) : '/home'
      if (!destination) throw new Error('Unsupported account role')
      sessionStorage.removeItem('max-launch-pending')
      sessionStorage.removeItem('max-launch-suppressed')
      if (destination === '/admin/') {
        window.location.replace('/admin/')
      } else if (destination === '/home') {
        navigate('/home')
      } else {
        throw new Error('Unsupported account role')
      }
    } catch (bindingError: any) {
      sessionStorage.removeItem('max-launch-pending')
      const detail = bindingError?.response?.data?.detail
      setError(typeof detail === 'string' && detail.trim()
        ? `Вход выполнен, но MAX не удалось связать: ${detail}`
        : 'Вход выполнен, но MAX не удалось связать. Повторите запуск из MAX или обратитесь к администратору.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-gradient-soft px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-pop">
            <Sparkles className="h-6 w-6" />
          </span>
          <h1 className="text-2xl font-bold text-ink-900">UniPath MAX</h1>
          <p className="mt-1 text-sm text-ink-500">Ваш карьерный навигатор в университете</p>
        </div>

        <form className="space-y-4 rounded-3xl bg-white p-6 shadow-card sm:p-7" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700" role="alert">
              {error}
            </div>
          )}
          <Input
            label="Электронная почта"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="student@demo.local"
          />
          <Input
            label="Пароль"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
          <Button type="submit" fullWidth loading={loading} leftIcon={<LogIn className="h-4 w-4" />}>
            Войти
          </Button>
          <p className="text-center text-sm text-ink-500">
            Нет аккаунта?{' '}
            <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">Зарегистрироваться</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
