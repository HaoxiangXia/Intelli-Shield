<template>
  <div ref="chartRef" class="line-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  series: {
    type: Array,
    required: true,
  },
  labels: {
    type: Array,
    default: () => Array.from({ length: 24 }, (_, i) => `${i}:00`),
  },
  height: {
    type: String,
    default: '200px',
  },
  showLegend: {
    type: Boolean,
    default: true,
  },
  enableDataZoom: {
    type: Boolean,
    default: true,
  },
  options: {
    type: Object,
    default: () => ({}),
  },
})

const chartRef = ref(null)
let chartInstance = null

const defaultColors = [
  { line: '#0284c7', area: ['rgba(2,132,199,0.18)', 'rgba(2,132,199,0.02)'] },
  { line: '#dc2626', area: ['rgba(220,38,38,0.18)', 'rgba(220,38,38,0.02)'] },
  { line: '#d97706', area: ['rgba(217,119,6,0.16)', 'rgba(217,119,6,0.02)'] },
  { line: '#16a34a', area: ['rgba(22,163,74,0.16)', 'rgba(22,163,74,0.02)'] }
]

function renderChart() {
  if (!chartInstance) return

  const defaultDataZoom = [
    {
      type: 'inside',
      start: 80,
      end: 100,
      zoomLock: false,
    },
    {
      type: 'slider',
      height: 20,
      bottom: 0,
      handleIcon: 'M8.2,13.3h-1.6v-2.6h1.6V13.3z',
      handleSize: '120%',
      start: 80,
      end: 100,
      showDetail: false,
    }
  ]

  const baseOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#cbd5e1',
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: '#0f172a', fontSize: 12, fontFamily: 'Inter, -apple-system, sans-serif' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08); border-radius: 4px;'
    },
    axisPointer: {
      type: 'line',
      lineStyle: { color: '#0284c7', width: 1, type: 'dashed' },
    },
    legend: props.showLegend
      ? {
          data: props.series.map(s => s.name),
          textStyle: { color: '#0f172a', fontSize: 12, fontWeight: 600 },
          top: 0,
          itemWidth: 14,
          itemHeight: 3,
        }
      : undefined,
    grid: {
      left: 36,
      right: 16,
      bottom: props.enableDataZoom ? 28 : 16,
      top: props.showLegend ? 36 : 16,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.labels,
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisTick: { show: false },
      axisLabel: { color: '#64748b', fontSize: 11, margin: 8, fontFamily: "'JetBrains Mono', monospace" }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748b', fontSize: 11, fontFamily: "'JetBrains Mono', monospace" },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: props.series.map((s, i) => {
      const color = s.color || defaultColors[i]?.line || defaultColors[0].line
      const areaColor = s.areaColor || defaultColors[i]?.area || defaultColors[0].area
      const type = s.type || 'line'
      const base = {
        name: s.name,
        type,
        data: s.data,
        showSymbol: false,
        barMaxWidth: s.barMaxWidth || 26,
        emphasis: { focus: 'series' }
      }

      // 柱状系列不需要平滑/面积/标记线
      if (type === 'bar') {
        return {
          ...base,
          itemStyle: { color, borderRadius: s.borderRadius ?? [2, 2, 0, 0] }
        }
      }

      return {
        ...base,
        smooth: 0.4,
        lineStyle: { color, width: s.lineWidth || 3 },
        emphasis: { ...base.emphasis, lineStyle: { width: s.emphasisWidth || 5 } },
        areaStyle: s.area === false
          ? undefined
          : {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: areaColor[0] },
                { offset: 1, color: areaColor[1] },
              ]),
            },
        markLine: s.markLine
          ? {
              silent: true,
              symbol: 'none',
              data: s.markLine,
              lineStyle: { color, type: 'dashed', width: 1.5 },
              label: s.markLineLabel
            }
          : undefined
      }
    }),
    dataZoom: props.enableDataZoom ? defaultDataZoom : [],
  }

  chartInstance.setOption({
    ...baseOption,
    ...props.options,
    // 轴配置与 grid 一样做合并, 否则调用方传 options 时会把 type/data 全冲掉
    grid: { ...baseOption.grid, ...(props.options?.grid || {}) },
    xAxis: { ...baseOption.xAxis, ...(props.options?.xAxis || {}) },
    yAxis: { ...baseOption.yAxis, ...(props.options?.yAxis || {}) },
    legend: props.options?.legend
      ? { ...baseOption.legend, ...props.options.legend }
      : baseOption.legend,
  })
}

onMounted(() => {
  chartInstance = echarts.init(chartRef.value)
  renderChart()

  const resizeHandler = () => chartInstance?.resize()
  window.addEventListener('resize', resizeHandler)

  onUnmounted(() => {
    window.removeEventListener('resize', resizeHandler)
    chartInstance?.dispose()
  })
})

watch(
  () => [props.series, props.labels, props.showLegend, props.enableDataZoom, props.options],
  renderChart,
  { deep: true }
)
</script>

<style scoped>
.line-chart {
  width: 100%;
  height: v-bind(height);
  border-radius: 4px;
  overflow: hidden;
}
</style>
