import { MonthlyKpiReportTier7Report } from '@/app/reports/components/monthly-kpi-report-tier-7/MonthlyKpiReportTier7Report'

export async function generateMetadata() {
  return { title: 'Monthly KPI Report Tier 7 | Prodoscore' }
}

export default async function MonthlyKpiReportTier7Page({
  searchParams,
}: {
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}) {
  const params = await searchParams

  return (
    <MonthlyKpiReportTier7Report
      domainId={params.domain_id ?? '9'}
      startDate={params.start_date ?? '2026-05-01'}
      endDate={params.end_date ?? '2026-05-29'}
    />
  )
}
