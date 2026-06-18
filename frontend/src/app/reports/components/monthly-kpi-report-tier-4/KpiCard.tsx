// KpiCard — a single Pulse tab KPI summary card
// HTML source: Pulse tab KPI cards section
// Interactions: none (display only)
// Depends on: none

interface KpiCardProps {
  label: string
  value: string | number
  subLabel?: string
  variant?: 'default' | 'attention' | 'inactive' | 'top'
}

const variantStyles: Record<string, string> = {
  default: 'bg-white border-neutral-200',
  attention: 'bg-status-attention-bg border-status-attention',
  inactive: 'bg-status-inactive-bg border-status-inactive',
  top: 'bg-status-top-bg border-status-top',
}

const valueStyles: Record<string, string> = {
  default: 'text-neutral-900',
  attention: 'text-status-attention',
  inactive: 'text-status-inactive',
  top: 'text-status-top',
}

export function KpiCard({ label, value, subLabel, variant = 'default' }: KpiCardProps) {
  return (
    <div
      className={`rounded-xl border p-5 shadow-xs flex flex-col gap-1 ${variantStyles[variant]}`}
    >
      <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">{label}</p>
      <p className={`text-3xl font-extrabold ${valueStyles[variant]}`}>{value}</p>
      {subLabel && (
        <p className="text-xs text-neutral-400 mt-0.5">{subLabel}</p>
      )}
    </div>
  )
}
