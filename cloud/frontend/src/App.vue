<template>
  <div class="app-wrapper">
    <!-- Aurora background or soft layered blurs -->
    <div class="bg-blur top-left"></div>
    <div class="bg-blur bottom-right"></div>
    <div class="bg-blur center-light"></div>
    
    <TopHeader />
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
import TopHeader from './components/dashboard/TopHeader.vue'
import SidebarNav from './components/dashboard/SidebarNav.vue'
import './assets/styles.css'
</script>

<style>
.app-wrapper {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.bg-blur {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  z-index: -1;
}
.top-left {
  width: 500px;
  height: 500px;
  background: rgba(111, 160, 255, 0.3);
  top: -200px;
  left: -200px;
}
.bottom-right {
  width: 600px;
  height: 600px;
  background: rgba(53, 201, 139, 0.15);
  bottom: -200px;
  right: -200px;
}
.center-light {
  width: 400px;
  height: 400px;
  background: rgba(245, 184, 75, 0.1);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 0 24px 24px 0;
  gap: 24px;
}
.main-content {
  flex: 1;
  overflow: hidden;
  height: calc(100vh - 80px - 24px); /* header height + padding */
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
