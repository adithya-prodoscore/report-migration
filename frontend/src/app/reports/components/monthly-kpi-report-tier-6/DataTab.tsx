'use client'
import { useState } from 'react'
import { EmployeeDataTable } from './EmployeeDataTable'
import type { MonthlyKpiReportTier6Data } from '@/hooks/useMonthlyKpiReportTier6'

interface DataTabProps {
  data: MonthlyKpiReportTier6Data
}

export function DataTab({ data }: DataTabProps) {
  const [search, setSearch] = useState('')

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, role, dept, or manager…"
          className="flex-1 max-w-sm px-3 py-2 text-sm border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-indigo-500 bg-white"
          aria-label="Search employees"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="text-xs text-neutral-500 hover:text-neutral-800"
            aria-label="Clear search"
          >
            Clear
          </button>
        )}
      </div>

      <EmployeeDataTable
        employees={data.ALL_EMPLOYEES}
        toolMeta={data.TOOL_META}
        search={search}
      />
    </div>
  )
}
