<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div class="page-title">供应商</div>
      <div class="toolbar-right">
        <el-button type="primary" @click="openDlg()">新增供应商</el-button>
      </div>
    </div>
    <el-table :data="paged" border stripe v-loading="loading">
      <el-table-column prop="name" label="供应商名称" min-width="160" />
      <el-table-column prop="contact" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="150" />
      <el-table-column prop="remark" label="备注" min-width="140" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDlg(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="del(row)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <TablePager v-model:page="page" v-model:page-size="pageSize" :total="total" />

    <el-dialog v-model="dlg" :title="editRow ? '编辑供应商' : '新增供应商'" width="440px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import api from '../api'
import TablePager from '../components/TablePager.vue'
import { usePaging } from '../usePaging'

const rows = ref([])
const loading = ref(false)
const { page, pageSize, paged, total, resetPage } = usePaging(rows)
const dlg = ref(false)
const editRow = ref(null)
const form = reactive({ name: '', contact: '', phone: '', remark: '' })

async function load() {
  loading.value = true
  try { rows.value = await api.get('/suppliers'); resetPage() } finally { loading.value = false }
}
onMounted(load)

function openDlg(row = null) {
  editRow.value = row
  form.name = row?.name || ''; form.contact = row?.contact || ''
  form.phone = row?.phone || ''; form.remark = row?.remark || ''
  dlg.value = true
}
async function submit() {
  if (!form.name) return ElMessage.warning('请填写名称')
  if (editRow.value) await api.put(`/suppliers/${editRow.value.id}`, form)
  else await api.post('/suppliers', form)
  ElMessage.success('已保存')
  dlg.value = false
  load()
}
async function del(row) {
  await api.delete(`/suppliers/${row.id}`)
  ElMessage.success('已删除')
  load()
}
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; }
.page-title { font-weight: 700; font-size: 16px; color: #1f2937; margin-right: 20px; white-space: nowrap; }
.toolbar-center { flex: 1; display: flex; justify-content: center; gap: 10px; align-items: center; }
.toolbar-right { display: flex; gap: 10px; align-items: center; }
</style>
