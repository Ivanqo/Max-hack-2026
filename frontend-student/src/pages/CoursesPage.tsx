import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api'

export default function CoursesPage() {
  const queryClient = useQueryClient()

  const { data: courses, isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: async () => {
      const response = await apiClient.get('/courses')
      return response.data
    },
  })

  const enrollMutation = useMutation({
    mutationFn: async (courseId: number) => {
      await apiClient.post(`/courses/${courseId}/enroll`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] })
      queryClient.invalidateQueries({ queryKey: ['enrollments'] })
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Загрузка...</div>
  }

  return (
    <div className="px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Доступные курсы</h1>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {courses?.map((course: any) => (
          <div key={course.id} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900">{course.title}</h3>
              <p className="mt-2 text-sm text-gray-500 line-clamp-3">{course.description}</p>

              <div className="mt-4 flex items-center justify-between">
                <span className="text-sm text-gray-500">
                  Записано студентов: {course.enrollments?.length || 0}
                </span>
              </div>

              <div className="mt-4 flex space-x-2">
                <Link
                  to={`/courses/${course.id}`}
                  className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Подробнее
                </Link>
                {!course.isEnrolled && (
                  <button
                    onClick={() => enrollMutation.mutate(course.id)}
                    disabled={enrollMutation.isPending}
                    className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {enrollMutation.isPending ? 'Записываем...' : 'Записаться'}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
