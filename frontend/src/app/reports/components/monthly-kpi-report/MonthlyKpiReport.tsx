'use client'

import { useState } from 'react'
import useMonthlyKpiReport from '@/app/hooks/useMonthlyKpiReport'
import PulseSection from './PulseSection'
import WorkforceSection from './WorkforceSection'
import DataSection from './DataSection'

interface MonthlyKpiReportProps {
  domainId: string
  startDate: string
  endDate: string
}

export default function MonthlyKpiReport({
  domainId,
  startDate,
  endDate,
}: MonthlyKpiReportProps) {
  const { data, isLoading, isError, error } = useMonthlyKpiReport({
    domainId,
    startDate,
    endDate,
  })

  const [activeTab, setActiveTab] = useState<'pulse' | 'workforce' | 'data'>('pulse')
  const [workMode, setWorkMode] = useState<'all' | 'remote' | 'in-office'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand-blue-500"></div>
          <p className="mt-4 text-slate-600">Loading report...</p>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg bg-red-50 p-6 border border-red-200">
        <h3 className="text-lg font-semibold text-red-900">Failed to load report</h3>
        <p className="text-red-700 mt-2">{error?.message || 'Unknown error occurred'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">{data.CONFIG.report_title}</h1>
        <p className="text-slate-600 mt-2">Period: {data.COMPANY.period}</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-slate-200">
        <div className="flex gap-8">
          {[
            { id: 'pulse', label: 'Pulse' },
            { id: 'workforce', label: 'Workforce' },
            { id: 'data', label: 'Data' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-4 px-1 font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-brand-blue-500 text-brand-blue-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Work Mode Toggle */}
      {data.CONFIG.has_work_mode && (
        <div className="flex gap-2">
          {[
            { id: 'all', label: 'All Modes' },
            { id: 'in-office', label: 'In-Office' },
            { id: 'remote', label: 'Remote' },
          ].map(mode => (
            <button
              key={mode.id}
              onClick={() => setWorkMode(mode.id as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                workMode === mode.id
                  ? 'bg-brand-blue-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'pulse' && (
        <PulseSection
          company={data.COMPANY}
          roles={data.ROLES}
          needsAttention={data.NEEDS_ATTENTION}
          topPerformers={data.TOP_PERFORMERS}
          companyDaily={data.COMPANY_DAILY}
          companyDailyTime={data.COMPANY_DAILY_TIME}
        />
      )}

      {activeTab === 'workforce' && (
        <WorkforceSection
          roles={data.ROLES}
          roleDaily={data.ROLE_DAILY}
          roleAvgs={data.ROLE_AVGS}
          managerDaily={data.MANAGER_DAILY}
          managerAvgs={data.MANAGER_AVGS}
          departmentDaily={data.DEPARTMENT_DAILY}
          departmentAvgs={data.DEPARTMENT_AVGS}
          allEmployees={data.ALL_EMPLOYEES}
          workMode={workMode}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />
      )}

      {activeTab === 'data' && (
        <DataSection
          allEmployees={data.ALL_EMPLOYEES}
          companyAvgs={data.COMPANY_AVGS}
          roleAvgs={data.ROLE_AVGS}
          managerAvgs={data.MANAGER_AVGS}
          departmentAvgs={data.DEPARTMENT_AVGS}
          toolMeta={data.TOOL_META}
        />
      )}
    </div>
  )
}
