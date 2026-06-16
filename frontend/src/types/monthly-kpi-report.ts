// Type definitions for Monthly KPI Report API response

export interface MetricItem {
  section: string
  label: string
  value: string
  roleAvg: string
}

export interface DailyMetric {
  day: string
  score: number
}

export interface DailyTimeMetric {
  day: string
  minutes: number
  label: string
}

export interface EmployeeRecord {
  name: string
  role: string
  manager: string
  department: string
  timezone: string
  workplace: string
  domain: string
  score: number
  mon: number
  tue: number
  wed: number
  thu: number
  fri: number
  firstActivity: string
  lastActivity: string
  estAvailHours: string
  activeTime: string
  activeTimeMin: number
  pctActive: string
  pct1stHalf: string
  pct2ndHalf: string
  monTime: string
  tueTime: string
  wedTime: string
  thuTime: string
  friTime: string
  monTimeMin: number
  tueTimeMin: number
  wedTimeMin: number
  thuTimeMin: number
  friTimeMin: number
  mostProdWeek: string
  mostProdDay: string
  mostProdHour: string
  leastProdWeek: string
  leastProdDay: string
  leastProdHour: string
  intMeetPct: string
  extMeetPct: string
  intMeetTime: string
  extMeetTime: string
  popMeetTime: string
  daysInOffice: string
  avgScoreInOffice: string
  avgInOfficeActiveTime: string
  daysRemote: string
  avgScoreRemote: string
  avgRemoteActiveTime: string
}

export interface TriageItem {
  name: string
  manager: string
  role: string
  score: number
  scoreGap: string
  roleAvg: number
  activeTime: string
  timeGap: string
  roleAvgTime: string
  gaps: string[]
  standouts: string[]
  daily: DailyMetric[]
  dailyTime: DailyTimeMetric[]
  firstActivity: string
  lastActivity: string
  pctActive: string
  mostProductiveDay: string
  leastProductiveDay: string
}

export interface CompanyMetrics {
  name: string
  period: string
  totalEmployees: number
  flagged: number
  inactive: number
  topPerformers: number
  avgScore: number
  avgActiveTime: string
  avgActiveTimeMin: number
  flaggedPct: string
}

export interface RoleMetric {
  role: string
  avg: number
  avgTime: number
  avgTimeLabel: string
}

export interface DailyChart {
  day: string
  score: number
}

export interface GroupAvgs {
  score: string
  mon: string
  tue: string
  wed: string
  thu: string
  fri: string
  firstActivity: string
  lastActivity: string
  estAvailHours: string
  activeTime: string
  pctActive: string
  mostProdDay?: string
  leastProdDay?: string
}

export interface ToolMeta {
  name: string
  cat: string
  munit: string
  platformCat: string
}

export interface Config {
  tabs: Record<string, boolean>
  scorecard: Record<string, boolean>
  dataLayout: Record<string, any>
  scoped_manager?: string | null
  hierarchy_depth: number
  report_title: string
  report_kind: string
  has_work_mode: boolean
  daily_deep_dive: boolean
  employee_scorecard: boolean
  workforce_dimensions: string[]
  default_metric: string
  default_workforce_view: string
  kpi_card_mode: string
  comparison_baseline: string
  score_denominator: string
  working_day_gates: boolean
  percentile_view: boolean
  company_label: string
  priorPeriodStart?: string | null
  priorPeriodEnd?: string | null
  priorPeriodLabel?: string | null
  currentPeriodLabel: string
}

export interface MonthlyKpiReportResponse {
  COMPANY: CompanyMetrics
  ROLES: RoleMetric[]
  COMPANY_DAILY: DailyChart[]
  COMPANY_DAILY_TIME: DailyTimeMetric[]
  ROLE_DAILY: Record<string, DailyChart[]>
  ROLE_DAILY_TIME: Record<string, DailyTimeMetric[]>
  ROLE_AVGS: Record<string, GroupAvgs>
  MANAGER_DAILY: Record<string, DailyChart[]>
  MANAGER_DAILY_TIME: Record<string, DailyTimeMetric[]>
  MANAGER_AVGS: Record<string, GroupAvgs>
  DEPARTMENT_DAILY: Record<string, DailyChart[]>
  DEPARTMENT_DAILY_TIME: Record<string, DailyTimeMetric[]>
  DEPARTMENT_AVGS: Record<string, GroupAvgs>
  DOMAIN_DAILY: Record<string, DailyChart[]>
  DOMAIN_DAILY_TIME: Record<string, DailyTimeMetric[]>
  COMPANY_AVGS: GroupAvgs
  COMPANY_DAILY_WM: Record<string, DailyChart[]>
  ROLE_DAILY_WM: Record<string, Record<string, DailyChart[]>>
  MANAGER_DAILY_WM: Record<string, Record<string, DailyChart[]>>
  DEPARTMENT_DAILY_WM: Record<string, Record<string, DailyChart[]>>
  TOOLS_WM: Record<string, Record<string, string>>
  TOOL_META: Record<string, ToolMeta>
  NEEDS_ATTENTION: TriageItem[]
  INACTIVE: TriageItem[]
  TOP_PERFORMERS: TriageItem[]
  ALL_EMPLOYEES: EmployeeRecord[]
  CONFIG: Config
  BOTTOM_10_LIST?: any[]
  ORG_CUTOFFS?: Record<string, any>
  DAILY_DETAIL?: Record<string, any>
  SCORECARD_MEETINGS?: Record<string, any>
}
