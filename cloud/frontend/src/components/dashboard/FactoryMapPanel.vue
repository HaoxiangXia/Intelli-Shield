<template>
  <GlassCard class="factory-map-panel">
    <template #header>
      <div class="header-left">
        <h3 class="glass-title">工厂平面图</h3>
      </div>
      <div class="header-right">
        <span class="update-time">最近更新 {{ updateTime || '--:--:--' }}</span>
      </div>
    </template>
    
    <div class="map-body">
      <!-- Left side: 3 Metric cards -->
      <div class="map-metrics">
        <MetricCard label="设备总数" :value="stats.total" valueColor="var(--color-primary)" />
        <MetricCard label="在线" :value="stats.online" valueColor="var(--color-success)" />
        <MetricCard label="报警" :value="stats.alarm" valueColor="var(--color-danger)" />
      </div>
      
      <!-- Right side: Actual map -->
      <div class="map-container">
        <!-- Background Map Image -->
        <div class="simulated-map">
          <img :src="mapUrl" alt="Factory Map" class="map-image" />
          
          <!-- Nodes -->
          <div
            v-for="node in mapNodes"
            :key="node.deviceId"
            class="node"
            :class="node.status"
            :style="{ top: node.top, left: node.left }"
            :title="node.title"
          >
            <div
              v-if="node.showRipple"
              class="ripple"
              :class="node.status === 'warning' ? 'ripple-danger' : ''"
            ></div>
          </div>
        </div>
        
        <!-- Legend -->
        <div class="map-legend">
          <div class="legend-item">
            <span class="dot normal"></span>
            <span>正常</span>
          </div>
          <div class="legend-item">
            <span class="dot danger"></span>
            <span>报警</span>
          </div>
          <div class="legend-item">
            <span class="dot offline"></span>
            <span>离线</span>
          </div>
        </div>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import GlassCard from './GlassCard.vue'
import MetricCard from './MetricCard.vue'
import api from '../../lib/api'

const stats = ref({ total: 0, online: 0, alarm: 0 })
const devices = ref([])
const updateTime = ref('')
const mapUrl = `${import.meta.env.BASE_URL}map.jpg`

const MAP_WIDTH = 1920
const MAP_HEIGHT = 1080
const REFRESH_MS = 5000

let refreshTimer = null

function clampPercent(value) {
  return Math.min(92, Math.max(8, value))
}

function fallbackPosition(index) {
  const col = index % 3
  const row = Math.floor(index / 3)
  const left = 20 + col * 30
  const top = 25 + row * 20
  return { left: `${left}%`, top: `${top}%` }
}

function resolvePosition(device, index) {
  const posX = Number(device?.pos_x)
  const posY = Number(device?.pos_y)
  if (!Number.isFinite(posX) || !Number.isFinite(posY) || posX <= 0 || posY <= 0) {
    return fallbackPosition(index)
  }
  const left = clampPercent((posX / MAP_WIDTH) * 100)
  const top = clampPercent((posY / MAP_HEIGHT) * 100)
  return { left: `${left}%`, top: `${top}%` }
}

function resolveStatus(device) {
  if (device?.online_status !== 1) return 'offline'
  if (device?.alarm_status === 1) return 'warning'
  return 'normal'
}

function resolveUpdateTime(list) {
  const latest = (list || [])
    .map((item) => item?.update_time)
    .filter(Boolean)
    .sort()
    .pop()
  if (!latest) return ''
  return latest.length >= 19 ? latest.slice(11, 19) : latest
}

const mapNodes = computed(() =>
  devices.value.map((device, index) => {
    const position = resolvePosition(device, index)
    const status = resolveStatus(device)
    return {
      deviceId: device.device_id || `device-${index}`,
      status,
      top: position.top,
      left: position.left,
      showRipple: status !== 'offline',
      title: `${device.device_id || '-'} | ${status === 'warning' ? '报警' : status === 'offline' ? '离线' : '正常'}`
    }
  })
)

async function fetchLatest() {
  try {
    const res = await api.get('/api/latest')
    const payload = res.data || {}
    stats.value = payload.stats || { total: 0, online: 0, alarm: 0 }
    devices.value = payload.devices || []
    updateTime.value = resolveUpdateTime(payload.devices)
  } catch (error) {
    console.error('最新设备数据加载失败', error)
  }
}

onMounted(() => {
  fetchLatest()
  refreshTimer = setInterval(fetchLatest, REFRESH_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.factory-map-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.header-left, .header-right {
  display: flex;
  align-items: center;
}
.glass-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-main);
}
.update-time {
  font-size: 13px;
  color: var(--color-primary);
  background: rgba(47, 107, 255, 0.1);
  padding: 4px 12px;
  border-radius: 12px;
}
.map-body {
  display: flex;
  gap: 24px;
  flex: 1;
}
.map-metrics {
  width: 140px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.map-container {
  flex: 1;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.simulated-map {
  flex: 1;
  position: relative;
  background: #f0f2f5;
  overflow: hidden;
}
.map-image {
  width: 100%;
  height: 100%;
  object-fit: fill;
  display: block;
  opacity: 0.9;
}
.node {
  position: absolute;
  width: 14px; height: 14px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}
.node.normal { background: var(--color-success); box-shadow: 0 0 10px var(--color-success); }
.node.warning { background: var(--color-danger); box-shadow: 0 0 10px var(--color-danger); }
.node.offline { background: #8a7df0; }
.ripple {
  position: absolute;
  border: 2px solid var(--color-success);
  border-radius: 50%;
  width: 100%; height: 100%;
  top: -2px; left: -2px;
  animation: ripple-anim 2s infinite ease-out;
}
.ripple-danger { border-color: var(--color-danger); }
@keyframes ripple-anim {
  from { transform: scale(1); opacity: 1; }
  to { transform: scale(3); opacity: 0; }
}

.map-legend {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255,255,255,0.3);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.dot {
  width: 8px; height: 8px; border-radius: 50%;
}
.dot.normal { background: var(--color-success); }
.dot.danger { background: var(--color-danger); }
.dot.offline { background: #8a7df0; } /* Purpleish */
</style>
