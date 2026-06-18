'use client'
// EmployeeDataTable — full Data tab metrics table with sticky name column,
// search filter, sort, and CSV download.
// HTML source: Data tab full employee metrics table
// Interactions: sort by column header, search by name, CSV export

import { useState, useMemo, useCallback } from 'react'
import type { EmployeeRecord, ToolMetaRecord } from '@/hooks/useMonthlyKpiReportTier4'

const WD = ['mon', 'tue', 'wed', 'thu', 'fri'] as const
const WD_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

function scoreBadge(score: number) {
  if (score >= 70) return 'bg-tier-high-bg text-tier-high'
  if (score >= 40) return 'bg-tier-avg-bg text-tier-avg'
  return 'bg-tier-low-bg text-tier-low'
}

type SortDir = 'asc' | 'desc'

interface EmployeeDataTableProps {
  employees: EmployeeRecord[]
  companyAvgs: Record<string, string>
  toolMeta: Record<string, ToolMetaRecord>
}

export function EmployeeDataTable({ employees, companyAvgs, toolMeta }: EmployeeDataTableProps) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<string>('score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const toolKeys = useMemo(() => Object.keys(toolMeta).sort(), [toolMeta])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return employees.filter(
      (e) =>
        e.name.toLowerCase().includes(q) ||
        e.role.toLowerCase().includes(q) ||
        e.manager.toLowerCase().includes(q) ||
        e.department.toLowerCase().includes(q),
    )
  }, [employees, search])

  const sorted = useMemo(() => {
    const clone = [...filtered]
    clone.sort((a, b) => {
      const av = a[sortKey as keyof EmployeeRecord] ?? 0
      const bv = b[sortKey as keyof EmployeeRecord] ?? 0
      const aNum = typeof av === 'number' ? av : parseFloat(av as string) || 0
      const bNum = typeof bv === 'number' ? bv : parseFloat(bv as string) || 0
      return sortDir === 'asc' ? aNum - bNum : bNum - aNum
    })
    return clone
  }, [filtered, sortKey, sortDir])

  function handleSort(key: string) {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const downloadCsv = useCallback(() => {
    const baseKeys = [
      'name', 'role', 'manager', 'department', 'score',
      ...WD, 'activeTime', 'firstActivity', 'lastActivity',
      'estAvailHours', 'pctActive', 'pct1stHalf', 'pct2ndHalf',
      'intMeetPct', 'extMeetPct', 'intMeetTime', 'extMeetTime',
      'daysInOffice', 'daysRemote', 'workplace', 'timezone',
    ]
    const allKeys = [...baseKeys, ...toolKeys]
    const header = allKeys.join(',')
    const rows = sorted.map((e) =>
      allKeys.map((k) => JSON.stringify((e as Record<string, unknown>)[k] ?? '')).join(',')
    )
    const csv = [header, ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'monthly-kpi-report-tier-4.csv'
    a.click()
    URL.revokeObjectURL(url)
  }, [sorted, toolKeys])

  function thClass(key: string) {
    return `px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide cursor-pointer select-none whitespace-nowrap hover:text-neutral-800 ${
      sortKey === key ? 'text-brand-indigo-600' : ''
    }`
  }

  function sortIndicator(key: string) {
    if (sortKey !== key) return null
    return sortDir === 'asc' ? ' ↑' : ' ↓'
  }

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <input
          type="search"
          placeholder="Search employees, roles, managers…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 text-sm border border-neutral-200 rounded-lg bg-white text-neutral-800 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-brand-indigo-500 w-72"
        />
        <button
          onClick={downloadCsv}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-brand-indigo-600 border border-brand-indigo-200 rounded-lg bg-brand-indigo-50 hover:bg-brand-indigo-100 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-neutral-200 shadow-xs">
        <table className="min-w-full text-sm border-collapse">
          <thead className="bg-neutral-50 sticky top-0 z-10">
            <tr>
              {/* Sticky name column */}
              <th scope="col" className="sticky left-0 z-20 bg-neutral-50 px-4 py-2.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wide border-r border-neutral-200 whitespace-nowrap">
                Name
              </th>
              <th scope="col" className={thClass('score')} onClick={() => handleSort('score')}>
                Score{sortIndicator('score')}
              </th>
              {WD.map((w, i) => (
                <th key={w} scope="col" className={thClass(w)} onClick={() => handleSort(w)}>
                  {WD_LABELS[i]}{sortIndicator(w)}
                </th>
              ))}
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Active Time</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">First</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Last</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Est. Avail</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">% Active</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">1st Half</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">2nd Half</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Int Meet %</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Ext Meet %</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Int Meet Time</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Ext Meet Time</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Days In-Office</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Days Remote</th>
              <th scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Workplace</th>
              {toolKeys.map((tk) => (
                <th key={tk} scope="col" className="px-3 py-2.5 text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">
                  {toolMeta[tk]?.name ?? tk}
                </th>
              ))}
            </tr>
          </thead>

          {/* Company average row */}
          <tbody>
            <tr className="bg-kpi-gray-50 border-b border-neutral-200 font-semibold">
              <td className="sticky left-0 z-10 bg-kpi-gray-50 px-4 py-2.5 text-xs text-neutral-600 font-extrabold border-r border-neutral-200 whitespace-nowrap">
                Company Avg
              </td>
              <td className="px-3 py-2.5 text-center">
                <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold ${
                  Number(companyAvgs.score ?? 0) >= 70
                    ? 'bg-tier-high-bg text-tier-high'
                    : Number(companyAvgs.score ?? 0) >= 40
                      ? 'bg-tier-avg-bg text-tier-avg'
                      : 'bg-tier-low-bg text-tier-low'
                }`}>
                  {companyAvgs.score ?? '-'}
                </span>
              </td>
              {WD.map((w) => (
                <td key={w} className="px-3 py-2.5 text-xs text-neutral-600 text-center">{companyAvgs[w] ?? '-'}</td>
              ))}
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.activeTime ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.firstActivity ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.lastActivity ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.estAvailHours ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.pctActive ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.pct1stHalf ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.pct2ndHalf ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.intMeetPct ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.extMeetPct ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.intMeetTime ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.extMeetTime ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.daysInOffice ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">{companyAvgs.daysRemote ?? '-'}</td>
              <td className="px-3 py-2.5 text-xs text-neutral-600">-</td>
              {toolKeys.map((tk) => (
                <td key={tk} className="px-3 py-2.5 text-xs text-neutral-600">{(companyAvgs as Record<string, string>)[tk] ?? '-'}</td>
              ))}
            </tr>

            {/* Employee rows */}
            {sorted.map((e) => (
              <tr key={e.name} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                <td className="sticky left-0 z-10 bg-white hover:bg-neutral-50 px-4 py-2.5 border-r border-neutral-200 whitespace-nowrap">
                  <div>
                    <p className="text-xs font-semibold text-neutral-900">{e.name}</p>
                    <p className="text-xs text-neutral-500">{e.role}</p>
                  </div>
                </td>
                <td className="px-3 py-2.5 text-center">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold ${scoreBadge(e.score)}`}>
                    {e.score}
                  </span>
                </td>
                {WD.map((w) => (
                  <td key={w} className="px-3 py-2.5 text-xs text-neutral-700 text-center">
                    {(e as Record<string, unknown>)[w] as number ?? '-'}
                  </td>
                ))}
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.activeTime}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.firstActivity}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.lastActivity}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.estAvailHours}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.pctActive}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.pct1stHalf}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.pct2ndHalf}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.intMeetPct}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.extMeetPct}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.intMeetTime}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.extMeetTime}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.daysInOffice}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.daysRemote}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-700">{e.workplace}</td>
                {toolKeys.map((tk) => (
                  <td key={tk} className="px-3 py-2.5 text-xs text-neutral-700">
                    {(e as Record<string, unknown>)[tk] as string ?? '-'}
                  </td>
                ))}
              </tr>
            ))}

            {sorted.length === 0 && (
              <tr>
                <td
                  colSpan={16 + toolKeys.length}
                  className="text-center py-12 text-sm text-neutral-400"
                >
                  No employees match the search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-neutral-400">
        Showing {sorted.length} of {employees.length} employees
      </p>
    </div>
  )
}
