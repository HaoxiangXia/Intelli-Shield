<template>
  <div class="threat-timeline-panel">
    <div class="threat-body">
      <div class="ecg-chart-box">
        <svg class="ecg-svg" viewBox="0 0 600 82" preserveAspectRatio="none">
          <defs>
            <linearGradient id="threatAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#EF4444" stop-opacity="0.30" />
              <stop offset="35%" stop-color="#F59E0B" stop-opacity="0.20" />
              <stop offset="70%" stop-color="#38BDF8" stop-opacity="0.10" />
              <stop offset="100%" stop-color="#10B981" stop-opacity="0.03" />
            </linearGradient>
          </defs>

          <!-- 4 档危害烈度平滑拟合面积填充 -->
          <path
            :d="areaPath"
            fill="url(#threatAreaGrad)"
          />

          <!-- 4 档危害烈度平滑贝塞尔拟合曲线 -->
          <path
            :d="linePath"
            fill="none"
            :stroke="currentThreatScore >= 2.2 || activeHazard ? '#EF4444' : (currentThreatScore >= 1.5 ? '#F59E0B' : '#10B981')"
            stroke-width="2.2"
            stroke-linecap="round"
          />

          <!-- 4 档危害阈值标注层 (置于曲线之后绘制, 避免被曲线覆盖) -->
          <!-- 统一左对齐等距堆叠, 各自紧贴本档阈值线上方, 颜色对应判级 -->
          <!-- Level 3 紧迫危险阻断阈值 2.20 -->
          <line x1="0" y1="19.3" x2="600" y2="19.3" stroke="rgba(239, 68, 68, 0.45)" stroke-dasharray="3,3" stroke-width="1"/>
          <text x="5" y="10" fill="#EF4444" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700"
                stroke="#ffffff" stroke-width="2.4" paint-order="stroke">Threat = 2.20 [Level 3 紧迫危险 · 动力切断制动阈值]</text>

          <!-- Level 2 临界预警警戒线 1.50 -->
          <line x1="0" y1="31" x2="600" y2="31" stroke="rgba(245, 158, 11, 0.45)" stroke-dasharray="3,3" stroke-width="1"/>
          <text x="5" y="24" fill="#F59E0B" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700"
                stroke="#ffffff" stroke-width="2.4" paint-order="stroke">Threat = 1.50 [Level 2 临界预警警戒线]</text>

          <!-- Level 1 低度注意 0.50 -->
          <line x1="0" y1="47.7" x2="600" y2="47.7" stroke="rgba(56, 189, 248, 0.35)" stroke-dasharray="2,2" stroke-width="0.8"/>
          <text x="5" y="38" fill="#38BDF8" font-family="'JetBrains Mono', monospace" font-size="7.5"
                stroke="#ffffff" stroke-width="2.4" paint-order="stroke">Threat = 0.50 [Level 1 低度注意]</text>

          <!-- Level 0 安全基线 0.00 -->
          <line x1="0" y1="56" x2="600" y2="56" stroke="rgba(16, 185, 129, 0.25)" stroke-width="0.8"/>
          <text x="5" y="52" fill="#10B981" font-family="'JetBrains Mono', monospace" font-size="7.5"
                stroke="#ffffff" stroke-width="2.4" paint-order="stroke">Threat = 0.00 [Level 0 安全基线]</text>

          <!-- 动态播放指示针当前威胁跟踪点 -->
          <circle
            :cx="playheadX"
            :cy="currentThreatY"
            r="3.5"
            :fill="currentThreatColor"
            stroke="#ffffff"
            stroke-width="1.2"
          >
            <animate attributeName="r" values="3;5;3" dur="1.2s" repeatCount="indefinite" />
          </circle>
          <!-- ================= 后端动态生成的红光空间防线情况条 (Ribbon Segments) ================= -->
          <!-- 门控活动通道底槽 (与上方风险曲线共用 0~600 时间轴) -->
          <rect x="0" y="60" width="600" height="15" fill="#f1f5f9" stroke="#cbd5e1" rx="2" />

          <!-- 动态情况条切片 (由后端实时生成) -->
          <g v-for="seg in ribbonSegments" :key="seg.id">
            <rect
              :x="seg.x"
              y="61.5"
              :width="seg.width"
              height="12"
              :fill="seg.color_bg"
              :stroke="seg.color_stroke"
              :stroke-width="seg.is_hazard ? 1.2 : 1"
              rx="2"
            >
              <animate
                v-if="seg.is_hazard"
                attributeName="opacity"
                values="0.75;1;0.75"
                dur="1.2s"
                repeatCount="indefinite"
              />
            </rect>
            <text
              :x="seg.x + seg.width / 2"
              y="70.5"
              :fill="seg.color_text"
              :font-size="seg.width > 120 ? '7.5' : (seg.width > 40 ? '6.8' : '6.0')"
              font-family="'PingFang SC', sans-serif"
              :font-weight="seg.is_hazard ? '700' : '600'"
              text-anchor="middle"
            >
              {{ seg.width > 160 ? seg.label : (seg.width > 9 ? seg.short_label : (seg.is_hazard ? '🚨' : '')) }}
            </text>
          </g>
          <!-- 动态播放指示针 (随着视频播放同步移动) -->
          <line
            :x1="playheadX"
            :x2="playheadX"
            y1="0"
            y2="77"
            stroke="#0284c7"
            stroke-width="1.5"
            stroke-dasharray="2,2"
          />
          <circle :cx="playheadX" cy="67.5" r="3" fill="#0284c7" stroke="#ffffff" stroke-width="1"/>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCctvMetadata } from '../../composables/useCctvMetadata'

const props = defineProps({
  activeHazard: {
    type: Boolean,
    default: true
  },
  todayInterventions: {
    type: Number,
    default: 38
  },
  currentTime: {
    type: Number,
    default: 0
  }
})

const { frames: metadataFrames, metadata: cctvMetadata, load: loadCctvMetadata } = useCctvMetadata()
const backendAnalysis = ref(null)

const duration = computed(() => {
  return Number(backendAnalysis.value?.duration_sec ?? cctvMetadata.value?.duration_seconds ?? 30.08)
})

const playheadX = computed(() => {
  const dur = duration.value > 0 ? duration.value : 30.08
  const cur = Math.max(0, Math.min(dur, Number(props.currentTime) || 0))
  return (cur / dur) * 600
})

async function fetchLatestAnalysis() {
  try {
    const res = await fetch('/api/cctv/timeline-analysis?cctv_id=CCTV-04')
    if (res.ok) {
      backendAnalysis.value = await res.json()
    }
  } catch (err) {
    console.warn('[ThreatTimelineChart] 后端动态遥测拉取失败，启用客户端本地推演降级:', err)
  }
}

onMounted(async () => {
  await loadCctvMetadata()
  fetchLatestAnalysis()
})

// 情况条文案统一采用「处置阶段轴」措辞, 对应 PRD 4.4 两段式安全处置闭环:
// 常态通行 → 接近预警 → 强制制动 → 险情解除 → 联锁再触发 → 流程闭环
const fallbackSegments = [
  {
    id: 'seg-1',
    start_time: 0.0,
    end_time: 2.4,
    x: 0.0,
    width: 47.9,
    label: '常态通行 · 工人与车辆空间隔离，无需干预',
    short_label: '常态通行',
    color_bg: 'rgba(16, 185, 129, 0.14)',
    color_stroke: 'rgba(16, 185, 129, 0.35)',
    color_text: '#047857',
    is_hazard: false
  },
  {
    id: 'seg-2',
    start_time: 2.4,
    end_time: 3.6,
    x: 47.9,
    width: 23.9,
    label: '接近预警 · 声光提示，尚未触发联锁',
    short_label: '接近预警',
    color_bg: 'rgba(245, 158, 11, 0.22)',
    color_stroke: '#d97706',
    color_text: '#b45309',
    is_hazard: false
  },
  {
    id: 'seg-3',
    start_time: 3.6,
    end_time: 23.4,
    x: 71.8,
    width: 394.9,
    label: '强制制动 · 物理一票否决，切断画面内全车动力',
    short_label: '强制制动',
    color_bg: 'rgba(220, 38, 38, 0.22)',
    color_stroke: '#dc2626',
    color_text: '#991b1b',
    is_hazard: true
  },
  {
    id: 'seg-4',
    start_time: 23.4,
    end_time: 29.6,
    x: 466.8,
    width: 123.7,
    label: '险情解除 · 责任人确认后恢复车辆动力',
    short_label: '险情解除',
    color_bg: 'rgba(16, 185, 129, 0.14)',
    color_stroke: 'rgba(16, 185, 129, 0.35)',
    color_text: '#047857',
    is_hazard: false
  },
  {
    id: 'seg-6',
    start_time: 29.6,
    end_time: 30.08,
    x: 590.5,
    width: 9.5,
    label: '流程闭环 · 回归常态通行',
    short_label: '闭环',
    color_bg: 'rgba(16, 185, 129, 0.14)',
    color_stroke: 'rgba(16, 185, 129, 0.35)',
    color_text: '#047857',
    is_hazard: false
  }
]

function buildDynamicRibbon(frames, totalDur) {
  if (!frames || frames.length === 0) return fallbackSegments
  const dur = totalDur > 0 ? totalDur : 30.08
  const fps = Number(cctvMetadata.value?.fps || 10.0)
  const segments = []
  let currentSeg = null

  for (let i = 0; i < frames.length; i++) {
    const f = frames[i]
    const t = Number(f.timestamp ?? (i / fps))
    const level = f.alarm_level || 'NORMAL'
    const isInterlocked = f.interlock?.engaged || level === 'CRITICAL'

    let stateKey = 'NORMAL'
    let label = '常态通行 · 工人与车辆安全隔离'
    let shortLabel = '常态'
    let colorBg = 'rgba(16, 185, 129, 0.14)'
    let colorStroke = 'rgba(16, 185, 129, 0.35)'
    let colorText = '#047857'
    let isHazard = false

    if (isInterlocked) {
      stateKey = 'CRITICAL'
      label = '强制制动 · 物理一票否决，切断画面内全车动力'
      shortLabel = '强制制动'
      colorBg = 'rgba(220, 38, 38, 0.25)'
      colorStroke = '#dc2626'
      colorText = '#991b1b'
      isHazard = true
    } else if (level === 'WARNING') {
      stateKey = 'WARNING'
      label = '接近预警 · 声光提示，尚未触发联锁'
      shortLabel = '接近预警'
      colorBg = 'rgba(245, 158, 11, 0.22)'
      colorStroke = '#d97706'
      colorText = '#b45309'
      isHazard = false
    }

    if (!currentSeg || currentSeg.stateKey !== stateKey) {
      if (currentSeg) {
        currentSeg.end_time = t
        currentSeg.width = Math.max(2, ((currentSeg.end_time - currentSeg.start_time) / dur) * 600)
        segments.push(currentSeg)
      }
      currentSeg = {
        id: `dyn-seg-${segments.length + 1}`,
        stateKey,
        start_time: t,
        end_time: t,
        x: (t / dur) * 600,
        width: 0,
        label,
        short_label: shortLabel,
        color_bg: colorBg,
        color_stroke: colorStroke,
        color_text: colorText,
        is_hazard: isHazard
      }
    } else {
      currentSeg.end_time = t
    }
  }
  if (currentSeg) {
    currentSeg.end_time = dur
    currentSeg.width = Math.max(2, ((currentSeg.end_time - currentSeg.start_time) / dur) * 600)
    segments.push(currentSeg)
  }
  return segments.length > 0 ? segments : fallbackSegments
}

const ribbonSegments = computed(() => {
  if (backendAnalysis.value?.ribbon_segments?.length) {
    return backendAnalysis.value.ribbon_segments
  }
  const frames = metadataFrames.value
  if (frames && frames.length > 0) {
    return buildDynamicRibbon(frames, duration.value)
  }
  return fallbackSegments
})

// 0.0 ~ 3.0 危害烈度映射到 SVG Y 轴: Y = 56 - (Score / 3.0) * 50
const threatPoints = computed(() => {
  const frames = metadataFrames.value
  const dur = duration.value > 0 ? duration.value : 30.08
  if (!frames || frames.length === 0) {
    const fallback = [
      { t: 0.0, s: 0.45 },
      { t: 1.5, s: 0.45 },
      { t: 2.3, s: 0.55 },
      { t: 2.8, s: 1.25 },
      { t: 3.4, s: 1.85 },
      { t: 3.8, s: 2.35 },
      { t: 4.8, s: 2.48 },
      { t: 10.0, s: 2.48 },
      { t: 16.0, s: 2.48 },
      { t: 22.0, s: 2.48 },
      { t: 23.2, s: 2.35 },
      { t: 23.8, s: 1.45 },
      { t: 24.5, s: 0.75 },
      { t: 26.0, s: 0.45 },
      { t: 28.5, s: 0.45 },
      { t: 29.3, s: 0.45 },
      { t: 29.8, s: 0.45 },
      { t: 30.08, s: 0.45 }
    ]
    return fallback.map(p => ({
      x: (p.t / dur) * 600,
      y: 56 - (p.s / 3.0) * 50,
      threat: p.s
    }))
  }

  // 从全量帧采样约 38 个控制点，保持微观走势并平滑高频噪声
  const step = Math.max(1, Math.floor(frames.length / 38))
  const sampled = []
  for (let i = 0; i < frames.length; i += step) {
    const f = frames[i]
    const t = Number(f.timestamp ?? (i * 0.1))
    const s = Number(f.probes?.threat_score ?? (f.alarm_level === 'CRITICAL' ? 2.48 : 0.45))
    sampled.push({
      x: Math.min(600, (t / dur) * 600),
      y: Math.max(6, Math.min(56, 56 - (s / 3.0) * 50)),
      threat: s
    })
  }
  if (sampled.length > 0) {
    sampled[0].x = 0
    const lastF = frames[frames.length - 1]
    const lastS = Number(lastF.probes?.threat_score ?? 0.45)
    sampled.push({
      x: 600,
      y: 56 - (lastS / 3.0) * 50,
      threat: lastS
    })
  }
  return sampled
})

// Catmull-Rom 拟合三次贝塞尔平滑样条曲线
function generateSmoothCurve(pts) {
  if (!pts || pts.length === 0) return ''
  if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`

  let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i === 0 ? 0 : i - 1]
    const p1 = pts[i]
    const p2 = pts[i + 1]
    const p3 = pts[i + 2] || p2

    const tension = 0.25
    const cp1x = p1.x + (p2.x - p0.x) * tension
    const cp1y = p1.y + (p2.y - p0.y) * tension
    const cp2x = p2.x - (p3.x - p1.x) * tension
    const cp2y = p2.y - (p3.y - p1.y) * tension

    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`
  }
  return d
}

const linePath = computed(() => {
  if (backendAnalysis.value?.line_path) {
    return backendAnalysis.value.line_path
  }
  return generateSmoothCurve(threatPoints.value)
})

const areaPath = computed(() => {
  if (backendAnalysis.value?.area_path) {
    return backendAnalysis.value.area_path
  }
  if (!linePath.value) return ''
  return `${linePath.value} L 600 58 L 0 58 Z`
})

// 当前播放时间点上的威胁烈度与高度
const currentThreatScore = computed(() => {
  const dur = duration.value > 0 ? duration.value : 30.08
  const cur = Math.max(0, Math.min(dur, Number(props.currentTime) || 0))
  const frames = metadataFrames.value
  const fps = Number(cctvMetadata.value?.fps || 10.0)
  if (frames && frames.length) {
    const targetId = Math.max(1, Math.min(frames.length, Math.round(cur * fps) + 1))
    const f = frames[targetId - 1]
    if (f) return Number(f.probes?.threat_score ?? 0.45)
  }
  return 0.45
})
const currentThreatY = computed(() => {
  return Math.max(6, Math.min(56, 56 - (currentThreatScore.value / 3.0) * 50))
})

const currentThreatColor = computed(() => {
  const s = currentThreatScore.value
  if (s >= 2.2) return '#EF4444'
  if (s >= 1.5) return '#F59E0B'
  if (s >= 0.5) return '#38BDF8'
  return '#10B981'
})
</script>

<style scoped>
.threat-timeline-panel {
  height: 100%;
  background: var(--bg-panel);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  user-select: none;
}

.threat-body {
  height: 100%;
  padding: 8px 14px;
  box-sizing: border-box;
  display: flex;
}

.ecg-chart-box {
  flex: 1;
  min-width: 0;
  height: 100%;
  position: relative;
}

.ecg-svg {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
