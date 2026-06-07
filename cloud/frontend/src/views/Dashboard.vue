<template>
  <div class="dashboard-container">
    <!-- Center Column (Map and Chart) -->
    <div class="center-col">
      <div class="top-section">
        <FactoryMapPanel />
      </div>
      <div class="bottom-section">
        <AlarmTrendChart />
      </div>
    </div>
    
    <!-- Right Column (Alarms) -->
    <div class="right-col">
      <AlarmEventPanel />
    </div>
  </div>
</template>

<script setup>
import FactoryMapPanel from '../components/dashboard/FactoryMapPanel.vue'
import AlarmTrendChart from '../components/dashboard/AlarmTrendChart.vue'
import AlarmEventPanel from '../components/dashboard/AlarmEventPanel.vue'
</script>

<style scoped>
.dashboard-container {
  display: flex;
  gap: 24px;
  height: 100%;
  width: 100%;
}
.center-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0; /* Important for flex child to not overflow */
}
.right-col {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}
.top-section {
  flex: 5;
  min-height: 480px;
}
.bottom-section {
  flex: 3;
  min-height: 280px;
}

@media (max-width: 1400px) {
  .right-col {
    width: 340px;
  }
}
@media (max-width: 1100px) {
  .dashboard-container {
    flex-direction: column;
    overflow-y: auto;
    padding-bottom: 24px;
  }
  .right-col {
    width: 100%;
    min-height: 500px;
  }
  .center-col {
    flex: none;
  }
}
</style>
