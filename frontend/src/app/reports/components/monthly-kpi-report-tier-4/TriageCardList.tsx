'use client'
// TriageCardList — expandable employee triage cards for NEEDS_ATTENTION,
// INACTIVE, and TOP_PERFORMERS sections of the Pulse tab.
// HTML source: Pulse tab triage cards section
// Chart type (sparklines): line → ECharts type: 'line' (LOCKED)
// Interactions: expand/collapse per card, tooltip on sparkline

import { useState } from 'react'
import ReactECharts from 'echarts-for-react'

export interface DailyScore {
  day: string
  score: number
}

export interface TriageEmployee {
  name: string
  manager: string
  role: string
  score: number
  scoreGap: number
  roleAvg: number
  activeTime: string
  timeGap: string
  roleAvgTime: string
  daily: DailyScore[]
  dailyTime: string[]
  firstActivity?: string
  lastActivity?: string
  pctActive?: string
  mostProductiveDay?: string
  leastProductiveDay?: string
  reason?: string   // INACTIVE only
  gaps?: unknown[]
  standouts?: unknown[]
}

interface SparklineProps {
  data: DailyScore[]
  color: string
}

function Sparkline({ data, color }: SparklineProps) {
  const option = {
    textStyle: { fontFamily: 'var(--font-family-primary), sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      textStyle: { color: '#111827', fontSize: 11 },
    },
    grid: { left: 0, right: 0, top: 4, bottom: 0 },
    xAxis: { type: 'category', show: false, data: data.map((d) => d.day) },
    yAxis: { type: 'value', show: false, min: 0, max: 100 },
    series: [
      {
        type: 'line',
        smooth: true,
        data: data.map((d) => d.score),
        lineStyle: { color, width: 2 },
        itemStyle: { color },
        symbol: 'circle',
        symbolSize: 4,
        areaStyle: { color, opacity: 0.1 },
      },
    ],
  }
  return (
    <ReactECharts
      option={option}
      style={{ height: '60px', width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}

function scoreTierColor(score: number) {
  if (score >= 70) return '#16a34a'
  if (score >= 40) return '#2563eb'
  return '#dc2626'
}

function scoreTierBg(score: number) {
  if (score >= 70) return 'bg-tier-high-bg text-tier-high'
  if (score >= 40) return 'bg-tier-avg-bg text-tier-avg'
  return 'bg-tier-low-bg text-tier-low'
}

interface TriageCardProps {
  employee: TriageEmployee
  variant: 'attention' | 'inactive' | 'top'
}

function TriageCard({ employee: e, variant }: TriageCardProps) {
  const [expanded, setExpanded] = useState(false)
  const color = scoreTierColor(e.score)

  const headerBg =
    variant === 'attention'
      ? 'border-l-4 border-status-attention'
      : variant === 'top'
        ? 'border-l-4 border-status-top'
        : 'border-l-4 border-status-inactive'

  return (
    <div className={`bg-white rounded-xl border border-neutral-200 shadow-xs overflow-hidden ${headerBg}`}>
      {/* Card header — always visible */}
      <button
        className="w-full text-left px-5 py-4 flex items-center gap-4"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        {/* Score badge */}
        <div
          className={`w-11 h-11 rounded-full flex items-center justify-center text-sm font-extrabold shrink-0 ${scoreTierBg(e.score)}`}
        >
          {e.score}
        </div>

        {/* Name / role / manager */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-neutral-900 truncate">{e.name}</p>
          <p className="text-xs text-neutral-500 truncate">
            {e.role} · {e.manager}
          </p>
        </div>

        {/* Active time */}
        <div className="hidden sm:block text-right shrink-0">
          <p className="text-xs text-neutral-500">Active time</p>
          <p className="text-sm font-semibold text-neutral-800">{e.activeTime}</p>
        </div>

        {/* Role avg gap */}
        <div className="hidden md:block text-right shrink-0">
          <p className="text-xs text-neutral-500">vs Role avg</p>
          <p
            className={`text-sm font-semibold ${
              e.scoreGap >= 0 ? 'text-tier-high' : 'text-tier-low'
            }`}
          >
            {e.scoreGap >= 0 ? `+${e.scoreGap}` : e.scoreGap}
          </p>
        </div>

        {/* Expand chevron */}
        <svg
          className={`w-4 h-4 text-neutral-400 shrink-0 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-neutral-100 px-5 py-4 space-y-4">
          {/* Sparkline */}
          <div>
            <p className="text-xs font-semibold text-neutral-500 mb-1">Daily Score Trend (Mon–Fri)</p>
            <Sparkline data={e.daily} color={color} />
          </div>

          {/* Grid of metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <p className="text-neutral-400 uppercase tracking-wide font-semibold">Role Avg</p>
              <p className="text-neutral-800 font-semibold mt-0.5">{e.roleAvg}</p>
            </div>
            <div>
              <p className="text-neutral-400 uppercase tracking-wide font-semibold">Role Avg Time</p>
              <p className="text-neutral-800 font-semibold mt-0.5">{e.roleAvgTime}</p>
            </div>
            <div>
              <p className="text-neutral-400 uppercase tracking-wide font-semibold">Time Gap</p>
              <p className={`font-semibold mt-0.5 ${e.timeGap?.startsWith('+') ? 'text-tier-high' : 'text-tier-low'}`}>
                {e.timeGap}
              </p>
            </div>
            {e.firstActivity && (
              <div>
                <p className="text-neutral-400 uppercase tracking-wide font-semibold">First Activity</p>
                <p className="text-neutral-800 font-semibold mt-0.5">{e.firstActivity}</p>
              </div>
            )}
            {e.lastActivity && (
              <div>
                <p className="text-neutral-400 uppercase tracking-wide font-semibold">Last Activity</p>
                <p className="text-neutral-800 font-semibold mt-0.5">{e.lastActivity}</p>
              </div>
            )}
            {e.pctActive && (
              <div>
                <p className="text-neutral-400 uppercase tracking-wide font-semibold">% Active</p>
                <p className="text-neutral-800 font-semibold mt-0.5">{e.pctActive}</p>
              </div>
            )}
            {e.mostProductiveDay && (
              <div>
                <p className="text-neutral-400 uppercase tracking-wide font-semibold">Best Day</p>
                <p className="text-neutral-800 font-semibold mt-0.5">{e.mostProductiveDay}</p>
              </div>
            )}
            {e.leastProductiveDay && (
              <div>
                <p className="text-neutral-400 uppercase tracking-wide font-semibold">Weakest Day</p>
                <p className="text-neutral-800 font-semibold mt-0.5">{e.leastProductiveDay}</p>
              </div>
            )}
            {e.reason && (
              <div className="col-span-2 sm:col-span-3">
                <p className="text-neutral-400 uppercase tracking-wide font-semibold">Reason</p>
                <p className="text-neutral-600 mt-0.5">{e.reason}</p>
              </div>
            )}
          </div>

          {/* Daily time labels */}
          {e.dailyTime && e.dailyTime.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-neutral-500 mb-1">Daily Active Time</p>
              <div className="flex gap-3">
                {e.dailyTime.map((t, i) => (
                  <div key={i} className="text-center">
                    <p className="text-xs text-neutral-400">{e.daily[i]?.day ?? ''}</p>
                    <p className="text-xs font-semibold text-neutral-700">{t}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface TriageCardListProps {
  needsAttention: TriageEmployee[]
  inactive: TriageEmployee[]
  topPerformers: TriageEmployee[]
}

export function TriageCardList({ needsAttention, inactive, topPerformers }: TriageCardListProps) {
  return (
    <div className="space-y-8">
      {/* Needs Attention */}
      {needsAttention.length > 0 && (
        <section>
          <h3 className="text-sm font-extrabold text-neutral-700 uppercase tracking-wide mb-3">
            Needs Attention
            <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-status-attention-bg text-status-attention">
              {needsAttention.length}
            </span>
          </h3>
          <div className="space-y-2">
            {needsAttention.map((e) => (
              <TriageCard key={e.name} employee={e} variant="attention" />
            ))}
          </div>
        </section>
      )}

      {/* Inactive / PTO */}
      {inactive.length > 0 && (
        <section>
          <h3 className="text-sm font-extrabold text-neutral-700 uppercase tracking-wide mb-3">
            Inactive / PTO
            <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-status-inactive-bg text-status-inactive">
              {inactive.length}
            </span>
          </h3>
          <div className="space-y-2">
            {inactive.map((e) => (
              <TriageCard key={e.name} employee={e} variant="inactive" />
            ))}
          </div>
        </section>
      )}

      {/* Top Performers */}
      {topPerformers.length > 0 && (
        <section>
          <h3 className="text-sm font-extrabold text-neutral-700 uppercase tracking-wide mb-3">
            Top Performers
            <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-status-top-bg text-status-top">
              {topPerformers.length}
            </span>
          </h3>
          <div className="space-y-2">
            {topPerformers.map((e) => (
              <TriageCard key={e.name} employee={e} variant="top" />
            ))}
          </div>
        </section>
      )}

      {needsAttention.length === 0 && inactive.length === 0 && topPerformers.length === 0 && (
        <p className="text-sm text-neutral-400 text-center py-8">
          No triage data available for this period.
        </p>
      )}
    </div>
  )
}
