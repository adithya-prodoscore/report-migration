'use client'

import { useState, useMemo, useCallback } from 'react'
import type { MonthlyKpiReportTier2Response, EmployeeRecordTier2 } from '@/types/monthly-kpi-report-tier-2'

interface DataSectionTier2Props {
  data: MonthlyKpiReportTier2Response
}

type SortKey = keyof Pick<EmployeeRecordTier2, 'name' | 'role' | 'manager' | 'department' | 'score' | 'activeTimeMin'>
type SortDir = 'asc' | 'desc'

const FIXED_COLUMNS: { key: SortKey | string; label: string; sortable: boolean }[] = [
  { key: 'name',        label: 'Employee',   sortable: true },
  { key: 'role',        label: 'Role',        sortable: true },
  { key: 'manager',     label: 'Manager',     sortable: true },
  { key: 'department',  label: 'Department',  sortable: true },
  { key: 'score',       label: 'Score',       sortable: true },
  { key: 'activeTimeMin', label: 'Active Time', sortable: true },
  { key: 'activeTime',  label: 'Avg Active',  sortable: false },
  { key: 'firstActivity', label: 'First',     sortable: false },
  { key: 'lastActivity',  label: 'Last',      sortable: false },
  { key: 'pctActive',   label: '% Active',    sortable: false },
  { key: 'workplace',   label: 'Workplace',   sortable: true },
  { key: 'mostProdDay', label: 'Best Day',    sortable: false },
  { key: 'leastProdDay','label': 'Slow Day',  sortable: false },
  { key: 'intMeetPct',  label: 'Int Meet %',  sortable: false },
  { key: 'extMeetPct',  label: 'Ext Meet %',  sortable: false },
  { key: 'daysInOffice','label': 'In-Office', sortable: false },
  { key: 'daysRemote',  label: 'Remote',      sortable: false },
]

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="text-neutral-300 text-xs">↕</span>
  return <span className="text-brand-indigo-500 text-xs">{dir === 'asc' ? '↑' : '↓'}</span>
}

function exportCsv(employees: EmployeeRecordTier2[]) {
  if (employees.length === 0) return
  const keys = Object.keys(employees[0]) as (keyof EmployeeRecordTier2)[]
  const header = keys.join(',')
  const rows = employees.map((emp) =>
    keys.map((k) => {
      const v = emp[k]
      if (typeof v === 'string' && (v.includes(',') || v.includes('"'))) {
        return `"${v.replace(/"/g, '""')}"`
      }
      return v ?? ''
    }).join(',')
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'monthly-kpi-report-tier-2.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function DataSectionTier2({ data }: DataSectionTier2Props) {
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [search, setSearch] = useState('')
  const [filterRole, setFilterRole] = useState('')
  const [filterManager, setFilterManager] = useState('')
  const [filterDept, setFilterDept] = useState('')
  const [filterWorkplace, setFilterWorkplace] = useState('')

  const allEmployees = data.ALL_EMPLOYEES ?? []

  const roles = useMemo(
    () => [...new Set(allEmployees.map((e) => e.role))].sort(),
    [allEmployees]
  )
  const managers = useMemo(
    () => [...new Set(allEmployees.map((e) => e.manager))].sort(),
    [allEmployees]
  )
  const departments = useMemo(
    () => [...new Set(allEmployees.map((e) => e.department))].sort(),
    [allEmployees]
  )
  const workplaces = useMemo(
    () => [...new Set(allEmployees.map((e) => e.workplace))].sort(),
    [allEmployees]
  )

  const filtered = useMemo(() => {
    let list = allEmployees
    if (search) {
      const q = search.toLowerCase()
      list = list.filter((e) => e.name.toLowerCase().includes(q))
    }
    if (filterRole) list = list.filter((e) => e.role === filterRole)
    if (filterManager) list = list.filter((e) => e.manager === filterManager)
    if (filterDept) list = list.filter((e) => e.department === filterDept)
    if (filterWorkplace) list = list.filter((e) => e.workplace === filterWorkplace)
    return list
  }, [allEmployees, search, filterRole, filterManager, filterDept, filterWorkplace])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortKey as keyof EmployeeRecordTier2]
      const bv = b[sortKey as keyof EmployeeRecordTier2]
      if (typeof av === 'number' && typeof bv === 'number') {
        return sortDir === 'asc' ? av - bv : bv - av
      }
      const as = String(av ?? '').toLowerCase()
      const bs = String(bv ?? '').toLowerCase()
      return sortDir === 'asc' ? as.localeCompare(bs) : bs.localeCompare(as)
    })
  }, [filtered, sortKey, sortDir])

  const handleSort = useCallback(
    (key: SortKey) => {
      if (sortKey === key) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
      } else {
        setSortKey(key)
        setSortDir(key === 'name' ? 'asc' : 'desc')
      }
    },
    [sortKey]
  )

  const companyAvgs = data.COMPANY_AVGS as Record<string, string>

  return (
    <section className="space-y-4">
      {/* Filters Row */}
      <div className="flex flex-wrap gap-2 items-center">
        <input
          type="search"
          placeholder="Search employee name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-1.5 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-indigo-500 w-52"
          aria-label="Search employees"
        />

        {[
          { label: 'All Roles', value: filterRole, setter: setFilterRole, options: roles },
          { label: 'All Managers', value: filterManager, setter: setFilterManager, options: managers },
          { label: 'All Departments', value: filterDept, setter: setFilterDept, options: departments },
          { label: 'All Workplaces', value: filterWorkplace, setter: setFilterWorkplace, options: workplaces },
        ].map(({ label, value, setter, options }) => (
          <select
            key={label}
            value={value}
            onChange={(e) => setter(e.target.value)}
            className="px-3 py-1.5 text-sm border border-neutral-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-indigo-500"
            aria-label={label}
          >
            <option value="">{label}</option>
            {options.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        ))}

        <button
          onClick={() => exportCsv(sorted)}
          className="ml-auto px-4 py-1.5 text-sm font-medium text-brand-indigo-600 border border-brand-indigo-300 rounded-lg hover:bg-brand-indigo-50 transition-colors"
          aria-label="Download CSV"
        >
          ⬇ Download CSV
        </button>
      </div>

      <div className="text-xs text-neutral-400">
        Showing {sorted.length} of {allEmployees.length} employees
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-neutral-200 shadow-xs">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-neutral-50 border-b border-neutral-200">
              {FIXED_COLUMNS.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={`px-3 py-2.5 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap ${
                    col.sortable ? 'cursor-pointer select-none hover:text-neutral-700' : ''
                  }`}
                  onClick={col.sortable ? () => handleSort(col.key as SortKey) : undefined}
                >
                  <span className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && (
                      <SortIcon active={sortKey === col.key} dir={sortDir} />
                    )}
                  </span>
                </th>
              ))}
            </tr>
            {/* Company averages row */}
            {companyAvgs && (
              <tr className="bg-brand-indigo-50 border-b border-brand-indigo-100 text-xs text-neutral-600 font-medium">
                <td className="px-3 py-2 text-brand-indigo-700 font-semibold" colSpan={2}>Company Average</td>
                <td className="px-3 py-2" />
                <td className="px-3 py-2" />
                <td className="px-3 py-2 font-bold text-neutral-800">{companyAvgs.score}</td>
                <td className="px-3 py-2">{companyAvgs.activeTime}</td>
                <td className="px-3 py-2">{companyAvgs.activeTime}</td>
                <td className="px-3 py-2">{companyAvgs.firstActivity}</td>
                <td className="px-3 py-2">{companyAvgs.lastActivity}</td>
                <td className="px-3 py-2">{companyAvgs.pctActive}</td>
                <td className="px-3 py-2" colSpan={7} />
              </tr>
            )}
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {sorted.map((emp) => {
              const scoreColor =
                emp.score >= 70
                  ? 'text-tier-high font-bold'
                  : emp.score >= 40
                  ? 'text-tier-avg font-semibold'
                  : 'text-tier-low font-semibold'
              return (
                <tr key={emp.name} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-3 py-2 font-medium text-neutral-900 whitespace-nowrap">{emp.name}</td>
                  <td className="px-3 py-2 text-neutral-600 whitespace-nowrap">{emp.role}</td>
                  <td className="px-3 py-2 text-neutral-500 whitespace-nowrap">{emp.manager}</td>
                  <td className="px-3 py-2 text-neutral-500 whitespace-nowrap">{emp.department}</td>
                  <td className={`px-3 py-2 ${scoreColor}`}>{emp.score}</td>
                  <td className="px-3 py-2 text-neutral-600">{emp.activeTimeMin}</td>
                  <td className="px-3 py-2 text-neutral-600">{emp.activeTime}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.firstActivity}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.lastActivity}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.pctActive}</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                      emp.workplace === 'Remote Only'
                        ? 'bg-mode-remote-bg text-mode-remote'
                        : emp.workplace === 'In-Office Only'
                        ? 'bg-mode-office-bg text-mode-office'
                        : 'bg-neutral-100 text-neutral-600'
                    }`}>
                      {emp.workplace}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-neutral-500">{emp.mostProdDay}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.leastProdDay}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.intMeetPct}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.extMeetPct}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.daysInOffice}</td>
                  <td className="px-3 py-2 text-neutral-500">{emp.daysRemote}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <div className="py-8 text-center text-sm text-neutral-400">
            No employees match your filters.
          </div>
        )}
      </div>
    </section>
  )
}
