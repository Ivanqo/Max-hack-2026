import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, GraduationCap, Pencil, Plus, Sparkles, Target, Trash2 } from 'lucide-react'
import { fetchStudentProfile, updateStudentProfile } from '@/lib/endpoints'
import { skillLevelLabels } from '@/lib/labels'
import { Badge, Button, Card, ErrorState, Input, LoadingState, ProgressBar, Select, Sheet, Textarea, useToast } from '@/ui'
import type { SelectedSkill } from '@/types'

const STUDY_YEARS = [1, 2, 3, 4, 5, 6]

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const toast = useToast()

  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['student-profile'], queryFn: fetchStudentProfile })

  const [editOpen, setEditOpen] = useState(false)
  const [form, setForm] = useState({ university: '', institute: '', program: '', studyYear: '', careerGoal: '', interests: '' })
  const [newSkillName, setNewSkillName] = useState('')
  const [newSkillLevel, setNewSkillLevel] = useState(3)

  const mutation = useMutation({
    mutationFn: updateStudentProfile,
    onSuccess: () => {
      toast.success('Изменения сохранены')
      queryClient.invalidateQueries({ queryKey: ['student-profile'] })
      queryClient.invalidateQueries({ queryKey: ['career-analysis'] })
      queryClient.invalidateQueries({ queryKey: ['career-gps-summary'] })
      queryClient.invalidateQueries({ queryKey: ['opportunities'] })
    },
    onError: () => toast.error('Не удалось сохранить изменения', 'Попробуйте ещё раз.'),
  })

  const completeness = useMemo(() => {
    if (!data) return 0
    const checks = [
      Boolean(data.profile.university),
      Boolean(data.profile.institute),
      Boolean(data.profile.program),
      Boolean(data.profile.studyYear),
      Boolean(data.profile.careerGoal),
      data.profile.interests.length > 0,
      data.skills.length >= 2,
    ]
    return Math.round((checks.filter(Boolean).length / checks.length) * 100)
  }, [data])

  const openEdit = () => {
    if (!data) return
    setForm({
      university: data.profile.university,
      institute: data.profile.institute,
      program: data.profile.program,
      studyYear: data.profile.studyYear ? String(data.profile.studyYear) : '',
      careerGoal: data.profile.careerGoal,
      interests: data.profile.interests.join(', '),
    })
    setEditOpen(true)
  }

  const saveBasicInfo = () => {
    mutation.mutate(
      {
        university: form.university,
        institute: form.institute,
        program: form.program,
        studyYear: form.studyYear || undefined,
        careerGoal: form.careerGoal,
        interests: form.interests.split(',').map((s) => s.trim()).filter(Boolean),
      },
      { onSuccess: () => setEditOpen(false) },
    )
  }

  const currentSkills = (data?.skills || []).map<SelectedSkill>((s) => ({ name: s.name, level: s.level }))

  const saveSkills = (skills: SelectedSkill[]) => mutation.mutate({ skills })

  const handleAddSkill = () => {
    if (!newSkillName.trim()) return
    const existing = currentSkills.filter((s) => s.name.toLowerCase() !== newSkillName.trim().toLowerCase())
    saveSkills([...existing, { name: newSkillName.trim(), level: newSkillLevel }])
    setNewSkillName('')
    setNewSkillLevel(3)
  }

  const handleDeleteSkill = (name: string) => {
    saveSkills(currentSkills.filter((s) => s.name !== name))
  }

  if (isLoading) return <LoadingState label="Загружаем профиль…" />
  if (isError || !data) return <ErrorState title="Профиль недоступен" message="Сначала заполните анкету или попробуйте обновить страницу." onRetry={() => refetch()} />

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      {/* Header */}
      <div className="overflow-hidden rounded-3xl border border-ink-100 bg-white shadow-soft">
        <div className="bg-brand-gradient p-6 text-white sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">{data.user.name || data.user.email}</h1>
              <p className="mt-0.5 text-sm text-white/80">{data.profile.university || 'Университет не выбран'}</p>
            </div>
            <Button variant="secondary" size="sm" leftIcon={<Pencil className="h-4 w-4" />} onClick={openEdit} className="bg-white text-brand-700 hover:bg-white/90">
              Редактировать
            </Button>
          </div>
        </div>
        <div className="p-5">
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="font-medium text-ink-700">Заполненность профиля</span>
            <span className="font-semibold text-ink-900">{completeness}%</span>
          </div>
          <ProgressBar value={completeness} tone={completeness >= 80 ? 'success' : completeness >= 40 ? 'brand' : 'warning'} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-ink-900">
            <GraduationCap className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} /> Обучение
          </h2>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-ink-400">Институт</dt>
              <dd className="mt-0.5 font-medium text-ink-900">{data.profile.institute || '—'}</dd>
            </div>
            <div>
              <dt className="text-ink-400">Программа</dt>
              <dd className="mt-0.5 font-medium text-ink-900">{data.profile.program || '—'}</dd>
            </div>
            <div>
              <dt className="text-ink-400">Курс</dt>
              <dd className="mt-0.5 font-medium text-ink-900">{data.profile.studyYear ? `${data.profile.studyYear} курс` : '—'}</dd>
            </div>
            <div>
              <dt className="text-ink-400">MAX-профиль</dt>
              <dd className="mt-0.5 font-medium text-ink-900">{data.user.maxUserId ? 'Связан' : 'Не связан'}</dd>
            </div>
          </dl>
        </Card>

        <Card>
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-ink-900">
            <Target className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} /> Карьерная цель и интересы
          </h2>
          <p className="text-sm text-ink-700">{data.profile.careerGoal || 'Цель ещё не выбрана'}</p>
          {data.profile.interests.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {data.profile.interests.map((interest) => (
                <Badge key={interest} tone="brand">{interest}</Badge>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold text-ink-900">
            <BookOpen className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} /> Навыки
          </h2>
          {mutation.isPending && <span className="text-xs text-ink-400">Сохраняем…</span>}
        </div>

        <div className="mb-5 grid gap-2 sm:grid-cols-[1fr_160px_auto]">
          <Input value={newSkillName} onChange={(e) => setNewSkillName(e.target.value)} placeholder="Название навыка" />
          <Select value={newSkillLevel} onChange={(e) => setNewSkillLevel(Number(e.target.value))}>
            <option value={2}>Начальный</option>
            <option value={3}>Средний</option>
            <option value={4}>Продвинутый</option>
            <option value={5}>Экспертный</option>
          </Select>
          <Button onClick={handleAddSkill} disabled={mutation.isPending || !newSkillName.trim()} leftIcon={<Plus className="h-4 w-4" />}>
            Добавить
          </Button>
        </div>

        {data.skills.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {data.skills.map((skill) => (
              <div key={skill.id} className="flex items-center gap-2 rounded-xl border border-ink-200 py-1.5 pl-3.5 pr-1.5">
                <span className="text-sm font-medium text-ink-800">{skill.name}</span>
                <span className="text-xs text-ink-400">{skillLevelLabels[skill.level]}</span>
                <button
                  onClick={() => handleDeleteSkill(skill.name)}
                  disabled={mutation.isPending}
                  className="rounded-lg p-1 text-ink-300 hover:bg-rose-50 hover:text-rose-600"
                  aria-label={`Удалить ${skill.name}`}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded-xl bg-ink-50 p-4 text-sm text-ink-500">Добавьте навыки, чтобы улучшить карьерные рекомендации и подбор возможностей.</p>
        )}
      </Card>

      <Card>
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-ink-900">
          <Sparkles className="h-4.5 w-4.5 text-brand-600" style={{ height: 18, width: 18 }} /> Подписки
        </h2>
        {data.subscriptions.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {data.subscriptions.map((sub) => (
              <Badge key={sub.id} tone={sub.active ? 'success' : 'neutral'}>
                {sub.topic}{sub.newItems > 0 && ` · ${sub.newItems} новых`}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-sm text-ink-500">Подпишитесь на темы на странице «Возможности», чтобы получать уведомления.</p>
        )}
      </Card>

      <Sheet open={editOpen} onClose={() => setEditOpen(false)} title="Редактировать профиль">
        <div className="space-y-4">
          <Input label="Университет" value={form.university} onChange={(e) => setForm({ ...form, university: e.target.value })} />
          <Input label="Институт" value={form.institute} onChange={(e) => setForm({ ...form, institute: e.target.value })} />
          <Input label="Программа" value={form.program} onChange={(e) => setForm({ ...form, program: e.target.value })} />
          <Select label="Курс" value={form.studyYear} onChange={(e) => setForm({ ...form, studyYear: e.target.value })}>
            <option value="">Не указан</option>
            {STUDY_YEARS.map((y) => <option key={y} value={y}>{y} курс</option>)}
          </Select>
          <Textarea
            label="Карьерная цель"
            rows={3}
            value={form.careerGoal}
            onChange={(e) => setForm({ ...form, careerGoal: e.target.value })}
            placeholder="Например: BIM-координатор в строительстве"
          />
          <Input
            label="Интересы"
            hint="Через запятую"
            value={form.interests}
            onChange={(e) => setForm({ ...form, interests: e.target.value })}
            placeholder="BIM, проектирование, стажировки"
          />
          <Button fullWidth loading={mutation.isPending} onClick={saveBasicInfo}>Сохранить</Button>
        </div>
      </Sheet>
    </div>
  )
}
