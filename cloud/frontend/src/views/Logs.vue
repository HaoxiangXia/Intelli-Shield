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
  border-bottom: 1px solid rgba(184, 169, 232, 0.15);
}

.card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: #3a3550;
}

.filter-bar {
  display: grid;
  grid-template-columns: 160px 160px 200px auto;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-control {
  height: 36px;
  border: 1px solid rgba(184, 169, 232, 0.2);
  border-radius: 12px;
  padding: 0 12px;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  background: rgba(255, 255, 255, 0.3);
  color: #3a3550;
  outline: none;
  transition: border-color 0.2s, background 0.2s;
}

.filter-control:focus {
  border-color: rgba(139, 92, 246, 0.4);
  background: rgba(255, 255, 255, 0.45);
}

.filter-action {
  height: 36px;
  padding: 0 16px;
  border: 1px solid rgba(184, 169, 232, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.25);
  color: #3a3550;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  justify-self: start;
  transition: background 0.2s, transform 0.15s ease;
}

.filter-action:hover {
  background: rgba(255, 255, 255, 0.4);
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
  font-family: 'Outfit', sans-serif;
  font-size: 11px;
  font-weight: 600;
  color: #8a8aa8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(184, 169, 232, 0.12);
  background: rgba(255, 255, 255, 0.1);
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(184, 169, 232, 0.08);
  vertical-align: middle;
  color: #4a4a6a;
}

.data-table tbody tr {
  transition: background-color 0.2s ease;
}

.data-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.2);
}

.device-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
}

.time-col {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #8a8aa8;
  white-space: nowrap;
}

.level-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'Outfit', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.04em;
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
  padding: 36px 16px;
  color: #8a8aa8;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(184, 169, 232, 0.12);
}

.page-btn {
  padding: 8px 18px;
  border: 1px solid rgba(184, 169, 232, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.25);
  color: #3a3550;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.45);
  transform: translateY(-1px);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #8a8aa8;
}

@media (max-width: 900px) {
  .filter-bar {
    grid-template-columns: 1fr;
  }
}
</style>
