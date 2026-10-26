<template>
  <div class="help-page">
    <h2>系统帮助 · 用大白话说清楚整个系统</h2>

    <el-card shadow="never" class="card">
      <template #header><b>一、整体结构：上面两个大板块，左边是小页面</b></template>
      <p>系统打开后，<b>顶部</b>是几个大板块：<b>库存、采购、设置、帮助</b>。<b>左侧</b>是当前板块下的具体小页面。点顶部的板块，左侧的菜单会跟着换。</p>
      <ul>
        <li><b>库存</b> 板块下有：产品库存、出库记录、出库退料</li>
        <li><b>采购</b> 板块下有：采购、供应商</li>
        <li><b>设置</b> 板块下有：用户管理（加账号、改密码）</li>
        <li><b>帮助</b> 就是你现在看的这个页面</li>
      </ul>
    </el-card>

    <el-card shadow="never" class="card">
      <template #header><b>二、日常使用顺序：先把货买进来，再把货发出去</b></template>
      <el-steps :active="4" align-center style="margin:10px 0">
        <el-step title="1. 添加供应商" description="从谁那儿买货" />
        <el-step title="2. 添加采购" description="货买进来了" />
        <el-step title="3. 开出库单" description="把货领出去" />
        <el-step title="4. 需要时退料" description="领多了退回来" />
      </el-steps>
      <p><b>第一步：添加供应商</b>（采购 → 供应商）。先登记有哪些供应商，比如"某某五金"。不登记的话，后面采购单里选不了供应商。</p>
      <p><b>第二步：添加采购</b>（采购 → 采购 → 点"添加采购"）。填好是哪个物料、买了多少、哪个供应商、什么时候到货。这一步做完，<b>仓库里就有货了</b>。</p>
      <p><b>第三步：开出库单</b>（库存 → 产品库存 → 点右上角"出库单"）。选择要领的物料、填领多少、谁领的。提交后系统自动生成一个工单号（CK 开头），<b>库存就会相应减少</b>。</p>
      <p><b>第四步：退料</b>（库存 → 产品库存 → 点右上角"退料单"，或直接看"出库退料"页面）。领多了、用不完，就开退料单把货退回仓库。<b>退回去库存就会加回来</b>。退料时只能选已有的出库（申领）工单，选的是哪张工单，货就退到那笔采购上。</p>
    </el-card>

    <el-card shadow="never" class="card">
      <template #header><b>三、库存是怎么算出来的（大白话版）</b></template>
      <p><b>1. 产品库存页看到的"当前实际库存数量"</b>：等于这个物料<b>所有采购单加起来的剩余量</b>。它是算出来的，不能直接改。</p>
      <p><b>2. 每一笔采购单的"实际剩余数量"</b> = 采购数量 − 申领数量（被领走的）+ 退回数量（退回来的）。买进来 100，领走 30，退回 10，这笔采购单还剩 80。</p>
      <p><b>3. 领货的规则（先进先出）</b>：你领货时，系统<b>从最早买进来的那批先扣</b>。老的那批不够扣了，就接着扣下一批。如果都扣完了还不够，最后一笔会记成负数——意思是"货已经超领了"，等你下次采购进来会自动补上。</p>
      <p><b>4. 超领了怎么办</b>：比如库存是负 5，你又新买了一批 50。系统会自动把旧的负数 5 清成 0，并把 5 记到新采购单头上（相当于新到的货先补之前的欠账），<b>不需要你手动处理</b>。</p>
      <p><b>5. 退料</b>：退的货会回到<b>当初领出货物的那笔采购单</b>上，不是随便加到哪一笔。这样每笔采购单的账都是对的。</p>
    </el-card>

    <el-card shadow="never" class="card">
      <template #header><b>四、各页面是干嘛的（一句话版）</b></template>
      <el-table :data="pageList" border size="small">
        <el-table-column prop="page" label="页面" width="140" />
        <el-table-column prop="desc" label="作用" />
      </el-table>
    </el-card>

    <el-card shadow="never" class="card">
      <template #header><b>五、常见问题</b></template>
      <p><b>Q：出库单和退料单在哪里开？</b><br>A：都在"产品库存"页面<b>右上角</b>的两个按钮：出库单、退料单。</p>
      <p><b>Q：工单号的规则？</b><br>A：出库单 CK 开头、退料单 TL 开头、采购单 CG 开头，后面跟日期和 3 位序号，比如 CK_20260828001，每天序号从 001 重新数。</p>
      <p><b>Q：为什么产品库存里有的物料是负数？</b><br>A：说明这个物料领出去的比买进来的多（超领了）。等下次采购入库后系统会自动把欠的补上。</p>
      <p><b>Q：新加的物料在哪里维护？</b><br>A：在"产品库存"页添加物料（物料编号、名称、规格），然后通过"添加采购"把数量买进来。</p>
    </el-card>
  </div>
</template>

<script setup>
const pageList = [
  { page: '产品库存', desc: '看每个物料现在仓库里还剩多少，也是开出库单、退料单的入口' },
  { page: '出库记录', desc: '历史开过的所有出库（申领）工单，只看不改' },
  { page: '出库退料', desc: '历史开过的所有退料记录，只看不改' },
  { page: '采购', desc: '录入采购单（买货入库），能看到每笔采购的剩余量' },
  { page: '供应商', desc: '维护供应商名单，采购单里要选' },
  { page: '用户管理', desc: '给同事开账号、改密码、停用账号' },
]
</script>

<style scoped>
.help-page { max-width: 900px; margin: 0 auto; }
.card { margin-bottom: 16px; }
.card p { line-height: 1.9; margin: 6px 0; color: #333; }
.card ul { line-height: 1.9; padding-left: 20px; color: #333; }
</style>
