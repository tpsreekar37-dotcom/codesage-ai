export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface Repository {
  id: string;
  name: string;
  type: 'zip' | 'github';
  github_url: string | null;
  status: 'active' | 'deleted';
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface Analysis {
  id: string;
  repository_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface Finding {
  severity: 'high' | 'medium' | 'low';
  file: string;
  line: number | null;
  category: 'security' | 'bug' | 'performance' | 'code_smell';
  message: string;
  suggestion: string;
}

export interface Report {
  id: string;
  analysis_id: string;
  score_quality: number;
  score_security: number;
  score_performance: number;
  score_maintainability: number;
  findings: Finding[];
  markdown_content: string;
  created_at: string;
}

export interface DashboardStats {
  total_repositories: number;
  total_analyses: number;
  completed_analyses: number;
  failed_analyses: number;
  average_quality_score: number;
  recent_analyses: Analysis[];
}
