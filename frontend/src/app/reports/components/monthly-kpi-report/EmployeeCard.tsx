'use client'

import { useState } from 'react'
import type { TriageItem } from '@/types/monthly-kpi-report'

interface EmployeeCardProps {
  employee: TriageItem
  status: 'flagged' | 'inactive' | 'top'
}

export default function EmployeeCard({
  employee,
  status,
}: EmployeeCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const statusStyles = {
    flagged: {
      badge: 'kpi-badge-monitor',
      label: 'Needs Attention',
      color: 'text-tier-monitor',
    },
    inactive: {
      badge: 'bg-gray-100 text-gray-700',
      label: 'Inactive',
      color: 'text-gray-600',
    },
    top: {
      badge: 'kpi-badge-on-track',
      label: 'Top Performer',
      color: 'text-tier-on-track',
    },
  }

  const style = statusStyles[status]

  return (
    <div className="kpi-card cursor-pointer hover:shadow-md transition-shadow">
      <div onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="kpi-text-primary">{employee.name}</h4>
            <p className="kpi-text-secondary">{employee.role} • {employee.manager}</p>
          </div>
          <span className={`kpi-badge ${style.badge}`}>{style.label}</span>
        </div>

        <div className="flex items-end justify-between mt-4 gap-4">
          <div className="flex-1">
            <div className="flex items-baseline gap-2">
              <span className={`text-2xl font-bold ${style.color}`}>{employee.score}</span>
              <span className="text-sm text-slate-600">{employee.scoreGap}</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">vs {employee.roleAvg} avg</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-slate-900">{employee.activeTime}</p>
            <p className="text-xs text-slate-500">{employee.timeGap}</p>
          </div>
          <button className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
            <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-slate-200 space-y-4">
          {/* Daily Sparkline */}
          <div>
            <p className="text-xs font-semibold text-slate-600 uppercase mb-2">Weekly Scores</p>
            <div className="flex gap-1 items-end h-12">
              {employee.daily.map(day => (
                <div key={day.day} className="flex-1 flex flex-col items-center">
                  <div
                    style={{
                      height: `${(day.score / 100) * 100}%`,
                      backgroundColor: '#1E86D9',
                      borderRadius: '2px',
                    }}
                    className="w-full min-h-1"
                  />
                  <span className="text-xs text-slate-600 mt-1">{day.day[0]}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Details */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-slate-600">Most Productive</p>
              <p className="font-semibold text-slate-900">{employee.mostProductiveDay}</p>
            </div>
            <div>
              <p className="text-slate-600">Least Productive</p>
              <p className="font-semibold text-slate-900">{employee.leastProductiveDay}</p>
            </div>
            <div>
              <p className="text-slate-600">First Activity</p>
              <p className="font-semibold text-slate-900">{employee.firstActivity}</p>
            </div>
            <div>
              <p className="text-slate-600">Last Activity</p>
              <p className="font-semibold text-slate-900">{employee.lastActivity}</p>
            </div>
          </div>

          {/* Gaps and Standouts */}
          {(employee.gaps.length > 0 || employee.standouts.length > 0) && (
            <div className="space-y-2">
              {employee.gaps.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-red-700">Areas to improve:</p>
                  <ul className="text-xs text-slate-600 mt-1 list-disc list-inside">
                    {employee.gaps.map((gap, idx) => (
                      <li key={idx}>{gap}</li>
                    ))}
                  </ul>
                </div>
              )}
              {employee.standouts.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-green-700">Standout areas:</p>
                  <ul className="text-xs text-slate-600 mt-1 list-disc list-inside">
                    {employee.standouts.map((standout, idx) => (
                      <li key={idx}>{standout}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
