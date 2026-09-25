export type UserRole = 'admin' | 'editor' | 'institute_admin' | 'university_admin' | 'student' | 'mentor' | 'organizer';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  university: string;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export const MANAGER_ROLES: UserRole[] = ['admin', 'editor', 'institute_admin', 'university_admin'];

export type VerifiedStatus = 'draft' | 'verified' | 'outdated';

export interface KnowledgeBase {
  id: string;
  title: string;
  content: string;
  category: string;
  responsibleUnit: string;
  audience: string[];
  tags: string[];
  sourceUrl: string;
  published: boolean;
  verified: boolean;
  verifiedStatus: VerifiedStatus;
  actualUntil: string | null;
  createdAt: string;
  updatedAt: string;
}

export type OpportunityType = 'internship' | 'vacancy' | 'project' | 'hackathon' | 'event' | 'course';
export type OpportunityVerifiedStatus = 'pending' | 'verified' | 'rejected';

export interface OpportunitySkillRef {
  name: string;
  level: number;
  weight: number;
}

export interface Opportunity {
  id: string;
  title: string;
  company: string;
  description: string;
  type: OpportunityType;
  location: string;
  remote: boolean;
  requirements: string[];
  skills: OpportunitySkillRef[];
  status: 'active' | 'inactive';
  published: boolean;
  verifiedStatus: OpportunityVerifiedStatus;
  deadline: string | null;
  sourceUrl: string;
  createdAt: string;
  updatedAt: string;
}

export type DemandLevel = 'high' | 'medium' | 'low';

export interface CareerRoleSkillRef {
  name: string;
  level: number;
}

export interface CareerRole {
  id: string;
  title: string;
  description: string;
  skills: string[];
  skillLevels: CareerRoleSkillRef[];
  avgSalary: string;
  demandLevel: DemandLevel;
  active: boolean;
  educationPath: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Analytics {
  totalUsers: number;
  activeUsers: number;
  totalOpportunities: number;
  activeOpportunities: number;
  totalKnowledgeBase: number;
  publishedKnowledge: number;
  userGrowth: Array<{ date: string; count: number }>;
  popularRoles: Array<{ role: string; count: number }>;
  topSearchQueries: Array<{ query: string; count: number }>;
  unansweredQueries: Array<{ query: string; count: number }>;
  opportunityViews: number;
  opportunitySaves: number;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  linkMaxProfile: (initData: string) => Promise<User>;
  logout: () => void;
}
