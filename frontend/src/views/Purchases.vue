<template>
  <el-card shadow="never">
    <div class="toolbar">
      <div class="page-title">采购管理</div>
      <div class="toolbar-center">
        <el-select
          v-model="keyword"
          filterable remote clearable default-first-option
          :remote-method="onSearch"
          :loading="searching"
          placeholder="搜索单号/供应商/物料"
          style="width:340px"
          @change="onPick"
          @clear="load"
        >
          <el-option v-for="r in options" :key="r.id" :label="r.order_no" :value="r.order_no">
            <div class="opt-row">
              <span class="opt-date">{{ r.purchase_date }}</span>
              <span class="opt-no">{{ r.order_no }}</span>
              <span>{{ r.supplier_name || '-' }}</span>
              <span>{{ r.purchaser || '-' }}</span>
            </div>
          </el-option>
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="openDlg">添加采购</el-button>
      </div>
    </div>

    <el-table :data="paged" border stripe v-loading="loading" row-key="id">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="padding: 8px 40px">
            <el-table :data="row.items" border size="small">
              <el-table-column prop="material_code" label="物料编号" width="150" />
              <el-table-column prop="material_name" label="物料名称" min-width="120" />
              <el-table-column prop="spec" label="规格" width="100" />
              <el-table-column prop="purchase_qty" label="采购数量" width="100" align="right" />
              <el-table-column prop="claimed_qty" label="申领数量" width="100" align="right">
                <template #default="{ row: it }">
                  <span :style="{ color: it.claimed_qty < 0 ? '#f56c6c' : '' }">{{ it.claimed_qty }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="return_qty" label="退单数量" width="100" align="right" />
              <el-table-column prop="remaining_qty" label="实际剩余" width="100" align="right">
                <template #default="{ row: it }">
                  <span :style="{ color: it.remaining_qty < 0 ? '#f56c6c' : '' }">{{ it.remaining_qty }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="remark" label="备注" min-width="140" />
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="purchase_date" label="采购日期" width="105" />
      <el-table-column prop="purchaser" label="采购人" width="90" />
      <el-table-column prop="order_no" label="采购单号" width="150" class-name="nowrap-cell" />
      <el-table-column prop="supplier_name" label="供应商" min-width="110" />
      <el-table-column prop="in_stock_date" label="入库日期" width="105" />
      <el-table-column prop="status" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'approved' ? 'success' : 'warning'" size="small">
            {{ row.status === 'approved' ? '已审核' : '待审核' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="明细数" width="70" align="center">
        <template #default="{ row }">{{ row.items.length }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button v-if="row.status !== 'approved'" link type="warning" @click="openEdit(row)">修改</el-button>
          <el-button v-if="row.status !== 'approved'" link type="success" @click="approve(row)">审核</el-button>
        </template>
      </el-table-column>
    </el-table>
    <TablePager v-model:page="page" v-model:page-size="pageSize" :total="total" />

    <!-- 采购单详情 -->
    <el-dialog v-model="detailDlg" :title="`采购单详情 ${detailRow.order_no || ''}`" width="1100px" destroy-on-close>
      <div class="print-area">
        <div class="print-only">采购单详情 {{ detailRow.order_no }}</div>
        <el-descriptions :column="3" border size="small" style="margin-bottom:12px">
          <el-descriptions-item label="采购单号">{{ detailRow.order_no }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ detailRow.supplier_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="采购人">{{ detailRow.purchaser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="采购日期">{{ detailRow.purchase_date }}</el-descriptions-item>
          <el-descriptions-item label="入库日期">{{ detailRow.in_stock_date }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailRow.status === 'approved' ? 'success' : 'warning'" size="small">
              {{ detailRow.status === 'approved' ? '已审核' : '待审核' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="明细数">{{ (detailRow.items || []).length }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ detailRow.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="detailRow.items || []" border size="small" show-summary :summary-method="sumDetail">
          <el-table-column prop="material_code" label="物料编号" width="150" />
          <el-table-column prop="material_name" label="物料名称" min-width="120" />
          <el-table-column prop="spec" label="规格" width="100" />
          <el-table-column prop="purchase_qty" label="采购数量" width="100" align="right" />
          <el-table-column prop="claimed_qty" label="申领数量" width="100" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.claimed_qty < 0 ? '#f56c6c' : '' }">{{ row.claimed_qty }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="return_qty" label="退单数量" width="100" align="right" />
          <el-table-column prop="remaining_qty" label="实际剩余" width="100" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.remaining_qty < 0 ? '#f56c6c' : '' }">{{ row.remaining_qty }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="120" />
        </el-table>
      </div>
      <template #footer>
        <span class="footer-left"><el-button @click="printPage">打 印</el-button></span>
        <el-button type="primary" @click="detailDlg = false">关 闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dlg" :title="editingId ? '修改采购单' : '添加采购单'" width="960px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="供应商">
          <el-select v-model="form.supplier_id" filterable clearable style="width:100%">
            <el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="采购人" required>
          <div class="row-line">
            <el-select v-model="form.purchaser" filterable allow-create default-first-option
              placeholder="选择或输入采购人" style="width:190px">
              <el-option v-for="u in userOptions" :key="u.id" :label="u.real_name || u.username" :value="u.real_name || u.username" />
            </el-select>
            <span class="sep">采购日期</span>
            <el-date-picker v-model="form.purchase_date" type="date" value-format="YYYY-MM-DD" style="width:150px" />
            <span class="sep">入库日期</span>
            <el-date-picker v-model="form.in_stock_date" type="date" value-format="YYYY-MM-DD" style="width:150px" />
          </div>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" /></el-form-item>
      </el-form>

      <div class="items-head">
        <b>采购明细</b>
        <div>
          <el-button size="small" @click="openMatDlg">新增物料</el-button>
          <el-button type="primary" size="small" @click="addItem">添加明细</el-button>
        </div>
      </div>
      <el-table :data="items" border size="small">
        <el-table-column label="物料（可搜索；搜不到可点新增物料）" min-width="200">
          <template #default="{ row, $index }">
            <el-select v-model="row.material_id" filterable remote :remote-method="searchMaterials"
              :loading="dlgSearching" placeholder="输入物料名称或编号搜索" style="width:100%"
              @change="id => onPicked(id, $index)">
              <el-option v-for="m in materialOptions" :key="m.id" :label="`${m.code} - ${m.name}`" :value="m.id" />
              <el-option v-if="!materialOptions.length && lastQuery" key="__new__" label="" :value="'__new__'">
                <span style="color:#667eea">＋ 新增物料「{{ lastQuery }}」</span>
              </el-option>
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="编号">
          <template #default="{ row }">{{ row.code }}</template>
        </el-table-column>
        <el-table-column label="规格">
          <template #default="{ row }">{{ row.spec }}</template>
        </el-table-column>
        <el-table-column label="采购数量">
          <template #default="{ row }">
            <el-input-number v-model="row.purchase_qty" :min="0.01" style="width:100%" />
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
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">提交</el-button>
      </template>
    </el-dialog>

    <!-- 新增物料（嵌套在采购弹窗内） -->
    <el-dialog v-model="matDlg" title="新增物料" width="500px" destroy-on-close append-to-body>
      <el-form label-width="80px">
        <el-form-item label="编号" required><el-input v-model="matForm.code" placeholder="如 11-Y01-002-201" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="matForm.name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="matForm.spec" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="matForm.remark" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="matDlg = false">取消</el-button>
        <el-button type="primary" @click="submitMaterial">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import TablePager from '../components/TablePager.vue'
import { usePaging } from '../usePaging'

const route = useRoute()
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
  try { options.value = await api.get('/purchases', { params: { keyword: q } }) }
  finally { searching.value = false }
}
function onPick(v) {
  if (v) { keyword.value = v; load() }
}
const dlg = ref(false)
const submitting = ref(false)
const dlgSearching = ref(false)
const materialOptions = ref([])
const suppliers = ref([])
const items = ref([])
const form = reactive({
  supplier_id: null,
  purchaser: '',
  purchase_date: new Date().toISOString().slice(0, 10),
  in_stock_date: new Date().toISOString().slice(0, 10),
  remark: '',
})
const editingId = ref(null)
const userOptions = ref([])

async function load() {
  loading.value = true
  try { rows.value = await api.get('/purchases', { params: { keyword: keyword.value } }); resetPage() }
  finally { loading.value = false }
}
onMounted(async () => {
  const q = route.query
  if (q.order_no) {
    keyword.value = String(q.order_no)
    await load()
    const row = rows.value.find(r => r.order_no === q.order_no)
    if (row) openDetail(row)
    router.replace({ path: '/purchases' })
  } else if (q.material_code) {
    keyword.value = String(q.material_code)
    await load()
    router.replace({ path: '/purchases' })
  } else {
    load()
  }
  api.get('/suppliers').then(d => suppliers.value = d)
  api.get('/users').then(d => userOptions.value = d.filter(u => u.username !== 'admin'))
})

function openDlg() {
  editingId.value = null
  form.supplier_id = null; form.purchaser = ''; form.remark = ''
  form.purchase_date = form.in_stock_date = new Date().toISOString().slice(0, 10)
  items.value = []
  dlg.value = true
}
function openEdit(row) {
  editingId.value = row.id
  form.supplier_id = row.supplier_id
  form.purchaser = row.purchaser || ''
  form.purchase_date = row.purchase_date
  form.in_stock_date = row.in_stock_date
  form.remark = row.remark || ''
  items.value = row.items.map(it => ({
    material_id: it.material_id, code: it.material_code, spec: it.spec,
    purchase_qty: it.purchase_qty, remark: it.remark || '',
  }))
  dlg.value = true
}
async function approve(row) {
  try {
    await ElMessageBox.confirm(
      '审核通过后，该采购单将计入库存，出库/退料才能扣减到此单的明细。审核后不能再修改。确定审核通过吗？',
      '审核确认', { type: 'warning', confirmButtonText: '审核通过', cancelButtonText: '取消' }
    )
  } catch { return }
  await api.post(`/purchases/${row.id}/approve`)
  ElMessage.success(`采购单 ${row.order_no} 已审核`)
  load()
}
function addItem() {
  items.value.push({ material_id: null, code: '', spec: '', purchase_qty: 1, remark: '' })
}
async function searchMaterials(q) {
  lastQuery.value = q || ''
  if (!q) return
  dlgSearching.value = true
  try { materialOptions.value = await api.get('/materials', { params: { keyword: q } }) }
  finally { dlgSearching.value = false }
}
function onPicked(id, idx) {
  if (id === '__new__') {
    // 下拉里点了"新增物料"：记住这一行，打开新增弹窗（名称预填搜索词）
    if (items.value[idx]) items.value[idx].material_id = null
    pendingMatRow.value = idx
    matForm.code = ''; matForm.name = lastQuery.value || ''; matForm.spec = ''; matForm.remark = ''
    matDlg.value = true
    return
  }
  const m = materialOptions.value.find(x => x.id === id)
  if (m && items.value[idx]) { items.value[idx].code = m.code; items.value[idx].spec = m.spec }
}

// ---- 采购单详情 ----
const detailDlg = ref(false)
const detailRow = ref({})

function openDetail(row) {
  detailRow.value = row
  detailDlg.value = true
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

// ---- 新增物料（采购弹窗内） ----
const matDlg = ref(false)
const matForm = reactive({ code: '', name: '', spec: '', remark: '' })
const lastQuery = ref('')
const pendingMatRow = ref(null)

function openMatDlg() {
  matForm.code = ''; matForm.name = ''; matForm.spec = ''; matForm.remark = ''
  pendingMatRow.value = null
  matDlg.value = true
}
async function submitMaterial() {
  if (!matForm.code || !matForm.name) return ElMessage.warning('请填写编号和名称')
  const m = await api.post('/materials', { ...matForm, code: matForm.code.toUpperCase() })
  ElMessage.success('物料已添加')
  matDlg.value = false
  materialOptions.value = [m, ...materialOptions.value]
  const idx = pendingMatRow.value
  const target = (idx != null && items.value[idx]) ? items.value[idx] : items.value.find(i => !i.material_id)
  if (target) { target.material_id = m.id; target.code = m.code; target.spec = m.spec }
  pendingMatRow.value = null
}
async function submit() {
  if (!form.purchaser) return ElMessage.warning('请选择或输入采购人')
  const valid = items.value.filter(i => i.material_id && i.purchase_qty > 0)
  if (!valid.length) return ElMessage.warning('请至少添加一行有效明细（选物料、数量>0）')
  submitting.value = true
  try {
    const payload = { ...form, items: valid.map(i => ({ material_id: i.material_id, purchase_qty: i.purchase_qty, remark: i.remark || '' })) }
    const r = editingId.value
      ? await api.put(`/purchases/${editingId.value}`, payload)
      : await api.post('/purchases', payload)
    ElMessage.success(editingId.value ? `采购单已修改，单号 ${r.order_no}` : `采购单已添加，单号 ${r.order_no}（待审核）`)
    dlg.value = false
    load()
  } finally { submitting.value = false }
}
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; }
.page-title { font-weight: 700; font-size: 16px; color: #1f2937; margin-right: 20px; white-space: nowrap; }
.toolbar-center { flex: 1; display: flex; justify-content: center; gap: 10px; align-items: center; }
.toolbar-right { display: flex; gap: 10px; align-items: center; }
.items-head { display: flex; justify-content: space-between; align-items: center; margin: 14px 0 8px; }
.row-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sep { color: #909399; font-size: 13px; }
:deep(.nowrap-cell .cell) { white-space: nowrap; }
.opt-row { display: flex; gap: 12px; align-items: center; font-size: 13px; }
.opt-date { color: #909399; }
.opt-no { font-weight: 600; }
</style>
