'use client'
// RoleAvgChart — avg score by role horizontal bar chart
// HTML chart type: horizontal bar → ECharts type: 'bar' with horizontal axes (LOCKED)
// HTML source: Pulse tab role breakdown section
// Interactions: tooltip on hover

import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'

export interface RoleRecord {
  role: string
  avg: number
  avgTimeLabel: string
}

interface RoleAvgChartProps {
  roles: RoleRecord[]
  height?: number
}

export function RoleAvgChart({ roles, height = 280 }: RoleAvgChartProps) {
  const sorted = useMemo(() => [...roles].sort((a, b) => a.avg - b.avg), [roles])

  const option = useMemo(
    () => ({
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
          return `<b>${p.name}</b>: ${p.value}`
        },
      },
      grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'value',
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: '#F1F5F9' } },
        axisLabel: { color: '#64748B', fontSize: 11 },
      },
      yAxis: {
        type: 'category',
        data: sorted.map((r) => r.role),
        axisLabel: { color: '#334155', fontSize: 12 },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#E2E8F0' } },
      },
      series: [
        {
          type: 'bar',
          data: sorted.map((r) => ({
            value: r.avg,
            itemStyle: {
              color: r.avg >= 70 ? '#16a34a' : r.avg >= 40 ? '#2563eb' : '#dc2626',
              borderRadius: [0, 4, 4, 0],
            },
          })),
          label: {
            show: true,
            position: 'right',
            color: '#334155',
            fontSize: 12,
            fontWeight: 600,
          },
          barMaxWidth: 32,
        },
      ],
    }),
    [sorted],
  )

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
