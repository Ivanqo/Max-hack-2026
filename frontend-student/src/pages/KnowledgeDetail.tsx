import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, CalendarClock, CheckCircle2, ExternalLink, ShieldAlert } from 'lucide-react'
import { fetchKnowledgeDetail } from '@/lib/endpoints'
import { knowledgeAudienceLabels, formatDate } from '@/lib/labels'
import { Badge, Card, ErrorState, LoadingState } from '@/ui'

export default function KnowledgeDetail() {
  const { id = '' } = useParams()
  const { data: item, isLoading, isError, refetch } = useQuery({
    queryKey: ['knowledge-item', id],
    queryFn: () => fetchKnowledgeDetail(id),
  })

  if (isLoading) return <LoadingState label="Загружаем материал…" />
  if (isError || !item) return <ErrorState title="Материал не найден" onRetry={() => refetch()} />

  const isOutdated = item.verifiedStatus === 'outdated'

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      <Link to="/knowledge" className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 hover:text-ink-800">
        <ArrowLeft className="h-4 w-4" /> База знаний
      </Link>

      <Card>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge tone="brand">{item.category}</Badge>
          {item.verified ? (
            <Badge tone="success"><CheckCircle2 className="h-3.5 w-3.5" /> Проверено университетом</Badge>
          ) : (
            <Badge tone="neutral">На проверке</Badge>
          )}
          {isOutdated && (
            <Badge tone="danger"><ShieldAlert className="h-3.5 w-3.5" /> Информация устарела</Badge>
          )}
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-ink-900">{item.title}</h1>

        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm text-ink-500">
          <span>Источник: {item.source.name}</span>
          <span className="inline-flex items-center gap-1">
            <CalendarClock className="h-3.5 w-3.5" /> Обновлено {formatDate(item.updatedAt)}
          </span>
          {item.actualUntil && <span>Актуально до {formatDate(item.actualUntil)}</span>}
        </div>

        {item.audience.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {item.audience.map((a) => (
              <Badge key={a} tone="neutral" size="sm">{knowledgeAudienceLabels[a] || a}</Badge>
            ))}
          </div>
        )}

        <div className="mt-6 whitespace-pre-wrap rounded-2xl bg-ink-50/70 p-5 text-sm leading-relaxed text-ink-700">
          {item.content}
        </div>

        {item.source.url && (
          <a
            href={item.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700"
          >
            Открыть источник <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </Card>
    </div>
  )
}
