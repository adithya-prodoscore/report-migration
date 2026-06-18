'use client'

import { useState, useMemo } from 'react'
import type { MonthlyKpiReportTier2Response } from '@/types/monthly-kpi-report-tier-2'
import { EmployeeCardTier2 } from './EmployeeCardTier2'

interface PulseSectionTier2Props {
  data: MonthlyKpiReportTier2Response
}

type KpiTab = 'attention' | 'inactive' | 'top'

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 70 ? 'bg-tier-high' : score >= 40 ? 'bg-tier-avg' : 'bg-tier-low'
  return (
    <div className="w-full h-2 bg-neutral-100 rounded-full overflow-hidden">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(score, 100)}%` }} />
    </div>
  )
}

function KpiSummaryCard({
  label,
  value,
  subValue,
  color,
  active,
  onClick,
}: {
  label: string
  value: string | number
  subValue?: string
  color: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 rounded-xl border p-4 text-left transition-all ${
        active
          ? 'border-brand-indigo-500 bg-brand-indigo-50 shadow-sm'
          : 'border-neutral-200 bg-white hover:border-neutral-300 hover:shadow-xs'
      }`}
      aria-pressed={active}
    >
      <div className={`text-3xl font-extrabold tracking-tight ${color}`}>{value}</div>
      <div className="mt-1 text-sm font-medium text-neutral-700">{label}</div>
      {subValue && <div className="text-xs text-neutral-400 mt-0.5">{subValue}</div>}
    </button>
  )
}

function CompanyTrendChart({ data }: { data: { day: string; score: number }[] }) {
  if (!data || data.length === 0) return null
  const max = Math.max(...data.map((d) => d.score), 1)
  return (
    <div className="flex items-end gap-3 h-24">
      {data.map((d) => {
        const pct = (d.score / max) * 100
        const barColor =
          d.score >= 70 ? 'bg-tier-high' : d.score >= 40 ? 'bg-tier-avg' : 'bg-tier-low'
        return (
          <div key={d.day} className="flex flex-col items-center gap-1 flex-1">
            <span className="text-xs font-semibold text-neutral-700">{d.score}</span>
            <div className="w-full rounded-t-sm" style={{ height: `${pct}%`, minHeight: 4 }}>
              <div className={`w-full h-full rounded-t-sm ${barColor}`} />
            </div>
            <span className="text-xs text-neutral-500">{d.day}</span>
          </div>
        )
      })}
    </div>
  )
}

function RoleScoreList({ roles }: { roles: MonthlyKpiReportTier2Response['ROLES'] }) {
  if (!roles || roles.length === 0) return <p className="text-sm text-neutral-400">No role data.</p>
  return (
    <div className="space-y-2">
      {roles.map((r) => (
        <div key={r.role} className="flex items-center gap-3">
          <div className="w-36 text-sm text-neutral-700 truncate">{r.role}</div>
          <div className="flex-1">
            <ScoreBar score={r.avg} />
          </div>
          <div className="w-8 text-sm font-semibold text-neutral-900 text-right">{r.avg}</div>
          <div className="w-20 text-xs text-neutral-500 text-right">{r.avgTimeLabel}</div>
        </div>
      ))}
    </div>
  )
}

export function PulseSectionTier2({ data }: PulseSectionTier2Props) {
  const [activeTab, setActiveTab] = useState<KpiTab>('attention')
  const company = data.COMPANY

  const triageList = useMemo(() => {
    if (activeTab === 'attention') return data.NEEDS_ATTENTION
    if (activeTab === 'inactive') return data.INACTIVE
    return data.TOP_PERFORMERS
  }, [activeTab, data])

  return (
    <section className="space-y-8">
      {/* KPI Summary Cards */}
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">Company Overview</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="col-span-2 sm:col-span-1 rounded-xl border border-neutral-200 bg-white p-4">
            <div className="text-3xl font-extrabold text-neutral-900">{company.avgScore}</div>
            <div className="text-sm font-medium text-neutral-700 mt-1">Avg Score</div>
            <div className="text-xs text-neutral-400 mt-0.5">{company.period}</div>
            <ScoreBar score={company.avgScore} />
          </div>
          <KpiSummaryCard
            label="Needs Attention"
            value={company.flagged}
            subValue={company.flaggedPct}
            color="text-status-attention"
            active={activeTab === 'attention'}
            onClick={() => setActiveTab('attention')}
          />
          <KpiSummaryCard
            label="Inactive / PTO"
            value={company.inactive}
            color="text-status-inactive"
            active={activeTab === 'inactive'}
            onClick={() => setActiveTab('inactive')}
          />
          <KpiSummaryCard
            label="Top Performers"
            value={company.topPerformers}
            color="text-status-top"
            active={activeTab === 'top'}
            onClick={() => setActiveTab('top')}
          />
        </div>
        <div className="mt-3 flex items-center gap-4 text-sm text-neutral-500">
          <span>{company.totalEmployees} employees</span>
          <span>Avg active time: <span className="font-medium text-neutral-700">{company.avgActiveTime}</span></span>
        </div>
      </div>

      {/* Daily Trend */}
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">Company Daily Trend</h2>
        <div className="bg-white rounded-xl border border-neutral-200 p-5 shadow-xs">
          <CompanyTrendChart data={data.COMPANY_DAILY} />
        </div>
      </div>

      {/* Average Score by Role */}
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">Average Score by Role</h2>
        <div className="bg-white rounded-xl border border-neutral-200 p-5 shadow-xs">
          <RoleScoreList roles={data.ROLES} />
        </div>
      </div>

      {/* Triage Employee Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-neutral-900">
            {activeTab === 'attention' && `Needs Attention (${data.NEEDS_ATTENTION.length})`}
            {activeTab === 'inactive' && `Inactive / PTO (${data.INACTIVE.length})`}
            {activeTab === 'top' && `Top Performers (${data.TOP_PERFORMERS.length})`}
          </h2>
        </div>
        {triageList.length === 0 ? (
          <div className="bg-white rounded-xl border border-neutral-200 p-8 text-center text-neutral-400 text-sm">
            No employees in this category.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {triageList.map((emp) => (
              <EmployeeCardTier2 key={emp.name} employee={emp} type={activeTab} />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
