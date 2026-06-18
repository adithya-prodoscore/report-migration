'use client'

import { useState, useMemo } from 'react'
import { DailyTrendChart } from './DailyTrendChart'
import type { MonthlyKpiReportTier3Data, DailyScore } from '@/hooks/useMonthlyKpiReportTier3'

type DimensionKey = 'role' | 'manager' | 'department'
type WorkModeKey = 'all' | 'Remote' | 'In-Office'

interface WorkforceTabProps {
  data: MonthlyKpiReportTier3Data
}

const DIMENSIONS: { key: DimensionKey; label: string }[] = [
  { key: 'role', label: 'By Role' },
  { key: 'manager', label: 'By Manager' },
  { key: 'department', label: 'By Department' },
]

const WORK_MODES: { key: WorkModeKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'Remote', label: 'Remote' },
  { key: 'In-Office', label: 'In-Office' },
]

function getAvgDailyData(
  daily: Record<string, DailyScore[]>,
  dailyWm: Record<string, Record<string, DailyScore[]>>,
  groupName: string,
  workMode: WorkModeKey,
): DailyScore[] {
  if (workMode === 'all') return daily[groupName] ?? []
  return dailyWm[groupName]?.[workMode] ?? []
}

function AvgsGrid({ avgs }: { avgs: Record<string, string> }) {
  const COLS = [
    ['Score', 'score'],
    ['Active Time', 'activeTime'],
    ['First Activity', 'firstActivity'],
    ['Last Activity', 'lastActivity'],
    ['Est. Available', 'estAvailHours'],
    ['% Active', 'pctActive'],
    ['1st Half', 'pct1stHalf'],
    ['2nd Half', 'pct2ndHalf'],
    ['Mon', 'mon'],
    ['Tue', 'tue'],
    ['Wed', 'wed'],
    ['Thu', 'thu'],
    ['Fri', 'fri'],
    ['Int. Meet %', 'intMeetPct'],
    ['Ext. Meet %', 'extMeetPct'],
    ['Office Days', 'daysInOffice'],
    ['Remote Days', 'daysRemote'],
  ] as const

  return (
    <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {COLS.map(([label, key]) => (
        <div key={key} className="bg-neutral-50 rounded-lg px-3 py-2">
          <p className="text-xs text-neutral-400 truncate">{label}</p>
          <p className="text-sm font-semibold text-neutral-800">{avgs[key] ?? '—'}</p>
        </div>
      ))}
    </div>
  )
}

function GroupCard({
  name,
  avgs,
  daily,
  workMode,
}: {
  name: string
  avgs: Record<string, string>
  daily: DailyScore[]
  workMode: WorkModeKey
}) {
  const [expanded, setExpanded] = useState(false)
  const score = avgs['score'] ?? '—'

  return (
    <div className="bg-white rounded-xl border border-neutral-200 shadow-xs overflow-hidden">
      <button
        className="w-full text-left px-5 py-4 flex items-center justify-between"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-kpi-blue-50 flex items-center justify-center text-sm font-bold text-kpi-blue-600">
            {score}
          </div>
          <span className="font-semibold text-neutral-900">{name}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-neutral-500">{avgs['activeTime'] ?? '—'}</span>
          <svg
            className={`w-4 h-4 text-neutral-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 border-t border-neutral-100">
          {daily.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wide mb-2">
                Daily Trend — {workMode === 'all' ? 'All' : workMode}
              </p>
              <DailyTrendChart data={daily} color="#1E86D9" height={180} />
            </div>
          )}
          <AvgsGrid avgs={avgs} />
        </div>
      )}
    </div>
  )
}

export function WorkforceTab({ data }: WorkforceTabProps) {
  const [dimension, setDimension] = useState<DimensionKey>('role')
  const [workMode, setWorkMode] = useState<WorkModeKey>('all')

  const { avgsMaps, dailyMaps, dailyWmMaps } = useMemo(() => {
    return {
      avgsMaps: {
        role: data.ROLE_AVGS,
        manager: data.MANAGER_AVGS,
        department: data.DEPARTMENT_AVGS,
      },
      dailyMaps: {
        role: data.ROLE_DAILY,
        manager: data.MANAGER_DAILY,
        department: data.DEPARTMENT_DAILY,
      },
      dailyWmMaps: {
        role: data.ROLE_DAILY_WM,
        manager: data.MANAGER_DAILY_WM,
        department: data.DEPARTMENT_DAILY_WM,
      },
    }
  }, [data])

  const currentAvgs = avgsMaps[dimension]
  const currentDaily = dailyMaps[dimension]
  const currentWm = dailyWmMaps[dimension]
  const groups = Object.keys(currentAvgs).sort()

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap gap-4 items-center">
        {/* Dimension tabs */}
        <div className="flex rounded-lg border border-neutral-200 overflow-hidden">
          {DIMENSIONS.map((d) => (
            <button
              key={d.key}
              onClick={() => setDimension(d.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                dimension === d.key
                  ? 'bg-brand-indigo-600 text-white'
                  : 'bg-white text-neutral-600 hover:bg-neutral-50'
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>

        {/* Work mode pills */}
        <div className="flex gap-2">
          {WORK_MODES.map((m) => (
            <button
              key={m.key}
              onClick={() => setWorkMode(m.key)}
              aria-pressed={workMode === m.key}
              className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors ${
                workMode === m.key
                  ? 'bg-mode-office text-white border-mode-office'
                  : 'bg-white text-neutral-600 border-neutral-200 hover:border-mode-office hover:text-mode-office'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Group cards */}
      <div className="flex flex-col gap-4">
        {groups.map((groupName) => (
          <GroupCard
            key={groupName}
            name={groupName}
            avgs={currentAvgs[groupName] ?? {}}
            daily={getAvgDailyData(currentDaily, currentWm, groupName, workMode)}
            workMode={workMode}
          />
        ))}
      </div>
    </div>
  )
}
