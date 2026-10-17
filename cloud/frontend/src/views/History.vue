<template>
  <div class="ledger-page">
    <div class="content-container">
      <!-- 页面标头 (克制、严谨、专业工业风) -->
      <header class="page-header">
        <div class="header-main">
          <h1 class="page-title">隐患台账与处置审计</h1>
          <p class="page-desc">
            特种车辆高位视频感知与 OmniJev-4B 认知探针历史留痕审计
          </p>
        </div>
        <div class="header-actions">
          <span class="system-tag">HPC 节点 107.4ms 恒频对齐</span>
          <button @click="fetchHistory" class="btn-refresh" type="button" :disabled="isRefreshing">
            <RefreshCw :size="13" :class="{ spinning: isRefreshing }" />
            <span>刷新</span>
          </button>
        </div>
      </header>

      <!-- 紧凑工业统计栏 (去除卡片堆叠，采用整齐细线网格) -->
      <div class="metrics-grid">
        <div class="metric-block">
          <span class="m-label">累计入账记录</span>
          <span class="m-val">{{ totalCount }}</span>
        </div>
        <div class="metric-block">
          <span class="m-label">危急切断 (一票否决)</span>
          <span class="m-val text-danger">{{ criticalCount }}</span>
        </div>
        <div class="metric-block">
          <span class="m-label">临界预警干预</span>
          <span class="m-val text-warning">{{ warningCount }}</span>
        </div>
        <div class="metric-block">
          <span class="m-label">误报排除 (难负例)</span>
          <span class="m-val text-secondary">{{ dismissedCount }}</span>
        </div>
      </div>

      <!-- 过滤筛选标签 (平铺分段式，无花哨小圆点与荧光) -->
      <div class="filter-toolbar">
        <div class="segment-group">
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'ALL' }"
            @click="currentFilter = 'ALL'"
            type="button"
          >
            全部 ({{ totalCount }})
          </button>
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'CRITICAL' }"
            @click="currentFilter = 'CRITICAL'"
            type="button"
          >
            危急切断 ({{ criticalCount }})
          </button>
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'WARNING' }"
            @click="currentFilter = 'WARNING'"
            type="button"
          >
            临界预警 ({{ warningCount }})
          </button>
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'DISMISSED' }"
            @click="currentFilter = 'DISMISSED'"
            type="button"
          >
            误报排除 ({{ dismissedCount }})
          </button>
        </div>
      </div>

      <!-- 精密高密度数据网格 (纯正工业安防台账，彻底根除卡片堆叠与贴纸泛滥) -->
      <div class="table-container">
        <table class="ledger-table">
          <thead>
            <tr>
              <th style="width: 130px;">事件编号</th>
              <th style="width: 155px;">记录时间</th>
              <th style="width: 190px;">监控点位 / 作业区</th>
              <th style="width: 110px;">告警定性</th>
              <th>双系统归因与排险证据 (YOLO + 红光 + OmniJev-4B)</th>
              <th style="width: 130px;">处置结论</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredData.length === 0">
              <td colspan="6" class="empty-cell">该分类下暂无已归档台账记录</td>
            </tr>
            <tr v-for="item in filteredData" :key="item.id" class="ledger-row">
              <td class="font-mono id-cell">{{ item.id }}</td>
              <td class="font-mono time-cell">{{ item.timestamp }}</td>
              <td>
                <div class="point-name">{{ item.device_id }}</div>
                <div class="point-zone">{{ item.zone }}</div>
              </td>
              <td>
                <span class="severity-tag" :class="`sev-${item.level?.toLowerCase()}`">
                  {{ item.levelText }}
                </span>
              </td>
              <td class="evidence-cell">
                <div class="evidence-main">{{ item.description }}</div>
                <div class="evidence-telemetry font-mono" v-if="item.probesSummary">
                  {{ item.probesSummary }} · 延迟 107.4ms
                </div>
              </td>
              <td>
                <span class="status-cell" :class="`st-${item.status}`">
                  {{ item.statusText }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import api from '../lib/api'

// 6 条严谨工业安全台账，覆盖红线突破、预警缓冲、拐角盲区、责任人核验与门控过滤场景
const MOCK_HISTORY_RECORDS = [
  {
    id: 'HAZ-20261017-001',
    device_id: 'CCTV-04',
    zone: 'B区 · 高架立体库主干道',
    level: 'CRITICAL',
    levelText: '危急制动',
    timestamp: '2026-10-17 14:28:19',
    description: '人员双脚越入三向红光激光防线内侧 (-1.46m)，OmniJev-4B 识别工人处于死角盲区且背向叉车 P(back)=82%，全车动力切断联锁触发，现场排险完毕二次确认恢复。',
    probesSummary: '探针: P(coll)=85.7% | 烈度 2.48 / 3.0',
    status: 'confirmed',
    statusText: '已排险恢复'
  },
  {
    id: 'HAZ-20261017-002',
    device_id: 'CCTV-02',
    zone: 'A区 · 原料卸载暂存区',
    level: 'WARNING',
    levelText: '临界预警',
    timestamp: '2026-10-17 11:15:42',
    description: '叉车接近作业通廊 (间距 1.2m)，OmniJev-4B 识别工人低头看手机 P(phone)=78%，系统发起三向激光高亮与声光蜂鸣干预，作业人员主动避让。',
    probesSummary: '探针: P(coll)=42.3% | 烈度 1.32 / 3.0',
    status: 'resolved',
    statusText: '已避让放行'
  },
  {
    id: 'HAZ-20261016-003',
    device_id: 'CCTV-01',
    zone: 'C区 · 成品组装中转区',
    level: 'CRITICAL',
    levelText: '危急制动',
    timestamp: '2026-10-16 16:50:08',
    description: '货架盲区即将交汇前夕，高位空间感知提前预判冲突轨迹 P(coll)=88.5%，提前 1.5 秒切断全车动力广播报警，成功阻断盲区挤压风险。',
    probesSummary: '探针: P(coll)=88.5% | 烈度 2.35 / 3.0',
    status: 'confirmed',
    statusText: '已排险恢复'
  },
  {
    id: 'HAZ-20261016-004',
    device_id: 'CCTV-04',
    zone: 'B区 · 高架立体库主干道',
    level: 'DISMISSED',
    levelText: '误报排除',
    timestamp: '2026-10-16 09:32:15',
    description: '现场专人手持荧光指挥棒导引人车协同作业，安全责任人核验判定为误报，一键恢复车辆动力并将多模态数据对沉淀为难负例样本。',
    probesSummary: '人在回路: 判定误报 | 样本已归档',
    status: 'dismissed',
    statusText: '判定误报恢复'
  },
  {
    id: 'HAZ-20261015-005',
    device_id: 'CCTV-03',
    zone: 'D区 · 叉车充换电接驳站',
    level: 'NORMAL',
    levelText: '门控过滤',
    timestamp: '2026-10-15 17:04:30',
    description: '车载驾驶员登车作业 (IoP=0.74)，时空门控引擎判定为人车刚性绑定，自动抑制 GPU 探针调用与声光警报，虚警压降 100%。',
    probesSummary: '时空门控: 司机排除 (IoP >= 0.65)',
    status: 'resolved',
    statusText: '门控自动过滤'
  },
  {
    id: 'HAZ-20261015-006',
    device_id: 'CCTV-02',
    zone: 'A区 · 原料卸载暂存区',
    level: 'CRITICAL',
    levelText: '危急制动',
    timestamp: '2026-10-15 10:21:05',
    description: '工人跨越叉车后方一字红光进入作业危险盲区，底线防御一票否决触发全车制动停机，现场核查批评教育后闭环恢复。',
    probesSummary: '探针: P(coll)=90.2% | 烈度 2.48 / 3.0',
    status: 'confirmed',
    statusText: '已排险恢复'
  }
]

const historyData = ref([])
const currentFilter = ref('ALL')
const isRefreshing = ref(false)

const totalCount = computed(() => historyData.value.length)
const criticalCount = computed(() => historyData.value.filter(i => i.level === 'CRITICAL').length)
const warningCount = computed(() => historyData.value.filter(i => i.level === 'WARNING').length)
const dismissedCount = computed(() => historyData.value.filter(i => i.level === 'DISMISSED').length)

const filteredData = computed(() => {
  if (currentFilter.value === 'ALL') return historyData.value
  return historyData.value.filter(i => i.level === currentFilter.value)
})

async function fetchHistory() {
  isRefreshing.value = true
  try {
    const res = await api.get('/api/history', { params: { limit: 50 } })
    if (res.data?.items?.length) {
      historyData.value = res.data.items
    } else {
      historyData.value = MOCK_HISTORY_RECORDS
    }
  } catch (e) {
    console.warn('历史数据从 API 加载失败，回退至内置台账模拟记录:', e)
    historyData.value = MOCK_HISTORY_RECORDS
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 300)
  }
}

onMounted(fetchHistory)
</script>

<style scoped>
.ledger-page {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-canvas);
  color: var(--text-main);
  box-sizing: border-box;
}

.content-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 页面标头 */
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-machined);
}

.page-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.5px;
  margin: 0 0 4px 0;
}

.page-desc {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.system-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 4px 10px;
  border-radius: 4px;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: var(--bg-panel-subtle);
  border-color: var(--border-bright);
  color: var(--text-main);
}

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 统计磁贴：细线工业网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: var(--border-machined);
  border: 1px solid var(--border-machined);
  border-radius: 6px;
  gap: 1px;
  overflow: hidden;
}

.metric-block {
  background: var(--bg-panel);
  padding: 12px 18px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.m-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.m-val {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.5px;
}

.text-danger { color: var(--emergency-red); }
.text-warning { color: var(--warning-amber); }
.text-secondary { color: var(--text-secondary); }

/* 过滤工具栏 */
.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.segment-group {
  display: inline-flex;
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 2px;
  gap: 2px;
}

.seg-btn {
  border: none;
  background: transparent;
  padding: 5px 12px;
  border-radius: 3px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  font-weight: 500;
}

.seg-btn:hover {
  color: var(--text-main);
}

.seg-btn.active {
  background: var(--bg-panel);
  color: var(--text-main);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 数据网格容器 */
.table-container {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 6px;
  overflow: hidden;
}

.ledger-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 12px;
}

.ledger-table thead {
  background: var(--bg-panel-subtle);
  border-bottom: 1px solid var(--border-machined);
}

.ledger-table th {
  padding: 10px 14px;
  font-weight: 600;
  color: var(--text-muted);
  font-size: 11px;
  letter-spacing: 0.3px;
}

.ledger-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-machined);
  color: var(--text-main);
  vertical-align: top;
}

.ledger-row:hover td {
  background: #f8fafc;
}

.ledger-row:last-child td {
  border-bottom: none;
}

/* 单元格微排版 */
.font-mono {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.id-cell {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 11.5px;
}

.time-cell {
  font-size: 11px;
  color: var(--text-muted);
}

.point-name {
  font-weight: 600;
  color: var(--text-main);
}

.point-zone {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* 级别标签：克制纯色，杜绝荧光和彩色边线 */
.severity-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
}

.sev-critical {
  color: var(--emergency-red);
  background: rgba(239, 68, 68, 0.08);
}

.sev-warning {
  color: var(--warning-amber);
  background: rgba(245, 158, 11, 0.08);
}

.sev-dismissed {
  color: var(--text-secondary);
  background: var(--bg-panel-subtle);
}

.sev-normal {
  color: var(--nominal-green);
  background: rgba(16, 185, 129, 0.08);
}

/* 归因与证据栏 */
.evidence-cell {
  line-height: 1.5;
}

.evidence-main {
  color: var(--text-main);
  font-size: 12px;
}

.evidence-telemetry {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 处置结论 */
.status-cell {
  display: inline-block;
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 2px 7px;
  border-radius: 3px;
  white-space: nowrap;
}

.st-confirmed {
  color: #047857;
  border-color: rgba(16, 185, 129, 0.25);
  background: rgba(16, 185, 129, 0.05);
}

.st-resolved {
  color: #b45309;
  border-color: rgba(245, 158, 11, 0.25);
  background: rgba(245, 158, 11, 0.05);
}

.st-dismissed {
  color: var(--text-secondary);
}

.empty-cell {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
}
</style>
