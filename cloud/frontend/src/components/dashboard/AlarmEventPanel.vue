<template>
  <GlassCard class="alarm-event-panel">
    <template #header>
      <div class="header-left">
        <h3 class="glass-title">告警事件</h3>
        <span class="badge-count">{{ events.length }}条</span>
      </div>
    </template>
    
    <div class="event-list">
      <AlarmEventItem 
        v-for="(item, index) in events" 
        :key="index" 
        :item="item" 
      />
    </div>
  </GlassCard>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import GlassCard from './GlassCard.vue'
import AlarmEventItem from './AlarmEventItem.vue'
import api from '../../lib/api'

const events = ref([])
const REFRESH_MS = 10000
let refreshTimer = null

function formatTime(timestamp) {
  if (!timestamp) return '--:--'
  return timestamp.length >= 16 ? timestamp.slice(11, 16) : timestamp
}

function formatDurationFromTimestamp(timestamp) {
  if (!timestamp) return '-'
  const normalized = timestamp.replace(' ', 'T')
  const start = new Date(normalized)
  if (Number.isNaN(start.getTime())) return '-'
  const diffSec = Math.max(0, Math.floor((Date.now() - start.getTime()) / 1000))
  if (diffSec < 60) return `${diffSec}秒`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}分钟`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}小时${diffMin % 60}分`
  const diffDay = Math.floor(diffHour / 24)
  return `${diffDay}天${diffHour % 24}小时`
}

function resolveImageUrl(imagePath) {
  if (!imagePath) return ''
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) return imagePath
  const normalized = imagePath.replace(/\\/g, '/')
  const imagesIndex = normalized.lastIndexOf('/images/')
  if (imagesIndex !== -1) {
    return normalized.slice(imagesIndex)
  }
  const alarmsIndex = normalized.lastIndexOf('/alarms/')
  if (alarmsIndex !== -1) {
    return `/images${normalized.slice(alarmsIndex)}`
  }
  const filename = normalized.split('/').pop()
  return filename ? `/images/alarms/${filename}` : ''
}

function mapAlarmToEvent(alarm) {
  return {
    deviceId: alarm?.device_id || '-',
    time: formatTime(alarm?.timestamp),
    status: alarm?.alarm === 1 ? '已报警' : '已恢复',
    area: alarm?.zone || '未知',
    duration: formatDurationFromTimestamp(alarm?.timestamp),
    desc: alarm?.description || '报警事件',
    imageUrl: resolveImageUrl(alarm?.image_path)
  }
}

async function fetchEvents() {
  try {
    const res = await api.get('/api/recent-alarms', { params: { limit: 10 } })
    const alarms = res.data?.alarms || []
    events.value = alarms.map(mapAlarmToEvent)
  } catch (error) {
    console.error('告警事件加载失败', error)
    events.value = []
  }
}

onMounted(() => {
  fetchEvents()
  refreshTimer = setInterval(fetchEvents, REFRESH_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.alarm-event-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.glass-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-main);
}
.badge-count {
  font-size: 12px;
  color: var(--color-primary);
  background: rgba(47, 107, 255, 0.1);
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 500;
}
.event-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  flex: 1;
  padding-right: 8px;
  /* 自定义滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: rgba(184, 169, 232, 0.3) transparent;
}
/* Custom Scrollbar for Chrome/Safari */
.event-list::-webkit-scrollbar {
  width: 5px;
}
.event-list::-webkit-scrollbar-track {
  background: transparent;
}
.event-list::-webkit-scrollbar-thumb {
  background: rgba(184, 169, 232, 0.3);
  border-radius: 10px;
}
.event-list::-webkit-scrollbar-thumb:hover {
  background: rgba(184, 169, 232, 0.5);
}
</style>
