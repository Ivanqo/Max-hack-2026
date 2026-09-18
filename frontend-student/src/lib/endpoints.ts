import { apiClient } from './api'
import type {
  CareerAnalysis,
  CareerGoalOption,
  CareerGpsSummary,
  Institute,
  KnowledgeItem,
  KnowledgeSearchResponse,
  OnboardingPayload,
  OptionItem,
  Opportunity,
  Program,
  SelectedSkill,
  SkillOption,
  StudentProfileResponse,
  StudentProfileUpdate,
  SubscriptionItem,
} from '@/types'

export const fetchUniversities = async (): Promise<OptionItem[]> => {
  const { data } = await apiClient.get('/universities')
  return data
}

export const fetchInstitutes = async (universityId: string): Promise<Institute[]> => {
  const { data } = await apiClient.get('/institutes', { params: { universityId } })
  return data
}

export const fetchPrograms = async (instituteId: string): Promise<Program[]> => {
  const { data } = await apiClient.get('/programs', { params: { instituteId } })
  return data
}

export const fetchInterests = async (): Promise<OptionItem[]> => {
  const { data } = await apiClient.get('/interests')
  return data
}

export const fetchSkillOptions = async (): Promise<SkillOption[]> => {
  const { data } = await apiClient.get('/skills')
  return data
}

export const submitOnboarding = async (payload: OnboardingPayload): Promise<{ completed: boolean }> => {
  const { data } = await apiClient.post('/onboarding', payload)
  return data
}

export const fetchCareerGpsSummary = async (): Promise<CareerGpsSummary> => {
  const { data } = await apiClient.get('/student/career-gps')
  return data
}

export const fetchCareerGoals = async (): Promise<CareerGoalOption[]> => {
  const { data } = await apiClient.get('/career/goals')
  return data
}

export const fetchCareerAnalysis = async (roleId: number): Promise<CareerAnalysis> => {
  const { data } = await apiClient.get(`/career/analysis/${roleId}`)
  return data
}

export interface OpportunityFilters {
  search?: string
  type?: string
  minMatch?: number
}

export const fetchOpportunities = async (filters: OpportunityFilters = {}): Promise<Opportunity[]> => {
  const params: Record<string, string> = {}
  if (filters.search) params.search = filters.search
  if (filters.type) params.type = filters.type
  if (filters.minMatch) params.minMatch = String(filters.minMatch)
  const { data } = await apiClient.get('/student/opportunities', { params })
  return data
}

export const fetchOpportunityDetail = async (id: string): Promise<Opportunity> => {
  const { data } = await apiClient.get(`/student/opportunities/${id}`)
  return data
}

export const saveOpportunity = async (id: string): Promise<void> => {
  await apiClient.post(`/student/opportunities/${id}/save`)
}

export const unsaveOpportunity = async (id: string): Promise<void> => {
  await apiClient.delete(`/student/opportunities/${id}/save`)
}

export const fetchSubscriptions = async (): Promise<SubscriptionItem[]> => {
  const { data } = await apiClient.get('/student/subscriptions')
  return data
}

export const createSubscription = async (topic: string): Promise<SubscriptionItem> => {
  const { data } = await apiClient.post('/student/subscriptions', { topic, filters: { topic }, active: true })
  return data
}

export const fetchStudentProfile = async (): Promise<StudentProfileResponse> => {
  const { data } = await apiClient.get('/student/profile')
  return data
}

export const updateStudentProfile = async (payload: StudentProfileUpdate): Promise<StudentProfileResponse> => {
  const { data } = await apiClient.patch('/student/profile', payload)
  return data
}

export const searchKnowledge = async (query: string): Promise<KnowledgeSearchResponse> => {
  if (!query.trim()) {
    return { results: [], total: 0, query: '' }
  }
  const { data } = await apiClient.get('/knowledge/search', { params: { q: query } })
  return data
}

export const fetchKnowledgeList = async (): Promise<KnowledgeItem[]> => {
  const { data } = await apiClient.get('/knowledge')
  return data
}

export const fetchKnowledgeDetail = async (id: string): Promise<KnowledgeItem> => {
  const { data } = await apiClient.get(`/knowledge/${id}`)
  return data
}

export const levelFromSkills = (skills: SelectedSkill[], name: string): number | undefined =>
  skills.find((skill) => skill.name.toLowerCase() === name.toLowerCase())?.level
