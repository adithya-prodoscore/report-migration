'use client'

import { useState, useRef, useEffect } from 'react'
import type { EmployeeRecordT1 } from '@/app/hooks/useMonthlyKpiReportTier1'

type SortKey = 'name' | 'score' | 'roleAvg' | 'delta' | 'activeTime' | 'status'
type SortDir = 'asc' | 'desc'

interface EmployeeTableProps {
  employees: EmployeeRecordT1[]
  onRowClick: (emp: EmployeeRecordT1) => void
  sortKey: SortKey
  sortDir: SortDir
  onSort: (key: SortKey) => void
  page: number
  pageSize: number
  onPageChange: (p: number) => void
}

function scoreTier(score: number): 'critical' | 'monitor' | 'high' {
  if (score < 40) return 'critical'
  if (score < 70) return 'monitor'
  return 'high'
}

const TIER_SCORE_TEXT: Record<string, string> = { critical: 'text-kpi-tier-critical', monitor: 'text-kpi-gray-800', high: 'text-kpi-tier-high' }
const STATUS_DOT: Record<string, string> = { 'needs-attention': 'bg-kpi-red-500', 'inactive': 'bg-kpi-yellow-500', 'most-engaged': 'bg-kpi-blue-500' }

function Sparkline({ trendCy, trendColor }: { trendCy: number[]; trendColor: string }) {
  if (trendCy.length === 0) return null
  const W = 130; const H = 30
  const mn = Math.min(...trendCy); const mx = Math.max(...trendCy); const range = mx - mn || 1
  const n = trendCy.length
  const xs = trendCy.map((_, i) => (i / Math.max(n - 1, 1)) * W)
  const ys = trendCy.map(v => H - 3 - ((v - mn) / range) * (H - 6))
  const d = xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(' ')
  const color = trendColor.includes('red') ? '#F1433C' : '#1E86D9'
  return <svg width={W} height={H} aria-hidden="true" className="inline-block align-middle"><path d={d} fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" /></svg>
}

const COLUMNS: { key: SortKey; label: string; sortable: boolean }[] = [
  { key: 'name',       label: 'Employee',    sortable: true },
  { key: 'score',      label: 'Score',       sortable: true },
  { key: 'roleAvg',    label: 'Role Avg',    sortable: true },
  { key: 'delta',      label: 'Delta',       sortable: true },
  { key: 'activeTime', label: 'Active Time', sortable: false },
  { key: 'status',     label: 'Trend',       sortable: false },
]

export function EmployeeTable({ employees, onRowClick, sortKey, sortDir, onSort, page, pageSize, onPageChange }: EmployeeTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const h = () => setIsScrolled(el.scrollLeft > 0)
    el.addEventListener('scroll', h, { passive: true })
    return () => el.removeEventListener('scroll', h)
  }, [])

  const start = (page - 1) * pageSize
  const paged = employees.slice(start, start + pageSize)
  const totalPages = Math.max(1, Math.ceil(employees.length / pageSize))

  function handleDownloadCsv() {
    const headers = ['Name', 'Dept', 'Role', 'Manager', 'Score', 'Role Avg', 'Delta', 'Active Time', 'Status']
    const rows = employees.map(e => [e.name, e.dept, e.role, e.manager, e.score, e.roleAvg, e.delta, e.activeTime, e.status])
    const csv = [headers, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'monthly_kpi_report_tier1.csv'; a.click(); URL.revokeObjectURL(a.href)
  }

  return (
    <div className="bg-kpi-white border border-kpi-gray-100 rounded-xl overflow-hidden shadow-shadow-xs">
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-kpi-gray-100 gap-4">
        <div className="flex items-baseline gap-4">
          <span className="text-[15px] font-bold text-kpi-gray-950">Employees</span>
          <span className="text-[13px] text-kpi-gray-500">Showing <strong className="text-kpi-gray-900 font-bold">{employees.length}</strong> of {employees.length}</span>
        </div>
        <button type="button" className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-kpi-white border border-kpi-gray-200 rounded-md text-[13px] font-semibold text-kpi-gray-800 hover:bg-kpi-blue-50 hover:border-kpi-blue-400 hover:text-kpi-blue-700 transition-colors" onClick={handleDownloadCsv}>
          <svg className="w-3.5 h-3.5 stroke-current fill-none" viewBox="0 0 16 16" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M8 2v9M4.5 7.5 8 11 11.5 7.5M3 13h10" /></svg>
          Download CSV
        </button>
      </div>
      <div ref={scrollRef} className="overflow-x-auto overflow-y-auto" style={{ maxHeight: '70vh' }}>
        <table className="w-full text-[14px]" style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
          <thead>
            <tr>
              {COLUMNS.map(col => (
                <th key={col.key} scope="col"
                  className={['bg-kpi-white text-[13px] font-semibold text-kpi-gray-700 text-left px-5 py-4 border-b border-r border-kpi-gray-200 last:border-r-0 whitespace-nowrap select-none sticky top-0 z-[3]', col.key === 'name' ? 'sticky left-0 z-[4] min-w-[240px]' : '', col.sortable ? 'cursor-pointer hover:text-kpi-blue-600' : '', sortKey === col.key ? 'text-kpi-gray-950' : ''].join(' ')}
                  onClick={col.sortable ? () => onSort(col.key) : undefined}
                >
                  {col.label}{col.sortable && <span className={`ml-1.5 text-[10px] ${sortKey === col.key ? 'opacity-100' : 'opacity-0'}`}>{sortDir === 'asc' ? '↑' : '↓'}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.length === 0 && (
              <tr><td colSpan={COLUMNS.length} className="py-16 text-center text-[14px] text-kpi-gray-500">
                <p className="text-[16px] font-semibold text-kpi-gray-700 mb-1">No employees match these filters</p>
                <p>Try clearing one or more filters above.</p>
              </td></tr>
            )}
            {paged.map(emp => {
              const tier = scoreTier(emp.score)
              const delta = parseInt(emp.delta)
              const hasDot = emp.status !== 'on-track'
              return (
                <tr key={emp.id} className="group cursor-pointer" onClick={() => onRowClick(emp)} tabIndex={0} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onRowClick(emp) }}>
                  <td className={['sticky left-0 z-[2] bg-kpi-white group-hover:bg-kpi-gray-50 pl-7 pr-5 py-[22px] border-r border-b border-kpi-gray-100 relative min-w-[240px]', isScrolled ? 'shadow-[6px_0_8px_-2px_rgba(0,0,0,0.12)]' : ''].join(' ')}>
                    <span className={`absolute left-0 top-0 bottom-0 w-1 ${tier === 'critical' ? 'bg-kpi-tier-critical' : tier === 'high' ? 'bg-kpi-tier-high' : 'bg-kpi-tier-monitor'}`} aria-hidden="true" />
                    <div className="flex items-center gap-2.5">
                      {hasDot ? <span className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_DOT[emp.status] ?? 'bg-kpi-gray-300'}`} aria-hidden="true" /> : <span className="w-2 h-2 flex-shrink-0" aria-hidden="true" />}
                      <div className="flex flex-col leading-snug">
                        <span className="font-semibold text-kpi-gray-950 text-[15px]">{emp.name}</span>
                        <span className="text-[12px] text-kpi-gray-500 mt-0.5">{emp.role}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-[22px] border-r border-b border-kpi-gray-100 bg-kpi-white group-hover:bg-kpi-gray-50 whitespace-nowrap">
                    <span className={`font-semibold text-[15px] ${TIER_SCORE_TEXT[tier]}`}>{emp.score}</span>
                  </td>
                  <td className="px-5 py-[22px] border-r border-b border-kpi-gray-100 bg-kpi-white group-hover:bg-kpi-gray-50 whitespace-nowrap text-kpi-gray-600">{emp.roleAvg}</td>
                  <td className="px-5 py-[22px] border-r border-b border-kpi-gray-100 bg-kpi-white group-hover:bg-kpi-gray-50 whitespace-nowrap">
                    <span className={`inline-flex items-center gap-1.5 font-semibold text-[14px] ${delta > 0 ? 'text-kpi-tier-high' : delta < 0 ? 'text-kpi-tier-critical' : 'text-kpi-gray-500'}`}>
                      <span>{delta > 0 ? '↑' : delta < 0 ? '↓' : ''}</span>{emp.delta}
                    </span>
                  </td>
                  <td className="px-5 py-[22px] border-r border-b border-kpi-gray-100 bg-kpi-white group-hover:bg-kpi-gray-50 whitespace-nowrap text-kpi-gray-800 font-medium">{emp.activeTime}</td>
                  <td className="px-5 py-[22px] border-b border-kpi-gray-100 bg-kpi-white group-hover:bg-kpi-gray-50 w-40 text-center">
                    <Sparkline trendCy={emp.trendCy} trendColor={emp.trendColor} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-kpi-gray-100 text-[13px] flex-wrap gap-3">
          <span className="text-kpi-gray-600">Showing <strong className="font-bold text-kpi-gray-900">{start + 1}–{Math.min(start + pageSize, employees.length)}</strong> of {employees.length}</span>
          <div className="flex items-center gap-1">
            <button className="w-8 h-8 flex items-center justify-center border border-kpi-gray-200 rounded-md text-kpi-gray-800 hover:bg-kpi-blue-50 hover:border-kpi-blue-400 disabled:text-kpi-gray-300 disabled:border-kpi-gray-100 disabled:cursor-not-allowed" disabled={page === 1} onClick={() => onPageChange(page - 1)} aria-label="Previous page">‹</button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(p => Math.abs(p - page) <= 2 || p === 1 || p === totalPages)
              .reduce<(number | string)[]>((acc, p, i, arr) => { if (i > 0 && typeof arr[i-1] === 'number' && (p as number) - (arr[i-1] as number) > 1) acc.push('…'); acc.push(p); return acc }, [])
              .map((p, i) => p === '…' ? <span key={`e${i}`} className="px-1 text-kpi-gray-400">…</span> : <button key={p} className={`w-8 h-8 flex items-center justify-center border rounded-md text-[13px] font-semibold ${page === p ? 'bg-kpi-blue-600 text-white border-kpi-blue-600' : 'border-kpi-gray-200 text-kpi-gray-800 hover:bg-kpi-blue-50 hover:border-kpi-blue-400'}`} onClick={() => onPageChange(p as number)} aria-current={page === p ? 'page' : undefined}>{p}</button>)
            }
            <button className="w-8 h-8 flex items-center justify-center border border-kpi-gray-200 rounded-md text-kpi-gray-800 hover:bg-kpi-blue-50 hover:border-kpi-blue-400 disabled:text-kpi-gray-300 disabled:border-kpi-gray-100 disabled:cursor-not-allowed" disabled={page === totalPages} onClick={() => onPageChange(page + 1)} aria-label="Next page">›</button>
          </div>
        </div>
      )}
    </div>
  )
}
