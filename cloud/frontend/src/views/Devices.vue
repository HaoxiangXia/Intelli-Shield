<template>
  <div class="array-page">
    <div class="content">
      <header class="page-header">
        <div>
          <h1>视频感知阵列</h1>
          <div class="subtitle">Perception Camera Array · 双系统认知探针前哨部署台账</div>
        </div>
        <div class="ws-status">
          <span class="ws-dot" :class="{ connected: status === 'ready' }"></span>
          <span>{{ statusText }}</span>
        </div>
      </header>

      <!-- 阵列总览 -->
      <div class="summary-strip">
        <div class="summary-cell">
          <span class="s-label">接入摄像头</span>
          <span class="s-value">{{ onlineCount }}<span class="s-sub">/ {{ CAMERAS.length }}</span></span>
        </div>
        <div class="summary-cell">
          <span class="s-label">险情段合计</span>
          <span class="s-value">{{ totalEpisodes }}<span class="s-sub">段</span></span>
        </div>
        <div class="summary-cell">
          <span class="s-label">峰值碰撞风险</span>
          <span class="s-value" :class="riskClass">{{ peakRiskText }}</span>
        </div>
        <div class="summary-cell">
          <span class="s-label">OmniJev 探针延迟</span>
          <span class="s-value">{{ avgLatencyText }}</span>
        </div>
      </div>

      <!-- 摄像头卡片阵列 -->
      <div class="camera-grid">
        <article
          v-for="cam in cards"
          :key="cam.id"
          class="cam-card"
          :class="[cam.stateClass, { selected: selected?.id === cam.id }]"
          @click="selectedId = cam.id"
        >
          <div class="cam-card-head">
            <div class="cam-title">
              <Video :size="15" class="cam-icon" />
              <span class="cam-id">{{ cam.id }}</span>
            </div>
            <span class="cam-state" :class="cam.stateClass">{{ cam.stateText }}</span>
          </div>

          <div class="cam-name">{{ cam.name }}</div>
          <div class="cam-meta">
            <span class="meta-chip">{{ cam.zone }}</span>
            <span class="meta-chip">{{ cam.position }}</span>
          </div>

          <!-- 已接入: 实测时序统计 -->
          <div v-if="cam.stats" class="cam-stats">
            <div class="stat-row">
              <div class="stat-item">
                <span class="st-label">分析帧数</span>
                <span class="st-value">{{ cam.stats.totalFrames }} 帧</span>
              </div>
              <div class="stat-item">
                <span class="st-label">时序长度</span>
                <span class="st-value">{{ cam.stats.durationSec.toFixed(2) }} 秒</span>
              </div>
            </div>

            <div class="stat-row">
              <div class="stat-item">
                <span class="st-label">险情帧占比</span>
                <span class="st-value danger">{{ cam.stats.dangerFramePct }}%</span>
              </div>
              <div class="stat-item">
                <span class="st-label">险情段</span>
                <span class="st-value">{{ cam.stats.episodes.length }} 段</span>
              </div>
            </div>

            <div class="bar-title">风险帧 / 安全帧分布</div>
            <div class="split-bar">
              <div class="seg crit" :style="{ width: `${critPct(cam.stats)}%` }"></div>
              <div class="seg warn" :style="{ width: `${warnPct(cam.stats)}%` }"></div>
              <div class="seg safe" :style="{ width: `${cam.stats.safeFramePct}%` }"></div>
            </div>
            <div class="split-legend">
              <span><i class="dot crit"></i>CRITICAL {{ critPct(cam.stats) }}%</span>
              <span><i class="dot warn"></i>WARNING {{ warnPct(cam.stats) }}%</span>
              <span><i class="dot safe"></i>NORMAL {{ cam.stats.safeFramePct }}%</span>
            </div>

            <dl class="cam-kv">
              <div><dt>峰值碰撞风险</dt><dd class="danger">{{ cam.stats.peakRiskPct }}%</dd></div>
              <div><dt>峰值危害烈度</dt><dd class="danger">{{ cam.stats.peakThreatScore }} / 3.0</dd></div>
              <div><dt>最近物理间距</dt><dd>{{ cam.stats.minDistPx }}px ({{ cam.stats.minDistM }}m)</dd></div>
              <div><dt>门控 GPU 唤醒率</dt><dd>{{ cam.stats.gpuActivePct }}%</dd></div>
              <div><dt>司机排除累计</dt><dd>{{ cam.stats.driverExcludedTotal }} 次</dd></div>
              <div><dt>平均探针延迟</dt><dd>{{ cam.stats.avgLatencyMs }} 毫秒</dd></div>
            </dl>

            <div v-if="cam.stats.episodes.length" class="cam-episodes">
              <div class="ep-title">险情段落</div>
              <div v-for="ep in cam.stats.episodes" :key="ep.id" class="ep-item">
                <span class="ep-id">{{ ep.id }}</span>
                <span class="ep-range">{{ ep.startTime.toFixed(2) }}s ~ {{ ep.endTime.toFixed(2) }}s</span>
                <span class="ep-tag" :class="ep.level === 'CRITICAL' ? 'crit' : 'warn'">
                  {{ ep.level === 'CRITICAL' ? 'CRITICAL' : 'WARNING' }}
                </span>
              </div>
            </div>
          </div>

          <!-- 未接入: 显式声明, 不填充任何指标 -->
          <div v-else class="cam-pending">
            <AlertCircle :size="18" class="pending-icon" />
            <div class="pending-title">采集端未接入</div>
            <div class="pending-desc">
              该路摄像头尚未完成 HPC 端 YOLO + OmniJev-4B 时序推理，暂无实测帧元数据。
            </div>
            <div class="pending-spec">
              规划接入后输出：感知帧元数据 · 红光禁区多边形 · 三路认知探针
            </div>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Video, AlertCircle } from 'lucide-vue-next'
import {
  useCctvMetadata,
  CAMERA_REGISTRY,
  summarizeCctvStats
} from '../composables/useCctvMetadata'

const CAMERAS = CAMERA_REGISTRY

const { frames, status, load } = useCctvMetadata()

const selectedId = ref(CAMERAS[0].id)

// 仅对已跑通 HPC 采集的路注入实测统计; 其余保持"未接入", 不做任何填充
const statsById = ref({})

const cards = computed(() =>
  CAMERAS.map(cam => {
    const stats = cam.hasMetadata ? statsById.value[cam.id] || null : null
    return {
      ...cam,
      stats,
      stateClass: cam.hasMetadata ? (stats ? 'online' : 'loading') : 'pending',
      stateText: cam.hasMetadata ? (stats ? '在线 · 实时接入' : '载入中') : '未接入'
    }
  })
)

const selected = computed(() => cards.value.find(c => c.id === selectedId.value) || null)

const onlineCount = computed(() => CAMERAS.filter(c => c.hasMetadata).length)

const totalEpisodes = computed(() =>
  Object.values(statsById.value).reduce((sum, s) => sum + (s?.episodes.length || 0), 0)
)

const peakRiskPct = computed(() => {
  const values = Object.values(statsById.value)
    .map(s => s?.peakRiskPct || 0)
    .filter(v => v > 0)
  return values.length ? Math.max(...values) : 0
})

const peakRiskText = computed(() =>
  peakRiskPct.value ? `${peakRiskPct.value}%` : '--'
)

const riskClass = computed(() => {
  const v = peakRiskPct.value
  if (v >= 70) return 'danger'
  if (v >= 40) return 'warn'
  return 'ok'
})

const avgLatencyText = computed(() => {
  const values = Object.values(statsById.value)
    .map(s => s?.avgLatencyMs)
    .filter(v => Number.isFinite(v))
  if (!values.length) return '--'
  return `${(values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)} 毫秒`
})

const statusText = computed(() => {
  if (status.value === 'ready') return `元数据已载入 · ${frames.value.length} 帧`
  if (status.value === 'loading') return '正在载入 HPC 元数据...'
  if (status.value === 'error') return '元数据载入失败'
  return '等待接入'
})

function critPct(stats) {
  return +((stats.criticalFrames / stats.totalFrames) * 100).toFixed(1)
}

function warnPct(stats) {
  return +((stats.warningFrames / stats.totalFrames) * 100).toFixed(1)
}

onMounted(async () => {
  const loaded = await load()
  if (!loaded.length) return
  const stats = summarizeCctvStats(loaded)
  for (const cam of CAMERAS) {
    if (cam.hasMetadata) statsById.value[cam.id] = stats
  }
})
</script>

<style scoped>
.array-page {
  height: 100%;
  overflow-y: auto;
}

.content {
  padding: 20px 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: page-reveal 0.5s cubic-bezier(0.4, 0, 0.2, 1) both;
}

@keyframes page-reveal {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  margin-top: 3px;
}

.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.ws-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-muted);
}

.ws-dot.connected {
  background: var(--nominal-green);
  box-shadow: 0 0 6px var(--nominal-green);
}

/* ── 阵列总览 ───────────────────────────────────────────────────────── */
.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border-machined);
  border: 1px solid var(--border-machined);
}

.summary-cell {
  background: var(--bg-panel);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.s-label {
  font-size: 11px;
  color: var(--text-muted);
}

.s-value {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
}

.s-value.danger { color: var(--emergency-red); }
.s-value.warn { color: var(--safety-amber); }
.s-value.ok { color: var(--nominal-green); }

.s-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 4px;
  font-weight: 400;
}

/* ── 摄像头卡片 ─────────────────────────────────────────────────────── */
.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
  gap: 14px;
}

.cam-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-left: 3px solid var(--text-muted);
  padding: 14px 16px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cam-card:hover {
  border-color: var(--border-bright);
}

.cam-card.online {
  border-left-color: var(--nominal-green);
}

.cam-card.pending {
  border-left-color: var(--border-bright);
  background: var(--bg-panel-subtle);
}

.cam-card.selected {
  box-shadow: inset 0 0 0 1px var(--telemetry-cyan);
}

.cam-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.cam-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cam-icon {
  color: var(--telemetry-cyan);
}

.cam-id {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

.cam-state {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border: 1px solid currentColor;
}

.cam-state.online { color: var(--nominal-green); }
.cam-state.pending { color: var(--text-muted); }
.cam-state.loading { color: var(--safety-amber); }

.cam-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.cam-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.meta-chip {
  font-size: 10px;
  color: var(--text-secondary);
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 2px 6px;
}

/* ── 实测指标 ───────────────────────────────────────────────────────── */
.cam-stats {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-top: 4px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-machined);
}

.stat-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.st-label {
  font-size: 10px;
  color: var(--text-muted);
}

.st-value {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}

.st-value.danger { color: var(--emergency-red); }

.bar-title {
  font-size: 10px;
  color: var(--text-muted);
}

.split-bar {
  display: flex;
  height: 8px;
  border: 1px solid var(--border-machined);
  overflow: hidden;
}

.split-bar .seg { height: 100%; }
.split-bar .crit { background: var(--emergency-red); }
.split-bar .warn { background: var(--safety-amber); }
.split-bar .safe { background: var(--nominal-green); }

.split-legend {
  display: flex;
  gap: 10px;
  font-size: 10px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.split-legend .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 3px;
}

.split-legend .dot.crit { background: var(--emergency-red); }
.split-legend .dot.warn { background: var(--safety-amber); }
.split-legend .dot.safe { background: var(--nominal-green); }

.cam-kv {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.cam-kv > div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
}

.cam-kv dt {
  color: var(--text-muted);
}

.cam-kv dd {
  margin: 0;
  font-family: var(--font-mono);
  color: var(--text-main);
  font-weight: 600;
}

.cam-kv dd.danger { color: var(--emergency-red); }

.cam-episodes {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px dashed var(--border-machined);
}

.ep-title {
  font-size: 10px;
  color: var(--text-muted);
}

.ep-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
}

.ep-id {
  color: var(--text-main);
  font-weight: 700;
}

.ep-range {
  color: var(--text-secondary);
  flex: 1;
}

.ep-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  border: 1px solid currentColor;
}

.ep-tag.crit { color: var(--emergency-red); }
.ep-tag.warn { color: var(--safety-amber); }

/* ── 未接入态 ───────────────────────────────────────────────────────── */
.cam-pending {
  margin-top: 4px;
  padding: 14px 12px;
  border: 1px dashed var(--border-bright);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.pending-icon {
  color: var(--text-muted);
}

.pending-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}

.pending-desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.6;
}

.pending-spec {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  padding-top: 6px;
  border-top: 1px dashed var(--border-machined);
  width: 100%;
}
</style>