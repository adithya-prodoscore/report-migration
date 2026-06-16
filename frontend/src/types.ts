// MonthlyKPI API response types (mirrors backend schemas.py)

export interface DailyBucket {
  date: string;
  score: number;
  active_minutes: number;
  work_mode?: string;
}

export interface EmployeeRecord {
  employee_id: string;
  name: string;
  role: string;
  department: string;
  manager: string;
  timezone?: string;
  overall_score: number;
  overall_active_minutes: number;
  overall_active_pct: string; // "75.3%"
  in_office_pct: string; // "25.0%"
  remote_pct: string; // "75.0%"
  collab_score: number;
  call_score: number;
  focus_score: number;
  daily_buckets?: DailyBucket[];
}

export interface TriageEmployee {
  employee_id: string;
  name: string;
  role: string;
  score: number;
  active_minutes: number;
}

export interface CompanyKPI {
  total_employees: number;
  avg_score: number;
  avg_active_minutes: number;
  avg_active_pct: string; // "45.2%"
}

export interface AvgsRecord {
  avg_score: number;
  avg_active_minutes: number;
  avg_active_pct: string;
}

export interface WorkModePivot {
  in_office?: Record<string, unknown>;
  remote?: Record<string, unknown>;
}

export interface MonthlyKpiResponse {
  start_date: string;
  end_date: string;
  domain_id: number;
  generated_at: string; // ISO timestamp
  COMPANY: CompanyKPI;
  ROLES: Record<string, AvgsRecord>;
  ALL_EMPLOYEES: EmployeeRecord[];
  NEEDS_ATTENTION: TriageEmployee[];
  INACTIVE: TriageEmployee[];
  TOP_PERFORMERS: TriageEmployee[];
  AVGS: Record<string, string>;
  CONFIG?: Record<string, unknown>;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}