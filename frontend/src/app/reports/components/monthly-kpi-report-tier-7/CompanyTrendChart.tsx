'use client'

import ReactECharts from 'echarts-for-react'
import { DayScore, DayTime } from '@/hooks/useMonthlyKpiReportTier7'

interface CompanyTrendChartProps {
  daily: DayScore[]
  dailyTime: DayTime[]
  metric: 'score' | 'time'
}

export function CompanyTrendChart({ daily, dailyTime, metric }: CompanyTrendChartProps) {
  // Source type (1.5I): "bar" → Lookup table row: "bar" (vertical) → ECharts type: 'bar'
  const isScore = metric === 'score'
  const days = isScore ? daily.map((d) => d.day) : dailyTime.map((d) => d.day)
  const values = isScore
    ? daily.map((d) => d.score)
    : dailyTime.map((d) => d.minutes)

  const option = {
    textStyle: { fontFamily: 'var(--font-family-primary), sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      textStyle: { color: '#111827', fontSize: 12 },
      formatter: (params: unknown[]) => {
        const p = params[0] as { name: string; value: number }
        if (isScore) return `${p.name}: ${p.value}`
        const h = Math.floor(p.value / 60)
        const m = p.value % 60
        return `${p.name}: ${h}h ${String(m).padStart(2, '0')}min`
      },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: days,
      axisLabel: { color: '#6D6D6D', fontSize: 12 },
      axisLine: { lineStyle: { color: '#E7E7E7' } },
    },
    yAxis: {
      type: 'value' as const,
      name: isScore ? 'Score' : 'Minutes',
      nameTextStyle: { color: '#6D6D6D', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F6F6F6' } },
      axisLabel: { color: '#6D6D6D', fontSize: 11 },
    },
    series: [
      {
        name: isScore ? 'Company Score' : 'Active Time',
        type: 'bar' as const,
        data: values,
        barMaxWidth: 48,
        itemStyle: {
          color: '#1E86D9',
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: '220px', width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
