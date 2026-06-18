// DataTab — thin wrapper that renders the EmployeeDataTable within the Data tab.
// HTML source: Data tab section
// Interactions: see EmployeeDataTable (search, sort, CSV download)

import { EmployeeDataTable } from './EmployeeDataTable'
import type { MonthlyKpiReportTier4Data } from '@/hooks/useMonthlyKpiReportTier4'

interface DataTabProps {
  data: MonthlyKpiReportTier4Data
}

export function DataTab({ data }: DataTabProps) {
  return (
    <div>
      <h2 className="text-sm font-extrabold text-neutral-500 uppercase tracking-wide mb-4">
        All Employees — Full Metrics
      </h2>
      <EmployeeDataTable
        employees={data.ALL_EMPLOYEES}
        companyAvgs={data.COMPANY_AVGS}
        toolMeta={data.TOOL_META}
      />
    </div>
  )
}
