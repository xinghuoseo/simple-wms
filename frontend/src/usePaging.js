// 表格客户端分页：usePaging(rows) -> { page, pageSize, paged, total }
import { computed, ref } from 'vue'

export function usePaging(rows) {
  const page = ref(1)
  const pageSize = ref(25)
  const total = computed(() => rows.value.length)
  const paged = computed(() => {
    const s = (page.value - 1) * pageSize.value
    return rows.value.slice(s, s + pageSize.value)
  })
  function resetPage() { page.value = 1 }
  return { page, pageSize, paged, total, resetPage }
}
