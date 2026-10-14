<template>
  <aside class="triage-dock">
    <div class="triage-header">
      <span class="triage-title">险情核验处置坞</span>
    </div>

    <!-- 待复核告警卡片 (PRD 4.4 规范) -->
    <div
      class="active-hazard-card"
      :class="{ 'resolved-card': !isCardPending }"
    >
      <div class="hazard-title-row">
        <div class="hazard-badge">
          <span class="rec-dot" v-if="isCardPending"></span>
          <span :style="{ color: isCardPending ? 'var(--emergency-red)' : 'var(--nominal-green)' }" class="hazard-text">
            <template v-if="isCardPending">
              <AlertOctagon :size="13" class="badge-icon-hazard" />
              <span>待复核{{ cardIncident?.level === 'CRITICAL' ? '临界' : '接近' }}险情 (帧 #{{ cardIncident?.frameId }})</span>
            </template>
            <template v-else-if="cardIncident">
              <CheckCircle2 :size="13" class="badge-icon-resolved" />
              <span>警报已核验{{ cardIncident.status === 'confirmed' ? '属实' : '排除' }} ({{ cardIncident.id }})</span>
            </template>
            <template v-else>
              <CheckCircle2 :size="13" class="badge-icon-resolved" />
              <span>暂无待复核险情</span>
            </template>
          </span>
        </div>
        <span class="hazard-time">
          <template v-if="cardIncident">
            {{ cardIncident.startTime.toFixed(2) }}秒 · 持续 {{ cardIncident.durationSec.toFixed(2) }}秒
          </template>
          <template v-else>等待告警流入</template>
        </span>
      </div>

      <!-- 三路认知探针遥测仪 -->
      <div class="probe-triad-box">
        <div class="probe-triad-title">
          <span>OmniJev 三路认知探针遥测</span>
          <span style="color:var(--text-muted)">RTX 3090 集群 · {{ cardIncident?.latencyMs ?? 107.4 }}毫秒</span>
        </div>
        <div class="probe-triad-grid">
          <div class="probe-metric-item">
            <span class="p-label">1. 碰撞风险概率</span>
            <span
              class="p-val"
              :style="{ color: isCardPending ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
            >
              {{ cardIncident ? `${cardIncident.collisionRisk}%` : '--' }}
            </span>
            <div class="p-bar-wrap">
              <div
                class="p-bar-fill"
                :style="{ width: `${cardIncident?.collisionRisk ?? 0}%`, background: isCardPending ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
              ></div>
            </div>
          </div>

          <div class="probe-metric-item">
            <span class="p-label">2. 工人注意力状态</span>
            <span
              class="p-val"
              :style="{ color: isCardPending ? 'var(--safety-amber)' : 'var(--nominal-green)', fontSize: '11px' }"
            >
              <template v-if="cardIncident">{{ (cardIncident.awareness * 100).toFixed(0) }}% 分心背对</template>
              <template v-else>--</template>
            </span>
            <div class="p-bar-wrap">
              <div
                class="p-bar-fill"
                :style="{ width: `${(cardIncident?.awareness ?? 0) * 100}%`, background: isCardPending ? 'var(--safety-amber)' : 'var(--nominal-green)' }"
              ></div>
            </div>
          </div>

          <div class="probe-metric-item">
            <span class="p-label">3. 综合危害烈度</span>
            <span
              class="p-val"
              :style="{ color: isCardPending ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
            >
              <template v-if="cardIncident">{{ cardIncident.threatScore }} / 3.0</template>
              <template v-else>--</template>
            </span>
            <div class="p-bar-wrap">
              <div
                class="p-bar-fill"
                :style="{ width: `${((cardIncident?.threatScore ?? 0) / 3) * 100}%`, background: isCardPending ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 真实高清关键帧抓拍切片 -->
      <div v-if="cardIncident" class="hd-snapshot-container" @click="showHdModal = true" title="点击放大查看 1080P 高清逐帧原图">
        <span class="hd-badge-overlay">
          CCTV-04 抓拍 #{{ cardIncident.keyframe.id }} ({{ cardIncident.keyframe.label }})
          · 物理间距 {{ cardIncident.minDistPx }}px / {{ cardIncident.minDistM }}m
        </span>
        <span class="hd-action-tip">
          <Maximize2 :size="11" class="tip-icon" />
          <span>点击放大展开 1080P 逐帧研判</span>
        </span>

        <img
          :src="`/samples/cctv/keyframes/${cardIncident.keyframe.file}`"
          alt="CCTV 关键帧抓拍"
          class="snapshot-real-img"
        />
      </div>

      <div class="hazard-caption">
        <strong>{{ isCardPending ? '双系统分层仲裁依据:' : '核验结论 (责任人):' }}</strong>
        <template v-if="isCardPending && cardIncident">
          物理间距最近 {{ cardIncident.minDistPx }}px ({{ cardIncident.minDistM }}m)，
          {{ cardIncident.reasons?.length ? cardIncident.reasons.join('；') : '多帧连续越阈' }}。
        </template>
        <template v-else-if="cardIncident">
          经安全责任人现场复核，判定为【{{ cardIncident.status === 'confirmed' ? '险情属实' : resolvedReason }}】，
          样本已提交算法微调队列。
        </template>
        <template v-else>当前无待复核险情，实时流持续监听中。</template>
      </div>

      <!-- 责任人一键核验按钮区域 (PRD 4.4 规范) -->
      <div class="verification-actions">
        <template v-if="isCardPending">
          <div class="action-btn-row">
            <button
              class="action-confirm-hazard"
              @click="handleConfirmHazard"
              title="确认确实存在危险，触发对讲并归入台账，沉淀为正样本"
            >
              <AlertTriangle :size="14" class="btn-icon" />
              <span>确认属实 - 紧迫隐患</span>
            </button>
            <button
              class="action-exclude-false"
              @click="showFalseModal = true"
              title="属于专人指挥或特种作业，排除警报，沉淀为难负例"
            >
              <ShieldCheck :size="14" class="btn-icon" />
              <span>判定误报 - 排除警报</span>
            </button>
          </div>
        </template>
        <template v-else>
          <div class="resolved-banner">
            <div class="resolved-banner-left">
              <CheckCircle2 :size="14" class="resolved-icon" />
              <span>本轮核验已闭环</span>
            </div>
            <span style="font-weight:700;">已核验 {{ reviewedCount }} / {{ visibleIncidents.length }} 段</span>
          </div>
        </template>
      </div>

      <!-- 算法数据飞轮状态指示条 (PRD 4.4 规范) -->
      <div class="data-flywheel-ribbon">
        <div>
          <span class="flywheel-tag">数据飞轮</span>
          <span style="margin-left: 6px;">反哺目标检测与认知微调模型池</span>
        </div>
        <span
          class="flywheel-status"
          :style="{ color: flywheelColor }"
        >
          {{ flywheelText }}
        </span>
      </div>
    </div>

    <!-- 告警事件流水清单 -->
    <div class="stream-panel">
      <div class="stream-toolbar">
        <button
          class="stream-tab"
          :class="{ active: currentTab === 'all' }"
          @click="currentTab = 'all'"
        >
          全部 ({{ visibleIncidents.length }})
        </button>
        <button
          class="stream-tab"
          :class="{ active: currentTab === 'pending' }"
          @click="currentTab = 'pending'"
        >
          待复核 ({{ pendingCount }})
        </button>
        <button
          class="stream-tab"
          :class="{ active: currentTab === 'ledger' }"
          @click="currentTab = 'ledger'"
        >
          隐患台账 ({{ ledgerCount }})
        </button>
      </div>

      <div class="incident-table-wrap">
        <div
          v-for="item in filteredIncidents"
          :key="item.id"
          class="incident-row"
          :class="{ active: rowView(item).isActive }"
          @click="locateIncident(item)"
          title="点击定位到该告警时刻"
        >
          <span class="row-time">{{ rowView(item).time }}</span>
          <span class="row-device">{{ rowView(item).device }}</span>
          <span class="tag-pill" :class="rowView(item).tagClass">{{ rowView(item).tagText }}</span>
          <span class="row-meta">{{ rowView(item).meta }}</span>
        </div>
        <div v-if="filteredIncidents.length === 0" class="incident-empty">
          <template v-if="visibleIncidents.length === 0">暂无告警记录 · 播放推进后自动累积</template>
          <template v-else>该分类下暂无记录</template>
        </div>
      </div>
    </div>

    <!-- 误报排除原因选择弹窗 -->
    <div class="modal-backdrop" :class="{ open: showFalseModal }">
      <div class="modal-dialog">
        <div class="modal-header">
          <div class="modal-title-with-icon">
            <ShieldAlert :size="15" class="modal-icon" />
            <span>责任人判定误报 · 选择排除核验依据</span>
          </div>
          <button class="close-btn" @click="showFalseModal = false" aria-label="关闭">
            <X :size="16" />
          </button>
        </div>
        <div class="modal-body">
          <p class="modal-desc">
            排除警报后，大屏将恢复绿色常态，本条事件将被自动标注为 <strong>高难负例样本 (Hard Negative)</strong> 注入模型训练微调池：
          </p>
          <label class="reason-option">
            <input type="radio" v-model="selectedReason" value="现场专人指挥作业">
            <div>
              <strong>现场有专人持荧光指挥棒导引</strong>
              <div class="reason-sub">具备人车协同作业安全视距</div>
            </div>
          </label>
          <label class="reason-option">
            <input type="radio" v-model="selectedReason" value="具备特种检修作业临时安全许可">
            <div>
              <strong>具备特种检修作业临时安全许可</strong>
              <div class="reason-sub">通廊已提前放置黄色阻拦锥桶</div>
            </div>
          </label>
          <label class="reason-option">
            <input type="radio" v-model="selectedReason" value="摄像头透视错位虚假干涉">
            <div>
              <strong>摄像头透视错位虚假干涉 (高度层不同)</strong>
              <div class="reason-sub">叉车与人员处于不同垂直标高作业面</div>
            </div>
          </label>
        </div>
        <div class="modal-footer">
          <button class="btn-modal" @click="showFalseModal = false">取消</button>
          <button class="btn-modal btn-modal-primary" @click="submitFalseAlarm">
            一键排除并沉淀为难负例样本
          </button>
        </div>
      </div>
    </div>

    <!-- 高清逐帧研判与实景监控弹窗 -->
    <div class="modal-backdrop" :class="{ open: showHdModal }">
      <div class="modal-dialog hd-modal-dialog">
        <div class="modal-header">
          <span>高清画幅逐帧研判与现场实景监控 (CCTV-04 1920×1080@25帧/秒)</span>
          <button class="close-btn" @click="showHdModal = false" aria-label="关闭">
            <X :size="16" />
          </button>
        </div>
        <div class="modal-tabs">
          <button
            class="modal-tab-btn"
            :class="{ active: hdViewMode === 'keyframe' }"
            @click="hdViewMode = 'keyframe'"
          >
            <Image :size="13" class="tab-icon" />
            <span>算法探针标注关键帧 (#0575)</span>
          </button>
          <button
            class="modal-tab-btn"
            :class="{ active: hdViewMode === 'video' }"
            @click="hdViewMode = 'video'"
          >
            <Video :size="13" class="tab-icon" />
            <span>现场实景监控视频 (output_video7.mp4)</span>
          </button>
          <button
            class="modal-tab-btn"
            :class="{ active: hdViewMode === 'sequence' }"
            @click="hdViewMode = 'sequence'"
          >
            <Film :size="13" class="tab-icon" />
            <span>全时序处置时间切片 (5帧序列)</span>
          </button>
        </div>

        <div class="modal-body" style="padding:12px;">
          <!-- 1. 标注关键帧视图 -->
          <div class="hd-stage-wrap" v-if="hdViewMode === 'keyframe'">
            <img
              :src="cardIncident ? `/samples/cctv/keyframes/${cardIncident.keyframe.file}` : ''"
              :alt="cardIncident ? `1080P 标注关键帧 ${cardIncident.keyframe.id}` : '无关键帧'"
              class="hd-modal-media"
            />
          </div>

          <!-- 2. 原视频视图 -->
          <div class="hd-stage-wrap" v-else-if="hdViewMode === 'video'">
            <video
              src="/samples/cctv/videos/output_video7.mp4"
              controls
              autoplay
              loop
              class="hd-modal-media"
            ></video>
          </div>

          <!-- 3. 时序切片序列视图 -->
          <div class="hd-sequence-grid" v-else-if="hdViewMode === 'sequence'">
            <div class="seq-card">
              <span class="seq-tag">#0025 (1.0秒) 正常安全</span>
              <img src="/samples/cctv/keyframes/keyframe_0025_01_NORMAL_SAFE.png" alt="帧 25" />
            </div>
            <div class="seq-card">
              <span class="seq-tag">#0200 (8.0秒) 预警缓冲</span>
              <img src="/samples/cctv/keyframes/keyframe_0200_02_WARNING_BUFFER.png" alt="帧 200" />
            </div>
            <div class="seq-card">
              <span class="seq-tag">#0325 (13.0秒) 接近警示</span>
              <img src="/samples/cctv/keyframes/keyframe_0325_03_WARNING_APPROACH.png" alt="帧 325" />
            </div>
            <div class="seq-card critical-border">
              <span class="seq-tag tag-danger">#0575 (23.0秒) 临界碰撞</span>
              <img src="/samples/cctv/keyframes/keyframe_0575_04_CRITICAL_HAZARD.png" alt="帧 575" />
            </div>
            <div class="seq-card">
              <span class="seq-tag">#0700 (28.0秒) 复位安全</span>
              <img src="/samples/cctv/keyframes/keyframe_0700_05_NORMAL_CLEARED.png" alt="帧 700" />
            </div>
          </div>

          <div class="hd-meta-footer">
            <span>现场位置: 仓库主干道 (中转区南段)</span>
            <span v-if="cardIncident">
              险情段 {{ cardIncident.id }} ({{ cardIncident.startTime.toFixed(2) }}s ~ {{ cardIncident.endTime.toFixed(2) }}s)
              | 物理间距: {{ cardIncident.minDistPx }}像素 ({{ cardIncident.minDistM }}m)
              | 碰撞风险: {{ cardIncident.collisionRisk }}%
              | 综合烈度: {{ cardIncident.threatScore }} / 3.0
            </span>
            <span style="color:var(--telemetry-cyan);">OmniJev 延迟: {{ cardIncident?.latencyMs ?? 107.4 }}毫秒</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-modal" @click="showHdModal = false">关闭窗口</button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import {
  AlertOctagon,
  CheckCircle2,
  Maximize2,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  X,
  Image,
  Video,
  Film
} from 'lucide-vue-next'
import { useCctvMetadata } from '../../composables/useCctvMetadata'

const props = defineProps({
  currentTime: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['confirm-hazard', 'exclude-false', 'pending-change', 'locate-incident'])

const showFalseModal = ref(false)
const showHdModal = ref(false)
const hdViewMode = ref('keyframe')
const selectedReason = ref('现场专人指挥作业')
const resolvedReason = ref('现场专人指挥作业')

const flywheelText = ref('待标注采样')
const flywheelColor = ref('#7c3aed')

const currentTab = ref('all')

// ── 关键帧切片 (与 public/samples/cctv/keyframes/ 一一对应) ──────────────
const KEYFRAMES = [
  { t: 1.0, id: '0025', file: 'keyframe_0025_01_NORMAL_SAFE.png', label: '正常安全' },
  { t: 8.0, id: '0200', file: 'keyframe_0200_02_WARNING_BUFFER.png', label: '预警缓冲' },
  { t: 13.0, id: '0325', file: 'keyframe_0325_03_WARNING_APPROACH.png', label: '接近警示' },
  { t: 23.0, id: '0575', file: 'keyframe_0575_04_CRITICAL_HAZARD.png', label: '临界碰撞' },
  { t: 28.0, id: '0700', file: 'keyframe_0700_05_NORMAL_CLEARED.png', label: '复位安全' }
]

function nearestKeyframe(t) {
  return KEYFRAMES.reduce((best, kf) =>
    Math.abs(kf.t - t) < Math.abs(best.t - t) ? kf : best
  )
}

// ── 告警段落提取 ────────────────────────────────────────────────────────
// 连续非 NORMAL 帧合并为一段险情; 短于 MIN_EPISODE_FRAMES 的单帧抖动丢弃。
const MIN_EPISODE_FRAMES = 8 // 25fps 下约 0.32s

function summarizeEpisode(run) {
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
    reasons: peak.reasons || [],
    status: 'pending', // pending | confirmed | resolved
    keyframe: nearestKeyframe(peak.timestamp),
    isLedger: false
  }
}

function buildEpisodes(frames) {
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
  // 核验队列按发生时刻正序, 展示列表按时刻倒序 (最新在上)
  return episodes.sort((a, b) => a.startTime - b.startTime)
}

const { frames: cctvFrames, load: loadMetadata } = useCctvMetadata()

const episodes = ref([])
// 播放高水位: 记录曾经播放到的最远时刻, 回拖不会让已发生的告警从流水里消失
const maxReachedTime = ref(0)

watch(
  () => props.currentTime,
  (t) => {
    const v = Number(t) || 0
    if (v > maxReachedTime.value) maxReachedTime.value = v
  },
  { immediate: true }
)

onMounted(async () => {
  const frames = await loadMetadata()
  if (frames.length) episodes.value = buildEpisodes(frames)
})

// 已发生 (播放水位越过) 且仍待复核的段落
const visibleIncidents = computed(() =>
  episodes.value.filter(e => e.startTime <= maxReachedTime.value)
)

const incidents = visibleIncidents

const pendingIncident = computed(
  () => visibleIncidents.value.find(e => e.status === 'pending') || null
)

const hasPending = computed(() => pendingIncident.value !== null)

watch(
  hasPending,
  (v) => emit('pending-change', v),
  { immediate: true }
)

const reviewedCount = computed(() => visibleIncidents.value.filter(e => e.status !== 'pending').length)

// 顶部卡片数据源: 有待复核则显示该条, 否则回落到最近一次核验结论
const activeIncident = computed(() => pendingIncident.value || null)
const lastReviewed = computed(() => {
  const done = visibleIncidents.value.filter(e => e.status !== 'pending')
  return done.length ? done[done.length - 1] : null
})

// 卡片展示对象: 待复核险情 -> 进行中; 全部核验完 -> 最近一条结论
const cardIncident = computed(() => pendingIncident.value || lastReviewed.value)

const isCardPending = computed(() => pendingIncident.value !== null)

const pendingCount = computed(() => visibleIncidents.value.filter(e => e.status === 'pending').length)
const ledgerCount = computed(() => visibleIncidents.value.filter(e => e.isLedger).length)

const filteredIncidents = computed(() => {
  // 最新告警排在最前
  const rows = [...visibleIncidents.value].sort((a, b) => b.startTime - a.startTime)
  if (currentTab.value === 'pending') return rows.filter(i => i.status === 'pending')
  if (currentTab.value === 'ledger') return rows.filter(i => i.isLedger)
  return rows
})

function rowView(i) {
  if (i.status === 'pending') {
    return {
      time: i.startTime.toFixed(2) + '秒',
      device: `CCTV-04 (帧 #${i.frameId})`,
      tagClass: i.level === 'CRITICAL' ? 'tag-critical' : 'tag-warning',
      tagText: i.level === 'CRITICAL' ? '待复核' : '接近预警',
      meta: `${i.minDistPx ?? '--'}像素 / ${i.collisionRisk}%`,
      isActive: i.id === activeIncident.value?.id
    }
  }
  if (i.status === 'confirmed') {
    return {
      time: i.startTime.toFixed(2) + '秒',
      device: `CCTV-04 (帧 #${i.frameId})`,
      tagClass: 'tag-warning',
      tagText: '已入台账',
      meta: '正样本',
      isActive: false
    }
  }
  return {
    time: i.startTime.toFixed(2) + '秒',
    device: `CCTV-04 (帧 #${i.frameId})`,
    tagClass: 'tag-resolved',
    tagText: '误报解除',
    meta: '难负例',
    isActive: false
  }
}

function handleConfirmHazard() {
  const target = pendingIncident.value
  if (!target) return
  target.status = 'confirmed'
  target.isLedger = true
  flywheelText.value = '已标注为正样本 (已入微调池)'
  flywheelColor.value = '#15803d'
  emit('confirm-hazard', target)
}

function submitFalseAlarm() {
  const target = pendingIncident.value
  if (!target) return
  showFalseModal.value = false
  resolvedReason.value = selectedReason.value

  target.status = 'resolved'
  flywheelText.value = '已标注为高难负例 (反哺降误报)'
  flywheelColor.value = '#15803d'

  emit('exclude-false', selectedReason.value, target)
}

function locateIncident(i) {
  emit('locate-incident', i.startTime)
}

defineExpose({
  openHdModal: () => { showHdModal.value = true }
})
</script>

<style scoped>
.triage-dock {
  background: var(--bg-panel);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  height: 100%;
  user-select: none;
}

.triage-header {
  height: 38px;
  background: var(--bg-surface-elevated);
  border-bottom: 1px solid var(--border-machined);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 0.5px;
  font-size: 13px;
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
}

.active-hazard-card {
  padding: 12px 14px;
  background: rgba(255, 59, 48, 0.05);
  border-bottom: 2px solid var(--emergency-red);
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all 0.3s;
}

.active-hazard-card.resolved-card {
  background: rgba(48, 209, 88, 0.05);
  border-bottom: 2px solid var(--nominal-green);
}

.hazard-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hazard-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--emergency-red);
}

.rec-dot {
  width: 6px;
  height: 6px;
  background: var(--emergency-red);
  border-radius: 50%;
  animation: recBlink 1s infinite;
}

@keyframes recBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.hazard-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.probe-triad-box {
  background: var(--bg-canvas);
  border: 1px solid var(--border-machined);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.probe-triad-title {
  font-size: 11px;
  color: var(--telemetry-cyan);
  display: flex;
  justify-content: space-between;
  font-weight: 600;
}

.probe-triad-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.probe-metric-item {
  display: flex;
  flex-direction: column;
  padding: 5px;
  background: var(--bg-panel-subtle);
  border: 1px solid rgba(36, 45, 61, 0.8);
}

.p-label {
  font-size: 10px;
  color: var(--text-muted);
}

.p-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
  font-family: var(--font-mono);
}

.p-bar-wrap {
  width: 100%;
  height: 3px;
  background: #242d3d;
  margin-top: 4px;
  overflow: hidden;
}

.p-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.hd-snapshot-container {
  position: relative;
  height: 140px;
  background: #000;
  border: 1px solid var(--border-machined);
  overflow: hidden;
  cursor: pointer;
}

.snapshot-real-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hd-badge-overlay {
  position: absolute;
  top: 6px;
  left: 6px;
  font-size: 10px;
  background: rgba(0,0,0,0.8);
  border: 1px solid var(--border-machined);
  padding: 2px 6px;
  color: #fff;
  z-index: 2;
}

.hd-action-tip {
  position: absolute;
  bottom: 6px;
  right: 6px;
  font-size: 10px;
  background: rgba(0, 210, 255, 0.25);
  border: 1px solid var(--telemetry-cyan);
  padding: 2px 6px;
  color: var(--telemetry-cyan);
  z-index: 2;
}

.hazard-caption {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-panel-subtle);
  padding: 8px;
  border-left: 2px solid var(--emergency-red);
  line-height: 1.5;
}

.verification-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.action-btn-row {
  display: flex;
  gap: 8px;
}

.action-confirm-hazard {
  flex: 1.2;
  background: var(--emergency-red);
  color: #fff;
  border: 1px solid var(--emergency-red);
  padding: 9px 8px;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.15s ease;
}

.action-confirm-hazard:hover {
  background: #ff5247;
  box-shadow: 0 0 10px rgba(255, 59, 48, 0.4);
}

.action-exclude-false {
  flex: 1;
  background: var(--bg-surface-elevated);
  color: var(--text-main);
  border: 1px solid var(--border-bright);
  padding: 9px 8px;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.15s ease;
}

.action-exclude-false:hover {
  border-color: var(--nominal-green);
  color: var(--nominal-green);
}

.resolved-banner {
  background: rgba(48,209,88,0.1);
  border: 1px solid var(--nominal-green);
  padding: 8px 10px;
  font-size: 12px;
  color: var(--nominal-green);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-flywheel-ribbon {
  background: rgba(191, 90, 242, 0.08);
  border: 1px dashed var(--flywheel-purple);
  padding: 6px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  /* 面板底色为浅色 (白底叠 8% 紫), 必须用深色前景, 浅紫在此不可读 */
  color: #5b21b6;
}

.flywheel-tag {
  font-size: 10px;
  background: var(--flywheel-purple);
  color: #000;
  font-weight: 700;
  padding: 1px 5px;
}

.stream-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 200px;
}

.stream-toolbar {
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-machined);
  display: flex;
  gap: 6px;
}

.stream-tab {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  padding: 3px 10px;
  font-size: 11px;
  cursor: pointer;
}

.stream-tab.active {
  color: var(--text-main);
  background: var(--bg-surface-elevated);
  border-color: var(--border-machined);
  font-weight: 600;
}

.incident-table-wrap {
  flex: 1;
  overflow-y: auto;
}

.incident-empty {
  padding: 28px 14px;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
}

.incident-row {
  display: grid;
  grid-template-columns: 56px 100px 64px 1fr;
  align-items: center;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-machined);
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s;
}

.incident-row:hover {
  background: var(--bg-surface-elevated);
}

.incident-row.active {
  background: var(--bg-surface-elevated);
  border-left: 3px solid var(--emergency-red);
}

.row-time {
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--font-mono);
}

.row-device {
  color: var(--text-main);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tag-pill {
  display: inline-block;
  padding: 1px 5px;
  font-size: 10px;
  font-weight: 700;
  text-align: center;
  width: fit-content;
}

.tag-critical {
  background: var(--emergency-red-dim);
  color: var(--emergency-red);
  border: 1px solid var(--emergency-red);
}

.tag-warning {
  background: var(--safety-amber-dim);
  color: var(--safety-amber);
  border: 1px solid var(--safety-amber);
}

.tag-resolved {
  background: var(--nominal-green-dim);
  color: var(--nominal-green);
  border: 1px solid var(--nominal-green);
}

.row-meta {
  text-align: right;
  color: var(--text-secondary);
  font-size: 11px;
  font-family: var(--font-mono);
}

/* 弹窗通用样式 */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-backdrop.open {
  display: flex;
}

.modal-dialog {
  width: 440px;
  background: var(--bg-panel);
  border: 1px solid var(--border-bright);
  box-shadow: 0 16px 48px rgba(0,0,0,0.8);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 12px 16px;
  background: var(--bg-surface-elevated);
  border-bottom: 1px solid var(--border-machined);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
  font-size: 13px;
}

.close-btn {
  cursor: pointer;
  color: var(--text-muted);
}
.close-btn:hover {
  color: #fff;
}

.modal-tabs {
  display: flex;
  background: var(--bg-canvas);
  border-bottom: 1px solid var(--border-machined);
  padding: 0 12px;
  gap: 8px;
}

.modal-tab-btn {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  padding: 8px 10px;
  font-size: 12px;
  cursor: pointer;
}

.modal-tab-btn.active {
  color: var(--telemetry-cyan);
  border-bottom-color: var(--telemetry-cyan);
  font-weight: 700;
}

.modal-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-desc {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.reason-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  cursor: pointer;
  font-size: 12px;
  transition: border-color 0.15s;
}

.reason-option:hover {
  border-color: var(--telemetry-cyan);
}

.reason-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.modal-footer {
  padding: 12px 16px;
  background: var(--bg-surface-elevated);
  border-top: 1px solid var(--border-machined);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-modal {
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid var(--border-machined);
  background: var(--bg-panel-subtle);
  color: var(--text-main);
}

.btn-modal-primary {
  background: var(--nominal-green);
  color: #000;
  font-weight: 700;
  border-color: var(--nominal-green);
}

.hd-modal-dialog {
  width: 820px;
}

.hd-stage-wrap {
  background: #000;
  height: 380px;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border-machined);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hd-modal-media {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.hd-sequence-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}

.seq-card {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.seq-card.critical-border {
  border-color: var(--emergency-red);
}

.seq-card img {
  width: 100%;
  height: 90px;
  object-fit: cover;
}

.seq-tag {
  font-size: 10px;
  color: var(--text-muted);
}

.seq-tag.tag-danger {
  color: var(--emergency-red);
  font-weight: 700;
}

.hd-meta-footer {
  font-size: 11px;
  color: var(--text-secondary);
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.hazard-text {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.badge-icon-hazard {
  color: #991b1b;
  flex-shrink: 0;
}

.badge-icon-resolved {
  color: #14532d;
  flex-shrink: 0;
}

.hd-action-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tip-icon {
  flex-shrink: 0;
}

.resolved-banner-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.resolved-icon {
  flex-shrink: 0;
}

.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-icon {
  color: var(--safety-amber);
  flex-shrink: 0;
}

.close-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
}

.close-btn:hover {
  color: #fff;
}

.modal-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tab-icon {
  flex-shrink: 0;
}
</style>
