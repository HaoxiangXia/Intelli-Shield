<template>
  <div class="video-analysis-viewport">
    <!-- 顶部操作栏 -->
    <div class="panel-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-title">实景监控视频智能推演</span>
      </div>
      <div class="toolbar-right">
        <!-- 主运行/暂停按钮 -->
        <button
          class="run-control-btn"
          :class="{ 'is-running': isRunning }"
          @click="togglePlay"
        >
          <Pause v-if="isRunning" :size="13" class="btn-icon" />
          <Play v-else :size="13" class="btn-icon" />
          <span>{{ isRunning ? '暂停推演演示' : '开始运行演示' }}</span>
        </button>

        <!-- 动态 AI 标注层显隐切换按钮 -->
        <button
          class="tool-btn"
          :class="{ active: showAiOverlay }"
          @click="showAiOverlay = !showAiOverlay"
        >
          <Crosshair :size="13" class="tool-btn-icon" />
          <span>{{ showAiOverlay ? '隐藏 AI 视觉模型标注层' : '显示 AI 视觉模型标注层' }}</span>
        </button>

        <!-- 三向红光区域显隐切换按钮 -->
        <button
          class="tool-btn"
          :class="{ active: showRedZone }"
          @click="showRedZone = !showRedZone"
        >
          <ShieldAlert :size="13" class="tool-btn-icon" />
          <span>{{ showRedZone ? '隐藏三向红光区' : '显示三向红光区' }}</span>
        </button>

        <!-- 重置按钮 -->
        <button class="tool-btn" @click="resetToBeginning">
          <RotateCcw :size="13" class="tool-btn-icon" />
          <span>重置片头</span>
        </button>
      </div>
    </div>

    <!-- 主视频播放舞台 -->
    <div class="main-video-stage" ref="stageRef">
      <div class="video-player-container" ref="containerRef">
        <!-- 原生视频组件 -->
        <video
          ref="videoRef"
          src="/samples/cctv/videos/output_video7.mp4"
          class="main-cctv-video"
          playsinline
          loop
          :muted="isMuted"
          @timeupdate="onTimeUpdate"
          @play="isRunning = true"
          @pause="isRunning = false"
          @loadedmetadata="onVideoLoaded"
        ></video>

        <!-- 动态数据驱动的 SVG 标注图层 (根据 JSON 精确像素绘制) -->
        <svg
          v-if="showAiOverlay && currentFrameData"
          class="ai-canvas-svg"
          :style="svgLayerStyle"
        >
          <defs>
            <linearGradient id="beamGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#ff3b30" />
              <stop offset="100%" stop-color="#ff9f0a" />
            </linearGradient>
          </defs>

          <!-- 0. 叉车三向红光安全禁区多边形 (Ground Optical Red-Zone Polygon) -->
          <template v-if="showRedZone">
            <g v-for="(polyPoints, pIdx) in scaledRedZonePolygons" :key="'rz-' + pIdx">
              <polygon
                :points="polyPoints"
                :fill="isCriticalAlarm ? 'rgba(239, 68, 68, 0.24)' : (isWarningAlarm ? 'rgba(245, 158, 11, 0.20)' : 'rgba(16, 185, 129, 0.12)')"
                :stroke="isCriticalAlarm ? '#ff3b30' : (isWarningAlarm ? '#ff9f0a' : '#10b981')"
                stroke-width="2.5"
                stroke-dasharray="8,4"
              />
            </g>
          </template>
          <!-- 1. 动态绘制当前帧检出的所有 YOLO 目标框 -->
          <g v-for="(box, bIdx) in scaledDetections" :key="bIdx">
            <rect
              :x="box.x"
              :y="box.y"
              :width="box.w"
              :height="box.h"
              fill="none"
              :stroke="box.color"
              stroke-width="2"
              :stroke-dasharray="box.isDanger ? 'none' : '4,2'"
              rx="2"
            />
            <rect
              :x="box.x"
              :y="Math.max(0, box.y - 20)"
              :width="box.tagW"
              height="20"
              :fill="box.color"
              rx="2"
            />
            <text
              :x="box.x + 6"
              :y="Math.max(0, box.y - 20) + 14"
              fill="#000"
              font-size="11"
              font-weight="700"
              font-family="'PingFang SC', -apple-system, sans-serif"
            >
              {{ box.label }}
            </text>
          </g>

          <!-- 2. 地面行人足底接地点准星与红光边界拓扑标牌 -->
          <g v-for="(anchor, aIdx) in scaledFootAnchors" :key="'fa-' + aIdx">
            <circle :cx="anchor.x" :cy="anchor.y" r="10" fill="none" :stroke="anchor.color" stroke-width="2" />
            <circle :cx="anchor.x" :cy="anchor.y" r="4" :fill="anchor.color" />
            <line :x1="anchor.x - 14" :y1="anchor.y" :x2="anchor.x + 14" :y2="anchor.y" :stroke="anchor.color" stroke-width="1.8" />
            <line :x1="anchor.x" :y1="anchor.y - 14" :x2="anchor.x" :y2="anchor.y + 14" :stroke="anchor.color" stroke-width="1.8" />
            <g :transform="`translate(${anchor.x}, ${anchor.y + 22})`">
              <rect x="-82" y="-11" width="164" height="22" fill="rgba(15, 23, 42, 0.9)" :stroke="anchor.color" stroke-width="1.5" rx="3" />
              <text
                x="0"
                y="4"
                text-anchor="middle"
                :fill="anchor.color"
                font-size="10.5"
                font-weight="700"
                font-family="'PingFang SC', 'JetBrains Mono', monospace"
              >
                {{ anchor.badgeText }}
              </text>
            </g>
          </g>
        </svg>

        <!-- 顶部监控画面信息水印 -->
        <div class="camera-hud-top">
          <div class="cam-info-pill">
            <span class="live-dot" :class="{ running: isRunning }"></span>
            <span class="cam-name">CCTV-04 仓库主干道 (中转区南段)</span>
          </div>
          <div class="omnijev-capsule">
            <div class="capsule-col">
              <span class="capsule-label">三向红光物理边界</span>
              <span
                class="capsule-value"
                :class="isCriticalAlarm ? 'val-danger' : (isWarningAlarm ? 'val-warning' : 'val-safe')"
              >
                {{ redZoneSummaryText }}
              </span>
            </div>
            <div class="capsule-col">
              <span class="capsule-label">碰撞风险概率</span>
              <span
                class="capsule-value"
                :class="isCriticalAlarm ? 'val-danger' : (isWarningAlarm ? 'val-warning' : 'val-safe')"
              >
                {{ ((currentProbes.collision_risk || 0.12) * 100).toFixed(1) }}%
              </span>
            </div>
            <div class="capsule-col">
              <span class="capsule-label">综合危害烈度 (4级)</span>
              <span
                class="capsule-value"
                :class="threatTier.cls"
                :style="{ color: threatTier.color }"
              >
                {{ (currentProbes.threat_score ?? 0.45).toFixed(2) }} / 3.0 ({{ threatTier.text }})
              </span>
            </div>
          </div>
        </div>

        <!-- 底部视频控制栏与关键时序跳转 -->
        <div class="video-control-bar">
          <div class="timeline-scrubber-wrap">
            <div class="timeline-timecode-badge">
              <span class="cam-timecode">{{ formattedTimecode }}</span>
            </div>
            <input
              type="range"
              min="0"
              :max="duration || 30"
              step="0.04"
              v-model="currentTime"
              @input="onSeek"
              class="video-range-slider"
            />
          </div>

          <div class="keyframe-jump-strip">
            <span class="strip-label">关键时序节点跳转:</span>
            <button class="seek-chip" @click="seekTo(1.0)">
              <ShieldCheck :size="12" class="chip-icon safe-icon" />
              <span>01秒 红光外安全 (帧 #0026)</span>
            </button>
            <button class="seek-chip" @click="seekTo(2.7)">
              <AlertCircle :size="12" class="chip-icon warn-icon" />
              <span>03秒 0~0.3m缓冲预警 (帧 #0068)</span>
            </button>
            <button class="seek-chip chip-critical" @click="seekTo(8.0)">
              <AlertTriangle :size="12" class="chip-icon danger-icon" />
              <span>08秒 越过红线告警 (帧 #0201)</span>
            </button>
            <button class="seek-chip chip-critical" @click="seekTo(23.0)">
              <Flame :size="12" class="chip-icon danger-icon" />
              <span>23秒 红区内高危交汇 (帧 #0575)</span>
            </button>
            <button class="seek-chip" @click="seekTo(28.0)">
              <Shield :size="12" class="chip-icon safe-icon" />
              <span>28秒 驶离红线复位 (帧 #0701)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Play,
  Pause,
  Crosshair,
  RotateCcw,
  ShieldCheck,
  AlertCircle,
  AlertTriangle,
  Flame,
  Shield,
  ShieldAlert
} from 'lucide-vue-next'
import { useCctvMetadata } from '../../composables/useCctvMetadata'

const props = defineProps({
  activeHazard: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['time-update', 'open-hd'])

const videoRef = ref(null)
const containerRef = ref(null)
const isRunning = ref(false)
const isMuted = ref(true)
const showAiOverlay = ref(true)
const showRedZone = ref(true) // 默认开启三向红光区域渲染，支持按钮切换
const currentTime = ref(0)
const duration = ref(30.08)
// JSON 帧数据集 (从 HPC 生成的 752 帧元数据载入, 与告警流水共享同一单例)
const { frames: metadataFrames, metadata: cctvMetadata, load: loadMetadata } = useCctvMetadata()
const videoNativeW = ref(1920)
const videoNativeH = ref(1080)

// 屏幕渲染比例计算
const displayMetrics = ref({
  width: 1920,
  height: 1080,
  left: 0,
  top: 0
})

// 查找当前视频播放时间点对应的 JSON 帧
// 查找当前视频播放时间点对应的 JSON 帧 (自适应时间戳对齐，支持任意帧率数据集)
const currentFrameData = computed(() => {
  const framesList = metadataFrames.value
  if (!framesList || framesList.length === 0) return null
  const targetTime = currentTime.value
  const total = framesList.length

  // 快速基于实际帧率估算初始下标
  const fps = Number(cctvMetadata.value?.fps || (total > 350 ? 25.0 : 10.0))
  const estimatedIdx = Math.max(0, Math.min(total - 1, Math.round(targetTime * fps)))
  const cand = framesList[estimatedIdx]
  if (cand && Math.abs(cand.timestamp - targetTime) <= 0.02) {
    return cand
  }

  // 二分查找最贴近当前视频播放时间戳的帧
  let low = 0
  let high = total - 1
  let best = cand || framesList[0]
  let minDiff = Math.abs(best.timestamp - targetTime)

  while (low <= high) {
    const mid = (low + high) >> 1
    const item = framesList[mid]
    const diff = Math.abs(item.timestamp - targetTime)
    if (diff < minDiff) {
      minDiff = diff
      best = item
    }
    if (item.timestamp < targetTime) {
      low = mid + 1
    } else if (item.timestamp > targetTime) {
      high = mid - 1
    } else {
      return item
    }
  }
  return best
})

const currentProbes = computed(() => {
  return currentFrameData.value?.probes || {
    collision_risk: 0.12,
    threat_score: 0.45,
    latency_ms: 107.4,
    worker_awareness: { unaware: 0.05, yielding: 0.15, separated: 0.80 }
  }
})

const isCriticalAlarm = computed(() => {
  return currentFrameData.value?.alarm_level === 'CRITICAL'
})

const isWarningAlarm = computed(() => {
  return currentFrameData.value?.alarm_level === 'WARNING'
})

const redZoneSummaryText = computed(() => {
  const rz = currentFrameData.value?.red_zone
  if (!rz) {
    return isCriticalAlarm.value ? '侵入红线' : '红线外'
  }
  if (rz.state === 'INSIDE') {
    return '侵入红线'
  }
  if (rz.state === 'BUFFER') {
    return '临界缓冲'
  }
  return '红线外'
})

const threatTier = computed(() => {
  const t = Number(currentProbes.value.threat_score ?? 0.45)
  if (t >= 2.2) return { text: 'Level 3 紧迫危险', cls: 'threat-level-3', color: '#EF4444' }
  if (t >= 1.5) return { text: 'Level 2 临界预警', cls: 'threat-level-2', color: '#F59E0B' }
  if (t >= 0.5) return { text: 'Level 1 低度注意', cls: 'threat-level-1', color: '#38BDF8' }
  return { text: 'Level 0 正常受控', cls: 'threat-level-0', color: '#10B981' }
})

const formattedTimecode = computed(() => {
  const t = currentTime.value
  const mins = Math.floor(t / 60)
  const secs = Math.floor(t % 60)
  const ms = Math.floor((t % 1) * 100)
  const pad = (n, l = 2) => String(n).padStart(l, '0')
  const fid = currentFrameData.value?.frame_id || (Math.floor(t * 10) + 1)
  return `${pad(mins)}:${pad(secs)}.${pad(ms)} (帧 #${fid})`
})

// 将 1920x1080 坐标动态换算为页面显示的实际位置
const scaledDetections = computed(() => {
  if (!currentFrameData.value || !currentFrameData.value.detections) return []
  const { width: dW, height: dH, left: dL, top: dT } = displayMetrics.value
  const scaleX = dW / videoNativeW.value
  const scaleY = dH / videoNativeH.value

  const allowedClasses = new Set(['person', 'pedestrian', 'truck', 'truckHead', 'smallTruck', 'forkTruck', 'forklift'])

  return currentFrameData.value.detections
    .filter(det => allowedClasses.has(det.class_name))
    .map(det => {
    const [x1, y1, x2, y2] = det.bbox
    const rawClass = det.class_name
    const conf = Math.round((det.confidence || 0) * 100)
    const label = `${rawClass} ${conf}%`
    const isDanger = isCriticalAlarm.value

    let color = '#0284c7'
    if (rawClass === 'person') {
      color = isDanger ? '#dc2626' : '#d97706'
    } else if (rawClass === 'forkTruck') {
      color = '#e11d48'
    } else if (rawClass === 'truck' || rawClass === 'truckHead' || rawClass === 'smallTruck') {
      color = '#0284c7'
    } else if (rawClass.toLowerCase().includes('helmet')) {
      color = '#16a34a'
    } else if (rawClass === 'cell phone') {
      color = '#9333ea'
    }

    const tagW = Math.max(76, label.length * 8 + 12)
    return {
      x: dL + x1 * scaleX,
      y: dT + y1 * scaleY,
      w: (x2 - x1) * scaleX,
      h: (y2 - y1) * scaleY,
      label,
      color,
      tagW,
      isDanger
    }
  })
})

// 绘制地面三向红光安全禁区多边形
const scaledRedZonePolygons = computed(() => {
  const polys = currentFrameData.value?.red_zone?.polygons
  if (!polys || !Array.isArray(polys)) return []
  const { width: dW, height: dH, left: dL, top: dT } = displayMetrics.value
  const scaleX = dW / videoNativeW.value
  const scaleY = dH / videoNativeH.value

  return polys.map(poly =>
    poly
      .map(([px, py]) => `${(dL + px * scaleX).toFixed(1)},${(dT + py * scaleY).toFixed(1)}`)
      .join(' ')
  )
})

// 绘制地面行人足底接地点锚点与红光距离标牌
const scaledFootAnchors = computed(() => {
  const rz = currentFrameData.value?.red_zone
  const anchors = rz?.foot_anchors
  if (!anchors || !Array.isArray(anchors)) return []
  const { width: dW, height: dH, left: dL, top: dT } = displayMetrics.value
  const scaleX = dW / videoNativeW.value
  const scaleY = dH / videoNativeH.value

  const distM = rz.min_dist_m !== null && rz.min_dist_m !== undefined ? Number(rz.min_dist_m) : 0
  let color = '#10b981'
  let badgeText = `[安全] 红线外 +${distM.toFixed(2)}m`
  if (rz.state === 'INSIDE') {
    color = '#ff3b30'
    badgeText = `[越界] 足底越过红线: ${distM.toFixed(2)}m`
  } else if (rz.state === 'BUFFER') {
    color = '#ff9f0a'
    badgeText = `[缓冲] 0~0.3m缓冲带: +${distM.toFixed(2)}m`
  }

  return anchors.slice(0, 1).map(([fx, fy]) => ({
    x: dL + fx * scaleX,
    y: dT + fy * scaleY,
    color,
    badgeText
  }))
})

const svgLayerStyle = computed(() => {
  return {
    position: 'absolute',
    top: '0px',
    left: '0px',
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    zIndex: 8
  }
})

// 计算视频实际显示尺寸与黑边偏移 (object-fit: contain)
function updateDisplayMetrics() {
  if (!videoRef.value || !containerRef.value) return
  const containerRect = containerRef.value.getBoundingClientRect()
  const cW = containerRect.width
  const cH = containerRect.height
  const vRatio = videoNativeW.value / videoNativeH.value
  const cRatio = cW / cH

  let dW, dH, dL, dT
  if (cRatio > vRatio) {
    dH = cH
    dW = cH * vRatio
    dL = (cW - dW) / 2
    dT = 0
  } else {
    dW = cW
    dH = cW / vRatio
    dL = 0
    dT = (cH - dH) / 2
  }

  displayMetrics.value = {
    width: dW,
    height: dH,
    left: dL,
    top: dT
  }
}

function onVideoLoaded() {
  if (videoRef.value) {
    videoNativeW.value = videoRef.value.videoWidth || 1920
    videoNativeH.value = videoRef.value.videoHeight || 1080
    duration.value = videoRef.value.duration || 30.08
    updateDisplayMetrics()
  }
}

function togglePlay() {
  if (!videoRef.value) return
  if (videoRef.value.paused) {
    videoRef.value.play().then(() => {
      isRunning.value = true
    }).catch(e => console.error(e))
  } else {
    videoRef.value.pause()
    isRunning.value = false
  }
}

function onTimeUpdate() {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
    emit('time-update', currentTime.value)
  }
}

function onSeek() {
  if (videoRef.value) {
    videoRef.value.currentTime = Number(currentTime.value)
    emit('time-update', Number(currentTime.value))
  }
}
function seekTo(sec) {
  if (videoRef.value) {
    videoRef.value.currentTime = sec
    currentTime.value = sec
    emit('time-update', sec)
    if (videoRef.value.paused) {
      videoRef.value.play()
      isRunning.value = true
    }
  }
}

function resetToBeginning() {
  seekTo(0)
}

// 载入 HPC 生成的 752 帧元数据 (全局单例, 与告警流水共用同一份数据)
async function loadHpcMetadata() {
  const loaded = await loadMetadata()
  if (loaded.length) {
    console.log(`[Intelli-Shield] 成功载入 ${loaded.length} 帧 HPC 算法元数据`)
  }
}

onMounted(() => {
  loadHpcMetadata()
  window.addEventListener('resize', updateDisplayMetrics)
  if (videoRef.value) {
    videoRef.value.currentTime = 0.0
    currentTime.value = 0.0
    emit('time-update', 0.0)
    setTimeout(updateDisplayMetrics, 200)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', updateDisplayMetrics)
})

// 供父组件定位到指定告警时刻
defineExpose({ seekTo })
</script>

<style scoped>
.video-analysis-viewport {
  background: var(--bg-canvas);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  height: 100%;
  width: 100%;
}

.panel-toolbar {
  height: 38px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-machined);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  font-size: 12px;
  flex-shrink: 0;
  user-select: none;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.toolbar-title {
  color: var(--text-main);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.5px;
}

/* 主运行/暂停按钮 */
.run-control-btn {
  background: var(--telemetry-cyan);
  color: #000;
  border: 1px solid var(--telemetry-cyan);
  padding: 5px 14px;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s ease;
  box-shadow: 0 0 10px rgba(0, 210, 255, 0.3);
}

.run-control-btn:hover {
  background: #38bdf8;
  box-shadow: 0 0 14px rgba(0, 210, 255, 0.5);
}

.run-control-btn.is-running {
  background: var(--safety-amber);
  border-color: var(--safety-amber);
  color: #000;
  box-shadow: 0 0 10px rgba(255, 159, 10, 0.4);
}

.btn-icon {
  flex-shrink: 0;
}

.tool-btn-icon {
  flex-shrink: 0;
}

.run-control-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tool-btn {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  padding: 5px 10px;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}

.tool-btn:hover {
  color: var(--text-main);
  border-color: var(--border-bright);
}

.tool-btn.active {
  background: var(--telemetry-cyan-dim);
  border-color: var(--telemetry-cyan);
  color: var(--telemetry-cyan);
}

/* 主视频舞台 */
.main-video-stage {
  flex: 1 1 auto;
  min-height: 0;
  position: relative;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 0;
}

.video-player-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-cctv-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

/* 顶部监控信息条 */
.camera-hud-top {
  position: absolute;
  top: 12px;
  left: 14px;
  right: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  pointer-events: none;
  z-index: 10;
}

.cam-info-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(17, 21, 28, 0.9);
  border: 1px solid var(--border-machined);
  padding: 4px 10px;
  font-size: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.timeline-timecode-badge {
  display: flex;
  align-items: center;
  background: rgba(17, 21, 28, 0.9);
  border: 1px solid var(--border-machined);
  padding: 3px 8px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.live-dot {
  width: 7px;
  height: 7px;
  background: #64748b;
  border-radius: 50%;
}

.live-dot.running {
  background: var(--emergency-red);
  box-shadow: 0 0 8px var(--emergency-red);
  animation: recBlink 1s infinite;
}

@keyframes recBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.cam-name {
  color: #fff;
  font-weight: 600;
}

.cam-timecode {
  color: var(--telemetry-cyan);
  font-family: var(--font-mono);
  font-size: 11px;
}

/* 顶部认知探针胶囊 */
.omnijev-capsule {
  background: rgba(17, 21, 28, 0.9);
  border: 1px solid var(--border-machined);
  padding: 4px 12px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  pointer-events: auto;
  backdrop-filter: blur(4px);
}

.capsule-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.capsule-label {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

.capsule-value {
  font-size: 12px;
  font-weight: 700;
  color: #f1f5f9;
  font-family: var(--font-mono);
}

.highlight-cyan {
  color: var(--telemetry-cyan);
}

.val-danger, .threat-level-3 {
  color: #EF4444;
  text-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
}

.val-warning, .threat-level-2 {
  color: #F59E0B;
}

.val-caution, .threat-level-1 {
  color: #38BDF8;
}

.val-safe, .threat-level-0 {
  color: #10B981;
}
/* 底部进度拖动条与节点切换 */
.video-control-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.96);
  border-top: 1px solid var(--border-machined);
  box-shadow: 0 -2px 10px rgba(15, 23, 42, 0.06);
  padding: 5px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 12;
  backdrop-filter: blur(8px);
}

.timeline-scrubber-wrap {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
}

.video-range-slider {
  flex: 1;
  min-width: 0;
  height: 6px;
  background: var(--border-machined);
  outline: none;
  accent-color: var(--telemetry-cyan);
  cursor: pointer;
  border-radius: 3px;
}

.keyframe-jump-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
}

.strip-label {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.seek-chip {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  padding: 3px 8px;
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.chip-icon {
  flex-shrink: 0;
}

.safe-icon {
  color: var(--nominal-green);
}

.warn-icon {
  color: var(--safety-amber);
}

.danger-icon {
  color: var(--emergency-red);
}

.seek-chip.chip-critical:hover .danger-icon {
  color: #000;
}
.seek-chip:hover {
  background: var(--bg-panel-subtle);
  border-color: var(--telemetry-cyan);
  color: var(--text-main);
}

.seek-chip.chip-critical {
  border-color: var(--emergency-red);
  color: var(--emergency-red);
  background: rgba(255, 59, 48, 0.1);
  font-weight: 700;
}

.seek-chip.chip-critical:hover {
  background: var(--emergency-red);
  color: #000;
}
</style>
