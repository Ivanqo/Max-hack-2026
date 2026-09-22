import { Link } from 'react-router-dom'
import { ArrowRight, BarChart3, BookOpen, Briefcase, LayoutDashboard, ShieldCheck, Users } from 'lucide-react'
import { Card } from '@/ui'

const sections = [
  { to: '/', icon: LayoutDashboard, title: 'Дашборд', text: 'Ключевые показатели платформы и сигналы, требующие внимания.' },
  { to: '/opportunities', icon: Briefcase, title: 'Возможности', text: 'Публикация и проверка стажировок, проектов, хакатонов и событий.' },
  { to: '/knowledge', icon: BookOpen, title: 'База знаний', text: 'Актуальные материалы, ответы на вопросы и контроль публикаций.' },
  { to: '/career-roles', icon: Users, title: 'Карьерные роли', text: 'Роли, навыки и образовательные траектории для Career GPS.' },
  { to: '/analytics', icon: BarChart3, title: 'Аналитика', text: 'Вовлечённость студентов, поисковые запросы и статистика контента.' },
]

export const AboutPage = () => (
  <div className="space-y-6 animate-fade-in">
    <section className="overflow-hidden rounded-3xl bg-brand-gradient p-6 text-white shadow-pop sm:p-8">
      <div className="max-w-2xl">
        <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <p className="text-sm font-medium text-white/75">О платформе</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">Управляйте студенческим маршрутом из одного места</h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-white/85">
          UniPath MAX объединяет контент университета, карьерные возможности и аналитику — чтобы студенту было проще найти следующий шаг.
        </p>
      </div>
    </section>

    <section>
      <div className="mb-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">Навигация по панели</p>
        <h2 className="mt-1 text-xl font-bold tracking-tight text-ink-900">Что можно делать</h2>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sections.map(({ to, icon: Icon, title, text }) => (
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
      <h2 className="font-semibold text-ink-900">Роли и ответственность</h2>
      <p className="mt-1.5 max-w-2xl text-sm leading-6 text-ink-600">
        Доступные разделы зависят от роли. Цвет акцента помогает быстро понять, в каком рабочем контексте вы находитесь: администрирование, редактура или управление подразделением.
      </p>
    </Card>
  </div>
)
