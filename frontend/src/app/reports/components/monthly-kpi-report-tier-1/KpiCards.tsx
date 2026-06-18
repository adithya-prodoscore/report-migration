'use client'

import { useMemo } from 'react'
import type { EmployeeRecordT1 } from '@/hooks/useMonthlyKpiReportTier1'

type Status = 'needs-attention' | 'inactive' | 'most-engaged' | 'on-track' | 'all'

interface KpiCardsProps {
  employees: EmployeeRecordT1[]
  activeStatus: Status | null
  onStatusClick: (s: Status) => void
}

interface CardCounts {
  needsAttention: number
  inactive: number
  mostEngaged: number
  total: number
}

export function KpiCards({ employees, activeStatus, onStatusClick }: KpiCardsProps) {
  const counts: CardCounts = useMemo(() => ({
    needsAttention: employees.filter(e => e.status === 'needs-attention').length,
    inactive: employees.filter(e => e.status === 'inactive').length,
    mostEngaged: employees.filter(e => e.status === 'most-engaged').length,
    total: employees.length,
  }), [employees])

  function pct(n: number) {
    if (counts.total === 0) return '0%'
    return `${Math.round((n / counts.total) * 100)}%`
  }

  const cards = [
    {
      status: 'needs-attention' as Status,
      count: counts.needsAttention,
      label: 'Needs Attention',
      descriptor: 'Below role baseline',
      colorBase: 'kpi-red',
      iconPath: 'M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01',
    },
    {
      status: 'inactive' as Status,
      count: counts.inactive,
      label: 'Inactive / PTO',
      descriptor: 'Verification needed',
      colorBase: 'kpi-yellow',
      iconPath: 'M6 4h4v16H6zM14 4h4v16h-4z',
    },
    {
      status: 'most-engaged' as Status,
      count: counts.mostEngaged,
      label: 'Most Engaged',
      descriptor: 'Recognition priority',
      colorBase: 'kpi-blue',
      iconPath: 'M12 2a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM8.21 13.89 7 22l5-3 5 3-1.21-8.12',
    },
    {
      status: 'all' as Status,
      count: counts.total,
      label: 'All Employees',
      descriptor: 'Everyone in view',
      colorBase: 'kpi-gray',
      iconPath: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
    },
  ]

  const colorMap: Record<string, { accentBar: string; iconBg: string; iconFg: string; glow: string }> = {
    'kpi-red':    { accentBar: 'bg-kpi-red-500',    iconBg: 'bg-kpi-red-50',    iconFg: 'text-kpi-red-500',    glow: 'ring-kpi-red-100' },
    'kpi-yellow': { accentBar: 'bg-kpi-yellow-500', iconBg: 'bg-kpi-yellow-50', iconFg: 'text-kpi-yellow-700', glow: 'ring-kpi-yellow-100' },
    'kpi-blue':   { accentBar: 'bg-kpi-blue-500',   iconBg: 'bg-kpi-blue-50',   iconFg: 'text-kpi-blue-500',   glow: 'ring-kpi-blue-100' },
    'kpi-gray':   { accentBar: 'bg-kpi-gray-400',   iconBg: 'bg-kpi-gray-50',   iconFg: 'text-kpi-gray-600',   glow: 'ring-kpi-gray-100' },
  }

  return (
    <div className="grid grid-cols-2 gap-6 lg:grid-cols-4 mb-4">
      {cards.map(card => {
        const colors = colorMap[card.colorBase]
        const isActive = activeStatus === card.status
        return (
          <button
            key={card.status}
            type="button"
            aria-pressed={isActive}
            onClick={() => onStatusClick(card.status)}
            className={[
              'relative bg-kpi-white border rounded-xl p-5 text-left cursor-pointer',
              'transition-all duration-150 hover:-translate-y-px',
              isActive ? `ring-2 ${colors.glow} border-current shadow-shadow-sm` : 'border-kpi-gray-100',
              'overflow-hidden',
            ].join(' ')}
          >
            {/* Top accent bar */}
            <span
              className={`absolute top-0 left-0 right-0 h-[3px] ${colors.accentBar}`}
              aria-hidden="true"
            />
            {/* Icon */}
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-3 ${colors.iconBg} ${colors.iconFg}`}>
              <svg className="w-[18px] h-[18px] stroke-current fill-none" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d={card.iconPath} />
              </svg>
            </div>
            {/* Value */}
            <div className="text-4xl font-extrabold text-kpi-gray-950 tracking-tight leading-tight mb-1">
              {card.count}
            </div>
            <div className="text-sm font-bold text-kpi-gray-900 mb-0.5">{card.label}</div>
            <div className="text-xs text-kpi-gray-500 leading-snug mb-1.5">{card.descriptor}</div>
            {/* Stat line */}
            {card.status !== 'all' && (
              <div className="flex items-baseline gap-1 text-xs">
                <span className="font-bold text-kpi-gray-700">{pct(card.count)}</span>
                <span className="text-kpi-gray-400">of company</span>
              </div>
            )}
            {card.status === 'all' && (
              <span className="text-xs text-kpi-gray-400">the whole company</span>
            )}
          </button>
        )
      })}
    </div>
  )
}
