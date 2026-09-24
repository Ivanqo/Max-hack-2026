import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { AlertCircle, BookOpen, Briefcase, Plus, Search, TrendingUp, Users } from 'lucide-react';
import { fetchAnalytics } from '@/api/endpoints';
import { useAuthUser } from '@/contexts/AuthContext';
import { adminQueryKey } from '@/lib/adminQueryScope';
import { Badge, Card, ErrorState, LoadingState } from '@/ui';

export const Dashboard = () => {
  const user = useAuthUser();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: adminQueryKey(user, 'analytics'), queryFn: fetchAnalytics });

  if (isLoading) return <LoadingState label="Загружаем панель…" />;
  if (isError || !data) return <ErrorState onRetry={() => refetch()} />;

  const stats = [
    { label: 'Пользователи', value: data.totalUsers, sub: `${data.activeUsers} активных`, icon: Users, tone: 'bg-brand-100 text-brand-700' },
    { label: 'Активные возможности', value: data.activeOpportunities, sub: `из ${data.totalOpportunities} всего`, icon: Briefcase, tone: 'bg-accent-100 text-accent-700' },
    { label: 'Опубликовано материалов', value: data.publishedKnowledge, sub: `из ${data.totalKnowledgeBase} всего`, icon: BookOpen, tone: 'bg-amber-100 text-amber-700' },
    { label: 'Открытий возможностей', value: data.opportunityViews, sub: `${data.opportunitySaves} сохранений`, icon: TrendingUp, tone: 'bg-sky-100 text-sky-700' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">Дашборд</h1>
          <p className="mt-1 text-sm text-ink-500">Актуальное состояние платформы вашего университета.</p>
        </div>
        <div className="flex gap-2">
          <Link to="/opportunities" className="inline-flex h-10 items-center gap-1.5 rounded-xl bg-brand-600 px-4 text-sm font-medium text-white hover:bg-brand-700">
            <Plus className="h-4 w-4" /> Возможность
          </Link>
          <Link to="/knowledge" className="inline-flex h-10 items-center gap-1.5 rounded-xl border border-ink-200 bg-white px-4 text-sm font-medium text-ink-700 hover:bg-ink-50">
            <Plus className="h-4 w-4" /> Материал
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink-500">{stat.label}</p>
                <p className="mt-1 text-3xl font-bold text-ink-900">{stat.value}</p>
                <p className="mt-0.5 text-xs text-ink-400">{stat.sub}</p>
              </div>
              <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${stat.tone}`}>
                <stat.icon className="h-5 w-5" />
              </span>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-4 flex items-center gap-2">
            <AlertCircle className="h-4.5 w-4.5 text-rose-600" style={{ height: 18, width: 18 }} />
            <h2 className="text-base font-semibold text-ink-900">Требует внимания: запросы без ответа</h2>
          </div>
          {data.unansweredQueries.length > 0 ? (
            <ul className="space-y-2">
              {data.unansweredQueries.slice(0, 6).map((item) => (
                <li key={item.query} className="flex items-center justify-between rounded-lg bg-rose-50/60 px-3 py-2 text-sm">
                  <span className="truncate text-ink-800">«{item.query}»</span>
                  <Badge tone="danger">{item.count}×</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Все поисковые запросы студентов находят ответ. Отлично!</p>
          )}
          {data.unansweredQueries.length > 0 && (
            <Link to="/knowledge" className="mt-3 inline-block text-sm font-medium text-brand-600 hover:text-brand-700">
              Добавить материалы →
            </Link>
          )}
        </Card>

        <Card>
          <div className="mb-4 flex items-center gap-2">
            <Search className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} />
            <h2 className="text-base font-semibold text-ink-900">Популярные запросы</h2>
          </div>
          {data.topSearchQueries.length > 0 ? (
            <ul className="space-y-2">
              {data.topSearchQueries.slice(0, 6).map((item) => (
                <li key={item.query} className="flex items-center justify-between text-sm">
                  <span className="truncate text-ink-700">«{item.query}»</span>
                  <span className="font-semibold text-ink-900">{item.count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Пока нет данных о поисковых запросах.</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-4 text-base font-semibold text-ink-900">Рост пользователей (14 дней)</h2>
          {data.userGrowth.length > 0 ? (
            <div className="flex h-32 items-end gap-1">
              {data.userGrowth.map((point) => {
                const max = Math.max(...data.userGrowth.map((p) => p.count), 1);
                return (
                  <div key={point.date} className="group relative flex-1">
                    <div
                      className="w-full rounded-t bg-brand-500/80 transition-colors group-hover:bg-brand-600"
                      style={{ height: `${Math.max(4, (point.count / max) * 100)}%` }}
                      title={`${point.date}: ${point.count}`}
                    />
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-ink-500">Недостаточно данных.</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-4 text-base font-semibold text-ink-900">Популярные карьерные роли</h2>
          {data.popularRoles.length > 0 ? (
            <ul className="space-y-2.5">
              {data.popularRoles.slice(0, 6).map((item) => (
                <li key={item.role} className="flex items-center justify-between text-sm">
                  <span className="text-ink-700">{item.role}</span>
                  <span className="font-semibold text-ink-900">Интересов: {item.count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-500">Карьерные роли пока не заведены.</p>
          )}
        </Card>
      </div>
    </div>
  );
};
