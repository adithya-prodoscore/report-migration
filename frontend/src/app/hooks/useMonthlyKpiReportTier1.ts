import { useState, useEffect } from 'react'

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

interface UseMonthlyKpiReportTier1Options {
  domainId: string
  startDate: string
  endDate: string
}

interface UseMonthlyKpiReportTier1Result {
  data: MonthlyKpiReportTier1Data | null
  isLoading: boolean
  isError: boolean
  error: Error | null
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

const useMonthlyKpiReportTier1 = ({
  domainId,
  startDate,
  endDate,
}: UseMonthlyKpiReportTier1Options): UseMonthlyKpiReportTier1Result => {
  const [data, setData] = useState<MonthlyKpiReportTier1Data | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setIsLoading(true)
        setIsError(false)
        setError(null)

        const params = new URLSearchParams({
          domain_id: domainId,
          start_date: startDate,
          end_date: endDate,
        })

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
        const response = await fetch(
          `${baseUrl}/api/v1/monthly-kpi-report-tier-1?${params}`,
          {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          }
        )

        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`)
        }

        const jsonData = await response.json()
        setData(jsonData)
      } catch (err) {
        const fetchError = err instanceof Error ? err : new Error('Unknown error fetching report')
        setError(fetchError)
        setIsError(true)
      } finally {
        setIsLoading(false)
      }
    }

    if (domainId && startDate && endDate) {
      fetchReport()
    }
  }, [domainId, startDate, endDate])

  return { data, isLoading, isError, error }
}

export default useMonthlyKpiReportTier1
