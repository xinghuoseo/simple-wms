<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div class="page-title">产品库存</div>
      <div class="toolbar-center">
        <el-select
          v-model="keyword"
          filterable remote clearable default-first-option
          :remote-method="onSearch"
          :loading="topSearching"
          placeholder="搜索物料编号/名称"
          style="width:360px"
          @change="onPick"
          @clear="load"
        >
          <el-option v-for="r in topOptions" :key="r.material_id" :label="r.material_code" :value="r.material_code">
            <div class="opt-row">
              <span class="opt-no">{{ r.material_code }}</span>
              <span>{{ r.material_name }}</span>
              <span :style="{ color: r.stock_qty < 0 ? '#f56c6c' : '' }">库存 {{ r.stock_qty }}</span>
              <span class="opt-remark">{{ r.spec || '' }}</span>
            </div>
          </el-option>
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="info" plain @click="exportExcel">导出库存</el-button>
        <el-button type="warning" @click="issueDlg = true">出库单</el-button>
        <el-button type="success" @click="returnDlg = true">退料单</el-button>
      </div>
    </div>

    <el-table :data="paged" border stripe v-loading="loading">
      <el-table-column prop="material_code" label="物料编号" width="150" />
      <el-table-column prop="material_name" label="物料名称" min-width="140" />
      <el-table-column prop="stock_qty" label="当前实际库存数量" width="140" align="right">
        <template #default="{ row }">
          <span :style="{ color: row.stock_qty < 0 ? '#f56c6c' : '' }">{{ row.stock_qty }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="purchase_total" label="采购总数量" width="110" align="right" />
      <el-table-column prop="issue_total" label="申领总数量" width="110" align="right" />
      <el-table-column prop="return_total" label="退料工单总数量" width="130" align="right" />
      <el-table-column prop="spec" label="规格" width="110" />
      <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button link type="warning" @click="openEdit(row)">修改</el-button>
        </template>
      </el-table-column>
    </el-table>
    <TablePager v-model:page="page" v-model:page-size="pageSize" :total="total" />

    <!-- 出库单弹窗：与出库记录页同一套组件 -->
    <IssueDialog v-model="issueDlg" @done="load" />

    <!-- 退料单弹窗：先选出库单，列出明细，仅可改回退数量 -->
    <el-dialog v-model="returnDlg" title="退料单" width="960px" destroy-on-close @open="resetReturn">
      <el-alert type="warning" :closable="false" style="margin-bottom:12px"
        title="为什么先选出库单？退料是针对某一张出库单退的：先找到当时领料的那张出库单，系统会列出这张单领了哪些物料、各剩多少可退，你只填回退数量，退回的物料才能准确记回对应工单的账上。" />
      <el-form label-width="90px">
        <el-form-item label="出库单" required>
          <el-select v-model="returnOrderNo" filterable remote :remote-method="searchIssues"
            :loading="searching" placeholder="输入出库单号/物料名称/编号/领料人搜索" style="width:100%"
            @change="onIssueOrderPicked">
            <el-option v-for="i in issueOptions" :key="i.order_no"
              :label="`${i.order_no}（${i.issue_date}，领料人 ${i.issuer || '-'}）`" :value="i.order_no" />
          </el-select>
        </el-form-item>
        <el-form-item label="回退日期" required>
          <el-date-picker v-model="returnDate" type="date" value-format="YYYY-MM-DD" style="width:300px" />
        </el-form-item>
      </el-form>

      <template v-if="returnRows.length">
        <el-alert type="info" :closable="false" style="margin-bottom:10px"
          title="出库数量是锁定的，只能填写回退数量；重新选择出库单会作废当前已填内容" />
        <el-table :data="returnRows" border size="small">
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
        </el-table>
      </template>

      <template #footer>
        <el-button @click="returnDlg = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!returnOrderNo" @click="submitReturn">提交</el-button>
      </template>
    </el-dialog>

    <!-- 物料采购明细详情：只列剩余不为 0 的采购行 -->
    <el-dialog v-model="detailDlg" :title="`${detailMaterial.code} ${detailMaterial.name} - 采购明细（剩余≠0）`"
      width="1100px" destroy-on-close>
      <div class="print-area">
        <div class="print-only">采购明细 — {{ detailMaterial.code }} {{ detailMaterial.name }}</div>
        <el-table :data="detailRows" border size="small" v-loading="detailLoading" show-summary
          :summary-method="sumDetail">
          <el-table-column prop="order_no" label="采购单号" width="150" class-name="nowrap-cell" />
          <el-table-column prop="in_stock_date" label="入库日期" width="105" />
          <el-table-column prop="supplier_name" label="供应商" width="120" />
          <el-table-column prop="spec" label="规格" width="100" />
          <el-table-column prop="purchase_qty" label="采购数量" width="95" align="right" />
          <el-table-column prop="claimed_qty" label="申领数量" width="95" align="right" />
          <el-table-column prop="return_qty" label="退回数量" width="95" align="right" />
          <el-table-column prop="remaining_qty" label="实际剩余" width="95" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.remaining_qty < 0 ? '#f56c6c' : '' }">{{ row.remaining_qty }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center">
            <template #default="{ row }">
              <el-button link type="primary" @click="goPurchase(row.order_no)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-if="!detailLoading && !detailRows.length" description="没有剩余数量不为 0 的采购明细" :image-size="60" />
      <template #footer>
        <span class="footer-left"><el-button @click="printPage">打 印</el-button></span>
        <el-button type="primary" @click="detailDlg = false">关 闭</el-button>
      </template>
    </el-dialog>
    <!-- 修改物料 -->
    <el-dialog v-model="editDlg" title="修改物料" width="500px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="物料编号" required><el-input v-model="editForm.code" /></el-form-item>
        <el-form-item label="物料名称" required><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="editForm.spec" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editForm.remark" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDlg = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import IssueDialog from '../components/IssueDialog.vue'
import TablePager from '../components/TablePager.vue'
import { usePaging } from '../usePaging'
import * as XLSX from 'xlsx'

const rows = ref([])
const loading = ref(false)
const { page, pageSize, paged, total, resetPage } = usePaging(rows)
const keyword = ref('')
const topSearching = ref(false)
const topOptions = ref([])

async function onSearch(q) {
  if (!q) { topOptions.value = []; return }
  topSearching.value = true
  try { topOptions.value = await api.get('/inventory', { params: { keyword: q } }) }
  finally { topSearching.value = false }
}
function onPick(v) {
  if (v) { keyword.value = v; load() }
}
const stockMap = ref({})

async function load() {
  loading.value = true
  try {
    rows.value = await api.get('/inventory', { params: { keyword: keyword.value } })
    stockMap.value = Object.fromEntries(rows.value.map(r => [r.material_id, r.stock_qty]))
    resetPage()
  } finally { loading.value = false }
}
onMounted(load)

const submitting = ref(false)
function today() { return new Date().toISOString().slice(0, 10) }

// ---- 出库单（使用公共 IssueDialog 组件，与出库记录页同一套） ----
const issueDlg = ref(false)

// ---- 退回单 ----
const returnDlg = ref(false)
const returnOrderNo = ref('')
const returnDate = ref(today())
const issueOptions = ref([])
const returnRows = ref([])
const searching = ref(false)

function resetReturn() {
  returnOrderNo.value = ''
  returnDate.value = today()
  issueOptions.value = []
  returnRows.value = []
}
async function searchIssues(q) {
  if (!q) return
  searching.value = true
  try { issueOptions.value = await api.get('/issues', { params: { keyword: q } }) }
  finally { searching.value = false }
}
async function onIssueOrderPicked(orderNo) {
  // 重新选择出库单：之前填的内容全部作废
  const d = await api.get(`/issues/${orderNo}/detail-for-return`)
  returnRows.value = d.items.map(it => ({ ...it, return_qty: 0 }))
}
async function submitReturn() {
  const items = returnRows.value.filter(r => r.return_qty > 0)
    .map(r => ({ issue_item_id: r.issue_item_id, qty: r.return_qty }))
  if (!items.length) return ElMessage.warning('请至少填写一行回退数量')
  submitting.value = true
  try {
    const r = await api.post('/returns', { issue_order_no: returnOrderNo.value, return_date: returnDate.value, items })
    ElMessage.success(`退回成功，单号 ${r.return_no}`)
    returnDlg.value = false
    load()
  } finally { submitting.value = false }
}

// ---- 物料采购明细详情 ----
const detailDlg = ref(false)
const detailLoading = ref(false)
const detailRows = ref([])
const detailMaterial = reactive({ code: '', name: '' })

async function openDetail(row) {
  detailMaterial.code = row.material_code
  detailMaterial.name = row.material_name
  detailDlg.value = true
  detailLoading.value = true
  try { detailRows.value = await api.get(`/purchases/by-material/${row.material_id}`) }
  finally { detailLoading.value = false }
}

// ---- 修改物料 ----
const editDlg = ref(false)
const editForm = reactive({ id: null, code: '', name: '', spec: '', remark: '' })

function openEdit(row) {
  editForm.id = row.material_id
  editForm.code = row.material_code
  editForm.name = row.material_name
  editForm.spec = row.spec
  editForm.remark = row.remark
  editForm._origCode = row.material_code
  editForm._origName = row.material_name
  editDlg.value = true
}
async function submitEdit() {
  if (!editForm.code || !editForm.name) return ElMessage.warning('请填写编号和名称')
  const changed = editForm.code !== editForm._origCode || editForm.name !== editForm._origName
  if (changed) {
    try {
      await ElMessageBox.confirm(
        '修改物料编号或名称后，所有采购单、出库单、退料单中对应的物料编号和名称都会同步修改。确定要修改吗？',
        '二次确认', { type: 'warning', confirmButtonText: '确定修改', cancelButtonText: '取消' }
      )
    } catch { return }
  }
  submitting.value = true
  try {
    await api.put(`/materials/${editForm.id}`, { ...editForm, id: undefined })
    ElMessage.success('物料已修改')
    editDlg.value = false
    load()
  } finally { submitting.value = false }
}

const router = useRouter()
function goPurchase(orderNo) {
  detailDlg.value = false
  router.push({ path: '/purchases', query: { order_no: orderNo } })
}

function sumDetail({ columns, data }) {
  return columns.map((col, i) => {
    if (i === 0) return '合计'
    const prop = col.property
    if (!['purchase_qty', 'claimed_qty', 'return_qty', 'remaining_qty'].includes(prop)) return ''
    const v = data.reduce((s, r) => s + Number(r[prop] || 0), 0)
    return v.toFixed(2).replace(/\.00$/, '')
  })
}
function printPage() { window.print() }

// ---- 导出库存（按当前表格列，含当前搜索结果） ----
function exportExcel() {
  if (!rows.value.length) return ElMessage.warning('当前没有可导出的数据')
  const header = ['物料编号', '物料名称', '当前实际库存数量', '采购总数量', '申领总数量', '退料工单总数量', '规格', '备注']
  const data = rows.value.map(r => [
    r.material_code, r.material_name, Number(r.stock_qty), Number(r.purchase_total),
    Number(r.issue_total), Number(r.return_total), r.spec, r.remark,
  ])
  const ws = XLSX.utils.aoa_to_sheet([header, ...data])
  ws['!cols'] = [{ wch: 18 }, { wch: 24 }, { wch: 16 }, { wch: 12 }, { wch: 12 }, { wch: 15 }, { wch: 14 }, { wch: 30 }]
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '产品库存')
  XLSX.writeFile(wb, `产品库存_${today()}.xlsx`)
  ElMessage.success(`已导出 ${rows.value.length} 条库存记录`)
}
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; }
.page-title { font-weight: 700; font-size: 16px; color: #1f2937; margin-right: 20px; white-space: nowrap; }
.toolbar-center { flex: 1; display: flex; justify-content: center; gap: 10px; align-items: center; }
.toolbar-right { display: flex; gap: 10px; align-items: center; }
.items-head { display: flex; justify-content: space-between; align-items: center; margin: 14px 0 8px; }
:deep(.nowrap-cell .cell) { white-space: nowrap; }
.opt-row { display: flex; gap: 12px; align-items: center; font-size: 13px; }
.opt-no { font-weight: 600; }
.opt-remark { color: #909399; margin-left: auto; }
</style>
