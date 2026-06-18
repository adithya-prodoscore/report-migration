'use client'

import { useState } from 'react'
import type { TriageItemTier2, DailyChart } from '@/types/monthly-kpi-report-tier-2'

interface EmployeeCardTier2Props {
  employee: TriageItemTier2
  type: 'attention' | 'inactive' | 'top'
}

function TierBadge({ type }: { type: 'attention' | 'inactive' | 'top' }) {
  if (type === 'attention') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-attention-bg text-status-attention">
        Needs Attention
      </span>
    )
  }
  if (type === 'inactive') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-inactive-bg text-status-inactive">
        Inactive
      </span>
    )
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-top-bg text-status-top">
      Top Performer
    </span>
  )
}

function MiniSparkline({ data }: { data: DailyChart[] }) {
  if (!data || data.length === 0) return null
  const max = Math.max(...data.map((d) => d.score), 1)
  return (
    <div className="flex items-end gap-0.5 h-8">
      {data.map((d) => {
        const heightPct = max > 0 ? (d.score / max) * 100 : 0
        return (
          <div key={d.day} className="flex flex-col items-center gap-0.5 flex-1">
            <div
              className="w-full rounded-sm bg-brand-indigo-400 transition-all"
              style={{ height: `${Math.max(heightPct, 8)}%` }}
              title={`${d.day}: ${d.score}`}
            />
            <span className="text-xs text-neutral-400">{d.day[0]}</span>
          </div>
        )
      })}
    </div>
  )
}

export function EmployeeCardTier2({ employee, type }: EmployeeCardTier2Props) {
  const [expanded, setExpanded] = useState(false)

  const scoreGap =
    typeof employee.scoreGap === 'number'
      ? employee.scoreGap > 0
        ? `+${employee.scoreGap}`
        : String(employee.scoreGap)
      : String(employee.scoreGap)

  const gapColor =
    type === 'top'
      ? 'text-tier-high'
      : typeof employee.scoreGap === 'number' && employee.scoreGap < 0
      ? 'text-tier-critical'
      : 'text-neutral-500'

  return (
    <div className="bg-white border border-neutral-200 rounded-xl shadow-xs overflow-hidden">
      {/* Card Header */}
      <div className="px-4 py-3 flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-neutral-900 truncate">{employee.name}</span>
            <TierBadge type={type} />
          </div>
          <div className="mt-0.5 text-sm text-neutral-500">
            {employee.role} · {employee.manager}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-xl font-bold text-neutral-900">{employee.score}</div>
          <div className={`text-xs font-medium ${gapColor}`}>
            {scoreGap} vs role avg {employee.roleAvg}
          </div>
        </div>
      </div>

      {/* Score Bar */}
      <div className="px-4">
        <div className="h-1.5 w-full bg-neutral-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              employee.score >= 70
                ? 'bg-tier-high'
                : employee.score >= 40
                ? 'bg-tier-avg'
                : 'bg-tier-low'
            }`}
            style={{ width: `${Math.min(employee.score, 100)}%` }}
          />
        </div>
      </div>

      {/* Summary Row */}
      <div className="px-4 py-2 flex items-center gap-4 text-sm text-neutral-600 border-b border-neutral-100">
        <span>⏱ {employee.activeTime}</span>
        <span>🕐 {employee.firstActivity} – {employee.lastActivity}</span>
        {employee.pctActive && employee.pctActive !== '-' && (
          <span>{employee.pctActive} active</span>
        )}
      </div>

      {/* Expandable Detail */}
      <button
        className="w-full px-4 py-2 text-sm text-brand-indigo-600 hover:bg-neutral-50 flex items-center justify-between transition-colors"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-label={expanded ? 'Collapse employee detail' : 'Expand employee detail'}
      >
        <span>{expanded ? 'Hide detail' : 'Show daily breakdown'}</span>
        <svg
          className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-neutral-100 pt-3">
          {/* Sparkline */}
          {employee.daily && employee.daily.length > 0 && (
            <div>
              <div className="text-xs font-medium text-neutral-500 mb-1">Daily Score (Mon–Fri)</div>
              <MiniSparkline data={employee.daily} />
            </div>
          )}

          {/* Daily Time */}
          {employee.dailyTime && employee.dailyTime.length > 0 && (
            <div>
              <div className="text-xs font-medium text-neutral-500 mb-1">Active Time by Day</div>
              <div className="flex gap-2 text-xs text-neutral-700">
                {(['Mon','Tue','Wed','Thu','Fri'] as const).map((day, i) => (
                  <div key={day} className="flex flex-col items-center">
                    <span className="text-neutral-400">{day}</span>
                    <span>{employee.dailyTime[i] ?? '—'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Productivity */}
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-neutral-400 text-xs">Best day</span>
              <div className="text-neutral-700 font-medium">{employee.mostProductiveDay}</div>
            </div>
            <div>
              <span className="text-neutral-400 text-xs">Slowest day</span>
              <div className="text-neutral-700 font-medium">{employee.leastProductiveDay}</div>
            </div>
          </div>

          {/* Role gap detail */}
          <div className="text-sm grid grid-cols-2 gap-2">
            <div>
              <span className="text-neutral-400 text-xs">Role avg active time</span>
              <div className="text-neutral-700">{employee.roleAvgTime}</div>
            </div>
            <div>
              <span className="text-neutral-400 text-xs">Time gap</span>
              <div className={`font-medium ${gapColor}`}>
                {typeof employee.timeGap === 'string' ? employee.timeGap : '—'}
              </div>
            </div>
          </div>

          {/* Inactive reason */}
          {type === 'inactive' && employee.reason && (
            <div className="text-xs text-status-inactive bg-status-inactive-bg rounded-lg px-3 py-2">
              {employee.reason}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
