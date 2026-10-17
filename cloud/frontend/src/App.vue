<template>
  <div class="app-wrapper">
    <div class="main-layout">
      <SidebarNav />
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import SidebarNav from './components/dashboard/SidebarNav.vue'
</script>

<style scoped>
.app-wrapper {
  position: relative;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-canvas);
}

.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
  background: var(--border-machined);
  gap: 1px;
}

.main-content {
  flex: 1;
  overflow: hidden;
  background-color: var(--bg-canvas);
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
