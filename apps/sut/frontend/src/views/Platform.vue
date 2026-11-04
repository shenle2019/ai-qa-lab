<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'

const summary = ref({ projects: 0, cases: 0, plans: 0, executions: 0, defects: 0, open_defects: 0, pass_rate: 0 })
const projects = ref([])
const cases = ref([])
const plans = ref([])
const executions = ref([])
const defects = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const generating = ref(false)

const projectForm = reactive({ name: '', description: '' })
const caseForm = reactive({ project_id: null, title: '', module: 'api', priority: 'medium', steps: '', expected: '' })
const genForm = reactive({ project_id: null, requirement: '', max_cases: 5 })
const planForm = reactive({ project_id: null, name: '' })
const defectForm = reactive({ project_id: null, title: '', severity: 'medium' })

const latestExecution = computed(() => executions.value[0] || null)

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [s, p, c, pl, e, d] = await Promise.all([
      api.platformSummary(),
      api.platformProjects(),
      api.platformCases(),
      api.platformPlans(),
      api.platformExecutions(),
      api.platformDefects(),
    ])
    summary.value = s
    projects.value = p
    cases.value = c
    plans.value = pl
    executions.value = e
    defects.value = d
    if (!caseForm.project_id && p.length) caseForm.project_id = p[0].id
    if (!genForm.project_id && p.length) genForm.project_id = p[0].id
    if (!planForm.project_id && p.length) planForm.project_id = p[0].id
    if (!defectForm.project_id && p.length) defectForm.project_id = p[0].id
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function seed() {
  try {
    await api.seedPlatform()
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function createProject() {
  if (!projectForm.name.trim()) return
  try {
    await api.createPlatformProject({ name: projectForm.name.trim(), description: projectForm.description.trim() })
    projectForm.name = ''
    projectForm.description = ''
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function createCase() {
  if (!caseForm.project_id || !caseForm.title.trim()) return
  try {
    await api.createPlatformCase({ ...caseForm, title: caseForm.title.trim() })
    caseForm.title = ''
    caseForm.steps = ''
    caseForm.expected = ''
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function generateCases() {
  if (!genForm.project_id || genForm.requirement.trim().length < 10) {
    error.value = '需求描述至少 10 个字'
    return
  }
  generating.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await api.generatePlatformCases({
      project_id: genForm.project_id,
      requirement: genForm.requirement.trim(),
      max_cases: genForm.max_cases,
    })
    notice.value = `${result.model_name} 生成 ${result.cases.length} 条草稿用例（${result.prompt_version}）`
    genForm.requirement = ''
    await refresh()
  } catch (err) {
    error.value = err.message
  } finally {
    generating.value = false
  }
}

async function submitReview(item) {
  try {
    await api.submitPlatformCase(item.id)
    notice.value = `已提交审核：${item.title}`
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function reviewCase(item, decision) {
  try {
    await api.reviewPlatformCase(item.id, { decision, reviewer: 'local' })
    notice.value = decision === 'approved' ? `已通过：${item.title}` : `已驳回：${item.title}`
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function executePlan(item) {
  notice.value = `正在执行：${item.name}…`
  error.value = ''
  try {
    let execution = await api.executePlatformPlan(item.id)
    for (let index = 0; index < 60 && execution.status === 'running'; index += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1000))
      execution = await api.platformExecution(execution.id)
    }
    notice.value =
      execution.status === 'running'
        ? '执行仍在进行，请稍后刷新'
        : `执行完成：${execution.passed}/${execution.total} 通过，${execution.duration_ms} ms`
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function createPlan() {
  if (!planForm.project_id || !planForm.name.trim()) return
  try {
    await api.createPlatformPlan({ project_id: planForm.project_id, name: planForm.name.trim() })
    planForm.name = ''
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function createDefect() {
  if (!defectForm.project_id || !defectForm.title.trim()) return
  try {
    await api.createPlatformDefect({ ...defectForm, title: defectForm.title.trim() })
    defectForm.title = ''
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function closeDefect(defect) {
  try {
    await api.updatePlatformDefect(defect.id, { status: 'closed' })
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(refresh)
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">MODULE 07 · TEST PLATFORM</p>
        <h2>项目、用例、计划、执行、缺陷、报表</h2>
        <p class="muted">一个最小的持续测试平台闭环：建项目 → 写用例 → 排计划 → 看执行结果 → 记缺陷 → 看通过率。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ summary.projects }}</strong><span>项目</span></div>
        <div><strong>{{ summary.cases }}</strong><span>用例</span></div>
        <div><strong>{{ summary.plans }}</strong><span>计划</span></div>
        <div><strong>{{ summary.open_defects }}</strong><span>未关闭缺陷</span></div>
        <div><strong>{{ (summary.pass_rate * 100).toFixed(1) }}%</strong><span>通过率</span></div>
      </div>
    </article>

    <div class="toolbar card">
      <div class="filters">
        <span class="muted">平台数据保存在 SUT 的 SQLite 中</span>
      </div>
      <div class="toolbar-actions">
        <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '刷新中' : '刷新' }}</button>
        <button class="btn" @click="seed">加载演示数据</button>
      </div>
    </div>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="notice" class="alert">{{ notice }}</p>

    <div class="platform-columns">
      <article class="card">
        <div class="card-head">
          <div><h2>项目</h2><p>项目是所有用例和计划的容器</p></div>
        </div>
        <form class="platform-form" @submit.prevent="createProject">
          <input v-model="projectForm.name" placeholder="项目名称" />
          <input v-model="projectForm.description" placeholder="描述（可选）" />
          <button class="btn">新建项目</button>
        </form>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>项目</th><th>创建时间</th></tr></thead>
            <tbody>
              <tr v-for="item in projects" :key="item.id">
                <td class="mono">#{{ item.id }}</td>
                <td><strong>{{ item.name }}</strong><p class="cell-sub">{{ item.description }}</p></td>
                <td class="muted">{{ formatTime(item.created_at) }}</td>
              </tr>
              <tr v-if="!projects.length"><td colspan="3" class="empty">还没有项目。</td></tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card">
        <div class="card-head">
          <div><h2>用例</h2><p>手工新建直接可用；AI 生成需审核</p></div>
        </div>
        <div class="gen-panel">
          <p class="cell-sub">输入需求，生成结构化草稿用例；通过审核后才允许执行。</p>
          <form class="platform-form" @submit.prevent="generateCases">
            <select v-model.number="genForm.project_id">
              <option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
            <textarea v-model="genForm.requirement" rows="3" placeholder="粘贴需求或接口说明（至少 10 字）"></textarea>
            <input v-model.number="genForm.max_cases" type="number" min="1" max="20" style="max-width: 90px" title="最多生成条数" />
            <button class="btn" :disabled="generating">{{ generating ? '生成中…' : 'AI 生成用例' }}</button>
          </form>
        </div>
        <form class="platform-form" @submit.prevent="createCase">
          <select v-model.number="caseForm.project_id">
            <option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
          <input v-model="caseForm.title" placeholder="用例标题" />
          <select v-model="caseForm.module">
            <option value="api">API</option><option value="web">Web</option><option value="app">App</option><option value="perf">性能</option>
          </select>
          <select v-model="caseForm.priority">
            <option value="low">低</option><option value="medium">中</option><option value="high">高</option>
          </select>
          <button class="btn">新建用例</button>
        </form>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>用例</th><th>模块</th><th>优先级</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="item in cases" :key="item.id">
                <td class="mono">#{{ item.id }}</td>
                <td>
                  <strong>{{ item.title }}</strong>
                  <p class="cell-sub">{{ item.expected }}</p>
                  <p v-if="item.source === 'ai'" class="cell-sub">AI · {{ item.prompt_version }}</p>
                </td>
                <td>{{ item.module }}</td>
                <td>{{ item.priority }}</td>
                <td><span class="badge" :class="item.status === 'approved' ? 'module-done' : 'module-planned'">{{ item.status }}</span></td>
                <td class="row-actions">
                  <button v-if="item.status === 'draft'" class="btn ghost" @click="submitReview(item)">提交审核</button>
                  <template v-else-if="item.status === 'pending_review'">
                    <button class="btn ghost" @click="reviewCase(item, 'approved')">通过</button>
                    <button class="btn ghost" @click="reviewCase(item, 'rejected')">驳回</button>
                  </template>
                  <span v-else class="muted">-</span>
                </td>
              </tr>
              <tr v-if="!cases.length"><td colspan="6" class="empty">还没有用例。</td></tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card">
        <div class="card-head">
          <div><h2>计划</h2><p>执行本项目已审核通过的用例</p></div>
        </div>
        <form class="platform-form" @submit.prevent="createPlan">
          <select v-model.number="planForm.project_id">
            <option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
          <input v-model="planForm.name" placeholder="计划名称" />
          <button class="btn">新建计划</button>
        </form>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>计划</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="item in plans" :key="item.id">
                <td class="mono">#{{ item.id }}</td>
                <td>{{ item.name }}</td>
                <td><span class="badge" :class="item.status === 'failed' ? 'module-planned' : 'module-done'">{{ item.status }}</span></td>
                <td class="muted">{{ formatTime(item.created_at) }}</td>
                <td><button class="btn ghost" @click="executePlan(item)">执行</button></td>
              </tr>
              <tr v-if="!plans.length"><td colspan="5" class="empty">还没有计划。</td></tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card">
        <div class="card-head">
          <div><h2>最近执行</h2><p>通过/失败/跳过与耗时</p></div>
          <a v-if="latestExecution" class="btn ghost" :href="`/api/platform/executions/${latestExecution.id}/report`" target="_blank" rel="noreferrer">查看报告</a>
        </div>
        <div v-if="latestExecution" class="execution-summary">
          <div><span>状态</span><strong>{{ latestExecution.status }}</strong></div>
          <div><span>总数</span><strong>{{ latestExecution.total }}</strong></div>
          <div><span>通过</span><strong>{{ latestExecution.passed }}</strong></div>
          <div><span>失败</span><strong>{{ latestExecution.failed }}</strong></div>
          <div><span>跳过</span><strong>{{ latestExecution.skipped }}</strong></div>
          <div><span>耗时</span><strong>{{ latestExecution.duration_ms }} ms</strong></div>
        </div>
        <div class="table-wrap" style="margin-top:12px">
          <table>
            <thead><tr><th>执行</th><th>结果</th><th>耗时</th></tr></thead>
            <tbody>
              <tr v-for="item in (latestExecution?.results || [])" :key="item.id">
                <td>{{ item.case_name }}</td>
                <td><span class="badge" :class="item.status === 'passed' ? 'module-done' : 'module-planned'">{{ item.status }}</span></td>
                <td>{{ item.duration_ms }} ms</td>
              </tr>
              <tr v-if="!latestExecution"><td colspan="3" class="empty">还没有执行记录。</td></tr>
            </tbody>
          </table>
        </div>
      </article>
    </div>

    <article class="card">
      <div class="card-head">
        <div><h2>缺陷</h2><p>失败用例可以转成缺陷并跟踪关闭</p></div>
      </div>
      <form class="platform-form" @submit.prevent="createDefect">
        <select v-model.number="defectForm.project_id">
          <option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <input v-model="defectForm.title" placeholder="缺陷标题" />
        <select v-model="defectForm.severity">
          <option value="low">低</option><option value="medium">中</option><option value="high">高</option><option value="critical">严重</option>
        </select>
        <button class="btn">新建缺陷</button>
      </form>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>缺陷</th><th>严重度</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in defects" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td>{{ item.title }}</td>
              <td>{{ item.severity }}</td>
              <td><span class="badge" :class="item.status === 'open' ? 'module-planned' : 'module-done'">{{ item.status }}</span></td>
              <td><button v-if="item.status === 'open'" class="btn ghost" @click="closeDefect(item)">关闭</button></td>
            </tr>
            <tr v-if="!defects.length"><td colspan="5" class="empty">还没有缺陷。</td></tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<style scoped>
.platform-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.platform-form { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.platform-form input, .platform-form select, .platform-form textarea { min-width: 120px; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
.platform-form textarea { flex: 1 1 100%; font-family: inherit; resize: vertical; }
.gen-panel { margin: 10px 0 4px; padding: 10px 12px; border: 1px dashed var(--line); border-radius: 10px; }
.row-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.execution-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.execution-summary div { padding: 10px 12px; border: 1px solid var(--line); border-radius: 10px; background: rgba(4, 8, 16, 0.35); }
.execution-summary span { display: block; color: var(--muted); font-size: 11px; }
.execution-summary strong { font-size: 18px; }
@media (max-width: 980px) { .platform-columns { grid-template-columns: 1fr; } .execution-summary { grid-template-columns: 1fr 1fr; } }
</style>
