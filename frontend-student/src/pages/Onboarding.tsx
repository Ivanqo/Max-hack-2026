import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CheckCircle2, Sparkles } from 'lucide-react'
import {
  fetchInstitutes,
  fetchInterests,
  fetchPrograms,
  fetchSkillOptions,
  fetchUniversities,
  submitOnboarding,
} from '@/lib/endpoints'
import type { OnboardingPayload } from '@/types'
import { Button, Chip, cn, ErrorState, LoadingState, Select, Textarea, useToast } from '@/ui'

const STEPS = ['Университет', 'Институт', 'Программа', 'Интересы', 'Навыки', 'Цель'] as const

function useOnboardingState() {
  const [data, setData] = useState<OnboardingPayload>({
    universityId: '',
    instituteId: '',
    courseId: '',
    studyYear: '',
    interests: [],
    skills: [],
    careerGoal: '',
  })
  const update = (field: keyof OnboardingPayload, value: unknown) => {
    setData((prev) => {
      const next = { ...prev, [field]: value } as OnboardingPayload
      if (field === 'universityId') {
        next.instituteId = ''
        next.courseId = ''
      } else if (field === 'instituteId') {
        next.courseId = ''
      }
      return next
    })
  }
  return { data, update }
}

function StepShell({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold text-ink-900 sm:text-2xl">{title}</h2>
        <p className="mt-1.5 text-sm text-ink-500">{description}</p>
      </div>
      {children}
    </div>
  )
}

function SelectionGrid<T extends { id: string; name: string }>({
  items,
  isLoading,
  isError,
  onRetry,
  selectedId,
  onSelect,
  emptyLabel,
}: {
  items: T[] | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
  selectedId: string
  onSelect: (id: string) => void
  emptyLabel: string
}) {
  if (isLoading) return <LoadingState label="Загружаем варианты…" />
  if (isError) return <ErrorState onRetry={onRetry} />
  if (!items || items.length === 0) return <p className="rounded-xl bg-ink-50 p-6 text-center text-sm text-ink-500">{emptyLabel}</p>
  return (
    <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onSelect(item.id)}
          aria-pressed={selectedId === item.id}
          className={cn(
            'flex min-h-[52px] items-center rounded-xl border-2 px-4 py-3 text-left text-sm font-medium transition-colors',
            selectedId === item.id ? 'border-brand-600 bg-brand-50 text-brand-800' : 'border-ink-200 text-ink-700 hover:border-brand-300 hover:bg-brand-50/40',
          )}
        >
          {item.name}
        </button>
      ))}
    </div>
  )
}

function Footer({ onBack, onNext, nextLabel = 'Продолжить', nextDisabled, loading, showBack = true }: {
  onBack?: () => void
  onNext: () => void
  nextLabel?: string
  nextDisabled?: boolean
  loading?: boolean
  showBack?: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-3 pt-2">
      {showBack ? (
        <Button variant="outline" onClick={onBack} leftIcon={<ArrowLeft className="h-4 w-4" />}>Назад</Button>
      ) : <span />}
      <Button onClick={onNext} disabled={nextDisabled} loading={loading} rightIcon={!loading ? <ArrowRight className="h-4 w-4" /> : undefined}>
        {nextLabel}
      </Button>
    </div>
  )
}

export default function Onboarding() {
  const navigate = useNavigate()
  const toast = useToast()
  const [step, setStep] = useState(0)
  const [submitted, setSubmitted] = useState(false)
  const { data, update } = useOnboardingState()

  const universities = useQuery({ queryKey: ['universities'], queryFn: fetchUniversities })
  const institutes = useQuery({
    queryKey: ['institutes', data.universityId],
    queryFn: () => fetchInstitutes(data.universityId),
    enabled: Boolean(data.universityId),
  })
  const programs = useQuery({
    queryKey: ['programs', data.instituteId],
    queryFn: () => fetchPrograms(data.instituteId),
    enabled: Boolean(data.instituteId),
  })
  const interests = useQuery({ queryKey: ['interests'], queryFn: fetchInterests })
  const skillOptions = useQuery({ queryKey: ['skill-options'], queryFn: fetchSkillOptions })

  // Preselect a single university automatically for a smoother demo flow.
  useEffect(() => {
    if (universities.data && universities.data.length === 1 && !data.universityId) {
      update('universityId', universities.data[0].id)
    }
    // `update` is re-created every render; the universityId guard makes this a safe one-shot effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [universities.data, data.universityId])

  const mutation = useMutation({
    mutationFn: submitOnboarding,
    onSuccess: () => {
      setSubmitted(true)
      window.setTimeout(() => navigate('/home', { replace: true }), 1600)
    },
    onError: () => toast.error('Не удалось отправить анкету', 'Проверьте соединение и попробуйте ещё раз.'),
  })

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1))
  const back = () => setStep((s) => Math.max(s - 1, 0))

  const toggleInterest = (id: string) => {
    update('interests', data.interests.includes(id) ? data.interests.filter((i) => i !== id) : [...data.interests, id])
  }

  const selectedSkills = new Map(data.skills.map((s) => [s.name, s]))
  const toggleSkill = (name: string) => {
    const exists = selectedSkills.has(name)
    update('skills', exists ? data.skills.filter((s) => s.name !== name) : [...data.skills, { name, level: 3 }])
  }
  const setSkillLevel = (name: string, level: number) => {
    update('skills', data.skills.map((s) => (s.name === name ? { ...s, level } : s)))
  }

  if (submitted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-brand-gradient-soft px-4">
        <div className="animate-scale-in rounded-3xl bg-white p-10 text-center shadow-card">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-accent-100 text-accent-700">
            <CheckCircle2 className="h-8 w-8" />
          </span>
          <h1 className="mt-5 text-xl font-bold text-ink-900">Ваш профиль готов</h1>
          <p className="mt-2 text-sm text-ink-500">Строим ваш карьерный маршрут…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-brand-gradient-soft px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-xl">
        <div className="mb-6 flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient text-white">
            <Sparkles className="h-4.5 w-4.5" style={{ height: 18, width: 18 }} />
          </span>
          <span className="text-base font-bold text-ink-900">UniPath MAX</span>
        </div>

        <div className="mb-6">
          <div className="mb-2 flex items-center justify-between text-xs font-medium text-ink-400">
            <span>Шаг {step + 1} из {STEPS.length}</span>
            <span>{STEPS[step]}</span>
          </div>
          <div className="flex gap-1.5">
            {STEPS.map((label, i) => (
              <div key={label} className={cn('h-1.5 flex-1 rounded-full', i <= step ? 'bg-brand-600' : 'bg-white/70')} />
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-card sm:p-8">
          {step === 0 && (
            <StepShell title="Выберите университет" description="Укажите университет, в котором вы сейчас учитесь.">
              <SelectionGrid
                items={universities.data}
                isLoading={universities.isLoading}
                isError={universities.isError}
                onRetry={() => universities.refetch()}
                selectedId={data.universityId}
                onSelect={(id) => update('universityId', id)}
                emptyLabel="Университеты недоступны"
              />
              <Footer showBack={false} onNext={next} nextDisabled={!data.universityId} />
            </StepShell>
          )}

          {step === 1 && (
            <StepShell title="Выберите институт" description="Укажите ваш институт или факультет.">
              <SelectionGrid
                items={institutes.data}
                isLoading={institutes.isLoading}
                isError={institutes.isError}
                onRetry={() => institutes.refetch()}
                selectedId={data.instituteId}
                onSelect={(id) => update('instituteId', id)}
                emptyLabel="Институты недоступны"
              />
              <Footer onBack={back} onNext={next} nextDisabled={!data.instituteId} />
            </StepShell>
          )}

          {step === 2 && (
            <StepShell title="Программа и курс" description="Укажите образовательную программу и курс обучения.">
              <SelectionGrid
                items={programs.data}
                isLoading={programs.isLoading}
                isError={programs.isError}
                onRetry={() => programs.refetch()}
                selectedId={data.courseId}
                onSelect={(id) => update('courseId', id)}
                emptyLabel="Программы недоступны"
              />
              <Select label="Курс обучения" value={data.studyYear} onChange={(e) => update('studyYear', e.target.value)}>
                <option value="">Выберите курс</option>
                {[1, 2, 3, 4, 5, 6].map((y) => <option key={y} value={y}>{y}</option>)}
              </Select>
              <Footer onBack={back} onNext={next} nextDisabled={!data.courseId || !data.studyYear} />
            </StepShell>
          )}

          {step === 3 && (
            <StepShell title="Что вам интересно?" description="Отметьте одну или несколько тем — так мы точнее подберём материалы.">
              {interests.isLoading ? (
                <LoadingState />
              ) : interests.isError ? (
                <ErrorState onRetry={() => interests.refetch()} />
              ) : (
                <div className="flex flex-wrap gap-2">
                  {(interests.data || []).map((interest) => (
                    <Chip key={interest.id} selected={data.interests.includes(interest.id)} onClick={() => toggleInterest(interest.id)}>
                      {interest.name}
                    </Chip>
                  ))}
                </div>
              )}
              <Footer onBack={back} onNext={next} nextDisabled={data.interests.length === 0} />
            </StepShell>
          )}

          {step === 4 && (
            <StepShell title="Ваши навыки" description="Выберите навыки, которыми уже умеете пользоваться, и укажите уровень.">
              {skillOptions.isLoading ? (
                <LoadingState />
              ) : skillOptions.isError ? (
                <ErrorState onRetry={() => skillOptions.refetch()} />
              ) : (
                <div className="space-y-2">
                  {(skillOptions.data || []).map((skill) => {
                    const selected = selectedSkills.get(skill.name)
                    return (
                      <div key={skill.id} className={cn('flex items-center justify-between gap-3 rounded-xl border-2 px-4 py-2.5', selected ? 'border-brand-600 bg-brand-50' : 'border-ink-200')}>
                        <button type="button" onClick={() => toggleSkill(skill.name)} className="flex-1 text-left text-sm font-medium text-ink-800">
                          {skill.name}
                        </button>
                        {selected && (
                          <select
                            value={selected.level}
                            onChange={(e) => setSkillLevel(skill.name, Number(e.target.value))}
                            className="rounded-lg border border-ink-200 bg-white px-2 py-1.5 text-xs"
                            aria-label={`Уровень: ${skill.name}`}
                          >
                            <option value={2}>Начальный</option>
                            <option value={3}>Средний</option>
                            <option value={4}>Продвинутый</option>
                            <option value={5}>Экспертный</option>
                          </select>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
              <Footer onBack={back} onNext={next} nextDisabled={data.skills.length === 0} />
            </StepShell>
          )}

          {step === 5 && (
            <StepShell title="Какая у вас карьерная цель?" description="Опишите роль или результат, к которому вы стремитесь — мы подберём релевантные возможности.">
              <Textarea
                rows={5}
                value={data.careerGoal}
                onChange={(e) => update('careerGoal', e.target.value)}
                placeholder="Например: хочу стать BIM-координатором и работать с цифровыми моделями строительных объектов"
              />
              <Footer
                onBack={back}
                onNext={() => mutation.mutate(data)}
                nextLabel="Завершить анкету"
                nextDisabled={!data.careerGoal.trim()}
                loading={mutation.isPending}
              />
            </StepShell>
          )}
        </div>
      </div>
    </div>
  )
}
