import { useQuery } from '@tanstack/react-query'

// ---------------------------------------------------------------------------
// Types — mirrors MonthlyKpiReportTier7Response Pydantic schema
// ---------------------------------------------------------------------------

export interface DayScore {
  day: string
  score: number
}

export interface DayTime {
  day: string
  minutes: number
  label: string
}

export interface RoleSummary {
  role: string
  avg: number
  avgTime: number
  avgTimeLabel: string
}

export interface CompanyMeta {
  name: string
  period: string
  totalEmployees: number
  flagged: number
  inactive: number
  topPerformers: number
  avgScore: number
  avgActiveTime: string
  flaggedPct: string
  avgActiveTimeMin: number
}

export interface TriageDailyEntry {
  day: string
  score: number
}

export interface NeedsAttentionRecord {
  name: string
  manager: string
  role: string
  score: number
  scoreGap: number
  roleAvg: number
  activeTime: string
  timeGap: string
  roleAvgTime: string
  gaps: unknown[]
  daily: TriageDailyEntry[]
  dailyTime: string[]
  dailyTimeMin: number[]
  firstActivity: string
  lastActivity: string
  pctActive: string
  mostProductiveDay: string
  leastProductiveDay: string
}

export interface InactiveRecord {
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
  daily: TriageDailyEntry[]
  dailyTime: string[]
}

export interface TopPerformerRecord {
  name: string
  manager: string
  role: string
  score: number
  scoreGap: number
  roleAvg: number
  activeTime: string
  activeTimeMin: number
  timeGap: string
  roleAvgTime: string
  roleAvgTimeMin: number
  daily: TriageDailyEntry[]
  dailyTime: string[]
  dailyTimeMin: number[]
  firstActivity: string
  lastActivity: string
  pctActive: string
  mostProductiveDay: string
  leastProductiveDay: string
  standouts: unknown[]
}

export interface ToolMetaEntry {
  name: string
  cat: string
  munit: string
  platformCat: string
}

export interface ReportConfig {
  tabs: { pulse: boolean; workforce: boolean; data: boolean; scorecard: boolean }
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
  currentPeriodLabel: string
  [key: string]: unknown
}

export interface MonthlyKpiReportTier7Data {
  COMPANY: CompanyMeta
  ROLES: RoleSummary[]
  COMPANY_DAILY: DayScore[]
  COMPANY_DAILY_TIME: DayTime[]
  ROLE_AVGS: Record<string, Record<string, string>>
  ROLE_DAILY: Record<string, DayScore[]>
  ROLE_DAILY_TIME: Record<string, DayTime[]>
  MANAGER_AVGS: Record<string, Record<string, string>>
  MANAGER_DAILY: Record<string, DayScore[]>
  MANAGER_DAILY_TIME: Record<string, DayTime[]>
  DEPARTMENT_AVGS: Record<string, Record<string, string>>
  DEPARTMENT_DAILY: Record<string, DayScore[]>
  DEPARTMENT_DAILY_TIME: Record<string, DayTime[]>
  DOMAIN_AVGS: unknown[]
  DOMAIN_DAILY: Record<string, DayScore[]>
  DOMAIN_DAILY_TIME: unknown[]
  COMPANY_AVGS: Record<string, string>
  TOOL_META: Record<string, ToolMetaEntry>
  COMPANY_DAILY_WM: Record<string, DayScore[]>
  ROLE_DAILY_WM: Record<string, Record<string, DayScore[]>>
  MANAGER_DAILY_WM: Record<string, Record<string, DayScore[]>>
  DEPARTMENT_DAILY_WM: Record<string, Record<string, DayScore[]>>
  TOOLS_WM: Record<string, Record<string, string>>
  NEEDS_ATTENTION: NeedsAttentionRecord[]
  INACTIVE: InactiveRecord[]
  TOP_PERFORMERS: TopPerformerRecord[]
  ALL_EMPLOYEES: Record<string, unknown>[]
  BOTTOM_10_LIST: unknown[]
  ORG_CUTOFFS: Record<string, unknown>
  SCORECARD_MEETINGS: Record<string, unknown>
  DAILY_DETAIL: Record<string, unknown>
  CONFIG: ReportConfig
  generated_at: string | null
  domain_id: number
}

// ---------------------------------------------------------------------------
// Fetch function
// ---------------------------------------------------------------------------

async function fetchMonthlyKpiReportTier7(
  domainId: string,
  startDate: string,
  endDate: string,
): Promise<MonthlyKpiReportTier7Data> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? ''
  const url = `${base}/api/v1/reports/monthly-kpi-report-tier-7?domain_id=${domainId}&start_date=${startDate}&end_date=${endDate}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useMonthlyKpiReportTier7(
  domainId: string,
  startDate: string,
  endDate: string,
) {
  return useQuery({
    queryKey: ['monthly-kpi-report-tier-7', domainId, startDate, endDate],
    queryFn: () => fetchMonthlyKpiReportTier7(domainId, startDate, endDate),
    enabled: Boolean(domainId && startDate && endDate),
  })
}
