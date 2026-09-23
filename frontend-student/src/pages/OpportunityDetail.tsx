import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Bookmark, BookmarkCheck, Calendar, ExternalLink, MapPin } from 'lucide-react'
import { fetchOpportunityDetail, saveOpportunity, unsaveOpportunity } from '@/lib/endpoints'
import { opportunityTypeLabels, formatDate } from '@/lib/labels'
import { Badge, Button, Card, ErrorState, LoadingState, ReadinessRing, useToast } from '@/ui'

export default function OpportunityDetail() {
  const { id = '' } = useParams()
  const toast = useToast()
  const queryClient = useQueryClient()

  const { data: opportunity, isLoading, isError, refetch } = useQuery({
    queryKey: ['opportunity', id],
    queryFn: () => fetchOpportunityDetail(id),
  })

  const saveMutation = useMutation({
    mutationFn: () => (opportunity?.isSaved ? unsaveOpportunity(id) : saveOpportunity(id)),
    onSuccess: () => {
      toast.success(opportunity?.isSaved ? 'Убрано из сохранённого' : 'Сохранено')
      queryClient.invalidateQueries({ queryKey: ['opportunity', id] })
      queryClient.invalidateQueries({ queryKey: ['opportunities'] })
    },
    onError: () => toast.error('Не удалось сохранить возможность'),
  })

  if (isLoading) return <LoadingState label="Загружаем возможность…" />
  if (isError || !opportunity) return <ErrorState title="Не удалось загрузить возможность" onRetry={() => refetch()} />

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      <Link to="/opportunities" className="inline-flex items-center gap-1.5 text-sm font-medium text-ink-500 hover:text-ink-800">
        <ArrowLeft className="h-4 w-4" /> Все возможности
      </Link>

      <div className="rounded-3xl border border-ink-100 bg-white p-6 shadow-soft sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge tone="brand">{opportunityTypeLabels[opportunity.type] || opportunity.type}</Badge>
              <Badge tone={opportunity.verifiedStatus === 'verified' ? 'success' : 'neutral'}>
                {opportunity.verifiedStatus === 'verified' ? 'Проверено университетом' : 'На проверке'}
              </Badge>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-ink-900">{opportunity.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink-500">
              <span>{opportunity.company}</span>
              {opportunity.location && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" /> {opportunity.location}{opportunity.remote && ' · удалённо'}
                </span>
              )}
              {opportunity.deadline && (
                <span className="inline-flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" /> до {formatDate(opportunity.deadline)}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3 self-start rounded-2xl bg-ink-50 p-3">
            <ReadinessRing value={opportunity.matchPercentage} size={64} />
            <div>
              <p className="text-xs uppercase tracking-wide text-ink-400">Совпадение</p>
              <p className="text-sm font-medium text-ink-700">с вашим профилем</p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          {opportunity.sourceUrl ? (
            <a
              href={opportunity.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-brand-600 px-5 text-sm font-semibold text-white shadow-soft transition-colors hover:bg-brand-700 sm:flex-none"
            >
              Откликнуться / открыть источник <ExternalLink className="h-4 w-4" />
            </a>
          ) : (
            <div className="flex flex-1 items-center rounded-xl border border-dashed border-ink-200 bg-ink-50 px-4 py-2.5 text-sm text-ink-500">
              Источник ещё не указан — сохраните возможность, детали появятся позже.
            </div>
          )}
          <Button
            variant="outline"
            leftIcon={opportunity.isSaved ? <BookmarkCheck className="h-4 w-4 text-brand-600" /> : <Bookmark className="h-4 w-4" />}
            loading={saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {opportunity.isSaved ? 'Сохранено' : 'Сохранить'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3 text-base font-semibold text-ink-900">Почему подходит</h2>
          {opportunity.matchReasons.length > 0 ? (
            <ul className="space-y-2">
              {opportunity.matchReasons.map((reason, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink-700">
                  <span className="mt-0.5 text-accent-600">✓</span> {reason}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Заполните профиль и навыки, чтобы увидеть персональные причины совпадения.</p>
          )}
        </Card>
        <Card>
          <h2 className="mb-3 text-base font-semibold text-ink-900">Чего не хватает</h2>
          {opportunity.gaps.length > 0 ? (
            <ul className="space-y-2">
              {opportunity.gaps.map((gap, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink-700">
                  <span className="mt-0.5 text-amber-500">⚠</span> {gap}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Пробелов не найдено — вы соответствуете требованиям.</p>
          )}
          <Link to="/career-gps" className="mt-3 inline-block text-sm font-medium text-brand-600 hover:text-brand-700">
            Посмотреть карьерный маршрут →
          </Link>
        </Card>
      </div>

      <Card>
        <h2 className="mb-3 text-base font-semibold text-ink-900">Описание</h2>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-700">{opportunity.description}</p>
      </Card>

      {opportunity.requirements.length > 0 && (
        <Card>
          <h2 className="mb-3 text-base font-semibold text-ink-900">Требования</h2>
          <div className="flex flex-wrap gap-2">
            {opportunity.requirements.map((req, i) => (
              <Badge key={i} tone="neutral" size="md">{req}</Badge>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
