import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  // Workspace
  { path: '/', component: () => import('./views/projects/ProjectOverview.vue'), meta: { title: '项目概览' } },
  { path: '/projects', component: () => import('./views/projects/ProjectsView.vue'), meta: { title: '项目管理' } },
  { path: '/overview', component: () => import('./views/projects/ProjectOverview.vue'), meta: { title: '项目概览' } },
  { path: '/system-ai', component: () => import('./views/ai/SystemAiView.vue'), meta: { title: '系统 AI 配置' } },
  { path: '/ai-logs', component: () => import('./views/ai/AiLogsView.vue'), meta: { title: 'AI 调用日志' } },
  { path: '/users', component: () => import('./views/ai/UsersView.vue'), meta: { title: '用户管理' } },

  // Testing
  { path: '/requirements', component: () => import('./views/testing/RequirementsView.vue'), meta: { title: '需求管理' } },
  { path: '/functional', component: () => import('./views/testing/FunctionalView.vue'), meta: { title: '功能测试' } },
  { path: '/kb', component: () => import('./views/testing/KnowledgeBaseView.vue'), meta: { title: '知识库' } },

  // Automation
  { path: '/environments', component: () => import('./views/automation/EnvironmentsView.vue'), meta: { title: '环境管理' } },
  { path: '/api-automation', component: () => import('./views/automation/ApiAutomationView.vue'), meta: { title: '接口自动化' } },
  { path: '/ui-automation', component: () => import('./views/automation/UiAutomationView.vue'), meta: { title: 'UI 自动化' } },

  // Project
  { path: '/modules', component: () => import('./views/projects/ModulesView.vue'), meta: { title: '模块管理' } },
  { path: '/members', component: () => import('./views/projects/MembersView.vue'), meta: { title: '成员管理' } },

  // Legacy pages (kept reachable; sidebar groups them under 开发工具)
  { path: '/dashboard', component: () => import('./views/Dashboard.vue'), meta: { title: '仪表盘' } },
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
  { path: '/:pathMatch(.*)*', component: () => import('./views/NotFound.vue'), meta: { title: '页面不存在' } },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
