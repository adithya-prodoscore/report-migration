'use client'

import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import type {
  TriageEmployeeRecord,
  InactiveEmployeeRecord,
  DailyScore,
} from '@/hooks/useMonthlyKpiReportTier3'

type TriageVariant = 'flagged' | 'inactive' | 'top'

interface TriageCardListProps {
  title: string
  items: (TriageEmployeeRecord | InactiveEmployeeRecord)[]
  variant: TriageVariant
}

function scoreTierClass(score: number): string {
  if (score >= 70) return 'text-kpi-tier-high bg-kpi-tier-high-pale'
  if (score >= 40) return 'text-kpi-tier-monitor bg-kpi-tier-monitor-pale'
  return 'text-kpi-tier-critical bg-kpi-tier-critical-pale'
}

function MiniTrendChart({ daily }: { daily: DailyScore[] }) {
  const option = {
    textStyle: { fontFamily: 'var(--font-family-primary, Geist, sans-serif)' },
    tooltip: { show: false },
    grid: { left: 2, right: 2, top: 2, bottom: 2 },
    xAxis: { type: 'category', data: daily.map((d) => d.day), show: false },
    yAxis: { type: 'value', min: 0, max: 100, show: false },
    series: [
      {
        type: 'bar',
        data: daily.map((d) => d.score),
        itemStyle: { color: '#1E86D9', borderRadius: [2, 2, 0, 0] },
        barMaxWidth: 12,
      },
    ],
  }
  return (
    <ReactECharts
      option={option}
      style={{ height: '52px', width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}

function TriageCard({
  item,
  variant,
  expanded,
  onToggle,
}: {
  item: TriageEmployeeRecord | InactiveEmployeeRecord
  variant: TriageVariant
  expanded: boolean
  onToggle: () => void
}) {
  const scoreGap = item.scoreGap
  const gapColor = scoreGap >= 0 ? 'text-status-top' : 'text-tier-low'
  const gapSign = scoreGap >= 0 ? '+' : ''

  const borderColors: Record<TriageVariant, string> = {
    flagged: 'border-l-status-attention',
    inactive: 'border-l-status-inactive',
    top: 'border-l-status-top',
  }

  return (
    <div className={`bg-white rounded-xl border border-neutral-200 border-l-4 ${borderColors[variant]} shadow-xs overflow-hidden`}>
      {/* Header row */}
      <button
        className="w-full text-left px-5 py-4 flex items-center justify-between gap-4"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${scoreTierClass(item.score)}`}>
            {item.score}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-neutral-900 truncate">{item.name}</p>
            <p className="text-xs text-neutral-500 truncate">{item.role} &middot; {item.manager}</p>
          </div>
        </div>
        <div className="flex items-center gap-6 flex-shrink-0 text-right">
          <div>
            <p className="text-xs text-neutral-400 mb-0.5">Role avg</p>
            <p className="text-sm font-semibold text-neutral-700">{item.roleAvg}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-400 mb-0.5">Gap</p>
            <p className={`text-sm font-semibold ${gapColor}`}>{gapSign}{scoreGap}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-400 mb-0.5">Active</p>
            <p className="text-sm font-medium text-neutral-700">{item.activeTime}</p>
          </div>
          <svg
            className={`w-4 h-4 text-neutral-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-5 pb-5 border-t border-neutral-100">
          {'reason' in item && (
            <p className="mt-3 text-xs text-neutral-500 italic">{(item as InactiveEmployeeRecord).reason}</p>
          )}
          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-neutral-400">First activity</p>
              <p className="text-sm font-medium text-neutral-700">
                {'firstActivity' in item ? (item as TriageEmployeeRecord).firstActivity : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">Last activity</p>
              <p className="text-sm font-medium text-neutral-700">
                {'lastActivity' in item ? (item as TriageEmployeeRecord).lastActivity : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">% Active</p>
              <p className="text-sm font-medium text-neutral-700">
                {'pctActive' in item ? (item as TriageEmployeeRecord).pctActive : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">Role avg time</p>
              <p className="text-sm font-medium text-neutral-700">{item.roleAvgTime}</p>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wide mb-2">Daily trend (Mon–Fri)</p>
            <MiniTrendChart daily={item.daily} />
          </div>
          <div className="mt-3 flex gap-4">
            {'mostProductiveDay' in item && (
              <p className="text-xs text-neutral-400">
                Best day: <span className="font-semibold text-neutral-600">{(item as TriageEmployeeRecord).mostProductiveDay}</span>
              </p>
            )}
            {'leastProductiveDay' in item && (
              <p className="text-xs text-neutral-400">
                Weakest day: <span className="font-semibold text-neutral-600">{(item as TriageEmployeeRecord).leastProductiveDay}</span>
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function TriageCardList({ title, items, variant }: TriageCardListProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  if (items.length === 0) return null

  const headerColor: Record<TriageVariant, string> = {
    flagged: 'text-status-attention',
    inactive: 'text-neutral-500',
    top: 'text-status-top',
  }

  return (
    <section>
      <h3 className={`text-sm font-semibold uppercase tracking-wider mb-3 ${headerColor[variant]}`}>
        {title} ({items.length})
      </h3>
      <div className="flex flex-col gap-3">
        {items.map((item, i) => (
          <TriageCard
            key={item.name}
            item={item}
            variant={variant}
            expanded={expandedIdx === i}
            onToggle={() => setExpandedIdx(expandedIdx === i ? null : i)}
          />
        ))}
      </div>
    </section>
  )
}
