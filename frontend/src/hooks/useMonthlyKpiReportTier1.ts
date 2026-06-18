import { useQuery } from '@tanstack/react-query'

// ---------------------------------------------------------------------------
// TypeScript types (mirroring backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface MetricItemT1 {
  section: string
  label: string
  value: string
  roleAvg: string
}

export interface EmployeeRecordT1 {
  id: string
  name: string
  dept: string
  role: string
  manager: string
  score: number
  roleAvg: number
  delta: string
  activeTime: string
  trendCy: number[]
  trendColor: string
  status: 'inactive' | 'needs-attention' | 'most-engaged' | 'on-track'
  metrics: MetricItemT1[]
}

export interface FilterOptionsT1 {
  dept: string[]
  role: string[]
  manager: string[]
  employee: string[]
}

export interface HeaderMetadataT1 {
  title: string
  breadcrumb: string
  dateRange: string
  dateFrom: string
  dateTo: string
}

export interface MonthlyKpiReportTier1Data {
  employees: EmployeeRecordT1[]
  filter_options: FilterOptionsT1
  header: HeaderMetadataT1
}

// ---------------------------------------------------------------------------
// Fetch function
// ---------------------------------------------------------------------------

async function fetchMonthlyKpiReportTier1(
  domainId: string,
  startDate: string,
  endDate: string,
): Promise<MonthlyKpiReportTier1Data> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? ''
  const url = `${base}/api/v1/monthly-kpi-report-tier-1?domain_id=${encodeURIComponent(domainId)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`)
  return res.json() as Promise<MonthlyKpiReportTier1Data>
}

// ---------------------------------------------------------------------------
// React Query hook
// ---------------------------------------------------------------------------

export function useMonthlyKpiReportTier1(
  domainId: string,
  startDate: string,
  endDate: string,
) {
  return useQuery({
    queryKey: ['monthly-kpi-report-tier-1', domainId, startDate, endDate],
    queryFn: () => fetchMonthlyKpiReportTier1(domainId, startDate, endDate),
    enabled: Boolean(domainId && startDate && endDate),
  })
}
