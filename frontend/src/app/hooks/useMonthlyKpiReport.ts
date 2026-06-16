import { useState, useEffect } from 'react'
import type { MonthlyKpiReportResponse } from '@/types/monthly-kpi-report'

interface UseMonthlyKpiReportOptions {
  domainId: string
  startDate: string
  endDate: string
}

interface UseMonthlyKpiReportResult {
  data: MonthlyKpiReportResponse | null
  isLoading: boolean
  isError: boolean
  error: Error | null
}

const useMonthlyKpiReport = ({
  domainId,
  startDate,
  endDate,
}: UseMonthlyKpiReportOptions): UseMonthlyKpiReportResult => {
  const [data, setData] = useState<MonthlyKpiReportResponse | null>(null)
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

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/v1/monthly-kpi-report?${params}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          }
        )

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`)
        }

        const jsonData = await response.json()
        setData(jsonData)
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error')
        setError(error)
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

export default useMonthlyKpiReport
