<script setup>
const modules = [
  {
    id: '01',
    name: '方法论',
    reference: 'awesome-test-automation',
    stars: '7,208',
    license: '未声明',
    capability: '知识图谱、分层选型、检查表',
    status: 'done',
    href: '/ui/#/methodology',
  },
  {
    id: '02',
    name: 'Python 测试开发',
    reference: 'pytest',
    stars: '14,661',
    license: 'MIT',
    capability: '收集、fixture、参数化、marker、断言、重试、报告',
    status: 'done',
    href: '/portfolio/module-02-minipytest-report.html',
  },
  {
    id: '03',
    name: '接口自动化',
    reference: 'Hoppscotch',
    stars: '80,721',
    license: 'MIT',
    capability: '请求、环境变量、5 类断言、集合、批量运行',
    status: 'done',
    href: '/ui/#/workbench',
  },
  {
    id: '04',
    name: 'Web 自动化',
    reference: 'Playwright',
    stars: '99,087',
    license: 'Apache-2.0',
    capability: 'CDP、选择器、自动等待、断言、截图',
    status: 'done',
    href: '/portfolio/module-04-playwright-report.html',
  },
  {
    id: '05',
    name: 'App 自动化',
    reference: 'Appium',
    stars: '22,174',
    license: 'Apache-2.0',
    capability: 'ADB、UIAutomator、定位、点击、截图',
    status: 'done',
    href: '/portfolio/module-05-appium-report.html',
  },
  {
    id: '06',
    name: '性能测试',
    reference: 'k6',
    stars: '32,102',
    license: 'AGPL-3.0',
    capability: 'VU、ramp-up、P95/P99、阈值、报告',
    status: 'done',
    href: '/portfolio/module-06-load-report.html',
  },
  {
    id: '07',
    name: '测试平台',
    reference: 'MeterSphere',
    stars: '13,600',
    license: 'NOASSERTION',
    capability: '项目、用例、计划、执行、缺陷、报表',
    status: 'done',
    href: '/ui/#/platform',
  },
  {
    id: '08',
    name: 'LLM 评测',
    reference: 'DeepEval',
    stars: '19,242',
    license: 'Apache-2.0',
    capability: '数据集、裁判、指标、阈值、对比报告',
    status: 'done',
    href: '/portfolio/module-08-llm-report.html',
  },
]

const layers = [
  {
    layer: '接口层',
    when: '先做。覆盖业务规则、契约、异常和边界。',
    how: '迷你 pytest + requests + API 工作台',
    output: 'JSON/HTML 报告、状态码与响应断言',
  },
  {
    layer: 'Web 层',
    when: '关键用户路径，接口测不到的前端交互。',
    how: '迷你 Playwright（CDP）',
    output: '真实点击/填表/截图',
  },
  {
    layer: 'App 层',
    when: '移动端核心流程、启动、登录、关键页面。',
    how: '迷你 Appium（ADB/UIAutomator）',
    output: '设备操作、控件断言、截图',
  },
  {
    layer: '性能层',
    when: '上线前、大促前、接口改动后。',
    how: '迷你压测引擎（VU + 阈值）',
    output: 'RPS、P95/P99、错误率、PASS/FAIL',
  },
  {
    layer: 'LLM 层',
    when: '有模型输出、RAG、Agent 或 Prompt 改动时。',
    how: '迷你评测引擎（数据集 + 裁判 + 指标）',
    output: '相关性、忠实度、上下文指标、对比报告',
  },
]

const workflow = [
  '接需求：先写清楚“什么算坏”，再决定测什么。',
  '风险评估：钱、权限、数据、用户路径，优先测高损失的地方。',
  '选层：接口优先，Web/App 补关键路径，性能看上线，LLM 看输出。',
  '备数据：固定种子 + 随机后缀，保证可重复。',
  '自动化：一条命令跑完，失败能定位到文件行号。',
  '出报告：人看 HTML，机器看 JSON，阈值决定红绿。',
  '进回归：每次改动都跑，结果进平台，缺陷能跟踪。',
]

const checks = [
  '有没有一套可运行的 SUT，而不是 mock 一张嘴。',
  '测试数据能不能重复跑，不互相污染。',
  '失败时能不能定位到具体文件和行号。',
  '报告能不能离线打开，不依赖平台账号。',
  '关键接口有没有契约/异常/边界用例。',
  'Web/App 有没有覆盖一条真实用户路径。',
  '性能有没有 P95 和错误率阈值。',
  'LLM 有没有数据集、指标和 baseline 对比。',
  '结果能不能进测试平台，缺陷能不能关闭。',
  'CI 能不能在 push 后自动跑。',
]
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">MODULE 01 · METHODOLOGY</p>
        <h2>8 个模块，一张选型地图</h2>
        <p class="muted">
          先判断风险，再选测试层；先做接口，再补 Web/App；性能看上线，LLM 看输出。每个模块都以 GitHub 同主题最高星项目为参考，clean-room 复刻核心闭环。
        </p>
      </div>
      <div class="hero-metrics">
        <div><strong>8</strong><span>模块</span></div>
        <div><strong>5</strong><span>测试层</span></div>
        <div><strong>1</strong><span>平台闭环</span></div>
      </div>
    </article>

    <div class="quick-links">
      <RouterLink to="/portfolio" class="quick-link">模块验收</RouterLink>
      <RouterLink to="/platform" class="quick-link">测试平台</RouterLink>
      <a class="quick-link" href="/learning/" target="_blank" rel="noreferrer">学习手册</a>
      <a class="quick-link" href="https://github.com/shenle2019/ai-qa-lab" target="_blank" rel="noreferrer">GitHub 仓库</a>
    </div>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>分层选型决策树</h2>
          <p>不是所有项目都要全做。按风险和收益选层。</p>
        </div>
      </div>
      <div class="method-layers">
        <div v-for="item in layers" :key="item.layer" class="method-layer">
          <div class="method-layer-head">
            <strong>{{ item.layer }}</strong>
            <span>{{ item.how }}</span>
          </div>
          <p>{{ item.when }}</p>
          <p class="muted">产出：{{ item.output }}</p>
        </div>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>8 模块知识图谱</h2>
          <p>每个模块的参考项目、许可证和核心能力</p>
        </div>
      </div>
      <div class="module-grid">
        <a v-for="item in modules" :key="item.id" class="module-card card" :href="item.href" target="_blank" rel="noreferrer">
          <div class="module-head">
            <span class="module-id">{{ item.id }}</span>
            <span class="badge module-done">已完成</span>
          </div>
          <h3>{{ item.name }}</h3>
          <p class="module-scope">{{ item.capability }}</p>
          <div class="module-ref">
            <span>{{ item.reference }}</span>
            <span>★ {{ item.stars }} · {{ item.license }}</span>
          </div>
        </a>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>AI 协作流程</h2>
          <p>从需求到回归，每一步都有产物</p>
        </div>
      </div>
      <ol class="method-workflow">
        <li v-for="(item, index) in workflow" :key="item">
          <span>{{ String(index + 1).padStart(2, '0') }}</span>
          <p>{{ item }}</p>
        </li>
      </ol>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>落地检查表</h2>
          <p>交付前逐条过，答不上来就还没做完</p>
        </div>
      </div>
      <ul class="rules method-checks">
        <li v-for="item in checks" :key="item">{{ item }}</li>
      </ul>
    </article>
  </section>
</template>

<style scoped>
.method-layers { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.method-layer { padding: 14px 16px; border: 1px solid var(--line); border-radius: 12px; background: rgba(4, 8, 16, 0.32); }
.method-layer-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
.method-layer-head strong { font-size: 15px; }
.method-layer-head span { color: var(--accent); font-size: 11px; text-align: right; }
.method-layer p { margin: 8px 0 0; font-size: 13px; }
.method-workflow { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.method-workflow li { display: grid; grid-template-columns: 42px 1fr; gap: 10px; align-items: start; padding: 10px 12px; border: 1px solid var(--line); border-radius: 10px; background: rgba(4, 8, 16, 0.28); }
.method-workflow span { color: var(--accent); font-family: Consolas, monospace; font-size: 12px; }
.method-workflow p { margin: 0; font-size: 13px; }
.method-checks { columns: 2; column-gap: 24px; }
.method-checks li { break-inside: avoid; }
.module-card { text-decoration: none; color: inherit; }
@media (max-width: 900px) { .method-layers { grid-template-columns: 1fr; } .method-checks { columns: 1; } }
</style>
