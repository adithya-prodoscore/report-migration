'use client'

import { useState, useMemo } from 'react'
import { WorkforceTrendChart } from './WorkforceTrendChart'
import {
  RoleSummary,
  DayScore,
  MonthlyKpiReportTier7Data,
} from '@/hooks/useMonthlyKpiReportTier7'

type Dimension = 'role' | 'manager' | 'department'

interface WorkforceTabProps {
  roles: RoleSummary[]
  data: MonthlyKpiReportTier7Data
}

const DIM_LABELS: Record<Dimension, string> = {
  role: 'By Role',
  manager: 'By Manager',
  department: 'By Department',
}

function scoreTierClass(score: number): string {
  if (score >= 70) return 'text-kpi-tier-high font-semibold'
  if (score >= 40) return 'text-kpi-tier-avg font-semibold'
  return 'text-kpi-tier-critical font-semibold'
}

export function WorkforceTab({ data }: WorkforceTabProps) {
  const [dim, setDim] = useState<Dimension>('role')
  const [showWM, setShowWM] = useState(false)

  const avgsMap = useMemo(() => {
    if (dim === 'role') return data.ROLE_AVGS
    if (dim === 'manager') return data.MANAGER_AVGS
    return data.DEPARTMENT_AVGS
  }, [dim, data])

  const dailyMap = useMemo(() => {
    if (dim === 'role') return data.ROLE_DAILY
    if (dim === 'manager') return data.MANAGER_DAILY
    return data.DEPARTMENT_DAILY
  }, [dim, data])

  const wmMap = useMemo(() => {
    if (dim === 'role') return data.ROLE_DAILY_WM
    if (dim === 'manager') return data.MANAGER_DAILY_WM
    return data.DEPARTMENT_DAILY_WM
  }, [dim, data])

  const groups = Object.keys(avgsMap)

  return (
    <div className="space-y-6">
      {/* Sub-tab bar */}
      <div className="flex items-center gap-1 border-b border-neutral-200">
        {(['role', 'manager', 'department'] as Dimension[]).map((d) => (
          <button
            key={d}
            onClick={() => setDim(d)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              dim === d
                ? 'border-kpi-blue-500 text-kpi-blue-500'
                : 'border-transparent text-kpi-gray-500 hover:text-neutral-800'
            }`}
          >
            {DIM_LABELS[d]}
          </button>
        ))}

        {/* Work-mode toggle pill */}
        <button
          onClick={() => setShowWM((v) => !v)}
          aria-pressed={showWM}
          className={`ml-auto text-xs px-3 py-1 rounded-full font-medium border transition-colors ${
            showWM
              ? 'bg-mode-office text-neutral-0 border-mode-office'
              : 'bg-neutral-0 text-kpi-gray-600 border-neutral-200 hover:border-mode-office'
          }`}
        >
          Work Mode
        </button>
      </div>

      {/* Group cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {groups.map((group) => {
          const avgs = avgsMap[group] ?? {}
          const daily = (dailyMap[group] ?? []) as DayScore[]
          const wm = (wmMap[group] ?? {}) as Record<string, DayScore[]> | undefined
          const score = parseInt(avgs.score ?? '0', 10)

          return (
            <div
              key={group}
              className="bg-neutral-0 border border-neutral-200 rounded-lg shadow-sm overflow-hidden"
            >
              {/* Group header */}
              <div className="px-4 py-3 border-b border-neutral-100 flex items-center justify-between">
                <p className="text-sm font-semibold text-neutral-900 truncate">{group}</p>
                <span className={`text-lg ${scoreTierClass(score)}`}>{isNaN(score) ? '—' : score}</span>
              </div>

              {/* Trend chart */}
              {daily.length > 0 && (
                <div className="px-2 pt-2">
                  <WorkforceTrendChart
                    groupName={group}
                    daily={daily}
                    wm={wm as { Remote?: DayScore[]; 'In-Office'?: DayScore[] }}
                    showWorkMode={showWM}
                  />
                </div>
              )}

              {/* Key metrics */}
              <div className="px-4 py-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-kpi-gray-500">
                <span>Active time: <span className="font-medium text-neutral-800">{avgs.activeTime ?? '—'}</span></span>
                <span>1st activity: <span className="font-medium text-neutral-800">{avgs.firstActivity ?? '—'}</span></span>
                <span>Int meet: <span className="font-medium text-neutral-800">{avgs.intMeetPct ?? '—'}</span></span>
                <span>Ext meet: <span className="font-medium text-neutral-800">{avgs.extMeetPct ?? '—'}</span></span>
                {showWM && (
                  <>
                    <span>In-Office: <span className="font-medium text-mode-office">{avgs.daysInOffice ?? '—'}</span></span>
                    <span>Remote: <span className="font-medium text-mode-remote">{avgs.daysRemote ?? '—'}</span></span>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
