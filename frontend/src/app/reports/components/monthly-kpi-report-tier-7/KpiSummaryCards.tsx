'use client'

import { CompanyMeta } from '@/hooks/useMonthlyKpiReportTier7'

interface KpiSummaryCardsProps {
  company: CompanyMeta
}

function ScoreTierColor(score: number): string {
  if (score >= 70) return 'text-kpi-tier-high'
  if (score >= 40) return 'text-kpi-tier-avg'
  return 'text-kpi-tier-critical'
}

function ScoreTierBg(score: number): string {
  if (score >= 70) return 'bg-kpi-tier-high-pale'
  if (score >= 40) return 'bg-kpi-tier-avg-bg'
  return 'bg-kpi-tier-critical-pale'
}

interface KpiCardProps {
  label: string
  count: number
  sublabel: string
  accentClass: string
  badgeText?: string
}

function KpiCard({ label, count, sublabel, accentClass, badgeText }: KpiCardProps) {
  return (
    <div className="rounded-lg bg-neutral-0 border border-neutral-200 shadow-sm overflow-hidden flex flex-col">
      <div className={`h-1 w-full ${accentClass}`} />
      <div className="p-5 flex flex-col gap-1 flex-1">
        <p className="text-xs font-semibold text-kpi-gray-500 uppercase tracking-wide">{label}</p>
        <p className="text-3xl font-bold text-neutral-900">{count}</p>
        <p className="text-xs text-kpi-gray-500">{sublabel}</p>
        {badgeText && (
          <span className="mt-1 inline-block text-xs font-medium text-kpi-gray-600 bg-kpi-gray-100 rounded-full px-2 py-0.5 w-fit">
            {badgeText}
          </span>
        )}
      </div>
    </div>
  )
}

export function KpiSummaryCards({ company }: KpiSummaryCardsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KpiCard
        label="Needs Attention"
        count={company.flagged}
        sublabel={`${company.flaggedPct} of workforce`}
        accentClass="bg-status-attention"
        badgeText={company.flaggedPct}
      />
      <KpiCard
        label="Inactive / PTO"
        count={company.inactive}
        sublabel="Low or no activity"
        accentClass="bg-status-inactive"
      />
      <KpiCard
        label="Top Performers"
        count={company.topPerformers}
        sublabel="Above role baseline"
        accentClass="bg-status-top"
      />
      <div className="rounded-lg bg-neutral-0 border border-neutral-200 shadow-sm overflow-hidden flex flex-col">
        <div className="h-1 w-full bg-kpi-blue-500" />
        <div className="p-5 flex flex-col gap-1 flex-1">
          <p className="text-xs font-semibold text-kpi-gray-500 uppercase tracking-wide">Company Score</p>
          <p className={`text-3xl font-bold ${ScoreTierColor(company.avgScore)}`}>
            {company.avgScore}
          </p>
          <p className="text-xs text-kpi-gray-500">{company.avgActiveTime} avg active</p>
          <span className={`mt-1 inline-block text-xs font-medium rounded-full px-2 py-0.5 w-fit ${ScoreTierBg(company.avgScore)} ${ScoreTierColor(company.avgScore)}`}>
            {company.totalEmployees} employees
          </span>
        </div>
      </div>
    </div>
  )
}
