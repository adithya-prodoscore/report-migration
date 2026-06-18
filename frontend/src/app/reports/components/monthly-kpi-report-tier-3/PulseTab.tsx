import { KpiCard } from './KpiCard'
import { DailyTrendChart } from './DailyTrendChart'
import { RoleAvgChart } from './RoleAvgChart'
import { TriageCardList } from './TriageCardList'
import type { MonthlyKpiReportTier3Data } from '@/hooks/useMonthlyKpiReportTier3'

interface PulseTabProps {
  data: MonthlyKpiReportTier3Data
}

export function PulseTab({ data }: PulseTabProps) {
  const { COMPANY, COMPANY_DAILY, ROLES, NEEDS_ATTENTION, INACTIVE, TOP_PERFORMERS } = data

  return (
    <div className="space-y-8">
      {/* KPI Summary Cards */}
      <section>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <KpiCard
            label="Company Score"
            value={COMPANY.avgScore}
            sub={COMPANY.period}
          />
          <KpiCard
            label="Needs Attention"
            value={COMPANY.flagged}
            sub={COMPANY.flaggedPct}
            variant="warning"
          />
          <KpiCard
            label="Most Engaged"
            value={COMPANY.topPerformers}
            variant="success"
          />
          <KpiCard
            label="Inactive / PTO"
            value={COMPANY.inactive}
            sub={`${COMPANY.totalEmployees} total employees`}
            variant="inactive"
          />
        </div>
      </section>

      {/* Company Daily Trend + Avg Active Time */}
      <section>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5">
            <h3 className="text-sm font-semibold text-neutral-700 mb-3">Company Score — Mon–Fri Avg</h3>
            <DailyTrendChart data={COMPANY_DAILY} color="#1E86D9" height={220} showAvgLine />
          </div>
          <div className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5">
            <h3 className="text-sm font-semibold text-neutral-700 mb-3">Avg Score by Role</h3>
            <RoleAvgChart roles={ROLES} height={220} />
          </div>
        </div>
      </section>

      {/* Company stats summary row */}
      <section className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-xs text-neutral-400 uppercase tracking-wide">Avg Active Time</p>
            <p className="text-lg font-bold text-neutral-800 mt-1">{COMPANY.avgActiveTime}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-400 uppercase tracking-wide">Period</p>
            <p className="text-lg font-bold text-neutral-800 mt-1">{COMPANY.period}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-400 uppercase tracking-wide">Employees</p>
            <p className="text-lg font-bold text-neutral-800 mt-1">{COMPANY.totalEmployees}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-400 uppercase tracking-wide">Roles</p>
            <p className="text-lg font-bold text-neutral-800 mt-1">{ROLES.length}</p>
          </div>
        </div>
      </section>

      {/* Triage Lists */}
      <div className="space-y-8">
        <TriageCardList title="Needs Attention" items={NEEDS_ATTENTION} variant="flagged" />
        <TriageCardList title="Most Engaged" items={TOP_PERFORMERS} variant="top" />
        <TriageCardList title="Inactive / PTO" items={INACTIVE} variant="inactive" />
      </div>
    </div>
  )
}
