import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Bookmark,
  Compass,
  ListChecks,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react'
import { fetchCareerGpsSummary, fetchOpportunities, fetchStudentProfile, fetchSubscriptions } from '@/lib/endpoints'
import { Badge, Card, EmptyState, ErrorState, ReadinessRing, Skeleton } from '@/ui'
import { useAuth } from '@/contexts/AuthContext'
import { opportunityTypeLabels } from '@/lib/labels'
import { userQueryKey } from '@/lib/queryClient'

function greeting() {
  const hour = new Date().getHours()
  if (hour < 6) return 'Доброй ночи'
  if (hour < 12) return 'Доброе утро'
  if (hour < 18) return 'Добрый день'
  return 'Добрый вечер'
}

export default function Home() {
  const { user } = useAuth()
  const userId = user?.id ?? null

  const profileQuery = useQuery({ queryKey: userQueryKey(userId, 'student-profile'), queryFn: fetchStudentProfile })
  const gpsQuery = useQuery({ queryKey: userQueryKey(userId, 'career-gps-summary'), queryFn: fetchCareerGpsSummary })
  const opportunitiesQuery = useQuery({ queryKey: userQueryKey(userId, 'opportunities', {}), queryFn: () => fetchOpportunities() })
  const subscriptionsQuery = useQuery({ queryKey: userQueryKey(userId, 'subscriptions'), queryFn: fetchSubscriptions })

  const profile = profileQuery.data
  const firstName = (profile?.user.firstName || user?.name || '').split(' ')[0]

  const nextAction = useMemo(() => {
    if (profile && !profile.profile.onboardingCompleted) {
      return {
        title: 'Завершите анкету',
        description: 'Расскажите о себе, чтобы мы могли построить ваш карьерный маршрут и подобрать возможности.',
        cta: 'Пройти онбординг',
        to: '/onboarding',
      }
    }
    if (profile && profile.skills.length < 2) {
      return {
        title: 'Добавьте навыки в профиль',
        description: 'Ещё 2 навыка — и точность карьерных рекомендаций заметно вырастет.',
        cta: 'Добавить навыки',
        to: '/profile',
      }
    }
    if (profile && !profile.profile.careerGoal) {
      return {
        title: 'Выберите карьерную цель',
        description: 'Карьерный навигатор покажет, чего не хватает до выбранной роли и что делать дальше.',
        cta: 'Открыть карьерный навигатор',
        to: '/career-gps',
      }
    }
    const topOpportunity = opportunitiesQuery.data?.[0]
    if (topOpportunity && topOpportunity.matchPercentage >= 60) {
      return {
        title: `Загляните в «${topOpportunity.title}»`,
        description: `Совпадение ${topOpportunity.matchPercentage}% — одна из лучших возможностей для вас сейчас.`,
        cta: 'Посмотреть возможность',
        to: `/opportunities/${topOpportunity.id}`,
      }
    }
    return {
      title: 'Изучите новые возможности',
      description: 'Стажировки, проекты и хакатоны обновляются регулярно — проверьте, что подходит вам.',
      cta: 'Смотреть возможности',
      to: '/opportunities',
    }
  }, [profile, opportunitiesQuery.data])

  const topOpportunities = (opportunitiesQuery.data || []).slice(0, 3)
  const readiness = gpsQuery.data ? Math.round((gpsQuery.data.currentScore / gpsQuery.data.maxScore) * 100) : 0
  const activeSubscriptions = (subscriptionsQuery.data || []).filter((s) => s.active)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero */}
      <div className="overflow-hidden rounded-3xl bg-brand-gradient p-6 text-white shadow-pop sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-white/80">{greeting()}{firstName ? `, ${firstName}` : ''} 👋</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">
              {profile?.profile.careerGoal ? `Цель: ${profile.profile.careerGoal}` : 'Куда движется ваша карьера?'}
            </h1>
            <p className="mt-2 max-w-lg text-sm text-white/85">
              {profile?.profile.university || 'UniPath MAX'} · отслеживайте прогресс, находите возможности и держите руку на пульсе университета.
            </p>
          </div>
          {!gpsQuery.isLoading && gpsQuery.data && (
            <div className="flex items-center gap-4 self-start rounded-2xl bg-white/10 p-4 backdrop-blur">
              <ReadinessRing value={readiness} size={84} />
              <div>
                <p className="text-xs uppercase tracking-wide text-white/70">Готовность к цели</p>
                <Link to="/career-gps" className="mt-1 inline-flex items-center gap-1 text-sm font-semibold text-white hover:underline">
                  Открыть карьерный навигатор <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Next best action */}
      <Card className="border-brand-100 bg-brand-50/60">
        <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-soft">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">Сейчас важнее всего</p>
              <h2 className="text-base font-semibold text-ink-900">{nextAction.title}</h2>
              <p className="mt-0.5 text-sm text-ink-600">{nextAction.description}</p>
            </div>
          </div>
          <Link
            to={nextAction.to}
            className="inline-flex h-11 w-full shrink-0 items-center justify-center gap-1.5 rounded-xl bg-brand-600 px-5 text-sm font-medium text-white shadow-soft transition-colors hover:bg-brand-700 sm:w-auto"
          >
            {nextAction.cta} <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recommended opportunities */}
        <Card className="lg:col-span-2" padding="none">
          <div className="flex items-center justify-between border-b border-ink-100 p-5">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} />
              <h2 className="text-base font-semibold text-ink-900">Рекомендованные возможности</h2>
            </div>
            <Link to="/opportunities" className="text-sm font-medium text-brand-600 hover:text-brand-700">
              Все возможности
            </Link>
          </div>
          <div className="divide-y divide-ink-100">
            {opportunitiesQuery.isLoading &&
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="space-y-2 p-5">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              ))}
            {opportunitiesQuery.isError && (
              <div className="p-5">
                <ErrorState onRetry={() => opportunitiesQuery.refetch()} />
              </div>
            )}
            {!opportunitiesQuery.isLoading && !opportunitiesQuery.isError && topOpportunities.length === 0 && (
              <div className="p-5">
                <EmptyState title="Пока нет доступных возможностей" message="Загляните позже — университет публикует новые стажировки и проекты регулярно." />
              </div>
            )}
            {topOpportunities.map((opp) => (
              <Link
                key={opp.id}
                to={`/opportunities/${opp.id}`}
                className="flex items-center justify-between gap-4 p-5 transition-colors hover:bg-ink-50/70"
              >
                <div className="min-w-0">
                  <div className="mb-1 flex items-center gap-2">
                    <Badge tone="brand">{opportunityTypeLabels[opp.type] || opp.type}</Badge>
                    {opp.deadline && (
                      <span className="text-xs text-ink-400">до {new Date(opp.deadline).toLocaleDateString('ru-RU')}</span>
                    )}
                  </div>
                  <h3 className="truncate text-sm font-semibold text-ink-900">{opp.title}</h3>
                  <p className="truncate text-xs text-ink-500">{opp.company}</p>
                </div>
                <div className="shrink-0 text-right">
                  <div className="text-lg font-bold text-brand-600">{opp.matchPercentage}%</div>
                  <div className="text-[11px] text-ink-400">совпадение</div>
                </div>
              </Link>
            ))}
          </div>
        </Card>

        {/* Right column */}
        <div className="space-y-6">
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Target className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} />
              <h2 className="text-base font-semibold text-ink-900">Что подтянуть</h2>
            </div>
            {gpsQuery.isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : gpsQuery.data && gpsQuery.data.nextSteps.length > 0 ? (
              <ul className="space-y-2.5">
                {gpsQuery.data.nextSteps.slice(0, 3).map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-ink-600">
                    <ListChecks className="mt-0.5 h-4 w-4 shrink-0 text-accent-600" />
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-500">Пока нет рекомендаций — заполните профиль и навыки.</p>
            )}
            <Link to="/career-gps" className="mt-4 flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700">
              <Compass className="h-4 w-4" /> Подробный разбор
            </Link>
          </Card>

          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Bookmark className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} />
              <h2 className="text-base font-semibold text-ink-900">Ваши подписки</h2>
            </div>
            {subscriptionsQuery.isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : activeSubscriptions.length > 0 ? (
              <ul className="flex flex-wrap gap-2">
                {activeSubscriptions.map((sub) => (
                  <li key={sub.id}>
                    <Badge tone={sub.newItems > 0 ? 'success' : 'neutral'}>
                      {sub.topic}
                      {sub.newItems > 0 && ` · ${sub.newItems}`}
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-500">Подпишитесь на темы на странице «Возможности», чтобы не пропускать новое.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
