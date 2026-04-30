<template>
  <div class="app-container">
    <AuroraBackground />
    <SidebarNav />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import SidebarNav from './components/SidebarNav.vue'
import AuroraBackground from './components/AuroraBackground.vue'
</script>

<style>
@import url('https://rsms.me/inter/inter.css');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  /* Notion Inspired Colors */
  --notion-black: rgba(0, 0, 0, 0.95);
  --notion-blue: #0075de;
  --notion-blue-hover: #005bab;
  --notion-blue-bg: #f2f9ff;
  --notion-badge-text: #097fe8;
  
  --warm-dark: #31302e;
  --warm-gray-500: #615d59;
  --warm-gray-300: #a39e98;
  
  --semantic-teal: #2a9d99;
  --semantic-green: #1aae39;
  --semantic-orange: #dd5b00;
  
  /* Layout */
  --radius-micro: 4px;
  --radius-subtle: 5px;
  --radius-std: 8px;
  --radius-lg: 12px;
  --radius-pill: 9999px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: 'Inter', -apple-system, system-ui, Segoe UI, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #e2e8f0;
  color: var(--notion-black);
  min-height: 100vh;
  overflow-x: hidden;
}

/* Notion Typography Presets */
h1, .display-hero {
  font-weight: 700;
  letter-spacing: -0.04em; /* Approx -2.125px at 64px */
  line-height: 1.0;
  color: var(--notion-black);
}

h2, .section-heading {
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.0;
  color: var(--notion-black);
}

h3, .card-title {
  font-weight: 700;
  letter-spacing: -0.012em;
  line-height: 1.25;
}

.body-large { font-size: 20px; font-weight: 600; line-height: 1.4; letter-spacing: -0.006em; }
.body-std { font-size: 16px; font-weight: 400; line-height: 1.5; }
.caption { font-size: 14px; font-weight: 500; line-height: 1.43; color: var(--warm-gray-500); }

/* Global Components */
.btn-primary {
  background: var(--notion-blue);
  color: #fff;
  padding: 8px 16px;
  border-radius: var(--radius-micro);
  border: 1px solid transparent;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary:hover {
  background: var(--notion-blue-hover);
  transform: scale(1.02);
}

.btn-primary:active {
  transform: scale(0.95);
}

.badge-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  background: var(--notion-blue-bg);
  color: var(--notion-badge-text);
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.app-container {
  min-height: 100vh;
  display: flex;
  position: relative;
}

.main-content {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1), transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(140, 120, 180, 0.25);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(140, 120, 180, 0.4);
}

::selection {
  background: rgba(184, 169, 232, 0.3);
  color: #3a3550;
}
</style>
