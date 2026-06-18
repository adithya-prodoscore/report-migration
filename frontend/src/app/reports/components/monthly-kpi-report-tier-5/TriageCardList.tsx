'use client'
import { useState } from 'react'
import type {
  TriageEmployeeRecord,
  InactiveEmployeeRecord,
  DailyScore,
} from '@/hooks/useMonthlyKpiReportTier5'

function scorePillClass(score: number): string {
  if (score >= 70) return 'bg-kpi-tier-high-pale text-kpi-tier-high'
  if (score >= 40) return 'bg-neutral-100 text-kpi-tier-monitor'
  return 'bg-kpi-tier-critical-pale text-kpi-tier-critical'
}

function MiniBarChart({ daily }: { daily: DailyScore[] }) {
  const max = Math.max(...daily.map((d) => d.score), 1)
  return (
    <div className="flex items-end gap-1 h-8">
      {daily.map((d) => (
        <div key={d.day} className="flex flex-col items-center gap-0.5" style={{ flex: 1 }}>
          <div
            className="w-full rounded-sm bg-brand-indigo-400"
            style={{ height: `${Math.round((d.score / max) * 28)}px` }}
          />
          <span className="text-[9px] text-neutral-400">{d.day.slice(0, 1)}</span>
        </div>
      ))}
    </div>
  )
}

interface TriageCardProps {
  employee: TriageEmployeeRecord
  kind: 'attention' | 'top'
}

function TriageCard({ employee: e, kind }: TriageCardProps) {
  const [expanded, setExpanded] = useState(false)
  const borderColor = kind === 'attention' ? 'border-status-attention' : 'border-status-top'

  return (
    <div className={`rounded-lg border-l-4 ${borderColor} bg-white border border-neutral-200 shadow-xs`}>
      <button
        className="w-full text-left px-4 py-3 flex items-center justify-between gap-4"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className={`text-sm font-bold px-2 py-0.5 rounded ${scorePillClass(e.score)}`}>
            {e.score}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-neutral-900 truncate">{e.name}</p>
            <p className="text-xs text-neutral-500 truncate">
              {e.role} &middot; {e.manager}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div className="hidden sm:flex flex-col items-end text-xs text-neutral-500">
            <span>Active: <b className="text-neutral-800">{e.activeTime}</b></span>
            <span className={e.scoreGap < 0 ? 'text-kpi-tier-critical' : 'text-status-top'}>
              {e.scoreGap >= 0 ? '+' : ''}{e.scoreGap} vs role avg ({e.roleAvg})
            </span>
          </div>
          <span className={`text-neutral-400 transition-transform duration-150 ${expanded ? 'rotate-90' : ''}`}>
            &#9654;
          </span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-neutral-100 mt-0 pt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
          <div>
            <p className="text-neutral-400 uppercase text-[10px] font-semibold mb-1">Active Time</p>
            <p className="font-semibold text-neutral-800">{e.activeTime}</p>
            <p className={`mt-0.5 ${e.timeGap.startsWith('-') ? 'text-kpi-tier-critical' : 'text-status-top'}`}>{e.timeGap} vs {e.roleAvgTime}</p>
          </div>
          <div>
            <p className="text-neutral-400 uppercase text-[10px] font-semibold mb-1">Activity Window</p>
            <p className="font-semibold text-neutral-800">{e.firstActivity} – {e.lastActivity}</p>
            <p className="text-neutral-500 mt-0.5">{e.pctActive} active</p>
          </div>
          <div>
            <p className="text-neutral-400 uppercase text-[10px] font-semibold mb-1">Best / Worst Day</p>
            <p className="font-semibold text-neutral-800">{e.mostProductiveDay}</p>
            <p className="text-neutral-500 mt-0.5">Least: {e.leastProductiveDay}</p>
          </div>
          <div>
            <p className="text-neutral-400 uppercase text-[10px] font-semibold mb-2">Daily Score</p>
            <MiniBarChart daily={e.daily} />
          </div>
        </div>
      )}
    </div>
  )
}

interface InactiveCardProps {
  employee: InactiveEmployeeRecord
}

function InactiveCard({ employee: e }: InactiveCardProps) {
  return (
    <div className="rounded-lg border-l-4 border-status-inactive bg-white border border-neutral-200 shadow-xs">
      <div className="px-4 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-sm font-bold px-2 py-0.5 rounded bg-status-inactive-bg text-status-inactive">
            {e.score}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-neutral-900 truncate">{e.name}</p>
            <p className="text-xs text-neutral-500 truncate">
              {e.role} &middot; {e.manager}
            </p>
          </div>
        </div>
        <p className="hidden sm:block text-xs text-neutral-400 max-w-xs text-right">{e.reason}</p>
      </div>
    </div>
  )
}

interface TriageCardListProps {
  needsAttention: TriageEmployeeRecord[]
  inactive: InactiveEmployeeRecord[]
  topPerformers: TriageEmployeeRecord[]
}

export function TriageCardList({
  needsAttention,
  inactive,
  topPerformers,
}: TriageCardListProps) {
  return (
    <div className="space-y-8">
      {needsAttention.length > 0 && (
        <section>
          <h3 className="text-sm font-bold text-status-attention uppercase tracking-wide mb-3">
            Needs Attention ({needsAttention.length})
          </h3>
          <div className="space-y-2">
            {needsAttention.map((e) => (
              <TriageCard key={e.name} employee={e} kind="attention" />
            ))}
          </div>
        </section>
      )}

      {inactive.length > 0 && (
        <section>
          <h3 className="text-sm font-bold text-status-inactive uppercase tracking-wide mb-3">
            Inactive / PTO ({inactive.length})
          </h3>
          <div className="space-y-2">
            {inactive.map((e) => (
              <InactiveCard key={e.name} employee={e} />
            ))}
          </div>
        </section>
      )}

      {topPerformers.length > 0 && (
        <section>
          <h3 className="text-sm font-bold text-status-top uppercase tracking-wide mb-3">
            Most Engaged ({topPerformers.length})
          </h3>
          <div className="space-y-2">
            {topPerformers.map((e) => (
              <TriageCard key={e.name} employee={e} kind="top" />
            ))}
          </div>
        </section>
      )}

      {needsAttention.length === 0 && inactive.length === 0 && topPerformers.length === 0 && (
        <p className="text-sm text-neutral-400 text-center py-8">No triage data available for this period.</p>
      )}
    </div>
  )
}
