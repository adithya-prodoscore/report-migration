'use client'

import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { DayScore } from '@/hooks/useMonthlyKpiReportTier7'

interface WorkforceTrendChartProps {
  groupName: string
  daily: DayScore[]
  wm?: { Remote?: DayScore[]; 'In-Office'?: DayScore[] }
  showWorkMode: boolean
}

export function WorkforceTrendChart({
  groupName,
  daily,
  wm,
  showWorkMode,
}: WorkforceTrendChartProps) {
  // Source type (1.5I): "line" → Lookup: "line" → ECharts type: 'line'
  const option = useMemo(() => {
    const days = daily.map((d) => d.day)
    const series = []

    if (showWorkMode && wm) {
      if (wm['In-Office']) {
        series.push({
          name: 'In-Office',
          type: 'line' as const,
          smooth: true,
          data: wm['In-Office'].map((d) => d.score),
          lineStyle: { color: '#7c3aed' },
          itemStyle: { color: '#7c3aed' },
        })
      }
      if (wm['Remote']) {
        series.push({
          name: 'Remote',
          type: 'line' as const,
          smooth: true,
          data: wm['Remote'].map((d) => d.score),
          lineStyle: { color: '#0891b2' },
          itemStyle: { color: '#0891b2' },
        })
      }
    } else {
      series.push({
        name: groupName,
        type: 'line' as const,
        smooth: true,
        data: daily.map((d) => d.score),
        lineStyle: { color: '#1E86D9' },
        itemStyle: { color: '#1E86D9' },
      })
    }

    return {
      textStyle: { fontFamily: 'var(--font-family-primary), sans-serif' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#E5E7EB',
        borderWidth: 1,
        textStyle: { color: '#111827', fontSize: 12 },
      },
      legend:
        showWorkMode && wm
          ? { data: ['In-Office', 'Remote'], textStyle: { fontSize: 11 } }
          : { show: false },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category' as const,
        data: days,
        axisLabel: { color: '#6D6D6D', fontSize: 11 },
        axisLine: { lineStyle: { color: '#E7E7E7' } },
      },
      yAxis: {
        type: 'value' as const,
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: '#F6F6F6' } },
        axisLabel: { color: '#6D6D6D', fontSize: 11 },
      },
      series,
    }
  }, [groupName, daily, wm, showWorkMode])

  return (
    <ReactECharts
      option={option}
      notMerge
      style={{ height: '160px', width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  )
}
