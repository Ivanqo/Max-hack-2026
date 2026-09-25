import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { currentMaxInitData } from '@/lib/maxLaunch';
import { Button, Input } from '@/ui';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, linkMaxProfile } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const account = await login(email, password);
      const initData = currentMaxInitData();
      const authenticatedAccount = initData ? await linkMaxProfile(initData) : account;
      sessionStorage.removeItem('max-launch-suppressed');
      if (authenticatedAccount.role === 'student') {
        window.location.replace('/');
        return;
      }
      navigate('/');
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail;
      setError(typeof detail === 'string' && detail.trim()
        ? detail
        : err instanceof Error ? err.message : 'Не удалось войти. Проверьте почту, пароль и права доступа.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-gradient-soft p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-pop">
            <Sparkles className="h-6 w-6" />
          </span>
          <h1 className="text-2xl font-bold text-ink-900">Панель администратора</h1>
          <p className="mt-1 text-sm text-ink-500">UniPath MAX · управление платформой университета</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-3xl bg-white p-6 shadow-card sm:p-7">
          {error && (
            <div className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700" role="alert">{error}</div>
          )}
          <Input
            label="Электронная почта"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@demo.local"
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
          <Button type="submit" fullWidth loading={loading} leftIcon={<LogIn className="h-4 w-4" />}>Войти</Button>
        </form>
      </div>
    </div>
  );
};
