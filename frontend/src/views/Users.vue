<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div class="page-title">用户管理</div>
      <div class="toolbar-right">
        <el-button type="primary" @click="openDlg()">新增用户</el-button>
      </div>
    </div>
    <el-table :data="paged" border stripe v-loading="loading">
      <el-table-column prop="username" label="用户名" width="160" />
      <el-table-column prop="real_name" label="姓名" width="160" />
      <el-table-column prop="created_at" label="创建时间" min-width="170" />
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

    <el-dialog v-model="dlg" :title="editRow ? '编辑用户' : '新增用户'" width="440px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!editRow" />
        </el-form-item>
        <el-form-item :label="editRow ? '新密码' : '密码'" :required="!editRow">
          <el-input v-model="form.password" type="password" show-password
            :placeholder="editRow ? '留空则不修改密码' : ''" />
        </el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.real_name" /></el-form-item>
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
const form = reactive({ username: '', password: '', real_name: '' })

async function load() {
  loading.value = true
  try { rows.value = await api.get('/users'); resetPage() } finally { loading.value = false }
}
onMounted(load)

function openDlg(row = null) {
  editRow.value = row
  form.username = row?.username || ''
  form.password = ''
  form.real_name = row?.real_name || ''
  dlg.value = true
}
async function submit() {
  if (!editRow.value && (!form.username || !form.password)) return ElMessage.warning('请填写用户名和密码')
  if (editRow.value) await api.put(`/users/${editRow.value.id}`, form)
  else await api.post('/users', form)
  ElMessage.success('已保存')
  dlg.value = false
  load()
}
async function del(row) {
  await api.delete(`/users/${row.id}`)
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
