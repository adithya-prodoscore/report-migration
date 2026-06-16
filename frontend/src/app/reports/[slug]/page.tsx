import { REPORTS } from '../registry'
import { notFound } from 'next/navigation'

// 1. Statically import your report components normally
// import MonthlyKpiReport from '../components/monthly-kpi/MonthlyKpiReport'

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
  // const resolvedSearchParams = await searchParams

  // 2. Double-check the registry
  const report = REPORTS.find((r) => r.slug === slug)
  if (!report) notFound()

  // 3. Clear, explicit routing by slug
  switch (slug) {
    case 'monthly-kpi':
      return (<></>
        // <MonthlyKpiReport
        //   domainId={resolvedSearchParams.domain_id}
        //   startDate={resolvedSearchParams.start_date}
        //   endDate={resolvedSearchParams.end_date}
        // />
      )
      
    // Whenever you or the AI add a new report, just drop another case statement here.
    // case 'another-report':
    //   return <AnotherReportComponent ... />

    default:
      notFound()
  }
}