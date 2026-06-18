'use client'
// WorkforceTab — Workforce tab: group-by selector (role/manager/department),
// work-mode toggle (Remote / In-Office), per-group daily trend charts,
// and group-level metrics summary.
// HTML source: Workforce tab section
// Interactions: group-by selector, work-mode toggle pill, per-group expand

import { useState, useMemo } from 'react'
import { DailyTrendChart } from './DailyTrendChart'
import type { MonthlyKpiReportTier4Data } from '@/hooks/useMonthlyKpiReportTier4'

type Dimension = 'role' | 'manager' | 'department'
type WorkMode = 'score' | 'remote' | 'office'

const DIMENSION_LABELS: Record<Dimension, string> = {
  role: 'By Role',
  manager: 'By Manager',
  department: 'By Department',
}

const DIMENSION_KEYS: Record<Dimension, keyof MonthlyKpiReportTier4Data> = {
  role: 'ROLE_DAILY',
  manager: 'MANAGER_DAILY',
  department: 'DEPARTMENT_DAILY',
}

const WM_DIMENSION_KEYS: Record<Dimension, keyof MonthlyKpiReportTier4Data> = {
  role: 'ROLE_DAILY_WM',
  manager: 'MANAGER_DAILY_WM',
  department: 'DEPARTMENT_DAILY_WM',
}

const AVGS_KEYS: Record<Dimension, keyof MonthlyKpiReportTier4Data> = {
  role: 'ROLE_AVGS',
  manager: 'MANAGER_AVGS',
  department: 'DEPARTMENT_AVGS',
}

interface WorkforceTabProps {
  data: MonthlyKpiReportTier4Data
}

export function WorkforceTab({ data }: WorkforceTabProps) {
  const [dimension, setDimension] = useState<Dimension>(
    (data.CONFIG.default_workforce_view as Dimension) ?? 'role',
  )
  const [workMode, setWorkMode] = useState<WorkMode>('score')

  const dailyKey = DIMENSION_KEYS[dimension]
  const wmKey = WM_DIMENSION_KEYS[dimension]
  const avgsKey = AVGS_KEYS[dimension]

  const dailyData = data[dailyKey] as Record<string, { day: string; score: number }[]>
  const wmData = data[wmKey] as Record<string, Record<string, { day: string; score: number }[]>>
  const avgsData = data[avgsKey] as Record<string, Record<string, string>>

  const groups = useMemo(() => Object.keys(dailyData ?? {}).sort(), [dailyData])

  function getChartData(group: string) {
    if (workMode === 'remote') {
      return wmData?.[group]?.Remote ?? dailyData?.[group] ?? []
    }
    if (workMode === 'office') {
      return wmData?.[group]?.['In-Office'] ?? dailyData?.[group] ?? []
    }
    return dailyData?.[group] ?? []
  }

  function getColor(mode: WorkMode) {
    if (mode === 'remote') return '#0891b2'
    if (mode === 'office') return '#7c3aed'
    return '#1E86D9'
  }

  return (
    <div className="space-y-6">
      {/* Controls row */}
      <div className="flex flex-wrap gap-3 items-center justify-between">
        {/* Group-by selector */}
        <div className="flex gap-1 bg-neutral-100 rounded-lg p-1">
          {(['role', 'manager', 'department'] as Dimension[]).filter((d) =>
            data.CONFIG.workforce_dimensions?.includes(d),
          ).map((d) => (
            <button
              key={d}
              onClick={() => setDimension(d)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                dimension === d
                  ? 'bg-white text-brand-indigo-600 shadow-xs'
                  : 'text-neutral-500 hover:text-neutral-700'
              }`}
            >
              {DIMENSION_LABELS[d]}
            </button>
          ))}
        </div>

        {/* Work-mode toggle pills */}
        <div className="flex gap-1">
          {(['score', 'remote', 'office'] as WorkMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setWorkMode(m)}
              aria-pressed={workMode === m}
              className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors ${
                workMode === m
                  ? m === 'score'
                    ? 'bg-kpi-blue-500 text-white border-kpi-blue-500'
                    : m === 'remote'
                      ? 'bg-mode-remote text-white border-mode-remote'
                      : 'bg-mode-office text-white border-mode-office'
                  : 'bg-white text-neutral-500 border-neutral-200 hover:border-neutral-400'
              }`}
            >
              {m === 'score' ? 'Score' : m === 'remote' ? 'Remote' : 'In-Office'}
            </button>
          ))}
        </div>
      </div>

      {/* Group cards */}
      {groups.length === 0 && (
        <p className="text-sm text-neutral-400 text-center py-12">No data available.</p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {groups.map((group) => {
          const avgs = avgsData?.[group]
          const chartData = getChartData(group)
          const color = getColor(workMode)

          return (
            <div
              key={group}
              className="bg-white rounded-xl border border-neutral-200 shadow-xs p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-neutral-800 truncate">{group}</h3>
                {avgs?.score && (
                  <span
                    className={`text-sm font-extrabold px-2.5 py-0.5 rounded-full ${
                      Number(avgs.score) >= 70
                        ? 'bg-tier-high-bg text-tier-high'
                        : Number(avgs.score) >= 40
                          ? 'bg-tier-avg-bg text-tier-avg'
                          : 'bg-tier-low-bg text-tier-low'
                    }`}
                  >
                    {avgs.score}
                  </span>
                )}
              </div>

              {/* Mini chart */}
              {chartData.length > 0 && (
                <DailyTrendChart data={chartData} title={group} color={color} height={160} />
              )}

              {/* Key metrics row */}
              {avgs && (
                <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-neutral-100 text-xs">
                  <div>
                    <p className="text-neutral-400 uppercase font-semibold tracking-wide">Active Time</p>
                    <p className="text-neutral-800 font-semibold mt-0.5">{avgs.activeTime ?? '-'}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 uppercase font-semibold tracking-wide">First Activity</p>
                    <p className="text-neutral-800 font-semibold mt-0.5">{avgs.firstActivity ?? '-'}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 uppercase font-semibold tracking-wide">Last Activity</p>
                    <p className="text-neutral-800 font-semibold mt-0.5">{avgs.lastActivity ?? '-'}</p>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
