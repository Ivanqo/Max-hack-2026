export interface User {
  id: string;
  email: string;
  role: 'admin' | 'editor' | 'institute_admin' | 'university_admin' | 'student';
  createdAt: string;
}

export interface KnowledgeBase {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Opportunity {
  id: string;
  title: string;
  company: string;
  description: string;
  type: 'internship' | 'job' | 'project';
  location: string;
  remote: boolean;
  requirements: string[];
  status: 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
}

export interface CareerRole {
  id: string;
  title: string;
  description: string;
  skills: string[];
  avgSalary: string;
  demandLevel: 'high' | 'medium' | 'low';
  educationPath: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Analytics {
  totalUsers: number;
  activeUsers: number;
  totalOpportunities: number;
  totalKnowledgeBase: number;
  userGrowth: Array<{ date: string; count: number }>;
  popularRoles: Array<{ role: string; count: number }>;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}
