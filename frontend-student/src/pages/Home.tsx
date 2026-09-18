import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, MapPin, Building2, Calendar, Bookmark, TrendingUp, Loader2, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';

// Types
interface CareerGPSData {
  currentScore: number;
  maxScore: number;
  recommendations: string[];
  nextSteps: string[];
}

interface Opportunity {
  id: string;
  title: string;
  company: string;
  location: string;
  type: 'internship' | 'job' | 'project';
  deadline: string;
  match: number;
  saved: boolean;
}

interface Subscription {
  id: string;
  name: string;
  type: string;
  lastUpdate: string;
  newItems: number;
}

const opportunityTypeLabels: Record<Opportunity['type'], string> = {
  internship: 'Стажировка',
  job: 'Вакансия',
  project: 'Проект',
};

// API functions
const fetchCareerGPS = async (): Promise<CareerGPSData> => {
  const response = await apiClient.get('/student/career-gps');
  return response.data;
};

const fetchOpportunities = async (search: string = ''): Promise<Opportunity[]> => {
  const params = new URLSearchParams(search ? { search } : {});
  const response = await apiClient.get(`/student/opportunities?${params}`);
  return response.data;
};

const fetchSubscriptions = async (): Promise<Subscription[]> => {
  const response = await apiClient.get('/student/subscriptions');
  return response.data;
};

const toggleSaveOpportunity = async (opportunityId: string): Promise<void> => {
  await apiClient.post(`/student/opportunities/${opportunityId}/save`);
};

// Custom hook for debounced search
const useDebounce = <T,>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Components
const CareerGPSCard = ({ data }: { data: CareerGPSData }) => {
  const percentage = Math.round((data.currentScore / data.maxScore) * 100);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Карьерный навигатор</h2>
        <TrendingUp className="w-6 h-6 text-blue-600" />
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Готовность к цели</span>
          <span className="text-2xl font-bold text-blue-600">{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        <p className="text-sm text-gray-500 mt-1">
          {data.currentScore} из {data.maxScore} баллов
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Рекомендации</h3>
          <ul className="space-y-1">
            {data.recommendations.slice(0, 3).map((rec, index) => (
              <li key={index} className="text-sm text-gray-700 flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-2">Следующие шаги</h3>
          <ul className="space-y-1">
            {data.nextSteps.slice(0, 2).map((step, index) => (
              <li key={index} className="text-sm text-gray-700 flex items-start">
                <span className="text-green-600 mr-2">→</span>
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <button className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
        Открыть полный отчет
      </button>
    </div>
  );
};

const OpportunityCard = ({
  opportunity,
  onToggleSave
}: {
  opportunity: Opportunity;
  onToggleSave: (id: string) => void;
}) => {
  const typeColors = {
    internship: 'bg-blue-100 text-blue-800',
    job: 'bg-green-100 text-green-800',
    project: 'bg-purple-100 text-purple-800',
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-5 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{opportunity.title}</h3>
          <div className="flex items-center text-sm text-gray-600 space-x-3">
            <span className="flex items-center">
              <Building2 className="w-4 h-4 mr-1" />
              {opportunity.company}
            </span>
            <span className="flex items-center">
              <MapPin className="w-4 h-4 mr-1" />
              {opportunity.location}
            </span>
          </div>
        </div>
        <button
          onClick={() => onToggleSave(opportunity.id)}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label={opportunity.saved ? 'Убрать из сохраненного' : 'Сохранить возможность'}
        >
          <Bookmark
            className={`w-5 h-5 ${
              opportunity.saved ? 'fill-blue-600 text-blue-600' : 'text-gray-400'
            }`}
          />
        </button>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${typeColors[opportunity.type]}`}>
            {opportunityTypeLabels[opportunity.type] || opportunity.type}
          </span>
          <span className="flex items-center text-sm text-gray-500">
            <Calendar className="w-4 h-4 mr-1" />
            {new Date(opportunity.deadline).toLocaleDateString()}
          </span>
        </div>
        <div className="flex items-center">
          <span className="text-sm font-medium text-gray-700 mr-1">{opportunity.match}% совпадение</span>
          <div className="w-16 bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full"
              style={{ width: `${opportunity.match}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const SubscriptionCard = ({ subscription }: { subscription: Subscription }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 mb-1">{subscription.name}</h4>
          <p className="text-sm text-gray-600">{subscription.type}</p>
          <p className="text-xs text-gray-500 mt-1">
            Обновлено {new Date(subscription.lastUpdate).toLocaleDateString('ru-RU')}
          </p>
        </div>
        {subscription.newItems > 0 && (
          <span className="bg-blue-600 text-white text-xs font-bold rounded-full px-2.5 py-1">
            {subscription.newItems}
          </span>
        )}
      </div>
    </div>
  );
};

const LoadingState = () => (
  <div className="flex items-center justify-center py-12">
    <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
    <span className="ml-3 text-gray-600">Загрузка...</span>
  </div>
);

const ErrorState = ({ message, onRetry }: { message: string; onRetry: () => void }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
    <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-3" />
    <h3 className="text-lg font-semibold text-red-900 mb-2">Не удалось загрузить данные</h3>
    <p className="text-red-700 mb-4">{message}</p>
    <button
      onClick={onRetry}
      className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
    >
      Повторить
    </button>
  </div>
);

const EmptyState = ({ message }: { message: string }) => (
  <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
    <p className="text-gray-600">{message}</p>
  </div>
);

// Main Component
export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebounce(searchQuery, 500);

  // React Query hooks
  const {
    data: careerGPSData,
    isLoading: isLoadingCareerGPS,
    error: careerGPSError,
    refetch: refetchCareerGPS,
  } = useQuery({
    queryKey: ['careerGPS'],
    queryFn: fetchCareerGPS,
  });

  const {
    data: opportunities = [],
    isLoading: isLoadingOpportunities,
    error: opportunitiesError,
    refetch: refetchOpportunities,
  } = useQuery({
    queryKey: ['opportunities', debouncedSearch],
    queryFn: () => fetchOpportunities(debouncedSearch),
  });

  const {
    data: subscriptions = [],
    isLoading: isLoadingSubscriptions,
    error: subscriptionsError,
    refetch: refetchSubscriptions,
  } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: fetchSubscriptions,
  });

  const handleToggleSave = async (opportunityId: string) => {
    try {
      await toggleSaveOpportunity(opportunityId);
      refetchOpportunities();
    } catch (error) {
      console.error('Не удалось изменить сохранение:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Панель</h1>
          <p className="text-gray-600">Следите за карьерным прогрессом и находите подходящие возможности</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Career GPS */}
          <div className="lg:col-span-1">
            {isLoadingCareerGPS ? (
              <LoadingState />
            ) : careerGPSError ? (
              <ErrorState
                message="Не удалось загрузить Карьерный навигатор."
                onRetry={() => refetchCareerGPS()}
              />
            ) : careerGPSData ? (
              <CareerGPSCard data={careerGPSData} />
            ) : null}

            {/* Subscriptions Section */}
            <div className="mt-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Ваши подписки</h2>
              {isLoadingSubscriptions ? (
                <LoadingState />
              ) : subscriptionsError ? (
                <ErrorState
                  message="Не удалось загрузить подписки."
                  onRetry={() => refetchSubscriptions()}
                />
              ) : subscriptions.length === 0 ? (
                <EmptyState message="Активных подписок пока нет" />
              ) : (
                <div className="space-y-3">
                  {subscriptions.map((sub) => (
                    <SubscriptionCard key={sub.id} subscription={sub} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Opportunities */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Возможности</h2>

              {/* Search Bar */}
              <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Искать возможности..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  aria-label="Искать возможности"
                />
              </div>

              {/* Opportunities List */}
              {isLoadingOpportunities ? (
                <LoadingState />
              ) : opportunitiesError ? (
                <ErrorState
                  message="Не удалось загрузить возможности."
                  onRetry={() => refetchOpportunities()}
                />
              ) : opportunities.length === 0 ? (
                <EmptyState
                  message={
                    searchQuery
                      ? 'По вашему запросу возможности не найдены'
                      : 'Сейчас нет доступных возможностей'
                  }
                />
              ) : (
                <div className="space-y-4">
                  {opportunities.map((opportunity) => (
                    <OpportunityCard
                      key={opportunity.id}
                      opportunity={opportunity}
                      onToggleSave={handleToggleSave}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
