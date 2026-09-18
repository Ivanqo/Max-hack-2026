import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, BookOpen, Loader2, Plus, Trash2 } from 'lucide-react'
import { apiClient } from '@/lib/api'

interface StudentSkill {
  id: string
  name: string
  level: number
  levelLabel: string
  verified: boolean
}

interface StudentProfileResponse {
  user: {
    email: string
    name: string
    role: string
    maxUserId?: string
  }
  profile: {
    university: string
    institute: string
    program: string
    studyYear: number | null
    interests: string[]
    careerGoal: string
    onboardingCompleted: boolean
  }
  skills: StudentSkill[]
  subscriptions: Array<{ id: string; topic: string; active: boolean; newItems: number }>
}

const fetchProfile = async (): Promise<StudentProfileResponse> => {
  const response = await apiClient.get('/student/profile')
  return response.data
}

const saveSkills = async (skills: Array<{ name: string; level: number }>) => {
  const response = await apiClient.patch('/student/profile', { skills })
  return response.data
}

const levelLabels: Record<string, string> = {
  beginner: 'начальный',
  intermediate: 'средний',
  advanced: 'продвинутый',
  expert: 'экспертный',
}

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const [newSkillName, setNewSkillName] = useState('')
  const [newSkillLevel, setNewSkillLevel] = useState(3)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['student-profile'],
    queryFn: fetchProfile,
  })

  const mutation = useMutation({
    mutationFn: saveSkills,
    onSuccess: () => {
      setNewSkillName('')
      setNewSkillLevel(3)
      queryClient.invalidateQueries({ queryKey: ['student-profile'] })
      queryClient.invalidateQueries({ queryKey: ['career-analysis'] })
      queryClient.invalidateQueries({ queryKey: ['opportunities'] })
    },
  })

  const updateSkills = (skills: Array<{ name: string; level: number }>) => {
    mutation.mutate(skills)
  }

  const handleAddSkill = () => {
    if (!data || !newSkillName.trim()) return
    const existing = data.skills.filter(
      (skill) => skill.name.toLowerCase() !== newSkillName.trim().toLowerCase(),
    )
    updateSkills([...existing, { name: newSkillName.trim(), level: newSkillLevel }])
  }

  const handleDeleteSkill = (name: string) => {
    if (!data) return
    updateSkills(data.skills.filter((skill) => skill.name !== name))
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-10 w-10 animate-spin text-indigo-600" />
          <p className="text-gray-600">Загружаем профиль...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <div className="w-full max-w-md rounded-lg bg-white p-8 text-center shadow">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-500" />
          <h1 className="mb-2 text-xl font-bold text-gray-900">Профиль недоступен</h1>
          <p className="mb-6 text-gray-600">
            Сначала заполните анкету или попробуйте обновить страницу.
          </p>
          <button
            onClick={() => refetch()}
            className="rounded-lg bg-indigo-600 px-5 py-2 font-medium text-white hover:bg-indigo-700"
          >
            Повторить
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Профиль</h1>
          <p className="mt-2 text-gray-600">
            {data.user.name || data.user.email} · {data.profile.university || 'Университет не выбран'}
          </p>
        </div>

        <section className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-xl font-semibold text-gray-900">Карьерный контекст</h2>
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Программа</dt>
              <dd className="mt-1 text-gray-900">{data.profile.program || 'Не указано'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Курс</dt>
              <dd className="mt-1 text-gray-900">{data.profile.studyYear || 'Не указано'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Карьерная цель</dt>
              <dd className="mt-1 text-gray-900">{data.profile.careerGoal || 'Не указано'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">MAX-профиль</dt>
              <dd className="mt-1 text-gray-900">{data.user.maxUserId ? 'Связан' : 'Не связан'}</dd>
            </div>
          </dl>
        </section>

        <section className="rounded-lg bg-white p-6 shadow">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
              <BookOpen className="h-5 w-5" />
              Навыки
            </h2>
            {mutation.isPending && <span className="text-sm text-gray-500">Сохраняем...</span>}
          </div>

          <div className="mb-5 grid gap-3 sm:grid-cols-[1fr_180px_auto]">
            <input
              value={newSkillName}
              onChange={(event) => setNewSkillName(event.target.value)}
              placeholder="Название навыка"
              className="rounded-lg border border-gray-300 px-4 py-2"
            />
            <select
              value={newSkillLevel}
              onChange={(event) => setNewSkillLevel(Number(event.target.value))}
              className="rounded-lg border border-gray-300 px-4 py-2"
            >
              <option value={2}>Начальный</option>
              <option value={3}>Средний</option>
              <option value={4}>Продвинутый</option>
              <option value={5}>Экспертный</option>
            </select>
            <button
              onClick={handleAddSkill}
              disabled={mutation.isPending || !newSkillName.trim()}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              Добавить
            </button>
          </div>

          <div className="space-y-3">
            {data.skills.map((skill) => (
              <div
                key={skill.id}
                className="flex items-center justify-between rounded-lg border border-gray-200 p-4"
              >
                <div>
                  <p className="font-medium text-gray-900">{skill.name}</p>
                  <p className="text-sm text-gray-500">
                    {levelLabels[skill.levelLabel] || skill.levelLabel} · уровень {skill.level}/5
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteSkill(skill.name)}
                  disabled={mutation.isPending}
                  className="rounded-lg p-2 text-red-600 hover:bg-red-50 disabled:opacity-50"
                  aria-label={`Удалить ${skill.name}`}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
            {data.skills.length === 0 && (
              <p className="rounded-lg bg-gray-50 p-6 text-center text-gray-600">
                Добавьте навыки, чтобы улучшить Карьерный навигатор и подбор возможностей.
              </p>
            )}
          </div>
        </section>

        <section className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-xl font-semibold text-gray-900">Подписки</h2>
          <div className="space-y-3">
            {data.subscriptions.map((subscription) => (
              <div key={subscription.id} className="rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">{subscription.topic}</span>
                  <span className="text-sm text-gray-500">
                    {subscription.active ? 'активна' : 'приостановлена'} · подходящих материалов: {subscription.newItems}
                  </span>
                </div>
              </div>
            ))}
            {data.subscriptions.length === 0 && (
              <p className="text-gray-600">Подписок пока нет.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
