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
        <span class="nav-text">{{ item.name }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
const menuItems = [
  { name: '实时总览', path: '/' },
  { name: '趋势分析', path: '/trend' },
  { name: '事件追溯', path: '/history' },
  { name: '设备管理', path: '/devices' },
  { name: '业务日志', path: '/logs' }
]
</script>

<style scoped>
.sidebar-nav {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-self: center;
}
.nav-container {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-left: none;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 0 20px 20px 0;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: var(--glass-shadow);
  height: max-content;
}
.nav-item {
  text-decoration: none;
  padding: 14px 20px;
  border-radius: 16px;
  color: var(--color-text-secondary);
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  text-align: center;
}
.nav-item:hover {
  background: rgba(255, 255, 255, 0.4);
  color: var(--color-text-main);
  transform: translateY(-2px);
}
.nav-item.active {
  background: linear-gradient(135deg, var(--color-primary-light), var(--color-primary));
  color: #fff;
  box-shadow: 0 8px 20px rgba(47, 107, 255, 0.25);
  font-weight: 600;
}
.nav-item.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(47, 107, 255, 0.35);
}
</style>
