import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bookmark, BookmarkCheck, TrendingUp, AlertCircle, Loader2, BellPlus } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { apiClient } from '@/lib/api';

interface Opportunity {
  id: string;
  title: string;
  company: string;
  location: string;
  type: string;
  description: string;
  requirements: string[];
  matchPercentage: number;
  matchReasons: string[];
  gaps: string[];
  isSaved: boolean;
  postedDate: string;
}

interface OpportunitiesResponse {
  opportunities: Opportunity[];
  total: number;
}

// API functions
const fetchOpportunities = async (filters?: { type?: string; minMatch?: number }): Promise<OpportunitiesResponse> => {
  const params = new URLSearchParams();
  if (filters?.type) params.append('type', filters.type);
  if (filters?.minMatch) params.append('minMatch', filters.minMatch.toString());

  const response = await apiClient.get(`/student/opportunities?${params.toString()}`);
  const opportunities = response.data;
  return { opportunities, total: opportunities.length };
};

const saveOpportunity = async (opportunityId: string): Promise<void> => {
  await apiClient.post(`/student/opportunities/${opportunityId}/save`);
};

const unsaveOpportunity = async (opportunityId: string): Promise<void> => {
  await apiClient.delete(`/student/opportunities/${opportunityId}/save`);
};

const createSubscription = async (topic: string): Promise<void> => {
  await apiClient.post('/student/subscriptions', { topic, filters: { topic }, active: true });
};

export default function Opportunities() {
  const [filters, setFilters] = useState<{ type?: string; minMatch?: number }>({});
  const [subscriptionTopic, setSubscriptionTopic] = useState('Backend');
  const [searchParams] = useSearchParams();
  const highlightedOpportunityId = searchParams.get('opportunity');
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['opportunities', filters],
    queryFn: () => fetchOpportunities(filters),
  });

  const saveMutation = useMutation({
    mutationFn: saveOpportunity,
    onSuccess: (_, opportunityId) => {
      queryClient.setQueryData<OpportunitiesResponse>(
        ['opportunities', filters],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            opportunities: old.opportunities.map((opp) =>
              opp.id === opportunityId ? { ...opp, isSaved: true } : opp
            ),
          };
        }
      );
    },
  });

  const unsaveMutation = useMutation({
    mutationFn: unsaveOpportunity,
    onSuccess: (_, opportunityId) => {
      queryClient.setQueryData<OpportunitiesResponse>(
        ['opportunities', filters],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            opportunities: old.opportunities.map((opp) =>
              opp.id === opportunityId ? { ...opp, isSaved: false } : opp
            ),
          };
        }
      );
    },
  });

  const subscriptionMutation = useMutation({
    mutationFn: createSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-profile'] });
    },
  });

  const handleToggleSave = (opportunity: Opportunity) => {
    if (opportunity.isSaved) {
      unsaveMutation.mutate(opportunity.id);
    } else {
      saveMutation.mutate(opportunity.id);
    }
  };

  const getMatchColor = (percentage: number): string => {
    if (percentage >= 80) return 'text-green-600 bg-green-50';
    if (percentage >= 60) return 'text-blue-600 bg-blue-50';
    if (percentage >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getMatchBorderColor = (percentage: number): string => {
    if (percentage >= 80) return 'border-green-200 hover:border-green-300';
    if (percentage >= 60) return 'border-blue-200 hover:border-blue-300';
    if (percentage >= 40) return 'border-yellow-200 hover:border-yellow-300';
    return 'border-red-200 hover:border-red-300';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 text-lg">Loading opportunities...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Opportunities</h2>
          <p className="text-gray-600 mb-6">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['opportunities'] })}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!data || data.opportunities.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full text-center">
          <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Opportunities Found</h2>
          <p className="text-gray-600 mb-6">
            {filters.type || filters.minMatch
              ? 'Try adjusting your filters to see more results.'
              : 'Check back later for new opportunities that match your profile.'}
          </p>
          {(filters.type || filters.minMatch) && (
            <button
              onClick={() => setFilters({})}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Opportunities for You</h1>
          <p className="text-gray-600">
            {data.total} {data.total === 1 ? 'opportunity' : 'opportunities'} matched to your profile
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label htmlFor="subscription-topic" className="block text-sm font-medium text-gray-700 mb-1">
                MAX subscription topic
              </label>
              <input
                id="subscription-topic"
                value={subscriptionTopic}
                onChange={(event) => setSubscriptionTopic(event.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={() => subscriptionMutation.mutate(subscriptionTopic)}
              disabled={subscriptionMutation.isPending || !subscriptionTopic.trim()}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              <BellPlus className="h-4 w-4" />
              {subscriptionMutation.isPending ? 'Creating...' : 'Create subscription'}
            </button>
          </div>
          {subscriptionMutation.isSuccess && (
            <p className="mt-3 text-sm text-green-700">Subscription saved. New matching publications will trigger MAX notification.</p>
          )}
          {subscriptionMutation.error && (
            <p className="mt-3 text-sm text-red-700">
              {subscriptionMutation.error instanceof Error ? subscriptionMutation.error.message : 'Failed to create subscription'}
            </p>
          )}
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6 flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 mb-1">
              Type
            </label>
            <select
              id="type-filter"
              value={filters.type || ''}
              onChange={(e) => setFilters({ ...filters, type: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Types</option>
              <option value="internship">Internship</option>
              <option value="full-time">Full-time</option>
              <option value="part-time">Part-time</option>
              <option value="contract">Contract</option>
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label htmlFor="match-filter" className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Match
            </label>
            <select
              id="match-filter"
              value={filters.minMatch || ''}
              onChange={(e) =>
                setFilters({ ...filters, minMatch: e.target.value ? Number(e.target.value) : undefined })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Any Match</option>
              <option value="40">40% or higher</option>
              <option value="60">60% or higher</option>
              <option value="80">80% or higher</option>
            </select>
          </div>

          {(filters.type || filters.minMatch) && (
            <div className="flex items-end">
              <button
                onClick={() => setFilters({})}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 underline"
              >
                Clear Filters
              </button>
            </div>
          )}
        </div>

        {/* Opportunities List */}
        <div className="space-y-4">
          {data.opportunities.map((opportunity) => (
            <article
              key={opportunity.id}
              className={`bg-white rounded-lg shadow-sm border-2 transition-all ${
                highlightedOpportunityId === opportunity.id ? 'ring-4 ring-indigo-200' : ''
              } ${getMatchBorderColor(
                opportunity.matchPercentage
              )}`}
            >
              <div className="p-6">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <h2 className="text-xl font-bold text-gray-900 mb-1">{opportunity.title}</h2>
                    <p className="text-gray-600 mb-2">
                      {opportunity.company} • {opportunity.location} • {opportunity.type}
                    </p>
                    <p className="text-sm text-gray-500">
                      Posted {new Date(opportunity.postedDate).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div
                      className={`text-center px-4 py-2 rounded-lg ${getMatchColor(opportunity.matchPercentage)}`}
                    >
                      <div className="text-2xl font-bold">{opportunity.matchPercentage}%</div>
                      <div className="text-xs font-medium">Match</div>
                    </div>

                    <button
                      onClick={() => handleToggleSave(opportunity)}
                      disabled={saveMutation.isPending || unsaveMutation.isPending}
                      className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
                      aria-label={opportunity.isSaved ? 'Unsave opportunity' : 'Save opportunity'}
                    >
                      {opportunity.isSaved ? (
                        <BookmarkCheck className="w-6 h-6 text-blue-600" />
                      ) : (
                        <Bookmark className="w-6 h-6 text-gray-400" />
                      )}
                    </button>
                  </div>
                </div>

                <p className="text-gray-700 mb-4">{opportunity.description}</p>

                {/* Match Reasons */}
                {opportunity.matchReasons.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Why you match:</h3>
                    <ul className="space-y-1">
                      {opportunity.matchReasons.map((reason, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-green-500 mt-0.5">✓</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Gaps */}
                {opportunity.gaps.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">Areas to improve:</h3>
                    <ul className="space-y-1">
                      {opportunity.gaps.map((gap, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-yellow-500 mt-0.5">⚠</span>
                          <span>{gap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Requirements */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">Requirements:</h3>
                  <div className="flex flex-wrap gap-2">
                    {opportunity.requirements.map((req, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
                      >
                        {req}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                  <button className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                    Apply Now
                  </button>
                  <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium">
                    Learn More
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
