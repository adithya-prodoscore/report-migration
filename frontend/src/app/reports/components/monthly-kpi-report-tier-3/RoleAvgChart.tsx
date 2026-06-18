'use client'

import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import type { RoleRecord } from '@/hooks/useMonthlyKpiReportTier3'

interface RoleAvgChartProps {
  roles: RoleRecord[]
  height?: number
}

export function RoleAvgChart({ roles, height = 260 }: RoleAvgChartProps) {
  const option = useMemo(() => {
    const sorted = [...roles].sort((a, b) => b.avg - a.avg)
    const names = sorted.map((r) => r.role)
    const avgs = sorted.map((r) => r.avg)
    const colors = avgs.map((v) =>
      v >= 70 ? '#1E86D9' : v >= 40 ? '#1E86D9' : '#F1433C'
    )

    return {
      textStyle: { fontFamily: 'var(--font-family-primary, Geist, system-ui, sans-serif)' },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#E2E8F0',
        borderWidth: 1,
        textStyle: { color: '#1e293b', fontSize: 12 },
        formatter: (params: unknown[]) => {
          const p = params[0] as { name: string; value: number }
          return `${p.name}: <strong>${p.value}</strong>`
        },
      },
      grid: { left: '3%', right: '8%', bottom: '3%', top: '8px', containLabel: true },
      xAxis: { type: 'value', max: 100, axisLabel: { color: '#64748b', fontSize: 11 } },
      yAxis: {
        type: 'category',
        data: names,
        axisLabel: { color: '#334155', fontSize: 12 },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: avgs.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] } })),
          barMaxWidth: 28,
          label: { show: true, position: 'right', color: '#334155', fontSize: 11 },
        },
      ],
    }
  }, [roles])

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
