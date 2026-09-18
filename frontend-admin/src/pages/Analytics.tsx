import { useEffect, useState } from 'react';
import { TrendingUp, Users, Activity } from 'lucide-react';
import api from '@/api/client';
import { Analytics as AnalyticsType } from '@/types';

export const Analytics = () => {
  const [analytics, setAnalytics] = useState<AnalyticsType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await api.get('/admin/analytics');
        setAnalytics(response.data);
      } catch (error) {
        console.error('Не удалось загрузить аналитику:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Аналитика</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Всего пользователей</h3>
            <Users className="text-blue-500" size={24} />
          </div>
          <p className="text-4xl font-bold text-gray-900">{analytics?.totalUsers || 0}</p>
          <p className="text-sm text-gray-600 mt-2">Зарегистрированные аккаунты</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Активные пользователи</h3>
            <Activity className="text-green-500" size={24} />
          </div>
          <p className="text-4xl font-bold text-gray-900">{analytics?.activeUsers || 0}</p>
          <p className="text-sm text-gray-600 mt-2">Активны за последние 30 дней</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Доля активных</h3>
            <TrendingUp className="text-purple-500" size={24} />
          </div>
          <p className="text-4xl font-bold text-gray-900">
            {analytics?.totalUsers && analytics?.activeUsers
              ? Math.round((analytics.activeUsers / analytics.totalUsers) * 100)
              : 0}
            %
          </p>
          <p className="text-sm text-gray-600 mt-2">Вовлеченность пользователей</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Рост пользователей по дням</h2>
          <div className="space-y-3">
            {analytics?.userGrowth?.slice(-14).map((item) => (
              <div key={item.date} className="flex items-center gap-4">
                <span className="text-sm text-gray-600 w-32">
                  {new Date(item.date).toLocaleDateString()}
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-blue-500 h-4 rounded-full"
                    style={{
                      width: `${Math.min(
                        (item.count / (analytics?.totalUsers || 1)) * 100,
                        100
                      )}%`,
                    }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-900 w-16 text-right">
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Популярные карьерные роли</h2>
          <div className="space-y-3">
            {analytics?.popularRoles?.slice(0, 10).map((item, index) => (
              <div key={item.role} className="flex items-center gap-4">
                <span className="text-sm font-semibold text-gray-500 w-8">#{index + 1}</span>
                <span className="flex-1 text-sm text-gray-700">{item.role}</span>
                <span className="text-sm font-semibold text-gray-900">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Статистика контента</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-3 border-b">
              <span className="text-gray-700">Материалы базы знаний</span>
              <span className="text-2xl font-bold text-gray-900">
                {analytics?.totalKnowledgeBase || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b">
              <span className="text-gray-700">Активные возможности</span>
              <span className="text-2xl font-bold text-gray-900">
                {analytics?.totalOpportunities || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Карьерные роли</span>
              <span className="text-2xl font-bold text-gray-900">
                {analytics?.popularRoles?.length || 0}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Состояние системы</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-700">Вовлеченность пользователей</span>
                <span className="text-sm font-semibold text-green-600">Стабильно</span>
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '85%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-700">Актуальность контента</span>
                <span className="text-sm font-semibold text-blue-600">Хорошо</span>
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '72%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-700">Активность платформы</span>
                <span className="text-sm font-semibold text-purple-600">Активна</span>
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '91%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
