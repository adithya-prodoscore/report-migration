import { MonthlyKpiReportTier2 } from '@/app/reports/components/monthly-kpi-report-tier-2/MonthlyKpiReportTier2'

export async function generateMetadata() {
  return { title: 'Monthly KPI Report Tier 2 | Prodoscore' }
}

export default async function MonthlyKpiReportTier2Page({
  searchParams,
}: {
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}) {
  const params = await searchParams

  return (
    <MonthlyKpiReportTier2
      domainId={params.domain_id ?? ''}
      startDate={params.start_date ?? ''}
      endDate={params.end_date ?? ''}
    />
  )
}
