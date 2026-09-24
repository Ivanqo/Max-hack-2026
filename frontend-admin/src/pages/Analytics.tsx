import { useQuery } from '@tanstack/react-query';
import { Activity, Bookmark, Eye, Search, TrendingUp, Users } from 'lucide-react';
import { fetchAnalytics } from '@/api/endpoints';
import { useAuthUser } from '@/contexts/AuthContext';
import { adminQueryKey } from '@/lib/adminQueryScope';
import { Card, EmptyState, ErrorState, LoadingState, ProgressBar } from '@/ui';

export const Analytics = () => {
  const user = useAuthUser();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: adminQueryKey(user, 'analytics'), queryFn: fetchAnalytics });

  if (isLoading) return <LoadingState label="Загружаем аналитику…" />;
  if (isError || !data) return <ErrorState onRetry={() => refetch()} />;

  const engagementPct = data.totalUsers > 0 ? Math.round((data.activeUsers / data.totalUsers) * 100) : 0;
  const maxGrowth = Math.max(...data.userGrowth.map((p) => p.count), 1);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Аналитика</h1>
        <p className="mt-1 text-sm text-ink-500">Данные считаются по реальным событиям взаимодействия студентов.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-medium text-ink-600">Всего пользователей</h3>
            <Users className="h-5 w-5 text-brand-500" />
          </div>
          <p className="text-3xl font-bold text-ink-900">{data.totalUsers}</p>
          <p className="mt-1 text-xs text-ink-400">{data.activeUsers} активных аккаунтов</p>
        </Card>
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-medium text-ink-600">Вовлечённость</h3>
            <Activity className="h-5 w-5 text-accent-500" />
          </div>
          <p className="text-3xl font-bold text-ink-900">{engagementPct}%</p>
          <ProgressBar value={engagementPct} tone="success" size="sm" className="mt-2" />
        </Card>
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-medium text-ink-600">Открытия / сохранения</h3>
            <TrendingUp className="h-5 w-5 text-amber-500" />
          </div>
          <p className="text-3xl font-bold text-ink-900">{data.opportunityViews}</p>
          <p className="mt-1 flex items-center gap-1 text-xs text-ink-400"><Bookmark className="h-3 w-3" /> {data.opportunitySaves} сохранений</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-base font-semibold text-ink-900">Рост пользователей</h2>
          {data.userGrowth.length > 0 ? (
            <div className="space-y-2">
              {data.userGrowth.slice(-10).map((point) => (
                <div key={point.date} className="flex items-center gap-3 text-sm">
                  <span className="w-20 shrink-0 text-ink-500">{new Date(point.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}</span>
                  <ProgressBar value={point.count} max={maxGrowth} size="sm" className="flex-1" />
                  <span className="w-8 shrink-0 text-right font-semibold text-ink-900">{point.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Недостаточно данных" />
          )}
        </Card>

        <Card>
          <div className="mb-4 flex items-center gap-2">
            <Search className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} />
            <h2 className="text-base font-semibold text-ink-900">Популярные запросы</h2>
          </div>
          {data.topSearchQueries.length > 0 ? (
            <ul className="space-y-2">
              {data.topSearchQueries.map((item, i) => (
                <li key={item.query} className="flex items-center gap-3 text-sm">
                  <span className="w-5 shrink-0 text-ink-400">#{i + 1}</span>
                  <span className="flex-1 truncate text-ink-700">«{item.query}»</span>
                  <span className="font-semibold text-ink-900">{item.count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="Пока нет данных" />
          )}
        </Card>

        <Card>
          <div className="mb-4 flex items-center gap-2">
            <Eye className="h-4.5 w-4.5 text-rose-600" style={{ height: 18, width: 18 }} />
            <h2 className="text-base font-semibold text-ink-900">Запросы без ответа</h2>
          </div>
          {data.unansweredQueries.length > 0 ? (
            <ul className="space-y-2">
              {data.unansweredQueries.map((item) => (
                <li key={item.query} className="flex items-center justify-between rounded-lg bg-rose-50/60 px-3 py-2 text-sm">
                  <span className="truncate text-ink-800">«{item.query}»</span>
                  <span className="font-semibold text-rose-700">{item.count}×</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Все запросы студентов находят подтверждённый ответ.</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-4 text-base font-semibold text-ink-900">Статистика контента</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-ink-100 pb-3">
              <span className="text-sm text-ink-600">Материалы базы знаний</span>
              <span className="text-xl font-bold text-ink-900">{data.publishedKnowledge}<span className="text-sm font-normal text-ink-400"> / {data.totalKnowledgeBase}</span></span>
            </div>
            <div className="flex items-center justify-between border-b border-ink-100 pb-3">
              <span className="text-sm text-ink-600">Активные возможности</span>
              <span className="text-xl font-bold text-ink-900">{data.activeOpportunities}<span className="text-sm font-normal text-ink-400"> / {data.totalOpportunities}</span></span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-ink-600">Карьерные роли с интересом</span>
              <span className="text-xl font-bold text-ink-900">{data.popularRoles.length}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
