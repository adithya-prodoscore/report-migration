'use client'

import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMonthlyKpiReportTier3 } from '@/hooks/useMonthlyKpiReportTier3'
import { PulseTab } from './PulseTab'
import { WorkforceTab } from './WorkforceTab'
import { DataTab } from './DataTab'

const qc = new QueryClient()

interface ReportProps {
  domainId: string
  startDate: string
  endDate: string
}

type TabKey = 'pulse' | 'workforce' | 'data'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'pulse', label: 'Pulse' },
  { key: 'workforce', label: 'Workforce' },
  { key: 'data', label: 'Data' },
]

function ReportInner({ domainId, startDate, endDate }: ReportProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('pulse')

  const effectiveDomain = domainId || '9'
  const effectiveStart = startDate || '2026-05-01'
  const effectiveEnd = endDate || '2026-05-29'

  const { data, isLoading, isError, error } = useMonthlyKpiReportTier3(
    effectiveDomain,
    effectiveStart,
    effectiveEnd,
  )

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-neutral-50">
        <div className="w-10 h-10 border-4 border-brand-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="mt-4 text-sm text-neutral-500">Loading Monthly KPI Report Tier 3…</p>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-neutral-50 px-6">
        <p className="text-tier-low font-semibold text-lg">Failed to load report</p>
        <p className="mt-2 text-sm text-neutral-500 max-w-sm text-center">
          {error instanceof Error ? error.message : 'An unexpected error occurred.'}
        </p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-kpi-screen-bg">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200 px-6 py-4">
        <div className="max-w-screen-xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h1 className="text-xl font-extrabold text-neutral-900">
                {data.CONFIG.report_title}
              </h1>
              <p className="text-sm text-neutral-500 mt-0.5">
                {data.COMPANY.name} · {data.COMPANY.period}
              </p>
            </div>
            <div className="flex gap-3 text-xs text-neutral-500">
              <span className="px-2.5 py-1 rounded-full bg-neutral-100 font-medium">
                Range: Monthly
              </span>
              <span className="px-2.5 py-1 rounded-full bg-neutral-100 font-medium">
                Domain {data.domain_id}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab bar */}
      <nav className="bg-white border-b border-neutral-200 px-6">
        <div className="max-w-screen-xl mx-auto flex gap-0">
          {TABS.filter((t) => data.CONFIG.tabs[t.key]).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-5 py-3.5 text-sm font-semibold transition-colors border-b-2 ${
                activeTab === tab.key
                  ? 'border-brand-indigo-600 text-brand-indigo-600'
                  : 'border-transparent text-neutral-500 hover:text-neutral-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Tab content */}
      <main className="max-w-screen-xl mx-auto px-6 py-8">
        {activeTab === 'pulse' && <PulseTab data={data} />}
        {activeTab === 'workforce' && <WorkforceTab data={data} />}
        {activeTab === 'data' && <DataTab data={data} />}
      </main>
    </div>
  )
}

export function MonthlyKpiReportTier3Report(props: ReportProps) {
  return (
    <QueryClientProvider client={qc}>
      <ReportInner {...props} />
    </QueryClientProvider>
  )
}
