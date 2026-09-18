import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Sparkles, UserPlus } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button, Input } from '@/ui'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(email, password, name)
      navigate('/onboarding')
    } catch {
      setError('Не удалось зарегистрироваться. Проверьте данные и попробуйте ещё раз.')
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
          <h1 className="text-2xl font-bold text-ink-900">Создайте аккаунт</h1>
          <p className="mt-1 text-sm text-ink-500">Начните свой путь с UniPath MAX</p>
        </div>

        <form className="space-y-4 rounded-3xl bg-white p-6 shadow-card sm:p-7" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700" role="alert">
              {error}
            </div>
          )}
          <Input label="Полное имя" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Иван Иванов" />
          <Input
            label="Электронная почта"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@university.ru"
          />
          <Input
            label="Пароль"
            type="password"
            required
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Минимум 8 символов"
          />
          <Button type="submit" fullWidth loading={loading} leftIcon={<UserPlus className="h-4 w-4" />}>
            Зарегистрироваться
          </Button>
          <p className="text-center text-sm text-ink-500">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">Войти</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
