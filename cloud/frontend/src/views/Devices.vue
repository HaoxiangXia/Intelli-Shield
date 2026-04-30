<template>
  <div class="devices-page">
    <div class="content">
      <header class="header glass">
        <div class="header-left">
          <div class="header-title">
            <h1>设备列表</h1>
            <div class="subtitle">Device Management</div>
          </div>
          <div class="ws-status">
            <span class="ws-dot" :class="{ connected: socketConnected }"></span>
            <span>{{ socketStatusText }}</span>
          </div>
        </div>
      </header>

      <div class="card glass">
        <div class="card-header">
          <span class="card-title">设备状态</span>
        </div>

        <div class="filter-bar">
          <select v-model="filterStatus" class="filter-control" aria-label="状态筛选 Status Filter">
            <option value="all">全部状态</option>
            <option value="online">在线</option>
            <option value="offline">离线</option>
            <option value="alarm">报警</option>
          </select>
          <select v-model="filterZone" class="filter-control" aria-label="区域筛选 Zone Filter">
            <option value="all">全部区域</option>
            <option value="A区">A区</option>
            <option value="B区">B区</option>
            <option value="C区">C区</option>
            <option value="D区">D区</option>
            <option value="未知">未知</option>
          </select>
          <input v-model="filterDevice" class="filter-control" type="text" placeholder="设备ID搜索" />
          <button @click="resetFilters" class="filter-action" type="button">重置筛选</button>
        </div>

        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>设备ID</th>
                <th>在线状态</th>
                <th>当前区域</th>
                <th>报警状态</th>
                <th>报警计数</th>
                <th>最后更新</th>
                <th>报警图片</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredDevices.length === 0">
                <td colspan="7" class="empty-state">暂无匹配设备</td>
              </tr>
              <tr v-for="dev in filteredDevices" :key="dev.device_id" @click="showDeviceDetail(dev.device_id)">
                <td class="device-id">{{ dev.device_id || '-' }}</td>
                <td>
                  <span class="status-indicator">
                    <span class="status-dot" :class="dev.online_status === 1 ? 'normal' : 'offline'"></span>
                    <span class="status-text" :class="dev.online_status === 1 ? 'normal' : 'offline'">
                      {{ dev.online_status === 1 ? `在线 (${getDeviceZone(dev)})` : `离线 (${getDeviceZone(dev)})` }}
                    </span>
                  </span>
                </td>
                <td>{{ getDeviceZone(dev) }}</td>
                <td>
                  <span class="status-indicator">
                    <span class="status-dot" :class="dev.alarm_status === 1 ? 'alarm' : 'normal'"></span>
                    <span class="status-text" :class="dev.alarm_status === 1 ? 'alarm' : 'normal'">
                      {{ dev.alarm_status === 1 ? (getAlarmDurationText(dev) ? `报警(${getAlarmDurationText(dev)})` : '报警') : '正常' }}
                    </span>
                  </span>
                </td>
                <td>{{ dev.error_count || 0 }}</td>
                <td class="time-col">{{ dev.last_seen || '-' }}</td>
                <td>
                  <button v-if="dev.alarm_status === 1" @click.stop="showDeviceImages(dev.device_id)" class="img-btn">
                    查看
                  </button>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 设备详情模态框 -->
    <div class="modal glass-modal" v-if="showDeviceModal">
      <div class="modal-content glass">
        <div class="modal-header">
          <h3>设备详情 - {{ selectedDeviceId }}</h3>
          <button @click="showDeviceModal = false" class="modal-close" aria-label="关闭">×</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingDeviceDetail" class="empty-state">加载中...</div>
          <div v-else>
            <div class="device-meta">
              <div><strong>设备ID:</strong> {{ selectedDevice?.device_id || '-' }}</div>
              <div><strong>在线状态:</strong> {{ selectedDevice?.online_status === 1 ? '在线' : '离线' }}</div>
              <div><strong>当前区域:</strong> {{ getDeviceZone(selectedDevice) }}</div>
              <div><strong>报警状态:</strong> {{ selectedDevice?.alarm_status === 1 ? '报警' : '正常' }}</div>
              <div><strong>错误计数:</strong> {{ selectedDevice?.error_count || 0 }}</div>
              <div><strong>最后更新:</strong> {{ selectedDevice?.last_seen || '-' }}</div>
            </div>
            <div class="chart-container"><canvas id="historyChart" ref="historyChart"></canvas></div>
            <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 10px; color: #3a3550;">最近记录</h4>
            <div class="history-list">
              <div v-if="deviceHistory.length === 0" class="empty-state">暂无历史记录</div>
              <div v-for="(h, index) in deviceHistory" :key="index" class="history-item">
                <span>{{ h.timestamp || '-' }}</span>
                <span>{{ h.event || '-' }}</span>
              </div>
            </div>
            <div v-if="alarmDurationInfo" class="alarm-duration-info glass">
              <p style="font-weight:600;margin-bottom:8px;font-size:13px;color:#3a3550;">报警时长统计</p>
              <p v-if="alarmDurationInfo.currentDuration" style="color:#c23a31;font-weight:500;font-size:13px;">
                当前报警已持续: <strong>{{ formatDuration(alarmDurationInfo.currentDuration) }}</strong>
              </p>
              <p style="font-size:12px;color:#8a8aa8;">
                报警总次数: {{ alarmDurationInfo.totalSessions || 0 }} |
                平均时长: {{ formatDuration(alarmDurationInfo.avgDuration || 0) }} |
                最长: {{ formatDuration(alarmDurationInfo.maxDuration || 0) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片查看模态框 -->
    <div class="modal glass-modal" v-if="showImageModal">
      <div class="modal-content glass">
        <div class="modal-header">
          <h3>报警图片 - {{ selectedDeviceId }}</h3>
          <button @click="showImageModal = false" class="modal-close" aria-label="关闭">×</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingImages" class="empty-state">加载中...</div>
          <div v-else>
            <div v-if="deviceImages.length === 0" class="empty-state">暂无报警图片</div>
            <div v-else class="image-gallery">
              <img v-for="(img, index) in deviceImages" :key="index" :src="'/' + img.image_path" alt="报警图片" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { io } from 'socket.io-client'
import api from '../lib/api'
import { getAuthToken } from '../lib/auth'
import Chart from 'chart.js/auto'

const devices = ref([])
const filterStatus = ref('all')
const filterZone = ref('all')
const filterDevice = ref('')
const socketConnected = ref(false)
const socketStatusText = ref('Socket.io: 未连接')
const showDeviceModal = ref(false)
const showImageModal = ref(false)
const selectedDeviceId = ref('')
const selectedDevice = ref(null)
const deviceHistory = ref([])
const deviceImages = ref([])
const loadingDeviceDetail = ref(false)
const loadingImages = ref(false)
const alarmDurationInfo = ref(null)
const historyChart = ref(null)

let chartInstance = null
let socket = null

const filteredDevices = computed(() => {
  return devices.value.filter((dev) => {
    const id = (dev.device_id || '').toLowerCase()
    const keywordOk = !filterDevice.value || id.includes(filterDevice.value.toLowerCase())
    let statusOk = true
    if (filterStatus.value === 'online') statusOk = dev.online_status === 1
    if (filterStatus.value === 'offline') statusOk = dev.online_status !== 1
    if (filterStatus.value === 'alarm') statusOk = dev.alarm_status === 1
    const zoneOk = filterZone.value === 'all' ? true : getDeviceZone(dev) === filterZone.value
    return keywordOk && statusOk && zoneOk
  })
})

function resetFilters() {
  filterStatus.value = 'all'
  filterZone.value = 'all'
  filterDevice.value = ''
}

function inferZoneFromPosition(posX, posY) {
  const x = Number(posX)
  const y = Number(posY)
  if (!Number.isFinite(x) || !Number.isFinite(y) || (x === 0 && y === 0)) return '未知'
  const left = x < 960
  const top = y < 540
  if (left && top) return 'A区'
  if (!left && top) return 'B区'
  if (left && !top) return 'C区'
  return 'D区'
}

function getDeviceZone(dev) {
  if (!dev) return '未知'
  if (dev.current_zone) return String(dev.current_zone)
  if (dev.zone) return String(dev.zone)
  if (dev.zone_id) return String(dev.zone_id)
  return inferZoneFromPosition(dev.pos_x, dev.pos_y)
}

function formatDuration(seconds) {
  if (seconds == null || seconds <= 0) return '0秒'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  let parts = []
  if (h > 0) parts.push(`${h}小时`)
  if (m > 0) parts.push(`${m}分`)
  if (s > 0 || parts.length === 0) parts.push(`${s}秒`)
  return parts.join('')
}

function formatDurationShort(seconds) {
  if (seconds == null || seconds <= 0) return '0s'
  const s = Math.floor(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = Math.floor(s % 60)
  let parts = ''
  if (h > 0) parts += `${h}h`
  if (m > 0 || h > 0) parts += `${m}m`
  parts += `${sec}s`
  return parts
}

function getAlarmDurationSeconds(dev) {
  if (!dev || dev.alarm_status !== 1) return null
  if (dev.alarm_start_time) {
    const start = new Date(String(dev.alarm_start_time).replace(' ', 'T'))
    if (!Number.isNaN(start.getTime())) {
      return (Date.now() - start.getTime()) / 1000
    }
  }
  if (dev.current_duration_sec != null) return Number(dev.current_duration_sec)
  return null
}

function getAlarmDurationText(dev) {
  const seconds = getAlarmDurationSeconds(dev)
  if (seconds == null) return ''
  return formatDurationShort(seconds)
}

async function showDeviceDetail(deviceId) {
  selectedDeviceId.value = deviceId
  selectedDevice.value = devices.value.find(d => d.device_id === deviceId)
  loadingDeviceDetail.value = true
  deviceHistory.value = []
  alarmDurationInfo.value = null

  try {
    const res = await api.get(`/api/device/${deviceId}/history`)
    const data = res.data
    deviceHistory.value = data.history || []
    updateHourlyChart(data, deviceHistory.value)

    const sessRes = await api.get(`/api/device/${deviceId}/alarm-sessions`)
    if (sessRes.ok) {
      const sessData = sessRes.data
      alarmDurationInfo.value = {
        currentDuration: sessData.current_duration_sec,
        totalSessions: sessData.stats?.total_sessions,
        avgDuration: sessData.stats?.avg_duration,
        maxDuration: sessData.stats?.max_duration
      }
    }
  } catch (e) {
    console.error('加载设备详情失败:', e)
  } finally {
    loadingDeviceDetail.value = false
  }

  showDeviceModal.value = true
}

async function showDeviceImages(deviceId) {
  selectedDeviceId.value = deviceId
  loadingImages.value = true
  deviceImages.value = []

  try {
    const res = await api.get(`/api/device/${deviceId}/images`)
    const data = res.data
    deviceImages.value = data.images || []
  } catch (e) {
    console.error('加载设备图片失败:', e)
  } finally {
    loadingImages.value = false
  }

  showImageModal.value = true
}

function updateHourlyChart(apiData, historyData) {
  if (!historyChart.value) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  let labels = Array.isArray(apiData.hourly_labels) ? apiData.hourly_labels : []
  let counts = Array.isArray(apiData.hourly_counts) ? apiData.hourly_counts : []

  if (labels.length !== 24 || counts.length !== 24) {
    labels = Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, '0')}:00`)
    counts = Array.from({ length: 24 }, () => 0)

    const now = new Date()
    const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
    historyData.forEach((item) => {
      const ts = item.timestamp || ''
      const isAlarm = item.alarm_status === 1 || item.alarm === 1
      if (!isAlarm || !ts.startsWith(today)) return
      const hour = Number((ts.split(' ')[1] || '').split(':')[0])
      if (Number.isInteger(hour) && hour >= 0 && hour <= 23) counts[hour] += 1
    })
  }

  const ctx = historyChart.value.getContext('2d')
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '当天每小时报警次数',
        data: counts,
        backgroundColor: 'rgba(255, 59, 48, 0.20)',
        borderColor: '#ff3b30',
        borderWidth: 1.2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1 }
        }
      }
    }
  })
}

async function initData() {
  try {
    const res = await api.get('/api/latest')
    devices.value = res.data.devices || []
  } catch (e) {
    console.error('初始化数据失败:', e)
  }
}

onMounted(() => {
  initData()

  socket = io({ auth: { token: getAuthToken() } })
  socket.on('connect', () => {
    socketConnected.value = true
    socketStatusText.value = 'Socket.io: 已连接'
  })

  socket.on('disconnect', () => {
    socketConnected.value = false
    socketStatusText.value = 'Socket.io: 未连接'
  })

  socket.on('device_update', (payload) => {
    if (payload.devices) {
      payload.devices.forEach((dev) => {
        const index = devices.value.findIndex(d => d.device_id === dev.device_id)
        if (index !== -1) {
          devices.value[index] = { ...devices.value[index], ...dev }
        } else {
          devices.value.push(dev)
        }
      })
    }
  })

  socket.on('position_update', (data) => {
    if (data) {
      data.forEach((dev) => {
        const index = devices.value.findIndex(d => d.device_id === dev.device_id)
        if (index !== -1) {
          devices.value[index] = { ...devices.value[index], ...dev }
        } else {
          devices.value.push(dev)
        }
      })
    }
  })

  const durationInterval = setInterval(() => {
    if (document.visibilityState === 'visible') {
      devices.value = [...devices.value]
    }
  }, 1000)

  onUnmounted(() => {
    clearInterval(durationInterval)
    if (socket) socket.disconnect()
    if (chartInstance) chartInstance.destroy()
  })
})
</script>

<style scoped>
.devices-page {
  min-height: 100vh;
  position: relative;
}

.content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: page-reveal 0.7s cubic-bezier(0.4, 0, 0.2, 1) both;
}

@keyframes page-reveal {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.glass {
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow:
    0 8px 32px rgba(30, 64, 175, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.header {
  border-radius: 20px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.header-title h1 {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 600;
  color: #3a3550;
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: 12px;
  color: #8a8aa8;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-top: 2px;
}

.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #8a8aa8;
}

.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #b0a8c8;
  transition: background 0.3s ease;
}

.ws-dot.connected {
  background: #34c759;
  box-shadow: 0 0 8px rgba(52, 199, 89, 0.4);
}

.card {
  border-radius: 24px;
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--notion-black);
  letter-spacing: -0.012em;
}

.filter-bar {
  display: grid;
  grid-template-columns: 160px 160px 200px auto;
  gap: 12px;
  margin-bottom: 24px;
}

.filter-control {
  height: 36px;
  border: 1px solid var(--warm-gray-300);
  border-radius: var(--radius-micro);
  padding: 0 12px;
  font-size: 14px;
  background: #ffffff;
  color: var(--notion-black);
  outline: none;
  transition: all 0.2s;
}

.filter-control:focus {
  border-color: var(--notion-blue);
  box-shadow: 0 0 0 2px rgba(0, 117, 222, 0.1);
}

.filter-action {
  height: 36px;
  padding: 0 16px;
  border: 1px solid var(--warm-gray-300);
  border-radius: var(--radius-micro);
  background: rgba(0, 0, 0, 0.05);
  color: var(--notion-black);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-action:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.table-wrap {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 960px;
}

.data-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--warm-gray-500);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background: rgba(0, 0, 0, 0.02);
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  vertical-align: middle;
  color: var(--notion-black);
  font-size: 14px;
}

.data-table tbody tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

.data-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

.device-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 600;
}

.time-col {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--warm-gray-500);
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.normal { background: var(--semantic-green); }
.status-dot.alarm { background: var(--semantic-orange); animation: dot-pulse 1.5s ease-in-out infinite; }
.status-dot.offline { background: var(--warm-gray-300); }

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text.normal { color: var(--semantic-green); font-weight: 600; }
.status-text.alarm { color: var(--semantic-orange); font-weight: 600; }
.status-text.offline { color: var(--warm-gray-500); }

.img-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-pill);
  background: var(--notion-blue-bg);
  color: var(--notion-badge-text);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.img-btn:hover {
  background: #e1f0ff;
  transform: translateY(-1px);
}

.empty-state {
  text-align: center;
  padding: 36px 16px;
  color: #8a8aa8;
}

.glass-modal {
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: rgba(30, 20, 60, 0.5);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: modal-fade-in 0.25s ease;
}

@keyframes modal-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 24px;
  animation: modal-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes modal-slide-in {
  from { opacity: 0; transform: translateY(20px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.modal-header h3 {
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: #3a3550;
}

.modal-body {
  padding: 20px;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.15);
  color: #8a8aa8;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
  color: #3a3550;
  transform: rotate(90deg);
}

.device-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
  color: #4a4a6a;
  font-size: 13px;
}

.chart-container {
  height: 260px;
  margin-bottom: 12px;
}

.history-list {
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.08);
}

.history-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 13px;
  color: #4a4a6a;
}

.history-item:last-child {
  border-bottom: none;
}

.alarm-duration-info {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 16px;
}

.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.image-gallery img {
  max-width: 220px;
  max-height: 160px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease;
}

.image-gallery img:hover {
  transform: scale(1.04);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

@media (max-width: 900px) {
  .filter-bar {
    grid-template-columns: 1fr;
  }
  .device-meta {
    grid-template-columns: 1fr;
  }
}
</style>
