<template>
  <div class="glass-card" :class="[paddingClass]">
    <div v-if="$slots.header || title" class="glass-header">
      <slot name="header">
        <h3 class="glass-title">{{ title }}</h3>
        <slot name="title-extra"></slot>
      </slot>
    </div>
    <div class="glass-body">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  noPadding: Boolean
})

const paddingClass = computed(() => props.noPadding ? 'no-padding' : 'with-padding')
</script>

<style scoped>
.glass-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: var(--glass-shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.with-padding {
  padding: 24px;
}
.glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.glass-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-main);
}
.glass-body {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
