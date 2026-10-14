<template>
  <div class="trend-page">
    <main class="main-content-inner">

      <header class="page-header">
        <div>
          <h1>险情下降趋势</h1>
          <div class="subtitle">
            Hazard Trend · {{ summary.deployMonth }} 系统接入前后对照
          </div>
        </div>
        <span class="mock-badge" title="本页面数值为答辩演示用模拟数据，非生产环境实测结果">
          演示数据 MOCK
        </span>
      </header>

      <!-- 前后对比磁贴 -->
      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-head">
            <TrendingDown :size="15" class="stat-icon drop" />
            <span class="stat-title">月均险情上报量</span>
          </div>
          <div class="stat-value">
            {{ summary.preAvgTotal }}
            <span class="arrow">→</span>
            {{ summary.postAvgTotal }}
          </div>
          <div class="stat-delta down">▼ {{ summary.totalDropPct }}%</div>
        </div>

        <div class="stat-card">
          <div class="stat-head">
            <ShieldCheck :size="15" class="stat-icon ok" />
            <span class="stat-title">误报率</span>
          </div>
          <div class="stat-value">
            {{ summary.preAvgFalseRate }}%
            <span class="arrow">→</span>
            {{ summary.postAvgFalseRate }}%
          </div>
          <div class="stat-delta down">▼ {{ summary.falseRateDropPp }} pp</div>
        </div>

        <div class="stat-card">
          <div class="stat-head">
            <ShieldAlert :size="15" class="stat-icon warn" />
            <span class="stat-title">真实险情 (复核确认)</span>
          </div>
          <div class="stat-value">
            {{ summary.preAvgReal }}
            <span class="arrow">→</span>
            {{ summary.postAvgReal }}
          </div>
          <div class="stat-delta down">▼ {{ summary.realDropPct }}%</div>
        </div>

        <div class="stat-card">
          <div class="stat-head">
            <Target :size="15" class="stat-icon cyan" />
            <span class="stat-title">每起险情伴随误报</span>
          </div>
          <div class="stat-value">
            {{ summary.falsePerReal.pre }}
            <span class="arrow">→</span>
            {{ summary.falsePerReal.post }}
          </div>
          <div class="stat-delta neutral">信噪比改善</div>
        </div>
      </div>

      <!-- 趋势图 -->
      <div class="card glass trend-card">
        <div class="card-header">
          <h3 class="card-title">{{ chartTitle }}</h3>
          <div class="tabs">
            <button
              v-for="r in ranges"
              :key="r.value"
              :class="{ active: range === r.value }"
              @click="range = r.value"
            >
              {{ r.label }}
            </button>
          </div>
        </div>

        <div class="legend-note">
          <span class="legend-tag pre">系统接入前</span>
          <span>人工巡检 + 事后追溯，险情靠人眼发现</span>
          <span class="legend-sep"></span>
          <span class="legend-tag post">系统接入后</span>
          <span>红光禁区 + YOLO 感知 + OneJev 认知探针三层仲裁，险情持续下降</span>
        </div>

        <div class="chart-panel glass-inner">
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
      <div class="card glass quarter-card">
        <div class="card-header">
          <h3 class="card-title">季度汇总</h3>
          <span class="card-meta">由月度数据聚合推导</span>
        </div>
        <div class="table-wrap">
          <table class="quarter-table">
            <thead>
              <tr>
                <th>季度</th>
                <th>月均险情</th>
                <th>险情总数</th>
                <th>真实险情</th>
                <th>误报</th>
                <th>误报率</th>
                <th>阶段</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyRows" :key="q.quarter">
                <td class="mono">{{ q.quarter }}</td>
                <td class="mono">{{ q.avgMonthly }}</td>
                <td class="mono">{{ q.total }}</td>
                <td class="mono ok">{{ q.real }}</td>
                <td class="mono danger">{{ q.false }}</td>
                <td class="mono">
                  <span class="fp-bar">
                    <i :style="{ width: `${q.falseRate}%` }"></i>
                  </span>
                  {{ q.falseRate }}%
                </td>
                <td>
                  <span class="stage-tag" :class="stageOf(q.quarter)">{{ stageLabel(q.quarter) }}</span>
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
import { TrendingDown, ShieldCheck, ShieldAlert, Target } from 'lucide-vue-next'
import LineChart from '../components/LineChart.vue'
import {
  summary,
  monthlyRows,
  quarterlyRows
} from '../data/trendData'

const range = ref('month')

const ranges = [
  { label: '月度', value: 'month' },
  { label: '季度', value: 'quarter' }
]

const COLOR = {
  total: '#dc2626'
}

const chartTitle = computed(() =>
  range.value === 'month' ? '月度险情趋势' : '季度险情趋势'
)

const chartLabels = computed(() =>
  range.value === 'month'
    ? monthlyRows.map(r => r.month.slice(2))
    : quarterlyRows.map(q => q.quarter)
)

const rows = computed(() => (range.value === 'month' ? monthlyRows : quarterlyRows))

// 月度视图在接入月画分界线; 季度视图按阶段整段染色
const markLine = computed(() =>
  range.value === 'month' ? [{ xAxis: summary.deployMonth.slice(2) }] : []
)

const markLineLabel = computed(() =>
  range.value === 'month'
    ? {
        show: true,
        formatter: `系统接入 · 险情下降 ${summary.totalDropPct}%`,
        position: 'insideEndBottom',
        rotate: 0,
        distance: [0, 6],
        color: '#0f172a',
        fontSize: 11,
        fontWeight: 700,
        backgroundColor: 'rgba(2,132,199,0.14)',
        padding: [4, 7],
        borderRadius: 3
      }
    : undefined
)

// 主趋势: 险情总量单线, 视觉上只保留一条, 保证"整体下降"一眼可读。
// 真实/误报的拆分放在下方季度表里, 不再叠到图上互相干扰。
const chartSeries = computed(() => {
  const total = {
    name: '险情数量',
    data: rows.value.map(r => r.total),
    color: COLOR.total,
    lineWidth: 4,
    emphasisWidth: 6
  }

  if (range.value === 'month') {
    return [{ ...total, markLine: markLine.value, markLineLabel: markLineLabel.value }]
  }

  return [{ ...total, type: 'bar', area: false, barMaxWidth: 64 }]
})

const chartOptions = computed(() => ({
  dataZoom: [],
  grid: { left: 52, right: 24, top: 40, bottom: 32 },
  yAxis: {
    name: '险情笔数',
    nameTextStyle: { color: '#64748b', fontSize: 10, align: 'left' },
    nameGap: 12
  }
}))

// 季度所属阶段: 2026Q1 含接入月(03), 计入"接入后"
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
}

.main-content-inner {
  padding: 20px 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header h1 {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 600;
  color: var(--text-main);
}

.subtitle {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 3px;
}

.mock-badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--safety-amber);
  border: 1px dashed var(--safety-amber);
  background: var(--safety-amber-dim);
  padding: 3px 8px;
  letter-spacing: 0.04em;
}

/* ── 磁贴 ───────────────────────────────────────────────────────────── */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  padding: 13px 15px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.stat-head {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-icon.drop { color: var(--emergency-red); }
.stat-icon.ok { color: var(--nominal-green); }
.stat-icon.warn { color: var(--safety-amber); }
.stat-icon.cyan { color: var(--telemetry-cyan); }

.stat-title {
  font-size: 11px;
  color: var(--text-secondary);
}

.stat-value {
  font-family: var(--font-mono);
  font-size: 21px;
  font-weight: 700;
  color: var(--text-main);
}

.stat-value .arrow {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0 3px;
}

.stat-delta {
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono);
}

.stat-delta.down { color: var(--nominal-green); }
.stat-delta.neutral { color: var(--telemetry-cyan); }

/* ── 卡片 ───────────────────────────────────────────────────────────── */
.glass {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
}

.glass-inner {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
}

.trend-card,
.quarter-card {
  padding: 16px 18px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.card-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
}

.card-meta {
  font-size: 10px;
  color: var(--text-muted);
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 3px 9px;
}

.tabs {
  display: flex;
  gap: 4px;
}

.tabs button {
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid var(--border-machined);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.tabs button:hover {
  border-color: var(--border-bright);
}

.tabs button.active {
  background: var(--telemetry-cyan);
  border-color: var(--telemetry-cyan);
  color: #fff;
}

.legend-note {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.legend-tag {
  font-weight: 700;
  padding: 2px 7px;
  border: 1px solid currentColor;
  font-size: 10px;
}

.legend-tag.pre {
  color: var(--text-muted);
}

.legend-tag.post {
  color: var(--telemetry-cyan);
}

.legend-sep {
  width: 1px;
  height: 12px;
  background: var(--border-machined);
  margin: 0 4px;
}

.chart-panel {
  padding: 10px;
}

/* ── 季度表 ─────────────────────────────────────────────────────────── */
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
  padding: 7px 10px;
  border-bottom: 1px solid var(--border-machined);
  white-space: nowrap;
}

.quarter-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-machined);
  color: var(--text-main);
  white-space: nowrap;
}

.quarter-table tbody tr:hover td {
  background: var(--bg-panel-subtle);
}

.mono {
  font-family: var(--font-mono);
}

.mono.ok { color: var(--nominal-green); font-weight: 600; }
.mono.danger { color: var(--safety-amber); font-weight: 600; }

.fp-bar {
  display: inline-block;
  width: 44px;
  height: 6px;
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  margin-right: 6px;
  vertical-align: middle;
}

.fp-bar i {
  display: block;
  height: 100%;
  background: var(--safety-amber);
}

.stage-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border: 1px solid currentColor;
}

.stage-tag.stage-pre { color: var(--text-muted); }
.stage-tag.stage-post { color: var(--telemetry-cyan); }
</style>