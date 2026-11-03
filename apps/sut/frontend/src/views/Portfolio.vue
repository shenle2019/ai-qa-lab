<script setup>
import { computed } from 'vue'

const modules = [
  {
    id: '01',
    name: 'AI 协作与质量工程方法论',
    reference: 'atinfo/awesome-test-automation',
    stars: '7,208',
    href: 'https://github.com/atinfo/awesome-test-automation',
    status: 'planned',
    scope: '知识图谱、分层选型决策树、检查表',
  },
  {
    id: '02',
    name: 'Python 测试开发',
    reference: 'pytest-dev/pytest',
    stars: '14,661',
    href: 'https://github.com/pytest-dev/pytest',
    status: 'progress',
    scope: '迷你 pytest v0.1：收集、fixture、参数化、marker、断言、重试、JSON/HTML 报告；33 元测试 + 20 演示',
    report: '/portfolio/module-02-minipytest-report.html',
  },
  {
    id: '03',
    name: 'AI 接口自动化测试',
    reference: 'hoppscotch/hoppscotch',
    stars: '80,721',
    href: 'https://github.com/hoppscotch/hoppscotch',
    status: 'progress',
    scope: '基础接口套件 22 tests 通过；Hoppscotch 风格 API 工作台 v0.1 已上线',
  },
  {
    id: '04',
    name: 'AI Web 自动化测试',
    reference: 'microsoft/playwright',
    stars: '99,087',
    href: 'https://github.com/microsoft/playwright',
    status: 'progress',
    scope: 'miniplaywright v0.1：CDP 驱动、选择器、自动等待、断言、截图；6 元测试 + 5 个 SUT UI 用例',
    report: '/portfolio/module-04-playwright-report.html',
  },
  {
    id: '05',
    name: 'AI App 终端 UI 自动化',
    reference: 'appium/appium',
    stars: '22,174',
    href: 'https://github.com/appium/appium',
    status: 'planned',
    scope: '会话管理、元素定位、手势、模拟器驱动',
  },
  {
    id: '06',
    name: '性能测试专家 · AI 增强版',
    reference: 'grafana/k6',
    stars: '32,102',
    href: 'https://github.com/grafana/k6',
    status: 'planned',
    scope: '场景编排、阈值、P95/P99、实时指标',
  },
  {
    id: '07',
    name: 'AI 测试平台与工具开发',
    reference: 'metersphere/metersphere',
    stars: '13,600',
    href: 'https://github.com/metersphere/metersphere',
    status: 'progress',
    scope: '当前 SUT 控制台已上线，平台闭环待扩展',
  },
  {
    id: '08',
    name: 'Agent 专项测试与大模型评估',
    reference: 'confident-ai/deepeval',
    stars: '19,242',
    href: 'https://github.com/confident-ai/deepeval',
    status: 'planned',
    scope: '数据集、指标、裁判模型、阈值与对比报告',
  },
]

const doneCount = computed(() => modules.filter((item) => item.status === 'done').length)
const progressCount = computed(() => modules.filter((item) => item.status === 'progress').length)

const statusLabel = {
  done: '已完成',
  progress: '进行中',
  planned: '待开始',
}
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">ACCEPTANCE BOARD</p>
        <h2>8 个模块，一套验收标准</h2>
        <p class="muted">每个模块以 GitHub 同主题最高星项目为参考，复刻核心闭环，并交付原理、步骤、效果和可访问页面。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ modules.length }}</strong><span>模块</span></div>
        <div><strong>{{ progressCount }}</strong><span>进行中</span></div>
        <div><strong>{{ doneCount }}</strong><span>已完成</span></div>
      </div>
    </article>

    <div class="quick-links">
      <RouterLink to="/" class="quick-link">仪表盘</RouterLink>
      <RouterLink to="/tickets" class="quick-link">工单管理</RouterLink>
      <RouterLink to="/workbench" class="quick-link">API 工作台</RouterLink>
      <RouterLink to="/knowledge" class="quick-link">知识库问答</RouterLink>
      <RouterLink to="/report" class="quick-link">项目报告</RouterLink>
      <a class="quick-link" href="/docs" target="_blank" rel="noreferrer">OpenAPI 文档</a>
      <a class="quick-link" href="https://github.com/shenle2019/ai-qa-lab" target="_blank" rel="noreferrer">GitHub 仓库</a>
    </div>

    <div class="module-grid">
      <article v-for="item in modules" :key="item.id" class="module-card card">
        <div class="module-head">
          <span class="module-id">{{ item.id }}</span>
          <span class="badge" :class="`module-${item.status}`">{{ statusLabel[item.status] }}</span>
        </div>
        <h3>{{ item.name }}</h3>
        <p class="module-scope">{{ item.scope }}</p>
        <div class="module-ref">
          <a :href="item.href" target="_blank" rel="noreferrer">{{ item.reference }}</a>
          <span>★ {{ item.stars }}</span>
        </div>
        <p class="module-foot">
          <template v-if="item.report">
            验收页：<a :href="item.report" target="_blank" rel="noreferrer">打开报告</a>
          </template>
          <template v-else>验收页：{{ item.status === 'planned' ? '待上线' : '当前模块页' }}</template>
        </p>
      </article>
    </div>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>规则与交付物</h2>
          <p>2026-11-02 用户确认的复刻纪律</p>
        </div>
      </div>
      <ul class="rules">
        <li>先搜同主题 star 最高的 GitHub 项目，记录 star、license、链接和选型理由。</li>
        <li>理解后重写核心能力，不直接 fork 或整仓复制源码。</li>
        <li>复杂度下限是完整闭环：输入 → 执行 → 结果 → 可视化/报告。</li>
        <li>每个模块必须交付：可运行代码、验收网页、原理说明、使用步骤、最终效果。</li>
      </ul>
    </article>
  </section>
</template>
