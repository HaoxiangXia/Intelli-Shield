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
          <span class="btn-icon">{{ isRunning ? '⏸' : '▶' }}</span>
          <span>{{ isRunning ? '暂停推演演示' : '开始运行演示' }}</span>
        </button>

        <!-- 动态 AI 标注层显隐切换按钮 -->
        <button
          class="tool-btn"
          :class="{ active: showAiOverlay }"
          @click="showAiOverlay = !showAiOverlay"
        >
          <span>🎯 {{ showAiOverlay ? '隐藏 AI 实时标注层' : '显示 AI 实时标注层' }}</span>
        </button>

        <!-- 重置按钮 -->
        <button class="tool-btn" @click="resetToBeginning">
          <span>⟲ 重置片头</span>
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

          <!-- 1. 动态绘制当前帧检出的所有 YOLO 目标框 -->
          <g v-for="(box, bIdx) in scaledDetections" :key="bIdx">
            <!-- 框体 -->
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
            <!-- 标签背底 -->
            <rect
              :x="box.x"
              :y="Math.max(0, box.y - 20)"
              :width="box.tagW"
              height="20"
              :fill="box.color"
              rx="2"
            />
            <!-- 标签文字 -->
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

          <!-- 2. 人车间距动态测距射线 (当存在间距时) -->
          <g v-if="scaledDistanceRay">
            <line
              :x1="scaledDistanceRay.x1"
              :y1="scaledDistanceRay.y1"
              :x2="scaledDistanceRay.x2"
              :y2="scaledDistanceRay.y2"
              :stroke="isCriticalAlarm ? '#ff3b30' : '#ff9f0a'"
              stroke-width="2.5"
              stroke-dasharray="6,3"
            >
              <animate attributeName="stroke-dashoffset" values="0;18" dur="0.8s" repeatCount="indefinite" />
            </line>
            <!-- 射线中心距离标牌 -->
            <g :transform="`translate(${scaledDistanceRay.midX}, ${scaledDistanceRay.midY})`">
              <rect
                x="-55"
                y="-11"
                width="110"
                height="22"
                fill="#ffffff"
                :stroke="isCriticalAlarm ? '#dc2626' : '#d97706'"
                stroke-width="1.5"
                rx="2"
              />
              <text
                x="0"
                y="4"
                text-anchor="middle"
                :fill="isCriticalAlarm ? '#ff3b30' : '#ff9f0a'"
                font-size="10"
                font-weight="700"
                font-family="'JetBrains Mono', monospace"
              >
                {{ currentFrameData.min_dist_px }} 像素
              </text>
            </g>
          </g>
        </svg>

        <!-- 顶部监控画面信息水印 -->
        <div class="camera-hud-top">
          <div class="cam-info-pill">
            <span class="live-dot" :class="{ running: isRunning }"></span>
            <span class="cam-name">CCTV-04 仓库主干道 (中转区南段)</span>
            <span class="cam-timecode">{{ formattedTimecode }}</span>
          </div>
          <div class="stream-stat-pills">
            <span class="stat-pill">视频帧率: 25.0 帧/秒</span>
            <span class="stat-pill latency-pill">
              HPC 推理延迟: {{ currentProbes.latency_ms || 107.4 }} 毫秒
            </span>
            <span class="stat-pill status-pill" :class="alarmStatusClass">
              {{ alarmStatusText }}
            </span>
            <span
              class="stat-pill gate-status-badge"
              :class="currentFrameData?.gating?.status === 'OPEN' ? 'gate-active-pulse' : 'gate-standby-pill'"
            >
              {{ currentFrameData?.gating?.status === 'OPEN' ? '⚡ 门控: 激活唤醒 OneJev' : '🛡️ 门控: 阻断休眠 (GPU待机)' }}
            </span>
          </div>
        </div>

        <!-- 左下角浮动认知探针胶囊 (纯中文，由 JSON 数据实时驱动) -->
        <div class="omnijev-capsule">
          <div class="capsule-col">
            <span class="capsule-label">双系统认知直觉推演</span>
            <span class="capsule-value highlight-cyan">OneJev-0.8B (RTX 3090)</span>
          </div>
          <div class="capsule-col">
            <span class="capsule-label">前向推理延迟</span>
            <span class="capsule-value">{{ currentProbes.latency_ms || 107.4 }} 毫秒</span>
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
            <span class="capsule-label">综合危害烈度</span>
            <span
              class="capsule-value"
              :class="isCriticalAlarm ? 'val-danger' : (isWarningAlarm ? 'val-warning' : 'val-safe')"
            >
              {{ currentProbes.threat_score || 0.45 }} / 3.0 ({{ threatLevelText }})
            </span>
          </div>
        </div>

        <!-- 底部视频控制栏与关键时序跳转 -->
        <div class="video-control-bar">
          <div class="timeline-scrubber-wrap">
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
              01秒 正常安全 (帧 #0025)
            </button>
            <button class="seek-chip" @click="seekTo(8.0)">
              08秒 预警缓冲 (帧 #0200)
            </button>
            <button class="seek-chip" @click="seekTo(13.0)">
              13秒 接近警示 (帧 #0325)
            </button>
            <button class="seek-chip chip-critical" @click="seekTo(23.0)">
              🚨 23秒 临界碰撞 (帧 #0575)
            </button>
            <button class="seek-chip" @click="seekTo(28.0)">
              28秒 复位安全 (帧 #0700)
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

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
const currentTime = ref(0)
const duration = ref(30.08)

// JSON 帧数据集 (从 HPC 生成的 752 帧元数据载入)
const metadataFrames = ref([])
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
const currentFrameData = computed(() => {
  if (!metadataFrames.value || metadataFrames.value.length === 0) return null
  const targetTime = currentTime.value
  const targetFrameId = Math.max(1, Math.min(752, Math.round(targetTime * 25.0)))
  
  // 快速通过索引查取 (frame_id 对应数组下标 frame_id - 1)
  const item = metadataFrames.value[targetFrameId - 1]
  if (item && item.frame_id === targetFrameId) return item
  
  // 备用：按时间戳就近搜索
  return metadataFrames.value.find(f => Math.abs(f.timestamp - targetTime) <= 0.05) || metadataFrames.value[0]
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

const alarmStatusClass = computed(() => {
  if (isCriticalAlarm.value) return 'danger'
  if (isWarningAlarm.value) return 'warning'
  return 'safe'
})

const alarmStatusText = computed(() => {
  if (isCriticalAlarm.value) return '● 触发碰撞阻断 (紧急)'
  if (isWarningAlarm.value) return '▲ 接近预警缓冲 (注意)'
  return '✔ 处于安全通行区 (正常)'
})

const threatLevelText = computed(() => {
  const t = currentProbes.value.threat_score || 0.45
  if (t >= 2.0) return '三级临界'
  if (t >= 1.0) return '二级警示'
  return '安全基线'
})

const formattedTimecode = computed(() => {
  const t = currentTime.value
  const mins = Math.floor(t / 60)
  const secs = Math.floor(t % 60)
  const ms = Math.floor((t % 1) * 100)
  const pad = (n, l = 2) => String(n).padStart(l, '0')
  const fid = currentFrameData.value?.frame_id || Math.floor(t * 25)
  return `${pad(mins)}:${pad(secs)}.${pad(ms)} (帧 #${fid})`
})

// 将 1920x1080 坐标动态换算为页面显示的实际位置
const scaledDetections = computed(() => {
  if (!currentFrameData.value || !currentFrameData.value.detections) return []
  const { width: dW, height: dH, left: dL, top: dT } = displayMetrics.value
  const scaleX = dW / videoNativeW.value
  const scaleY = dH / videoNativeH.value

  return currentFrameData.value.detections.map(det => {
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

// 绘制人车测距射线 (严格仅在 person 与 forkTruck 之间计算最近交互对)
const scaledDistanceRay = computed(() => {
  if (!currentFrameData.value || !currentFrameData.value.min_dist_px) return null
  const dets = scaledDetections.value
  const persons = dets.filter(d => d.label.startsWith('person'))
  const forkTrucks = dets.filter(d => d.label.startsWith('forkTruck'))
  if (persons.length === 0 || forkTrucks.length === 0) return null

  let bestP = null
  let bestF = null
  let minD = Infinity

  for (const p of persons) {
    const pcX = p.x + p.w / 2
    const pcY = p.y + p.h / 2
    for (const f of forkTrucks) {
      const fcX = f.x + f.w / 2
      const fcY = f.y + f.h / 2
      const d = Math.hypot(pcX - fcX, pcY - fcY)
      if (d < minD) {
        minD = d
        bestP = { x: pcX, y: pcY }
        bestF = { x: fcX, y: fcY }
      }
    }
  }

  if (!bestP || !bestF) return null

  return {
    x1: bestP.x,
    y1: bestP.y,
    x2: bestF.x,
    y2: bestF.y,
    midX: (bestP.x + bestF.x) / 2,
    midY: (bestP.y + bestF.y) / 2
  }
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

// 载入 HPC 生成的 752 帧元数据
async function loadHpcMetadata() {
  try {
    const res = await fetch('/samples/cctv/benchmarks/cctv_frames_metadata.json')
    if (res.ok) {
      const data = await res.json()
      metadataFrames.value = data.frames || []
      console.log(`[Intelli-Shield] 成功载入 ${metadataFrames.value.length} 帧 HPC 算法元数据`)
    }
  } catch (err) {
    console.error('[Intelli-Shield] 载入算法元数据失败:', err)
  }
}

onMounted(() => {
  loadHpcMetadata()
  window.addEventListener('resize', updateDisplayMetrics)
  if (videoRef.value) {
    videoRef.value.currentTime = 23.0
    currentTime.value = 23.0
    setTimeout(updateDisplayMetrics, 200)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', updateDisplayMetrics)
})
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
  height: 42px;
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

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
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
  font-size: 12px;
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
  flex: 1;
  position: relative;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
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
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
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

.stream-stat-pills {
  display: flex;
  gap: 8px;
}

.stat-pill {
  background: rgba(17, 21, 28, 0.9);
  border: 1px solid var(--border-machined);
  padding: 4px 8px;
  font-size: 11px;
  color: var(--text-secondary);
  backdrop-filter: blur(4px);
}

.latency-pill {
  color: var(--telemetry-cyan);
  font-family: var(--font-mono);
}

.status-pill {
  color: var(--nominal-green);
  border-color: rgba(48, 209, 88, 0.3);
}

.status-pill.warning {
  color: var(--safety-amber);
  border-color: var(--safety-amber);
  background: rgba(255, 159, 10, 0.15);
  font-weight: 700;
}

.status-pill.danger {
  color: var(--emergency-red);
  border-color: var(--emergency-red);
  background: rgba(255, 59, 48, 0.2);
  font-weight: 700;
}

.gate-status-badge {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.gate-standby-pill {
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.4);
  background: rgba(15, 23, 42, 0.7);
}

.gate-active-pulse {
  color: #fff;
  border-color: #ff3b30;
  background: rgba(255, 59, 48, 0.35);
  box-shadow: 0 0 12px rgba(255, 59, 48, 0.6);
  animation: gatePulse 1.2s infinite;
}

@keyframes gatePulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.85; transform: scale(1.02); }
}

/* 左下角认知探针胶囊 */
.omnijev-capsule {
  position: absolute;
  bottom: 58px;
  left: 14px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border-bright);
  border-left: 3px solid var(--telemetry-cyan);
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
  z-index: 10;
  backdrop-filter: blur(8px);
}

.capsule-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.capsule-label {
  font-size: 10px;
  color: var(--text-muted);
}

.capsule-value {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
  font-family: var(--font-mono);
}

.highlight-cyan {
  color: var(--telemetry-cyan);
}

.val-danger {
  color: var(--emergency-red);
}

.val-warning {
  color: var(--safety-amber);
}

.val-safe {
  color: var(--nominal-green);
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
  padding: 6px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  z-index: 12;
  backdrop-filter: blur(8px);
}

.timeline-scrubber-wrap {
  width: 100%;
  display: flex;
  align-items: center;
}

.video-range-slider {
  width: 100%;
  height: 4px;
  background: var(--border-machined);
  outline: none;
  accent-color: var(--telemetry-cyan);
  cursor: pointer;
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
