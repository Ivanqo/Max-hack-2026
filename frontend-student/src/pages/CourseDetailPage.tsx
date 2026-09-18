import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { apiClient } from '@/lib/api'

export default function CourseDetailPage() {
  const { id } = useParams()

  const { data: course, isLoading } = useQuery({
    queryKey: ['course', id],
    queryFn: async () => {
      const response = await apiClient.get(`/courses/${id}`)
      return response.data
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Загрузка...</div>
  }

  return (
    <div className="px-4 py-6">
      <div className="mb-6">
        <Link to="/courses" className="text-indigo-600 hover:text-indigo-500">
          ← Назад к курсам
        </Link>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{course?.title}</h1>
          <p className="text-gray-600 mb-8">{course?.description}</p>

          <div className="border-t border-gray-200 pt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Материалы курса</h2>
            {course?.materials?.length > 0 ? (
              <div className="space-y-4">
                {course.materials.map((material: any) => (
                  <div key={material.id} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900">{material.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{material.type}</p>
                    {material.content && (
                      <p className="text-sm text-gray-600 mt-2">{material.content}</p>
                    )}
                    {material.url && (
                      <a
                        href={material.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-600 hover:text-indigo-500 mt-2 inline-block"
                      >
                        Открыть материал →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">Материалы пока не добавлены.</p>
            )}
          </div>

          <div className="border-t border-gray-200 pt-6 mt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Тесты</h2>
            {course?.quizzes?.length > 0 ? (
              <div className="space-y-4">
                {course.quizzes.map((quiz: any) => (
                  <div key={quiz.id} className="border border-gray-200 rounded-lg p-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{quiz.title}</h3>
                      <p className="text-sm text-gray-500 mt-1">Вопросов: {quiz.questions?.length || 0}</p>
                    </div>
                    <Link
                      to={`/quiz/${quiz.id}`}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      Пройти тест
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">Тесты пока не добавлены.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
