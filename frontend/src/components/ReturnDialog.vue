<template>
  <el-dialog :model-value="modelValue" title="退料单" width="960px" destroy-on-close
    @update:model-value="$emit('update:modelValue', $event)" @open="reset">
    <el-alert type="warning" :closable="false" style="margin-bottom:12px"
      title="为什么先选出库单？退料是针对某一张出库单退的：先找到当时领料的那张出库单，系统会列出这张单领了哪些物料、各剩多少可退，你只填回退数量，退回的物料才能准确记回对应工单的账上。" />
    <el-form label-width="90px">
      <el-form-item label="出库单" required>
        <el-select v-model="orderNo" filterable remote :remote-method="searchIssues"
          :loading="searching" placeholder="输入出库单号/物料名称/编号/领料人搜索" style="width:100%"
          @change="onPicked">
          <el-option v-for="i in issueOptions" :key="i.order_no"
            :label="`${i.order_no}（${i.issue_date}，领料人 ${i.issuer || '-'}）`" :value="i.order_no" />
        </el-select>
      </el-form-item>
      <el-form-item label="回退日期" required>
        <el-date-picker v-model="returnDate" type="date" value-format="YYYY-MM-DD" style="width:300px" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="remark" placeholder="备注" />
      </el-form-item>
    </el-form>

    <template v-if="rows.length">
      <el-alert type="info" :closable="false" style="margin-bottom:10px"
        title="出库数量是锁定的，只能填写回退数量；重新选择出库单会作废当前已填内容" />
      <el-table :data="rows" border size="small">
        <el-table-column prop="material_code" label="物料编号" />
        <el-table-column prop="material_name" label="物料名称" />
        <el-table-column prop="spec" label="规格" />
        <el-table-column prop="qty" label="出库数量（锁定）" align="right" />
        <el-table-column prop="returned" label="已退数量" align="right" />
        <el-table-column label="本次回退数量">
          <template #default="{ row }">
            <el-input-number v-model="row.return_qty" :min="0" :max="row.returnable" style="width:100%" />
          </template>
        </el-table-column>
        <el-table-column label="备注">
          <template #default="{ row }">
            <el-input v-model="row.remark" placeholder="备注" />
          </template>
        </el-table-column>
      </el-table>
    </template>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" :disabled="!orderNo" @click="submit">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { ref, watch } from 'vue'
import api from '../api'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'done'])

const searching = ref(false)
const submitting = ref(false)
const orderNo = ref('')
const returnDate = ref('')
const remark = ref('')
const issueOptions = ref([])
const rows = ref([])

watch(() => props.modelValue, (v) => { if (v) reset() })

function reset() {
  orderNo.value = ''
  returnDate.value = new Date().toISOString().slice(0, 10)
  remark.value = ''
  issueOptions.value = []
  rows.value = []
}
async function searchIssues(q) {
  if (!q) return
  searching.value = true
  try { issueOptions.value = await api.get('/issues', { params: { keyword: q } }) }
  finally { searching.value = false }
}
async function onPicked(no) {
  // 重新选择出库单：之前填的内容全部作废
  const d = await api.get(`/issues/${no}/detail-for-return`)
  rows.value = d.items.map(it => ({ ...it, return_qty: 0, remark: '' }))
  // FQ 开头的单（非工单申领虚拟单）自动填备注
  remark.value = no.startsWith('FQ') ? '非工单申领' : ''
}
async function submit() {
  const items = rows.value.filter(r => r.return_qty > 0)
    .map(r => ({ issue_item_id: r.issue_item_id, qty: r.return_qty, remark: r.remark || '' }))
  if (!items.length) return ElMessage.warning('请至少填写一行回退数量')
  submitting.value = true
  try {
    const r = await api.post('/returns', { issue_order_no: orderNo.value, return_date: returnDate.value, remark: remark.value, items })
    ElMessage.success(`退回成功，单号 ${r.return_no}`)
    emit('update:modelValue', false)
    emit('done')
  } finally { submitting.value = false }
}
</script>
