import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Bell, Bookmark, BookmarkCheck, Calendar, Search, SlidersHorizontal, X } from 'lucide-react'
import { createSubscription, fetchOpportunities, fetchSubscriptions, saveOpportunity, searchKnowledge, unsaveOpportunity } from '@/lib/endpoints'
import { userQueryKey } from '@/lib/queryClient'
import { useAuthStore } from '@/stores/authStore'
import { opportunityTypeOptions, opportunityTypeLabels, daysUntil, matchTone } from '@/lib/labels'
import { Badge, Button, Card, Chip, EmptyState, ErrorState, Input, LoadingState, Sheet, useToast } from '@/ui'
import type { Opportunity } from '@/types'

const matchBg: Record<string, string> = {
  success: 'bg-accent-50',
  brand: 'bg-brand-50',
  warning: 'bg-amber-50',
  danger: 'bg-rose-50',
}

function useDebounced<T>(value: T, delay = 400): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(handle)
  }, [value, delay])
  return debounced
}

function DeadlineBadge({ deadline }: { deadline: string | null }) {
  if (!deadline) return null
  const days = daysUntil(deadline)
  if (days === null) return null
  const tone = days <= 3 ? 'danger' : days <= 10 ? 'warning' : 'neutral'
  return (
    <span className="inline-flex items-center gap-1 text-xs text-ink-500">
      <Calendar className="h-3.5 w-3.5" />
      {days >= 0 ? (
        <Badge tone={tone} size="sm">{days === 0 ? 'Дедлайн сегодня' : `${days} дн. до дедлайна`}</Badge>
      ) : (
        <Badge tone="neutral" size="sm">Дедлайн прошёл</Badge>
      )}
    </span>
  )
}

function OpportunityCard({ opportunity, onToggleSave, saving }: { opportunity: Opportunity; onToggleSave: (o: Opportunity) => void; saving: boolean }) {
  return (
    <Card interactive padding="none" className="overflow-hidden">
      <Link to={`/opportunities/${opportunity.id}`} className="block p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge tone="brand">{opportunityTypeLabels[opportunity.type] || opportunity.type}</Badge>
              <DeadlineBadge deadline={opportunity.deadline} />
            </div>
            <h3 className="truncate text-base font-semibold text-ink-900">{opportunity.title}</h3>
            <p className="mt-0.5 truncate text-sm text-ink-500">
              {opportunity.company} {opportunity.location && `· ${opportunity.location}`} {opportunity.remote && '· удалённо'}
            </p>
          </div>
          <div className={`shrink-0 rounded-xl px-3 py-2 text-center ${matchBg[matchTone(opportunity.matchPercentage)]}`}>
            <div className="text-lg font-bold text-ink-900">{opportunity.matchPercentage}%</div>
            <div className="text-[10px] font-medium uppercase tracking-wide text-ink-400">совпадение</div>
          </div>
        </div>
        {opportunity.matchReasons.length > 0 && (
          <p className="mt-3 truncate text-xs text-accent-700">✓ {opportunity.matchReasons[0]}</p>
        )}
      </Link>
      <div className="flex items-center justify-between border-t border-ink-100 px-5 py-2.5">
        <Link to={`/opportunities/${opportunity.id}`} className="text-sm font-medium text-brand-600 hover:text-brand-700">
          Подробнее
        </Link>
        <button
          onClick={(e) => {
            e.preventDefault()
            onToggleSave(opportunity)
          }}
          disabled={saving}
          className="rounded-lg p-1.5 text-ink-400 transition-colors hover:bg-ink-100 hover:text-brand-600 disabled:opacity-50"
          aria-label={opportunity.isSaved ? 'Убрать из сохранённого' : 'Сохранить'}
        >
          {opportunity.isSaved ? <BookmarkCheck className="h-5 w-5 text-brand-600" /> : <Bookmark className="h-5 w-5" />}
        </button>
      </div>
    </Card>
  )
}

export default function Opportunities() {
  const userId = useAuthStore((state) => state.user?.id ?? null)
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const queryClient = useQueryClient()

  useEffect(() => {
    const highlighted = searchParams.get('opportunity')
    if (highlighted) navigate(`/opportunities/${highlighted}`, { replace: true })
  }, [searchParams, navigate])

  const [search, setSearch] = useState('')
  const [type, setType] = useState<string | undefined>()
  const [minMatch, setMinMatch] = useState<number | undefined>()
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [subscribeOpen, setSubscribeOpen] = useState(false)
  const [topic, setTopic] = useState('')
  const debouncedSearch = useDebounced(search)

  const filters = useMemo(() => ({ search: debouncedSearch, type, minMatch }), [debouncedSearch, type, minMatch])
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: userQueryKey(userId, 'opportunities', filters),
    queryFn: () => fetchOpportunities(filters),
  })
  const { data: subscriptions = [] } = useQuery({
    queryKey: userQueryKey(userId, 'subscriptions'),
    queryFn: fetchSubscriptions,
  })

  const saveMutation = useMutation({
    mutationFn: (o: Opportunity) => (o.isSaved ? unsaveOpportunity(o.id) : saveOpportunity(o.id)),
    onMutate: async (o) => {
      const opportunitiesKey = userQueryKey(userId, 'opportunities', filters)
      await queryClient.cancelQueries({ queryKey: opportunitiesKey })
      queryClient.setQueryData<Opportunity[]>(opportunitiesKey, (old) =>
        old?.map((item) => (item.id === o.id ? { ...item, isSaved: !item.isSaved } : item)),
      )
    },
    onError: () => toast.error('Не удалось сохранить возможность', 'Попробуйте ещё раз.'),
    onSuccess: (_, o) => toast.success(o.isSaved ? 'Убрано из сохранённого' : 'Сохранено'),
    onSettled: () => queryClient.invalidateQueries({ queryKey: userQueryKey(userId, 'opportunities') }),
  })

  const subscribeMutation = useMutation({
    mutationFn: async (term: string) => {
      const subscription = await createSubscription(term)
      let knowledge = null
      try {
        knowledge = await searchKnowledge(term)
      } catch {
        // Subscription creation should succeed even if knowledge search is temporarily unavailable.
      }
      return { subscription, knowledge }
    },
    onSuccess: ({ knowledge }) => {
      const article = knowledge?.results[0]
      toast.success('Подписка создана', article ? 'Нашли материал по этому термину в базе знаний.' : 'Мы пришлём уведомление, когда появится подходящая возможность.')
      setSubscribeOpen(false)
      setTopic('')
      queryClient.invalidateQueries({ queryKey: userQueryKey(userId, 'subscriptions') })
      if (article) navigate(`/knowledge/${article.id}`)
    },
    onError: () => toast.error('Не удалось создать подписку'),
  })

  const activeFilterCount = (type ? 1 : 0) + (minMatch ? 1 : 0)
  const searchTerm = search.trim()
  const alreadySubscribed = subscriptions.some((subscription) =>
    subscription.active && subscription.topic.trim().toLocaleLowerCase() === searchTerm.toLocaleLowerCase(),
  )

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Возможности для вас</h1>
        <p className="text-sm text-ink-500">Стажировки, проекты и хакатоны, отсортированные по совпадению с вашим профилем.</p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4.5 w-4.5 -translate-y-1/2 text-ink-400" style={{ height: 18, width: 18 }} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Искать по названию, навыкам…"
            className="w-full rounded-xl border border-ink-200 bg-white py-2.5 pl-10 pr-4 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            aria-label="Искать возможности"
          />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setFiltersOpen(true)} leftIcon={<SlidersHorizontal className="h-4 w-4" />}>
            Фильтры{activeFilterCount > 0 && ` (${activeFilterCount})`}
          </Button>
          <Button variant="secondary" onClick={() => setSubscribeOpen(true)} leftIcon={<Bell className="h-4 w-4" />}>
            Подписаться
          </Button>
        </div>
      </div>

      {searchTerm.length >= 2 && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-brand-100 bg-brand-50/70 px-4 py-3">
          <p className="text-sm text-ink-700">
            {alreadySubscribed
              ? `Вы уже подписаны на «${searchTerm}».`
              : `Следить за новыми возможностями по теме «${searchTerm}»?`}
          </p>
          {!alreadySubscribed && (
            <Button size="sm" variant="outline" onClick={() => { setTopic(searchTerm); setSubscribeOpen(true) }}>
              Подписаться на тему
            </Button>
          )}
        </div>
      )}

      {activeFilterCount > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          {type && (
            <Chip selected onClick={() => setType(undefined)}>
              {opportunityTypeLabels[type as keyof typeof opportunityTypeLabels]} <X className="ml-1 h-3.5 w-3.5" />
            </Chip>
          )}
          {minMatch && (
            <Chip selected onClick={() => setMinMatch(undefined)}>
              от {minMatch}% <X className="ml-1 h-3.5 w-3.5" />
            </Chip>
          )}
        </div>
      )}

      {isLoading && <LoadingState label="Подбираем возможности…" />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {!isLoading && !isError && (!data || data.length === 0) && (
        <EmptyState
          title={search || activeFilterCount > 0 ? 'Ничего не найдено' : 'Пока нет доступных возможностей'}
          message={search || activeFilterCount > 0 ? 'Попробуйте изменить запрос или сбросить фильтры.' : 'Загляните позже — университет публикует новые возможности регулярно.'}
          action={
            (search || activeFilterCount > 0) && (
              <Button size="sm" variant="outline" onClick={() => { setSearch(''); setType(undefined); setMinMatch(undefined) }}>
                Сбросить фильтры
              </Button>
            )
          }
        />
      )}
      {!isLoading && !isError && data && data.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {data.map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} onToggleSave={(o) => saveMutation.mutate(o)} saving={saveMutation.isPending} />
          ))}
        </div>
      )}

      <Sheet open={filtersOpen} onClose={() => setFiltersOpen(false)} title="Фильтры">
        <div className="space-y-5">
          <div>
            <p className="mb-2 text-sm font-medium text-ink-800">Тип</p>
            <div className="flex flex-wrap gap-2">
              {opportunityTypeOptions.map((opt) => (
                <Chip key={opt.value} selected={type === opt.value} onClick={() => setType(type === opt.value ? undefined : opt.value)}>
                  {opt.label}
                </Chip>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-2 text-sm font-medium text-ink-800">Минимальное совпадение</p>
            <div className="flex flex-wrap gap-2">
              {[40, 60, 80].map((value) => (
                <Chip key={value} selected={minMatch === value} onClick={() => setMinMatch(minMatch === value ? undefined : value)}>
                  от {value}%
                </Chip>
              ))}
            </div>
          </div>
          <Button fullWidth onClick={() => setFiltersOpen(false)}>Показать результаты</Button>
        </div>
      </Sheet>

      <Sheet open={subscribeOpen} onClose={() => setSubscribeOpen(false)} title="Подписаться на тему">
        <div className="space-y-4">
          <p className="text-sm text-ink-500">Получайте уведомления о новых возможностях, где встречается выбранный термин.</p>
          <Input label="Термин" value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Например, BIM" />
          <Button fullWidth loading={subscribeMutation.isPending} disabled={!topic.trim()} onClick={() => subscribeMutation.mutate(topic.trim())}>
            Создать подписку
          </Button>
        </div>
      </Sheet>
    </div>
  )
}
