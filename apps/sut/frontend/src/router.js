import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Tickets from './views/Tickets.vue'
import Knowledge from './views/Knowledge.vue'
import Workbench from './views/Workbench.vue'
import Report from './views/Report.vue'
import Portfolio from './views/Portfolio.vue'
import Platform from './views/Platform.vue'
import Models from './views/Models.vue'
import Methodology from './views/Methodology.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { title: '仪表盘' } },
    { path: '/tickets', component: Tickets, meta: { title: '工单管理' } },
    { path: '/knowledge', component: Knowledge, meta: { title: '知识库问答' } },
    { path: '/workbench', component: Workbench, meta: { title: 'API 工作台' } },
    { path: '/report', component: Report, meta: { title: '项目报告' } },
    { path: '/portfolio', component: Portfolio, meta: { title: '模块验收' } },
    { path: '/platform', component: Platform, meta: { title: '测试平台' } },
    { path: '/models', component: Models, meta: { title: '模型中心' } },
    { path: '/methodology', component: Methodology, meta: { title: '方法论' } },
  ],
})
