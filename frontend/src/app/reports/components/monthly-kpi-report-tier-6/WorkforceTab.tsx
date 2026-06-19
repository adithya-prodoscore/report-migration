'use client'
import { useState, useMemo } from 'react'
import { DailyTrendChart } from './DailyTrendChart'
import type { MonthlyKpiReportTier6Data, DailyScore } from '@/hooks/useMonthlyKpiReportTier6'

type Dimension = 'role' | 'manager' | 'department'

const DIMENSION_LABELS: Record<Dimension, string> = {
  role: 'By Role',
  manager: 'By Manager',
  department: 'By Department',
}

const DIMENSION_DAILY_MAP: Record<Dimension, keyof MonthlyKpiReportTier6Data> = {
  role: 'ROLE_DAILY',
  manager: 'MANAGER_DAILY',
  department: 'DEPARTMENT_DAILY',
}

const DIMENSION_AVGS_MAP: Record<Dimension, keyof MonthlyKpiReportTier6Data> = {
  role: 'ROLE_AVGS',
  manager: 'MANAGER_AVGS',
  department: 'DEPARTMENT_AVGS',
}

interface WorkforceTabProps {
  data: MonthlyKpiReportTier6Data
}

export function WorkforceTab({ data }: WorkforceTabProps) {
  const [dim, setDim] = useState<Dimension>('role')
  const [selected, setSelected] = useState<string | null>(null)

  const dailyMap = data[DIMENSION_DAILY_MAP[dim]] as Record<string, DailyScore[]>
  const avgsMap = data[DIMENSION_AVGS_MAP[dim]] as Record<string, Record<string, string>>
  const groups = useMemo(() => Object.keys(dailyMap).sort(), [dailyMap])

  const activeGroup = selected && groups.includes(selected) ? selected : groups[0] ?? null
  const activeSeries = activeGroup ? dailyMap[activeGroup] : []
  const activeAvgs = activeGroup ? avgsMap[activeGroup] : null

  return (
    <div className="space-y-6">
      {/* Sub-tab dimension selector */}
      <div className="flex gap-0 border-b border-neutral-200">
        {(Object.keys(DIMENSION_LABELS) as Dimension[]).map((d) => (
          <button
            key={d}
            onClick={() => { setDim(d); setSelected(null) }}
            className={`px-4 py-2.5 text-sm font-semibold transition-colors border-b-2 ${
              dim === d
                ? 'border-brand-indigo-600 text-brand-indigo-600'
                : 'border-transparent text-neutral-500 hover:text-neutral-800'
            }`}
          >
            {DIMENSION_LABELS[d]}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Group list */}
        <div className="lg:col-span-1">
          <p className="text-xs font-semibold uppercase text-neutral-400 mb-2">Groups</p>
          <ul className="space-y-1">
            {groups.map((g) => (
              <li key={g}>
                <button
                  onClick={() => setSelected(g)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    g === activeGroup
                      ? 'bg-brand-indigo-50 text-brand-indigo-700 font-semibold'
                      : 'text-neutral-700 hover:bg-neutral-100'
                  }`}
                >
                  {g}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Chart + stats */}
        <div className="lg:col-span-3 space-y-5">
          {activeGroup && (
            <>
              <div className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5">
                <h3 className="text-sm font-semibold text-neutral-700 mb-4">
                  Daily Score Trend &mdash; {activeGroup}
                </h3>
                <DailyTrendChart data={activeSeries} color="#4f46e5" title={activeGroup} />
              </div>

              {activeAvgs && (
                <div className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5">
                  <h3 className="text-sm font-semibold text-neutral-700 mb-4">Key Metrics</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                    {[
                      { label: 'Avg Score', key: 'score' },
                      { label: 'Active Time', key: 'activeTime' },
                      { label: 'First Activity', key: 'firstActivity' },
                      { label: 'Last Activity', key: 'lastActivity' },
                      { label: 'Est. Available', key: 'estAvailHours' },
                      { label: '% Active', key: 'pctActive' },
                      { label: 'Int. Meetings', key: 'intMeetPct' },
                      { label: 'Peak Hour', key: 'popMeetTime' },
                    ].map(({ label, key }) => (
                      <div key={key}>
                        <p className="text-xs text-neutral-400 uppercase font-semibold mb-0.5">{label}</p>
                        <p className="font-semibold text-neutral-800">{activeAvgs[key] ?? '-'}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
