'use client'

import { useState } from 'react'
import { KpiSummaryCards } from './KpiSummaryCards'
import { CompanyTrendChart } from './CompanyTrendChart'
import { RoleBreakdownChart } from './RoleBreakdownChart'
import { TriageCard } from './TriageCard'
import {
  CompanyMeta,
  RoleSummary,
  DayScore,
  DayTime,
  NeedsAttentionRecord,
  InactiveRecord,
  TopPerformerRecord,
} from '@/hooks/useMonthlyKpiReportTier7'

interface PulseTabProps {
  company: CompanyMeta
  roles: RoleSummary[]
  companyDaily: DayScore[]
  companyDailyTime: DayTime[]
  needsAttention: NeedsAttentionRecord[]
  inactive: InactiveRecord[]
  topPerformers: TopPerformerRecord[]
}

export function PulseTab({
  company,
  roles,
  companyDaily,
  companyDailyTime,
  needsAttention,
  inactive,
  topPerformers,
}: PulseTabProps) {
  const [trendMetric, setTrendMetric] = useState<'score' | 'time'>('score')

  return (
    <div className="space-y-8">
      {/* KPI Summary Cards */}
      <KpiSummaryCards company={company} />

      {/* Company trend + role breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Company trend chart */}
        <div className="bg-neutral-0 border border-neutral-200 rounded-lg shadow-sm p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-neutral-800">Company Trend</h3>
            <div className="flex gap-1">
              <button
                onClick={() => setTrendMetric('score')}
                aria-pressed={trendMetric === 'score'}
                className={`text-xs px-3 py-1 rounded-full font-medium border transition-colors ${
                  trendMetric === 'score'
                    ? 'bg-kpi-blue-500 text-neutral-0 border-kpi-blue-500'
                    : 'bg-neutral-0 text-kpi-gray-600 border-neutral-200 hover:border-kpi-blue-400'
                }`}
              >
                Score
              </button>
              <button
                onClick={() => setTrendMetric('time')}
                aria-pressed={trendMetric === 'time'}
                className={`text-xs px-3 py-1 rounded-full font-medium border transition-colors ${
                  trendMetric === 'time'
                    ? 'bg-kpi-blue-500 text-neutral-0 border-kpi-blue-500'
                    : 'bg-neutral-0 text-kpi-gray-600 border-neutral-200 hover:border-kpi-blue-400'
                }`}
              >
                Active Time
              </button>
            </div>
          </div>
          <CompanyTrendChart
            daily={companyDaily}
            dailyTime={companyDailyTime}
            metric={trendMetric}
          />
        </div>

        {/* Role breakdown chart */}
        <div className="bg-neutral-0 border border-neutral-200 rounded-lg shadow-sm p-5">
          <h3 className="text-sm font-semibold text-neutral-800 mb-3">Score by Role</h3>
          <RoleBreakdownChart roles={roles} />
        </div>
      </div>

      {/* Triage sections */}
      {needsAttention.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-status-attention uppercase tracking-wide mb-3">
            Needs Attention ({needsAttention.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {needsAttention.map((emp) => (
              <TriageCard key={emp.name} employee={emp} cardType="attention" />
            ))}
          </div>
        </section>
      )}

      {inactive.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-status-inactive uppercase tracking-wide mb-3">
            Inactive / PTO ({inactive.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {inactive.map((emp) => (
              <TriageCard key={emp.name} employee={emp} cardType="inactive" />
            ))}
          </div>
        </section>
      )}

      {topPerformers.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-status-top uppercase tracking-wide mb-3">
            Top Performers ({topPerformers.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {topPerformers.map((emp) => (
              <TriageCard key={emp.name} employee={emp} cardType="top" />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
