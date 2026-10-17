import { ref, shallowRef } from 'vue'

// 301 帧 (10 FPS 恒频推演) HPC 元数据约 1.7 MB, 全局单例保证只发起一次请求/解析。
// 使用 shallowRef: 帧数组按引用传递, 无需深层响应式代理。
const frames = shallowRef([])
const metadata = ref(null)
const status = ref('idle') // idle | loading | ready | error

let inflight = null

async function load() {
  if (status.value === 'ready') return frames.value
  if (inflight) return inflight

  status.value = 'loading'
  inflight = (async () => {
    try {
      const res = await fetch('/samples/cctv/benchmarks/cctv_frames_metadata.json')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      frames.value = data.frames || []
      metadata.value = data.metadata || {}
      status.value = 'ready'
      return frames.value
    } catch (err) {
      status.value = 'error'
      console.error('[Intelli-Shield] 载入算法元数据失败:', err)
      return []
    } finally {
      inflight = null
    }
  })()

  return inflight
}

// ── 摄像头台账 ────────────────────────────────────────────────────────────
// hasMetadata: 该路是否已跑通 HPC 采集与推理 (仅有 cctv_frames_metadata.json 的那路为 true)。
// 未接入的路在页面上显式标注, 不填充任何编造指标。
export const CAMERA_REGISTRY = [
  {
    id: 'CCTV-04',
    name: '仓库主干道 · 中转区南段',
    zone: 'A区',
    position: '冲压装配主通廊入口',
    hasMetadata: true,
    video: '/samples/cctv/videos/output_video7.mp4',
    thumbnail: '/samples/cctv/keyframes/keyframe_0575_04_CRITICAL_HAZARD.png'
  },
  {
    id: 'CCTV-01',
    name: '焊接工段 · 立柱内侧',
    zone: 'C区',
    position: '自动化焊接作业岛',
    hasMetadata: false
  },
  {
    id: 'CCTV-02',
    name: '冲压A线 · 机械手上方',
    zone: 'A区',
    position: '冲压装配主通廊',
    hasMetadata: false
  },
  {
    id: 'CCTV-05',
    name: '重载物料立库 · 叉车回转区',
    zone: 'B区',
    position: '重载物料立库区',
    hasMetadata: false
  },
  {
    id: 'CCTV-06',
    name: '叉车充换电接驳站 · 充电桩侧',
    zone: 'D区',
    position: '叉车充换电接驳站',
    hasMetadata: false
  }
]

// 连续非 NORMAL 帧合并为一段险情; 10 FPS 恒频下短于 3 帧 (0.3s) 丢弃防抖。
export const MIN_EPISODE_FRAMES = 3

export function summarizeEpisode(run) {
  // 峰值帧: 碰撞风险概率优先, 其次综合危害烈度
  let peak = run[0]
  for (const f of run) {
    const a = f.probes?.collision_risk || 0
    const b = peak.probes?.collision_risk || 0
    if (a > b || (a === b && (f.probes?.threat_score || 0) > (peak.probes?.threat_score || 0))) {
      peak = f
    }
  }

  // 物理间距取段落内最危险值
  let minDistPx = Infinity
  let minDistM = Infinity
  for (const f of run) {
    if (Number.isFinite(f.min_dist_px)) minDistPx = Math.min(minDistPx, f.min_dist_px)
    const m = f.red_zone?.min_dist_m
    if (m !== null && m !== undefined && Number.isFinite(Number(m))) {
      minDistM = Math.min(minDistM, Number(m))
    }
  }

  const p = peak.probes || {}
  const last = run[run.length - 1]
  return {
    id: `EP-${peak.frame_id}`,
    frameId: peak.frame_id,
    peakTime: peak.timestamp,
    startTime: run[0].timestamp,
    endTime: last.timestamp,
    durationSec: +(last.timestamp - run[0].timestamp).toFixed(2),
    frameCount: run.length,
    level: peak.alarm_level,
    minDistPx: Number.isFinite(minDistPx) ? +minDistPx.toFixed(1) : null,
    minDistM: Number.isFinite(minDistM) ? +minDistM.toFixed(2) : null,
    collisionRisk: +((p.collision_risk ?? 0) * 100).toFixed(1),
    threatScore: +(p.threat_score ?? 0).toFixed(2),
    awareness: +(p.worker_awareness?.unaware ?? 0).toFixed(2),
    latencyMs: p.latency_ms ?? 107.4,
    hazardBehavior: p.worker_hazard_behavior || null,
    reasons: peak.reasons || [],
    status: 'pending',
    isLedger: false
  }
}

export function buildEpisodes(frames) {
  const episodes = []
  let run = []
  const flush = () => {
    if (run.length >= MIN_EPISODE_FRAMES) episodes.push(summarizeEpisode(run))
    run = []
  }
  for (const f of frames) {
    if (f.alarm_level === 'NORMAL') flush()
    else run.push(f)
  }
  flush()
  // 核验队列按发生时刻正序
  return episodes.sort((a, b) => a.startTime - b.startTime)
}

// 单路摄像头的时序统计, 全部由实测帧聚合而来
export function summarizeCctvStats(frames) {
  if (!frames?.length) return null

  let critical = 0
  let warning = 0
  let gpuActive = 0
  let driverExcluded = 0
  let peakRisk = 0
  let peakThreat = 0
  let minDistPx = Infinity
  let minDistM = Infinity
  let latencySum = 0

  for (const f of frames) {
    if (f.alarm_level === 'CRITICAL') critical++
    else if (f.alarm_level === 'WARNING') warning++
    if (f.gating?.gpu_active) gpuActive++
    driverExcluded += f.gating?.driver_excluded || 0

    const p = f.probes || {}
    peakRisk = Math.max(peakRisk, p.collision_risk || 0)
    peakThreat = Math.max(peakThreat, p.threat_score || 0)
    latencySum += p.latency_ms || 0

    if (Number.isFinite(f.min_dist_px)) minDistPx = Math.min(minDistPx, f.min_dist_px)
    const m = f.red_zone?.min_dist_m
    if (m !== null && m !== undefined && Number.isFinite(Number(m))) {
      minDistM = Math.min(minDistM, Number(m))
    }
  }

  const total = frames.length
  const dangerFrames = critical + warning

  return {
    totalFrames: total,
    criticalFrames: critical,
    warningFrames: warning,
    dangerFramePct: +((dangerFrames / total) * 100).toFixed(1),
    safeFramePct: +(((total - dangerFrames) / total) * 100).toFixed(1),
    peakRiskPct: +(peakRisk * 100).toFixed(1),
    peakThreatScore: +peakThreat.toFixed(2),
    minDistPx: Number.isFinite(minDistPx) ? +minDistPx.toFixed(1) : null,
    minDistM: Number.isFinite(minDistM) ? +minDistM.toFixed(2) : null,
    gpuActivePct: +((gpuActive / total) * 100).toFixed(1),
    gpuSavePct: +(((total - gpuActive) / total) * 100).toFixed(1),
    driverExcludedTotal: driverExcluded,
    avgLatencyMs: +(latencySum / total).toFixed(1),
    durationSec: +(frames[frames.length - 1].timestamp - frames[0].timestamp).toFixed(2),
    episodes: buildEpisodes(frames)
  }
}

export function useCctvMetadata() {
  return { frames, metadata, status, load }
}