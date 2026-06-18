import { MonthlyKpiReportTier5Report } from '@/app/reports/components/monthly-kpi-report-tier-5/MonthlyKpiReportTier5Report'

export async function generateMetadata() {
  return { title: 'Monthly KPI Report Tier 5 | Prodoscore' }
}

export default async function MonthlyKpiReportTier5Page({
  searchParams,
}: {
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}) {
  const params = await searchParams

  return (
    <MonthlyKpiReportTier5Report
      domainId={params.domain_id ?? ''}
      startDate={params.start_date ?? ''}
      endDate={params.end_date ?? ''}
    />
  )
}
