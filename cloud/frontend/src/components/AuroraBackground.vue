<template>
  <div class="aurora-canvas">
    <div class="aurora-bands">
      <div class="aurora-band band-1"></div>
      <div class="aurora-band band-2"></div>
      <div class="aurora-band band-3"></div>
      <div class="aurora-band band-4"></div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.aurora-canvas {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.aurora-bands {
  position: absolute;
  inset: 0;
}

.aurora-band {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.7;
}

.band-1 {
  width: 800px;
  height: 800px;
  top: -20%;
  left: -10%;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.45), transparent 70%);
}

.band-2 {
  width: 900px;
  height: 900px;
  top: -10%;
  right: -15%;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.4), transparent 70%);
}

.band-3 {
  width: 700px;
  height: 700px;
  bottom: -15%;
  left: 5%;
  background: radial-gradient(circle, rgba(191, 219, 254, 0.4), transparent 70%);
}

.band-4 {
  width: 600px;
  height: 600px;
  bottom: 10%;
  right: 10%;
  background: radial-gradient(circle, rgba(219, 234, 254, 0.5), transparent 70%);
}
</style>
