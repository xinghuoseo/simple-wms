<!-- 表格底部分页条：左侧总条目数，右侧 上一页/下一页/每页条数 -->
<template>
  <div class="table-pager">
    <div class="pager-left">共 {{ total }} 条</div>
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :page-sizes="[25, 50, 100, 200]"
      :total="total"
      layout="prev, pager, next, sizes"
      background
      small
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ page: Number, pageSize: Number, total: Number })
const emit = defineEmits(['update:page', 'update:pageSize'])
const page = computed({
  get: () => props.page,
  set: v => emit('update:page', v),
})
const pageSize = computed({
  get: () => props.pageSize,
  set: v => emit('update:pageSize', v),
})
</script>

<style scoped>
.table-pager { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
.pager-left { color: #606266; font-size: 13px; }
</style>
