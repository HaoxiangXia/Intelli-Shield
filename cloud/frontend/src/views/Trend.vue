<template>
  <div class="trend-page">
    <main class="main-content-inner">
      <!-- 页面标头 -->
      <header class="page-header">
        <div class="header-main">
          <div class="header-title-row">
            <h1 class="page-title">险情下降趋势</h1>
            <span class="live-pulse-badge">
              <span class="pulse-dot"></span>
              <span class="badge-text">效能对比</span>
            </span>
          </div>
          <div class="subtitle">{{ summary.deployMonth }} 接入前后对照</div>
        </div>
        <div class="header-actions">
          <span class="milestone-badge font-mono">2026-03 接入投运</span>
        </div>
      </header>

      <!-- 前后对比磁贴 -->
      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-head">
            <TrendingDown :size="14" class="stat-icon drop" />
            <span class="stat-title">月均险情总量</span>
          </div>
          <div class="stat-value font-mono">
            {{ summary.preAvgTotal }}
            <span class="arrow">→</span>
            {{ summary.postAvgTotal }}
          </div>
          <div class="stat-delta down">▼ {{ summary.totalDropPct }}%</div>
        </div>

        <div class="stat-card">
          <div class="stat-head">
            <ShieldCheck :size="14" class="stat-icon ok" />
            <span class="stat-title">误报率</span>
          </div>
          <div class="stat-value font-mono">
            {{ summary.preAvgFalseRate }}%
            <span class="arrow">→</span>
            {{ summary.postAvgFalseRate }}%
          </div>
          <div class="stat-delta down">▼ {{ summary.falseRateDropPp }} pp</div>
        </div>

        <div class="stat-card">
          <div class="stat-head">
            <ShieldAlert :size="14" class="stat-icon warn" />
            <span class="stat-title">真实险情</span>
          </div>
          <div class="stat-value font-mono">
            {{ summary.preAvgReal }}
            <span class="arrow">→</span>
            {{ summary.postAvgReal }}
          </div>
          <div class="stat-delta down">▼ {{ summary.realDropPct }}%</div>
        </div>

        <div class="stat-card">
          <div class="stat-head">
            <Target :size="14" class="stat-icon cyan" />
            <span class="stat-title">伴随误报</span>
          </div>
          <div class="stat-value font-mono">
            {{ summary.falsePerReal.pre }}
            <span class="arrow">→</span>
            {{ summary.falsePerReal.post }}
          </div>
          <div class="stat-delta neutral">5.4× 信噪比</div>
        </div>
      </div>

      <!-- 趋势走势图卡片 -->
      <div class="trend-card">
        <div class="card-header">
          <div class="card-title-wrap">
            <Activity :size="15" class="title-icon" />
            <h3 class="card-title">{{ chartTitle }}</h3>
          </div>
          <div class="tabs">
            <button
              v-for="r in ranges"
              :key="r.value"
              :class="{ active: range === r.value }"
              @click="range = r.value"
              type="button"
            >
              {{ r.label }}
            </button>
          </div>
        </div>

        <!-- 阶段图例注释 -->
        <div class="legend-note">
          <span class="legend-tag pre">接入前</span>
          <span class="note-text">人工巡检，人眼滞后发现</span>
          <span class="legend-sep"></span>
          <span class="legend-tag post">接入后</span>
          <span class="note-text">红光禁区 + 认知探针，险情持续压降</span>
        </div>

        <div class="chart-panel">
          <LineChart
            :series="chartSeries"
            :labels="chartLabels"
            :height="'380px'"
            :showLegend="false"
            :enableDataZoom="false"
            :options="chartOptions"
          />
        </div>
      </div>

      <!-- 季度汇总表 -->
      <div class="quarter-card">
        <div class="card-header">
          <div class="card-title-wrap">
            <FileSpreadsheet :size="15" class="title-icon" />
            <h3 class="card-title">季度效能汇总表</h3>
          </div>
        </div>
        <div class="table-wrap">
          <table class="quarter-table">
            <thead>
              <tr>
                <th style="width: 100px;">季度</th>
                <th>月均险情</th>
                <th>险情总数</th>
                <th>真实险情</th>
                <th>误报数</th>
                <th style="width: 140px;">误报率</th>
                <th style="width: 100px;">阶段</th>
                <th style="width: 110px;">联锁制动</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyRows" :key="q.quarter" class="quarter-row">
                <td class="font-mono q-cell">{{ q.quarter }}</td>
                <td class="font-mono">{{ q.avgMonthly }}</td>
                <td class="font-mono font-bold">{{ q.total }}</td>
                <td class="font-mono val-danger font-bold">{{ q.real }}</td>
                <td class="font-mono val-warning">{{ q.false }}</td>
                <td class="font-mono">
                  <span class="fp-bar-wrap">
                    <span class="fp-bar" :style="{ width: `${q.falseRate}%` }"></span>
                  </span>
                  <span class="fp-rate">{{ q.falseRate }}%</span>
                </td>
                <td>
                  <span class="stage-tag" :class="stageOf(q.quarter)">
                    {{ stageLabel(q.quarter) }}
                  </span>
                </td>
                <td class="font-mono val-nominal font-bold">
                  {{ stageOf(q.quarter) === 'stage-post' ? '100%' : '人工' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  TrendingDown,
  ShieldCheck,
  ShieldAlert,
  Target,
  Activity,
  FileSpreadsheet
} from 'lucide-vue-next'
import LineChart from '../components/LineChart.vue'
import {
  summary,
  monthlyRows,
  quarterlyRows
} from '../data/trendData'

const range = ref('month')

const ranges = [
  { label: '月度趋势', value: 'month' },
  { label: '季度对比', value: 'quarter' }
]

const chartTitle = computed(() =>
  range.value === 'month' ? '月度险情走势' : '季度险情分布'
)

const chartLabels = computed(() =>
  range.value === 'month'
    ? monthlyRows.map(r => r.month.slice(2))
    : quarterlyRows.map(q => q.quarter)
)

const rows = computed(() => (range.value === 'month' ? monthlyRows : quarterlyRows))

const markLine = computed(() =>
  range.value === 'month' ? [{ xAxis: summary.deployMonth.slice(2) }] : []
)

const markLineLabel = computed(() =>
  range.value === 'month'
    ? {
        show: true,
        formatter: `系统接入 · 下降 ${summary.totalDropPct}%`,
        position: 'insideEndBottom',
        rotate: 0,
        distance: [0, 8],
        color: '#0284c7',
        fontSize: 11,
        fontWeight: 700,
        fontFamily: "'JetBrains Mono', monospace",
        backgroundColor: 'rgba(2, 132, 199, 0.12)',
        borderColor: '#0284c7',
        borderWidth: 1,
        padding: [3, 7],
        borderRadius: 3
      }
    : undefined
)

const chartSeries = computed(() => {
  const total = {
    name: '险情数量',
    data: rows.value.map(r => r.total),
    color: '#0284c7',
    areaColor: ['rgba(2, 132, 199, 0.18)', 'rgba(2, 132, 199, 0.01)'],
    lineWidth: 3,
    emphasisWidth: 5
  }

  if (range.value === 'month') {
    return [{ ...total, markLine: markLine.value, markLineLabel: markLineLabel.value }]
  }

  return [
    {
      ...total,
      type: 'bar',
      area: false,
      barMaxWidth: 48,
      itemStyle: {
        color: '#0284c7',
        borderRadius: [3, 3, 0, 0]
      }
    }
  ]
})

const chartOptions = computed(() => ({
  dataZoom: [],
  grid: { left: 44, right: 20, top: 36, bottom: 28 },
  yAxis: {
    name: '起',
    nameTextStyle: { color: '#64748b', fontSize: 11, align: 'left' },
    nameGap: 10
  }
}))

function stageOf(quarter) {
  const [y, q] = quarter.split('Q')
  const key = `${y}-${String((Number(q) - 1) * 3 + 1).padStart(2, '0')}`
  return key >= summary.deployMonth ? 'stage-post' : 'stage-pre'
}

function stageLabel(quarter) {
  return stageOf(quarter) === 'stage-post' ? '接入后' : '接入前'
}
</script>

<style scoped>
.trend-page {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-canvas);
  color: var(--text-main);
  box-sizing: border-box;
}

.main-content-inner {
  padding: 16px 20px 24px;
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 页面标头 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-machined);
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.5px;
  margin: 0;
}

.live-pulse-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.3);
  padding: 1px 6px;
  border-radius: 3px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--nominal-green);
}

.badge-text {
  font-size: 10px;
  font-weight: 700;
  color: var(--nominal-green);
  font-family: var(--font-mono);
}

.subtitle {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.milestone-badge {
  font-size: 11px;
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.3);
  padding: 4px 8px;
  border-radius: 4px;
}

/* ── 前后对比磁贴 ────────────────────────────────── */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border-machined);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  overflow: hidden;
}

.stat-card {
  background: var(--bg-panel);
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-head {
  display: flex;
  align-items: center;
  gap: 5px;
}

.stat-icon.drop { color: var(--emergency-red); }
.stat-icon.ok { color: var(--nominal-green); }
.stat-icon.warn { color: var(--safety-amber); }
.stat-icon.cyan { color: var(--telemetry-cyan); }

.stat-title {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.1;
  display: flex;
  align-items: baseline;
}

.stat-value .arrow {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 4px;
}

.stat-delta {
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono);
  padding: 1px 5px;
  border-radius: 2px;
  width: fit-content;
}

.stat-delta.down {
  color: var(--nominal-green);
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.25);
}

.stat-delta.neutral {
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.25);
}

/* ── 趋势卡片 ─────────────────────────────────────────────────────── */
.trend-card,
.quarter-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.card-title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.title-icon {
  color: var(--telemetry-cyan);
}

.card-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.tabs {
  display: flex;
  gap: 4px;
}

.tabs button {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid var(--border-machined);
  background: var(--bg-panel);
  color: var(--text-secondary);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tabs button:hover {
  border-color: var(--border-bright);
  color: var(--text-main);
}

.tabs button.active {
  background: var(--telemetry-cyan);
  border-color: var(--telemetry-cyan);
  color: #fff;
}

.legend-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  margin-bottom: 10px;
  font-size: 11px;
}

.legend-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 2px;
  white-space: nowrap;
}

.legend-tag.pre {
  color: var(--text-muted);
  background: #e2e8f0;
  border: 1px solid var(--border-bright);
}

.legend-tag.post {
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.3);
}

.note-text {
  color: var(--text-secondary);
  font-size: 11px;
}

.legend-sep {
  width: 1px;
  height: 12px;
  background: var(--border-bright);
  margin: 0 4px;
}

.chart-panel {
  padding: 2px 0;
}

/* ── 季度表 ───────────────────────────────────────────────────────── */
.table-wrap {
  overflow-x: auto;
}

.quarter-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.quarter-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-machined);
  background: var(--bg-panel-subtle);
  white-space: nowrap;
}

.quarter-row {
  border-bottom: 1px solid var(--border-machined);
  transition: background 0.12s ease;
}

.quarter-row:last-child {
  border-bottom: none;
}

.quarter-row:hover {
  background: var(--bg-panel-subtle);
}

.quarter-table td {
  padding: 8px 10px;
  white-space: nowrap;
}

.q-cell {
  font-weight: 700;
  color: var(--text-main);
}

.val-danger { color: var(--emergency-red); }
.val-warning { color: var(--safety-amber); }
.val-nominal { color: var(--nominal-green); }
.font-bold { font-weight: 700; }

.fp-bar-wrap {
  display: inline-block;
  width: 44px;
  height: 5px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
  margin-right: 6px;
  vertical-align: middle;
}

.fp-bar {
  display: block;
  height: 100%;
  background: var(--safety-amber);
}

.fp-rate {
  font-size: 11px;
  color: var(--text-secondary);
}

.stage-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 2px;
  white-space: nowrap;
}

.stage-tag.stage-pre {
  color: var(--text-muted);
  background: #f1f5f9;
  border: 1px solid var(--border-machined);
}

.stage-tag.stage-post {
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.3);
}

@media (max-width: 900px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
