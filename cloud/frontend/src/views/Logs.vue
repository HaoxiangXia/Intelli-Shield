<template>
  <div class="logs-page">
    <div class="content">
      <header class="header glass">
        <div class="header-left">
          <div class="header-title">
            <h1>业务日志</h1>
            <div class="subtitle">Business Logs</div>
          </div>
        </div>
      </header>

      <div class="card glass">
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
          <button @click="resetFilters" class="filter-action" type="button">重置筛选</button>
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
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content {
  padding: 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
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
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-shrink: 0;
}

.header-title h1 {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 600;
  color: #3a3550;
  letter-spacing: -0.01em;
  margin: 0;
}

.subtitle {
  font-size: 12px;
  color: #8a8aa8;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-top: 2px;
}

.card {
  border-radius: 24px;
  padding: 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(184, 169, 232, 0.15);
  flex-shrink: 0;
}

.card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: #3a3550;
}

.filter-bar {
  display: grid;
  grid-template-columns: 140px 140px 180px auto;
  gap: 12px;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.filter-control {
  height: 38px;
  border: 1px solid rgba(184, 169, 232, 0.2);
  border-radius: 12px;
  padding: 0 12px;
  font-size: 13px;
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: rgba(255, 255, 255, 0.3);
  color: #3a3550;
  outline: none;
  transition: all 0.2s;
}

.filter-control:focus {
  border-color: var(--color-primary);
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 4px rgba(47, 107, 255, 0.1);
}

.filter-action {
  height: 38px;
  padding: 0 16px;
  border: none;
  border-radius: 12px;
  background: rgba(184, 169, 232, 0.15);
  color: #5c5678;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  justify-self: start;
}

.filter-action:hover {
  background: rgba(184, 169, 232, 0.25);
  transform: translateY(-1px);
}

.table-wrap {
  flex: 1;
  overflow: auto;
  border-radius: 16px;
  margin-bottom: 20px;
  scrollbar-width: thin;
  scrollbar-color: rgba(184, 169, 232, 0.3) transparent;
}

.table-wrap::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-wrap::-webkit-scrollbar-thumb {
  background-color: rgba(184, 169, 232, 0.3);
  border-radius: 10px;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: rgba(255, 255, 255, 0.05);
}

.data-table thead {
  position: sticky;
  top: 0;
  z-index: 2;
  background: rgba(235, 240, 255, 0.95);
  backdrop-filter: blur(10px);
}

.data-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #5c5678;
  border-bottom: 1px solid rgba(184, 169, 232, 0.2);
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(184, 169, 232, 0.1);
  font-size: 13px;
  color: #3a3550;
  vertical-align: middle;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid rgba(184, 169, 232, 0.15);
  flex-shrink: 0;
}

.page-btn {
  padding: 8px 16px;
  border-radius: 12px;
  border: 1px solid rgba(184, 169, 232, 0.2);
  background: rgba(255, 255, 255, 0.2);
  color: #3a3550;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.4);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #8491ac;
  font-weight: 500;
}

.level-badge {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.level-badge.info {
  background: rgba(52, 199, 89, 0.14);
  color: #2d8a4e;
}

.level-badge.warning {
  background: rgba(255, 196, 87, 0.16);
  color: #a67c00;
}

.level-badge.error {
  background: rgba(255, 59, 48, 0.14);
  color: #c23a31;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: #8a8aa8;
}

.device-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--color-primary);
}

.time-col {
  white-space: nowrap;
  color: var(--color-text-secondary);
}

@media (max-width: 900px) {
  .filter-bar {
    grid-template-columns: 1fr;
  }
}
</style>
