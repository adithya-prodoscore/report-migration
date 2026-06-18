'use client'

interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
  variant?: 'default' | 'warning' | 'success' | 'inactive'
}

export function KpiCard({ label, value, sub, variant = 'default' }: KpiCardProps) {
  const variantClasses = {
    default: 'text-kpi-blue-500',
    warning: 'text-status-attention',
    success: 'text-status-top',
    inactive: 'text-status-inactive',
  }[variant]

  const bgClasses = {
    default: 'bg-white border-neutral-200',
    warning: 'bg-status-attention-bg border-status-attention',
    success: 'bg-status-top-bg border-status-top',
    inactive: 'bg-status-inactive-bg border-status-inactive',
  }[variant]

  return (
    <div className={`rounded-xl border p-5 shadow-xs ${bgClasses}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-neutral-500 mb-1">
        {label}
      </p>
      <p className={`text-3xl font-extrabold ${variantClasses}`}>{value}</p>
      {sub && <p className="mt-1 text-sm text-neutral-500">{sub}</p>}
    </div>
  )
}
