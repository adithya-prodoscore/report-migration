'use client'

import ReactECharts from 'echarts-for-react'
import { RoleSummary } from '@/hooks/useMonthlyKpiReportTier7'

interface RoleBreakdownChartProps {
  roles: RoleSummary[]
}

export function RoleBreakdownChart({ roles }: RoleBreakdownChartProps) {
  // Source type (1.5I): "horizontalBar" → Lookup: "bar" + swap xAxis/yAxis → ECharts type: 'bar'
  const sorted = [...roles].sort((a, b) => a.avg - b.avg)

  const option = {
    textStyle: { fontFamily: 'var(--font-family-primary), sans-serif' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      textStyle: { color: '#111827', fontSize: 12 },
    },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value' as const, max: 100, axisLabel: { color: '#6D6D6D', fontSize: 11 } },
    yAxis: {
      type: 'category' as const,
      data: sorted.map((r) => r.role),
      axisLabel: { color: '#4F4F4F', fontSize: 11 },
      axisLine: { lineStyle: { color: '#E7E7E7' } },
    },
    series: [
      {
        name: 'Avg Score',
        type: 'bar' as const,
        data: sorted.map((r) => r.avg),
        barMaxWidth: 24,
        itemStyle: { color: '#1E86D9' },
        label: {
          show: true,
          position: 'right' as const,
          color: '#4F4F4F',
          fontSize: 11,
          formatter: '{c}',
        },
      },
    ],
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${Math.max(180, sorted.length * 36)}px`, width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
