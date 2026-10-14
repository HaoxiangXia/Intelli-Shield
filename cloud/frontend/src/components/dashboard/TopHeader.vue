<template>
  <header class="telemetry-header">
    <div class="brand-section">
      <div class="brand-logo-badge">
        <img src="/logo.svg" alt="Logo" class="brand-logo-img" />
        <span class="brand-title">智盾</span>
        <span class="brand-version">2.0 工业安全中控指挥台</span>
      </div>
    </div>

    <div class="system-meta-section">
      <div class="system-clock">
        <Clock :size="13" class="clock-icon" />
        <span class="clock-time">{{ systemTime }}</span>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock } from 'lucide-vue-next'

const systemTime = ref('')
let timer = null

function updateClock() {
  const now = new Date()
  const pad = (n, l = 2) => String(n).padStart(l, '0')
  systemTime.value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ` +
                     `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}.${pad(Math.floor(now.getMilliseconds()), 3)}`
}

onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 100)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.telemetry-header {
  height: 52px;
  background-color: var(--bg-panel);
  border-bottom: 1px solid var(--border-machined);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
  position: relative;
  z-index: 20;
  user-select: none;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-logo-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-machined);
  border-left: 3px solid var(--telemetry-cyan);
}

.brand-logo-img {
  width: 18px;
  height: 18px;
}

.brand-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 1px;
  color: var(--text-main);
}

.brand-version {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 500;
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.2);
  padding: 2px 6px;
}
.system-meta-section {
  display: flex;
  align-items: center;
  gap: 14px;
}

.system-clock {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}

.clock-icon {
  color: var(--telemetry-cyan);
  flex-shrink: 0;
}
.clock-time {
  color: var(--text-main);
  font-weight: 600;
}
</style>
