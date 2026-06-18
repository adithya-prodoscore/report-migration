import type { CompanyRecord } from '@/hooks/useMonthlyKpiReportTier5'

interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
  highlight?: 'attention' | 'inactive' | 'top' | 'neutral'
}

function highlightClasses(h?: string): string {
  switch (h) {
    case 'attention': return 'bg-status-attention-bg border-status-attention text-status-attention'
    case 'inactive': return 'bg-status-inactive-bg border-status-inactive text-status-inactive'
    case 'top': return 'bg-status-top-bg border-status-top text-status-top'
    default: return 'bg-neutral-50 border-neutral-200 text-neutral-900'
  }
}

export function KpiCard({ label, value, sub, highlight }: KpiCardProps) {
  return (
    <div className={`rounded-lg border px-5 py-4 flex flex-col gap-1 ${highlightClasses(highlight)}`}>
      <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{label}</p>
      <p className="text-2xl font-extrabold leading-tight">{value}</p>
      {sub && <p className="text-xs opacity-60">{sub}</p>}
    </div>
  )
}

interface KpiCardsRowProps {
  company: CompanyRecord
}

export function KpiCardsRow({ company }: KpiCardsRowProps) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <KpiCard
        label="Needs Attention"
        value={company.flagged}
        sub={company.flaggedPct}
        highlight="attention"
      />
      <KpiCard
        label="Inactive / PTO"
        value={company.inactive}
        highlight="inactive"
      />
      <KpiCard
        label="Most Engaged"
        value={company.topPerformers}
        highlight="top"
      />
      <KpiCard
        label="Company Score"
        value={company.avgScore}
        sub={company.avgActiveTime}
        highlight="neutral"
      />
    </div>
  )
}
