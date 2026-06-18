export interface ReportMeta {
  slug: string
  title: string
  description: string
}

export const REPORTS: ReportMeta[] = [
  {
    slug: 'monthly-kpi-report',
    title: 'Monthly KPI Report',
    description: 'Employee productivity scores, performance triage, daily trends, and workforce analytics for the selected period.',
  },
  {
    slug: 'monthly-kpi-report-tier-2',
    title: 'Monthly KPI Report Tier 2',
    description: 'Full-fidelity Monthly KPI Report with production 6-gate working-day logic, role/manager/department cohort breakdowns, work-mode splits, and complete tool usage columns.',
  },
]
