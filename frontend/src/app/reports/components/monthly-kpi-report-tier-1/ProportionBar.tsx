'use client'

import { useState } from 'react'
import type { EmployeeRecordT1 } from '@/hooks/useMonthlyKpiReportTier1'

interface ProportionBarProps {
  employees: EmployeeRecordT1[]
}

interface Segment {
  key: string
  label: string
  color: string
  count: number
}

export function ProportionBar({ employees }: ProportionBarProps) {
  const [tooltip, setTooltip] = useState<{ seg: Segment; x: number } | null>(null)

  const total = employees.length
  const segments: Segment[] = [
    { key: 'needs-attention', label: 'Needs Attention', color: '#F1433C', count: employees.filter(e => e.status === 'needs-attention').length },
    { key: 'inactive',        label: 'Inactive',        color: '#E4D20E', count: employees.filter(e => e.status === 'inactive').length },
    { key: 'most-engaged',    label: 'Most Engaged',    color: '#1E86D9', count: employees.filter(e => e.status === 'most-engaged').length },
    { key: 'on-track',        label: 'On Track',        color: '#B0B0B0', count: employees.filter(e => e.status === 'on-track').length },
  ].filter(s => s.count > 0)

  if (total === 0) return null

  return (
    <div className="relative mb-8">
      <div
        role="img"
        aria-label="Workforce composition by status"
        className="flex w-full h-3.5 rounded-full overflow-hidden bg-kpi-gray-100"
        style={{ boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.04)' }}
        onMouseLeave={() => setTooltip(null)}
      >
        {segments.map(seg => (
          <div
            key={seg.key}
            style={{ flexBasis: `${(seg.count / total) * 100}%`, backgroundColor: seg.color }}
            className="h-full flex-shrink-0 transition-all duration-300 cursor-default hover:scale-y-125"
            onMouseEnter={(e) => setTooltip({ seg, x: e.currentTarget.getBoundingClientRect().left + e.currentTarget.offsetWidth / 2 })}
            onMouseMove={(e) => {
              const rect = e.currentTarget.closest('.relative')!.getBoundingClientRect()
              setTooltip(t => t ? { ...t, x: e.clientX - rect.left } : null)
            }}
          />
        ))}
      </div>
      {tooltip && (
        <div
          className="absolute bottom-full mb-2 flex items-center gap-1.5 px-2.5 py-1.5 bg-kpi-gray-950 text-white rounded-lg text-xs font-medium whitespace-nowrap pointer-events-none z-50"
          style={{ left: tooltip.x, transform: 'translateX(-50%)' }}
          aria-hidden="true"
        >
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: tooltip.seg.color }} />
          <span className="font-bold">{tooltip.seg.label}</span>
          <span className="opacity-70">{tooltip.seg.count} · {Math.round((tooltip.seg.count / total) * 100)}% of company</span>
          <span
            className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0"
            style={{ borderLeft: '5px solid transparent', borderRight: '5px solid transparent', borderTop: '5px solid #262626' }}
          />
        </div>
      )}
    </div>
  )
}
