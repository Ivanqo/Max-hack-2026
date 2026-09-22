import { ReactNode, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/ui';
import {
  BarChart3,
  BookOpen,
  Briefcase,
  LayoutDashboard,
  LogOut,
  Menu,
  Info,
  Sparkles,
  Users,
  X,
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Дашборд' },
  { path: '/opportunities', icon: Briefcase, label: 'Возможности' },
  { path: '/knowledge', icon: BookOpen, label: 'База знаний' },
  { path: '/career-roles', icon: Users, label: 'Карьерные роли' },
  { path: '/analytics', icon: BarChart3, label: 'Аналитика' },
  { path: '/about', icon: Info, label: 'О платформе' },
];

const roleTheme: Record<string, string> = {
  admin: 'theme-admin',
  editor: 'theme-editor',
  university_admin: 'theme-university-admin',
  institute_admin: 'theme-institute-admin',
};

function initials(value: string) {
  return value.split(/[\s@]/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('') || 'A';
}

const roleLabels: Record<string, string> = {
  admin: 'Администратор',
  university_admin: 'Администратор вуза',
  institute_admin: 'Администратор института',
  editor: 'Редактор',
};

export const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const items = user?.role === 'admin' ? [...navItems, { path: '/users', icon: Users, label: 'Пользователи' }] : navItems;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const NavLinks = ({ onNavigate }: { onNavigate?: () => void }) => (
    <nav className="flex-1 space-y-1 p-3">
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            onClick={onNavigate}
            className={cn(
              'flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors',
              isActive ? 'bg-brand-50 text-brand-700' : 'text-ink-600 hover:bg-ink-50 hover:text-ink-900',
            )}
          >
            <Icon className="h-4.5 w-4.5" style={{ height: 18, width: 18 }} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className={cn('flex min-h-screen min-w-0 bg-ink-50/60', roleTheme[user?.role || 'admin'])}>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-ink-100 bg-white lg:flex">
        <div className="flex items-center gap-2 p-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient text-white">
            <Sparkles className="h-4.5 w-4.5" style={{ height: 18, width: 18 }} />
          </span>
          <div>
            <p className="text-sm font-bold text-ink-900">UniPath MAX</p>
            <p className="text-xs text-ink-400">Панель администратора</p>
          </div>
        </div>
        <NavLinks />
        <div className="border-t border-ink-100 p-3">
          <div className="mb-2 flex items-center gap-2.5 rounded-xl px-2 py-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
              {initials(user?.full_name || user?.email || '')}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-ink-800">{user?.full_name || user?.email}</p>
              <p className="truncate text-xs text-ink-400">{roleLabels[user?.role || ''] || user?.role}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-ink-600 transition-colors hover:bg-rose-50 hover:text-rose-600"
          >
            <LogOut className="h-4.5 w-4.5" style={{ height: 18, width: 18 }} />
            Выйти
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="flex flex-1 flex-col">
        <header className="safe-top flex items-center justify-between border-b border-ink-100 bg-white px-4 py-3 lg:hidden">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white">
              <Sparkles className="h-4 w-4" />
            </span>
            <span className="text-sm font-bold text-ink-900">UniPath MAX</span>
          </div>
          <button
            onClick={() => setDrawerOpen(true)}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-ink-500 hover:bg-ink-100"
            aria-label="Открыть меню"
          >
            <Menu className="h-5 w-5" />
          </button>
        </header>

        <main className="min-w-0 flex-1 overflow-x-hidden overflow-y-auto p-4 sm:p-6 lg:p-8">{children}</main>
      </div>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-ink-950/40" onClick={() => setDrawerOpen(false)} />
          <div className="safe-top absolute left-0 top-0 flex h-full w-72 max-w-[85vw] flex-col bg-white shadow-card">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white">
                  <Sparkles className="h-4 w-4" />
                </span>
                <span className="text-sm font-bold text-ink-900">UniPath MAX</span>
              </div>
              <button onClick={() => setDrawerOpen(false)} className="rounded-full p-1.5 text-ink-400 hover:bg-ink-100" aria-label="Закрыть">
                <X className="h-5 w-5" />
              </button>
            </div>
            <NavLinks onNavigate={() => setDrawerOpen(false)} />
            <div className="border-t border-ink-100 p-3">
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-rose-600 hover:bg-rose-50"
              >
                <LogOut className="h-4.5 w-4.5" style={{ height: 18, width: 18 }} />
                Выйти
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
