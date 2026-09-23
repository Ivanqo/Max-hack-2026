import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { Compass, Home, Info, LayoutGrid, LogOut, Menu, Sparkles, User, X, BookOpen } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/ui'

const navItems = [
  { to: '/home', label: 'Главная', icon: Home },
  { to: '/career-gps', label: 'Карьерный навигатор', icon: Compass },
  { to: '/opportunities', label: 'Возможности', icon: LayoutGrid },
  { to: '/knowledge', label: 'База знаний', icon: BookOpen },
  { to: '/profile', label: 'Профиль', icon: User },
]

const aboutItem = { to: '/about', label: 'О платформе', icon: Info }

function initials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'U'
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen min-w-0 bg-ink-50/60">
      {/* Desktop top navigation */}
      <header className="sticky top-0 z-40 hidden border-b border-ink-100 bg-white/85 backdrop-blur md:block">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-8">
            <NavLink to="/home" className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-soft">
                <Sparkles className="h-4 w-4" />
              </span>
              <span className="text-base font-bold tracking-tight text-ink-900">UniPath <span className="text-brand-600">MAX</span></span>
            </NavLink>
            <nav className="flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      'rounded-xl px-3.5 py-2 text-sm font-medium transition-colors',
                      isActive ? 'bg-brand-50 text-brand-700' : 'text-ink-500 hover:bg-ink-50 hover:text-ink-800',
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
              <NavLink
                to={aboutItem.to}
                className={({ isActive }) =>
                  cn(
                    'rounded-xl px-3.5 py-2 text-sm font-medium transition-colors',
                    isActive ? 'bg-brand-50 text-brand-700' : 'text-ink-500 hover:bg-ink-50 hover:text-ink-800',
                  )
                }
              >
                {aboutItem.label}
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5 rounded-xl border border-ink-100 bg-white px-2.5 py-1.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
                {initials(user?.name || user?.email || '')}
              </span>
              <span className="max-w-[140px] truncate text-sm font-medium text-ink-700">{user?.name || user?.email}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex h-9 w-9 items-center justify-center rounded-xl text-ink-400 transition-colors hover:bg-rose-50 hover:text-rose-600"
              aria-label="Выйти"
              title="Выйти"
            >
              <LogOut className="h-4.5 w-4.5" style={{ height: 18, width: 18 }} />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile top bar */}
      <header className="safe-top sticky top-0 z-40 flex items-center justify-between border-b border-ink-100 bg-white/90 px-4 py-3 backdrop-blur md:hidden">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="text-base font-bold text-ink-900">UniPath MAX</span>
        </div>
        <button
          onClick={() => setMenuOpen(true)}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-ink-500 hover:bg-ink-100"
          aria-label="Открыть меню"
        >
          <Menu className="h-5 w-5" />
        </button>
      </header>

      {/* Mobile slide-in profile menu */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-ink-950/40" onClick={() => setMenuOpen(false)} />
          <div className="safe-top absolute right-0 top-0 h-full w-72 max-w-[85vw] animate-slide-up bg-white p-5 shadow-card">
            <div className="mb-6 flex items-center justify-between">
              <span className="text-sm font-semibold text-ink-900">Меню</span>
              <button onClick={() => setMenuOpen(false)} className="rounded-full p-1.5 text-ink-400 hover:bg-ink-100" aria-label="Закрыть">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-ink-100 p-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                {initials(user?.name || user?.email || '')}
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-ink-900">{user?.name || 'Студент'}</p>
                <p className="truncate text-xs text-ink-400">{user?.email}</p>
              </div>
            </div>
            <nav className="mb-5 space-y-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium',
                      isActive ? 'bg-brand-50 text-brand-700' : 'text-ink-600 hover:bg-ink-50 hover:text-ink-900',
                    )
                  }
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              ))}
              <NavLink
                to={aboutItem.to}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium',
                    isActive ? 'bg-brand-50 text-brand-700' : 'text-ink-600 hover:bg-ink-50 hover:text-ink-900',
                  )
                }
              >
                <Info className="h-4 w-4" />
                {aboutItem.label}
              </NavLink>
            </nav>
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-rose-600 hover:bg-rose-50"
            >
              <LogOut className="h-4 w-4" />
              Выйти
            </button>
          </div>
        </div>
      )}

      <main className="mx-auto min-w-0 max-w-6xl overflow-x-hidden px-4 pb-24 pt-5 sm:px-6 md:pb-12 md:pt-8">
        <Outlet />
      </main>

      {/* Mobile bottom navigation */}
      <nav className="safe-bottom fixed inset-x-0 bottom-0 z-40 border-t border-ink-100 bg-white/95 backdrop-blur md:hidden">
        <div className="mx-auto flex max-w-md items-stretch justify-between px-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium transition-colors',
                  isActive ? 'text-brand-600' : 'text-ink-400',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className="h-5 w-5" strokeWidth={isActive ? 2.5 : 2} />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
