'use client'

import { useState, useMemo, useRef } from 'react'
import { MonthlyKpiReportTier7Data, ToolMetaEntry } from '@/hooks/useMonthlyKpiReportTier7'

interface DataTabProps {
  data: MonthlyKpiReportTier7Data
}

const FIXED_COLS = [
  { key: 'score', label: 'Score' },
  { key: 'mon', label: 'Mon' },
  { key: 'tue', label: 'Tue' },
  { key: 'wed', label: 'Wed' },
  { key: 'thu', label: 'Thu' },
  { key: 'fri', label: 'Fri' },
  { key: 'activeTime', label: 'Active Time' },
  { key: 'pctActive', label: '% Active' },
  { key: 'firstActivity', label: 'First' },
  { key: 'lastActivity', label: 'Last' },
  { key: 'estAvailHours', label: 'Est. Avail' },
  { key: 'pct1stHalf', label: '1st Half' },
  { key: 'pct2ndHalf', label: '2nd Half' },
  { key: 'mostProdDay', label: 'Best Day' },
  { key: 'leastProdDay', label: 'Worst Day' },
  { key: 'intMeetPct', label: 'Int Meet%' },
  { key: 'extMeetPct', label: 'Ext Meet%' },
  { key: 'daysInOffice', label: 'In-Office' },
  { key: 'daysRemote', label: 'Remote' },
]

type SortDir = 'asc' | 'desc'

function scoreColor(val: unknown): string {
  if (typeof val !== 'number') return ''
  if (val >= 70) return 'text-kpi-tier-high'
  if (val >= 40) return 'text-kpi-tier-avg'
  return 'text-kpi-tier-critical'
}

export function DataTab({ data }: DataTabProps) {
  const { ALL_EMPLOYEES, COMPANY_AVGS, ROLE_AVGS, TOOL_META } = data

  const [search, setSearch] = useState('')
  const [filterRole, setFilterRole] = useState('all')
  const [filterDept, setFilterDept] = useState('all')
  const [sortKey, setSortKey] = useState('score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const tableRef = useRef<HTMLDivElement>(null)

  const roles = useMemo(
    () => ['all', ...Array.from(new Set(ALL_EMPLOYEES.map((e) => String(e.role ?? '')).filter(Boolean)))],
    [ALL_EMPLOYEES],
  )
  const depts = useMemo(
    () => ['all', ...Array.from(new Set(ALL_EMPLOYEES.map((e) => String(e.department ?? '')).filter((d) => d && d !== '—')))],
    [ALL_EMPLOYEES],
  )

  const toolCols = useMemo(
    () =>
      Object.entries(TOOL_META as Record<string, ToolMetaEntry>).map(([key, meta]) => ({
        key,
        label: meta.name,
        munit: meta.munit,
      })),
    [TOOL_META],
  )

  const allCols = [...FIXED_COLS, ...toolCols]

  const filtered = useMemo(() => {
    let rows = ALL_EMPLOYEES as Record<string, unknown>[]
    if (search) {
      const q = search.toLowerCase()
      rows = rows.filter(
        (e) =>
          String(e.name ?? '').toLowerCase().includes(q) ||
          String(e.role ?? '').toLowerCase().includes(q),
      )
    }
    if (filterRole !== 'all') rows = rows.filter((e) => e.role === filterRole)
    if (filterDept !== 'all') rows = rows.filter((e) => e.department === filterDept)
    return [...rows].sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      const an = typeof av === 'number' ? av : parseFloat(String(av)) || 0
      const bn = typeof bv === 'number' ? bv : parseFloat(String(bv)) || 0
      return sortDir === 'desc' ? bn - an : an - bn
    })
  }, [ALL_EMPLOYEES, search, filterRole, filterDept, sortKey, sortDir])

  function toggleSort(key: string) {
    if (sortKey === key) setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  function downloadCsv() {
    const headers = ['Name', 'Role', 'Manager', 'Department', ...allCols.map((c) => c.label)]
    const rows = filtered.map((e) =>
      [
        e.name,
        e.role,
        e.manager,
        e.department,
        ...allCols.map((c) => e[c.key] ?? ''),
      ]
        .map((v) => `"${String(v ?? '').replace(/"/g, '""')}"`)
        .join(','),
    )
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'monthly-kpi-report-tier-7.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Search name or role…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-neutral-200 rounded-md bg-neutral-0 text-sm text-neutral-800 px-3 py-1.5 w-52 focus:outline-none focus:border-kpi-blue-400"
        />
        <select
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value)}
          aria-label="Filter by role"
          className="border border-neutral-200 rounded-md bg-neutral-0 text-sm text-neutral-800 px-3 py-1.5 focus:outline-none focus:border-kpi-blue-400"
        >
          {roles.map((r) => (
            <option key={r} value={r}>
              {r === 'all' ? 'All roles' : r}
            </option>
          ))}
        </select>
        <select
          value={filterDept}
          onChange={(e) => setFilterDept(e.target.value)}
          aria-label="Filter by department"
          className="border border-neutral-200 rounded-md bg-neutral-0 text-sm text-neutral-800 px-3 py-1.5 focus:outline-none focus:border-kpi-blue-400"
        >
          {depts.map((d) => (
            <option key={d} value={d}>
              {d === 'all' ? 'All depts' : d}
            </option>
          ))}
        </select>
        <button
          onClick={downloadCsv}
          className="ml-auto text-xs font-medium px-3 py-1.5 rounded-md border border-neutral-200 bg-neutral-0 text-kpi-gray-700 hover:bg-neutral-100 transition-colors"
        >
          Download CSV
        </button>
      </div>

      {/* Transposed-style data table — sticky left column */}
      <div ref={tableRef} className="overflow-x-auto border border-neutral-200 rounded-lg shadow-sm">
        <table className="w-full text-xs border-collapse">
          <thead>
            {/* Group header row (Company avg + Role avg columns) */}
            <tr className="bg-kpi-gray-100">
              <th
                scope="col"
                className="sticky left-0 z-20 bg-kpi-gray-100 px-3 py-2 text-left font-semibold text-kpi-gray-700 border-b border-neutral-200 border-r border-neutral-200 min-w-[160px]"
              >
                Employee
              </th>
              <th
                colSpan={allCols.length}
                className="px-3 py-2 text-center font-semibold text-kpi-gray-700 border-b border-neutral-200"
              >
                {filtered.length} employees · Sorted by {allCols.find((c) => c.key === sortKey)?.label ?? sortKey} ({sortDir})
              </th>
            </tr>
            {/* Column header row */}
            <tr className="bg-kpi-gray-50">
              <th
                scope="col"
                className="sticky left-0 z-20 bg-kpi-gray-50 px-3 py-2 text-left font-semibold text-kpi-gray-600 uppercase tracking-wide border-b border-neutral-200 border-r border-neutral-200"
              >
                Name / Role
              </th>
              {allCols.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  onClick={() => toggleSort(col.key)}
                  className="px-3 py-2 text-center font-semibold text-kpi-gray-600 uppercase tracking-wide border-b border-neutral-200 whitespace-nowrap cursor-pointer hover:bg-kpi-gray-100 select-none"
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span className="ml-1">{sortDir === 'desc' ? '↓' : '↑'}</span>
                  )}
                </th>
              ))}
            </tr>

            {/* Company avg row */}
            {COMPANY_AVGS && (
              <tr className="bg-kpi-blue-50">
                <td className="sticky left-0 z-10 bg-kpi-blue-50 px-3 py-1.5 font-semibold text-kpi-blue-700 border-b border-neutral-200 border-r border-neutral-200">
                  Company Avg
                </td>
                {allCols.map((col) => (
                  <td
                    key={col.key}
                    className={`px-3 py-1.5 text-center border-b border-neutral-200 font-medium ${
                      col.key === 'score' ? 'text-kpi-blue-600' : 'text-kpi-gray-700'
                    }`}
                  >
                    {String((COMPANY_AVGS as Record<string, unknown>)[col.key] ?? '—')}
                  </td>
                ))}
              </tr>
            )}
          </thead>

          <tbody>
            {filtered.map((emp) => (
              <tr
                key={String(emp.name)}
                className="border-b border-neutral-100 hover:bg-kpi-gray-50 transition-colors"
              >
                {/* Sticky identity cell */}
                <td className="sticky left-0 z-10 bg-neutral-0 px-3 py-2 border-r border-neutral-200 min-w-[160px]">
                  <p className="font-semibold text-neutral-900 truncate">{String(emp.name)}</p>
                  <p className="text-kpi-gray-500 truncate">{String(emp.role ?? '—')}</p>
                </td>

                {allCols.map((col) => {
                  const raw = emp[col.key]
                  const display = raw !== undefined && raw !== null ? String(raw) : '—'
                  return (
                    <td
                      key={col.key}
                      className={`px-3 py-2 text-center whitespace-nowrap ${
                        col.key === 'score'
                          ? scoreColor(raw)
                          : 'text-neutral-700'
                      }`}
                    >
                      {display}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-kpi-gray-400">
        Showing {filtered.length} of {ALL_EMPLOYEES.length} employees
      </p>
    </div>
  )
}
