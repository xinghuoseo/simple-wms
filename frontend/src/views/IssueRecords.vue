<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div class="page-title">出库记录</div>
      <div class="toolbar-center">
        <el-select
          v-model="keyword"
          filterable remote clearable default-first-option
          :remote-method="onSearch"
          :loading="searching"
          placeholder="搜索单号/物料/领料人"
          style="width:340px"
          @change="onPick"
          @clear="load"
        >
          <el-option v-for="r in options" :key="r.id" :label="r.order_no" :value="r.order_no">
            <div class="opt-row">
              <span class="opt-date">{{ r.issue_date }}</span>
              <span class="opt-no">{{ r.order_no }}</span>
              <span>{{ r.issuer }}</span>
              <span class="opt-remark">{{ r.remark || (r.issue_type || '') }}</span>
            </div>
          </el-option>
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="warning" @click="issueDlg = true">出库单</el-button>
      </div>
    </div>
    <el-table :data="paged" border stripe v-loading="loading" row-key="id">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="padding: 8px 40px">
            <el-table :data="row.items" border size="small">
              <el-table-column prop="material_code" label="物料编号" width="150" />
              <el-table-column prop="material_name" label="物料名称" min-width="120" />
              <el-table-column prop="spec" label="规格" width="110" />
              <el-table-column prop="qty" label="出库数量" width="110" align="right" />
              <el-table-column prop="return_qty" label="已退数量" width="110" align="right" />
              <el-table-column prop="remark" label="备注" min-width="140" />
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="issue_date" label="出库日期" width="110" />
      <el-table-column prop="order_no" label="出库单号" width="160" class-name="nowrap-cell" />
      <el-table-column prop="issuer" label="领料人" width="100" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'approved'" type="success" size="small">已审核</el-tag>
          <el-tag v-else type="warning" size="small">待审核</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="140" class-name="nowrap-cell" />
      <el-table-column label="明细数" width="80" align="center">
        <template #default="{ row }">{{ row.items.length }}</template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button v-if="row.status !== 'approved'" link type="success" @click="approve(row)">审核</el-button>
          <el-button link type="danger" @click="del(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <TablePager v-model:page="page" v-model:page-size="pageSize" :total="total" />

    <!-- 出库单详情 -->
    <el-dialog v-model="detailDlg" :title="`出库单详情 ${detailRow.order_no || ''}`" width="1000px" destroy-on-close>
      <div class="print-area">
        <div class="print-only">出库单详情 {{ detailRow.order_no }}</div>
        <el-descriptions :column="3" border size="small" style="margin-bottom:12px">
          <el-descriptions-item label="出库单号">{{ detailRow.order_no }}</el-descriptions-item>
          <el-descriptions-item label="领料人">{{ detailRow.issuer || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="detailRow.status === 'approved'" type="success" size="small">已审核</el-tag>
            <el-tag v-else type="warning" size="small">待审核</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="出库日期">{{ detailRow.issue_date }}</el-descriptions-item>
          <el-descriptions-item label="明细数">{{ (detailRow.items || []).length }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ detailRow.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="detailRow.items || []" border size="small" show-summary :summary-method="sumItems">
          <el-table-column prop="material_code" label="物料编号" width="150" />
          <el-table-column prop="material_name" label="物料名称" min-width="120" />
          <el-table-column prop="spec" label="规格" width="100" />
          <el-table-column prop="qty" label="出库数量" width="100" align="right" />
          <el-table-column prop="return_qty" label="已退数量" width="100" align="right" />
          <el-table-column prop="remark" label="备注" min-width="120" />
          <el-table-column label="操作" align="center">
            <template #default="{ row }">
              <el-button link type="primary" @click="goPurchase(row.material_code)">采购明细</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <span class="footer-left"><el-button @click="printPage">打 印</el-button></span>
        <el-button type="primary" @click="detailDlg = false">关 闭</el-button>
      </template>
    </el-dialog>

    <IssueDialog v-model="issueDlg" @done="load" />
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import IssueDialog from '../components/IssueDialog.vue'
import TablePager from '../components/TablePager.vue'
import { usePaging } from '../usePaging'

const router = useRouter()
const rows = ref([])
const loading = ref(false)
const { page, pageSize, paged, total, resetPage } = usePaging(rows)
const keyword = ref('')
const searching = ref(false)
const options = ref([])

async function onSearch(q) {
  if (!q) { options.value = []; return }
  searching.value = true
  try { options.value = await api.get('/issues', { params: { keyword: q } }) }
  finally { searching.value = false }
}
function onPick(v) {
  if (v) { keyword.value = v; load() }
}
const issueDlg = ref(false)
const detailDlg = ref(false)
const detailRow = ref({})

function openDetail(row) {
  detailRow.value = row
  detailDlg.value = true
}

function goPurchase(materialCode) {
  detailDlg.value = false
  router.push({ path: '/purchases', query: { material_code: materialCode } })
}

function sumItems({ columns, data }) {
  return columns.map((col, i) => {
    if (i === 0) return '合计'
    const prop = col.property
    if (!['qty', 'return_qty'].includes(prop)) return ''
    const v = data.reduce((s, r) => s + Number(r[prop] || 0), 0)
    return v.toFixed(2).replace(/\.00$/, '')
  })
}
function printPage() { window.print() }

async function approve(row) {
  await ElMessageBox.confirm(`审核通过出库单 ${row.order_no}？审核后立即扣减库存`, '审核确认', { type: 'warning' })
  await api.post(`/issues/${row.id}/approve`)
  ElMessage.success('已审核，库存已扣减')
  load()
}

async function del(row) {
  await ElMessageBox.confirm(
    row.status === 'approved'
      ? `删除已审核出库单 ${row.order_no}？将反向回补库存（有退料记录的单不能删）`
      : `删除待审核出库单 ${row.order_no}？`,
    '删除确认', { type: 'warning' })
  await api.delete(`/issues/${row.id}`)
  ElMessage.success('已删除')
  load()
}

async function load() {
  loading.value = true
  try { rows.value = await api.get('/issues', { params: { keyword: keyword.value } }); resetPage() }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; }
.page-title { font-weight: 700; font-size: 16px; color: #1f2937; margin-right: 20px; white-space: nowrap; }
.toolbar-center { flex: 1; display: flex; justify-content: center; gap: 10px; align-items: center; }
.toolbar-right { display: flex; gap: 10px; align-items: center; }
:deep(.nowrap-cell .cell) { white-space: nowrap; }
.opt-row { display: flex; gap: 12px; align-items: center; font-size: 13px; }
.opt-date { color: #909399; }
.opt-no { font-weight: 600; }
.opt-remark { color: #909399; margin-left: auto; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
