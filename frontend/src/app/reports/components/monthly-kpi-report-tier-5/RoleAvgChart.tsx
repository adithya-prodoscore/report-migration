'use client'
import ReactECharts from 'echarts-for-react'
import type { RoleRecord } from '@/hooks/useMonthlyKpiReportTier5'

interface RoleAvgChartProps {
  roles: RoleRecord[]
}

export function RoleAvgChart({ roles }: RoleAvgChartProps) {
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
      formatter: (params: { name: string; value: number }[]) => {
        const p = params[0]
        const role = sorted.find((r) => r.role === p.name)
        return `<b>${p.name}</b><br/>Score: ${p.value}${
          role ? `<br/>Active: ${role.avgTimeLabel}` : ''
        }`
      },
    },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: '#6B7280', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((r) => r.role),
      axisLabel: { color: '#374151', fontSize: 12 },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((r) => r.avg),
        itemStyle: { color: '#4f46e5', borderRadius: [0, 4, 4, 0] },
        barMaxWidth: 24,
        label: {
          show: true,
          position: 'right',
          color: '#374151',
          fontSize: 11,
          fontWeight: 600,
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
