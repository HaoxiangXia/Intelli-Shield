<template>
  <div class="alarm-item">
    <div class="alarm-header">
      <div class="alarm-title">
        <span class="dot" :class="item.status === '已报警' ? 'danger' : 'normal'"></span>
        <span class="device-id">{{ item.deviceId }}</span>
      </div>
      <span class="time">{{ item.time }}</span>
    </div>
    
    <div class="alarm-content">
      <div class="tags">
        <span class="tag tag-danger">{{ item.status }}</span>
        <span class="tag tag-area">{{ item.area }}</span>
      </div>
      
      <div class="thumbnail-row">
        <div class="thumbnail">
          <img v-if="item.imageUrl" :src="item.imageUrl" alt="报警图片" class="thumbnail-img" />
          <div v-else class="placeholder-img">
            <el-icon><WarningFilled /></el-icon>
          </div>
        </div>
        <div class="details">
          <div class="duration">持续 {{ item.duration }}</div>
          <div class="desc">{{ item.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { WarningFilled } from '@element-plus/icons-vue'
defineProps({
  item: Object
})
</script>

<style scoped>
.alarm-item {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 16px;
  transition: all 0.2s ease;
  position: relative;
}
.alarm-item:hover {
  background: var(--glass-bg-strong);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(70, 100, 160, 0.08);
}
/* A slight gradient line on the left side to mark it's an alarm */
.alarm-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10%;
  height: 80%;
  width: 3px;
  background: var(--color-danger);
  border-radius: 0 4px 4px 0;
  opacity: 0.5;
}
.alarm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.alarm-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 6px;
  height: 6px;
  background: #8a7df0;
  border-radius: 50%;
}
.dot.danger {
  background: var(--color-danger);
}
.device-id {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-text-main);
}
.time {
  font-size: 13px;
  color: var(--color-text-muted);
}
.tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
}
.tag-danger {
  color: var(--color-danger);
  background: rgba(255, 77, 61, 0.1);
}
.tag-area {
  color: #6a5acd;
  background: rgba(106, 90, 205, 0.1);
}
.thumbnail-row {
  display: flex;
  gap: 12px;
}
.thumbnail {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0,0,0,0.03);
}
.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.placeholder-img {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(82, 113, 255, 0.1), rgba(53, 201, 139, 0.1));
  color: var(--color-danger);
  font-size: 20px;
}
.details {
  flex: 1;
}
.duration {
  font-size: 12px;
  color: var(--color-primary);
  margin-bottom: 6px;
}
.desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}
</style>
