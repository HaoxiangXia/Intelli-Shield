<template>
  <div class="glass-card-wrapper" :style="wrapperStyle">
    <div class="aurora-bg">
      <div class="blob blob-1" :style="{ background: themeColor1 }"></div>
      <div class="blob blob-2" :style="{ background: themeColor2 }"></div>
      <div class="blob blob-3" :style="{ background: themeColor3 }"></div>
    </div>
    <div class="glass-card" :style="cardStyle">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: 'auto' },
  themeColor1: { type: String, default: '#bae6fd' },
  themeColor2: { type: String, default: '#bfdbfe' },
  themeColor3: { type: String, default: '#3b82f6' },
  borderRadius: { type: String, default: '24px' },
  padding: { type: String, default: '24px' }
})

const wrapperStyle = computed(() => ({
  width: props.width,
  height: props.height,
  position: 'relative',
  borderRadius: props.borderRadius,
  overflow: 'hidden'
}))

const cardStyle = computed(() => ({
  position: 'relative',
  zIndex: 1,
  width: '100%',
  height: '100%',
  background: 'rgba(255, 255, 255, 0.12)',
  backdropFilter: 'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.18)',
  borderRadius: props.borderRadius,
  padding: props.padding,
  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.2)'
}))
</script>

<style scoped>
.glass-card-wrapper {
  display: inline-block;
}

.aurora-bg {
  position: absolute;
  inset: -2px;
  overflow: hidden;
  border-radius: inherit;
  z-index: 0;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.5;
  animation: float 12s ease-in-out infinite;
}

.blob-1 {
  width: 180px;
  height: 180px;
  top: -30%;
  left: -20%;
  animation-delay: 0s;
}

.blob-2 {
  width: 220px;
  height: 220px;
  bottom: -40%;
  right: -25%;
  animation-delay: -4s;
}

.blob-3 {
  width: 140px;
  height: 140px;
  top: 30%;
  right: -15%;
  animation-delay: -8s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(8%, -5%) scale(1.05);
  }
  50% {
    transform: translate(-5%, 8%) scale(0.95);
  }
  75% {
    transform: translate(-8%, -3%) scale(1.02);
  }
}

.glass-card {
  box-sizing: border-box;
}
</style>