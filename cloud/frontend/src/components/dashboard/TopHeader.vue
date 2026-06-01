<template>
  <header class="top-header">
    <div class="logo-area">
      <img src="/logo.png" alt="Logo" class="logo" />
      <span class="title">智盾</span>
    </div>
    
    <div class="user-area">
      <el-icon class="settings-icon"><Setting /></el-icon>
      <div class="admin-dropdown">
        <span class="admin-text">管理员</span>
        <el-icon class="arrow-icon"><ArrowDown /></el-icon>
      </div>
    </div>
  </header>
</template>

<script setup>
import { Setting, ArrowDown } from '@element-plus/icons-vue'
</script>

<style scoped>
.top-header {
  height: 80px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-left: 12px;
  transition: transform 0.3s ease;
}
.logo-area:hover {
  transform: translateX(4px);
}
.logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(47, 107, 255, 0.2));
}
.title {
  font-family: 'Outfit', 'Segoe UI', system-ui, sans-serif;
  font-size: 26px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--color-primary) 0%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-left: auto;
}
.settings-icon {
  font-size: 20px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.settings-icon:hover {
  color: var(--color-primary);
  transform: rotate(45deg);
}
.admin-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(10px);
  transition: all 0.3s;
}
.admin-dropdown:hover {
  background: var(--glass-bg-strong);
}
.admin-text {
  font-size: 14px;
  color: var(--color-text-main);
  font-weight: 500;
}
</style>
