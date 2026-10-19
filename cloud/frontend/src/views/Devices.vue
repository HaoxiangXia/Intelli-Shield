<template>
  <div class="array-page">
    <div class="content">
      <!-- 页面标头 -->
      <header class="page-header">
        <div class="header-main">
          <div class="header-title-row">
            <h1 class="page-title">视频感知阵列</h1>
            <span class="live-pulse-badge">
              <span class="pulse-dot"></span>
              <span class="badge-text">前哨阵列</span>
            </span>
          </div>
          <div class="subtitle">高位视频感知与车载联锁终端部署台账</div>
        </div>
        <div class="header-actions">
          <div class="officer-chip">
            <span class="officer-dot"></span>
            <span>车载联锁: <strong>STM32 就绪</strong></span>
          </div>
          <div class="ws-status font-mono">
            <span class="ws-dot" :class="{ connected: status === 'ready' }"></span>
            <span>{{ statusText }}</span>
          </div>
        </div>
      </header>

      <!-- 阵列总览：4栏细线网格 -->
      <div class="summary-strip">
        <div class="summary-cell">
          <span class="s-label">接入规模</span>
          <div class="s-val-row">
            <span class="s-value">{{ onlineCount }}</span>
            <span class="s-sub">/ {{ CAMERAS.length }} 路</span>
          </div>
        </div>
        <div class="summary-cell">
          <span class="s-label">险情段落</span>
          <div class="s-val-row">
            <span class="s-value">{{ totalEpisodes }}</span>
            <span class="s-sub">段</span>
          </div>
        </div>
        <div class="summary-cell">
          <span class="s-label">峰值风险</span>
          <div class="s-val-row">
            <span class="s-value" :class="riskClass">{{ peakRiskText }}</span>
          </div>
        </div>
        <div class="summary-cell">
          <span class="s-label">探针平均延时</span>
          <div class="s-val-row">
            <span class="s-value val-cyan">{{ avgLatencyText }}</span>
          </div>
        </div>
      </div>

      <!-- 主从联动战术检视工位 -->
      <div class="tactical-workstation">
        <!-- 左侧：摄像头列表 -->
        <div class="array-sidebar">
          <div class="sidebar-header">
            <span class="sidebar-title">监控节点 ({{ CAMERAS.length }})</span>
          </div>

          <div class="camera-list">
            <article
              v-for="cam in cards"
              :key="cam.id"
              class="cam-card"
              :class="[cam.stateClass, { selected: selected?.id === cam.id }]"
              @click="selectedId = cam.id"
            >
              <div class="cam-card-head">
                <div class="cam-title">
                  <Video :size="14" class="cam-icon" />
                  <span class="cam-id font-mono">{{ cam.id }}</span>
                </div>
                <span class="cam-state" :class="cam.stateClass">{{ cam.stateText }}</span>
              </div>

              <div class="cam-name">{{ cam.name }}</div>

              <div class="cam-meta">
                <span class="meta-chip">{{ cam.zone }}</span>
                <span class="meta-chip">{{ cam.position }}</span>
                <span class="meta-chip font-mono" v-if="cam.hasMetadata">1080P</span>
              </div>

              <!-- 已接入节点缩略与指标 -->
              <div v-if="cam.stats" class="cam-card-body">
                <div class="thumbnail-preview">
                  <img
                    v-if="cam.thumbnail"
                    :src="cam.thumbnail"
                    :alt="cam.id"
                    class="thumb-img"
                  />
                  <div class="thumb-badge font-mono">752 帧 · 4段险情</div>
                </div>

                <div class="stat-mini-row">
                  <div class="mini-item">
                    <span class="mini-k">时长</span>
                    <span class="mini-v font-mono">{{ cam.stats.durationSec.toFixed(1) }}s</span>
                  </div>
                  <div class="mini-item">
                    <span class="mini-k">峰值风险</span>
                    <span class="mini-v font-mono val-danger">{{ cam.stats.peakRiskPct }}%</span>
                  </div>
                  <div class="mini-item">
                    <span class="mini-k">GPU唤醒</span>
                    <span class="mini-v font-mono">{{ cam.stats.gpuActivePct }}%</span>
                  </div>
                </div>

                <div class="split-bar-mini">
                  <div class="seg crit" :style="{ width: `${critPct(cam.stats)}%` }"></div>
                  <div class="seg warn" :style="{ width: `${warnPct(cam.stats)}%` }"></div>
                  <div class="seg safe" :style="{ width: `${cam.stats.safeFramePct}%` }"></div>
                </div>
              </div>

              <!-- 待接入节点规划 -->
              <div v-else class="cam-pending-brief font-mono">
                标高 6.0m · 焦距 4mm · 待接入
              </div>
            </article>
          </div>
        </div>

        <!-- 右侧：当前选中节点检视台 -->
        <div class="tactical-deck">
          <!-- 1. 已接入实测节点 (CCTV-04) -->
          <template v-if="selected?.hasMetadata && selected?.stats">
            <div class="deck-toolbar">
              <div class="deck-title-group">
                <div class="deck-id-badge font-mono">{{ selected.id }}</div>
                <div class="deck-title-text">
                  <span class="title-main">{{ selected.name }}</span>
                  <span class="title-sub">{{ selected.zone }} · {{ selected.position }}</span>
                </div>
              </div>

              <div class="view-mode-tabs">
                <button
                  class="mode-btn"
                  :class="{ active: viewMode === 'video' }"
                  @click="viewMode = 'video'"
                  type="button"
                >
                  <Play :size="12" />
                  <span>实景视频</span>
                </button>
                <button
                  class="mode-btn"
                  :class="{ active: viewMode === 'keyframes' }"
                  @click="viewMode = 'keyframes'"
                  type="button"
                >
                  <Camera :size="12" />
                  <span>特征关键帧 (5帧)</span>
                </button>
              </div>
            </div>

            <!-- 主画面视窗 -->
            <div class="deck-stage">
              <div v-if="viewMode === 'video'" class="stage-media-wrap">
                <video
                  ref="videoPlayerRef"
                  :src="selected.video"
                  class="stage-video"
                  controls
                  playsinline
                  loop
                  muted
                ></video>
                <div class="stage-hud-overlay">
                  <span class="hud-chip font-mono">CCTV-04 · 1080P@25FPS</span>
                  <span class="hud-chip font-mono val-nominal">HPC 联机</span>
                </div>
              </div>

              <div v-else class="stage-keyframes-wrap">
                <div class="kf-main-preview">
                  <img
                    :src="`/samples/cctv/keyframes/${activeKeyframe.file}`"
                    :alt="activeKeyframe.label"
                    class="kf-large-img"
                  />
                  <div class="kf-badge-top font-mono">
                    #{{ activeKeyframe.id }} · {{ activeKeyframe.t.toFixed(1) }}s · {{ activeKeyframe.label }}
                  </div>
                </div>

                <div class="kf-thumb-strip">
                  <div
                    v-for="kf in KEYFRAMES"
                    :key="kf.id"
                    class="kf-thumb-card"
                    :class="{ active: activeKeyframe.id === kf.id }"
                    @click="activeKeyframe = kf"
                  >
                    <img
                      :src="`/samples/cctv/keyframes/${kf.file}`"
                      :alt="kf.label"
                      class="kf-thumb-img"
                    />
                    <div class="kf-thumb-label font-mono">#{{ kf.id }} {{ kf.label }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 探针遥测与联锁状态 -->
            <div class="telemetry-dashboard-grid">
              <div class="telemetry-card">
                <div class="card-head">
                  <Cpu :size="13" class="head-icon" />
                  <span>OmniJev-4B 探针实测极值 (~107ms)</span>
                </div>
                <div class="probe-kv-grid">
                  <div class="probe-kv-item">
                    <span class="p-k">峰值碰撞风险 P(coll)</span>
                    <span class="p-v font-mono val-danger">{{ selected.stats.peakRiskPct }}%</span>
                    <div class="p-mini-bar">
                      <div class="p-bar-fill" :style="{ width: `${selected.stats.peakRiskPct}%`, background: 'var(--emergency-red)' }"></div>
                    </div>
                  </div>
                  <div class="probe-kv-item">
                    <span class="p-k">危害烈度 Score</span>
                    <span class="p-v font-mono val-warning">{{ selected.stats.peakThreatScore }} / 3.0</span>
                    <div class="p-mini-bar">
                      <div class="p-bar-fill" :style="{ width: `${(selected.stats.peakThreatScore / 3.0) * 100}%`, background: 'var(--safety-amber)' }"></div>
                    </div>
                  </div>
                  <div class="probe-kv-item">
                    <span class="p-k">物理间距 (足底-车体)</span>
                    <span class="p-v font-mono">{{ selected.stats.minDistPx }}px ({{ selected.stats.minDistM }}m)</span>
                  </div>
                  <div class="probe-kv-item">
                    <span class="p-k">探针推理延迟</span>
                    <span class="p-v font-mono val-cyan">{{ selected.stats.avgLatencyMs }} ms</span>
                  </div>
                </div>
              </div>

              <div class="telemetry-card">
                <div class="card-head">
                  <ShieldAlert :size="13" class="head-icon" />
                  <span>红光禁区与车载联锁终端</span>
                </div>
                <div class="interlock-details">
                  <div class="i-row">
                    <span class="i-k">三向激光防线:</span>
                    <span class="i-v">左右侧 + 后向 650nm 激光</span>
                  </div>
                  <div class="i-row">
                    <span class="i-k">安全排除多边形:</span>
                    <span class="i-v font-mono">地表红激光凸包</span>
                  </div>
                  <div class="i-row">
                    <span class="i-k">行人接地锚点:</span>
                    <span class="i-v font-mono">(x_foot, y_foot)</span>
                  </div>
                  <div class="i-row">
                    <span class="i-k">车载网关 (STM32):</span>
                    <span class="i-v font-mono val-nominal">接触器常闭 · 联锁就绪</span>
                  </div>
                  <div class="i-row">
                    <span class="i-k">制动原则:</span>
                    <span class="i-v val-danger font-bold">越界一票否决 · 毫秒断电</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 时序险情段落流水 -->
            <div class="episodes-dock">
              <div class="episodes-head">
                <Layers :size="13" class="head-icon" />
                <span>时序险情段落流水 ({{ selected.stats.episodes.length }} 段)</span>
              </div>
              <div class="episodes-grid">
                <div
                  v-for="ep in selected.stats.episodes"
                  :key="ep.id"
                  class="episode-chip"
                  :class="ep.level === 'CRITICAL' ? 'crit' : 'warn'"
                  @click="seekVideoTo(ep.startTime)"
                  title="点击视频跳转至该时序"
                >
                  <div class="ep-top">
                    <span class="ep-id font-mono">{{ ep.id }}</span>
                    <span class="ep-level-tag">{{ ep.level === 'CRITICAL' ? '危急' : '预警' }}</span>
                  </div>
                  <div class="ep-time font-mono">
                    {{ ep.startTime.toFixed(1) }}s ~ {{ ep.endTime.toFixed(1) }}s ({{ ep.durationSec.toFixed(1) }}s)
                  </div>
                  <div class="ep-metrics font-mono">
                    <span>P: {{ ep.collisionRisk }}%</span>
                    <span>烈度: {{ ep.threatScore }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- 2. 待接入节点档案 -->
          <template v-else>
            <div class="pending-terminal">
              <div class="terminal-icon-wrap">
                <Activity :size="24" class="terminal-icon" />
              </div>
              <h2 class="terminal-title">节点 {{ selected?.id }} · 部署规范</h2>

              <div class="terminal-spec-grid">
                <div class="spec-block">
                  <div class="spec-k">覆盖作业区</div>
                  <div class="spec-v">{{ selected?.zone }} · {{ selected?.name }}</div>
                </div>
                <div class="spec-block">
                  <div class="spec-k">安装标高与角度</div>
                  <div class="spec-v font-mono">标高 6.0m · 俯角 45° · 焦距 4mm</div>
                </div>
                <div class="spec-block">
                  <div class="spec-k">视频流协议</div>
                  <div class="spec-v font-mono">RTSP over Gigabit PoE</div>
                </div>
                <div class="spec-block">
                  <div class="spec-k">车载网关终端映射</div>
                  <div class="spec-v font-mono">STM32F407 网关 #{{ selected?.id?.replace(/[^0-9]/g, '') }}</div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Video,
  Play,
  Camera,
  Cpu,
  ShieldAlert,
  Layers,
  Activity
} from 'lucide-vue-next'
import {
  useCctvMetadata,
  CAMERA_REGISTRY,
  summarizeCctvStats
} from '../composables/useCctvMetadata'

const CAMERAS = CAMERA_REGISTRY
const { frames, status, load } = useCctvMetadata()

const selectedId = ref(CAMERAS[0].id)
const viewMode = ref('video')
const videoPlayerRef = ref(null)

const KEYFRAMES = [
  { t: 1.0, id: '0025', file: 'keyframe_0025_01_NORMAL_SAFE.png', label: '常态安全' },
  { t: 8.0, id: '0200', file: 'keyframe_0200_02_WARNING_BUFFER.png', label: '预警缓冲' },
  { t: 13.0, id: '0325', file: 'keyframe_0325_03_WARNING_APPROACH.png', label: '接近警示' },
  { t: 23.0, id: '0575', file: 'keyframe_0575_04_CRITICAL_HAZARD.png', label: '临界碰撞' },
  { t: 28.0, id: '0700', file: 'keyframe_0700_05_NORMAL_CLEARED.png', label: '复位安全' }
]
const activeKeyframe = ref(KEYFRAMES[3])

const statsById = ref({})

const cards = computed(() =>
  CAMERAS.map(cam => {
    const stats = cam.hasMetadata ? statsById.value[cam.id] || null : null
    return {
      ...cam,
      stats,
      stateClass: cam.hasMetadata ? (stats ? 'online' : 'loading') : 'pending',
      stateText: cam.hasMetadata ? (stats ? '在线' : '载入中') : '待接入'
    }
  })
)

const selected = computed(() => cards.value.find(c => c.id === selectedId.value) || cards.value[0])

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
  if (v >= 70) return 'val-danger'
  if (v >= 40) return 'val-warning'
  return 'val-nominal'
})

const avgLatencyText = computed(() => {
  const values = Object.values(statsById.value)
    .map(s => s?.avgLatencyMs)
    .filter(v => Number.isFinite(v))
  if (!values.length) return '--'
  return `${(values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)} ms`
})

const statusText = computed(() => {
  if (status.value === 'ready') return `HPC 就绪 · ${frames.value.length} 帧`
  if (status.value === 'loading') return '载入中...'
  if (status.value === 'error') return '载入失败'
  return '等待接入'
})

function critPct(stats) {
  return +((stats.criticalFrames / stats.totalFrames) * 100).toFixed(1)
}

function warnPct(stats) {
  return +((stats.warningFrames / stats.totalFrames) * 100).toFixed(1)
}

function seekVideoTo(sec) {
  if (videoPlayerRef.value) {
    viewMode.value = 'video'
    videoPlayerRef.value.currentTime = sec
    videoPlayerRef.value.play().catch(() => {})
  }
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
  background: var(--bg-canvas);
  color: var(--text-main);
  box-sizing: border-box;
}

.content {
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

.officer-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.officer-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--telemetry-cyan);
}

.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 4px 8px;
  border-radius: 4px;
}

.ws-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
}

.ws-dot.connected {
  background: var(--nominal-green);
}

/* ── 阵列总览 ────────────────────────────────── */
.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border-machined);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  overflow: hidden;
}

.summary-cell {
  background: var(--bg-panel);
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.s-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.s-val-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.s-value {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.1;
}

.s-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.val-danger { color: var(--emergency-red); }
.val-warning { color: var(--safety-amber); }
.val-cyan { color: var(--telemetry-cyan); }
.val-nominal { color: var(--nominal-green); }
.font-bold { font-weight: 700; }

/* ── 战术工位双列布局 ─────────────────────────────────────────────── */
.tactical-workstation {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 14px;
  align-items: start;
}

/* 左侧：列表侧栏 */
.array-sidebar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 2px;
}

.sidebar-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
}

.camera-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cam-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.cam-card:hover {
  border-color: var(--border-bright);
}

.cam-card.selected {
  border-color: var(--telemetry-cyan);
  box-shadow: 0 0 0 1px var(--telemetry-cyan);
  background: var(--bg-panel-subtle);
}

.cam-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cam-title {
  display: flex;
  align-items: center;
  gap: 5px;
}

.cam-icon {
  color: var(--telemetry-cyan);
}

.cam-id {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
}

.cam-state {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 2px;
}

.cam-state.online {
  color: var(--nominal-green);
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.3);
}

.cam-state.pending {
  color: var(--text-muted);
  background: #f1f5f9;
  border: 1px solid var(--border-machined);
}

.cam-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
}

.cam-meta {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.meta-chip {
  font-size: 10px;
  color: var(--text-secondary);
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 1px 4px;
  border-radius: 2px;
}

.cam-card-body {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 3px;
  padding-top: 6px;
  border-top: 1px dashed var(--border-machined);
}

.thumbnail-preview {
  position: relative;
  width: 100%;
  height: 64px;
  background: #000;
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid var(--border-machined);
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.9;
}

.thumb-badge {
  position: absolute;
  bottom: 3px;
  left: 3px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 2px;
}

.stat-mini-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  text-align: center;
}

.mini-item {
  display: flex;
  flex-direction: column;
}

.mini-k {
  font-size: 9px;
  color: var(--text-muted);
}

.mini-v {
  font-size: 11px;
  font-weight: 700;
}

.split-bar-mini {
  display: flex;
  height: 3px;
  background: #e2e8f0;
  border-radius: 1.5px;
  overflow: hidden;
}

.split-bar-mini .seg { height: 100%; }
.split-bar-mini .crit { background: var(--emergency-red); }
.split-bar-mini .warn { background: var(--safety-amber); }
.split-bar-mini .safe { background: var(--nominal-green); }

.cam-pending-brief {
  margin-top: 2px;
  padding-top: 4px;
  border-top: 1px dashed var(--border-machined);
  font-size: 10px;
  color: var(--text-muted);
}

/* 右侧：战术检视工位 */
.tactical-deck {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.deck-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-machined);
}

.deck-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.deck-id-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.3);
  padding: 2px 6px;
  border-radius: 3px;
}

.deck-title-text {
  display: flex;
  flex-direction: column;
}

.title-main {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

.title-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.view-mode-tabs {
  display: flex;
  gap: 4px;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
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

.mode-btn:hover {
  border-color: var(--border-bright);
  color: var(--text-main);
}

.mode-btn.active {
  background: var(--telemetry-cyan);
  border-color: var(--telemetry-cyan);
  color: #fff;
}

/* 主画面区域 */
.deck-stage {
  position: relative;
  width: 100%;
  background: #000;
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  overflow: hidden;
}

.stage-media-wrap {
  position: relative;
  width: 100%;
  height: 340px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.stage-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.stage-hud-overlay {
  position: absolute;
  top: 6px;
  left: 6px;
  display: flex;
  gap: 6px;
  z-index: 5;
}

.hud-chip {
  background: rgba(0, 0, 0, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 2px;
}

.stage-keyframes-wrap {
  display: flex;
  flex-direction: column;
  background: #000;
}

.kf-main-preview {
  position: relative;
  width: 100%;
  height: 290px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kf-large-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.kf-badge-top {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 2px;
}

.kf-thumb-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  padding: 6px;
  background: #0a0e17;
  border-top: 1px solid #1e293b;
}

.kf-thumb-card {
  border: 1px solid #334155;
  border-radius: 2px;
  overflow: hidden;
  cursor: pointer;
  opacity: 0.7;
  transition: all 0.15s ease;
}

.kf-thumb-card:hover {
  opacity: 1;
  border-color: #94a3b8;
}

.kf-thumb-card.active {
  opacity: 1;
  border-color: var(--telemetry-cyan);
}

.kf-thumb-img {
  width: 100%;
  height: 42px;
  object-fit: cover;
  display: block;
}

.kf-thumb-label {
  font-size: 9px;
  color: #cbd5e1;
  text-align: center;
  padding: 1px 0;
  background: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 遥测与仪表盘网格 */
.telemetry-dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.telemetry-card {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-main);
}

.head-icon {
  color: var(--telemetry-cyan);
}

.probe-kv-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.probe-kv-item {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.p-k {
  font-size: 10px;
  color: var(--text-muted);
}

.p-v {
  font-size: 13px;
  font-weight: 700;
}

.p-mini-bar {
  width: 100%;
  height: 3px;
  background: #e2e8f0;
  border-radius: 1.5px;
  overflow: hidden;
  margin-top: 2px;
}

.p-bar-fill {
  height: 100%;
}

.interlock-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.i-row {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  font-size: 11px;
}

.i-k {
  color: var(--text-muted);
}

.i-v {
  font-weight: 600;
  color: var(--text-main);
  text-align: right;
}

/* 时序险情段落坞 */
.episodes-dock {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episodes-head {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-main);
}

.episodes-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.episode-chip {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  padding: 6px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.episode-chip:hover {
  border-color: var(--telemetry-cyan);
}

.episode-chip.crit {
  border-left: 3px solid var(--emergency-red);
}

.episode-chip.warn {
  border-left: 3px solid var(--safety-amber);
}

.ep-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ep-id {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-main);
}

.ep-level-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 3px;
  border-radius: 2px;
}

.crit .ep-level-tag {
  color: var(--emergency-red);
  background: var(--emergency-red-dim);
}

.warn .ep-level-tag {
  color: var(--safety-amber);
  background: var(--safety-amber-dim);
}

.ep-time {
  font-size: 10px;
  color: var(--text-muted);
}

.ep-metrics {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-secondary);
}

/* 待接入终端档案态 */
.pending-terminal {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  text-align: center;
  gap: 10px;
}

.terminal-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 4px;
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  display: flex;
  align-items: center;
  justify-content: center;
}

.terminal-icon {
  color: var(--telemetry-cyan);
}

.terminal-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.terminal-spec-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  width: 100%;
  max-width: 520px;
  margin-top: 8px;
  text-align: left;
}

.spec-block {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.spec-block .spec-k {
  font-size: 10px;
  color: var(--text-muted);
}

.spec-block .spec-v {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
}

@media (max-width: 1024px) {
  .tactical-workstation {
    grid-template-columns: 1fr;
  }
  .summary-strip {
    grid-template-columns: repeat(2, 1fr);
  }
  .telemetry-dashboard-grid {
    grid-template-columns: 1fr;
  }
  .episodes-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
