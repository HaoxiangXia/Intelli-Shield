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
        <component :is="item.icon" :size="15" class="nav-icon" />
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
import {
  LayoutDashboard,
  ClipboardList,
  TrendingUp,
  Video
} from 'lucide-vue-next'

const menuItems = [
  { name: '态势总览', icon: LayoutDashboard, path: '/' },
  { name: '隐患台账', icon: ClipboardList, path: '/history' },
  { name: '趋势分析', icon: TrendingUp, path: '/trend' },
  { name: '视频感知阵列', icon: Video, path: '/devices' }
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

.nav-icon {
  flex-shrink: 0;
  color: var(--text-muted);
  transition: color 0.15s ease;
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
.nav-item.active .nav-icon {
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
