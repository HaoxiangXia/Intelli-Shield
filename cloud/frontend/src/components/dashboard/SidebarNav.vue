<template>
  <nav class="sidebar-nav">
    <div class="brand-section">
      <div class="brand-logo-badge">
        <img src="/logo.svg" alt="Logo" class="brand-logo-img" />
        <span class="brand-title">智盾</span>
      </div>
    </div>

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
  justify-content: flex-start;
  background-color: var(--bg-panel);
  border-right: 1px solid var(--border-machined);
  user-select: none;
}

/* ── 品牌区 (原 TopHeader, 移至侧栏顶部) ─────────────────────────────── */
.brand-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 9px;
  padding: 16px 10px 14px;
  border-bottom: 1px solid var(--border-machined);
}

/* logo.svg 原始 viewBox 为 289x336 (竖版), 保持该比例避免被压扁留白 */
.brand-logo-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.brand-logo-img {
  width: 30px;
  height: 35px;
  object-fit: contain;
}

.brand-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 20px;
  line-height: 1;
  letter-spacing: 4px;
  /* 末字后的尾随字距会让 CJK 视觉偏左, 用 text-indent 抵消 */
  text-indent: 4px;
  color: var(--text-main);
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
  margin-top: auto;
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
