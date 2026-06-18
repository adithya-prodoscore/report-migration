import { MonthlyKpiReportTier3Report } from '@/app/reports/components/monthly-kpi-report-tier-3/MonthlyKpiReportTier3Report'

export async function generateMetadata() {
  return { title: 'Monthly KPI Report Tier 3 | Prodoscore' }
}

export default async function MonthlyKpiReportTier3Page({
  searchParams,
}: {
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}) {
  const params = await searchParams

  return (
    <MonthlyKpiReportTier3Report
      domainId={params.domain_id ?? ''}
      startDate={params.start_date ?? ''}
      endDate={params.end_date ?? ''}
    />
  )
}
