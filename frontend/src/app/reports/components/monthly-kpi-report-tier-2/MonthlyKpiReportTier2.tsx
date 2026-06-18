'use client'

import { useState } from 'react'
import useMonthlyKpiReportTier2 from '@/app/hooks/useMonthlyKpiReportTier2'
import { PulseSectionTier2 } from './PulseSectionTier2'
import { WorkforceSectionTier2 } from './WorkforceSectionTier2'
import { DataSectionTier2 } from './DataSectionTier2'

type Tab = 'pulse' | 'workforce' | 'data'

interface MonthlyKpiReportTier2Props {
  domainId?: string
  startDate?: string
  endDate?: string
}

const DEFAULT_DOMAIN = '9'
const DEFAULT_START = '2026-05-01'
const DEFAULT_END = '2026-05-29'

function TabBar({
  active,
  onChange,
  tabs,
}: {
  active: Tab
  onChange: (t: Tab) => void
  tabs: { id: Tab; label: string; enabled: boolean }[]
}) {
  return (
    <nav className="flex gap-1 border-b border-neutral-200" aria-label="Report tabs">
      {tabs
        .filter((t) => t.enabled)
        .map((t) => (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            className={`px-5 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
              active === t.id
                ? 'border-brand-indigo-500 text-brand-indigo-600'
                : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
            }`}
            aria-current={active === t.id ? 'page' : undefined}
          >
            {t.label}
          </button>
        ))}
    </nav>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-neutral-200 rounded w-64" />
      <div className="grid grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-neutral-200 rounded-xl" />
        ))}
      </div>
      <div className="h-40 bg-neutral-200 rounded-xl" />
      <div className="h-64 bg-neutral-200 rounded-xl" />
    </div>
  )
}

function ErrorState({ error }: { error: Error }) {
  return (
    <div className="rounded-xl border border-neutral-200 p-8 text-center">
      <div className="text-tier-critical text-lg font-semibold mb-2">
        Failed to load report
      </div>
      <div className="text-sm text-neutral-500">{error.message}</div>
      <p className="mt-3 text-xs text-neutral-400">
        Check that the backend is running and USE_MOCK_DATA is set correctly.
      </p>
    </div>
  )
}

export function MonthlyKpiReportTier2({
  domainId = DEFAULT_DOMAIN,
  startDate = DEFAULT_START,
  endDate = DEFAULT_END,
}: MonthlyKpiReportTier2Props) {
  const [activeTab, setActiveTab] = useState<Tab>('pulse')

  const { data, isLoading, isError, error } = useMonthlyKpiReportTier2({
    domainId: domainId || DEFAULT_DOMAIN,
    startDate: startDate || DEFAULT_START,
    endDate: endDate || DEFAULT_END,
  })

  const config = data?.CONFIG

  const tabs: { id: Tab; label: string; enabled: boolean }[] = [
    { id: 'pulse', label: 'Pulse', enabled: config?.tabs?.pulse ?? true },
    { id: 'workforce', label: 'Workforce', enabled: config?.tabs?.workforce ?? true },
    { id: 'data', label: 'Data', enabled: config?.tabs?.data ?? true },
  ]

  return (
    <main className="max-w-7xl mx-auto px-4 py-10 sm:px-6 lg:px-8 w-full">
      {/* Report Header */}
      <div className="mb-6 border-b border-neutral-200 pb-5">
        <h1 className="text-2xl font-extrabold tracking-tight text-neutral-950 sm:text-3xl">
          Monthly KPI Report Tier 2
        </h1>
        {data?.COMPANY && (
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-neutral-500">
            <span>{data.COMPANY.name}</span>
            <span>·</span>
            <span>{data.COMPANY.period}</span>
            <span>·</span>
            <span>{data.COMPANY.totalEmployees} employees</span>
          </div>
        )}
      </div>

      {/* Tab Bar */}
      {!isLoading && !isError && data && (
        <div className="mb-6">
          <TabBar active={activeTab} onChange={setActiveTab} tabs={tabs} />
        </div>
      )}

      {/* Content Area */}
      {isLoading && <LoadingSkeleton />}

      {isError && error && <ErrorState error={error} />}

      {!isLoading && !isError && data && (
        <>
          {activeTab === 'pulse' && <PulseSectionTier2 data={data} />}
          {activeTab === 'workforce' && <WorkforceSectionTier2 data={data} />}
          {activeTab === 'data' && <DataSectionTier2 data={data} />}
        </>
      )}
    </main>
  )
}
