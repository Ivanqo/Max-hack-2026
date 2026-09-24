import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { BookOpen, CheckCircle2, LifeBuoy, Search } from 'lucide-react'
import { fetchKnowledgeList, searchKnowledge } from '@/lib/endpoints'
import { userQueryKey } from '@/lib/queryClient'
import { useAuthStore } from '@/stores/authStore'
import { Badge, Chip, EmptyState, ErrorState, LoadingState, Skeleton } from '@/ui'
import type { KnowledgeItem } from '@/types'

function useDebounced<T>(value: T, delay = 400): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(handle)
  }, [value, delay])
  return debounced
}

function KnowledgeCard({ item }: { item: KnowledgeItem }) {
  return (
    <Link
      to={`/knowledge/${item.id}`}
      className="flex flex-col rounded-2xl border border-ink-100 bg-white p-5 shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-card"
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <Badge tone="brand">{item.category}</Badge>
        {item.verified && <CheckCircle2 className="h-4.5 w-4.5 shrink-0 text-accent-600" style={{ height: 18, width: 18 }} aria-label="Проверено" />}
      </div>
      <h3 className="line-clamp-2 text-sm font-semibold text-ink-900">{item.title}</h3>
      <p className="mt-1.5 line-clamp-3 flex-1 text-sm text-ink-500">{item.summary}</p>
      <div className="mt-3 flex items-center justify-between text-xs text-ink-400">
        <span className="truncate">{item.source.name}</span>
        {typeof item.relevanceScore === 'number' && (
          <span className="shrink-0 rounded-full bg-brand-50 px-2 py-0.5 font-medium text-brand-700">
            {Math.round(item.relevanceScore * 100)}%
          </span>
        )}
      </div>
    </Link>
  )
}

export default function Knowledge() {
  const userId = useAuthStore((state) => state.user?.id ?? null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<string | null>(null)
  const debouncedQuery = useDebounced(query)
  const isSearching = debouncedQuery.trim().length > 0

  const searchQuery = useQuery({
    queryKey: userQueryKey(userId, 'knowledge-search', debouncedQuery),
    queryFn: () => searchKnowledge(debouncedQuery),
    enabled: isSearching,
  })

  const browseQuery = useQuery({
    queryKey: userQueryKey(userId, 'knowledge-list'),
    queryFn: fetchKnowledgeList,
    enabled: !isSearching,
  })

  const categories = useMemo(() => {
    const set = new Set((browseQuery.data || []).map((item) => item.category))
    return Array.from(set)
  }, [browseQuery.data])

  const filteredBrowse = useMemo(() => {
    if (!browseQuery.data) return []
    return category ? browseQuery.data.filter((item) => item.category === category) : browseQuery.data
  }, [browseQuery.data, category])

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">База знаний</h1>
        <p className="mt-1 text-sm text-ink-500">Проверенные ответы университета — с источником и датой актуальности.</p>
      </div>

      <div className="relative">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4.5 w-4.5 -translate-y-1/2 text-ink-400" style={{ height: 18, width: 18 }} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Например: «как оформить практику»"
          className="w-full rounded-xl border border-ink-200 bg-white py-3 pl-10 pr-4 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          aria-label="Поиск по базе знаний"
        />
      </div>

      {!isSearching && categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <Chip selected={category === null} onClick={() => setCategory(null)}>Все темы</Chip>
          {categories.map((cat) => (
            <Chip key={cat} selected={category === cat} onClick={() => setCategory(category === cat ? null : cat)}>
              {cat}
            </Chip>
          ))}
        </div>
      )}

      {isSearching ? (
        <div>
          {searchQuery.isLoading && <LoadingState label="Ищем в базе знаний…" />}
          {searchQuery.isError && <ErrorState onRetry={() => searchQuery.refetch()} />}
          {searchQuery.data && searchQuery.data.results.length === 0 && (
            <EmptyState
              icon={<LifeBuoy className="h-6 w-6 text-ink-400" />}
              title="Подтверждённого ответа пока нет"
              message={searchQuery.data.message || `По запросу «${debouncedQuery}» ничего не найдено. Попробуйте переформулировать вопрос.`}
              action={
                searchQuery.data.escalation && (
                  <div className="rounded-xl bg-ink-50 px-4 py-2 text-sm text-ink-600">
                    Обратитесь: {searchQuery.data.escalation.unit} · {searchQuery.data.escalation.contact}
                  </div>
                )
              }
            />
          )}
          {searchQuery.data && searchQuery.data.results.length > 0 && (
            <>
              <p className="mb-3 text-sm text-ink-500">Найдено: {searchQuery.data.total}</p>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {searchQuery.data.results.map((item) => (
                  <KnowledgeCard key={item.id} item={item} />
                ))}
              </div>
            </>
          )}
        </div>
      ) : (
        <div>
          {browseQuery.isLoading && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
            </div>
          )}
          {browseQuery.isError && <ErrorState onRetry={() => browseQuery.refetch()} />}
          {browseQuery.data && filteredBrowse.length === 0 && (
            <EmptyState icon={<BookOpen className="h-6 w-6 text-ink-400" />} title="Материалов пока нет" message="Университет ещё не опубликовал материалы в этой категории." />
          )}
          {filteredBrowse.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {filteredBrowse.map((item) => (
                <KnowledgeCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
