'use client'

import { useState, useMemo } from 'react'
import type { EmployeeRecordT1 } from '@/app/hooks/useMonthlyKpiReportTier1'

interface CalloutSectionProps {
  employees: EmployeeRecordT1[]
}

type BucketKey = 'needs-attention' | 'inactive' | 'most-engaged'

const BUCKET_CONFIG: Record<BucketKey, { label: string; iconClass: string; chipClass: string; dotColor: string }> = {
  'needs-attention': { label: 'Needs Attention', iconClass: 'bg-kpi-red-50 text-kpi-red-500',    chipClass: 'bg-kpi-red-50 text-kpi-red-700',    dotColor: '#F1433C' },
  'inactive':        { label: 'Inactive',        iconClass: 'bg-kpi-yellow-50 text-kpi-yellow-700', chipClass: 'bg-kpi-yellow-50 text-kpi-yellow-700', dotColor: '#E4D20E' },
  'most-engaged':    { label: 'Most Engaged',    iconClass: 'bg-kpi-blue-50 text-kpi-blue-500',   chipClass: 'bg-kpi-blue-50 text-kpi-blue-700',   dotColor: '#1E86D9' },
}

function scoreTier(score: number): 'critical' | 'monitor' | 'high' {
  if (score < 40) return 'critical'
  if (score < 70) return 'monitor'
  return 'high'
}

const TIER_CARD: Record<string, string> = { critical: 'border-l-kpi-tier-critical', monitor: 'border-l-kpi-tier-monitor', high: 'border-l-kpi-tier-high' }
const TIER_SCORE_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-kpi-red-50',  text: 'text-kpi-tier-critical', border: 'border-kpi-red-100' },
  monitor:  { bg: 'bg-kpi-gray-50', text: 'text-kpi-gray-700',      border: 'border-kpi-gray-100' },
  high:     { bg: 'bg-kpi-blue-50', text: 'text-kpi-blue-700',      border: 'border-kpi-blue-100' },
}

function SparklineInline({ trendCy, trendColor }: { trendCy: number[]; trendColor: string }) {
  if (trendCy.length === 0) return null
  const W = 100; const H = 32
  const mn = Math.min(...trendCy); const mx = Math.max(...trendCy)
  const range = mx - mn || 1
  const xs = trendCy.map((_, i) => (i / Math.max(trendCy.length - 1, 1)) * W)
  const ys = trendCy.map(v => H - 4 - ((v - mn) / range) * (H - 8))
  const d = xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(' ')
  const color = trendColor.includes('red') ? '#F1433C' : '#1E86D9'
  return <svg width={W} height={H} aria-hidden="true" className="flex-shrink-0"><path d={d} fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" /></svg>
}

function getReasonChips(emp: EmployeeRecordT1): { label: string; cls: string }[] {
  if (emp.status === 'inactive') return [
    { label: `Score ${emp.score}`, cls: 'bg-kpi-yellow-50 text-kpi-yellow-700' },
    { label: emp.activeTime, cls: 'bg-kpi-yellow-50 text-kpi-yellow-700' },
  ]
  if (emp.status === 'needs-attention') {
    const d = parseInt(emp.delta)
    return [
      { label: `${emp.delta} vs role`, cls: 'bg-kpi-red-50 text-kpi-red-700' },
      { label: emp.activeTime, cls: d < -10 ? 'bg-kpi-red-50 text-kpi-red-700' : 'bg-kpi-gray-50 text-kpi-gray-700' },
      ...emp.metrics.filter(m => (m.section === 'TECH MODULES' || m.section === 'MEETINGS') && m.roleAvg !== '—' && m.value !== '—').slice(0, 2)
        .map(m => ({ label: `${m.label}: ${m.value} (avg ${m.roleAvg})`, cls: 'bg-kpi-red-50 text-kpi-red-700' })),
    ]
  }
  if (emp.status === 'most-engaged') return [
    { label: `${emp.delta} vs role`, cls: 'bg-kpi-blue-50 text-kpi-blue-700' },
    { label: emp.activeTime, cls: 'bg-kpi-blue-50 text-kpi-blue-700' },
  ]
  return []
}

export function CalloutSection({ employees }: CalloutSectionProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean | undefined>>({})
  const buckets = useMemo(() => {
    const res: Partial<Record<BucketKey, EmployeeRecordT1[]>> = {}
    for (const key of ['needs-attention', 'inactive', 'most-engaged'] as BucketKey[]) {
      const list = employees.filter(e => e.status === key)
      if (list.length > 0) res[key] = list
    }
    return res
  }, [employees])

  if (Object.keys(buckets).length === 0) {
    return (
      <section aria-label="Called-out employees" className="mb-6">
        <div className="border border-dashed border-kpi-gray-200 rounded-xl p-10 text-center bg-kpi-white">
          <p className="text-base font-semibold text-kpi-gray-800 mb-1">No flagged employees</p>
          <p className="text-sm text-kpi-gray-500">All employees are on track for this period.</p>
        </div>
      </section>
    )
  }

  return (
    <section aria-label="Called-out employees" className="mb-6">
      {(Object.entries(buckets) as [BucketKey, EmployeeRecordT1[]][]).map(([key, list]) => {
        const cfg = BUCKET_CONFIG[key]
        const isCollapsed = expanded[key] === false
        return (
          <div key={key} className="mb-6 last:mb-0">
            <div className="flex items-center gap-2.5 mb-3 px-1">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${cfg.iconClass}`}>
                <span className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: cfg.dotColor }} />
              </div>
              <span className="text-sm font-bold text-kpi-gray-950">{cfg.label}</span>
              <span className="text-xs text-kpi-gray-500 font-medium">{list.length} {list.length === 1 ? 'person' : 'people'}</span>
              <button type="button" className="ml-auto text-xs text-kpi-gray-400 hover:text-kpi-gray-700 font-medium" onClick={() => setExpanded(p => ({ ...p, [key]: isCollapsed ? undefined : false }))} aria-expanded={!isCollapsed}>
                {isCollapsed ? 'Show' : 'Hide'}
              </button>
            </div>
            {!isCollapsed && (
              <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))' }}>
                {list.map(emp => {
                  const tier = scoreTier(emp.score)
                  const ts = TIER_SCORE_STYLE[tier]
                  const chips = getReasonChips(emp)
                  return (
                    <div key={emp.id} className={`bg-kpi-white border border-kpi-gray-100 border-l-[3px] ${TIER_CARD[tier]} rounded-[10px] p-3.5 flex items-center gap-3.5 shadow-shadow-xs hover:shadow-shadow-sm transition-shadow`}>
                      <div className={`w-11 h-11 rounded-full flex-shrink-0 flex items-center justify-center font-bold text-[15px] border ${ts.bg} ${ts.text} ${ts.border}`}>{emp.score}</div>
                      <div className="flex-1 min-w-0 flex flex-col gap-1.5">
                        <div className="flex items-baseline flex-wrap gap-1.5">
                          <span className="text-sm font-bold text-kpi-gray-950">{emp.name}</span>
                          <span className="text-xs text-kpi-gray-500 font-medium">{emp.role} · {emp.dept}</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {chips.map((chip, ci) => <span key={ci} className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${chip.cls}`}>{chip.label}</span>)}
                        </div>
                      </div>
                      <SparklineInline trendCy={emp.trendCy} trendColor={emp.trendColor} />
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </section>
  )
}
