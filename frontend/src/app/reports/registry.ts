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
    slug: 'monthly-kpi-report-tier-1',
    title: 'Monthly KPI Report Tier 1',
    description: 'Anchor KPI Report mirroring the Prodoscore website: per-employee SCORE, WORK HABITS, MEETINGS, TECH MODULES, and WEB BROWSER metrics with triage status for each employee.',
  },
  {
    slug: 'monthly-kpi-report-tier-2',
    title: 'Monthly KPI Report Tier 2',
    description: 'Full-fidelity Monthly KPI Report with production 6-gate working-day logic, role/manager/department cohort breakdowns, work-mode splits, and complete tool usage columns.',
  },
  {
    slug: 'monthly-kpi-report-tier-3',
    title: 'Monthly KPI Report Tier 3',
    description: 'Full end-to-end Monthly KPI Report (Pulse/Workforce/Data tabs) with production 6-gate working-day logic, triage engine, role/manager/department cohort breakdowns, work-mode splits, and complete tool usage columns.',
  },
]
