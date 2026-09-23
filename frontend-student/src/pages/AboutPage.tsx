import { Link } from 'react-router-dom'
import { ArrowRight, BookOpen, Compass, GraduationCap, LayoutGrid, Sparkles, UserRound } from 'lucide-react'
import { Card } from '@/ui'

const capabilities = [
  { to: '/home', icon: Sparkles, title: 'Личный маршрут', text: 'Главная собирает ваш прогресс и подсказывает следующий полезный шаг.' },
  { to: '/career-gps', icon: Compass, title: 'Карьерный навигатор', text: 'Показывает готовность к цели и помогает понять, какие навыки развивать.' },
  { to: '/opportunities', icon: LayoutGrid, title: 'Возможности', text: 'Стажировки, проекты, хакатоны и события с персональным совпадением.' },
  { to: '/knowledge', icon: BookOpen, title: 'База знаний', text: 'Проверенные ответы о правилах, сервисах и возможностях университета.' },
  { to: '/profile', icon: UserRound, title: 'Профиль', text: 'Навыки, интересы и карьерная цель — основа точных рекомендаций.' },
]

export default function AboutPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <section className="overflow-hidden rounded-3xl bg-brand-gradient p-6 text-white shadow-pop sm:p-8">
        <div className="max-w-2xl">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
            <GraduationCap className="h-5 w-5" />
          </div>
          <p className="text-sm font-medium text-white/75">О платформе</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">UniPath MAX помогает двигаться к своей карьере</h1>
          <p className="mt-3 max-w-xl text-sm leading-6 text-white/85">
            Один понятный маршрут от интереса к следующему шагу: профиль, карьерный навигатор, проверенные знания и возможности университета.
          </p>
        </div>
      </section>

      <section>
        <div className="mb-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">Всё в одном месте</p>
          <h2 className="mt-1 text-xl font-bold tracking-tight text-ink-900">Возможности приложения</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map(({ to, icon: Icon, title, text }) => (
            <Link key={to} to={to} className="group">
              <Card interactive className="h-full">
                <div className="flex items-start justify-between gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                    <Icon className="h-5 w-5" />
                  </span>
                  <ArrowRight className="h-4 w-4 text-ink-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-600" />
                </div>
                <h3 className="mt-4 font-semibold text-ink-900">{title}</h3>
                <p className="mt-1.5 text-sm leading-5 text-ink-500">{text}</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <Card className="border-accent-200 bg-accent-50/60">
        <h2 className="font-semibold text-ink-900">Как получить точные рекомендации?</h2>
        <p className="mt-1.5 max-w-2xl text-sm leading-6 text-ink-600">
          Заполните профиль, укажите интересы и навыки, а затем откройте карьерный навигатор. Чем полнее ваш профиль, тем полезнее подбор возможностей.
        </p>
        <Link to="/profile" className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-800">
          Настроить профиль <ArrowRight className="h-4 w-4" />
        </Link>
      </Card>
    </div>
  )
}
