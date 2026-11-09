<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import EmptyState from '../../components/EmptyState.vue'
import RowMenu from '../../components/RowMenu.vue'
import { pickProject, saveProjectId } from '../../utils/project'
import { askConfirm } from '../../composables/confirm'

const tabs = [
  { key: 'agents', label: '场景 Agent' },
  { key: 'single-agent', label: '单接口 Agent' },
  { key: 'assets', label: '接口资产' },
  { key: 'endpoints', label: '接口管理' },
  { key: 'single-cases', label: '单接口用例' },
  { key: 'scenarios', label: '接口场景' },
  { key: 'runs', label: '执行记录' },
]
const tab = ref('endpoints')

const projects = ref([])
const projectId = ref(null)
const assets = ref([])
const endpoints = ref([])
const modules = ref([])
const cases = ref([])
const runs = ref([])
const loading = ref(false)
const message = ref('')
const error = ref('')

const filters = reactive({ q: '', method: '', module: '' })

const debugOpen = ref(false)
const debugTarget = ref(null)
const debugForm = reactive({
  base_url: '',
  headers: '{\n  "Authorization": "Bearer "\n}',
  params: '{}',
  body: '',
  expect_status: 200,
})
const debugResult = ref(null)
const debugError = ref('')
const debugBusy = ref(false)

const caseDrawer = ref(null)
const runDrawer = ref(null)
const runBusy = ref(false)

const singleForm = reactive({ endpoint_id: null, count: 5, kb_id: '', model_id: '' })
const singleBusy = ref(false)
const singleResult = ref(null)
const knowledgeBases = ref([])

const scenarioPick = ref([])
const scenarioForm = reactive({ goal: '', model_id: '' })
const scenarioBusy = ref(false)
const scenarioResult = ref(null)

const endpointModal = reactive({ open: false, id: null, method: 'GET', path: '', name: '', module: '未分组' })
const importForm = reactive({ open: false, name: '', spec: '' })
const importBusy = ref(false)

const methodClass = (method) => `m-${String(method || '').toLowerCase()}`
const statusText = { draft: '草稿', approved: '已启用', disabled: '已停用' }
const runStatusText = { passed: '通过', failed: '失败' }

const endpointOptions = computed(() => endpoints.value)
const passRate = computed(() => {
  if (!runs.value.length) return '—'
  const passed = runs.value.filter((item) => item.status === 'passed').length
  return `${Math.round((passed / runs.value.length) * 100)}%`
})

const PROJECT_KEY = 'aiqa.api.project'

async function loadProjects() {
  projects.value = await api.platformProjects()
  if (!projectId.value && projects.value.length) {
    projectId.value = pickProject(projects.value, PROJECT_KEY)?.id ?? projects.value[0].id
  }
}

function rememberProject() {
  saveProjectId(projectId.value, PROJECT_KEY)
}

async function loadAssets() {
  if (!projectId.value) return
  assets.value = await api.apiAssets(projectId.value)
}

async function loadEndpoints() {
  if (!projectId.value) return
  endpoints.value = await api.apiEndpoints(projectId.value, {
    q: filters.q,
    method: filters.method,
    module: filters.module,
  })
}

async function loadModules() {
  if (!projectId.value) return
  modules.value = await api.apiModules(projectId.value)
}

async function loadCases() {
  if (!projectId.value) return
  cases.value = await api.apiCases(projectId.value)
}

async function loadRuns() {
  if (!projectId.value) return
  runs.value = await api.apiRuns(projectId.value, 60)
}

async function loadKnowledge() {
  try {
    knowledgeBases.value = await api.knowledgeBases(projectId.value)
  } catch {
    knowledgeBases.value = []
  }
}

async function refreshAll() {
  if (!projectId.value) return
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      loadAssets(),
      loadEndpoints(),
      loadModules(),
      loadCases(),
      loadRuns(),
    ])
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function flash(text) {
  message.value = text
  setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 4000)
}

async function onProjectChange() {
  singleForm.endpoint_id = null
  scenarioPick.value = []
  singleResult.value = null
  scenarioResult.value = null
  rememberProject()
  await refreshAll()
  await loadKnowledge()
}

// ---------------------------------------------------------------- assets

function openImport() {
  importForm.open = true
  importForm.name = ''
  importForm.spec = ''
}

async function submitImport() {
  if (!importForm.spec.trim()) {
    error.value = '请粘贴 OpenAPI 文档内容'
    return
  }
  importBusy.value = true
  error.value = ''
  try {
    const result = await api.importApiSpec({
      project_id: projectId.value,
      spec: importForm.spec,
      name: importForm.name || null,
    })
    flash(`已导入 ${result.imported} 个接口（${result.name}）`)
    importForm.open = false
    await refreshAll()
  } catch (err) {
    error.value = err.message
  } finally {
    importBusy.value = false
  }
}

async function removeAsset(item) {
  if (!(await askConfirm({ message: `删除接口资产「${item.name}」？它导入的接口会一起删掉。` }))) return
  try {
    await api.deleteApiAsset(item.id)
    flash('接口资产已删除')
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

// ------------------------------------------------------------- endpoints

function openEndpoint(item = null) {
  endpointModal.open = true
  endpointModal.id = item ? item.id : null
  endpointModal.method = item ? item.method : 'GET'
  endpointModal.path = item ? item.path : '/api/'
  endpointModal.name = item ? item.name : ''
  endpointModal.module = item ? item.module : '未分组'
}

async function saveEndpoint() {
  try {
    if (endpointModal.id) {
      await api.updateApiEndpoint(endpointModal.id, {
        method: endpointModal.method,
        path: endpointModal.path,
        name: endpointModal.name,
        module: endpointModal.module,
      })
      flash('接口已更新')
    } else {
      await api.createApiEndpoint({
        project_id: projectId.value,
        method: endpointModal.method,
        path: endpointModal.path,
        name: endpointModal.name,
        module: endpointModal.module,
      })
      flash('接口已创建')
    }
    endpointModal.open = false
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

async function removeEndpoint(item) {
  if (!(await askConfirm({ message: `删除接口「${item.method} ${item.path}」？` }))) return
  try {
    await api.deleteApiEndpoint(item.id)
    flash('接口已删除')
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

function openDebug(item) {
  debugTarget.value = item
  debugResult.value = null
  debugError.value = ''
  debugForm.headers = '{\n  "Authorization": "Bearer "\n}'
  debugForm.params = '{}'
  debugForm.body = ''
  debugForm.expect_status = 200
  debugForm.base_url = ''
  const asset = assets.value.find((entry) => entry.id === item.asset_id)
  if (asset && asset.base_url) debugForm.base_url = asset.base_url
  debugOpen.value = true
}

function safeJson(text) {
  const trimmed = (text || '').trim()
  if (!trimmed) return null
  try {
    return JSON.parse(trimmed)
  } catch {
    throw new Error('请求体/参数不是合法的 JSON')
  }
}

async function sendDebug() {
  if (!debugTarget.value) return
  debugBusy.value = true
  debugResult.value = null
  debugError.value = ''
  error.value = ''
  try {
    const payload = {
      base_url: debugForm.base_url || null,
      headers: safeJson(debugForm.headers) || {},
      params: safeJson(debugForm.params) || {},
      body: safeJson(debugForm.body),
      expect_status: debugForm.expect_status || null,
    }
    debugResult.value = await api.debugApiEndpoint(debugTarget.value.id, payload)
    debugError.value = ''
    await loadRuns()
  } catch (err) {
    debugError.value = err.message || '请求失败，请检查访问密钥与接口地址'
  } finally {
    debugBusy.value = false
  }
}

async function diagnoseCurrent() {
  if (!debugResult.value) return
  runBusy.value = true
  try {
    const result = await api.diagnoseApiRun(debugResult.value.id)
    debugResult.value.ai_root_cause = result.ai_root_cause
    await loadRuns()
  } catch (err) {
    error.value = err.message
  } finally {
    runBusy.value = false
  }
}

// --------------------------------------------------------------- agents

async function generateSingle() {
  if (!singleForm.endpoint_id) {
    error.value = '请选择接口'
    return
  }
  singleBusy.value = true
  singleResult.value = null
  error.value = ''
  try {
    singleResult.value = await api.generateApiCases({
      endpoint_id: singleForm.endpoint_id,
      count: singleForm.count,
      kb_id: singleForm.kb_id ? Number(singleForm.kb_id) : null,
      model_id: singleForm.model_id ? Number(singleForm.model_id) : null,
    })
    flash(`已生成 ${singleResult.value.count} 条接口用例（草稿）`)
    await loadCases()
  } catch (err) {
    error.value = err.message
  } finally {
    singleBusy.value = false
  }
}

function toggleScenario(id) {
  const index = scenarioPick.value.indexOf(id)
  if (index >= 0) scenarioPick.value.splice(index, 1)
  else scenarioPick.value.push(id)
}

async function generateScenario() {
  if (!scenarioPick.value.length) {
    error.value = '至少选择一个接口'
    return
  }
  scenarioBusy.value = true
  scenarioResult.value = null
  error.value = ''
  try {
    scenarioResult.value = await api.generateApiScenario({
      project_id: projectId.value,
      endpoint_ids: scenarioPick.value,
      goal: scenarioForm.goal,
      model_id: scenarioForm.model_id ? Number(scenarioForm.model_id) : null,
    })
    flash(`场景「${scenarioResult.value.title}」已生成`)
    await loadCases()
  } catch (err) {
    error.value = err.message
  } finally {
    scenarioBusy.value = false
  }
}

// ----------------------------------------------------------------- cases

const singleCases = computed(() => cases.value.filter((item) => item.kind === 'case'))
const scenarioCases = computed(() => cases.value.filter((item) => item.kind === 'scenario'))

async function runCase(item) {
  runBusy.value = true
  error.value = ''
  try {
    const result = await api.runApiCase(item.id)
    flash(result.status === 'passed' ? '执行通过' : `执行失败：${result.error || ''}`)
    await loadRuns()
    runDrawer.value = result
  } catch (err) {
    error.value = err.message
  } finally {
    runBusy.value = false
  }
}

async function removeCase(item) {
  if (!(await askConfirm({ message: `删除用例「${item.title}」？` }))) return
  try {
    await api.deleteApiCase(item.id)
    flash('用例已删除')
    await loadCases()
  } catch (err) {
    error.value = err.message
  }
}

async function toggleCaseStatus(item) {
  const next = item.status === 'approved' ? 'draft' : 'approved'
  try {
    await api.updateApiCase(item.id, { status: next })
    await loadCases()
  } catch (err) {
    error.value = err.message
  }
}

async function openRun(item) {
  runBusy.value = true
  try {
    runDrawer.value = await api.apiRun(item.id)
  } catch (err) {
    error.value = err.message
  } finally {
    runBusy.value = false
  }
}

async function diagnoseRun(item) {
  runBusy.value = true
  try {
    const result = await api.diagnoseApiRun(item.id)
    item.ai_root_cause = result.ai_root_cause
    if (runDrawer.value && runDrawer.value.id === item.id) {
      runDrawer.value.ai_root_cause = result.ai_root_cause
    }
    await loadRuns()
  } catch (err) {
    error.value = err.message
  } finally {
    runBusy.value = false
  }
}

function pretty(value) {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function stepSummary(steps) {
  if (!Array.isArray(steps) || !steps.length) return '—'
  return steps.map((step) => `${step.method} ${step.url}`).join(' → ')
}

onMounted(async () => {
  await loadProjects()
  await refreshAll()
  await loadKnowledge()
})
</script>

<template>
  <section class="stack">
    <header class="hero">
      <div>
        <p class="eyebrow">API AUTOMATION</p>
        <h1>接口自动化</h1>
        <p class="muted">
          接口资产从 OpenAPI 导入，调试真发请求；单接口 Agent 生成用例，场景 Agent 把接口串成带数据流转的链路，执行结果留档并可 AI 归因。
        </p>
      </div>
      <div class="hero-metrics">
        <div>
          <strong>{{ endpoints.length }}</strong>
          <span>接口</span>
        </div>
        <div>
          <strong>{{ cases.length }}</strong>
          <span>用例</span>
        </div>
        <div>
          <strong>{{ passRate }}</strong>
          <span>近 60 次通过率</span>
        </div>
      </div>
    </header>

    <div class="toolbar">
      <select v-model.number="projectId" @change="onProjectChange">
        <option v-for="item in projects" :key="item.id" :value="item.id">
          #{{ item.id }} {{ item.name }}
        </option>
      </select>
      <div class="toolbar-group">
        <button class="btn ghost" :disabled="loading" @click="refreshAll">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
      <span v-if="message" class="ok-note">{{ message }}</span>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>

    <nav class="tabs sub-tabs">
      <button
        v-for="item in tabs"
        :key="item.key"
        class="tab"
        :class="{ active: tab === item.key }"
        @click="tab = item.key"
      >
        {{ item.label }}
      </button>
    </nav>

    <!-- 接口资产 -->
    <div v-if="tab === 'assets'" class="card">
      <div class="card-head">
        <div>
          <h2>接口资产</h2>
          <p class="muted">导入 OpenAPI / Swagger（JSON 或 YAML），接口会落到「接口管理」。</p>
        </div>
        <button class="btn" @click="openImport">导入文档</button>
      </div>
      <div v-if="!assets.length" class="empty">还没有导入过接口文档。</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>版本</th>
              <th>Base URL</th>
              <th>接口数</th>
              <th>导入时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in assets" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td>{{ item.name }}</td>
              <td class="mono">{{ item.spec_version || '—' }}</td>
              <td class="mono cell-sub">{{ item.base_url || '—' }}</td>
              <td>{{ item.endpoint_count }}</td>
              <td class="cell-sub">{{ new Date(item.created_at).toLocaleString() }}</td>
              <td>
                <button class="btn ghost tiny" @click="removeAsset(item)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 接口管理 -->
    <div v-if="tab === 'endpoints'" class="card">
      <div class="card-head">
        <div>
          <h2>接口管理</h2>
          <p class="muted">共 {{ endpoints.length }} 个接口，可直接调试。</p>
        </div>
        <div class="toolbar-group">
          <button class="btn ghost" @click="loadEndpoints">查询</button>
          <button class="btn" @click="openEndpoint()">新建接口</button>
        </div>
      </div>
      <div class="toolbar">
        <input v-model="filters.q" type="search" maxlength="80" placeholder="搜索名称或路径（最多 80 字）" @keyup.enter="loadEndpoints" />
        <select v-model="filters.method" @change="loadEndpoints">
          <option value="">全部方法</option>
          <option v-for="m in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']" :key="m" :value="m">{{ m }}</option>
        </select>
        <select v-model="filters.module" @change="loadEndpoints">
          <option value="">全部模块</option>
          <option v-for="item in modules" :key="item.module" :value="item.module">
            {{ item.module }}（{{ item.count }}）
          </option>
        </select>
      </div>
      <EmptyState
        v-if="!endpoints.length && !loading"
        icon="api"
        title="没有匹配的接口"
        hint="先到「接口资产」导入 OpenAPI 文档，或者手动新建一个接口。"
      >
        <template #action>
          <button class="btn tiny" type="button" @click="openEndpoint()">新建接口</button>
        </template>
      </EmptyState>
      <div v-else-if="endpoints.length" class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>方法</th>
              <th>路径</th>
              <th>名称</th>
              <th>模块</th>
              <th>用例</th>
              <th>来源</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading && !endpoints.length">
              <tr v-for="n in 5" :key="`sk-${n}`" class="skeleton-row">
                <td><span class="skeleton" style="width: 48px" /></td>
                <td><span class="skeleton" style="width: 220px" /></td>
                <td><span class="skeleton" style="width: 120px" /></td>
                <td><span class="skeleton" style="width: 88px" /></td>
                <td><span class="skeleton" style="width: 32px" /></td>
                <td><span class="skeleton" style="width: 64px" /></td>
                <td><span class="skeleton" style="width: 150px" /></td>
              </tr>
            </template>
            <tr v-for="item in endpoints" :key="item.id">
              <td><span class="method" :class="methodClass(item.method)">{{ item.method }}</span></td>
              <td class="mono">{{ item.path }}</td>
              <td>{{ item.name || '—' }}</td>
              <td class="cell-sub">{{ item.module }}</td>
              <td>{{ item.case_count }}</td>
              <td class="cell-sub">{{ item.source === 'openapi' ? '文档同步' : '手工' }}</td>
              <td>
                <div class="row-actions">
                  <button class="btn" @click="openDebug(item)">调试</button>
                  <button class="btn ghost tiny" @click="openEndpoint(item)">编辑</button>
                  <RowMenu :items="[{ label: '删除接口', danger: true, run: () => removeEndpoint(item) }]" />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 单接口 Agent -->
    <div v-if="tab === 'single-agent'" class="split-grid">
      <div class="card">
        <h2>单接口 Agent</h2>
        <p class="muted">选一个接口，模型会按正常、边界、异常角度生成可直接执行的用例。</p>
        <div class="form-stack">
          <label>
            接口
            <select v-model.number="singleForm.endpoint_id">
              <option :value="null">请选择接口</option>
              <option v-for="item in endpointOptions" :key="item.id" :value="item.id">
                {{ item.method }} {{ item.path }} · {{ item.name }}
              </option>
            </select>
          </label>
          <label>
            生成条数
            <input v-model.number="singleForm.count" type="number" min="1" max="15" />
          </label>
          <label>
            知识库（可选，用于补充接口约定）
            <select v-model="singleForm.kb_id">
              <option value="">不使用</option>
              <option v-for="item in knowledgeBases" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
          </label>
          <button
            class="btn"
            :disabled="singleBusy || !singleForm.endpoint_id"
            :title="singleForm.endpoint_id ? '' : '先选一个接口'"
            @click="generateSingle"
          >
            {{ singleBusy ? '生成中…' : 'AI 生成用例' }}
          </button>
          <p v-if="!singleForm.endpoint_id" class="search-hint">先在上方选择接口，生成按钮才可用。</p>
        </div>
      </div>
      <div class="card">
        <div class="card-head">
          <h2>本次生成</h2>
          <span class="cell-sub">已写入「单接口用例」，状态为草稿</span>
        </div>
        <div v-if="!singleResult" class="empty">还没有生成结果。</div>
        <div v-else class="result-list">
          <article v-for="item in singleResult.cases" :key="item.id" class="result-item">
            <header>
              <strong>{{ item.title }}</strong>
              <span class="badge">{{ statusText[item.status] || item.status }}</span>
            </header>
            <p class="mono cell-sub">{{ stepSummary(item.steps) }}</p>
            <p class="muted">{{ item.expected }}</p>
          </article>
        </div>
      </div>
    </div>

    <!-- 场景 Agent -->
    <div v-if="tab === 'agents'" class="split-grid">
      <div class="card">
        <h2>场景 Agent</h2>
        <p class="muted">勾选多个接口，模型会串成一条带数据流转的场景（前一步产出给后一步用）。</p>
        <label class="form-label">业务目标（可选）</label>
        <textarea
          v-model="scenarioForm.goal"
          rows="3"
          placeholder="例如：创建工单后按 id 查询详情，再删除并确认已消失"
        />
        <label class="form-label">选择接口（已选 {{ scenarioPick.length }}）</label>
        <div class="pick-list">
          <label v-for="item in endpoints" :key="item.id" class="pick-item">
            <input
              type="checkbox"
              :checked="scenarioPick.includes(item.id)"
              @change="toggleScenario(item.id)"
            />
            <span class="method" :class="methodClass(item.method)">{{ item.method }}</span>
            <span class="mono">{{ item.path }}</span>
            <span class="cell-sub">{{ item.name }}</span>
          </label>
        </div>
        <button class="btn" :disabled="scenarioBusy" @click="generateScenario">
          {{ scenarioBusy ? '生成中…' : '生成场景' }}
        </button>
      </div>
      <div class="card">
        <div class="card-head">
          <h2>本次生成</h2>
          <span class="cell-sub">已写入「接口场景」，状态为草稿</span>
        </div>
        <div v-if="!scenarioResult" class="empty">还没有生成场景。</div>
        <div v-else>
          <h3>{{ scenarioResult.title }}</h3>
          <p class="muted">{{ scenarioResult.expected }}</p>
          <ol class="step-list">
            <li v-for="(step, index) in scenarioResult.steps" :key="index">
              <div class="step-head">
                <span class="method" :class="methodClass(step.method)">{{ step.method }}</span>
                <span class="mono">{{ step.url }}</span>
              </div>
              <p class="cell-sub">{{ step.name }}</p>
              <p v-if="step.extract && Object.keys(step.extract).length" class="mono cell-sub">
                提取：{{ pretty(step.extract) }}
              </p>
            </li>
          </ol>
        </div>
      </div>
    </div>

    <!-- 单接口用例 -->
    <div v-if="tab === 'single-cases'" class="card">
      <div class="card-head">
        <div>
          <h2>单接口用例</h2>
          <p class="muted">共 {{ singleCases.length }} 条，可直接执行。</p>
        </div>
        <button class="btn ghost" @click="loadCases">刷新</button>
      </div>
      <div v-if="!singleCases.length" class="empty">还没有单接口用例，去「单接口 Agent」生成一批。</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>模块</th>
              <th>步骤</th>
              <th>状态</th>
              <th>来源</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in singleCases" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td>{{ item.title }}</td>
              <td class="cell-sub">{{ item.module }}</td>
              <td class="mono cell-sub">{{ stepSummary(item.steps) }}</td>
              <td><span class="badge">{{ statusText[item.status] || item.status }}</span></td>
              <td class="cell-sub">{{ item.source === 'ai' ? 'AI' : '手工' }}</td>
              <td class="row-actions">
                <button class="btn ghost tiny" :disabled="runBusy" @click="runCase(item)">执行</button>
                <button class="btn ghost tiny" @click="toggleCaseStatus(item)">
                  {{ item.status === 'approved' ? '停用' : '启用' }}
                </button>
                <button class="btn ghost tiny danger" @click="removeCase(item)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 接口场景 -->
    <div v-if="tab === 'scenarios'" class="card">
      <div class="card-head">
        <div>
          <h2>接口场景</h2>
          <p class="muted">共 {{ scenarioCases.length }} 条，按步骤顺序执行，变量在步骤间流转。</p>
        </div>
        <button class="btn ghost" @click="loadCases">刷新</button>
      </div>
      <div v-if="!scenarioCases.length" class="empty">还没有场景，去「场景 Agent」生成一条。</div>
      <div v-else class="result-list">
        <article v-for="item in scenarioCases" :key="item.id" class="result-item">
          <header>
            <strong>#{{ item.id }} {{ item.title }}</strong>
            <span class="badge">{{ statusText[item.status] || item.status }}</span>
          </header>
          <p class="mono cell-sub">{{ stepSummary(item.steps) }}</p>
          <div class="row-actions">
            <button class="btn ghost tiny" :disabled="runBusy" @click="runCase(item)">执行</button>
            <button class="btn ghost tiny danger" @click="removeCase(item)">删除</button>
          </div>
        </article>
      </div>
    </div>

    <!-- 执行记录 -->
    <div v-if="tab === 'runs'" class="card">
      <div class="card-head">
        <div>
          <h2>执行记录</h2>
          <p class="muted">最近 60 条，失败记录可以点「AI 归因」。</p>
        </div>
        <button class="btn ghost" @click="loadRuns">刷新</button>
      </div>
      <div v-if="!runs.length" class="empty">还没有执行记录。</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>类型</th>
              <th>标题</th>
              <th>结果</th>
              <th>状态码</th>
              <th>耗时</th>
              <th>时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in runs" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td class="cell-sub">{{ item.kind }}</td>
              <td>{{ item.title }}</td>
              <td>
                <span class="badge" :class="item.status === 'passed' ? 'badge-green' : 'badge-red'">
                  {{ runStatusText[item.status] || item.status }}
                </span>
              </td>
              <td class="mono">{{ item.status_code ?? '—' }}</td>
              <td class="cell-sub">{{ item.duration_ms }} ms</td>
              <td class="cell-sub">{{ new Date(item.created_at).toLocaleString() }}</td>
              <td class="row-actions">
                <button class="btn ghost tiny" @click="openRun(item)">详情</button>
                <button
                  v-if="item.status === 'failed'"
                  class="btn ghost tiny"
                  :disabled="runBusy"
                  @click="diagnoseRun(item)"
                >
                  AI 归因
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 导入弹窗 -->
    <div v-if="importForm.open" class="modal-mask">
      <div class="modal wide">
        <header>
          <h2>导入接口文档</h2>
          <button class="btn ghost tiny" data-modal-close @click="importForm.open = false">关闭</button>
        </header>
        <label class="form-label">资产名称（留空用文档标题）</label>
        <input v-model="importForm.name" placeholder="例如：工单服务" />
        <label class="form-label">OpenAPI / Swagger 内容（支持 JSON 与 YAML）</label>
        <textarea
          v-model="importForm.spec"
          rows="14"
          class="mono"
          placeholder="把 openapi.json / swagger.yaml 的内容粘贴进来"
        />
        <footer>
          <button class="btn ghost" @click="importForm.open = false">取消</button>
          <button class="btn" :disabled="importBusy" @click="submitImport">
            {{ importBusy ? '导入中…' : '导入' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- 接口弹窗 -->
    <div v-if="endpointModal.open" class="modal-mask">
      <div class="modal">
        <header>
          <h2>{{ endpointModal.id ? '编辑接口' : '新建接口' }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="endpointModal.open = false">关闭</button>
        </header>
        <label class="form-label">方法</label>
        <select v-model="endpointModal.method">
          <option v-for="m in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']" :key="m" :value="m">{{ m }}</option>
        </select>
        <label class="form-label">路径</label>
        <input v-model="endpointModal.path" class="mono" placeholder="/api/tickets" />
        <label class="form-label">名称</label>
        <input v-model="endpointModal.name" placeholder="查询工单列表" />
        <label class="form-label">模块</label>
        <input v-model="endpointModal.module" placeholder="tickets" />
        <footer>
          <button class="btn ghost" @click="endpointModal.open = false">取消</button>
          <button class="btn" @click="saveEndpoint">保存</button>
        </footer>
      </div>
    </div>

    <!-- 调试抽屉 -->
    <div v-if="debugOpen" class="modal-mask">
      <div class="modal wide">
        <header>
          <h2>
            <span class="method" :class="methodClass(debugTarget.method)">{{ debugTarget.method }}</span>
            <span class="mono">{{ debugTarget.path }}</span>
          </h2>
          <button class="btn ghost tiny" @click="debugOpen = false">关闭</button>
        </header>
        <label class="form-label">Base URL</label>
        <input
          v-model="debugForm.base_url"
          class="mono"
          placeholder="留空则用接口资产地址，例如 http://127.0.0.1:8000"
        />
        <label class="form-label">Headers（JSON）</label>
        <textarea v-model="debugForm.headers" rows="3" class="mono" />
        <label class="form-label">Query 参数（JSON）</label>
        <textarea v-model="debugForm.params" rows="3" class="mono" />
        <label class="form-label">请求体（JSON，GET 可留空）</label>
        <textarea v-model="debugForm.body" rows="5" class="mono" />
        <label class="form-label">期望状态码</label>
        <input v-model.number="debugForm.expect_status" type="number" placeholder="200" />
        <p v-if="debugError" class="alert error modal-alert">{{ debugError }}</p>
        <footer>
          <button class="btn ghost" @click="debugOpen = false">关闭</button>
          <button class="btn" :disabled="debugBusy" @click="sendDebug">
            {{ debugBusy ? '发送中…' : '发送请求' }}
          </button>
        </footer>
        <div v-if="debugResult" class="debug-result">
          <div class="debug-head">
            <span class="badge" :class="debugResult.status === 'passed' ? 'badge-green' : 'badge-red'">
              {{ debugResult.status === 'passed' ? '断言通过' : '断言失败' }}
            </span>
            <span class="mono">{{ debugResult.status_code ?? '无响应' }}</span>
            <span class="cell-sub">{{ debugResult.duration_ms }} ms</span>
          </div>
          <p v-if="debugResult.error" class="alert">{{ debugResult.error }}</p>
          <pre class="code">{{ pretty(debugResult.response) }}</pre>
          <div v-if="debugResult.status === 'failed'" class="agent-note">
            <div class="card-head">
              <strong>AI 归因</strong>
              <button class="btn ghost tiny" :disabled="runBusy" @click="diagnoseCurrent">分析</button>
            </div>
            <p v-if="debugResult.ai_root_cause" class="muted">{{ debugResult.ai_root_cause }}</p>
            <p v-else class="muted">还没有归因结果。</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 执行详情 -->
    <div v-if="runDrawer" class="modal-mask">
      <div class="modal wide">
        <header>
          <h2>#{{ runDrawer.id }} {{ runDrawer.title }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="runDrawer = null">关闭</button>
        </header>
        <div class="debug-head">
          <span class="badge" :class="runDrawer.status === 'passed' ? 'badge-green' : 'badge-red'">
            {{ runStatusText[runDrawer.status] || runDrawer.status }}
          </span>
          <span class="mono">{{ runDrawer.status_code ?? '—' }}</span>
          <span class="cell-sub">{{ runDrawer.duration_ms }} ms</span>
        </div>
        <p v-if="runDrawer.error" class="alert">{{ runDrawer.error }}</p>
        <h3>步骤</h3>
        <ol class="step-list">
          <li v-for="(step, index) in runDrawer.steps || []" :key="index">
            <div class="step-head">
              <span class="badge" :class="step.ok ? 'badge-green' : 'badge-red'">
                {{ step.ok ? '通过' : '失败' }}
              </span>
              <span class="mono">{{ step.request && step.request.method }} {{ step.request && step.request.url }}</span>
            </div>
            <p v-if="step.reason" class="cell-sub">{{ step.reason }}</p>
          </li>
        </ol>
        <h3>请求</h3>
        <pre class="code">{{ pretty(runDrawer.request) }}</pre>
        <h3>响应</h3>
        <pre class="code">{{ pretty(runDrawer.response) }}</pre>
        <div class="agent-note">
          <div class="card-head">
            <strong>AI 归因</strong>
            <button
              v-if="runDrawer.status === 'failed'"
              class="btn ghost tiny"
              :disabled="runBusy"
              @click="diagnoseRun(runDrawer)"
            >
              分析
            </button>
          </div>
          <p v-if="runDrawer.ai_root_cause" class="muted">{{ runDrawer.ai_root_cause }}</p>
          <p v-else class="muted">还没有归因结果。</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.sub-tabs {
  margin-bottom: 6px;
}
.toolbar-group {
  display: flex;
  gap: 8px;
}
.toolbar select {
  width: auto;
  min-width: 150px;
}
.toolbar input[type='search'] {
  flex: 1 1 240px;
  width: auto;
}
.ok-note {
  margin-left: auto;
  color: var(--green);
  font-size: 12px;
}
.form-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 14px;
}
.form-stack label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12.5px;
  color: var(--muted);
}
.form-stack select,
.form-stack input,
.form-label + input,
.form-label + textarea,
.form-label + select {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.form-label {
  display: block;
  margin: 12px 0 6px;
  font-size: 12.5px;
  color: var(--muted);
}
.method {
  display: inline-block;
  min-width: 58px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.04em;
}
.m-get {
  background: rgba(56, 189, 248, 0.16);
  color: #7dd3fc;
}
.m-post {
  background: rgba(52, 211, 153, 0.16);
  color: #6ee7b7;
}
.m-put,
.m-patch {
  background: rgba(251, 191, 36, 0.16);
  color: #fcd34d;
}
.m-delete {
  background: rgba(248, 113, 113, 0.16);
  color: #fca5a5;
}
.badge-green {
  background: rgba(52, 211, 153, 0.16);
  color: #6ee7b7;
}
.badge-red {
  background: rgba(248, 113, 113, 0.16);
  color: #fca5a5;
}
.pick-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 6px;
  margin-bottom: 12px;
}
.pick-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 12.5px;
}
.pick-item:hover {
  background: rgba(56, 189, 248, 0.06);
}
.pick-item input {
  width: 14px;
  height: 14px;
  accent-color: var(--accent);
}
.result-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.result-item {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px;
  background: rgba(4, 8, 16, 0.35);
}
.result-item header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}
.step-list {
  margin: 10px 0 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.step-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.code {
  max-height: 260px;
  overflow: auto;
  padding: 10px;
  border-radius: 8px;
  background: rgba(3, 6, 12, 0.7);
  border: 1px solid var(--line);
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}
.debug-result {
  margin-top: 16px;
  border-top: 1px solid var(--line);
  padding-top: 12px;
}
.debug-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.agent-note {
  margin-top: 14px;
  padding: 12px;
  border: 1px dashed var(--line);
  border-radius: 10px;
}
.btn.tiny {
  padding: 5px 10px;
  font-size: 12px;
}
.btn.ghost.danger {
  color: #fca5a5;
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
  width: min(620px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 18px 20px;
}
.modal.wide {
  width: min(900px, 100%);
}
.modal header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
.modal textarea,
.modal input,
.modal select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
@media (max-width: 1200px) {
  .split-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
