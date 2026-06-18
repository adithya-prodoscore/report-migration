'use client'
// DailyTrendChart — Mon-Fri weekday average score line/area chart
// HTML chart type: line/area → ECharts type: 'line' with areaStyle (LOCKED)
// HTML source: Pulse tab company/group daily trend section
// Interactions: tooltip on hover

import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'

export interface DailyScorePoint {
  day: string
  score: number
}

interface DailyTrendChartProps {
  data: DailyScorePoint[]
  title?: string
  color?: string
  height?: number
}

export function DailyTrendChart({
  data,
  title,
  color = '#1E86D9',
  height = 240,
}: DailyTrendChartProps) {
  const option = useMemo(
    () => ({
      textStyle: { fontFamily: 'var(--font-family-primary), sans-serif' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#E5E7EB',
        borderWidth: 1,
        textStyle: { color: '#111827', fontSize: 12 },
        formatter: (params: { name: string; value: number }[]) => {
          const p = params[0]
          return `<b>${p.name}</b>: ${p.value}`
        },
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.map((d) => d.day),
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#E2E8F0' } },
        axisLabel: { color: '#64748B', fontSize: 12 },
      },
      yAxis: {
        type: 'value',
        name: 'Score',
        nameTextStyle: { color: '#64748B', fontSize: 11 },
        splitLine: { lineStyle: { color: '#F1F5F9' } },
        axisLabel: { color: '#64748B', fontSize: 11 },
        min: 0,
        max: 100,
      },
      series: [
        {
          name: title ?? 'Score',
          type: 'line',
          smooth: true,
          data: data.map((d) => d.score),
          areaStyle: { color: color, opacity: 0.12 },
          lineStyle: { color, width: 2 },
          itemStyle: { color },
          symbol: 'circle',
          symbolSize: 6,
        },
      ],
    }),
    [data, title, color],
  )

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
