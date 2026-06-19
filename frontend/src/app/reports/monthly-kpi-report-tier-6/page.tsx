import { MonthlyKpiReportTier6Report } from '@/app/reports/components/monthly-kpi-report-tier-6/MonthlyKpiReportTier6Report'

export async function generateMetadata() {
  return { title: 'Monthly KPI Report Tier 6 | Prodoscore' }
}

export default async function MonthlyKpiReportTier6Page({
  searchParams,
}: {
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}) {
  const params = await searchParams

  return (
    <MonthlyKpiReportTier6Report
      domainId={params.domain_id ?? ''}
      startDate={params.start_date ?? ''}
      endDate={params.end_date ?? ''}
    />
  )
}
