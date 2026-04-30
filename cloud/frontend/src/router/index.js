import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Devices from '../views/Devices.vue'
import Logs from '../views/Logs.vue'
import Trend from '../views/Trend.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/devices',
    name: 'Devices',
    component: Devices
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs
  },
  {
    path: '/trend',
    name: 'Trend',
    component: Trend
  },
  { path: '/history', name: 'History', component: () => import('../views/History.vue') } // 新增
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
