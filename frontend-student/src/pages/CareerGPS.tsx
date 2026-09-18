import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowRight, Award, Compass, MapPin, ShieldCheck, TrendingUp } from 'lucide-react'
import { fetchCareerAnalysis, fetchCareerGoals } from '@/lib/endpoints'
import { Badge, Chip, EmptyState, ErrorState, LoadingState, ProgressBar, ReadinessRing } from '@/ui'

const priorityTone: Record<string, 'danger' | 'warning' | 'neutral'> = {
  high: 'danger',
  medium: 'warning',
  low: 'neutral',
}
const priorityLabels: Record<string, string> = { high: 'Приоритет', medium: 'Важно', low: 'Можно позже' }

export default function CareerGPS() {
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null)

  const goalsQuery = useQuery({ queryKey: ['career-goals'], queryFn: fetchCareerGoals })

  useEffect(() => {
    if (goalsQuery.data && goalsQuery.data.length > 0 && selectedGoalId === null) {
      setSelectedGoalId(goalsQuery.data[0].id)
    }
  }, [goalsQuery.data, selectedGoalId])

  const analysisQuery = useQuery({
    queryKey: ['career-analysis', selectedGoalId],
    queryFn: () => fetchCareerAnalysis(selectedGoalId as number),
    enabled: selectedGoalId !== null,
  })

  if (goalsQuery.isLoading) return <LoadingState label="Загружаем карьерные цели…" />
  if (goalsQuery.isError) return <ErrorState onRetry={() => goalsQuery.refetch()} />

  if (!goalsQuery.data || goalsQuery.data.length === 0) {
    return (
      <EmptyState
        icon={<Compass className="h-6 w-6 text-ink-400" />}
        title="Карьерные роли пока не заведены"
        message="Как только университет опубликует карьерные роли, здесь появится ваш персональный маршрут."
      />
    )
  }

  const analysis = analysisQuery.data

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Career GPS</h1>
        <p className="mt-1 text-sm text-ink-500">Где вы сейчас, куда идёте и что нужно подтянуть, чтобы дойти быстрее.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {goalsQuery.data.map((goal) => (
          <Chip key={goal.id} selected={goal.id === selectedGoalId} onClick={() => setSelectedGoalId(goal.id)}>
            {goal.title}
          </Chip>
        ))}
      </div>

      {analysisQuery.isLoading && <LoadingState label="Считаем вашу готовность…" />}
      {analysisQuery.isError && <ErrorState onRetry={() => analysisQuery.refetch()} />}

      {analysis && (
        <div className="space-y-6">
          {/* Destination + readiness */}
          <div className="overflow-hidden rounded-3xl border border-ink-100 bg-white shadow-soft">
            <div className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand-600">
                  <MapPin className="h-3.5 w-3.5" /> Ваша цель
                </p>
                <h2 className="mt-1 text-xl font-bold text-ink-900">{analysis.goal.title}</h2>
                <p className="mt-1 max-w-md text-sm text-ink-500">{analysis.goal.description}</p>
              </div>
              <div className="flex items-center gap-4 self-start rounded-2xl bg-ink-50 p-4">
                <ReadinessRing value={analysis.readinessScore} />
                <div>
                  <p className="text-xs uppercase tracking-wide text-ink-400">Готовность</p>
                  <p className="text-sm font-medium text-ink-700">
                    {analysis.readinessScore >= 80 ? 'Почти на месте' : analysis.readinessScore >= 40 ? 'В процессе' : 'Только старт'}
                  </p>
                </div>
              </div>
            </div>
            <div className="border-t border-ink-100 bg-ink-50/60 px-6 py-3 text-xs text-ink-400">
              Обновлено {new Date(analysis.lastUpdated).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-ink-100 bg-white p-6 shadow-soft">
              <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-ink-900">
                <ShieldCheck className="h-4.5 w-4.5 text-accent-600" style={{ height: 18, width: 18 }} /> Ваши сильные стороны
              </h3>
              {analysis.strengths.length > 0 ? (
                <ul className="space-y-3">
                  {analysis.strengths.map((strength, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-ink-700">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent-100 text-accent-700">
                        <Award className="h-3 w-3" />
                      </span>
                      {strength}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-ink-500">Добавьте навыки в профиль, чтобы увидеть свои сильные стороны.</p>
              )}
            </div>

            <div className="rounded-2xl border border-ink-100 bg-white p-6 shadow-soft">
              <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-ink-900">
                <TrendingUp className="h-4.5 w-4.5 text-amber-600" style={{ height: 18, width: 18 }} /> Чего не хватает
              </h3>
              {analysis.gaps.length > 0 ? (
                <div className="space-y-4">
                  {analysis.gaps.map((gap, i) => (
                    <div key={i}>
                      <div className="mb-1.5 flex items-center justify-between">
                        <span className="text-sm font-medium text-ink-900">{gap.skill}</span>
                        <Badge tone={priorityTone[gap.priority]}>{priorityLabels[gap.priority]}</Badge>
                      </div>
                      <ProgressBar
                        value={gap.currentLevel}
                        max={gap.requiredLevel}
                        tone={gap.priority === 'high' ? 'danger' : gap.priority === 'medium' ? 'warning' : 'brand'}
                        size="sm"
                      />
                      <p className="mt-1 text-xs text-ink-400">
                        {gap.currentLevel}/5 сейчас · нужно {gap.requiredLevel}/5
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink-500">Пробелов не найдено — вы готовы к этой роли.</p>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-ink-100 bg-white p-6 shadow-soft">
            <h3 className="mb-4 text-base font-semibold text-ink-900">Что делать дальше</h3>
            {analysis.nextActions.length > 0 ? (
              <ol className="space-y-3">
                {analysis.nextActions.map((action) => (
                  <li key={action.id} className="flex items-center gap-4 rounded-xl border border-ink-100 p-4">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                      {action.priority}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-ink-900">{action.title}</p>
                      <p className="text-xs text-ink-400">{action.estimatedTime}</p>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-ink-500">Срочных действий нет — так держать!</p>
            )}
            <Link
              to="/opportunities"
              className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700"
            >
              Найти подходящие возможности <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
