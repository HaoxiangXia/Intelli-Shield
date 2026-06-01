<template>
  <GlassCard class="alarm-trend-panel">
    <template #header>
      <div class="header-left">
        <h3 class="glass-title">报警次数趋势</h3>
        <span class="badge-time">24小时</span>
      </div>
      <a href="#" class="view-all">查看全部 ></a>
    </template>
    
    <div class="chart-container">
      <v-chart class="chart" :option="chartOption" autoresize />
    </div>
  </GlassCard>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import GlassCard from './GlassCard.vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../../lib/api'

use([CanvasRenderer, LineChart, TooltipComponent, GridComponent, LegendComponent])

const chartOption = ref({
  tooltip: { trigger: 'axis' },
  legend: {
    icon: 'circle',
    itemWidth: 8,
    itemHeight: 8,
    data: ['今日', '昨日'],
    textStyle: { color: '#52617a' },
    top: 0
  },
  grid: { left: '3%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: [],
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#8491ac' }
  },
  yAxis: {
    type: 'value',
    max: 1,
    splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0,0,0,0.05)' } },
    axisLabel: { color: '#8491ac' }
  },
  series: [
    {
      name: '今日',
      type: 'line',
      smooth: true,
      showSymbol: false,
      itemStyle: { color: '#2f6bff' },
      lineStyle: { width: 3 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(47, 107, 255, 0.3)' }, { offset: 1, color: 'rgba(47, 107, 255, 0.0)' }]
        }
      },
      data: []
    },
    {
      name: '昨日',
      type: 'line',
      smooth: true,
      showSymbol: false,
      itemStyle: { color: '#35c98b' },
      lineStyle: { width: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(53, 201, 139, 0.2)' }, { offset: 1, color: 'rgba(53, 201, 139, 0.0)' }]
        }
      },
      data: []
    }
  ]
})

const REFRESH_MS = 60000
let refreshTimer = null

function resolveMaxValue(todayCounts, yesterdayCounts) {
  const values = [...(todayCounts || []), ...(yesterdayCounts || [])]
  const maxVal = values.length ? Math.max(...values) : 0
  return Math.max(1, Math.ceil(maxVal / 2) * 2)
}

async function fetchTrend() {
  try {
    const res = await api.get('/api/dashboard/alarm-trend')
    const payload = res.data || {}
    const labels = payload.labels || []
    const todayCounts = payload.today_counts || []
    const yesterdayCounts = payload.yesterday_counts || []

    chartOption.value = {
      ...chartOption.value,
      xAxis: { ...chartOption.value.xAxis, data: labels },
      yAxis: { ...chartOption.value.yAxis, max: resolveMaxValue(todayCounts, yesterdayCounts) },
      series: [
        { ...chartOption.value.series[0], data: todayCounts },
        { ...chartOption.value.series[1], data: yesterdayCounts }
      ]
    }
  } catch (error) {
    console.error('报警趋势数据加载失败', error)
  }
}

onMounted(() => {
  fetchTrend()
  refreshTimer = setInterval(fetchTrend, REFRESH_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.alarm-trend-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.glass-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-main);
}
.badge-time {
  font-size: 12px;
  background: var(--glass-bg-strong);
  padding: 2px 10px;
  border-radius: 12px;
  color: var(--color-text-secondary);
}
.view-all {
  font-size: 14px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.chart-container {
  flex: 1;
  width: 100%;
}
.chart {
  width: 100%;
  height: 100%;
}
</style>
