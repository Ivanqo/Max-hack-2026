import type { OpportunityType } from '@/types'

export const opportunityTypeLabels: Record<OpportunityType, string> = {
  internship: 'Стажировка',
  vacancy: 'Вакансия',
  project: 'Проект',
  hackathon: 'Хакатон',
  event: 'Событие',
  course: 'Курс',
}

export const opportunityTypeOptions: { value: OpportunityType; label: string }[] = [
  { value: 'internship', label: 'Стажировка' },
  { value: 'vacancy', label: 'Вакансия' },
  { value: 'project', label: 'Проект' },
  { value: 'hackathon', label: 'Хакатон' },
  { value: 'event', label: 'Событие' },
  { value: 'course', label: 'Курс' },
]

export const knowledgeAudienceLabels: Record<string, string> = {
  all: 'Все',
  students: 'Студенты',
  freshmen: 'Первокурсники',
  graduates: 'Выпускники',
  postgraduates: 'Магистранты',
  international: 'Иностранные студенты',
  local: 'Локальные студенты',
}

export const skillLevelLabels: Record<number, string> = {
  1: 'Начальный',
  2: 'Начальный',
  3: 'Средний',
  4: 'Продвинутый',
  5: 'Экспертный',
}

export function matchTone(score: number): 'success' | 'brand' | 'warning' | 'danger' {
  if (score >= 80) return 'success'
  if (score >= 60) return 'brand'
  if (score >= 40) return 'warning'
  return 'danger'
}

export function formatDate(value: string | null | undefined) {
  if (!value) return null
  return new Date(value).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function daysUntil(value: string | null | undefined): number | null {
  if (!value) return null
  const diff = new Date(value).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}
