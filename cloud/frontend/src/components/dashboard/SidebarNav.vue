<template>
  <nav class="sidebar-nav">
    <div class="nav-container">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="active"
      >
        <span class="nav-code">{{ item.code }}</span>
        <span class="nav-text-cn">{{ item.name }}</span>
      </router-link>
    </div>
    
    <div class="officer-duty-chip">
      <span class="duty-dot"></span>
      <span>安全责任人: <strong>#01 [在岗值守]</strong></span>
    </div>
  </nav>
</template>

<script setup>
const menuItems = [
  { name: '态势总览', code: '01', path: '/' },
  { name: '趋势分析', code: '02', path: '/trend' },
  { name: '隐患台账', code: '03', path: '/history' },
  { name: '设备集群', code: '04', path: '/devices' },
  { name: '运行日志', code: '05', path: '/logs' }
]
</script>

<style scoped>
.sidebar-nav {
  width: 150px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background-color: var(--bg-panel);
  border-right: 1px solid var(--border-machined);
  user-select: none;
}

.nav-container {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 6px;
}

.nav-item {
  text-decoration: none;
  padding: 10px 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-sans);
  transition: all 0.15s ease;
  background: transparent;
}

.nav-code {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  width: 16px;
}

.nav-text-cn {
  font-size: 13px;
  font-weight: 600;
  color: inherit;
}

.nav-item:hover {
  background: var(--bg-surface-elevated);
  color: var(--text-main);
  border-color: var(--border-machined);
}

.nav-item.active {
  background: rgba(2, 132, 199, 0.08);
  border-color: rgba(2, 132, 199, 0.25);
  border-left: 3px solid var(--telemetry-cyan);
  color: var(--telemetry-cyan);
  font-weight: 700;
}
.nav-item.active .nav-code {
  color: var(--telemetry-cyan);
}

.officer-duty-chip {
  padding: 10px 8px;
  border-top: 1px solid var(--border-machined);
  background: var(--bg-panel-subtle);
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.duty-dot {
  width: 6px;
  height: 6px;
  background: var(--nominal-green);
  border-radius: 50%;
  box-shadow: 0 0 6px var(--nominal-green);
  flex-shrink: 0;
}

.officer-duty-chip strong {
  color: var(--telemetry-cyan);
  font-weight: 600;
}
</style>
