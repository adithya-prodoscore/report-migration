'use client'

import { useState, useMemo } from 'react'
import type { MonthlyKpiReportTier2Response, DailyChart } from '@/types/monthly-kpi-report-tier-2'

interface WorkforceSectionTier2Props {
  data: MonthlyKpiReportTier2Response
}

type GroupDimension = 'role' | 'manager' | 'department'
type WorkMode = 'all' | 'In-Office' | 'Remote'

const WD_ABBR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

function GroupTrendChart({ data }: { data: DailyChart[] }) {
  if (!data || data.length === 0) return null
  const max = Math.max(...data.map((d) => d.score), 1)
  return (
    <div className="flex items-end gap-2 h-16 mt-1">
      {data.map((d) => {
        const pct = max > 0 ? (d.score / max) * 100 : 0
        const color =
          d.score >= 70 ? 'bg-tier-high' : d.score >= 40 ? 'bg-tier-avg' : 'bg-tier-low'
        return (
          <div key={d.day} className="flex flex-col items-center gap-0.5 flex-1">
            <span className="text-xs text-neutral-600">{d.score}</span>
            <div className={`w-full rounded-t-sm ${color}`} style={{ height: `${Math.max(pct, 6)}%` }} />
            <span className="text-xs text-neutral-400">{d.day[0]}</span>
          </div>
        )
      })}
    </div>
  )
}

function WorkModeCharts({
  wmData,
}: {
  wmData: Record<string, DailyChart[]>
}) {
  if (!wmData || Object.keys(wmData).length === 0) return null
  return (
    <div className="grid grid-cols-2 gap-3 mt-2">
      {Object.entries(wmData).map(([mode, days]) => (
        <div key={mode} className="bg-neutral-50 rounded-lg p-2">
          <div className="text-xs font-medium text-neutral-500 mb-1">
            {mode === 'In-Office' ? '🏢 In-Office' : '🏠 Remote'}
          </div>
          <GroupTrendChart data={days} />
        </div>
      ))}
    </div>
  )
}

export function WorkforceSectionTier2({ data }: WorkforceSectionTier2Props) {
  const [dimension, setDimension] = useState<GroupDimension>('role')
  const [workMode, setWorkMode] = useState<WorkMode>('all')
  const [search, setSearch] = useState('')

  const groupData = useMemo(() => {
    if (dimension === 'role') return { daily: data.ROLE_DAILY, avgs: data.ROLE_AVGS, wm: data.ROLE_DAILY_WM }
    if (dimension === 'manager') return { daily: data.MANAGER_DAILY, avgs: data.MANAGER_AVGS, wm: data.MANAGER_DAILY_WM }
    return { daily: data.DEPARTMENT_DAILY, avgs: data.DEPARTMENT_AVGS, wm: data.DEPARTMENT_DAILY_WM }
  }, [dimension, data])

  const groupNames = useMemo(() => {
    const names = Object.keys(groupData.daily || {})
    return search ? names.filter((n) => n.toLowerCase().includes(search.toLowerCase())) : names
  }, [groupData, search])

  const dimensionLabel = dimension === 'role' ? 'Role' : dimension === 'manager' ? 'Manager' : 'Department'

  return (
    <section className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 bg-neutral-100 rounded-lg p-1">
          {(['role', 'manager', 'department'] as GroupDimension[]).map((d) => (
            <button
              key={d}
              onClick={() => setDimension(d)}
              className={`px-3 py-1.5 text-sm rounded-md transition-all capitalize ${
                dimension === d
                  ? 'bg-white text-neutral-900 font-semibold shadow-xs'
                  : 'text-neutral-500 hover:text-neutral-700'
              }`}
              aria-pressed={dimension === d}
            >
              {d}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1 bg-neutral-100 rounded-lg p-1">
          {(['all', 'In-Office', 'Remote'] as WorkMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setWorkMode(m)}
              className={`px-3 py-1.5 text-sm rounded-md transition-all ${
                workMode === m
                  ? 'bg-white text-neutral-900 font-semibold shadow-xs'
                  : 'text-neutral-500 hover:text-neutral-700'
              }`}
              aria-pressed={workMode === m}
            >
              {m === 'all' ? 'All' : m === 'In-Office' ? '🏢 Office' : '🏠 Remote'}
            </button>
          ))}
        </div>

        <input
          type="search"
          placeholder={`Filter ${dimensionLabel}...`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-1.5 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-indigo-500 w-48"
          aria-label={`Filter by ${dimensionLabel}`}
        />
      </div>

      {/* Group Cards */}
      {groupNames.length === 0 ? (
        <div className="text-sm text-neutral-400 text-center py-8">No groups match your filter.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {groupNames.map((group) => {
            const avgs = groupData.avgs?.[group]
            const daily = workMode === 'all'
              ? groupData.daily?.[group]
              : groupData.wm?.[group]?.[workMode]
            const wmCharts = groupData.wm?.[group]

            return (
              <div
                key={group}
                className="bg-white rounded-xl border border-neutral-200 shadow-xs p-4"
              >
                {/* Group header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="font-semibold text-neutral-900 truncate">{group}</div>
                  {avgs?.score && (
                    <span className={`text-lg font-bold ${
                      Number(avgs.score) >= 70
                        ? 'text-tier-high'
                        : Number(avgs.score) >= 40
                        ? 'text-tier-avg'
                        : 'text-tier-low'
                    }`}>
                      {avgs.score}
                    </span>
                  )}
                </div>

                {/* Daily trend for this group */}
                {daily && daily.length > 0 && (
                  <GroupTrendChart data={daily} />
                )}

                {/* Work mode breakdown */}
                {workMode === 'all' && wmCharts && (
                  <WorkModeCharts wmData={wmCharts} />
                )}

                {/* Key avgs */}
                {avgs && (
                  <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-neutral-600">
                    <div><span className="text-neutral-400">Active time</span><div className="font-medium">{avgs.activeTime}</div></div>
                    <div><span className="text-neutral-400">% Active</span><div className="font-medium">{avgs.pctActive}</div></div>
                    <div><span className="text-neutral-400">First activity</span><div className="font-medium">{avgs.firstActivity}</div></div>
                    <div><span className="text-neutral-400">Last activity</span><div className="font-medium">{avgs.lastActivity}</div></div>
                    <div><span className="text-neutral-400">Est. avail.</span><div className="font-medium">{avgs.estAvailHours}</div></div>
                    {avgs.daysRemote && avgs.daysRemote !== '-' && (
                      <div><span className="text-neutral-400">Remote days</span><div className="font-medium">{avgs.daysRemote}</div></div>
                    )}
                    {avgs.daysInOffice && avgs.daysInOffice !== '-' && (
                      <div><span className="text-neutral-400">Office days</span><div className="font-medium">{avgs.daysInOffice}</div></div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
