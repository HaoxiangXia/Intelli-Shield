<template>
  <div class="threat-timeline-panel">
    <div class="threat-header">
      <span class="threat-title">时序危险走势与时空门控状态通道 (30秒连续序列)</span>
      <div class="keyframe-dots">
        <span class="kf-badge">#0025 🛡️ 门控阻断</span>
        <span class="kf-arrow">➔</span>
        <span class="kf-badge">#0200 司机排除</span>
        <span class="kf-arrow">➔</span>
        <span class="kf-badge">#0325 GPU待机</span>
        <span class="kf-arrow">➔</span>
        <span class="kf-badge kf-danger">#0575 ⚡ 门控激活 (唤醒 OneJev)</span>
        <span class="kf-arrow">➔</span>
        <span class="kf-badge">#0700 🛡️ 复位休眠</span>
      </div>
    </div>
    
    <div class="threat-body">
      <div class="ecg-chart-box">
        <svg class="ecg-svg" viewBox="0 0 600 82" preserveAspectRatio="none">
          <!-- 临界险情阈值 0.70 -->
          <line x1="0" y1="16" x2="600" y2="16" stroke="rgba(255, 59, 48, 0.4)" stroke-dasharray="3,3" stroke-width="1"/>
          <text x="5" y="13" fill="#ff3b30" font-family="'JetBrains Mono', monospace" font-size="8.5">P(碰撞) = 0.70 [临界险情阈值]</text>

          <!-- 注意预警阈值 0.40 -->
          <line x1="0" y1="34" x2="600" y2="34" stroke="rgba(255, 159, 10, 0.4)" stroke-dasharray="3,3" stroke-width="1"/>
          <text x="5" y="31" fill="#ff9f0a" font-family="'JetBrains Mono', monospace" font-size="8.5">P(碰撞) = 0.40 [注意预警阈值]</text>

          <!-- 面积填充 -->
          <path
            :d="areaPath"
            :fill="activeHazard ? 'rgba(255, 59, 48, 0.15)' : 'rgba(48, 209, 88, 0.08)'"
          />

          <!-- 折线 -->
          <path
            :d="linePath"
            fill="none"
            :stroke="activeHazard ? '#ff3b30' : '#30d158'"
            stroke-width="2"
          />

          <!-- 关键帧特征点 -->
          <g v-if="activeHazard">
            <circle cx="20" cy="50" r="2.5" fill="#30d158"/>
            <circle cx="160" cy="42" r="2.5" fill="#ff9f0a"/>
            <circle cx="260" cy="30" r="2.5" fill="#ff9f0a"/>
            <circle cx="460" cy="12" r="4" fill="#ff3b30">
              <animate attributeName="r" values="3;6;3" dur="1s" repeatCount="indefinite"/>
            </circle>
          </g>

          <!-- ================= 方案 4: 时空门控活动区间条 (Gate Activity Ribbon) ================= -->
          <!-- 门控活动通道底槽 -->
          <text x="5" y="70" fill="#64748b" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700">时空门控</text>
          <rect x="52" y="60" width="544" height="15" fill="#f1f5f9" stroke="#cbd5e1" rx="2" />

          <!-- 区间 1: 0s ~ 18s (x: 52 ~ 410) 门控阻断休眠 (司机排除/静止车) -->
          <rect x="54" y="62" width="354" height="11" fill="rgba(2, 132, 199, 0.10)" stroke="rgba(2, 132, 199, 0.3)" rx="2" />
          <text x="231" y="70.5" fill="#0369a1" font-size="7.5" font-family="'PingFang SC', sans-serif" font-weight="600" text-anchor="middle">
            🛡️ 门控阻断休眠 (车载司机排除 / 车辆静止 | GPU 待机 0W)
          </text>

          <!-- 区间 2: 18s ~ 26s (x: 410 ~ 522) 门控激活高危区间 (唤醒 OneJev) -->
          <rect x="410" y="61.5" width="112" height="12" fill="rgba(220, 38, 38, 0.20)" stroke="#dc2626" stroke-width="1.2" rx="2">
            <animate attributeName="opacity" values="0.75;1;0.75" dur="1.2s" repeatCount="indefinite" />
          </rect>
          <text x="466" y="70.5" fill="#991b1b" font-size="8" font-family="'PingFang SC', sans-serif" font-weight="700" text-anchor="middle">
            ⚡ 门控激活 (唤醒 OneJev 107ms)
          </text>

          <!-- 区间 3: 26s ~ 30s (x: 524 ~ 594) 复位安全 -->
          <rect x="524" y="62" width="70" height="11" fill="rgba(2, 132, 199, 0.10)" stroke="rgba(2, 132, 199, 0.3)" rx="2" />
          <text x="559" y="70.5" fill="#0369a1" font-size="7" font-family="'PingFang SC', sans-serif" text-anchor="middle">
            🛡️ 复位待机
          </text>
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

      <div class="telemetry-metrics-summary">
        <div class="metric-sub-card">
          <span class="metric-sub-label">时空门控节流率</span>
          <span class="metric-sub-val" style="color:#0284c7">73.3% 压降</span>
        </div>
        <div class="metric-sub-card">
          <span class="metric-sub-label">防误报拦截率</span>
          <span class="metric-sub-val" style="color:var(--nominal-green)">100% (司机排除)</span>
        </div>
        <div class="metric-sub-card">
          <span class="metric-sub-label">HPC 推理延迟</span>
          <span class="metric-sub-val">107.4 毫秒</span>
        </div>
        <div class="metric-sub-card">
          <span class="metric-sub-label">峰值危害烈度</span>
          <span class="metric-sub-val" :style="{ color: activeHazard ? 'var(--emergency-red)' : 'var(--nominal-green)' }">
            {{ activeHazard ? '2.48 / 3.0' : '0.45 / 3.0' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

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

const playheadX = computed(() => {
  const cur = Math.max(0, Math.min(30.08, Number(props.currentTime) || 0))
  // Map 0~30.08 seconds to X range: 52 to 594
  return 52 + (cur / 30.08) * (594 - 52)
})

const linePath = computed(() => {
  if (props.activeHazard) {
    return 'M 0 52 L 40 50 L 120 48 L 160 42 L 220 38 L 260 30 L 360 26 L 420 18 L 460 12 L 520 12 L 600 12'
  } else {
    return 'M 0 52 L 40 50 L 120 48 L 160 49 L 220 50 L 260 49 L 360 50 L 420 49 L 460 48 L 520 49 L 600 49'
  }
})

const areaPath = computed(() => {
  return `${linePath.value} L 600 58 L 0 58 Z`
})
</script>

<style scoped>
.threat-timeline-panel {
  height: 124px;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-machined);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  user-select: none;
}

.threat-header {
  height: 26px;
  padding: 0 14px;
  border-bottom: 1px solid rgba(36, 45, 61, 0.6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 10px;
}

.threat-title {
  color: var(--text-muted);
}

.keyframe-dots {
  display: flex;
  align-items: center;
  gap: 4px;
}

.kf-badge {
  color: var(--text-secondary);
  font-size: 9px;
}

.kf-badge.kf-danger {
  color: var(--emergency-red);
  font-weight: 700;
}

.kf-arrow {
  color: var(--border-bright);
  font-size: 8px;
}

.threat-body {
  flex: 1;
  padding: 4px 14px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.ecg-chart-box {
  flex: 1;
  height: 100%;
  position: relative;
}

.ecg-svg {
  width: 100%;
  height: 100%;
}

.telemetry-metrics-summary {
  width: 270px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  font-family: var(--font-mono);
  border-left: 1px solid var(--border-machined);
  padding-left: 12px;
}

.metric-sub-card {
  display: flex;
  flex-direction: column;
}

.metric-sub-label {
  font-size: 10px;
  color: var(--text-muted);
}

.metric-sub-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--telemetry-cyan);
}
</style>
