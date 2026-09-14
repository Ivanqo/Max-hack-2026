import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, CheckCircle, AlertCircle, Loader2, ExternalLink } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface KnowledgeSource {
  id: string;
  name: string;
  url?: string;
  type: 'document' | 'web' | 'database';
}

interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  summary: string;
  source: KnowledgeSource;
  verified: boolean;
  relevanceScore: number;
  createdAt: string;
  updatedAt: string;
}

interface SearchResponse {
  results: KnowledgeItem[];
  total: number;
  query: string;
  found?: boolean;
  message?: string;
  escalation?: {
    unit: string;
    contact: string;
  };
}

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

const searchKnowledge = async (query: string): Promise<SearchResponse> => {
  if (!query.trim()) {
    return { results: [], total: 0, query: '' };
  }

  const response = await apiClient.get(`/knowledge/search?q=${encodeURIComponent(query)}`);
  return response.data;
};

export default function Knowledge() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null);
  const debouncedQuery = useDebounce(searchQuery, 500);

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['knowledge', debouncedQuery],
    queryFn: () => searchKnowledge(debouncedQuery),
    enabled: debouncedQuery.trim().length > 0,
    staleTime: 5 * 60 * 1000,
  });

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  }, []);

  const handleItemClick = useCallback((item: KnowledgeItem) => {
    setSelectedItem(item);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedItem(null);
  }, []);

  const getSourceIcon = (type: KnowledgeSource['type']) => {
    switch (type) {
      case 'web':
        return <ExternalLink className="w-4 h-4" />;
      case 'document':
        return <span className="text-sm">📄</span>;
      case 'database':
        return <span className="text-sm">🗄️</span>;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Knowledge Base
          </h1>
          <p className="text-gray-600">
            Search through verified educational resources and materials
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
            </div>
            <input
              type="search"
              value={searchQuery}
              onChange={handleSearchChange}
              className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
              placeholder="Search for topics, concepts, or questions..."
              aria-label="Search knowledge base"
            />
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" aria-label="Loading" />
            <span className="ml-3 text-gray-600">Searching knowledge base...</span>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start">
            <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Search Error</h3>
              <p className="mt-1 text-sm text-red-700">
                {error instanceof Error ? error.message : 'Failed to search knowledge base. Please try again.'}
              </p>
            </div>
          </div>
        )}

        {/* Empty State - No Query */}
        {!searchQuery.trim() && !isLoading && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">Start Searching</h3>
            <p className="mt-2 text-gray-500">
              Enter a search term to find relevant information from our knowledge base
            </p>
          </div>
        )}

        {/* Empty State - No Results */}
        {debouncedQuery.trim() && !isLoading && !isError && data?.results.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No Results Found</h3>
            <p className="mt-2 text-gray-500">
              {data.message || `We could not find any results for "${debouncedQuery}". Try different keywords or broader terms.`}
            </p>
            {data.escalation && (
              <p className="mt-2 text-sm text-gray-500">
                {data.escalation.unit}: {data.escalation.contact}
              </p>
            )}
          </div>
        )}

        {/* Results */}
        {!isLoading && !isError && data && data.results.length > 0 && (
          <>
            <div className="mb-4 text-sm text-gray-600">
              Found {data.total} {data.total === 1 ? 'result' : 'results'} for &quot;{data.query}&quot;
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {data.results.map((item) => (
                <article
                  key={item.id}
                  onClick={() => handleItemClick(item)}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
                  tabIndex={0}
                  role="button"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleItemClick(item);
                    }
                  }}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900 flex-1 line-clamp-2">
                      {item.title}
                    </h3>
                    {item.verified && (
                      <CheckCircle
                        className="w-5 h-5 text-green-500 flex-shrink-0 ml-2"
                        aria-label="Verified"
                      />
                    )}
                  </div>

                  {/* Summary */}
                  <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                    {item.summary}
                  </p>

                  {/* Footer */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center space-x-1">
                      {getSourceIcon(item.source.type)}
                      <span className="truncate max-w-[150px]">{item.source.name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        {Math.round(item.relevanceScore * 100)}% match
                      </span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}

        {/* Detail Modal */}
        {selectedItem && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={handleCloseDetail}
            role="dialog"
            aria-modal="true"
            aria-labelledby="detail-title"
          >
            <div
              className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h2 id="detail-title" className="text-2xl font-bold text-gray-900 mb-2">
                      {selectedItem.title}
                    </h2>
                    <div className="flex items-center space-x-3 text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        {getSourceIcon(selectedItem.source.type)}
                        <span>{selectedItem.source.name}</span>
                      </div>
                      {selectedItem.verified && (
                        <div className="flex items-center space-x-1 text-green-600">
                          <CheckCircle className="w-4 h-4" />
                          <span>Verified</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={handleCloseDetail}
                    className="text-gray-400 hover:text-gray-600 transition-colors ml-4"
                    aria-label="Close detail view"
                  >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Content */}
                <div className="prose prose-sm max-w-none">
                  <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
                    <p className="text-sm text-blue-900">{selectedItem.summary}</p>
                  </div>
                  <div className="text-gray-700 whitespace-pre-wrap">
                    {selectedItem.content}
                  </div>
                </div>

                {/* Footer */}
                <div className="mt-6 pt-6 border-t border-gray-200 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Last updated: {new Date(selectedItem.updatedAt).toLocaleDateString()}
                  </div>
                  {selectedItem.source.url && (
                    <a
                      href={selectedItem.source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
                    >
                      <span>View Source</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
