<template>
  <div class="dashboard-workspace">
    <!-- 左侧列：实景视频智能推演视窗 与 时序威胁走势心电图 -->
    <div class="tactical-column">
      <div class="radar-section">
        <TacticalRadarTwin
          :active-hazard="isHazardActive"
          @time-update="onTimeUpdate"
          @open-hd="handleOpenHd"
        />
      </div>
      <div class="timeline-section">
        <ThreatTimelineChart
          :active-hazard="isHazardActive"
          :current-time="videoCurrentTime"
          :today-interventions="interventionsCount"
        />
      </div>
    </div>

    <!-- 右侧列：险情核验处置坞 -->
    <div class="triage-column">
      <IncidentTriageDock
        ref="triageDockRef"
        :active-hazard="isHazardActive"
        @confirm-hazard="onConfirmHazard"
        @exclude-false="onExcludeFalse"
      />
    </div>

    <!-- 全局浮动广播通知 -->
    <div class="notification-toast" :class="[{ show: toastVisible }, toastTypeClass]">
      <div class="toast-icon">{{ toastIcon }}</div>
      <div class="toast-content">
        <div class="toast-title">{{ toastTitle }}</div>
        <div class="toast-message">{{ toastMessage }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import TacticalRadarTwin from '../components/dashboard/TacticalRadarTwin.vue'
import ThreatTimelineChart from '../components/dashboard/ThreatTimelineChart.vue'
import IncidentTriageDock from '../components/dashboard/IncidentTriageDock.vue'

const isHazardActive = ref(true)
const videoCurrentTime = ref(0)
function onTimeUpdate(t) {
  videoCurrentTime.value = t
}
const interventionsCount = ref(38)
const triageDockRef = ref(null)

// 浮动通知系统
const toastVisible = ref(false)
const toastIcon = ref('📢')
const toastTitle = ref('')
const toastMessage = ref('')
const toastTypeClass = ref('toast-hazard')
let toastTimer = null

function triggerToast(icon, title, message, isDanger = true) {
  if (toastTimer) clearTimeout(toastTimer)
  toastIcon.value = icon
  toastTitle.value = title
  toastMessage.value = message
  toastTypeClass.value = isDanger ? 'toast-hazard' : 'toast-nominal'
  toastVisible.value = true

  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 4500)
}

function handleOpenHd() {
  if (triageDockRef.value) {
    triageDockRef.value.openHdModal()
  }
}

// PRD 4.4 责任人核验响应处理
function onConfirmHazard() {
  triggerToast(
    '📢',
    '现场对讲喊话已开启 · 归入《隐患台账》',
    '系统已向叉车下发减速制动指令，调度中心广播已通报：“通廊人员背向危险，请立即避让！”',
    true
  )
}

function onExcludeFalse(reason) {
  isHazardActive.value = false
  triggerToast(
    '🛡️',
    '警报已核验排除 · 样本沉淀为高难负例',
    `责任人核验依据：【${reason}】。大屏已恢复绿色常态，样本已反哺目标检测与认知探针模型训练池。`,
    false
  )
}
</script>

<style scoped>
.dashboard-workspace {
  display: grid;
  grid-template-columns: 1fr 430px;
  gap: 1px;
  background: var(--border-machined);
  height: 100%;
  width: 100%;
  overflow: hidden;
  position: relative;
}

.tactical-column {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-canvas);
  min-width: 0;
}

.radar-section {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.timeline-section {
  flex-shrink: 0;
}

.triage-column {
  width: 430px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-panel);
}

/* 浮动提示 */
.notification-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.15);
  padding: 12px 18px;
  color: var(--text-main);
  align-items: center;
  gap: 12px;
  z-index: 999;
  font-size: 12px;
  transform: translateY(140%);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  pointer-events: none;
}

.notification-toast.show {
  transform: translateY(0);
}

.toast-hazard {
  border-left: 4px solid var(--emergency-red);
}

.toast-nominal {
  border-left: 4px solid var(--nominal-green);
}

.toast-icon {
  font-size: 18px;
}

.toast-title {
  font-weight: 700;
  color: #fff;
}

.toast-message {
  color: var(--text-secondary);
  font-size: 12px;
  margin-top: 2px;
  line-height: 1.4;
}

@media (max-width: 1200px) {
  .dashboard-workspace {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
    overflow-y: auto;
  }
  .triage-column {
    width: 100%;
    height: 480px;
  }
}
</style>
