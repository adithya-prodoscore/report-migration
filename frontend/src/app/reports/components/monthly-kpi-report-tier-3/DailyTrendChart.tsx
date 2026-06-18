'use client'

import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import type { DailyScore } from '@/hooks/useMonthlyKpiReportTier3'

interface DailyTrendChartProps {
  data: DailyScore[]
  title?: string
  color?: string
  height?: number
  showAvgLine?: boolean
}

export function DailyTrendChart({
  data,
  title,
  color = '#1E86D9',
  height = 220,
  showAvgLine = false,
}: DailyTrendChartProps) {
  const option = useMemo(() => {
    const days = data.map((d) => d.day)
    const scores = data.map((d) => d.score)

    return {
      textStyle: { fontFamily: 'var(--font-family-primary, Geist, system-ui, sans-serif)' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#E2E8F0',
        borderWidth: 1,
        textStyle: { color: '#1e293b', fontSize: 12 },
        formatter: (params: unknown[]) => {
          const p = params[0] as { name: string; value: number }
          return `${p.name}: <strong>${p.value}</strong>`
        },
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: title ? '32px' : '16px', containLabel: true },
      title: title
        ? {
            text: title,
            textStyle: { fontSize: 13, fontWeight: 600, color: '#334155' },
            top: 4,
            left: 0,
          }
        : undefined,
      xAxis: {
        type: 'category',
        data: days,
        axisLine: { lineStyle: { color: '#E2E8F0' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748b', fontSize: 12 },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { color: '#64748b', fontSize: 11 },
        splitLine: { lineStyle: { color: '#F1F5F9' } },
      },
      series: [
        {
          type: 'bar',
          data: scores,
          itemStyle: { color, borderRadius: [4, 4, 0, 0] },
          barMaxWidth: 40,
          ...(showAvgLine
            ? {
                markLine: {
                  silent: true,
                  data: [{ type: 'average', name: 'Avg' }],
                  lineStyle: { color: '#94a3b8', type: 'dashed' },
                  label: { formatter: 'Avg: {c}', color: '#94a3b8', fontSize: 11 },
                },
              }
            : {}),
        },
      ],
    }
  }, [data, title, color, showAvgLine])

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
