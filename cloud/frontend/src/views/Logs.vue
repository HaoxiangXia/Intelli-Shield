<template>
  <div class="logs-page">
    <div class="content">
      <header class="page-header">
        <div class="header-main">
          <div class="header-title-row">
            <h1 class="page-title">业务日志与系统留痕</h1>
            <span class="live-pulse-badge">
              <span class="pulse-dot"></span>
              <span class="badge-text">系统日志中枢</span>
            </span>
          </div>
          <div class="subtitle">System & Business Operation Logs · 场端边缘网关与后端业务流时序日志</div>
        </div>
      </header>

      <div class="card">
        <div class="card-header">
          <span class="card-title">日志查询</span>
        </div>

        <div class="filter-bar">
          <select v-model="filterLevel" class="filter-control" aria-label="日志级别 Level Filter">
            <option value="all">全部级别</option>
            <option value="info">信息</option>
            <option value="warning">警告</option>
            <option value="error">错误</option>
          </select>
          <select v-model="filterCategory" class="filter-control" aria-label="日志分类 Category Filter">
            <option value="all">全部分类</option>
            <option value="ops">运维</option>
            <option value="biz">业务</option>
            <option value="sec">安全</option>
          </select>
          <input v-model="filterDevice" class="filter-control" type="text" placeholder="设备ID搜索" />
          <button @click="resetFilters" class="filter-action" type="button">
            <RotateCcw :size="13" class="btn-icon" />
            <span>重置筛选</span>
          </button>
        </div>

        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>级别</th>
                <th>分类</th>
                <th>设备ID</th>
                <th>事件</th>
                <th>消息</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="logs.length === 0">
                <td colspan="6" class="empty-state">暂无日志记录</td>
              </tr>
              <tr v-for="log in logs" :key="log.id">
                <td class="time-col">{{ log.ts || '-' }}</td>
                <td>
                  <span class="level-badge" :class="log.level">
                    {{ log.level || '-' }}
                  </span>
                </td>
                <td>{{ log.category || '-' }}</td>
                <td class="device-id">{{ log.device_id || '-' }}</td>
                <td>{{ log.event || '-' }}</td>
                <td>{{ log.message || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination">
          <button @click="prevPage" :disabled="page === 1" class="page-btn">上一页</button>
          <span class="page-info">第 {{ page }} 页，共 {{ totalPages }} 页</span>
          <button @click="nextPage" :disabled="page >= totalPages" class="page-btn">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { RotateCcw } from 'lucide-vue-next'
import api from '../lib/api'

const logs = ref([])
const filterLevel = ref('all')
const filterCategory = ref('all')
const filterDevice = ref('')
const page = ref(1)
const totalPages = ref(1)
const totalLogs = ref(0)

const limit = 20

function resetFilters() {
  filterLevel.value = 'all'
  filterCategory.value = 'all'
  filterDevice.value = ''
  page.value = 1
  fetchLogs()
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    fetchLogs()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    fetchLogs()
  }
}

async function fetchLogs() {
  try {
    const params = { page: page.value, page_size: limit }
    if (filterLevel.value !== 'all') params.level = filterLevel.value
    if (filterCategory.value !== 'all') params.category = filterCategory.value
    if (filterDevice.value) params.device_id = filterDevice.value

    const res = await api.get('/api/logs', { params })
    const data = res.data
    logs.value = data.logs || []
    totalLogs.value = data.total || 0
    totalPages.value = Math.ceil(totalLogs.value / limit)
  } catch (e) {
    console.error('获取日志失败:', e)
  }
}

watch([filterLevel, filterCategory, filterDevice], () => {
  page.value = 1
  fetchLogs()
})

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.logs-page {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-canvas);
  color: var(--text-main);
  box-sizing: border-box;
}

.content {
  padding: 20px 24px 28px;
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 页面标头 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-machined);
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.5px;
  margin: 0;
}

.live-pulse-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.3);
  padding: 2px 7px;
  border-radius: 3px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--nominal-green);
}

.badge-text {
  font-size: 10px;
  font-weight: 700;
  color: var(--nominal-green);
  font-family: var(--font-mono);
}

.subtitle {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.card {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-machined);
}

.card-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}

.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-control {
  height: 32px;
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 0 10px;
  font-size: 12px;
  font-family: var(--font-sans);
  background: var(--bg-panel);
  color: var(--text-main);
  outline: none;
  transition: border-color 0.15s ease;
}

.filter-control:focus {
  border-color: var(--telemetry-cyan);
}

.filter-action {
  height: 32px;
  padding: 0 14px;
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  background: var(--bg-panel-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.filter-action:hover {
  background: var(--bg-panel);
  border-color: var(--border-bright);
  color: var(--text-main);
}

.table-wrap {
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  text-align: left;
}

.data-table thead th {
  background: var(--bg-panel-subtle);
  color: var(--text-muted);
  font-weight: 700;
  font-size: 11px;
  padding: 9px 12px;
  border-bottom: 1px solid var(--border-machined);
  white-space: nowrap;
}

.data-table tbody tr {
  border-bottom: 1px solid var(--border-machined);
  transition: background 0.12s ease;
}

.data-table tbody tr:last-child {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: var(--bg-panel-subtle);
}

.data-table td {
  padding: 10px 12px;
  color: var(--text-main);
  vertical-align: middle;
}

.time-col {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.device-id {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--telemetry-cyan);
}

.level-badge {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.level-badge.info {
  color: var(--nominal-green);
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.3);
}

.level-badge.warning {
  color: var(--safety-amber);
  background: var(--safety-amber-dim);
  border: 1px solid rgba(217, 119, 6, 0.3);
}

.level-badge.error {
  color: var(--emergency-red);
  background: var(--emergency-red-dim);
  border: 1px solid rgba(220, 38, 38, 0.3);
}

.empty-state {
  text-align: center;
  padding: 36px 16px;
  color: var(--text-muted);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 6px;
}

.page-btn {
  padding: 5px 12px;
  border-radius: 4px;
  border: 1px solid var(--border-machined);
  background: var(--bg-panel);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.page-btn:hover:not(:disabled) {
  background: var(--bg-panel-subtle);
  border-color: var(--border-bright);
  color: var(--text-main);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
</style>
