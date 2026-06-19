import { REPORTS } from '../registry'
import { notFound } from 'next/navigation'
import { MonthlyKpiReport } from '../components/monthly-kpi-report'
import { MonthlyKpiReportTier7Report } from '../components/monthly-kpi-report-tier-7/MonthlyKpiReportTier7Report'

interface PageProps {
  params: Promise<{ slug: string }>
  searchParams: Promise<{ domain_id?: string; start_date?: string; end_date?: string }>
}

// Simple metadata generator
export async function generateMetadata({ params }: PageProps) {
  const { slug } = await params
  const report = REPORTS.find((r) => r.slug === slug)
  if (!report) return { title: 'Not Found' }
  return { title: `${report.title} | Prodoscore` }
}

export default async function ReportPage({ params, searchParams }: PageProps) {
  const { slug } = await params
  const resolvedSearchParams = await searchParams

  // Double-check the registry
  const report = REPORTS.find((r) => r.slug === slug)
  if (!report) notFound()

  // Default to sample period if not provided
  const domainId = resolvedSearchParams.domain_id || '9'
  const startDate = resolvedSearchParams.start_date || '2026-05-01'
  const endDate = resolvedSearchParams.end_date || '2026-05-29'

  // Clear, explicit routing by slug
  switch (slug) {
    case 'monthly-kpi-report':
      return (
        <div className="max-w-full mx-auto px-4 py-8 sm:px-6 lg:px-8">
          <MonthlyKpiReport
            domainId={domainId}
            startDate={startDate}
            endDate={endDate}
          />
        </div>
      )

    case 'monthly-kpi-report-tier-7':
      return (
        <MonthlyKpiReportTier7Report
          domainId={domainId}
          startDate={startDate}
          endDate={endDate}
        />
      )

    // Whenever you or the AI add a new report, just drop another case statement here.
    // case 'another-report':
    //   return <AnotherReportComponent ... />

    default:
      notFound()
  }
}
