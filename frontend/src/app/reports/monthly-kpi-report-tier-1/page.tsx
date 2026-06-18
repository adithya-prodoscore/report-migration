import { MonthlyKpiReportTier1 } from '@/app/reports/components/monthly-kpi-report-tier-1/MonthlyKpiReportTier1'

export async function generateMetadata() {
  return { title: 'Monthly KPI Report Tier 1 | Prodoscore' }
}

export default async function MonthlyKpiReportTier1Page({
  searchParams,
}: {
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}) {
  const params = await searchParams

  return (
    <MonthlyKpiReportTier1
      domainId={params.domain_id ?? ''}
      startDate={params.start_date ?? ''}
      endDate={params.end_date ?? ''}
    />
  )
}
