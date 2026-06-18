// PulseTab — Pulse tab content: KPI summary cards, daily trend chart,
// role average chart, and triage employee cards.
// HTML source: Pulse tab section
// Interactions: triage card expand/collapse (handled inside TriageCardList)

import { KpiCard } from './KpiCard'
import { DailyTrendChart } from './DailyTrendChart'
import { RoleAvgChart } from './RoleAvgChart'
import { TriageCardList } from './TriageCardList'
import type { MonthlyKpiReportTier4Data } from '@/hooks/useMonthlyKpiReportTier4'

interface PulseTabProps {
  data: MonthlyKpiReportTier4Data
}

export function PulseTab({ data }: PulseTabProps) {
  const { COMPANY, ROLES, COMPANY_DAILY, NEEDS_ATTENTION, INACTIVE, TOP_PERFORMERS } = data

  return (
    <div className="space-y-8">
      {/* KPI Summary Cards */}
      <section>
        <h2 className="text-sm font-extrabold text-neutral-500 uppercase tracking-wide mb-4">
          Company Overview
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <KpiCard
            label="Avg Score"
            value={COMPANY.avgScore}
            subLabel={`${COMPANY.totalEmployees} employees`}
          />
          <KpiCard
            label="Avg Active Time"
            value={COMPANY.avgActiveTime}
            subLabel={`${COMPANY.period}`}
          />
          <KpiCard
            label="Needs Attention"
            value={COMPANY.flagged}
            subLabel={COMPANY.flaggedPct}
            variant="attention"
          />
          <KpiCard
            label="Inactive / PTO"
            value={COMPANY.inactive}
            subLabel="Verification needed"
            variant="inactive"
          />
        </div>
      </section>

      {/* Company daily trend chart */}
      <section>
        <h2 className="text-sm font-extrabold text-neutral-500 uppercase tracking-wide mb-3">
          Company Daily Trend
        </h2>
        <div className="bg-white rounded-xl border border-neutral-200 p-4 shadow-xs">
          <DailyTrendChart data={COMPANY_DAILY} title="Company Avg" color="#1E86D9" />
        </div>
      </section>

      {/* Role average chart */}
      {ROLES.length > 0 && (
        <section>
          <h2 className="text-sm font-extrabold text-neutral-500 uppercase tracking-wide mb-3">
            Avg Score by Role
          </h2>
          <div className="bg-white rounded-xl border border-neutral-200 p-4 shadow-xs">
            <RoleAvgChart roles={ROLES} height={Math.max(200, ROLES.length * 36)} />
          </div>
        </section>
      )}

      {/* Triage employee cards */}
      <section>
        <h2 className="text-sm font-extrabold text-neutral-500 uppercase tracking-wide mb-4">
          Triage Summary
        </h2>
        <TriageCardList
          needsAttention={NEEDS_ATTENTION}
          inactive={INACTIVE}
          topPerformers={TOP_PERFORMERS}
        />
      </section>
    </div>
  )
}
