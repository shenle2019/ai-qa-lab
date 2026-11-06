<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const groups = [
  {
    title: '数据与看板',
    items: [
      { to: '/dashboard', name: '仪表盘', desc: 'V1 的首页看板，汇总工单、知识库和平台指标。' },
      { to: '/report', name: '项目报告', desc: '按模块生成验收报告，可导出 HTML。' },
      { to: '/portfolio', name: '模块验收', desc: '模块级的验收清单与完成状态。' },
    ],
  },
  {
    title: '接口与用例',
    items: [
      { to: '/workbench', name: 'API 工作台', desc: 'V1 的接口调试台，支持保存请求与查看响应。' },
      { to: '/platform', name: '测试平台', desc: 'V1 的用例/计划/执行/缺陷聚合页。' },
      { to: '/testcases', name: '测试用例', desc: 'V1 的用例库，按分类浏览。' },
    ],
  },
  {
    title: '知识与协作',
    items: [
      { to: '/knowledge', name: '知识库问答', desc: 'V1 的知识库检索问答，回答带引用片段。' },
      { to: '/tickets', name: '工单管理', desc: 'V1 的缺陷工单流转。' },
      { to: '/models', name: '模型中心', desc: 'V1 的模型配置与连通性测试。' },
      { to: '/methodology', name: '方法论', desc: '测试方法论文档，随代码一起发布。' },
    ],
  },
]

const total = computed(() => groups.reduce((sum, group) => sum + group.items.length, 0))
</script>

<template>
  <div class="stack">
    <header class="hero">
      <div>
        <p class="eyebrow">TOOLS &amp; LEGACY</p>
        <h1>工具与旧版入口</h1>
        <p class="muted">
          V1 控制台的功能已经并入新导航（需求、用例、知识库、接口、UI、环境），这里保留入口用于对照查询。
          新流程请走侧栏对应页面，旧页只做只读参考。
        </p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ total }}</strong><span>旧版页面</span></div>
      </div>
    </header>

    <section v-for="group in groups" :key="group.title" class="card">
      <div class="card-head">
        <h2>{{ group.title }}</h2>
        <span class="muted">{{ group.items.length }} 个</span>
      </div>
      <ul class="tool-list">
        <li v-for="item in group.items" :key="item.to">
          <div>
            <RouterLink :to="item.to" class="tool-name">{{ item.name }}</RouterLink>
            <p class="tool-desc">{{ item.desc }}</p>
          </div>
          <code class="tool-path">{{ item.to }}</code>
        </li>
      </ul>
    </section>

    <p class="alert info">
      这些页面沿用 V1 的布局，只继承了新版配色，没有重新设计。如果某个功能已经在新页面里覆盖，旧入口随时可以下线。
    </p>
  </div>
</template>

<style scoped>
.tool-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tool-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--hairline);
}

.tool-list li:last-child {
  border-bottom: 0;
}

.tool-name {
  color: var(--accent-strong);
  font-size: 14px;
  font-weight: 650;
}

.tool-name:hover {
  text-decoration: underline;
}

.tool-desc {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12.5px;
}

.tool-path {
  flex: 0 0 auto;
  padding: 2px 8px;
  border: 1px solid var(--hairline);
  border-radius: 6px;
  background: var(--surface-2);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11.5px;
}
</style>
