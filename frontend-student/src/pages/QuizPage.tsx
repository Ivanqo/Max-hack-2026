import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api'

export default function QuizPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState<any>(null)

  const { data: quiz, isLoading } = useQuery({
    queryKey: ['quiz', id],
    queryFn: async () => {
      const response = await apiClient.get(`/quizzes/${id}`)
      return response.data
    },
  })

  const submitMutation = useMutation({
    mutationFn: async (answers: Record<number, number>) => {
      const response = await apiClient.post(`/quizzes/${id}/submit`, { answers })
      return response.data
    },
    onSuccess: (data) => {
      setResult(data)
      setSubmitted(true)
    },
  })

  const handleAnswerChange = (questionId: number, optionId: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }))
  }

  const handleSubmit = () => {
    submitMutation.mutate(answers)
  }

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>
  }

  if (submitted && result) {
    return (
      <div className="px-4 py-6 max-w-3xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Quiz Results</h1>
          <div className="mb-6">
            <div className="text-center py-8">
              <div className="text-6xl font-bold text-indigo-600 mb-2">
                {result.score}%
              </div>
              <p className="text-xl text-gray-600">
                {result.correctAnswers} out of {result.totalQuestions} correct
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate(`/courses/${quiz.courseId}`)}
            className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Back to Course
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 max-w-3xl mx-auto">
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{quiz?.title}</h1>
        <p className="text-gray-600 mb-8">{quiz?.questions?.length} questions</p>

        <div className="space-y-8">
          {quiz?.questions?.map((question: any, index: number) => (
            <div key={question.id} className="border-b border-gray-200 pb-6 last:border-b-0">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {index + 1}. {question.text}
              </h3>
              <div className="space-y-2">
                {question.options?.map((option: any) => (
                  <label
                    key={option.id}
                    className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      value={option.id}
                      checked={answers[question.id] === option.id}
                      onChange={() => handleAnswerChange(question.id, option.id)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                    />
                    <span className="ml-3 text-gray-700">{option.text}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8">
          <button
            onClick={handleSubmit}
            disabled={submitMutation.isPending || Object.keys(answers).length !== quiz?.questions?.length}
            className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitMutation.isPending ? 'Submitting...' : 'Submit Quiz'}
          </button>
        </div>
      </div>
    </div>
  )
}
