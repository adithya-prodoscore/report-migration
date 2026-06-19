'use client'

import { useState } from 'react'
import { useMonthlyKpiReportTier7 } from '@/hooks/useMonthlyKpiReportTier7'
import { PulseTab } from './PulseTab'
import { WorkforceTab } from './WorkforceTab'
import { DataTab } from './DataTab'

interface MonthlyKpiReportTier7ReportProps {
  domainId: string
  startDate: string
  endDate: string
}

type TabId = 'pulse' | 'workforce' | 'data'

const TAB_LABELS: Record<TabId, string> = {
  pulse: 'Pulse',
  workforce: 'Workforce',
  data: 'Data',
}

export function MonthlyKpiReportTier7Report({
  domainId,
  startDate,
  endDate,
}: MonthlyKpiReportTier7ReportProps) {
  const { data, isLoading, isError, error } = useMonthlyKpiReportTier7(
    domainId,
    startDate,
    endDate,
  )
  const [activeTab, setActiveTab] = useState<TabId>('pulse')

  // -- Loading state --
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-10 h-10 border-4 border-kpi-blue-200 border-t-kpi-blue-500 rounded-full animate-spin" />
        <p className="text-sm text-kpi-gray-500">Loading Monthly KPI Report Tier 7…</p>
      </div>
    )
  }

  // -- Error state --
  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] gap-2">
        <p className="text-base font-semibold text-kpi-tier-critical">Failed to load report</p>
        <p className="text-sm text-kpi-gray-500">
          {error instanceof Error ? error.message : 'Unknown error'}
        </p>
        <p className="text-xs text-kpi-gray-400 mt-2">
          Check that the backend is running and USE_MOCK_DATA=true is set if BigQuery is unavailable.
        </p>
      </div>
    )
  }

  const company = data.COMPANY
  const enabledTabs = (Object.keys(TAB_LABELS) as TabId[]).filter(
    (t) => data.CONFIG?.tabs?.[t] !== false,
  )

  return (
    <div className="min-h-screen bg-kpi-screen-bg">
      {/* Report header */}
      <div className="bg-neutral-0 border-b border-neutral-200 shadow-xs">
        <div className="max-w-screen-2xl mx-auto px-6 py-4">
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <h1 className="text-lg font-bold text-neutral-900">Monthly KPI Report Tier 7</h1>
              <p className="text-sm text-kpi-gray-500">{company.name}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded-full bg-kpi-gray-100 text-kpi-gray-700 font-medium">
                Range: Monthly
              </span>
              <span className="px-2.5 py-1 rounded-full bg-kpi-gray-100 text-kpi-gray-700 font-medium">
                From: {company.period.split(' - ')[0]}
              </span>
              <span className="px-2.5 py-1 rounded-full bg-kpi-gray-100 text-kpi-gray-700 font-medium">
                To: {company.period.split(' - ')[1]}
              </span>
              {data.CONFIG?.working_day_gates && (
                <span className="px-2.5 py-1 rounded-full bg-kpi-blue-50 text-kpi-blue-600 font-medium">
                  6-Gate Working Days
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Tab bar */}
        <div className="max-w-screen-2xl mx-auto px-6">
          <div className="flex border-b-0">
            {enabledTabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-kpi-blue-500 text-kpi-blue-600'
                    : 'border-transparent text-kpi-gray-500 hover:text-neutral-800 hover:border-neutral-300'
                }`}
              >
                {TAB_LABELS[tab]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab content */}
      <div className="max-w-screen-2xl mx-auto px-6 py-8">
        {activeTab === 'pulse' && (
          <PulseTab
            company={company}
            roles={data.ROLES}
            companyDaily={data.COMPANY_DAILY}
            companyDailyTime={data.COMPANY_DAILY_TIME}
            needsAttention={data.NEEDS_ATTENTION}
            inactive={data.INACTIVE}
            topPerformers={data.TOP_PERFORMERS}
          />
        )}
        {activeTab === 'workforce' && (
          <WorkforceTab
            roles={data.ROLES}
            data={data}
          />
        )}
        {activeTab === 'data' && <DataTab data={data} />}
      </div>
    </div>
  )
}
