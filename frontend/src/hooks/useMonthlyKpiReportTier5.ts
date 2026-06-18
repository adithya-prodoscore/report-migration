import { useQuery } from '@tanstack/react-query'

// ---------------------------------------------------------------------------
// TypeScript types mirroring the Pydantic schemas
// ---------------------------------------------------------------------------

export interface DailyScore {
  day: string
  score: number
}

export interface DailyTime {
  day: string
  minutes: number
  label: string
}

export interface CompanyRecord {
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

export interface RoleRecord {
  role: string
  avg: number
  avgTime: number
  avgTimeLabel: string
}

export interface ToolMetaRecord {
  name: string
  cat: string
  munit: string
  platformCat: string
}

export interface TriageEmployeeRecord {
  name: string
  manager: string
  role: string
  score: number
  scoreGap: number
  roleAvg: number
  activeTime: string
  timeGap: string
  roleAvgTime: string
  roleAvgTimeMin?: number
  activeTimeMin?: number
  gaps: unknown[]
  standouts?: unknown[]
  daily: DailyScore[]
  dailyTime: string[]
  dailyTimeMin: number[]
  firstActivity: string
  lastActivity: string
  pctActive: string
  mostProductiveDay: string
  leastProductiveDay: string
}

export interface InactiveEmployeeRecord {
  name: string
  manager: string
  role: string
  score: number
  scoreGap: number
  roleAvg: number
  activeTime: string
  timeGap: string | Record<string, never>
  roleAvgTime: string
  reason: string
  daily: DailyScore[]
  dailyTime: string[]
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
  pctActive: string
  pct1stHalf: string
  pct2ndHalf: string
  monTime: string
  tueTime: string
  wedTime: string
  thuTime: string
  friTime: string
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
  [key: string]: string | number  // dynamic pivot + tool columns
}

export interface ConfigRecord {
  tabs: { pulse: boolean; workforce: boolean; data: boolean; scorecard: boolean }
  report_title: string
  report_kind: string
  has_work_mode: boolean
  workforce_dimensions: string[]
  default_workforce_view: string
  kpi_card_mode: string
  currentPeriodLabel: string
  [key: string]: unknown
}

export interface MonthlyKpiReportTier5Data {
  COMPANY: CompanyRecord
  ROLES: RoleRecord[]
  COMPANY_DAILY: DailyScore[]
  COMPANY_DAILY_TIME: DailyTime[]
  ROLE_AVGS: Record<string, Record<string, string>>
  MANAGER_AVGS: Record<string, Record<string, string>>
  DEPARTMENT_AVGS: Record<string, Record<string, string>>
  ROLE_DAILY: Record<string, DailyScore[]>
  MANAGER_DAILY: Record<string, DailyScore[]>
  DEPARTMENT_DAILY: Record<string, DailyScore[]>
  ROLE_DAILY_TIME: Record<string, DailyTime[]>
  MANAGER_DAILY_TIME: Record<string, DailyTime[]>
  DEPARTMENT_DAILY_TIME: Record<string, DailyTime[]>
  NEEDS_ATTENTION: TriageEmployeeRecord[]
  INACTIVE: InactiveEmployeeRecord[]
  TOP_PERFORMERS: TriageEmployeeRecord[]
  ALL_EMPLOYEES: EmployeeRecord[]
  COMPANY_AVGS: Record<string, string>
  TOOL_META: Record<string, ToolMetaRecord>
  COMPANY_DAILY_WM: Record<string, DailyScore[]>
  ROLE_DAILY_WM: Record<string, Record<string, DailyScore[]>>
  MANAGER_DAILY_WM: Record<string, Record<string, DailyScore[]>>
  DEPARTMENT_DAILY_WM: Record<string, Record<string, DailyScore[]>>
  TOOLS_WM: Record<string, Record<string, string>>
  CONFIG: ConfigRecord
  generated_at: string
  domain_id: number
}

// ---------------------------------------------------------------------------
// Fetch function
// ---------------------------------------------------------------------------

async function fetchMonthlyKpiReportTier5(
  domainId: string,
  startDate: string,
  endDate: string,
): Promise<MonthlyKpiReportTier5Data> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? ''
  const url = `${base}/api/v1/monthly-kpi-report-tier-5?domain_id=${domainId}&start_date=${startDate}&end_date=${endDate}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useMonthlyKpiReportTier5(
  domainId: string,
  startDate: string,
  endDate: string,
) {
  return useQuery({
    queryKey: ['monthly-kpi-report-tier-5', domainId, startDate, endDate],
    queryFn: () => fetchMonthlyKpiReportTier5(domainId, startDate, endDate),
    enabled: Boolean(domainId && startDate && endDate),
  })
}
