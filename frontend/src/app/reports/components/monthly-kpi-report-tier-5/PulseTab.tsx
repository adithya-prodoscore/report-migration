import { KpiCardsRow } from './KpiCard'
import { DailyTrendChart } from './DailyTrendChart'
import { RoleAvgChart } from './RoleAvgChart'
import { TriageCardList } from './TriageCardList'
import type { MonthlyKpiReportTier5Data } from '@/hooks/useMonthlyKpiReportTier5'

interface PulseTabProps {
  data: MonthlyKpiReportTier5Data
}

export function PulseTab({ data }: PulseTabProps) {
  return (
    <div className="space-y-8">
      {/* KPI Summary Cards */}
      <section>
        <h2 className="text-base font-bold text-neutral-700 mb-3">Company Overview</h2>
        <KpiCardsRow company={data.COMPANY} />
      </section>

      {/* Daily Trend + Role Avg side-by-side */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5">
          <h3 className="text-sm font-semibold text-neutral-700 mb-4">Company Daily Score Trend</h3>
          <DailyTrendChart data={data.COMPANY_DAILY} color="#1E86D9" />
        </div>
        <div className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5">
          <h3 className="text-sm font-semibold text-neutral-700 mb-4">Average Score by Role</h3>
          <RoleAvgChart roles={data.ROLES} />
        </div>
      </section>

      {/* Employee Triage Cards */}
      <section>
        <h2 className="text-base font-bold text-neutral-700 mb-4">Employee Triage</h2>
        <TriageCardList
          needsAttention={data.NEEDS_ATTENTION}
          inactive={data.INACTIVE}
          topPerformers={data.TOP_PERFORMERS}
        />
      </section>
    </div>
  )
}
