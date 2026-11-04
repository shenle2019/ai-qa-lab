import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('./views/Dashboard.vue'), meta: { title: '仪表盘' } },
  { path: '/tickets', component: () => import('./views/Tickets.vue'), meta: { title: '工单管理' } },
  { path: '/knowledge', component: () => import('./views/Knowledge.vue'), meta: { title: '知识库问答' } },
  { path: '/workbench', component: () => import('./views/Workbench.vue'), meta: { title: 'API 工作台' } },
  { path: '/report', component: () => import('./views/Report.vue'), meta: { title: '项目报告' } },
  { path: '/portfolio', component: () => import('./views/Portfolio.vue'), meta: { title: '模块验收' } },
  { path: '/platform', component: () => import('./views/Platform.vue'), meta: { title: '测试平台' } },
  { path: '/models', component: () => import('./views/Models.vue'), meta: { title: '模型中心' } },
  { path: '/testcases', component: () => import('./views/TestCases.vue'), meta: { title: '测试用例' } },
  { path: '/methodology', component: () => import('./views/Methodology.vue'), meta: { title: '方法论' } },
  { path: '/login', component: () => import('./views/Login.vue'), meta: { title: '访问密钥' } },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
