<template>
  <el-dialog :model-value="modelValue" title="出库单" width="960px" destroy-on-close
    @update:model-value="$emit('update:modelValue', $event)">
    <el-form label-width="90px">
      <el-form-item label="领料人" required>
        <div class="row-line">
          <el-select v-model="form.issuer" filterable allow-create default-first-option
            placeholder="选择或输入领料人" style="width:220px">
            <el-option v-for="u in userOptions" :key="u.id" :label="u.real_name || u.username" :value="u.real_name || u.username" />
          </el-select>
          <span class="sep">日期</span>
          <el-date-picker v-model="form.issue_date" type="date" value-format="YYYY-MM-DD" style="width:170px" />
          <span class="sep">申领类型</span>
          <el-select v-model="form.issue_type" style="width:150px">
            <el-option label="生产申领" value="生产申领" />
            <el-option label="非工单申领" value="非工单申领" />
          </el-select>
        </div>
      </el-form-item>
      <el-form-item label="备注"><el-input v-model="form.remark" style="width:100%" /></el-form-item>
    </el-form>

    <div class="items-head">
      <b>出库明细（可添加多个物料）</b>
      <el-button type="primary" size="small" @click="addItem">添加明细</el-button>
    </div>
    <el-table :data="items" border size="small">
      <el-table-column label="物料" min-width="200">
        <template #default="{ row, $index }">
          <el-select v-model="row.material_id" filterable remote :remote-method="searchMaterials"
            :loading="searching" placeholder="输入物料名称或编号搜索" style="width:100%"
            @change="id => onPicked(id, $index)">
            <el-option v-for="m in options" :key="m.id" :label="`${m.code} - ${m.name}`" :value="m.id" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="编号">
        <template #default="{ row }">{{ row.code }}</template>
      </el-table-column>
      <el-table-column label="规格">
        <template #default="{ row }">{{ row.spec }}</template>
      </el-table-column>
      <el-table-column label="领料数量">
        <template #default="{ row }">
          <el-input-number v-model="row.qty" :min="0.01" style="width:100%" />
        </template>
      </el-table-column>
      <el-table-column label="备注">
        <template #default="{ row }">
          <el-input v-model="row.remark" placeholder="备注" />
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ $index }">
          <el-button link type="danger" @click="items.splice($index, 1)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { reactive, ref, watch } from 'vue'
import api from '../api'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'done'])

const searching = ref(false)
const submitting = ref(false)
const options = ref([])
const items = ref([])
const userOptions = ref([])
const form = reactive({
  issuer: '生产', issue_date: new Date().toISOString().slice(0, 10), remark: '', issue_type: '生产申领',
})

watch(() => props.modelValue, (v) => {
  if (v) {
    form.issuer = '生产'; form.remark = ''; form.issue_type = '生产申领'
    form.issue_date = new Date().toISOString().slice(0, 10); items.value = []
    if (!userOptions.value.length) api.get('/users').then(d => userOptions.value = d.filter(u => u.username !== 'admin'))
  }
})

function addItem() {
  items.value.push({ material_id: null, code: '', spec: '', qty: 1, remark: '' })
}
async function searchMaterials(q) {
  if (!q) return
  searching.value = true
  try { options.value = await api.get('/materials', { params: { keyword: q } }) }
  finally { searching.value = false }
}
function onPicked(id, idx) {
  const m = options.value.find(x => x.id === id)
  if (m && items.value[idx]) { items.value[idx].code = m.code; items.value[idx].spec = m.spec }
}
async function submit() {
  if (!form.issuer) return ElMessage.warning('请填写领料人')
  const valid = items.value.filter(i => i.material_id && i.qty > 0)
  if (!valid.length) return ElMessage.warning('请至少添加一行有效明细')
  submitting.value = true
  try {
    // 非工单申领：备注为空时自动填
    const remark = form.issue_type === '非工单申领' && !form.remark ? '非工单申领' : form.remark
    const r = await api.post('/issues', { ...form, remark, items: valid.map(i => ({ material_id: i.material_id, qty: i.qty, remark: i.remark || '' })) })
    ElMessage.success(`出库单已保存待审核，单号 ${r.order_no}`)
    emit('update:modelValue', false)
    emit('done')
  } finally { submitting.value = false }
}
</script>

<style scoped>
.items-head { display: flex; justify-content: space-between; align-items: center; margin: 14px 0 8px; }
.row-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sep { color: #909399; font-size: 13px; }
</style>
