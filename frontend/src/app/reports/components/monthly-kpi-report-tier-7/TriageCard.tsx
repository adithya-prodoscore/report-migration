'use client'

import { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { NeedsAttentionRecord, InactiveRecord, TopPerformerRecord, TriageDailyEntry } from '@/hooks/useMonthlyKpiReportTier7'

type TriageEmployee = NeedsAttentionRecord | InactiveRecord | TopPerformerRecord

interface TriageCardProps {
  employee: TriageEmployee
  cardType: 'attention' | 'inactive' | 'top'
}

function miniBarOption(daily: TriageDailyEntry[], color: string) {
  return {
    textStyle: { fontFamily: 'var(--font-family-primary), sans-serif' },
    tooltip: { trigger: 'axis', confine: true, textStyle: { fontSize: 11 } },
    grid: { left: 0, right: 0, top: 4, bottom: 0, containLabel: false },
    xAxis: { type: 'category' as const, data: daily.map((d) => d.day), show: false },
    yAxis: { type: 'value' as const, show: false },
    series: [{
      type: 'bar' as const,
      data: daily.map((d) => d.score),
      itemStyle: { color, borderRadius: [2, 2, 0, 0] },
      barMaxWidth: 20,
    }],
  }
}

const CARD_CONFIG = {
  attention: {
    borderColor: 'border-l-status-attention',
    badgeColor: 'bg-status-attention-bg text-status-attention',
    chartColor: '#f59e0b',
    label: 'Needs Attention',
  },
  inactive: {
    borderColor: 'border-l-status-inactive',
    badgeColor: 'bg-status-inactive-bg text-status-inactive',
    chartColor: '#94a3b8',
    label: 'Inactive / PTO',
  },
  top: {
    borderColor: 'border-l-status-top',
    badgeColor: 'bg-status-top-bg text-status-top',
    chartColor: '#16a34a',
    label: 'Top Performer',
  },
}

export function TriageCard({ employee, cardType }: TriageCardProps) {
  const [expanded, setExpanded] = useState(false)
  const cfg = CARD_CONFIG[cardType]

  const scoreColor =
    employee.score >= 70
      ? 'bg-kpi-tier-high-pale text-kpi-tier-high'
      : employee.score >= 40
      ? 'bg-kpi-tier-avg-bg text-kpi-tier-avg'
      : 'bg-kpi-tier-critical-pale text-kpi-tier-critical'

  return (
    <div className={`rounded-lg bg-neutral-0 border border-neutral-200 border-l-4 ${cfg.borderColor} shadow-sm p-4`}>
      {/* Header row */}
      <div className="flex items-start gap-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${scoreColor}`}>
          {employee.score}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-semibold text-neutral-900 truncate">{employee.name}</p>
            <span className={`text-xs font-medium rounded-full px-2 py-0.5 ${cfg.badgeColor}`}>
              {cfg.label}
            </span>
          </div>
          <p className="text-xs text-kpi-gray-500 mt-0.5">
            {employee.role}
            {employee.manager && employee.manager !== 'Management' && (
              <span className="text-kpi-gray-400"> · {employee.manager}</span>
            )}
          </p>
        </div>
        <button
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          aria-label={expanded ? 'Collapse employee detail' : 'Expand employee detail'}
          className="shrink-0 text-xs text-kpi-blue-500 hover:text-kpi-blue-700 font-medium"
        >
          {expanded ? 'Less' : 'More'}
        </button>
      </div>

      {/* Compact metrics row */}
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-kpi-gray-500">
        <span>Score: <span className="font-medium text-neutral-800">{employee.score}</span></span>
        <span>Role avg: <span className="font-medium text-neutral-800">{employee.roleAvg}</span></span>
        <span>Gap: <span className={`font-medium ${employee.scoreGap < 0 ? 'text-kpi-tier-critical' : 'text-kpi-tier-high'}`}>{employee.scoreGap >= 0 ? '+' : ''}{employee.scoreGap}</span></span>
        <span>Active: <span className="font-medium text-neutral-800">{employee.activeTime}</span></span>
      </div>

      {/* Inline mini chart */}
      {employee.daily && employee.daily.length > 0 && (
        <div className="mt-3 h-12">
          <ReactECharts
            option={miniBarOption(employee.daily, cfg.chartColor)}
            style={{ height: '48px', width: '100%' }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      )}

      {/* Expanded detail */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-neutral-100 grid grid-cols-2 gap-x-6 gap-y-2 text-xs text-kpi-gray-500">
          {'firstActivity' in employee && (
            <>
              <span>First activity: <span className="font-medium text-neutral-800">{(employee as NeedsAttentionRecord).firstActivity}</span></span>
              <span>Last activity: <span className="font-medium text-neutral-800">{(employee as NeedsAttentionRecord).lastActivity}</span></span>
              <span>% active: <span className="font-medium text-neutral-800">{(employee as NeedsAttentionRecord).pctActive}</span></span>
              <span>Most prod day: <span className="font-medium text-neutral-800">{(employee as NeedsAttentionRecord).mostProductiveDay}</span></span>
            </>
          )}
          {'reason' in employee && (
            <span className="col-span-2 italic text-kpi-gray-400">{(employee as InactiveRecord).reason}</span>
          )}
          <span>Role avg time: <span className="font-medium text-neutral-800">{employee.roleAvgTime}</span></span>
          <span>Time gap: <span className="font-medium text-neutral-800">{typeof employee.timeGap === 'string' ? employee.timeGap : '—'}</span></span>
        </div>
      )}
    </div>
  )
}
