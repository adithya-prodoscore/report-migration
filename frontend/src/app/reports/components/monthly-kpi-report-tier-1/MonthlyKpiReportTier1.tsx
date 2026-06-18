'use client'

import { useState, useMemo } from 'react'
import useMonthlyKpiReportTier1 from '@/app/hooks/useMonthlyKpiReportTier1'
import type { EmployeeRecordT1 } from '@/app/hooks/useMonthlyKpiReportTier1'
import { KpiCards } from './KpiCards'
import { ProportionBar } from './ProportionBar'
import { CalloutSection } from './CalloutSection'
import { EmployeeTable } from './EmployeeTable'
import { EmployeeModal } from './EmployeeModal'

type SortKey = 'name' | 'score' | 'roleAvg' | 'delta' | 'activeTime' | 'status'
type SortDir = 'asc' | 'desc'
type Status = 'needs-attention' | 'inactive' | 'most-engaged' | 'on-track' | 'all'

interface MonthlyKpiReportTier1Props {
  domainId?: string
  startDate?: string
  endDate?: string
}

const DEFAULT_DOMAIN = '9'
const DEFAULT_START = '2026-05-01'
const DEFAULT_END = '2026-05-29'
const PAGE_SIZE = 25

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse px-4 py-10 max-w-7xl mx-auto">
      <div className="h-8 bg-kpi-gray-100 rounded w-72" />
      <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-32 bg-kpi-gray-100 rounded-xl" />
        ))}
      </div>
      <div className="h-3.5 bg-kpi-gray-100 rounded-full" />
      <div className="h-80 bg-kpi-gray-100 rounded-xl" />
      <div className="h-64 bg-kpi-gray-100 rounded-xl" />
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-kpi-gray-100 p-10 text-center max-w-lg mx-auto mt-10">
      <div className="text-kpi-tier-critical text-lg font-semibold mb-2">Failed to load report</div>
      <div className="text-sm text-kpi-gray-500">{message}</div>
      <p className="mt-3 text-xs text-kpi-gray-400">
        Check that the backend is running and NEXT_PUBLIC_API_BASE_URL is set correctly.
      </p>
    </div>
  )
}

function sortEmployees(employees: EmployeeRecordT1[], key: SortKey, dir: SortDir): EmployeeRecordT1[] {
  return [...employees].sort((a, b) => {
    let av: number | string
    let bv: number | string
    switch (key) {
      case 'name':       av = a.name;       bv = b.name;       break
      case 'score':      av = a.score;      bv = b.score;      break
      case 'roleAvg':    av = a.roleAvg;    bv = b.roleAvg;    break
      case 'delta':      av = parseInt(a.delta); bv = parseInt(b.delta); break
      case 'activeTime': av = a.activeTime; bv = b.activeTime; break
      case 'status':     av = a.status;     bv = b.status;     break
      default:           av = a.score;      bv = b.score
    }
    if (av < bv) return dir === 'asc' ? -1 : 1
    if (av > bv) return dir === 'asc' ? 1 : -1
    return 0
  })
}

export function MonthlyKpiReportTier1({
  domainId = DEFAULT_DOMAIN,
  startDate = DEFAULT_START,
  endDate = DEFAULT_END,
}: MonthlyKpiReportTier1Props) {
  // Filter state — one per dimension; empty = "all"
  const [filterDept,     setFilterDept]     = useState<Set<string>>(new Set())
  const [filterRole,     setFilterRole]     = useState<Set<string>>(new Set())
  const [filterManager,  setFilterManager]  = useState<Set<string>>(new Set())
  const [filterEmployee, setFilterEmployee] = useState<Set<string>>(new Set())
  const [filterStatus,   setFilterStatus]   = useState<Status | null>(null)

  // Sort state
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  // Pagination
  const [page, setPage] = useState(1)

  // Modal
  const [modalEmployee, setModalEmployee] = useState<EmployeeRecordT1 | null>(null)

  const { data, isLoading, isError, error } = useMonthlyKpiReportTier1({
    domainId: domainId || DEFAULT_DOMAIN,
    startDate: startDate || DEFAULT_START,
    endDate: endDate || DEFAULT_END,
  })

  // ---- Filter strip dropdowns (multi-select open state) ----
  const [openFilter, setOpenFilter] = useState<string | null>(null)

  // ---- Derived data ----
  const allEmployees = data?.employees ?? []

  const filteredEmployees = useMemo(() => {
    let list = allEmployees
    if (filterDept.size > 0)     list = list.filter(e => filterDept.has(e.dept))
    if (filterRole.size > 0)     list = list.filter(e => filterRole.has(e.role))
    if (filterManager.size > 0)  list = list.filter(e => filterManager.has(e.manager))
    if (filterEmployee.size > 0) list = list.filter(e => filterEmployee.has(e.name))
    if (filterStatus && filterStatus !== 'all') list = list.filter(e => e.status === filterStatus)
    return list
  }, [allEmployees, filterDept, filterRole, filterManager, filterEmployee, filterStatus])

  const sortedEmployees = useMemo(
    () => sortEmployees(filteredEmployees, sortKey, sortDir),
    [filteredEmployees, sortKey, sortDir]
  )

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
    setPage(1)
  }

  function handleKpiClick(status: Status) {
    setFilterStatus(prev => prev === status ? null : status)
    setPage(1)
  }

  function resetFilters() {
    setFilterDept(new Set())
    setFilterRole(new Set())
    setFilterManager(new Set())
    setFilterEmployee(new Set())
    setFilterStatus(null)
    setPage(1)
  }

  const anyFilterActive = filterDept.size > 0 || filterRole.size > 0 || filterManager.size > 0 || filterEmployee.size > 0 || filterStatus !== null

  const header = data?.header
  const filterOptions = data?.filter_options

  // --- Filter strip multi-select toggle helper ---
  function toggleFilter(set: Set<string>, setFn: (s: Set<string>) => void, value: string) {
    const next = new Set(set)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    setFn(next)
    setPage(1)
  }

  function FilterDropdown({
    label,
    filterKey,
    options,
    selected,
    onToggle,
    placeholder,
  }: {
    label: string
    filterKey: string
    options: string[]
    selected: Set<string>
    onToggle: (v: string) => void
    placeholder: string
  }) {
    const isOpen = openFilter === filterKey
    const hasSelection = selected.size > 0
    return (
      <div className="flex flex-col gap-1 flex-1 min-w-[160px] relative">
        <span className="text-[10px] font-bold text-kpi-gray-500 uppercase tracking-wider">{label}</span>
        <button
          type="button"
          className={[
            'flex items-center justify-between gap-2 px-3 py-2 rounded-lg border h-[38px] text-[13px] font-medium transition-all',
            hasSelection
              ? 'bg-kpi-blue-50 border-kpi-blue-400 text-kpi-blue-700'
              : 'bg-kpi-white border-kpi-gray-200 text-kpi-gray-800 hover:border-kpi-blue-300',
            isOpen ? 'border-kpi-blue-500 shadow-[0_0_0_3px_var(--color-kpi-blue-50)]' : '',
          ].join(' ')}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          onClick={(e) => { e.stopPropagation(); setOpenFilter(isOpen ? null : filterKey) }}
        >
          <span className="flex-1 text-left truncate">
            {hasSelection
              ? selected.size === 1
                ? Array.from(selected)[0]
                : `${selected.size} selected`
              : placeholder}
          </span>
          <svg className={`w-2.5 h-2.5 flex-shrink-0 stroke-current fill-none transition-transform ${isOpen ? 'rotate-180' : ''}`} viewBox="0 0 10 6" strokeWidth={1.8} strokeLinecap="round" aria-hidden="true">
            <path d="M1 1l4 4 4-4" />
          </svg>
        </button>
        {isOpen && (
          <div className="absolute top-full left-0 right-0 min-w-[240px] z-50 mt-1 bg-kpi-white border border-kpi-gray-200 rounded-lg shadow-shadow-lg max-h-[300px] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            {options.map(opt => (
              <div
                key={opt}
                role="option"
                aria-selected={selected.has(opt)}
                className="flex items-center gap-2.5 px-3.5 py-2 text-[13px] text-kpi-gray-800 cursor-pointer hover:bg-kpi-blue-50"
                onClick={() => onToggle(opt)}
              >
                <span className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 border-[1.5px] ${selected.has(opt) ? 'bg-kpi-blue-500 border-kpi-blue-500' : 'border-kpi-gray-300 bg-kpi-white'}`}>
                  {selected.has(opt) && (
                    <svg className="w-2.5 h-2.5 stroke-white fill-none" viewBox="0 0 24 24" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </span>
                <span className="flex-1 truncate">{opt}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Close dropdowns on outside click
  if (typeof window !== 'undefined') {
    // this is handled by parent click
  }

  return (
    <div
      className="flex flex-col h-screen overflow-hidden bg-kpi-screen-bg"
      onClick={() => setOpenFilter(null)}
    >
      {/* ── TOP NAV ── */}
      {header && (
        <nav className="flex-shrink-0 bg-kpi-white border-b border-kpi-gray-100 flex items-center justify-between px-8 h-[72px]">
          <div className="flex items-center gap-3">
            <div className="flex flex-col gap-0.5">
              <span className="text-[16px] font-bold text-kpi-gray-950 leading-tight tracking-tight">
                {header.title}
              </span>
              <span className="text-[12px] text-kpi-blue-500 font-medium">{header.breadcrumb}</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-baseline border border-kpi-gray-200 rounded-lg overflow-hidden text-[11px] font-semibold text-kpi-gray-600">
              <div className="px-5 py-2 border-r border-kpi-gray-200">
                <span className="block text-[9px] uppercase tracking-widest text-kpi-gray-400 font-bold mb-0.5">Range</span>
                {header.dateRange}
              </div>
              <div className="px-5 py-2 border-r border-kpi-gray-200">
                <span className="block text-[9px] uppercase tracking-widest text-kpi-gray-400 font-bold mb-0.5">From</span>
                {header.dateFrom}
              </div>
              <div className="px-5 py-2">
                <span className="block text-[9px] uppercase tracking-widest text-kpi-gray-400 font-bold mb-0.5">To</span>
                {header.dateTo}
              </div>
            </div>
          </div>
        </nav>
      )}

      {/* ── FILTER STRIP ── */}
      <div className="flex-shrink-0 bg-kpi-white border-b border-kpi-gray-100 px-8 py-3.5 flex items-end gap-3 relative">
        {filterOptions && (
          <>
            <FilterDropdown
              label="Department" filterKey="dept"
              options={filterOptions.dept} selected={filterDept}
              onToggle={v => toggleFilter(filterDept, setFilterDept, v)}
              placeholder="All departments"
            />
            <FilterDropdown
              label="Role" filterKey="role"
              options={filterOptions.role} selected={filterRole}
              onToggle={v => toggleFilter(filterRole, setFilterRole, v)}
              placeholder="All roles"
            />
            <FilterDropdown
              label="Manager team" filterKey="manager"
              options={filterOptions.manager} selected={filterManager}
              onToggle={v => toggleFilter(filterManager, setFilterManager, v)}
              placeholder="All manager teams"
            />
            <FilterDropdown
              label="Employee" filterKey="employee"
              options={filterOptions.employee} selected={filterEmployee}
              onToggle={v => toggleFilter(filterEmployee, setFilterEmployee, v)}
              placeholder="All employees"
            />
          </>
        )}
        {/* Reset */}
        <div className="flex items-end flex-shrink-0">
          <button
            type="button"
            disabled={!anyFilterActive}
            className={[
              'h-[38px] px-4 rounded-lg border text-[13px] font-semibold inline-flex items-center gap-1.5 transition-all',
              anyFilterActive
                ? 'text-kpi-blue-600 border-kpi-blue-300 bg-kpi-white cursor-pointer hover:bg-kpi-blue-50 hover:border-kpi-blue-500'
                : 'text-kpi-gray-400 border-kpi-gray-200 cursor-not-allowed',
            ].join(' ')}
            onClick={resetFilters}
          >
            <svg className="w-3.5 h-3.5 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" aria-hidden="true">
              <path d="M1 4v6h6M23 20v-6h-6" /><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
            </svg>
            Reset
          </button>
        </div>
      </div>

      {/* ── CONTENT ── */}
      <div className="flex-1 overflow-y-auto px-8 py-8 bg-kpi-screen-bg">
        {isLoading && <LoadingSkeleton />}
        {isError && <ErrorState message={error?.message ?? 'Unknown error'} />}
        {!isLoading && !isError && data && (
          <>
            {/* KPI Cards */}
            <KpiCards
              employees={filteredEmployees}
              activeStatus={filterStatus}
              onStatusClick={handleKpiClick}
            />
            {/* Proportion bar */}
            <ProportionBar employees={filteredEmployees} />
            {/* Zone 2 — called-out employees */}
            <CalloutSection employees={filteredEmployees} />
            {/* Employee table */}
            <EmployeeTable
              employees={sortedEmployees}
              onRowClick={setModalEmployee}
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={handleSort}
              page={page}
              pageSize={PAGE_SIZE}
              onPageChange={setPage}
            />
          </>
        )}
      </div>

      {/* ── METHODOLOGY TAB (right-edge) ── */}
      {data && (
        <MethodologyDrawer />
      )}

      {/* ── EMPLOYEE MODAL ── */}
      <EmployeeModal employee={modalEmployee} onClose={() => setModalEmployee(null)} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Methodology drawer (right-edge vertical tab + slide-in panel)
// ---------------------------------------------------------------------------
function MethodologyDrawer() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        type="button"
        className="fixed top-[200px] right-0 z-[60] inline-flex flex-col items-center px-2 py-4 border border-r-0 border-kpi-gray-100 rounded-l-[10px] bg-kpi-white text-kpi-gray-700 text-[12px] font-bold hover:text-kpi-blue-600 hover:bg-kpi-gray-50 transition-colors"
        aria-controls="methodology-drawer"
        aria-expanded={open}
        title="How employees are flagged"
        onClick={() => setOpen(true)}
      >
        <span style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', letterSpacing: '0.04em', lineHeight: 1 }}>
          Methodology
        </span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-[70] bg-[rgba(20,20,20,0.32)] transition-opacity" onClick={() => setOpen(false)} aria-hidden="true" />
          <aside
            id="methodology-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Methodology"
            className="fixed top-0 right-0 bottom-0 w-1/2 max-w-[92vw] min-w-[380px] bg-kpi-white z-[80] flex flex-col shadow-shadow-xl"
          >
            <div className="flex-shrink-0 px-7 pt-5 pb-4 border-b border-kpi-gray-100 relative">
              <div className="text-[10px] font-bold uppercase tracking-wider text-kpi-blue-500 mb-1">Methodology</div>
              <h2 className="text-[19px] font-extrabold text-kpi-gray-950 leading-snug tracking-tight">How employees are flagged</h2>
              <button
                type="button"
                className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg bg-kpi-gray-50 text-kpi-gray-600 hover:bg-kpi-gray-100 hover:text-kpi-gray-900"
                aria-label="Close methodology"
                onClick={() => setOpen(false)}
              >
                <svg className="w-4 h-4 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" aria-hidden="true">
                  <path d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-7 py-6">
              <div className="max-w-[620px] space-y-5 text-[13px] text-kpi-gray-600 leading-relaxed">
                <p>This report scans everyone's activity for the selected dates and points out the handful of people worth a closer look. Most people won't be flagged at all.</p>
                <div>
                  <h3 className="text-[13px] font-bold text-kpi-gray-950 mb-1">Compared to peers, not a fixed number</h3>
                  <p>Everyone is compared to others in the same role, not to one company-wide cutoff. A score of 77 means something very different in a role that averages 37 than in one that averages 70.</p>
                </div>
                <div>
                  <h3 className="text-[13px] font-bold text-kpi-gray-950 mb-1">Needs Attention</h3>
                  <p>People sitting below their role's typical level, on their score, their active time, or both. Someone keeping pace with peers on both is never flagged here.</p>
                </div>
                <div>
                  <h3 className="text-[13px] font-bold text-kpi-gray-950 mb-1">Inactive</h3>
                  <p>People with too little recorded activity to judge fairly. Someone shows up here when they have: no recorded activity at all, activity on fewer than half the days, a low score with under an hour of active time, or under 20 minutes of active time overall.</p>
                </div>
                <div>
                  <h3 className="text-[13px] font-bold text-kpi-gray-950 mb-1">Most Engaged</h3>
                  <p>People clearly above their role's typical level. Only those at or above their role's average score are considered.</p>
                </div>
              </div>
            </div>
          </aside>
        </>
      )}
    </>
  )
}
