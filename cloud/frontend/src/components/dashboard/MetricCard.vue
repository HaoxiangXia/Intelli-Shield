<template>
  <div class="metric-card">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value" :style="{ color: valueColor }">
      {{ value }}
      <span v-if="unit" class="unit">{{ unit }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  valueColor: {
    type: String,
    default: 'inherit'
  },
  unit: String
})
</script>

<style scoped>
.metric-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 16px;
  text-align: center;
  transition: transform 0.2s;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: var(--glass-shadow);
}
.metric-card:hover {
  transform: translateY(-2px);
  background: var(--glass-bg-strong);
}
.metric-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  font-weight: 500;
}
.metric-value {
  font-size: 32px;
  font-weight: 700;
}
.unit {
  font-size: 14px;
  font-weight: 500;
  margin-left: 2px;
}
</style>
