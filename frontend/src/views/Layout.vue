<template>
  <el-container style="height:100%">
    <el-header class="top-header">
      <div class="logo">仓库管理</div>
      <nav class="top-menu">
        <router-link
          v-for="t in topTabs" :key="t.path" :to="t.path"
          class="top-item" :class="{ active: topActive === t.path }"
        >{{ t.title }}</router-link>
      </nav>
      <div class="user-info">
        {{ realName }}
        <el-button link type="danger" @click="logout">退出</el-button>
      </div>
    </el-header>

    <el-container>
      <el-aside width="180px" class="side-aside">
        <el-menu :default-active="route.path" router>
          <template v-for="item in subMenus" :key="item.path">
            <el-menu-item :index="item.path">{{ item.title }}</el-menu-item>
          </template>
        </el-menu>
      </el-aside>
      <el-main class="main-area">
        <div class="content-wrap">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const realName = localStorage.getItem('real_name') || ''

const topActive = computed(() => '/' + route.path.split('/')[1])

const topTabs = [
  { path: '/inventory', title: '库存' },
  { path: '/purchases', title: '采购' },
  { path: '/users', title: '设置' },
  { path: '/help', title: '帮助' },
]

const subMenus = computed(() => {
  const map = {
    '/inventory': [
      { path: '/inventory', title: '产品库存' },
      { path: '/issues', title: '出库记录' },
      { path: '/returns', title: '退料记录' },
    ],
    '/issues': [
      { path: '/inventory', title: '产品库存' },
      { path: '/issues', title: '出库记录' },
      { path: '/returns', title: '退料记录' },
    ],
    '/returns': [
      { path: '/inventory', title: '产品库存' },
      { path: '/issues', title: '出库记录' },
      { path: '/returns', title: '退料记录' },
    ],
    '/purchases': [
      { path: '/purchases', title: '采购' },
      { path: '/suppliers', title: '供应商' },
    ],
    '/suppliers': [
      { path: '/purchases', title: '采购' },
      { path: '/suppliers', title: '供应商' },
    ],
    '/users': [{ path: '/users', title: '用户管理' }],
    '/help': [],
  }
  return map[topActive.value] || []
})

function logout() {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.top-header {
  display: flex; align-items: stretch; background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); padding: 0 20px;
  height: 56px; z-index: 50; position: relative;
}
.logo {
  display: flex; align-items: center;
  font-weight: 700; font-size: 17px; margin-right: 24px;
  color: #1f2937; letter-spacing: 0.5px; white-space: nowrap;
}
.top-menu { flex: 1; display: flex; align-items: stretch; height: 100%; }
.top-item {
  display: flex; align-items: center; height: 100%;
  padding: 0 18px; font-size: 14px; text-decoration: none;
  color: #6b7280; border-bottom: 2px solid transparent;
  box-sizing: border-box; transition: all 0.2s;
}
.top-item:hover { color: #667eea; background: #f9fafb; }
.top-item.active {
  color: #667eea; font-weight: 600;
  border-bottom: 2px solid #667eea; background: #f9fafb;
}
.user-info {
  display: flex; align-items: center; height: 100%;
  color: #4b5563; font-size: 14px; white-space: nowrap;
}
.side-aside { background: #fff; border-right: 1px solid #e5e7eb; }
.side-aside :deep(.el-menu) { border-right: none; }
.side-aside :deep(.el-menu-item) {
  color: #6b7280; border-left: 3px solid transparent; margin: 4px 0; height: 48px;
}
.side-aside :deep(.el-menu-item:hover) { background: #f3f4f6; color: #667eea; }
.side-aside :deep(.el-menu-item.is-active) {
  background: #eef2ff; color: #667eea; border-left-color: #667eea; font-weight: 600;
}
.main-area { background: #f0f2f5; padding: 20px; }
.content-wrap { max-width: 1440px; margin: 0 auto; }
</style>
