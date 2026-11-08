<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import EmptyState from '../../components/EmptyState.vue'
import { pickProject, saveProjectId } from '../../utils/project'

const PROJECT_KEY = 'aiqa.ui.project'

const projects = ref([])
const projectId = ref(null)
const tab = ref('explore')
const loading = ref(false)
const error = ref('')
const notice = ref('')
const browserReady = ref(null)

async function probeBrowser() {
  try {
    const body = await api.health()
    browserReady.value = body?.ui_automation !== false
  } catch {
    browserReady.value = null
  }
}

const cases = ref([])
const runs = ref([])

const form = reactive({
  url: 'http://127.0.0.1:8000/ui/#/projects',
  goal: '打开项目管理页，确认页面顶部出现「项目管理」标题',
  env: '{}',
})

const explored = ref(null)
const exploreBusy = ref(false)

const chat = reactive({ url: 'http://127.0.0.1:8000/ui/#/projects', question: '', reply: '', busy: false })

const editing = ref(null)
const editForm = reactive({ title: '', module: '', base_url: '', env: '{}', steps: '[]', status: 'draft' })
const editBusy = ref(false)

const scriptView = ref(null)
const runDrawer = ref(null)

const statusText = { draft: '草稿', ready: '已就绪', archived: '已归档' }
const runText = { passed: '通过', failed: '失败', running: '执行中' }

const readyCount = computed(() => cases.value.filter((item) => item.status === 'ready').length)
const passRate = computed(() => {
  const recent = runs.value.slice(0, 20)
  if (!recent.length) return '—'
  const passed = recent.filter((item) => item.status === 'passed').length
  return `${Math.round((passed / recent.length) * 100)}%`
})

function parseJson(text, fallback) {
  try {
    return JSON.parse(text)
  } catch (exc) {
    return fallback
  }
}

function loadProjects() {
  return api.platformProjects().then((rows) => {
    projects.value = rows
    projectId.value = pickProject(rows, PROJECT_KEY)?.id ?? null
  })
}

function onProjectChange() {
  saveProjectId(projectId.value, PROJECT_KEY)
  refresh()
}

function refresh() {
  if (!projectId.value) return Promise.resolve()
  loading.value = true
  error.value = ''
  return Promise.all([
    api.uiCases(projectId.value).then((rows) => { cases.value = rows }),
    api.uiRuns(projectId.value, 30).then((rows) => { runs.value = rows }),
  ])
    .catch((exc) => { error.value = exc.message })
    .finally(() => { loading.value = false })
}

async function explore() {
  error.value = ''
  notice.value = ''
  if (!form.goal.trim()) {
    error.value = '请先写清楚要验证什么'
    return
  }
  exploreBusy.value = true
  try {
    const result = await api.exploreUi({
      project_id: projectId.value,
      url: form.url,
      goal: form.goal,
      env: parseJson(form.env, {}),
      save: true,
    })
    explored.value = result
    notice.value = `已保存为草稿用例 #${result.case?.id ?? '?'}`
    await refresh()
  } catch (exc) {
    error.value = exc.message
  } finally {
    exploreBusy.value = false
  }
}

async function runCase(item) {
  error.value = ''
  notice.value = ''
  try {
    const result = await api.runUiCase(item.id)
    notice.value = `用例 #${item.id} ${runText[result.status] || result.status}，耗时 ${result.duration_ms} ms`
    await refresh()
    if (result.error) error.value = result.error
  } catch (exc) {
    error.value = exc.message
  }
}

async function showScript(item) {
  error.value = ''
  try {
    scriptView.value = await api.uiCaseScript(item.id)
  } catch (exc) {
    error.value = exc.message
  }
}

async function showRun(item) {
  error.value = ''
  try {
    runDrawer.value = await api.uiRun(item.id)
  } catch (exc) {
    error.value = exc.message
  }
}

function openEdit(item) {
  editing.value = item
  editForm.title = item.title
  editForm.module = item.module
  editForm.base_url = item.base_url
  editForm.env = JSON.stringify(item.env || {}, null, 2)
  editForm.steps = JSON.stringify(item.steps || [], null, 2)
  editForm.status = item.status
}

async function saveEdit() {
  editBusy.value = true
  error.value = ''
  try {
    await api.updateUiCase(editing.value.id, {
      title: editForm.title,
      module: editForm.module,
      base_url: editForm.base_url,
      env: parseJson(editForm.env, {}),
      steps: parseJson(editForm.steps, []),
      status: editForm.status,
    })
    editing.value = null
    notice.value = '已保存'
    await refresh()
  } catch (exc) {
    error.value = exc.message
  } finally {
    editBusy.value = false
  }
}

async function removeCase(item) {
  if (!window.confirm(`删除用例 #${item.id}「${item.title}」？`)) return
  error.value = ''
  try {
    await api.deleteUiCase(item.id)
    notice.value = '已删除'
    await refresh()
  } catch (exc) {
    error.value = exc.message
  }
}

async function askChat() {
  if (!chat.question.trim()) return
  chat.busy = true
  chat.reply = ''
  error.value = ''
  try {
    const result = await api.uiChat({ url: chat.url, question: chat.question })
    chat.reply = result.reply
  } catch (exc) {
    error.value = exc.message
  } finally {
    chat.busy = false
  }
}

function envSummary(item) {
  const keys = Object.keys(item.env || {})
  return keys.length ? `${keys.length} 个变量` : '不注入'
}

function fmtTime(value) {
  if (!value) return ''
  return (value || '').replace('T', ' ').slice(0, 19)
}

onMounted(async () => {
  probeBrowser()
  try {
    await loadProjects()
    await refresh()
  } catch (exc) {
    error.value = exc.message
  }
})
</script>

<template>
  <section class="stack">
    <header class="hero">
      <div>
        <p class="eyebrow">UI AUTOMATION</p>
        <h1>UI 自动化</h1>
        <p class="muted">
          AI 打开页面抓快照生成可执行步骤；Playwright 真跑，环境变量注入 localStorage 免登录，失败留截图。
        </p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ cases.length }}</strong><span>UI 用例</span></div>
        <div><strong>{{ readyCount }}</strong><span>已就绪</span></div>
        <div><strong>{{ passRate }}</strong><span>近 20 次通过率</span></div>
      </div>
    </header>

    <div class="toolbar">
      <select v-model="projectId" @change="onProjectChange">
        <option v-for="item in projects" :key="item.id" :value="item.id">#{{ item.id }} {{ item.name }}</option>
      </select>
      <button class="btn ghost" :disabled="loading" @click="refresh">刷新</button>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="notice" class="alert ok">{{ notice }}</p>
    <p v-if="browserReady === false" class="alert">
      当前部署环境没有安装 Playwright 浏览器，AI 探索和执行会返回 503。本机可用时请先执行
      <code>playwright install chromium</code>。
    </p>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'explore' }" @click="tab = 'explore'">AI 探索</button>
      <button class="tab" :class="{ active: tab === 'cases' }" @click="tab = 'cases'">UI 用例</button>
      <button class="tab" :class="{ active: tab === 'runs' }" @click="tab = 'runs'">执行记录</button>
    </div>

    <!-- AI explore -->
    <div v-if="tab === 'explore'" class="stack">
      <div class="split-grid">
        <article class="card">
          <div class="card-head">
            <div>
              <h2>探索生成用例</h2>
              <p class="muted">输入一个页面和一条测试目标，AI 会先抓快照再写步骤。</p>
            </div>
          </div>
          <div class="form-stack">
            <label>页面地址<input v-model="form.url" placeholder="http://127.0.0.1:8000/ui/#/projects" /></label>
            <label>测试目标
              <textarea v-model="form.goal" rows="3" placeholder="例如：打开知识库页面，确认有「试检索」入口" />
            </label>
            <label>环境注入（localStorage JSON，可留空）
              <textarea v-model="form.env" rows="3" class="mono" placeholder='{"token":"abc"}' />
            </label>
            <div class="form-actions">
              <button class="btn" :disabled="exploreBusy" @click="explore">
                {{ exploreBusy ? '抓页面并生成中…' : 'AI 生成用例' }}
              </button>
              <span class="muted">生成后会直接存为草稿</span>
            </div>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div>
              <h2>生成结果</h2>
              <p class="muted">{{ explored ? `${explored.title} · ${explored.nodes} 个可交互元素` : '还没有生成结果。' }}</p>
            </div>
          </div>
          <template v-if="explored">
            <p v-if="explored.reasoning" class="reasoning">{{ explored.reasoning }}</p>
            <ol class="step-list">
              <li v-for="(step, index) in explored.steps" :key="index">
                <span class="step-action">{{ step.action }}</span>
                <code>{{ step.target || step.value || step.ms }}</code>
                <span v-if="step.value && step.target" class="muted">→ {{ step.value }}</span>
              </li>
            </ol>
          </template>
          <p v-else class="empty">生成后这里会列出每一步动作。</p>
        </article>
      </div>

      <article class="card">
        <div class="card-head">
          <div>
            <h2>自由对话</h2>
            <p class="muted">就当前页面问一句话，AI 看着真实页面回答。</p>
          </div>
        </div>
        <div class="chat-row">
          <input v-model="chat.url" class="mono" placeholder="页面地址" />
          <input v-model="chat.question" placeholder="这个页面上有哪些功能区域？" @keyup.enter="askChat" />
          <button class="btn" :disabled="chat.busy" @click="askChat">{{ chat.busy ? '思考中…' : '提问' }}</button>
        </div>
        <p v-if="chat.reply" class="reply">{{ chat.reply }}</p>
      </article>
    </div>

    <!-- cases -->
    <article v-if="tab === 'cases'" class="card">
      <div class="card-head">
        <div>
          <h2>UI 用例</h2>
          <p class="muted">共 {{ cases.length }} 条，AI 生成的默认是草稿。</p>
        </div>
        <button class="btn ghost" @click="refresh">刷新</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>名称</th><th>模块</th><th>环境注入</th><th>脚本</th><th>状态</th>
              <th>来源</th><th>创建时间</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in cases" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td>{{ item.title }}</td>
              <td>{{ item.module }}</td>
              <td>{{ envSummary(item) }}</td>
              <td>{{ (item.steps || []).length }} 步</td>
              <td><span class="badge" :class="item.status === 'ready' ? 'badge-green' : ''">{{ statusText[item.status] || item.status }}</span></td>
              <td>{{ item.source === 'ai' ? 'AI' : '手工' }}</td>
              <td class="muted">{{ fmtTime(item.created_at) }}</td>
              <td class="row-actions">
                <button class="btn ghost tiny" @click="openEdit(item)">编辑</button>
                <button class="btn ghost tiny" @click="runCase(item)">执行</button>
                <button class="btn ghost tiny" @click="showScript(item)">脚本</button>
                <button class="btn ghost tiny danger" @click="removeCase(item)">删除</button>
              </td>
            </tr>
            <tr v-if="!cases.length">
              <td colspan="9">
                <EmptyState
                  icon="ui"
                  title="还没有 UI 用例"
                  hint="给页面地址和一句目标，AI 会抓快照生成可执行的 Playwright 步骤。"
                >
                  <template #action>
                    <button class="btn tiny" type="button" @click="tab = 'explore'">去 AI 探索</button>
                  </template>
                </EmptyState>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>

    <!-- runs -->
    <article v-if="tab === 'runs'" class="card">
      <div class="card-head">
        <div>
          <h2>执行记录</h2>
          <p class="muted">最近 {{ runs.length }} 条，失败会自动留截图。</p>
        </div>
        <button class="btn ghost" @click="refresh">刷新</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>用例</th><th>结果</th><th>耗时</th><th>步骤</th><th>时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in runs" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td>{{ item.title }}</td>
              <td>
                <span class="badge" :class="item.status === 'passed' ? 'badge-green' : 'badge-red'">
                  {{ runText[item.status] || item.status }}
                </span>
              </td>
              <td>{{ item.duration_ms }} ms</td>
              <td>{{ (item.steps || []).length }} 步</td>
              <td class="muted">{{ fmtTime(item.created_at) }}</td>
              <td class="row-actions"><button class="btn ghost tiny" @click="showRun(item)">详情</button></td>
            </tr>
            <tr v-if="!runs.length"><td colspan="7" class="empty">还没有执行记录。</td></tr>
          </tbody>
        </table>
      </div>
    </article>

    <!-- edit modal -->
    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal wide">
        <header>
          <h2>编辑用例 #{{ editing.id }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="editing = null">关闭</button>
        </header>
        <p v-if="error" class="alert modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label>名称<input v-model="editForm.title" /></label>
          <div class="form-row">
            <label>模块<input v-model="editForm.module" /></label>
            <label>状态
              <select v-model="editForm.status">
                <option value="draft">草稿</option>
                <option value="ready">已就绪</option>
                <option value="archived">已归档</option>
              </select>
            </label>
          </div>
          <label>Base URL<input v-model="editForm.base_url" class="mono" /></label>
          <label>环境注入（localStorage）<textarea v-model="editForm.env" rows="3" class="mono" /></label>
          <label>步骤（JSON 数组）<textarea v-model="editForm.steps" rows="10" class="mono" /></label>
          <div class="form-actions">
            <button class="btn" :disabled="editBusy" @click="saveEdit">{{ editBusy ? '保存中…' : '保存' }}</button>
            <button class="btn ghost" @click="editing = null">取消</button>
          </div>
        </div>
      </div>
    </div>

    <!-- script modal -->
    <div v-if="scriptView" class="modal-mask" @click.self="scriptView = null">
      <div class="modal wide">
        <header>
          <h2>{{ scriptView.title }} · 脚本</h2>
          <button class="btn ghost tiny" data-modal-close @click="scriptView = null">关闭</button>
        </header>
        <pre class="script">{{ scriptView.script }}</pre>
      </div>
    </div>

    <!-- run drawer -->
    <div v-if="runDrawer" class="modal-mask" @click.self="runDrawer = null">
      <div class="modal wide">
        <header>
          <h2>#{{ runDrawer.id }} {{ runDrawer.title }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="runDrawer = null">关闭</button>
        </header>
        <p class="muted">
          <span class="badge" :class="runDrawer.status === 'passed' ? 'badge-green' : 'badge-red'">
            {{ runText[runDrawer.status] || runDrawer.status }}
          </span>
          {{ runDrawer.duration_ms }} ms
        </p>
        <p v-if="runDrawer.error" class="alert">{{ runDrawer.error }}</p>
        <ol class="step-list">
          <li v-for="step in runDrawer.steps" :key="step.index">
            <span class="badge" :class="step.ok ? 'badge-green' : 'badge-red'">{{ step.ok ? '通过' : '失败' }}</span>
            <span class="step-action">{{ step.action }}</span>
            <code>{{ step.target || step.value }}</code>
            <span v-if="step.error" class="muted">{{ step.error }}</span>
          </li>
        </ol>
        <div v-if="runDrawer.screenshot_data" class="shot">
          <img :src="`data:image/png;base64,${runDrawer.screenshot_data}`" alt="失败截图" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.toolbar select {
  width: auto;
  min-width: 190px;
}
.hero-metrics {
  display: flex;
  gap: 30px;
}
.hero-metrics div {
  display: flex;
  flex-direction: column;
}
.hero-metrics strong {
  font-size: 26px;
}
.hero-metrics span {
  font-size: 12px;
  color: var(--muted);
}
.form-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-stack label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12.5px;
  color: var(--muted);
}
.form-stack input,
.form-stack textarea,
.form-stack select,
.chat-row input {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.form-row {
  display: flex;
  gap: 12px;
}
.form-row label {
  flex: 1;
}
.form-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.chat-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.chat-row input {
  flex: 1 1 240px;
}
.reasoning {
  border-left: 2px solid rgba(56, 189, 248, 0.4);
  padding-left: 10px;
  color: var(--muted);
  font-size: 12.5px;
}
.step-list {
  margin: 10px 0 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 12.5px;
}
.step-list code {
  font-size: 12px;
}
.step-action {
  display: inline-block;
  min-width: 92px;
  color: var(--accent);
  font-size: 11.5px;
}
.reply {
  margin-top: 12px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  white-space: pre-wrap;
  font-size: 13px;
}
.script {
  max-height: 60vh;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(4, 8, 16, 0.6);
  font-size: 12px;
  white-space: pre-wrap;
}
.shot img {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 10px;
  margin-top: 10px;
}
.badge-green {
  color: #4ade80;
  border-color: rgba(74, 222, 128, 0.35);
  background: rgba(74, 222, 128, 0.12);
}
.badge-red {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.35);
  background: rgba(248, 113, 113, 0.12);
}
.alert.ok {
  color: #4ade80;
}
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(3, 6, 12, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
  padding: 24px;
}
.modal {
  width: min(720px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 18px 20px;
}
.modal.wide {
  width: min(860px, 100%);
}
.modal header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.modal header h2 {
  font-size: 18px;
  margin: 0;
}
@media (max-width: 1100px) {
  .split-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
