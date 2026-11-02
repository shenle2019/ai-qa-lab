<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

const STORAGE_COLLECTIONS = 'aiqa.workbench.collections'
const STORAGE_ENV = 'aiqa.workbench.env'
const route = useRoute()

const defaultCollections = [
  {
    id: 'demo-health',
    name: 'SUT 健康检查',
    method: 'GET',
    url: '{{baseUrl}}/health',
    headers: [{ key: 'Accept', value: 'application/json' }],
    body: '',
    assertions: [
      { type: 'status', expected: '200', path: '' },
      { type: 'json_path_equals', expected: 'ok', path: '$.status' },
    ],
  },
  {
    id: 'demo-tickets',
    name: '工单列表',
    method: 'GET',
    url: '{{baseUrl}}/api/tickets',
    headers: [{ key: 'Accept', value: 'application/json' }],
    body: '',
    assertions: [{ type: 'status', expected: '200', path: '' }],
  },
]

function loadStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function saveStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

const environment = ref(loadStorage(STORAGE_ENV, [{ key: 'baseUrl', value: window.location.origin }]))
const collections = ref(loadStorage(STORAGE_COLLECTIONS, defaultCollections))
const history = ref([])
const response = ref(null)
const error = ref('')
const sending = ref(false)
const running = ref(false)
const runResults = ref([])
const activeTab = ref('body')

const request = reactive({
  name: 'SUT 健康检查',
  method: 'GET',
  url: '{{baseUrl}}/health',
  headers: [{ key: 'Accept', value: 'application/json' }],
  body: '',
  assertions: [
    { type: 'status', expected: '200' },
    { type: 'json_path_equals', expected: 'ok', path: '$.status' },
  ],
})

const assertionTypes = [
  { value: 'status', label: '状态码等于' },
  { value: 'max_ms', label: '耗时小于(ms)' },
  { value: 'body_contains', label: '响应文本包含' },
  { value: 'json_path_exists', label: 'JSON 路径存在' },
  { value: 'json_path_equals', label: 'JSON 路径等于' },
]

function substitute(text) {
  let output = text || ''
  for (const item of environment.value) {
    if (!item.key) continue
    output = output.split(`{{${item.key}}}`).join(item.value)
  }
  return output
}

function headerObject() {
  const result = {}
  for (const item of request.headers) {
    if (item.key.trim()) result[item.key.trim()] = substitute(item.value)
  }
  return result
}

function normalizeAssertions() {
  return request.assertions
    .filter((item) => item.type)
    .map((item) => ({
      type: item.type,
      path: item.path?.trim() || null,
      expected:
        item.type === 'status' || item.type === 'max_ms' ? Number(item.expected) : item.expected,
    }))
}

function toPayload(item = request) {
  return {
    name: item.name || 'request',
    method: item.method,
    url: substitute(item.url),
    headers: Object.fromEntries(
      item.headers.filter((header) => header.key.trim()).map((header) => [header.key.trim(), substitute(header.value)]),
    ),
    body: item.body ? substitute(item.body) : null,
    timeout_ms: 10000,
    assertions: item.assertions
      .filter((assertion) => assertion.type)
      .map((assertion) => ({
        type: assertion.type,
        path: assertion.path || null,
        expected:
          assertion.type === 'status' || assertion.type === 'max_ms'
            ? Number(assertion.expected)
            : assertion.expected,
      })),
  }
}

function prettyBody(text) {
  if (!text) return ''
  try {
    return JSON.stringify(JSON.parse(text), null, 2)
  } catch {
    return text
  }
}

async function send() {
  sending.value = true
  error.value = ''
  response.value = null
  try {
    const res = await fetch('/api/workbench/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(toPayload()),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `${res.status} ${res.statusText}`)
    }
    response.value = await res.json()
    history.value.unshift({ name: request.name, url: substitute(request.url), at: new Date().toLocaleTimeString('zh-CN', { hour12: false }) })
    history.value = history.value.slice(0, 10)
  } catch (err) {
    error.value = err.message
  } finally {
    sending.value = false
  }
}

function newRequest() {
  Object.assign(request, {
    name: '新建请求',
    method: 'GET',
    url: '{{baseUrl}}/health',
    headers: [{ key: 'Accept', value: 'application/json' }],
    body: '',
    assertions: [{ type: 'status', expected: '200' }],
  })
  response.value = null
  error.value = ''
}

onMounted(() => {
  if (route.query.demo === '1') send()
})

function saveRequest() {
  const item = JSON.parse(JSON.stringify(request))
  item.id = `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`
  collections.value.unshift(item)
  saveStorage(STORAGE_COLLECTIONS, collections.value)
}

function loadRequest(item) {
  Object.assign(request, JSON.parse(JSON.stringify(item)))
  response.value = null
  error.value = ''
}

function deleteRequest(id) {
  collections.value = collections.value.filter((item) => item.id !== id)
  saveStorage(STORAGE_COLLECTIONS, collections.value)
}

async function runCollection() {
  if (!collections.value.length) {
    error.value = '集合为空，先保存至少一个请求'
    return
  }
  running.value = true
  error.value = ''
  runResults.value = []
  try {
    const res = await fetch('/api/workbench/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requests: collections.value.map((item) => toPayload(item)) }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `${res.status} ${res.statusText}`)
    }
    runResults.value = await res.json()
  } catch (err) {
    error.value = err.message
  } finally {
    running.value = false
  }
}

function addHeader() {
  request.headers.push({ key: '', value: '' })
}
function removeHeader(index) {
  request.headers.splice(index, 1)
}
function addAssertion() {
  request.assertions.push({ type: 'status', expected: '200', path: '' })
}
function removeAssertion(index) {
  request.assertions.splice(index, 1)
}
function addEnv() {
  environment.value.push({ key: '', value: '' })
}
function removeEnv(index) {
  environment.value.splice(index, 1)
}
function saveEnv() {
  saveStorage(STORAGE_ENV, environment.value)
}
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">MODULE 03 · REFERENCE HOPPSCOTCH 80,721★</p>
        <h2>API Workbench</h2>
        <p class="muted">请求构建 → 变量替换 → 发送 → 断言 → 集合批量运行 → 报告。复刻 Hoppscotch 的核心闭环，后端由 FastAPI 代理执行。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ collections.length }}</strong><span>集合请求</span></div>
        <div><strong>{{ history.length }}</strong><span>本次历史</span></div>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>

    <div class="workbench-grid">
      <aside class="wb-left">
        <article class="card">
          <div class="card-head">
            <div>
              <h2>集合</h2>
              <p>保存在浏览器 localStorage</p>
            </div>
            <button class="btn ghost" :disabled="running" @click="runCollection">{{ running ? '运行中' : '运行全部' }}</button>
          </div>
          <div v-if="!collections.length" class="empty">保存请求后会出现在这里。</div>
          <ul v-else class="collection-list">
            <li v-for="item in collections" :key="item.id">
              <button class="collection-main" @click="loadRequest(item)">
                <span class="method-tag">{{ item.method }}</span>
                <span>
                  <strong>{{ item.name }}</strong>
                  <small>{{ item.url }}</small>
                </span>
              </button>
              <button class="icon-btn" title="删除" @click="deleteRequest(item.id)">×</button>
            </li>
          </ul>
        </article>

        <article class="card">
          <div class="card-head">
            <div>
              <h2>环境变量</h2>
              <p>在 URL/Header/Body 中用 {{ key }} 引用</p>
            </div>
            <button class="btn ghost" @click="saveEnv">保存</button>
          </div>
          <div class="kv-list">
            <div v-for="(item, index) in environment" :key="index" class="kv-row">
              <input v-model="item.key" placeholder="key" />
              <input v-model="item.value" placeholder="value" />
              <button class="icon-btn" @click="removeEnv(index)">×</button>
            </div>
          </div>
          <button class="btn ghost add-row" @click="addEnv">+ 添加变量</button>
        </article>

        <article class="card">
          <div class="card-head"><div><h2>历史</h2><p>最近 10 次发送</p></div></div>
          <div v-if="!history.length" class="empty">还没有发送记录。</div>
          <ul v-else class="history compact">
            <li v-for="(item, index) in history" :key="index">
              <div class="history-head">
                <strong>{{ item.name }}</strong>
                <span class="muted">{{ item.at }}</span>
              </div>
              <p class="mono">{{ item.url }}</p>
            </li>
          </ul>
        </article>
      </aside>

      <div class="wb-main">
        <article class="card">
          <div class="request-line">
            <input v-model="request.name" class="request-name" placeholder="请求名称" />
            <select v-model="request.method" class="method-select">
              <option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option>
            </select>
            <input v-model="request.url" class="request-url" placeholder="https://api.example.com/health" />
            <button class="btn" :disabled="sending" @click="send">{{ sending ? '发送中' : '发送' }}</button>
          </div>

          <div class="req-section">
            <div class="section-title"><span>Headers</span><button class="link-btn" @click="addHeader">+ 添加</button></div>
            <div class="kv-list">
              <div v-for="(item, index) in request.headers" :key="index" class="kv-row">
                <input v-model="item.key" placeholder="Header" />
                <input v-model="item.value" placeholder="Value" />
                <button class="icon-btn" @click="removeHeader(index)">×</button>
              </div>
            </div>
          </div>

          <div class="req-section">
            <div class="section-title"><span>Body</span><span class="muted">JSON / 原始文本</span></div>
            <textarea v-model="request.body" rows="5" placeholder='{"title": "来自 API 工作台的工单"}'></textarea>
          </div>

          <div class="req-section">
            <div class="section-title"><span>断言</span><button class="link-btn" @click="addAssertion">+ 添加</button></div>
            <div class="kv-list">
              <div v-for="(item, index) in request.assertions" :key="index" class="assertion-row">
                <select v-model="item.type">
                  <option v-for="type in assertionTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
                <input v-if="['json_path_exists', 'json_path_equals'].includes(item.type)" v-model="item.path" placeholder="$.id" />
                <input v-model="item.expected" placeholder="期望值" />
                <button class="icon-btn" @click="removeAssertion(index)">×</button>
              </div>
            </div>
          </div>

          <div class="request-actions">
            <button class="btn ghost" @click="newRequest">重置</button>
            <button class="btn ghost" @click="saveRequest">保存到集合</button>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div>
              <h2>响应</h2>
              <p>由后端 httpx 代理执行，避免浏览器跨域限制</p>
            </div>
            <div v-if="response" class="response-meta">
              <span class="badge" :class="response.passed ? 'status-closed' : 'priority-high'">{{ response.passed ? 'PASS' : 'FAIL' }}</span>
              <span class="mono">{{ response.status ?? 'ERR' }}</span>
              <span class="muted">{{ response.elapsed_ms }} ms</span>
              <span class="muted">{{ response.size }} B</span>
            </div>
          </div>

          <div v-if="!response" class="empty">发送请求后显示状态、耗时、响应体与断言结果。</div>
          <template v-else>
            <div v-if="response.failures.length" class="alert error">
              <p v-for="(failure, index) in response.failures" :key="index">{{ failure }}</p>
            </div>
            <div class="tabs">
              <button :class="['tab', { active: activeTab === 'body' }]" @click="activeTab = 'body'">Body</button>
              <button :class="['tab', { active: activeTab === 'headers' }]" @click="activeTab = 'headers'">Headers</button>
            </div>
            <pre v-if="activeTab === 'body'" class="response-body">{{ prettyBody(response.body_preview) }}</pre>
            <div v-else class="table-wrap">
              <table>
                <tbody>
                  <tr v-for="(value, key) in response.headers || {}" :key="key">
                    <td class="mono">{{ key }}</td>
                    <td>{{ value }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </article>

        <article v-if="runResults.length" class="card">
          <div class="card-head">
            <div><h2>集合运行报告</h2><p>{{ runResults.filter((item) => item.passed).length }} / {{ runResults.length }} 通过</p></div>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>请求</th><th>结果</th><th>状态</th><th>耗时</th><th>失败原因</th></tr></thead>
              <tbody>
                <tr v-for="item in runResults" :key="item.name">
                  <td>{{ item.name }}</td>
                  <td><span class="badge" :class="item.passed ? 'status-closed' : 'priority-high'">{{ item.passed ? 'PASS' : 'FAIL' }}</span></td>
                  <td class="mono">{{ item.status ?? 'ERR' }}</td>
                  <td class="muted">{{ item.elapsed_ms }} ms</td>
                  <td class="muted">{{ item.failures.join('; ') || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>
