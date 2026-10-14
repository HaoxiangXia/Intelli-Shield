import { ref, shallowRef } from 'vue'

// 752 帧 HPC 元数据约 4.1 MB, 全局单例保证只发起一次请求/解析。
// 使用 shallowRef: 帧数组按引用传递, 无需深层响应式代理。
const frames = shallowRef([])
const status = ref('idle') // idle | loading | ready | error

let inflight = null

async function load() {
  if (status.value === 'ready') return frames.value
  if (inflight) return inflight

  status.value = 'loading'
  inflight = (async () => {
    try {
      const res = await fetch('/samples/cctv/benchmarks/cctv_frames_metadata.json')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      frames.value = data.frames || []
      status.value = 'ready'
      return frames.value
    } catch (err) {
      status.value = 'error'
      console.error('[Intelli-Shield] 载入算法元数据失败:', err)
      return []
    } finally {
      inflight = null
    }
  })()

  return inflight
}

export function useCctvMetadata() {
  return { frames, status, load }
}
