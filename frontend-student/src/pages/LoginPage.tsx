import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LogIn, Sparkles } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useAuthStore } from '@/stores/authStore'
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
      const pendingInitData = sessionStorage.getItem('max-launch-pending')
      if (pendingInitData) {
        const { role } = await completeMaxLaunch(pendingInitData)
        sessionStorage.setItem('max-launch-processed', pendingInitData)
        sessionStorage.removeItem('max-launch-pending')
        if (role !== 'student') {
          window.location.replace('/admin/')
          return
        }
      }
      const role = useAuthStore.getState().user?.role
      if (role && role !== 'student') {
        window.location.replace('/admin/')
      } else {
        navigate('/home')
      }
    } catch {
      setError('Не удалось войти. Проверьте почту и пароль.')
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
