'use client'

import type { CompanyMetrics, RoleMetric, TriageItem, DailyChart } from '@/types/monthly-kpi-report'
import EmployeeCard from './EmployeeCard'

interface PulseSectionProps {
  company: CompanyMetrics
  roles: RoleMetric[]
  needsAttention: TriageItem[]
  topPerformers: TriageItem[]
  companyDaily: DailyChart[]
  companyDailyTime: any[]
}

export default function PulseSection({
  company,
  roles,
  needsAttention,
  topPerformers,
  companyDaily,
  companyDailyTime,
}: PulseSectionProps) {
  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="kpi-card">
          <div className="text-sm text-slate-600 font-medium">Needs Attention</div>
          <div className="mt-2 flex items-end justify-between">
            <div>
              <div className="text-3xl font-bold text-tier-monitor">{company.flagged}</div>
              <div className="text-xs text-slate-500 mt-1">{company.flaggedPct}</div>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="text-sm text-slate-600 font-medium">Inactive</div>
          <div className="mt-2 flex items-end justify-between">
            <div>
              <div className="text-3xl font-bold text-slate-600">{company.inactive}</div>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="text-sm text-slate-600 font-medium">Top Performers</div>
          <div className="mt-2 flex items-end justify-between">
            <div>
              <div className="text-3xl font-bold text-tier-on-track">{company.topPerformers}</div>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="text-sm text-slate-600 font-medium">Avg Score</div>
          <div className="mt-2">
            <div className="text-3xl font-bold text-brand-blue-600">{company.avgScore}</div>
            <div className="text-xs text-slate-500 mt-1">{company.avgActiveTime}</div>
          </div>
        </div>
      </div>

      {/* Weekly Trend */}
      <div className="kpi-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Weekly Trend</h3>
        <div className="flex items-end justify-around h-48 gap-4">
          {companyDaily.map(day => (
            <div key={day.day} className="flex-1 flex flex-col items-center justify-end">
              <div
                style={{
                  height: `${(day.score / 100) * 100}%`,
                  backgroundColor: '#1E86D9',
                  borderRadius: '4px 4px 0 0',
                }}
                className="w-full min-h-8"
              />
              <span className="text-xs text-slate-600 mt-2">{day.day}</span>
              <span className="text-sm font-semibold text-slate-900">{day.score}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Roles */}
      <div className="kpi-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">By Role</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {roles.map(role => (
            <div key={role.role} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">{role.role}</p>
                <p className="text-xs text-slate-600">{role.avgTimeLabel}</p>
              </div>
              <p className="text-lg font-bold text-brand-blue-600">{role.avg}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Needs Attention */}
      {needsAttention.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Needs Attention</h3>
          <div className="grid gap-4">
            {needsAttention.map(emp => (
              <EmployeeCard key={emp.name} employee={emp} status="flagged" />
            ))}
          </div>
        </div>
      )}

      {/* Top Performers */}
      {topPerformers.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Top Performers</h3>
          <div className="grid gap-4">
            {topPerformers.map(emp => (
              <EmployeeCard key={emp.name} employee={emp} status="top" />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
