import api from './client';
import type { Analytics, CareerRole, KnowledgeBase, Opportunity, User } from '@/types';

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export const fetchAnalytics = async (): Promise<Analytics> => {
  const { data } = await api.get('/admin/analytics');
  return data;
};

// ---------------------------------------------------------------------------
// Opportunities
// ---------------------------------------------------------------------------

export interface OpportunityFormValues {
  title: string;
  description: string;
  type: string;
  company: string;
  location: string;
  remote: boolean;
  requirements: string[];
  deadline: string | null;
  sourceUrl: string;
  verifiedStatus: string;
  published: boolean;
  skills: { name: string; level: number }[];
}

export const fetchOpportunities = async (): Promise<Opportunity[]> => {
  const { data } = await api.get('/admin/opportunities');
  return data;
};

export const createOpportunity = async (payload: OpportunityFormValues): Promise<Opportunity> => {
  const { data } = await api.post('/admin/opportunities', payload);
  return data;
};

export interface OpportunityRecipientPreview {
  recipientCount: number;
  linkedCount: number;
  recipients: { id: number; name: string; maxLinked: boolean; subscriptions: string[] }[];
}

export const previewOpportunityRecipients = async (payload: OpportunityFormValues): Promise<OpportunityRecipientPreview> => {
  const { data } = await api.post('/admin/opportunities/recipients-preview', payload);
  return data;
};

export const updateOpportunity = async (id: string, payload: OpportunityFormValues): Promise<Opportunity> => {
  const { data } = await api.put(`/admin/opportunities/${id}`, payload);
  return data;
};

export const deleteOpportunity = async (id: string): Promise<void> => {
  await api.delete(`/admin/opportunities/${id}`);
};

// ---------------------------------------------------------------------------
// Career roles
// ---------------------------------------------------------------------------

export interface CareerRoleFormValues {
  title: string;
  description: string;
  avgSalary: string;
  demandLevel: string;
  active: boolean;
  educationPath: string[];
  skills: { name: string; level: number }[];
}

export const fetchCareerRoles = async (): Promise<CareerRole[]> => {
  const { data } = await api.get('/career-roles');
  return data;
};

export const createCareerRole = async (payload: CareerRoleFormValues): Promise<CareerRole> => {
  const { data } = await api.post('/admin/career-roles', payload);
  return data;
};

export const updateCareerRole = async (id: string, payload: CareerRoleFormValues): Promise<CareerRole> => {
  const { data } = await api.put(`/admin/career-roles/${id}`, payload);
  return data;
};

export const deleteCareerRole = async (id: string): Promise<void> => {
  await api.delete(`/admin/career-roles/${id}`);
};

// ---------------------------------------------------------------------------
// Knowledge base
// ---------------------------------------------------------------------------

export interface KnowledgeFormValues {
  title: string;
  content: string;
  category: string;
  sourceUrl: string;
  audience: string[];
  verifiedStatus: string;
  published: boolean;
  actualUntil: string | null;
}

export const fetchKnowledgeItems = async (): Promise<KnowledgeBase[]> => {
  const { data } = await api.get('/admin/knowledge');
  return data;
};

export const createKnowledgeItem = async (payload: KnowledgeFormValues): Promise<KnowledgeBase> => {
  const { data } = await api.post('/admin/knowledge', payload);
  return data;
};

export const updateKnowledgeItem = async (id: string, payload: KnowledgeFormValues): Promise<KnowledgeBase> => {
  const { data } = await api.put(`/admin/knowledge/${id}`, payload);
  return data;
};

export const deleteKnowledgeItem = async (id: string): Promise<void> => {
  await api.delete(`/admin/knowledge/${id}`);
};

// ---------------------------------------------------------------------------
// Users (admin-only, real /api/v1/accounts/users/ DRF surface)
// ---------------------------------------------------------------------------

export interface UsersPage {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
}

export const fetchUsers = async (search?: string): Promise<UsersPage> => {
  const { data } = await api.get('/v1/accounts/users/', { params: search ? { search } : undefined });
  return data;
};

export const setUserActive = async (id: number, active: boolean): Promise<void> => {
  await api.post(`/v1/accounts/users/${id}/${active ? 'activate' : 'deactivate'}/`);
};

export interface AdminStudentProfile {
  user: { id: number; email: string; full_name: string; university: string; date_joined: string; last_login: string | null; max_linked: boolean };
  profile: null | { university: string; institute: string; program: string; study_year: number | null; interests: string[]; career_goal: string; onboarding_completed: boolean; updated_at: string };
  skills: { name: string; level: number; verified: boolean }[];
  subscriptions: { id: number; topic: string; filters: Record<string, unknown>; active: boolean; updated_at: string }[];
}

export const fetchStudentProfile = async (id: number): Promise<AdminStudentProfile> => {
  const { data } = await api.get(`/v1/accounts/users/${id}/student-profile/`);
  return data;
};

export interface UserStats {
  total_users: number;
  active_users: number;
  by_role: { students: number; mentors: number; organizers: number; admins: number };
}

export const fetchUserStats = async (): Promise<UserStats> => {
  const { data } = await api.get('/v1/accounts/users/stats/');
  return data;
};
