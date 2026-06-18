'use client'
import { useState, useMemo } from 'react'
import type { MonthlyKpiReportTier5Data, EmployeeRecord } from '@/hooks/useMonthlyKpiReportTier5'

const FIXED_COLS = [
  { key: 'name', label: 'Name' },
  { key: 'role', label: 'Role' },
  { key: 'manager', label: 'Manager' },
  { key: 'department', label: 'Dept' },
  { key: 'score', label: 'Score' },
  { key: 'activeTime', label: 'Active Time' },
  { key: 'mon', label: 'Mon' },
  { key: 'tue', label: 'Tue' },
  { key: 'wed', label: 'Wed' },
  { key: 'thu', label: 'Thu' },
  { key: 'fri', label: 'Fri' },
  { key: 'firstActivity', label: 'First' },
  { key: 'lastActivity', label: 'Last' },
  { key: 'estAvailHours', label: 'Est Avail' },
  { key: 'pctActive', label: '% Active' },
  { key: 'pct1stHalf', label: '1st Half' },
  { key: 'pct2ndHalf', label: '2nd Half' },
  { key: 'intMeetPct', label: 'Int Meet %' },
  { key: 'extMeetPct', label: 'Ext Meet %' },
  { key: 'intMeetTime', label: 'Int Meet' },
  { key: 'extMeetTime', label: 'Ext Meet' },
  { key: 'popMeetTime', label: 'Peak Meet' },
  { key: 'mostProdDay', label: 'Best Day' },
  { key: 'leastProdDay', label: 'Worst Day' },
  { key: 'mostProdHour', label: 'Best Hour' },
  { key: 'workplace', label: 'Workplace' },
  { key: 'daysInOffice', label: 'In-Office' },
  { key: 'daysRemote', label: 'Remote' },
]

function scoreClass(score: unknown): string {
  const n = Number(score)
  if (n >= 70) return 'text-kpi-tier-high font-bold'
  if (n >= 40) return 'text-neutral-800'
  return 'text-kpi-tier-critical font-bold'
}

interface EmployeeDataTableProps {
  employees: EmployeeRecord[]
  toolMeta: MonthlyKpiReportTier5Data['TOOL_META']
  search: string
}

export function EmployeeDataTable({ employees, toolMeta, search }: EmployeeDataTableProps) {
  const [sortKey, setSortKey] = useState<string>('score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const toolCols = useMemo(
    () =>
      Object.entries(toolMeta).map(([k, v]) => ({
        key: k,
        label: v.name,
      })),
    [toolMeta],
  )

  const allCols = [...FIXED_COLS, ...toolCols]

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return employees.filter(
      (e) =>
        !q ||
        e.name.toLowerCase().includes(q) ||
        e.role.toLowerCase().includes(q) ||
        e.department.toLowerCase().includes(q) ||
        e.manager.toLowerCase().includes(q),
    )
  }, [employees, search])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      const an = typeof av === 'number' ? av : parseFloat(String(av))
      const bn = typeof bv === 'number' ? bv : parseFloat(String(bv))
      if (!isNaN(an) && !isNaN(bn)) {
        return sortDir === 'desc' ? bn - an : an - bn
      }
      return sortDir === 'desc'
        ? String(bv).localeCompare(String(av))
        : String(av).localeCompare(String(bv))
    })
  }, [filtered, sortKey, sortDir])

  function handleSort(key: string) {
    if (key === sortKey) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  function downloadCsv() {
    const headers = allCols.map((c) => c.label)
    const rows = sorted.map((e) => allCols.map((c) => JSON.stringify(e[c.key] ?? '-')))
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'monthly_kpi_report_tier5.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div className="flex items-center justify-end mb-3">
        <button
          onClick={downloadCsv}
          className="text-xs font-semibold px-3 py-1.5 rounded border border-neutral-300 text-neutral-700 hover:bg-neutral-50 transition-colors"
        >
          Download CSV
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-neutral-200 shadow-xs bg-white">
        <table className="min-w-full text-xs border-collapse">
          <thead className="bg-neutral-50 sticky top-0 z-10">
            <tr>
              {allCols.map((c) => (
                <th
                  key={c.key}
                  scope="col"
                  onClick={() => handleSort(c.key)}
                  className="px-3 py-2.5 text-left text-[11px] font-semibold text-neutral-500 uppercase tracking-wide whitespace-nowrap cursor-pointer hover:text-neutral-800 select-none border-b border-neutral-200"
                >
                  {c.label}
                  {sortKey === c.key && (
                    <span className="ml-1">{sortDir === 'desc' ? '▼' : '▲'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {sorted.map((e) => (
              <tr key={e.name} className="hover:bg-neutral-50 transition-colors">
                {allCols.map((c) => (
                  <td
                    key={c.key}
                    className={`px-3 py-2 whitespace-nowrap ${
                      c.key === 'score' ? scoreClass(e.score) : 'text-neutral-700'
                    }`}
                  >
                    {e[c.key] ?? '-'}
                  </td>
                ))}
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td
                  colSpan={allCols.length}
                  className="text-center py-8 text-sm text-neutral-400"
                >
                  No employees match your search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="mt-2 text-xs text-neutral-400">
        Showing {sorted.length} of {employees.length} employees
      </p>
    </div>
  )
}
