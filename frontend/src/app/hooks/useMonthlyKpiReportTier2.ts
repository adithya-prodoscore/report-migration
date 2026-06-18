import { useState, useEffect } from 'react'
import type { MonthlyKpiReportTier2Response } from '@/types/monthly-kpi-report-tier-2'

interface UseMonthlyKpiReportTier2Options {
  domainId: string
  startDate: string
  endDate: string
}

interface UseMonthlyKpiReportTier2Result {
  data: MonthlyKpiReportTier2Response | null
  isLoading: boolean
  isError: boolean
  error: Error | null
}

const useMonthlyKpiReportTier2 = ({
  domainId,
  startDate,
  endDate,
}: UseMonthlyKpiReportTier2Options): UseMonthlyKpiReportTier2Result => {
  const [data, setData] = useState<MonthlyKpiReportTier2Response | null>(null)
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
          `${baseUrl}/api/v1/monthly-kpi-report-tier-2?${params}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
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

export default useMonthlyKpiReportTier2
