'use client'
import ReactECharts from 'echarts-for-react'
import type { DailyScore } from '@/hooks/useMonthlyKpiReportTier5'

interface DailyTrendChartProps {
  data: DailyScore[]
  title?: string
  color?: string
}

export function DailyTrendChart({
  data,
  title = 'Company Daily Score Trend',
  color = '#1E86D9',
}: DailyTrendChartProps) {
  const option = {
    textStyle: { fontFamily: 'var(--font-family-primary), sans-serif' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      textStyle: { color: '#111827', fontSize: 12 },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.day),
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#6B7280', fontSize: 11 },
    },
    series: [
      {
        name: title,
        type: 'bar',
        data: data.map((d) => d.score),
        itemStyle: { color, borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 48,
        label: {
          show: true,
          position: 'top',
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
      style={{ height: '240px', width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
