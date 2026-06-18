import { MonthlyKpiReportTier4Report } from '@/app/reports/components/monthly-kpi-report-tier-4/MonthlyKpiReportTier4Report'

export async function generateMetadata() {
  return { title: 'Monthly KPI Report Tier 4 | Prodoscore' }
}

export default async function MonthlyKpiReportTier4Page({
  searchParams,
}: {
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}) {
  const params = await searchParams

  return (
    <MonthlyKpiReportTier4Report
      domainId={params.domain_id ?? ''}
      startDate={params.start_date ?? ''}
      endDate={params.end_date ?? ''}
    />
  )
}
