export interface OptionItem {
  id: string
  name: string
}

export interface Institute extends OptionItem {
  universityId: string
}

export interface Program extends OptionItem {
  instituteId: string
}

export interface SkillOption {
  id: string
  name: string
  category: string
}

export interface SelectedSkill {
  name: string
  level: number
}

export interface OnboardingPayload {
  universityId: string
  instituteId: string
  courseId: string
  studyYear: string
  interests: string[]
  skills: SelectedSkill[]
  careerGoal: string
}

export interface CareerGpsSummary {
  currentScore: number
  maxScore: number
  recommendations: string[]
  nextSteps: string[]
}

export interface CareerGoalOption {
  id: number
  title: string
  description: string
  category: string
}

export interface SkillGap {
  skill: string
  currentLevel: number
  requiredLevel: number
  priority: 'high' | 'medium' | 'low'
}

export interface NextAction {
  id: number
  title: string
  type: 'course' | 'quiz' | 'resource'
  estimatedTime: string
  priority: number
}

export interface CareerAnalysis {
  goal: CareerGoalOption
  readinessScore: number
  strengths: string[]
  gaps: SkillGap[]
  nextActions: NextAction[]
  lastUpdated: string
}

export type OpportunityType = 'internship' | 'vacancy' | 'project' | 'hackathon' | 'event' | 'course'

export interface OpportunitySkillRef {
  name: string
  level: number
  weight: number
}

export interface Opportunity {
  id: string
  title: string
  company: string
  description: string
  type: OpportunityType
  location: string
  remote: boolean
  requirements: string[]
  skills: OpportunitySkillRef[]
  status: 'active' | 'inactive'
  published: boolean
  verifiedStatus: 'pending' | 'verified' | 'rejected'
  deadline: string | null
  sourceUrl: string
  matchPercentage: number
  matchReasons: string[]
  gaps: string[]
  isSaved: boolean
  postedDate: string
  createdAt: string
  updatedAt: string
}

export interface KnowledgeSource {
  id: string
  name: string
  url?: string
  type: 'web' | 'database'
}

export interface KnowledgeItem {
  id: string
  title: string
  content: string
  summary: string
  category: string
  audience: string[]
  source: KnowledgeSource
  sourceUrl: string
  published: boolean
  verified: boolean
  verifiedStatus: 'draft' | 'verified' | 'outdated'
  actualUntil: string | null
  createdAt: string
  updatedAt: string
  relevanceScore?: number
}

export interface KnowledgeSearchResponse {
  results: KnowledgeItem[]
  total: number
  query: string
  found?: boolean
  message?: string
  escalation?: {
    unit: string
    contact: string
  }
}

export interface StudentSkillItem {
  id: string
  name: string
  level: number
  levelLabel: string
  verified: boolean
  evidence?: string
}

export interface SubscriptionItem {
  id: string
  name: string
  type: string
  active: boolean
  topic: string
  filters: Record<string, unknown>
  lastUpdate: string
  newItems: number
}

export interface StudentProfileResponse {
  user: {
    id: number
    email: string
    firstName: string
    lastName: string
    name: string
    role: string
    maxUserId?: string | null
  }
  profile: {
    university: string
    institute: string
    program: string
    studyYear: number | null
    interests: string[]
    careerGoal: string
    onboardingCompleted: boolean
    updatedAt: string
  }
  skills: StudentSkillItem[]
  subscriptions: SubscriptionItem[]
}

export interface StudentProfileUpdate {
  firstName?: string
  lastName?: string
  university?: string
  institute?: string
  program?: string
  studyYear?: string | number
  interests?: string[]
  careerGoal?: string
  skills?: SelectedSkill[]
}
