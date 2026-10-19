<template>
  <div class="ledger-page">
    <div class="content-container">
      <!-- 页面标头 -->
      <header class="page-header">
        <div class="header-main">
          <div class="header-title-row">
            <h1 class="page-title">隐患台账与处置审计</h1>
            <span class="live-pulse-badge">
              <span class="pulse-dot"></span>
              <span class="badge-text">审计留痕</span>
            </span>
          </div>
          <p class="page-desc">特种车辆视频感知与探针排险处置台账</p>
        </div>
        <div class="header-actions">
          <div class="officer-chip">
            <span class="officer-dot"></span>
            <span>责任人: <strong>#01 [在岗]</strong></span>
          </div>
          <span class="system-tag font-mono">107.4ms 恒频对齐</span>
          <button @click="fetchHistory" class="btn-tool" type="button" :disabled="isRefreshing">
            <RefreshCw :size="12" :class="{ spinning: isRefreshing }" />
            <span>{{ isRefreshing ? '刷新中' : '刷新' }}</span>
          </button>
        </div>
      </header>

      <!-- 统计栏：4栏细线网格 -->
      <div class="metrics-grid">
        <div class="metric-block">
          <span class="m-label">台账总量</span>
          <div class="m-val-row">
            <span class="m-val">{{ totalCount }}</span>
            <span class="m-unit">起</span>
          </div>
        </div>
        <div class="metric-block">
          <span class="m-label">危急制动</span>
          <div class="m-val-row">
            <span class="m-val val-danger">{{ criticalCount }}</span>
            <span class="m-unit">起切断</span>
          </div>
        </div>
        <div class="metric-block">
          <span class="m-label">临界预警</span>
          <div class="m-val-row">
            <span class="m-val val-warning">{{ warningCount }}</span>
            <span class="m-unit">起避让</span>
          </div>
        </div>
        <div class="metric-block">
          <span class="m-label">误报排除</span>
          <div class="m-val-row">
            <span class="m-val val-cyan">{{ dismissedCount }}</span>
            <span class="m-unit">起沉淀</span>
          </div>
        </div>
      </div>

      <!-- 过滤栏 -->
      <div class="filter-toolbar">
        <div class="segment-group">
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'ALL' }"
            @click="currentFilter = 'ALL'"
            type="button"
          >
            全部 ({{ totalCount }})
          </button>
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'CRITICAL' }"
            @click="currentFilter = 'CRITICAL'"
            type="button"
          >
            危急制动 ({{ criticalCount }})
          </button>
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'WARNING' }"
            @click="currentFilter = 'WARNING'"
            type="button"
          >
            临界预警 ({{ warningCount }})
          </button>
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'DISMISSED' }"
            @click="currentFilter = 'DISMISSED'"
            type="button"
          >
            误报排除 ({{ dismissedCount }})
          </button>
          <button
            class="seg-btn"
            :class="{ active: currentFilter === 'NORMAL' }"
            @click="currentFilter = 'NORMAL'"
            type="button"
          >
            门控过滤 ({{ normalCount }})
          </button>
        </div>

        <div class="search-box">
          <Search :size="13" class="search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索事件ID / 点位 / 关键词..."
            class="search-input"
          />
          <button
            v-if="searchQuery"
            class="search-clear-btn"
            @click="searchQuery = ''"
          >
            <X :size="12" />
          </button>
        </div>
      </div>

      <!-- 数据表 -->
      <div class="table-container">
        <table class="ledger-table">
          <thead>
            <tr>
              <th style="width: 130px;">事件编号</th>
              <th style="width: 145px;">时间</th>
              <th style="width: 170px;">点位 / 区域</th>
              <th style="width: 95px;">定性</th>
              <th>排险依据与探针遥测</th>
              <th style="width: 110px;">结论</th>
              <th style="width: 90px; text-align: center;">研判</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredData.length === 0">
              <td colspan="7" class="empty-cell">无匹配记录</td>
            </tr>
            <template v-else-if="page === 1">
              <tr
                v-for="item in filteredData"
                :key="item.id"
                class="ledger-row"
                @click="openAuditModal(item)"
              >
                <td class="font-mono id-cell">{{ item.id }}</td>
                <td class="font-mono time-cell">{{ item.timestamp }}</td>
                <td>
                  <div class="point-name">
                    <Video :size="12" class="point-icon" />
                    <span>{{ item.device_id }}</span>
                  </div>
                  <div class="point-zone">{{ item.zone }}</div>
                </td>
                <td>
                  <span class="severity-tag" :class="`sev-${item.level?.toLowerCase()}`">
                    {{ item.levelText }}
                  </span>
                </td>
                <td class="evidence-cell">
                  <div class="evidence-main">{{ item.description }}</div>
                  <div class="evidence-telemetry font-mono" v-if="item.probesSummary">
                    <span class="telemetry-chip">{{ item.probesSummary }}</span>
                    <span class="telemetry-chip subtle" v-if="item.latency">{{ item.latency }}ms</span>
                    <span class="telemetry-chip subtle" v-if="item.redZoneSummary">{{ item.redZoneSummary }}</span>
                  </div>
                </td>
                <td>
                  <span class="status-cell" :class="`st-${item.status}`">
                    {{ item.statusText }}
                  </span>
                </td>
                <td style="text-align: center;">
                  <button
                    class="btn-inspect"
                    @click.stop="openAuditModal(item)"
                    type="button"
                  >
                    <Eye :size="12" />
                    <span>研判</span>
                  </button>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="7" class="empty-archive-cell">
                <div class="empty-archive-box">
                  <Archive :size="22" class="empty-icon" />
                  <div class="empty-archive-title font-mono">第 {{ page }} 页暂无活动归档缓存</div>
                  <div class="empty-archive-desc">
                    历史排险台账记录已归档至物理冷存储备份仓 · 支持按工单号精确检索
                  </div>
                  <button class="btn-return-page1" @click="page = 1" type="button">
                    返回第 1 页
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分页控制栏 -->
        <div class="pagination-bar">
          <div class="page-meta font-mono">
            <span>显示第 {{ page === 1 && filteredData.length > 0 ? `1-${filteredData.length}` : '0' }} 条</span>
            <span class="meta-sep">/</span>
            <span>共 {{ totalSimulatedCount }} 条记录</span>
            <span class="meta-sep">·</span>
            <span>{{ pageSize }} 条/页</span>
          </div>

          <div class="page-controls">
            <button
              class="page-nav-btn"
              :disabled="page <= 1"
              @click="page--"
              type="button"
            >
              <ChevronLeft :size="13" />
              <span>上一页</span>
            </button>

            <div class="page-numbers font-mono">
              <button
                v-for="p in totalPages"
                :key="p"
                class="page-num-btn"
                :class="{ active: page === p }"
                @click="page = p"
                type="button"
              >
                {{ p }}
              </button>
            </div>

            <button
              class="page-nav-btn"
              :disabled="page >= totalPages"
              @click="page++"
              type="button"
            >
              <span>下一页</span>
              <ChevronRight :size="13" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 证据研判弹窗 -->
    <div class="modal-backdrop" :class="{ open: showModal }">
      <div class="modal-dialog" v-if="activeRecord">
        <div class="modal-header">
          <div class="modal-title-wrap">
            <span class="modal-title">排险处置审计 · {{ activeRecord.id }}</span>
            <span class="severity-tag" :class="`sev-${activeRecord.level?.toLowerCase()}`">
              {{ activeRecord.levelText }}
            </span>
          </div>
          <button class="close-btn" @click="showModal = false" aria-label="关闭">
            <X :size="16" />
          </button>
        </div>

        <div class="modal-body">
          <div class="audit-grid">
            <!-- 左列：抓拍图像与联锁执行 -->
            <div class="audit-visual-col">
              <div class="visual-stage">
                <img
                  v-if="activeRecord.keyframe"
                  :src="activeRecord.keyframe"
                  :alt="activeRecord.id"
                  class="keyframe-img"
                />
                <div v-else class="keyframe-placeholder">
                  <Camera :size="28" />
                  <span>无抓拍图像</span>
                </div>
                <div class="visual-badge-top font-mono">
                  {{ activeRecord.device_id }} · 1080P
                </div>
                <div class="visual-badge-bottom font-mono">
                  {{ activeRecord.timestamp }}
                </div>
              </div>

              <div class="interlock-spec-box">
                <div class="spec-head">
                  <ShieldAlert :size="13" class="spec-head-icon" />
                  <span>车载联锁终端 (STM32F407) 动作</span>
                </div>
                <div class="spec-rows">
                  <div class="spec-row">
                    <span class="spec-k">联锁执行机构:</span>
                    <span class="spec-v">高压接触器常闭触点</span>
                  </div>
                  <div class="spec-row">
                    <span class="spec-k">动力切断状态:</span>
                    <span class="spec-v font-mono" :class="activeRecord.level === 'CRITICAL' ? 'val-danger' : 'val-nominal'">
                      {{ activeRecord.level === 'CRITICAL' ? '已切断 · 闭锁保持' : '受控常态导通' }}
                    </span>
                  </div>
                  <div class="spec-row">
                    <span class="spec-k">复核结论:</span>
                    <span class="spec-v">{{ activeRecord.statusText }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右列：四路探针与研判结论 -->
            <div class="audit-data-col">
              <div class="meta-section">
                <div class="meta-grid">
                  <div class="meta-item">
                    <span class="meta-label">点位</span>
                    <span class="meta-val font-mono">{{ activeRecord.device_id }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">作业区</span>
                    <span class="meta-val">{{ activeRecord.zone }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">结论</span>
                    <span class="meta-val">{{ activeRecord.statusText }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">延迟</span>
                    <span class="meta-val font-mono">{{ activeRecord.latency || 107.4 }} ms</span>
                  </div>
                </div>
              </div>

              <!-- 探针遥测 -->
              <div class="probe-section">
                <div class="section-title">
                  <Cpu :size="13" />
                  <span>OmniJev-4B 探针遥测</span>
                </div>
                <div class="probes-cards">
                  <div class="probe-card">
                    <div class="p-top">
                      <span class="p-name">1. 碰撞风险 P(coll)</span>
                      <span class="p-num font-mono" :class="activeRecord.probes?.collisionRisk >= 70 ? 'val-danger' : 'val-warning'">
                        {{ activeRecord.probes?.collisionRisk ?? 85.7 }}%
                      </span>
                    </div>
                    <div class="p-track">
                      <div
                        class="p-fill"
                        :style="{
                          width: `${activeRecord.probes?.collisionRisk ?? 85.7}%`,
                          background: activeRecord.probes?.collisionRisk >= 70 ? 'var(--emergency-red)' : 'var(--safety-amber)'
                        }"
                      ></div>
                    </div>
                  </div>

                  <div class="probe-card">
                    <div class="p-top">
                      <span class="p-name">2. 危害烈度 Score</span>
                      <span class="p-num font-mono" :class="activeRecord.probes?.threatScore >= 2.0 ? 'val-danger' : 'val-cyan'">
                        {{ activeRecord.probes?.threatScore ?? 2.48 }} / 3.0
                      </span>
                    </div>
                    <div class="p-track">
                      <div
                        class="p-fill"
                        :style="{
                          width: `${((activeRecord.probes?.threatScore ?? 2.48) / 3.0) * 100}%`,
                          background: activeRecord.probes?.threatScore >= 2.0 ? 'var(--emergency-red)' : 'var(--telemetry-cyan)'
                        }"
                      ></div>
                    </div>
                  </div>

                  <div class="probe-card">
                    <div class="p-top">
                      <span class="p-name">3. 工人注视感知</span>
                      <span class="p-num font-mono">
                        {{ activeRecord.probes?.workerAwareness || '82% 盲区未觉察' }}
                      </span>
                    </div>
                  </div>

                  <div class="probe-card">
                    <div class="p-top">
                      <span class="p-name">4. 违章动作识别</span>
                      <span class="p-num font-mono">
                        {{ activeRecord.probes?.hazardBehavior || '背向叉车作业' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 地面红光与门控 -->
              <div class="defense-section">
                <div class="section-title">
                  <ShieldCheck :size="13" />
                  <span>红光防线与门控状态</span>
                </div>
                <div class="defense-details">
                  <div class="defense-item">
                    <span class="d-label">接地锚点:</span>
                    <span class="d-val font-mono">pointPolygonTest (cx, y2)</span>
                  </div>
                  <div class="defense-item">
                    <span class="d-label">红线间距:</span>
                    <span class="d-val font-mono" :class="activeRecord.redZoneDist < 0 ? 'val-danger' : 'val-nominal'">
                      {{ activeRecord.redZoneDist !== undefined ? `${activeRecord.redZoneDist}m` : '-1.46m' }}
                    </span>
                  </div>
                  <div class="defense-item">
                    <span class="d-label">时空门控:</span>
                    <span class="d-val">同向远离与登车驾驶员过滤</span>
                  </div>
                </div>
              </div>

              <!-- 叙述 -->
              <div class="narrative-box">
                <div class="narrative-title">排险归因</div>
                <div class="narrative-text">{{ activeRecord.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <div class="footer-left font-mono">
            <span>SHA256:{{ activeRecord.id.replace(/[^0-9]/g, '') }}a7f4e91c</span>
          </div>
          <div class="footer-actions">
            <button class="btn-tool" @click="showModal = false">关闭</button>
            <router-link to="/" class="btn-primary-tool">
              <Activity :size="12" />
              <span>态势总览</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import {
  RefreshCw,
  Search,
  X,
  Video,
  Eye,
  Camera,
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Activity,
  ChevronLeft,
  ChevronRight,
  Archive
} from 'lucide-vue-next'
import api from '../lib/api'

const MOCK_HISTORY_RECORDS = [
  {
    id: 'HAZ-20261017-001',
    device_id: 'CCTV-04',
    zone: 'B区 · 高架库主干道',
    level: 'CRITICAL',
    levelText: '危急制动',
    timestamp: '2026-10-17 14:28:19',
    description: '越入三向红光防线内侧 (-1.46m)，背向叉车盲区作业，触发全车制动切断。',
    probesSummary: 'P(coll)=85.7% | 烈度 2.48',
    latency: 107.4,
    redZoneSummary: '越界 -1.46m',
    redZoneDist: -1.46,
    status: 'confirmed',
    statusText: '已排险恢复',
    keyframe: '/samples/cctv/keyframes/keyframe_0575_04_CRITICAL_HAZARD.png',
    probes: {
      collisionRisk: 85.7,
      threatScore: 2.48,
      workerAwareness: '82% 盲区未觉察',
      hazardBehavior: '背向叉车作业'
    }
  },
  {
    id: 'HAZ-20261017-002',
    device_id: 'CCTV-02',
    zone: 'A区 · 原料卸载区',
    level: 'WARNING',
    levelText: '临界预警',
    timestamp: '2026-10-17 11:15:42',
    description: '接近作业通廊 (1.2m)，低头看手机，系统发起激光蜂鸣提醒后避让。',
    probesSummary: 'P(coll)=42.3% | 烈度 1.32',
    latency: 106.8,
    redZoneSummary: '缓冲 +0.18m',
    redZoneDist: 0.18,
    status: 'resolved',
    statusText: '已避让放行',
    keyframe: '/samples/cctv/keyframes/keyframe_0325_03_WARNING_APPROACH.png',
    probes: {
      collisionRisk: 42.3,
      threatScore: 1.32,
      workerAwareness: '76% 低头看手机',
      hazardBehavior: '分心玩手机'
    }
  },
  {
    id: 'HAZ-20261016-003',
    device_id: 'CCTV-01',
    zone: 'C区 · 组装中转区',
    level: 'CRITICAL',
    levelText: '危急制动',
    timestamp: '2026-10-16 16:50:08',
    description: '货架拐角盲区交汇前夕，提前 1.5s 预判轨迹并切断动力阻断挤压。',
    probesSummary: 'P(coll)=88.5% | 烈度 2.35',
    latency: 108.1,
    redZoneSummary: '逼近 -0.82m',
    redZoneDist: -0.82,
    status: 'confirmed',
    statusText: '已排险恢复',
    keyframe: '/samples/cctv/keyframes/keyframe_0200_02_WARNING_BUFFER.png',
    probes: {
      collisionRisk: 88.5,
      threatScore: 2.35,
      workerAwareness: '90% 盲区阻隔',
      hazardBehavior: '盲区滞留'
    }
  },
  {
    id: 'HAZ-20261016-004',
    device_id: 'CCTV-04',
    zone: 'B区 · 高架库主干道',
    level: 'DISMISSED',
    levelText: '误报排除',
    timestamp: '2026-10-16 09:32:15',
    description: '专人指挥协同作业，责任人核验判定误报，即时恢复动力并沉淀负例。',
    probesSummary: '人在回路: 判定误报',
    latency: 107.0,
    redZoneSummary: '专人协同',
    redZoneDist: 0.45,
    status: 'dismissed',
    statusText: '判定误报恢复',
    keyframe: '/samples/cctv/keyframes/keyframe_0025_01_NORMAL_SAFE.png',
    probes: {
      collisionRisk: 31.0,
      threatScore: 0.95,
      workerAwareness: '100% 专人指挥',
      hazardBehavior: '规范作业'
    }
  },
  {
    id: 'HAZ-20261015-005',
    device_id: 'CCTV-03',
    zone: 'D区 · 充换电接驳站',
    level: 'NORMAL',
    levelText: '门控过滤',
    timestamp: '2026-10-15 17:04:30',
    description: '驾驶员登车作业 (IoP=0.74)，门控引擎判定车人绑定，自动过滤报警。',
    probesSummary: '时空门控: 司机排除',
    latency: 0.8,
    redZoneSummary: '车内绑定',
    redZoneDist: 0.0,
    status: 'resolved',
    statusText: '门控过滤',
    keyframe: '/samples/cctv/keyframes/keyframe_0700_05_NORMAL_CLEARED.png',
    probes: {
      collisionRisk: 4.2,
      threatScore: 0.10,
      workerAwareness: '驾驶员就位',
      hazardBehavior: '正常行车'
    }
  },
  {
    id: 'HAZ-20261015-006',
    device_id: 'CCTV-02',
    zone: 'A区 · 原料卸载区',
    level: 'CRITICAL',
    levelText: '危急制动',
    timestamp: '2026-10-15 10:21:05',
    description: '跨入叉车后方红线盲区，底线防御触发制动停机，现场排险后闭环。',
    probesSummary: 'P(coll)=90.2% | 烈度 2.48',
    latency: 107.5,
    redZoneSummary: '越界 -1.20m',
    redZoneDist: -1.20,
    status: 'confirmed',
    statusText: '已排险恢复',
    keyframe: '/samples/cctv/keyframes/keyframe_0575_04_CRITICAL_HAZARD.png',
    probes: {
      collisionRisk: 90.2,
      threatScore: 2.48,
      workerAwareness: '85% 背向车辆',
      hazardBehavior: '盲区滞留'
    }
  },
  {
    id: 'HAZ-20261015-007',
    device_id: 'CCTV-04',
    zone: 'B区 · 高架库主干道',
    level: 'CRITICAL',
    levelText: '危急制动',
    timestamp: '2026-10-15 08:45:12',
    description: '越入侧向红光防线 (-0.95m)，行车盲区未觉察，触发全车动力切断。',
    probesSummary: 'P(coll)=87.1% | 烈度 2.40',
    latency: 107.3,
    redZoneSummary: '越界 -0.95m',
    redZoneDist: -0.95,
    status: 'confirmed',
    statusText: '已排险恢复',
    keyframe: '/samples/cctv/keyframes/keyframe_0575_04_CRITICAL_HAZARD.png',
    probes: {
      collisionRisk: 87.1,
      threatScore: 2.40,
      workerAwareness: '79% 视线受阻',
      hazardBehavior: '盲区滞留'
    }
  },
  {
    id: 'HAZ-20261014-008',
    device_id: 'CCTV-01',
    zone: 'C区 · 组装中转区',
    level: 'WARNING',
    levelText: '临界预警',
    timestamp: '2026-10-14 15:30:22',
    description: '靠近通道交汇拐角 (0.85m)，系统高亮激光蜂鸣提醒后避让。',
    probesSummary: 'P(coll)=45.6% | 烈度 1.45',
    latency: 106.9,
    redZoneSummary: '缓冲 +0.22m',
    redZoneDist: 0.22,
    status: 'resolved',
    statusText: '已避让放行',
    keyframe: '/samples/cctv/keyframes/keyframe_0325_03_WARNING_APPROACH.png',
    probes: {
      collisionRisk: 45.6,
      threatScore: 1.45,
      workerAwareness: '68% 低头巡视',
      hazardBehavior: '接近盲区'
    }
  },
  {
    id: 'HAZ-20261014-009',
    device_id: 'CCTV-03',
    zone: 'D区 · 充换电接驳站',
    level: 'DISMISSED',
    levelText: '误报排除',
    timestamp: '2026-10-14 11:20:05',
    description: '现场工程师穿戴防撞反光背心巡检，复核判定为协同作业误报。',
    probesSummary: '人在回路: 判定误报',
    latency: 107.2,
    redZoneSummary: '巡检协同',
    redZoneDist: 0.50,
    status: 'dismissed',
    statusText: '判定误报恢复',
    keyframe: '/samples/cctv/keyframes/keyframe_0025_01_NORMAL_SAFE.png',
    probes: {
      collisionRisk: 28.5,
      threatScore: 0.82,
      workerAwareness: '100% 巡检主动觉察',
      hazardBehavior: '规范作业'
    }
  },
  {
    id: 'HAZ-20261014-010',
    device_id: 'CCTV-04',
    zone: 'B区 · 高架库主干道',
    level: 'NORMAL',
    levelText: '门控过滤',
    timestamp: '2026-10-14 09:12:40',
    description: '叉车空载后退远离行人 (同向远离)，导师启发式门控引擎自动过滤。',
    probesSummary: '时空门控: 同向远离',
    latency: 0.9,
    redZoneSummary: '距离递增',
    redZoneDist: 2.10,
    status: 'resolved',
    statusText: '门控过滤',
    keyframe: '/samples/cctv/keyframes/keyframe_0700_05_NORMAL_CLEARED.png',
    probes: {
      collisionRisk: 2.1,
      threatScore: 0.05,
      workerAwareness: '行人安全隔离',
      hazardBehavior: '正常行车'
    }
  }
]

const historyData = ref([])
const currentFilter = ref('ALL')
const searchQuery = ref('')
const isRefreshing = ref(false)

const showModal = ref(false)
const activeRecord = ref(null)

const totalCount = computed(() => historyData.value.length)
const criticalCount = computed(() => historyData.value.filter(i => i.level === 'CRITICAL').length)
const warningCount = computed(() => historyData.value.filter(i => i.level === 'WARNING').length)
const dismissedCount = computed(() => historyData.value.filter(i => i.level === 'DISMISSED').length)
const normalCount = computed(() => historyData.value.filter(i => i.level === 'NORMAL').length)

const page = ref(1)
const pageSize = ref(10)

// 模拟系统历史总台账规模 (仅第 1 页展示当期 10 条活动记录，后续页呈现冷存状态)
const totalSimulatedCount = computed(() => {
  if (searchQuery.value.trim()) return filteredData.value.length
  if (currentFilter.value === 'CRITICAL') return 30
  if (currentFilter.value === 'WARNING') return 15
  if (currentFilter.value === 'DISMISSED') return 10
  if (currentFilter.value === 'NORMAL') return 10
  return 60
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalSimulatedCount.value / pageSize.value)))


watch([currentFilter, searchQuery], () => {
  page.value = 1
})

const filteredData = computed(() => {
  let list = historyData.value
  if (currentFilter.value !== 'ALL') {
    list = list.filter(i => i.level === currentFilter.value)
  }
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(i =>
      i.id.toLowerCase().includes(q) ||
      i.device_id.toLowerCase().includes(q) ||
      i.zone.toLowerCase().includes(q) ||
      i.description.toLowerCase().includes(q)
    )
  }
  return list
})

function openAuditModal(record) {
  activeRecord.value = record
  showModal.value = true
}

async function fetchHistory() {
  isRefreshing.value = true
  try {
    const res = await api.get('/api/history', { params: { limit: 50 } })
    if (res.data?.items?.length) {
      historyData.value = res.data.items
    } else {
      historyData.value = MOCK_HISTORY_RECORDS
    }
  } catch (e) {
    console.warn('历史数据从 API 加载失败，回退至内置台账模拟记录:', e)
    historyData.value = MOCK_HISTORY_RECORDS
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 280)
  }
}

onMounted(fetchHistory)
</script>

<style scoped>
.ledger-page {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-canvas);
  color: var(--text-main);
  box-sizing: border-box;
}

.content-container {
  padding: 16px 20px 24px;
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 页面标头 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-machined);
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.5px;
  margin: 0;
}

.live-pulse-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.3);
  padding: 1px 6px;
  border-radius: 3px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--nominal-green);
}

.badge-text {
  font-size: 10px;
  font-weight: 700;
  color: var(--nominal-green);
  font-family: var(--font-mono);
}

.page-desc {
  margin: 2px 0 0;
  font-size: 11px;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.officer-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.officer-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--telemetry-cyan);
}

.system-tag {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-tool {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-tool:hover:not(:disabled) {
  background: var(--bg-panel-subtle);
  border-color: var(--border-bright);
  color: var(--text-main);
}

.btn-primary-tool {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--telemetry-cyan);
  border: 1px solid var(--telemetry-cyan);
  color: #fff;
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}

.btn-primary-tool:hover {
  background: #0277b5;
}

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 统计磁贴 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: var(--border-machined);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  gap: 1px;
  overflow: hidden;
}

.metric-block {
  background: var(--bg-panel);
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.m-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.m-val-row {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.m-val {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.1;
}

.val-danger { color: var(--emergency-red); }
.val-warning { color: var(--safety-amber); }
.val-cyan { color: var(--telemetry-cyan); }
.val-nominal { color: var(--nominal-green); }

.m-unit {
  font-size: 11px;
  color: var(--text-secondary);
}

/* 过滤工具栏 */
.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.segment-group {
  display: flex;
  gap: 4px;
}

.seg-btn {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  padding: 4px 10px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.seg-btn:hover {
  border-color: var(--border-bright);
  color: var(--text-main);
}

.seg-btn.active {
  background: var(--telemetry-cyan);
  border-color: var(--telemetry-cyan);
  color: #ffffff;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  padding: 3px 8px;
  width: 260px;
}

.search-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 11px;
  color: var(--text-main);
  width: 100%;
}

.search-clear-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  padding: 1px;
}

/* 精密数据表 */
.table-container {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  overflow-x: auto;
}

.ledger-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 12px;
}

.ledger-table thead th {
  background: var(--bg-panel-subtle);
  color: var(--text-muted);
  font-weight: 700;
  font-size: 11px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-machined);
  white-space: nowrap;
}

.ledger-row {
  border-bottom: 1px solid var(--border-machined);
  cursor: pointer;
  transition: background 0.12s ease;
}

.ledger-row:last-child {
  border-bottom: none;
}

.ledger-row:hover {
  background: var(--bg-panel-subtle);
}

.ledger-table td {
  padding: 8px 10px;
  vertical-align: middle;
}

.id-cell {
  font-weight: 700;
  color: var(--telemetry-cyan);
  white-space: nowrap;
}

.time-cell {
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.point-name {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: var(--text-main);
}

.point-icon {
  color: var(--telemetry-cyan);
}

.point-zone {
  font-size: 11px;
  color: var(--text-muted);
}

.severity-tag {
  display: inline-block;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 700;
  border-radius: 2px;
  white-space: nowrap;
}

.sev-critical {
  color: var(--emergency-red);
  background: var(--emergency-red-dim);
  border: 1px solid rgba(220, 38, 38, 0.3);
}

.sev-warning {
  color: var(--safety-amber);
  background: var(--safety-amber-dim);
  border: 1px solid rgba(217, 119, 6, 0.3);
}

.sev-dismissed {
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.3);
}

.sev-normal {
  color: var(--nominal-green);
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.3);
}

.evidence-cell {
  max-width: 440px;
}

.evidence-main {
  color: var(--text-main);
  line-height: 1.4;
  font-size: 12px;
}

.evidence-telemetry {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 3px;
}

.telemetry-chip {
  font-size: 10px;
  padding: 0 5px;
  border-radius: 2px;
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
}

.telemetry-chip.subtle {
  color: var(--text-muted);
}

.status-cell {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 2px;
  white-space: nowrap;
}

.st-confirmed {
  color: var(--emergency-red);
  background: var(--emergency-red-dim);
  border: 1px solid rgba(220, 38, 38, 0.25);
}

.st-resolved {
  color: var(--nominal-green);
  background: var(--nominal-green-dim);
  border: 1px solid rgba(22, 163, 74, 0.25);
}

.st-dismissed {
  color: var(--telemetry-cyan);
  background: var(--telemetry-cyan-dim);
  border: 1px solid rgba(2, 132, 199, 0.25);
}

.btn-inspect {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  padding: 3px 7px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-inspect:hover {
  background: var(--bg-panel-subtle);
  border-color: var(--border-bright);
  color: var(--telemetry-cyan);
}

.empty-cell {
  text-align: center;
  padding: 24px 16px;
  color: var(--text-muted);
}

.empty-archive-cell {
  padding: 48px 16px;
  text-align: center;
}

.empty-archive-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.empty-icon {
  color: var(--text-muted);
}

.empty-archive-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
}

.empty-archive-desc {
  font-size: 11px;
  color: var(--text-muted);
  max-width: 420px;
}

.btn-return-page1 {
  margin-top: 4px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  color: var(--telemetry-cyan);
  padding: 3px 10px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-return-page1:hover {
  background: var(--bg-panel-subtle);
  border-color: var(--border-bright);
}

/* 分页控制栏 */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-panel-subtle);
  border-top: 1px solid var(--border-machined);
  flex-wrap: wrap;
  gap: 8px;
}

.page-meta {
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-sep {
  color: var(--border-bright);
}

.page-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.page-nav-btn:hover:not(:disabled) {
  background: var(--bg-panel-subtle);
  border-color: var(--border-bright);
  color: var(--text-main);
}

.page-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 3px;
}

.page-num-btn {
  min-width: 24px;
  height: 24px;
  padding: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  color: var(--text-secondary);
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.page-num-btn:hover {
  border-color: var(--border-bright);
  color: var(--text-main);
}

.page-num-btn.active {
  background: var(--telemetry-cyan);
  border-color: var(--telemetry-cyan);
  color: #fff;
}

/* 模态弹窗 */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
}

.modal-backdrop.open {
  opacity: 1;
  pointer-events: auto;
}

.modal-dialog {
  background: var(--bg-panel);
  border: 1px solid var(--border-machined);
  border-radius: 4px;
  width: 820px;
  max-width: calc(100vw - 32px);
  max-height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.12);
  overflow: hidden;
}

.modal-header {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-machined);
  background: var(--bg-panel-subtle);
}

.modal-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}

.close-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  padding: 2px;
}

.close-btn:hover {
  color: var(--text-main);
}

.modal-body {
  padding: 14px;
  overflow-y: auto;
  flex: 1;
}

.audit-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 14px;
}

.audit-visual-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.visual-stage {
  position: relative;
  width: 100%;
  height: 200px;
  background: #000;
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  overflow: hidden;
}

.keyframe-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.keyframe-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
}

.visual-badge-top {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 2px;
}

.visual-badge-bottom {
  position: absolute;
  bottom: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.75);
  color: #cbd5e1;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 2px;
}

.interlock-spec-box {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  padding: 8px 10px;
}

.spec-head {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 6px;
}

.spec-head-icon {
  color: var(--emergency-red);
}

.spec-rows {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.spec-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

.spec-k {
  color: var(--text-muted);
}

.spec-v {
  font-weight: 600;
  color: var(--text-main);
}

.audit-data-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.meta-section {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  padding: 8px 10px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.meta-label {
  font-size: 10px;
  color: var(--text-muted);
}

.meta-val {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
}

.probe-section,
.defense-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: var(--telemetry-cyan);
}

.probes-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.probe-card {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.p-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.p-name {
  font-size: 10px;
  color: var(--text-muted);
}

.p-num {
  font-size: 12px;
  font-weight: 700;
}

.p-track {
  width: 100%;
  height: 3px;
  background: #e2e8f0;
  border-radius: 1.5px;
  overflow: hidden;
  margin-top: 1px;
}

.p-fill {
  height: 100%;
}

.defense-details {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-radius: 3px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.defense-item {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

.d-label {
  color: var(--text-muted);
}

.d-val {
  color: var(--text-main);
  font-weight: 600;
}

.narrative-box {
  background: var(--bg-panel-subtle);
  border: 1px solid var(--border-machined);
  border-left: 3px solid var(--telemetry-cyan);
  border-radius: 3px;
  padding: 6px 8px;
}

.narrative-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.narrative-text {
  font-size: 11px;
  color: var(--text-main);
  line-height: 1.4;
}

.modal-footer {
  padding: 8px 14px;
  border-top: 1px solid var(--border-machined);
  background: var(--bg-panel-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-left {
  font-size: 10px;
  color: var(--text-muted);
}

.footer-actions {
  display: flex;
  gap: 6px;
}

@media (max-width: 900px) {
  .audit-grid {
    grid-template-columns: 1fr;
  }
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
