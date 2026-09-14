import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

interface CareerGoal {
  id: number
  title: string
  description: string
  category: string
}

interface SkillGap {
  skill: string
  currentLevel: number
  requiredLevel: number
  priority: 'high' | 'medium' | 'low'
}

interface NextAction {
  id: number
  title: string
  type: 'course' | 'quiz' | 'resource'
  estimatedTime: string
  priority: number
}

interface CareerAnalysis {
  goal: CareerGoal
  readinessScore: number
  strengths: string[]
  gaps: SkillGap[]
  nextActions: NextAction[]
  lastUpdated: string
}

export default function CareerGPS() {
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null)

  const {
    data: goals,
    isLoading: goalsLoading,
    error: goalsError,
  } = useQuery<CareerGoal[]>({
    queryKey: ['career-goals'],
    queryFn: async () => {
      const response = await apiClient.get('/career/goals')
      return response.data
    },
  })

  const {
    data: analysis,
    isLoading: analysisLoading,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useQuery<CareerAnalysis>({
    queryKey: ['career-analysis', selectedGoalId],
    queryFn: async () => {
      const response = await apiClient.get(`/career/analysis/${selectedGoalId}`)
      return response.data
    },
    enabled: selectedGoalId !== null,
  })

  useEffect(() => {
    if (goals && goals.length > 0 && !selectedGoalId) {
      setSelectedGoalId(goals[0].id)
    }
  }, [goals, selectedGoalId])

  const getReadinessColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getReadinessBackground = (score: number) => {
    if (score >= 80) return 'bg-green-100'
    if (score >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  const getPriorityBadge = (priority: string) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-gray-100 text-gray-800',
    }
    return colors[priority as keyof typeof colors] || colors.low
  }

  if (goalsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading career goals...</p>
        </div>
      </div>
    )
  }

  if (goalsError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <div className="flex">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading career goals</h3>
              <p className="mt-2 text-sm text-red-700">
                {goalsError instanceof Error ? goalsError.message : 'An unexpected error occurred'}
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!goals || goals.length === 0) {
    return (
      <div className="px-4 py-6 max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Career GPS</h1>
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No career goals set</h3>
          <p className="mt-2 text-sm text-gray-500">
            Set your career goals to get personalized recommendations and track your progress.
          </p>
          <button
            onClick={() => refetchAnalysis()}
            className="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Set Career Goal
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Career GPS</h1>
        <p className="mt-2 text-sm text-gray-600">
          Track your progress towards your career goals and get personalized recommendations
        </p>
      </div>

      <div className="mb-6">
        <label htmlFor="goal-select" className="block text-sm font-medium text-gray-700 mb-2">
          Select Career Goal
        </label>
        <select
          id="goal-select"
          value={selectedGoalId || ''}
          onChange={(e) => setSelectedGoalId(Number(e.target.value))}
          className="block w-full max-w-md px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          aria-label="Select career goal"
        >
          {goals.map((goal) => (
            <option key={goal.id} value={goal.id}>
              {goal.title}
            </option>
          ))}
        </select>
      </div>

      {analysisLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mx-auto mb-3"></div>
            <p className="text-gray-600 text-sm">Analyzing your career readiness...</p>
          </div>
        </div>
      )}

      {analysisError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {analysisError instanceof Error ? analysisError.message : 'Failed to load career analysis'}
              </p>
            </div>
          </div>
        </div>
      )}

      {analysis && (
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-gray-900">{analysis.goal.title}</h2>
                  <p className="mt-1 text-sm text-gray-500">{analysis.goal.description}</p>
                  <span className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                    {analysis.goal.category}
                  </span>
                </div>
                <div className={`ml-6 flex-shrink-0 text-center ${getReadinessBackground(analysis.readinessScore)} rounded-lg p-4`}>
                  <div className={`text-3xl font-bold ${getReadinessColor(analysis.readinessScore)}`}>
                    {analysis.readinessScore}%
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Readiness</div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 bg-gray-50">
              <div className="flex items-center text-xs text-gray-500">
                <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Last updated: {new Date(analysis.lastUpdated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="h-5 w-5 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Your Strengths
              </h3>
              {analysis.strengths.length > 0 ? (
                <ul className="space-y-2">
                  {analysis.strengths.map((strength, index) => (
                    <li key={index} className="flex items-start">
                      <span className="flex-shrink-0 h-5 w-5 text-green-500 mr-2">✓</span>
                      <span className="text-sm text-gray-700">{strength}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500 italic">No strengths identified yet. Complete courses to build your profile.</p>
              )}
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="h-5 w-5 text-orange-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                Skill Gaps
              </h3>
              {analysis.gaps.length > 0 ? (
                <div className="space-y-4">
                  {analysis.gaps.map((gap, index) => (
                    <div key={index} className="border-l-4 border-orange-400 pl-4">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="text-sm font-medium text-gray-900">{gap.skill}</h4>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadge(gap.priority)}`}>
                          {gap.priority}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span>Current: {gap.currentLevel}/10</span>
                        <span>→</span>
                        <span>Required: {gap.requiredLevel}/10</span>
                      </div>
                      <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${(gap.currentLevel / gap.requiredLevel) * 100}%` }}
                          role="progressbar"
                          aria-valuenow={gap.currentLevel}
                          aria-valuemin={0}
                          aria-valuemax={gap.requiredLevel}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">No skill gaps identified. You are on track!</p>
              )}
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <svg className="h-5 w-5 text-indigo-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Next Actions
            </h3>
            {analysis.nextActions.length > 0 ? (
              <div className="space-y-3">
                {analysis.nextActions.map((action) => (
                  <div
                    key={action.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-indigo-400 hover:shadow-sm transition-all cursor-pointer"
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        // Handle action click
                      }
                    }}
                  >
                    <div className="flex items-start flex-1">
                      <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                        action.priority === 1 ? 'bg-indigo-100' : 'bg-gray-100'
                      }`}>
                        <span className="text-sm font-semibold text-gray-700">{action.priority}</span>
                      </div>
                      <div className="ml-4 flex-1">
                        <h4 className="text-sm font-medium text-gray-900">{action.title}</h4>
                        <div className="mt-1 flex items-center space-x-3 text-xs text-gray-500">
                          <span className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-800">
                            {action.type}
                          </span>
                          <span className="flex items-center">
                            <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {action.estimatedTime}
                          </span>
                        </div>
                      </div>
                    </div>
                    <svg className="h-5 w-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-2 text-sm text-gray-500">All caught up! No immediate actions required.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
