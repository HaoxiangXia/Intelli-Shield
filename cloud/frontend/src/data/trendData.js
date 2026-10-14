// 趋势分析演示数据集 (MOCK)
// ─────────────────────────────────────────────────────────────────────────────
// ⚠️ 以下数值为答辩演示用的模拟数据, 非生产环境实测结果。
//    上线前 (2026-03 之前) 模拟"纯人工巡检 + 事后追溯"模式:
//      依赖巡检员目视, 漏检多、误报多、无连续时序。
//    上线后 模拟"红光禁区 + YOLO 感知 + OneJev 认知探针"三层仲裁:
//      时空门控抑制司机误报, 红光越阈硬约束压降漏检, 险情总量与误报率同步下降。
//
// 数据粒度: 2025-10 ~ 2026-09 共 12 个自然月; 季度由月度聚合推导, 保证口径一致。
// 字段: total 险情上报总数 / real 经复核属实的真实险情 / false 误报 (total - real)

export const DEPLOY_MONTH = '2026-03'

const MONTHLY = [
  { month: '2025-10', total: 142, real: 41 },
  { month: '2025-11', total: 158, real: 46 },
  { month: '2025-12', total: 137, real: 39 },
  { month: '2026-01', total: 151, real: 44 },
  { month: '2026-02', total: 129, real: 37 },
  { month: '2026-03', total: 78, real: 36 },
  { month: '2026-04', total: 61, real: 31 },
  { month: '2026-05', total: 50, real: 28 },
  { month: '2026-06', total: 42, real: 25 },
  { month: '2026-07', total: 36, real: 22 },
  { month: '2026-08', total: 31, real: 20 },
  { month: '2026-09', total: 27, real: 18 }
]

function withFalseRate(row) {
  const falseCount = row.total - row.real
  return {
    ...row,
    false: falseCount,
    falseRate: +((falseCount / row.total) * 100).toFixed(1)
  }
}

function mean(list, key) {
  if (!list.length) return 0
  return +(list.reduce((sum, r) => sum + r[key], 0) / list.length).toFixed(1)
}

// 月度序列 (误报数与误报率在此推导)
export const monthlyRows = MONTHLY.map(withFalseRate)

function quarterOf(month) {
  const [y, m] = month.split('-')
  return `${y}Q${Math.ceil(Number(m) / 3)}`
}

function aggregate(rows) {
  const total = rows.reduce((s, r) => s + r.total, 0)
  const real = rows.reduce((s, r) => s + r.real, 0)
  const falseCount = total - real
  return {
    total,
    real,
    false: falseCount,
    falseRate: +((falseCount / total) * 100).toFixed(1),
    months: rows.length,
    avgMonthly: +(total / rows.length).toFixed(1)
  }
}

// 季度序列 (由月度聚合, 不单独手写, 避免口径漂移)
export const quarterlyRows = (() => {
  const buckets = new Map()
  for (const row of monthlyRows) {
    const key = quarterOf(row.month)
    if (!buckets.has(key)) buckets.set(key, [])
    buckets.get(key).push(row)
  }
  return [...buckets.entries()].map(([quarter, rows]) => ({
    quarter,
    ...aggregate(rows)
  }))
})()

const deployIndex = monthlyRows.findIndex(r => r.month === DEPLOY_MONTH)

export const preRows = monthlyRows.slice(0, deployIndex)
export const postRows = monthlyRows.slice(deployIndex)

// 部署前后对比指标
export const summary = {
  deployMonth: DEPLOY_MONTH,
  preAvgTotal: mean(preRows, 'total'),
  postAvgTotal: mean(postRows, 'total'),
  preAvgReal: mean(preRows, 'real'),
  postAvgReal: mean(postRows, 'real'),
  preAvgFalseRate: mean(preRows, 'falseRate'),
  postAvgFalseRate: mean(postRows, 'falseRate')
}

summary.totalDropPct = +(
  ((summary.preAvgTotal - summary.postAvgTotal) / summary.preAvgTotal) * 100
).toFixed(1)

summary.falseRateDropPp = +(summary.preAvgFalseRate - summary.postAvgFalseRate).toFixed(1)

// 真实险情 (人工复核确认) 同步下降 37.9%, 说明下降不只是"把噪音过滤掉",
// 提前预警 + 声光阻断确实拦下了实际险情, 而非以漏检换取低报警量。
summary.realDropPct = +(
  ((summary.preAvgReal - summary.postAvgReal) / summary.preAvgReal) * 100
).toFixed(1)

// 每一起真实险情伴随的误报笔数: 上线前 2.46 笔, 上线后 0.81 笔。
// 该比值下降是"信噪比改善"最直观的单一指标。
summary.falsePerReal = {
  pre: +((summary.preAvgTotal - summary.preAvgReal) / summary.preAvgReal).toFixed(2),
  post: +((summary.postAvgTotal - summary.postAvgReal) / summary.postAvgReal).toFixed(2)
}