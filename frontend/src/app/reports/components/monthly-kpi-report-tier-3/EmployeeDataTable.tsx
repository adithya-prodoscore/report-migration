'use client'

import { useState, useMemo, useCallback } from 'react'
import type { EmployeeRecord, ToolMetaRecord } from '@/hooks/useMonthlyKpiReportTier3'

interface EmployeeDataTableProps {
  employees: EmployeeRecord[]
  toolMeta: Record<string, ToolMetaRecord>
  companyAvgs: Record<string, string>
  roleAvgs: Record<string, Record<string, string>>
}

const FIXED_COLS: { key: keyof EmployeeRecord; label: string }[] = [
  { key: 'score', label: 'Score' },
  { key: 'mon', label: 'Mon' },
  { key: 'tue', label: 'Tue' },
  { key: 'wed', label: 'Wed' },
  { key: 'thu', label: 'Thu' },
  { key: 'fri', label: 'Fri' },
  { key: 'activeTime', label: 'Active Time' },
  { key: 'pctActive', label: '% Active' },
  { key: 'firstActivity', label: 'First Activity' },
  { key: 'lastActivity', label: 'Last Activity' },
  { key: 'estAvailHours', label: 'Est. Avail' },
  { key: 'pct1stHalf', label: '1st Half' },
  { key: 'pct2ndHalf', label: '2nd Half' },
  { key: 'mostProdDay', label: 'Best Day' },
  { key: 'leastProdDay', label: 'Worst Day' },
  { key: 'intMeetPct', label: 'Int Meet %' },
  { key: 'extMeetPct', label: 'Ext Meet %' },
  { key: 'intMeetTime', label: 'Int Meet' },
  { key: 'extMeetTime', label: 'Ext Meet' },
  { key: 'daysInOffice', label: 'Office Days' },
  { key: 'daysRemote', label: 'Remote Days' },
  { key: 'workplace', label: 'Workplace' },
]

function scoreBg(score: number | string): string {
  const s = typeof score === 'number' ? score : parseInt(String(score), 10)
  if (isNaN(s)) return ''
  if (s >= 70) return 'bg-kpi-tier-high-pale text-kpi-tier-high'
  if (s >= 40) return 'bg-kpi-tier-monitor-pale text-kpi-tier-monitor'
  return 'bg-kpi-tier-critical-pale text-kpi-tier-critical'
}

function downloadCsv(employees: EmployeeRecord[], toolKeys: string[]) {
  const allKeys = [...FIXED_COLS.map((c) => c.key as string), ...toolKeys]
  const header = ['name', 'role', 'manager', 'department', ...allKeys]
  const rows = employees.map((emp) =>
    header.map((k) => String(emp[k] ?? '')).join(',')
  )
  const csv = [header.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'monthly-kpi-report-tier-3.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function EmployeeDataTable({
  employees,
  toolMeta,
  companyAvgs,
  roleAvgs,
}: EmployeeDataTableProps) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<string>('score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [roleFilter, setRoleFilter] = useState('all')
  const [deptFilter, setDeptFilter] = useState('all')
  const [showCompanyAvg, setShowCompanyAvg] = useState(true)
  const [showRoleAvg, setShowRoleAvg] = useState(false)

  const toolKeys = useMemo(() => Object.keys(toolMeta), [toolMeta])
  const allRoles = useMemo(
    () => ['all', ...Array.from(new Set(employees.map((e) => e.role))).sort()],
    [employees],
  )
  const allDepts = useMemo(
    () => ['all', ...Array.from(new Set(employees.map((e) => e.department))).sort()],
    [employees],
  )

  const filtered = useMemo(() => {
    let result = employees
    if (search)
      result = result.filter(
        (e) =>
          e.name.toLowerCase().includes(search.toLowerCase()) ||
          e.role.toLowerCase().includes(search.toLowerCase()),
      )
    if (roleFilter !== 'all') result = result.filter((e) => e.role === roleFilter)
    if (deptFilter !== 'all') result = result.filter((e) => e.department === deptFilter)
    return [...result].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av === undefined || bv === undefined) return 0
      const an = typeof av === 'number' ? av : parseFloat(String(av))
      const bn = typeof bv === 'number' ? bv : parseFloat(String(bv))
      if (!isNaN(an) && !isNaN(bn)) return sortDir === 'asc' ? an - bn : bn - an
      return sortDir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    })
  }, [employees, search, roleFilter, deptFilter, sortKey, sortDir])

  const handleSort = useCallback(
    (key: string) => {
      if (sortKey === key) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
      } else {
        setSortKey(key)
        setSortDir('desc')
      }
    },
    [sortKey],
  )

  const SortIcon = ({ col }: { col: string }) => {
    if (sortKey !== col) return <span className="ml-1 text-neutral-300">↕</span>
    return <span className="ml-1 text-brand-indigo-600">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <div className="space-y-4">
      {/* Controls bar */}
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {/* Search */}
          <input
            type="search"
            placeholder="Search employee or role..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-1.5 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-indigo-400 w-52"
          />
          {/* Role filter */}
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-2 py-1.5 text-sm border border-neutral-200 rounded-lg focus:outline-none text-neutral-700"
            aria-label="Filter by role"
          >
            {allRoles.map((r) => (
              <option key={r} value={r}>{r === 'all' ? 'All Roles' : r}</option>
            ))}
          </select>
          {/* Dept filter */}
          <select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="px-2 py-1.5 text-sm border border-neutral-200 rounded-lg focus:outline-none text-neutral-700"
            aria-label="Filter by department"
          >
            {allDepts.map((d) => (
              <option key={d} value={d}>{d === 'all' ? 'All Departments' : d}</option>
            ))}
          </select>
          {/* Toggle pills */}
          <button
            aria-pressed={showCompanyAvg}
            onClick={() => setShowCompanyAvg((v) => !v)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors ${
              showCompanyAvg
                ? 'bg-brand-indigo-600 text-white border-brand-indigo-600'
                : 'bg-white text-neutral-500 border-neutral-200'
            }`}
          >
            Company Avg
          </button>
          <button
            aria-pressed={showRoleAvg}
            onClick={() => setShowRoleAvg((v) => !v)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors ${
              showRoleAvg
                ? 'bg-brand-indigo-600 text-white border-brand-indigo-600'
                : 'bg-white text-neutral-500 border-neutral-200'
            }`}
          >
            Role Avgs
          </button>
        </div>
        {/* CSV download */}
        <button
          onClick={() => downloadCsv(filtered, toolKeys)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-neutral-700 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          CSV
        </button>
      </div>

      {/* Count */}
      <p className="text-xs text-neutral-400">
        Showing {filtered.length} of {employees.length} employees
      </p>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-neutral-200 shadow-xs">
        <table className="min-w-full text-sm">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              {/* Sticky name column */}
              <th
                scope="col"
                className="sticky left-0 z-10 bg-neutral-50 px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wide min-w-[180px] cursor-pointer hover:bg-neutral-100"
                onClick={() => handleSort('name')}
              >
                Employee <SortIcon col="name" />
              </th>
              <th scope="col" className="px-3 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Role</th>
              <th scope="col" className="px-3 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap">Manager</th>
              {FIXED_COLS.map((col) => (
                <th
                  key={col.key as string}
                  scope="col"
                  className="px-3 py-3 text-center text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap cursor-pointer hover:bg-neutral-100"
                  onClick={() => handleSort(col.key as string)}
                >
                  {col.label} <SortIcon col={col.key as string} />
                </th>
              ))}
              {toolKeys.map((k) => (
                <th
                  key={k}
                  scope="col"
                  className="px-3 py-3 text-center text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap cursor-pointer hover:bg-neutral-100"
                  onClick={() => handleSort(k)}
                  title={toolMeta[k]?.name}
                >
                  {toolMeta[k]?.name ?? k} <SortIcon col={k} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100 bg-white">
            {/* Company avg row */}
            {showCompanyAvg && (
              <tr className="bg-kpi-blue-50">
                <td className="sticky left-0 z-10 bg-kpi-blue-50 px-4 py-2.5 font-semibold text-kpi-blue-700 text-xs">Company Avg</td>
                <td className="px-3 py-2.5 text-xs text-kpi-blue-500">—</td>
                <td className="px-3 py-2.5 text-xs text-kpi-blue-500">—</td>
                {FIXED_COLS.map((col) => (
                  <td key={col.key as string} className="px-3 py-2.5 text-center text-xs font-medium text-kpi-blue-700">
                    {companyAvgs[col.key as string] ?? '—'}
                  </td>
                ))}
                {toolKeys.map((k) => (
                  <td key={k} className="px-3 py-2.5 text-center text-xs font-medium text-kpi-blue-700">
                    {companyAvgs[k] ?? '—'}
                  </td>
                ))}
              </tr>
            )}
            {/* Role avg rows */}
            {showRoleAvg &&
              Object.entries(roleAvgs)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([role, avgs]) => (
                  <tr key={`role-avg-${role}`} className="bg-neutral-50">
                    <td className="sticky left-0 z-10 bg-neutral-50 px-4 py-2 text-xs font-semibold text-neutral-600">{role} Avg</td>
                    <td className="px-3 py-2 text-xs text-neutral-400">{role}</td>
                    <td className="px-3 py-2 text-xs text-neutral-400">—</td>
                    {FIXED_COLS.map((col) => (
                      <td key={col.key as string} className="px-3 py-2 text-center text-xs text-neutral-600">
                        {avgs[col.key as string] ?? '—'}
                      </td>
                    ))}
                    {toolKeys.map((k) => (
                      <td key={k} className="px-3 py-2 text-center text-xs text-neutral-600">
                        {avgs[k] ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
            {/* Employee rows */}
            {filtered.map((emp) => (
              <tr key={emp.name} className="hover:bg-neutral-50 transition-colors">
                <td className="sticky left-0 z-10 bg-white hover:bg-neutral-50 px-4 py-2.5 font-medium text-neutral-900 whitespace-nowrap">
                  {emp.name}
                </td>
                <td className="px-3 py-2.5 text-neutral-500 whitespace-nowrap">{emp.role}</td>
                <td className="px-3 py-2.5 text-neutral-500 whitespace-nowrap">{emp.manager}</td>
                {FIXED_COLS.map((col) => {
                  const val = emp[col.key]
                  const isScore = col.key === 'score'
                  return (
                    <td
                      key={col.key as string}
                      className={`px-3 py-2.5 text-center whitespace-nowrap ${
                        isScore ? `font-bold rounded ${scoreBg(val as number)}` : 'text-neutral-600'
                      }`}
                    >
                      {String(val ?? '—')}
                    </td>
                  )
                })}
                {toolKeys.map((k) => (
                  <td key={k} className="px-3 py-2.5 text-center text-neutral-600 whitespace-nowrap">
                    {String(emp[k] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td
                  colSpan={3 + FIXED_COLS.length + toolKeys.length}
                  className="px-4 py-8 text-center text-neutral-400 text-sm"
                >
                  No employees match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
