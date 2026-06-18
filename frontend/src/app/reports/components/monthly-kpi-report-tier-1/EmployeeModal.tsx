'use client'

import { useRef, useEffect } from 'react'
import type { EmployeeRecordT1 } from '@/hooks/useMonthlyKpiReportTier1'

interface EmployeeModalProps {
  employee: EmployeeRecordT1 | null
  onClose: () => void
}

function scoreTier(score: number): 'critical' | 'monitor' | 'high' {
  if (score < 40) return 'critical'
  if (score < 70) return 'monitor'
  return 'high'
}

const TIER_SCORE_TEXT: Record<string, string> = {
  critical: 'text-kpi-tier-critical',
  monitor:  'text-kpi-tier-monitor',
  high:     'text-kpi-tier-high',
}

const SECTION_ORDER = ['SCORE', 'WORK HABITS', 'MOST & LEAST PRODUCTIVE', 'MEETINGS', 'TECH MODULES', 'WEB BROWSER']

export function EmployeeModal({ employee, onClose }: EmployeeModalProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const tier = employee ? scoreTier(employee.score) : 'monitor'

  useEffect(() => {
    if (!employee) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [employee, onClose])

  useEffect(() => {
    if (employee) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [employee])

  if (!employee) return null

  // Group metrics by section
  const grouped: Record<string, typeof employee.metrics> = {}
  for (const m of employee.metrics) {
    if (!grouped[m.section]) grouped[m.section] = []
    grouped[m.section].push(m)
  }
  const sections = SECTION_ORDER.filter(s => grouped[s])

  function handleDownload() {
    const rows = [
      ['Section', 'Label', 'Value', 'Role Avg'],
      ...employee!.metrics.map(m => [m.section, m.label, m.value, m.roleAvg]),
    ]
    const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${employee!.name.replace(/\s+/g, '_')}_kpi.csv`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center px-5 py-10 overflow-y-auto"
      style={{ background: 'rgba(13,39,68,0.45)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-name"
    >
      <div
        ref={panelRef}
        className="bg-kpi-white rounded-xl w-full max-w-[760px] shadow-shadow-xl overflow-hidden flex flex-col"
        style={{ maxHeight: 'calc(100vh - 80px)' }}
      >
        {/* Header */}
        <div className="px-7 pt-6 pb-5 border-b border-kpi-gray-100 flex items-start justify-between gap-5 flex-shrink-0">
          <div className="flex-1 min-w-0">
            <h2 id="modal-name" className="text-[22px] font-bold text-kpi-gray-950 leading-snug mb-1.5">
              {employee.name}
            </h2>
            <p className="text-[13px] text-kpi-gray-600 leading-relaxed">
              {employee.role}
              <span className="mx-2 text-kpi-gray-300">·</span>
              {employee.dept}
              {employee.manager && (
                <><span className="mx-2 text-kpi-gray-300">·</span>Mgr: {employee.manager}</>
              )}
            </p>
          </div>
          {/* Score */}
          <div className="flex-shrink-0 flex items-start gap-4">
            <div className="text-right">
              <div className={`text-[36px] font-extrabold leading-none tracking-tight ${TIER_SCORE_TEXT[tier]}`}>
                {employee.score}
              </div>
              <div className="text-[11px] uppercase tracking-wider font-bold text-kpi-gray-500 mt-1">Score</div>
            </div>
          </div>
          <button
            type="button"
            className="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-full bg-kpi-gray-50 text-kpi-gray-600 hover:bg-kpi-gray-100 hover:text-kpi-gray-900 transition-colors"
            aria-label="Close"
            onClick={onClose}
          >
            <svg className="w-4 h-4 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>
        {/* Body */}
        <div className="overflow-y-auto flex-1">
          {sections.map(sec => (
            <div key={sec} className="border-t border-kpi-gray-100 first:border-t-0">
              <div className="px-7 py-3 text-[11px] uppercase tracking-wider font-bold text-kpi-gray-500 bg-kpi-gray-50">
                {sec}
              </div>
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <td className="px-7 py-1.5 text-[10px] uppercase tracking-wider text-kpi-gray-400 font-bold w-1/2">Metric</td>
                    <td className="px-7 py-1.5 text-[10px] uppercase tracking-wider text-kpi-gray-400 font-bold text-right w-1/4">Value</td>
                    <td className="px-7 py-1.5 text-[10px] uppercase tracking-wider text-kpi-gray-400 font-bold text-right w-1/4">Role Avg</td>
                  </tr>
                </thead>
                <tbody>
                  {grouped[sec].map((m, i) => (
                    <tr key={i} className="border-b border-kpi-gray-50 last:border-b-0 hover:bg-kpi-gray-50">
                      <td className="px-7 py-2.5 text-[13px] text-kpi-gray-700 font-medium">{m.label}</td>
                      <td className="px-7 py-2.5 text-[13px] text-kpi-gray-950 font-semibold tabular-nums text-right">{m.value}</td>
                      <td className="px-7 py-2.5 text-[12px] text-kpi-gray-500 font-medium tabular-nums text-right">{m.roleAvg}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
        {/* Footer */}
        <div className="px-7 py-3.5 border-t border-kpi-gray-100 flex justify-end gap-3 flex-shrink-0 bg-kpi-gray-50">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-kpi-white border border-kpi-gray-200 rounded-md text-[13px] font-semibold text-kpi-gray-800 hover:bg-kpi-blue-50 hover:border-kpi-blue-400 hover:text-kpi-blue-700 transition-colors"
            onClick={handleDownload}
          >
            <svg className="w-3.5 h-3.5 stroke-current fill-none" viewBox="0 0 16 16" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M8 2v9M4.5 7.5 8 11 11.5 7.5M3 13h10" />
            </svg>
            Download CSV
          </button>
        </div>
      </div>
    </div>
  )
}
