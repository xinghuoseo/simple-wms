import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/inventory',
    children: [
      { path: 'inventory', component: () => import('../views/Inventory.vue') },
      { path: 'issues', component: () => import('../views/IssueRecords.vue') },
      { path: 'returns', component: () => import('../views/ReturnRecords.vue') },
      { path: 'purchases', component: () => import('../views/Purchases.vue') },
      { path: 'suppliers', component: () => import('../views/Suppliers.vue') },
      { path: 'users', component: () => import('../views/Users.vue') },
      { path: 'help', component: () => import('../views/Help.vue') },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.path !== '/login' && !localStorage.getItem('token')) return '/login'
})

export default router
