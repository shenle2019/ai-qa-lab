<script setup>
const timeline = [
  {
    time: '17:02',
    title: '项目启动',
    detail: '在 E:\\ailearning\\ai-qa-lab 建立 monorepo、CLAUDE.md、目录约定和 Python 3.11 环境。',
  },
  {
    time: '17:10',
    title: 'SUT 后端最小闭环',
    detail: 'FastAPI + SQLAlchemy + SQLite，健康检查、工单 CRUD、知识库 mock，6 个 pytest 用例通过。',
  },
  {
    time: '17:13',
    title: '公开仓库与 CI',
    detail: '创建 shenle2019/ai-qa-lab，推送 main；GitHub Actions 跑 pytest。HTTPS 被阻断后改用 SSH 443。',
  },
  {
    time: '17:30',
    title: '接口自动化套件',
    detail: 'suites/api 黑盒测试，覆盖健康检查、契约、CRUD、异常/边界、知识库 mock，22 个用例通过。',
  },
  {
    time: '18:00',
    title: '模块复刻规则与选型',
    detail: '记录“最高星项目复刻 + 完整闭环 + 验收网页”规则，产出 8 模块选型矩阵。',
  },
  {
    time: '18:20',
    title: 'SUT 控制台',
    detail: 'Vue 3 + Vite + Pinia + Router + ECharts，仪表盘、工单、知识库、模块验收 4 个页面。',
  },
  {
    time: '18:40',
    title: '模块 03 复刻 v0.1',
    detail: 'Hoppscotch 风格 API 工作台：请求构建、环境变量、5 类断言、集合、批量运行与报告。',
  },
  {
    time: '11-03',
    title: '模块 02 迷你 pytest',
    detail: '自研收集器、fixture、参数化、marker、断言内省、重试、JSON/HTML 报告；33 个元测试 + 20 个演示用例。',
  },
  {
    time: '11-03',
    title: '模块 04 迷你 Playwright',
    detail: 'CDP 驱动 Edge、选择器、自动等待、断言、截图；6 个元测试 + 5 个 SUT UI 用例。',
  },
  {
    time: '11-03',
    title: '模块 05 迷你 Appium',
    detail: 'ADB/UIAutomator 驱动 Android Settings：元素定位、点击、等待、截图；5 个元测试 + 3 个演示用例。',
  },
  {
    time: '11-03',
    title: '模块 06 迷你压测',
    detail: 'VU 并发、ramp-up、P95/P99、错误率、阈值判定、离线 HTML；8239 次请求，1371 RPS，P95 21ms。',
  },
  {
    time: '11-03',
    title: '模块 07 测试平台',
    detail: '项目、用例、计划、执行、缺陷、报表闭环；17 个平台 API，支持导入迷你 pytest 报告。',
  },
  {
    time: '11-03',
    title: '模块 08 LLM 评测',
    detail: '数据集、Mock/DeepSeek 裁判、相关性/忠实度/上下文指标、阈值、baseline vs candidate；5 条数据 0.52→0.72。',
  },
  {
    time: '11-03',
    title: '模块 01 方法论',
    detail: '8 模块知识图谱、5 层选型决策树、7 步协作流程、10 条检查表；页面 /ui/#/methodology。',
  },
  {
    time: '11-03',
    title: 'CRUD 用例扩充',
    detail: '接口 29 + Web 28 + App 24 + 平台 26，共 107 个新增用例；全部记录到 CRUD 测试报告。',
  },
  {
    time: '11-04',
    title: '平台闭环',
    detail: '模型中心、AI 生成用例、审核门禁、服务端真实执行、HTML 报告；341 个 pytest 用例通过。',
  },
]

const metrics = [
  { value: '383', label: 'pytest 用例' },
  { value: '58', label: '迷你演示' },
  { value: '8', label: '模块选型' },
  { value: '8', label: '复刻闭环' },
]

const endpoints = [
  ['GET', '/health', '健康检查'],
  ['GET', '/api/tickets', '工单列表'],
  ['POST', '/api/tickets', '创建工单'],
  ['GET', '/api/tickets/{id}', '查询单个工单'],
  ['PATCH', '/api/tickets/{id}', '更新状态/优先级'],
  ['POST', '/api/kb/query', '知识库问答（mock）'],
  ['POST', '/api/workbench/send', 'API 工作台单请求'],
  ['POST', '/api/workbench/run', 'API 工作台批量运行'],
]

const faqs = [
  {
    q: '1. 学习页标题为什么改了？',
    a: '从 “AI QA Lab” 改成 “AI全栈测试开发平台-shenle”，只改显示名，内容和仓库名不变。',
  },
  {
    q: '2. SUT 在哪里，我能看见吗？',
    a: '代码在 apps/sut/backend 和 apps/sut/frontend；界面看 /ui/，接口看 /docs，现在共 9 个 HTTP 接口。',
  },
  {
    q: '3. 模块 03 接口自动化学的是什么？',
    a: '参考 Hoppscotch，复刻了请求、环境变量、5 种断言、集合、批量运行和报告；入口 /ui/#/workbench。',
  },
  {
    q: '4. 模块 01 方法论是什么？',
    a: '参考 awesome-test-automation，先确定 8 个模块、最高星参考项目和复刻规则；产物是选型矩阵和 CLAUDE.md。',
  },
  {
    q: '5. 模块 07 测试平台现在有什么？',
    a: '项目、用例、计划、执行、缺陷和汇总已可用；支持 AI 生成用例、审核门禁、服务端真实执行和 HTML 报告；未做定时调度与分布式执行。',
  },
]
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">PROJECT REPORT · 2026-11-03</p>
        <h2>从零搭起一套可运行、可测试、可复刻的 AI 全栈测试工程</h2>
        <p class="muted">
          这份报告回答四个问题：做了什么、原理是什么、步骤是什么、最后成果是什么，以及它能否脱离本地在公网运行。
        </p>
      </div>
      <div class="hero-metrics">
        <div v-for="item in metrics" :key="item.label">
          <strong>{{ item.value }}</strong><span>{{ item.label }}</span>
        </div>
      </div>
    </article>

    <div class="quick-links">
      <a class="quick-link" href="https://github.com/shenle2019/ai-qa-lab" target="_blank" rel="noreferrer">GitHub 仓库</a>
      <a class="quick-link" href="/docs" target="_blank" rel="noreferrer">OpenAPI</a>
      <RouterLink to="/portfolio" class="quick-link">模块验收</RouterLink>
      <RouterLink to="/workbench" class="quick-link">API 工作台</RouterLink>
      <a class="quick-link" href="/learning/" target="_blank" rel="noreferrer">完整学习手册</a>
      <a class="quick-link" href="https://shenle2019.github.io/ai-qa-lab/reports/" target="_blank" rel="noreferrer">历史报告归档</a>
      <a class="quick-link" href="/portfolio/test-report-2026-11-03.html" target="_blank" rel="noreferrer">CRUD 测试报告</a>
    </div>

    <article class="hero card">
      <div>
        <p class="eyebrow">BEGINNER WALKTHROUGH</p>
        <h2>新手向完整拆解</h2>
        <p class="muted">每一步做了什么、为什么、涉及哪些测试开发名词、原理是什么、效果是什么；含术语速查、实现说明和 25 道自测题。</p>
      </div>
      <div class="learning-actions">
        <a class="btn" href="/learning/" target="_blank" rel="noreferrer">打开学习手册</a>
        <a class="btn ghost" href="https://shenle2019.github.io/ai-qa-lab/learning/" target="_blank" rel="noreferrer">公网版</a>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>一、我做了什么</h2>
          <p>按时间线归档，每一步都有可验证产物</p>
        </div>
      </div>
      <ol class="timeline">
        <li v-for="item in timeline" :key="item.time">
          <span class="timeline-time">{{ item.time }}</span>
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
          </div>
        </li>
      </ol>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>二、原理是什么</h2>
          <p>一条数据流，三个层次</p>
        </div>
      </div>
      <pre class="report-diagram">Browser (Vue 3 SPA)
  ├─ 仪表盘 / 工单 / 知识库 / API 工作台 / 项目报告
  └─ fetch /api/*
        │
        ▼
FastAPI (apps/sut/backend)
  ├─ /health, /api/tickets, /api/kb/query
  ├─ /api/workbench/send, /api/workbench/run
  └─ /ui ← Vue 构建产物（同源托管）
        │
        ▼
SQLAlchemy → SQLite</pre>
      <ul class="rules">
        <li><strong>统一被测系统：</strong>前端和后端都围绕同一套工单/知识库数据，接口测试与 UI 测试覆盖同一条链路。</li>
        <li><strong>分层测试：</strong>后端冒烟、接口黑盒、工作台契约测试各自独立；测试库用临时 SQLite，数据随机后缀隔离。</li>
        <li><strong>API 工作台：</strong>浏览器只负责编辑请求；FastAPI 用 httpx 代理发送，解决 CORS，统一超时和断言求值。</li>
        <li><strong>复刻方法：</strong>先搜同主题最高星项目，记录 star/license/链接，再 clean-room 重写核心闭环，不 fork、不复制源码。</li>
        <li><strong>同源部署：</strong>前端构建产物由 FastAPI 在 /ui 挂载，生产环境只需要一个容器/端口。</li>
      </ul>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>三、步骤是什么</h2>
          <p>从零到验收的完整命令</p>
        </div>
      </div>
      <div class="report-steps">
        <div>
          <h3>本地启动</h3>
          <pre class="response-body">cd /e/ailearning/ai-qa-lab
bash scripts/start_sut.sh</pre>
        </div>
        <div>
          <h3>跑测试</h3>
          <pre class="response-body">./.venv/Scripts/python.exe -m pytest apps/sut/backend suites/api libs/minipytest/tests libs/miniplaywright/tests -q</pre>
        </div>
        <div>
          <h3>验收页面</h3>
          <pre class="response-body">/ui/               仪表盘
/ui/#/tickets      工单管理
/ui/#/workbench    API 工作台
/ui/#/report       本项目报告
/ui/#/portfolio    模块验收</pre>
        </div>
        <div>
          <h3>部署</h3>
          <pre class="response-body">docker build -t ai-qa-lab .
docker run -p 8000:8000 ai-qa-lab
# 或 Render Blueprint：render.yaml</pre>
        </div>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>四、最后成果是什么</h2>
          <p>代码、页面、测试、文档、部署配置</p>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>产物</th><th>位置</th><th>状态</th></tr></thead>
          <tbody>
            <tr><td>SUT 后端</td><td class="mono">apps/sut/backend</td><td>可运行，9 个接口（7 业务 + 2 工作台）</td></tr>
            <tr><td>Vue 控制台</td><td class="mono">apps/sut/frontend</td><td>9 个页面，已构建</td></tr>
            <tr><td>接口套件</td><td class="mono">suites/api</td><td>56 tests passing</td></tr>
            <tr><td>API 工作台</td><td class="mono">/ui/#/workbench</td><td>闭环可用</td></tr>
            <tr><td>迷你 Playwright</td><td class="mono">libs/miniplaywright</td><td>6 元测试 + 33 个 SUT UI 用例</td></tr>
            <tr><td>迷你 Appium</td><td class="mono">libs/miniappium</td><td>29 元测试 + 3 个 Settings 用例</td></tr>
            <tr><td>迷你压测</td><td class="mono">libs/miniload</td><td>5 元测试 + 1 次 SUT 压测；P95 21ms</td></tr>
            <tr><td>测试平台</td><td class="mono">/ui/#/platform</td><td>项目/用例/计划/执行/缺陷/报表；38 backend tests</td></tr>
            <tr><td>CRUD 测试报告</td><td class="mono">docs/portfolio/test-report-2026-11-03.html</td><td>107 个新增用例</td></tr>
            <tr><td>LLM 评测</td><td class="mono">libs/minieval</td><td>5 元测试 + 5 条数据；0.52→0.72</td></tr>
            <tr><td>方法论</td><td class="mono">/ui/#/methodology</td><td>8 模块图谱 + 5 层选型 + 检查表</td></tr>
            <tr><td>复刻矩阵</td><td class="mono">docs/requirements/module-matrix.md</td><td>8 模块选型完成</td></tr>
            <tr><td>验收材料</td><td class="mono">docs/portfolio</td><td>报告 + 截图</td></tr>
            <tr><td>CI</td><td class="mono">.github/workflows/ci.yml</td><td>GitHub Actions</td></tr>
            <tr><td>容器部署</td><td class="mono">Dockerfile / render.yaml</td><td>待平台授权</td></tr>
          </tbody>
        </table>
      </div>
      <div class="endpoint-grid">
        <div v-for="item in endpoints" :key="item[1]" class="endpoint-item">
          <span class="method-tag">{{ item[0] }}</span>
          <span class="mono">{{ item[1] }}</span>
          <span class="muted">{{ item[2] }}</span>
        </div>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>五、能否在远端公网访问运行</h2>
          <p>能，但要区分“静态报告”和“完整后端”</p>
        </div>
      </div>
      <div class="alert" style="border: 1px solid rgba(52, 211, 153, 0.28); color: #a7f3d0; background: rgba(52, 211, 153, 0.08)">
        结论：完整项目可以部署到公网；GitHub Pages 只能托管静态报告，FastAPI 后端需要容器平台（Render / Hugging Face Spaces / 任何 Docker 主机）。
      </div>
      <p class="muted">已部署到 Railway（Docker），公网地址：https://ai-qa-lab-production.up.railway.app/ui/；静态报告仍在 GitHub Pages。</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>方式</th><th>能运行什么</th><th>是否需要账号</th><th>当前状态</th></tr></thead>
          <tbody>
            <tr><td>GitHub Pages</td><td>项目报告、截图、文档</td><td>已有 GitHub</td><td>可立即部署</td></tr>
            <tr><td>Railway Docker</td><td>完整 SUT + Vue + 模型中心 + 执行报告</td><td>已有账号</td><td>已上线</td></tr>
            <tr><td>Hugging Face Spaces</td><td>完整应用</td><td>需要 HF 账号</td><td>备选（当前网络不可达）</td></tr>
            <tr><td>本地</td><td>全部功能</td><td>无</td><td>已运行</td></tr>
          </tbody>
        </table>
      </div>
      <p class="muted">
        部署配置已写入仓库：<span class="mono">Dockerfile</span>、<span class="mono">render.yaml</span>、<span class="mono">.dockerignore</span>。
        启动时通过 <span class="mono">SEED_DEMO=1</span> 自动写入演示工单；数据库为 SQLite，免费平台的临时磁盘在重启后会重置，适合演示环境。
      </p>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>六、五个常见问题</h2>
          <p>2026-11-03 验收问答</p>
        </div>
      </div>
      <ul class="rules">
        <li v-for="item in faqs" :key="item.q">
          <strong>{{ item.q }}</strong> {{ item.a }}
        </li>
      </ul>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>七、边界与下一步</h2>
          <p>如实记录，不夸大</p>
        </div>
      </div>
      <ul class="rules">
        <li>当前没有登录/权限体系；模块 07 复刻 MeterSphere 时补。</li>
        <li>知识库仍是 mock；模块 08 接入 DeepSeek + 真实检索与评测。</li>
        <li>API 工作台只做 REST，不做 GraphQL/WebSocket/请求链路变量提取。</li>
        <li>SQLite 适合演示，不适合多用户生产；后续可切 PostgreSQL。</li>
        <li>完整应用已部署到 Railway；静态报告在 GitHub Pages。</li>
      </ul>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>八、新手向：这个项目怎么一步步做出来</h2>
          <p>每一步：做了什么 → 为什么 → 名词解释 → 原理 → 效果</p>
        </div>
      </div>
      <p class="muted">完整拆解已单独成页，包含 10+ 个步骤、术语速查表、实现说明和 13 道自测题。</p>
      <div class="quick-links" style="margin-top:16px">
        <a class="quick-link" href="https://shenle2019.github.io/ai-qa-lab/learning/" target="_blank" rel="noreferrer">打开完整学习手册</a>
        <a class="quick-link" href="https://shenle2019.github.io/ai-qa-lab/reports/" target="_blank" rel="noreferrer">历史报告归档</a>
      <a class="quick-link" href="/portfolio/test-report-2026-11-03.html" target="_blank" rel="noreferrer">CRUD 测试报告</a>
      </div>
      <ul class="rules" style="margin-top:14px">
        <li>第 1–2 步：定目标和验收标准、搭仓库与环境。</li>
        <li>第 3–5 步：造 SUT、写冒烟测试、做接口自动化。</li>
        <li>第 6–7 步：做 Vue 控制台、复刻 Hoppscotch API 工作台。</li>
        <li>第 8–10 步：CI 与截图、报告归档、本地/远端部署。</li>
        <li>核心原则：测试金字塔、测试隔离、黑盒/契约测试、CORS 代理、不可变快照。</li>
      </ul>
    </article>
  </section>
</template>
