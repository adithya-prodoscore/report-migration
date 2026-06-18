import { EmployeeDataTable } from './EmployeeDataTable'
import type { MonthlyKpiReportTier3Data } from '@/hooks/useMonthlyKpiReportTier3'

interface DataTabProps {
  data: MonthlyKpiReportTier3Data
}

export function DataTab({ data }: DataTabProps) {
  return (
    <div>
      <EmployeeDataTable
        employees={data.ALL_EMPLOYEES}
        toolMeta={data.TOOL_META}
        companyAvgs={data.COMPANY_AVGS}
        roleAvgs={data.ROLE_AVGS}
      />
    </div>
  )
}
