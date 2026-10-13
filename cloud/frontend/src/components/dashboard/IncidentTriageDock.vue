<template>
  <aside class="triage-dock">
    <div class="triage-header">
      <span class="triage-title">险情核验处置坞</span>
    </div>

    <!-- 待复核告警卡片 (PRD 4.4 规范) -->
    <div
      class="active-hazard-card"
      :class="{ 'resolved-card': !activeHazard }"
    >
      <div class="hazard-title-row">
        <div class="hazard-badge">
          <span class="rec-dot" v-if="activeHazard"></span>
          <span :style="{ color: activeHazard ? 'var(--emergency-red)' : 'var(--nominal-green)' }">
            {{ activeHazard ? '待复核临界险情 (帧 #0575)' : '✔ 警报已核验排除 (已解挂)' }}
          </span>
        </div>
        <span class="hazard-time">{{ activeHazard ? '23.00秒 实时抓拍' : '已归档闭环' }}</span>
      </div>

      <!-- 三路认知探针遥测仪 -->
      <div class="probe-triad-box">
        <div class="probe-triad-title">
          <span>OmniJev 三路认知探针遥测</span>
          <span style="color:var(--text-muted)">RTX 3090 集群 · 107.4毫秒</span>
        </div>
        <div class="probe-triad-grid">
          <div class="probe-metric-item">
            <span class="p-label">1. 碰撞风险概率</span>
            <span
              class="p-val"
              :style="{ color: activeHazard ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
            >
              {{ activeHazard ? '78.5%' : '12.0%' }}
            </span>
            <div class="p-bar-wrap">
              <div
                class="p-bar-fill"
                :style="{ width: activeHazard ? '78.5%' : '12%', background: activeHazard ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
              ></div>
            </div>
          </div>

          <div class="probe-metric-item">
            <span class="p-label">2. 工人注意力状态</span>
            <span
              class="p-val"
              :style="{ color: activeHazard ? 'var(--safety-amber)' : 'var(--nominal-green)', fontSize: '11px' }"
            >
              {{ activeHazard ? '分心背对 60%' : '安全隔离 85%' }}
            </span>
            <div class="p-bar-wrap">
              <div
                class="p-bar-fill"
                :style="{ width: activeHazard ? '60%' : '85%', background: activeHazard ? 'var(--safety-amber)' : 'var(--nominal-green)' }"
              ></div>
            </div>
          </div>

          <div class="probe-metric-item">
            <span class="p-label">3. 综合危害烈度</span>
            <span
              class="p-val"
              :style="{ color: activeHazard ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
            >
              {{ activeHazard ? '2.48 / 3.0' : '0.45 / 3.0' }}
            </span>
            <div class="p-bar-wrap">
              <div
                class="p-bar-fill"
                :style="{ width: activeHazard ? '82%' : '15%', background: activeHazard ? 'var(--emergency-red)' : 'var(--nominal-green)' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 真实高清关键帧抓拍切片 -->
      <div class="hd-snapshot-container" @click="showHdModal = true" title="点击放大查看 1080P 高清逐帧原图">
        <span class="hd-badge-overlay">
          {{ activeHazard ? 'CCTV-04 抓拍 #0575 (足底越过红光线 -0.88m · 一票否决)' : 'CCTV-04 抓拍 #0025 (红光线外 +2.27m 安全隔离)' }}
        </span>
        <span class="hd-action-tip">🔍 点击放大展开 1080P 逐帧研判</span>

        <img
          :src="activeHazard ? '/samples/cctv/keyframes/keyframe_0575_04_CRITICAL_HAZARD.png' : '/samples/cctv/keyframes/keyframe_0025_01_NORMAL_SAFE.png'"
          alt="CCTV 关键帧抓拍"
          class="snapshot-real-img"
        />
      </div>

      <div class="hazard-caption">
        <strong>{{ activeHazard ? '双系统分层仲裁结论:' : '核验结论 (责任人解除):' }}</strong>
        {{ activeHazard 
          ? '【紧急】工人双脚踏入叉车三向红光警戒线内侧 (-0.88m / ZONE_INSIDE)，物理硬约束一票否决直出 CRITICAL；叠加 OmniJev 探针检出分心背对 65.0%，已触发声光急停阻断。'
          : `经安全责任人现场视频复核，判定为【${resolvedReason}】。威胁排除，大屏复位，样本已提交算法微调队列。`
        }}
      </div>

      <!-- 责任人一键核验按钮区域 (PRD 4.4 规范) -->
      <div class="verification-actions">
        <template v-if="activeHazard">
          <div class="action-btn-row">
            <button
              class="action-confirm-hazard"
              @click="handleConfirmHazard"
              title="确认确实存在危险，触发对讲并归入台账，沉淀为正样本"
            >
              <span>🚨 确认属实 - 紧迫隐患</span>
            </button>
            <button
              class="action-exclude-false"
              @click="showFalseModal = true"
              title="属于专人指挥或特种作业，排除警报，沉淀为难负例"
            >
              <span>🛡️ 判定误报 - 排除警报</span>
            </button>
          </div>
        </template>
        <template v-else>
          <div class="resolved-banner">
            <span>✔ 警报解除流程已闭环</span>
            <span style="font-weight:700;">高难负例样本已沉淀</span>
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
          全部 ({{ incidents.length }})
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
          :class="{ active: item.isActive }"
        >
          <span class="row-time">{{ item.time }}</span>
          <span class="row-device">{{ item.device }}</span>
          <span class="tag-pill" :class="item.tagClass">{{ item.tagText }}</span>
          <span class="row-meta">{{ item.meta }}</span>
        </div>
      </div>
    </div>

    <!-- 误报排除原因选择弹窗 -->
    <div class="modal-backdrop" :class="{ open: showFalseModal }">
      <div class="modal-dialog">
        <div class="modal-header">
          <span>🛡️ 责任人判定误报 · 选择排除核验依据</span>
          <span class="close-btn" @click="showFalseModal = false">✕</span>
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
          <span class="close-btn" @click="showHdModal = false">✕</span>
        </div>
        <div class="modal-tabs">
          <button
            class="modal-tab-btn"
            :class="{ active: hdViewMode === 'keyframe' }"
            @click="hdViewMode = 'keyframe'"
          >
            🖼️ 算法探针标注关键帧 (#0575)
          </button>
          <button
            class="modal-tab-btn"
            :class="{ active: hdViewMode === 'video' }"
            @click="hdViewMode = 'video'"
          >
            📹 现场实景监控视频 (output_video7.mp4)
          </button>
          <button
            class="modal-tab-btn"
            :class="{ active: hdViewMode === 'sequence' }"
            @click="hdViewMode = 'sequence'"
          >
            🎞️ 全时序处置时间切片 (5帧序列)
          </button>
        </div>

        <div class="modal-body" style="padding:12px;">
          <!-- 1. 标注关键帧视图 -->
          <div class="hd-stage-wrap" v-if="hdViewMode === 'keyframe'">
            <img
              src="/samples/cctv/keyframes/keyframe_0575_04_CRITICAL_HAZARD.png"
              alt="1080P 标注关键帧 0575"
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
            <span>物理间距: 111.4像素 | 碰撞风险: 78.5% | 综合烈度: 2.48 / 3.0</span>
            <span style="color:var(--telemetry-cyan);">OmniJev 延迟: 107.4毫秒</span>
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
import { ref, computed } from 'vue'

const props = defineProps({
  activeHazard: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['confirm-hazard', 'exclude-false'])

const showFalseModal = ref(false)
const showHdModal = ref(false)
const hdViewMode = ref('keyframe')
const selectedReason = ref('现场专人指挥作业')
const resolvedReason = ref('现场专人指挥作业')

const flywheelText = ref('待标注采样')
const flywheelColor = ref('#c084fc')

const currentTab = ref('all')

const incidents = ref([
  {
    id: 1,
    time: '17:12:00',
    device: 'CCTV-04 (中转区南段)',
    type: 'critical',
    tagClass: 'tag-critical',
    tagText: '待复核',
    meta: '111.4像素 / 78.5%',
    isActive: true,
    isPending: true,
    isLedger: false
  },
  {
    id: 2,
    time: '17:11:54',
    device: 'CCTV-04 (集装箱卡车旁)',
    type: 'warning',
    tagClass: 'tag-warning',
    tagText: '接近预警',
    meta: '184像素 / 48.0%',
    isActive: false,
    isPending: false,
    isLedger: false
  },
  {
    id: 3,
    time: '17:11:44',
    device: 'CCTV-04 (北通廊道)',
    type: 'resolved',
    tagClass: 'tag-resolved',
    tagText: '误报解除',
    meta: '难负例',
    isActive: false,
    isPending: false,
    isLedger: false
  },
  {
    id: 4,
    time: '17:08:22',
    device: 'CCTV-02 (冲压A线)',
    type: 'ledger',
    tagClass: 'tag-warning',
    tagText: '已入台账',
    meta: '正样本',
    isActive: false,
    isPending: false,
    isLedger: true
  },
  {
    id: 5,
    time: '17:02:18',
    device: 'CCTV-01 (焊接工段)',
    type: 'resolved',
    tagClass: 'tag-resolved',
    tagText: '误报解除',
    meta: '难负例',
    isActive: false,
    isPending: false,
    isLedger: false
  },
  {
    id: 6,
    time: '16:58:05',
    device: 'CCTV-04 (主通廊交汇)',
    type: 'ledger',
    tagClass: 'tag-critical',
    tagText: '已入台账',
    meta: '正样本',
    isActive: false,
    isPending: false,
    isLedger: true
  }
])

const pendingCount = computed(() => incidents.value.filter(i => i.isPending).length)
const ledgerCount = computed(() => incidents.value.filter(i => i.isLedger).length)

const filteredIncidents = computed(() => {
  if (currentTab.value === 'pending') {
    return incidents.value.filter(i => i.isPending)
  }
  if (currentTab.value === 'ledger') {
    return incidents.value.filter(i => i.isLedger)
  }
  return incidents.value
})

function handleConfirmHazard() {
  flywheelText.value = '✔ 标注为正样本 (已入微调池)'
  flywheelColor.value = '#30d158'
  
  const activeItem = incidents.value.find(i => i.id === 1)
  if (activeItem) {
    activeItem.tagText = '已入台账'
    activeItem.isPending = false
    activeItem.isLedger = true
  }

  emit('confirm-hazard')
}

function submitFalseAlarm() {
  showFalseModal.value = false
  resolvedReason.value = selectedReason.value
  
  flywheelText.value = '✔ 标注为高难负例 (反哺降误报)'
  flywheelColor.value = '#30d158'

  const activeItem = incidents.value.find(i => i.id === 1)
  if (activeItem) {
    activeItem.tagClass = 'tag-resolved'
    activeItem.tagText = '误报解除'
    activeItem.meta = '难负例'
    activeItem.isPending = false
  }

  emit('exclude-false', selectedReason.value)
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
  color: #e9d5ff;
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
</style>
