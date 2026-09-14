import { useEffect, useState } from 'react';
import { Users, BookOpen, Briefcase, TrendingUp } from 'lucide-react';
import api from '@/api/client';
import { Analytics } from '@/types';

export const Dashboard = () => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await api.get('/admin/analytics');
        setAnalytics(response.data);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  const stats = [
    {
      label: 'Total Users',
      value: analytics?.totalUsers || 0,
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      label: 'Active Users',
      value: analytics?.activeUsers || 0,
      icon: TrendingUp,
      color: 'bg-green-500',
    },
    {
      label: 'Opportunities',
      value: analytics?.totalOpportunities || 0,
      icon: Briefcase,
      color: 'bg-purple-500',
    },
    {
      label: 'Knowledge Articles',
      value: analytics?.totalKnowledgeBase || 0,
      icon: BookOpen,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon size={24} className="text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">User Growth</h2>
          <div className="space-y-2">
            {analytics?.userGrowth?.slice(-7).map((item) => (
              <div key={item.date} className="flex justify-between items-center">
                <span className="text-gray-600">{new Date(item.date).toLocaleDateString()}</span>
                <span className="font-semibold text-gray-900">{item.count} users</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Popular Career Roles</h2>
          <div className="space-y-2">
            {analytics?.popularRoles?.slice(0, 5).map((item) => (
              <div key={item.role} className="flex justify-between items-center">
                <span className="text-gray-600">{item.role}</span>
                <span className="font-semibold text-gray-900">{item.count} interests</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
