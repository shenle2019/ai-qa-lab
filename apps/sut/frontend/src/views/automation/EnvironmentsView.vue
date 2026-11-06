<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import { pickProjectSmart, saveProjectId } from '../../utils/project'

const PROJECT_KEY = 'aiqa.environments.project'
const KINDS = [
  { value: 'dev', label: '开发' },
  { value: 'test', label: '测试' },
  { value: 'staging', label: '预发' },
  { value: 'prod', label: '生产' },
]

const projects = ref([])
const projectId = ref(null)
const rows = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const form = reactive({ name: '', kind: 'test', base_url: '', variables: '', note: '' })
const editing = ref(null)
const editForm = reactive({ name: '', kind: 'test', base_url: '', variables: '', note: '' })

const readyCount = computed(() => rows.value.filter((item) => item.base_url).length)

function kindLabel(value) {
  return KINDS.find((item) => item.value === value)?.label || value
}

function varCount(item) {
  return Object.keys(item.variables || {}).length
}

function loadProjects() {
  return api.platformProjects().then(async (list) => {
    projects.value = list
    const picked = await pickProjectSmart(list, PROJECT_KEY, () => api.platformCases())
    projectId.value = picked?.id ?? null
  })
}

async function refresh() {
  if (!projectId.value) {
    rows.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    rows.value = await api.environments(projectId.value)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function onProjectChange() {
  saveProjectId(projectId.value, PROJECT_KEY)
  refresh()
}

function parseVariables(raw) {
  const text = (raw || '').trim()
  if (!text) return {}
  let parsed
  try {
    parsed = JSON.parse(text)
  } catch {
    throw new Error('变量必须是 JSON 对象，例如 {"token":"abc"}')
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('变量必须是 JSON 对象，例如 {"token":"abc"}')
  }
  return parsed
}

async function create() {
  if (!projectId.value) {
    error.value = '请先选择项目'
    return
  }
  if (!form.name.trim()) {
    error.value = '请输入环境名称'
    return
  }
  let variables
  try {
    variables = parseVariables(form.variables)
  } catch (err) {
    error.value = err.message
    return
  }
  error.value = ''
  try {
    await api.createEnvironment({
      project_id: projectId.value,
      name: form.name.trim(),
      kind: form.kind,
      base_url: form.base_url.trim(),
      variables,
      note: form.note.trim(),
    })
    form.name = ''
    form.base_url = ''
    form.variables = ''
    form.note = ''
    notice.value = '环境已创建'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

function openEdit(item) {
  editing.value = item
  editForm.name = item.name
  editForm.kind = item.kind
  editForm.base_url = item.base_url
  editForm.variables = JSON.stringify(item.variables || {}, null, 2)
  editForm.note = item.note
}

async function saveEdit() {
  if (!editing.value) return
  if (!editForm.name.trim()) {
    error.value = '请输入环境名称'
    return
  }
  let variables
  try {
    variables = parseVariables(editForm.variables)
  } catch (err) {
    error.value = err.message
    return
  }
  try {
    await api.updateEnvironment(editing.value.id, {
      name: editForm.name.trim(),
      kind: editForm.kind,
      base_url: editForm.base_url.trim(),
      variables,
      note: editForm.note.trim(),
    })
    editing.value = null
    notice.value = '环境已更新'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function remove(item) {
  if (!window.confirm(`删除环境「${item.name}」？`)) return
  try {
    await api.deleteEnvironment(item.id)
    notice.value = '环境已删除'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(async () => {
  await loadProjects()
  await refresh()
})
</script>

<template>
  <section class="stack">
    <article class="hero">
      <div>
        <p class="eyebrow">ENVIRONMENTS</p>
        <h2>环境管理</h2>
        <p class="muted">按项目维护 dev / test / staging / prod 的 Base URL 和变量，接口与 UI 自动化调试时可以直接抄地址。</p>
      </div>
      <div class="hero-metrics">
        <div>
          <strong>{{ rows.length }}</strong>
          <span>环境</span>
        </div>
        <div>
          <strong>{{ readyCount }}</strong>
          <span>已配地址</span>
        </div>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-else-if="notice" class="alert ok">{{ notice }}</p>

    <article class="card">
      <div class="toolbar">
        <select v-model="projectId" @change="onProjectChange">
          <option v-for="item in projects" :key="item.id" :value="item.id">#{{ item.id }} {{ item.name }}</option>
        </select>
        <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '加载中…' : '刷新' }}</button>
      </div>
    </article>

    <article class="card">
      <h3>新建环境</h3>
      <p class="muted">同名环境会提示已存在；变量用 JSON 对象，键值都会按字符串保存。</p>
      <div class="env-form">
        <input v-model="form.name" placeholder="环境名称，如：本地测试" maxlength="80" />
        <select v-model="form.kind">
          <option v-for="item in KINDS" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
        <input v-model="form.base_url" placeholder="Base URL，如：http://127.0.0.1:8000" />
        <input v-model="form.note" placeholder="备注（可选）" />
        <textarea v-model="form.variables" rows="2" class="mono" placeholder='变量 JSON（可选），如 {"token":"abc"}' />
        <button class="btn" @click="create">保存环境</button>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h3>环境列表</h3>
          <p class="muted">共 {{ rows.length }} 个</p>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>类型</th>
              <th>Base URL</th>
              <th>变量</th>
              <th>备注</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in rows" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td>{{ kindLabel(item.kind) }}</td>
              <td class="mono">{{ item.base_url || '未配置' }}</td>
              <td>{{ varCount(item) }} 个</td>
              <td class="cell-sub">{{ item.note || '—' }}</td>
              <td class="row-actions">
                <button class="btn ghost tiny" @click="openEdit(item)">编辑</button>
                <button class="btn ghost tiny" @click="remove(item)">删除</button>
              </td>
            </tr>
            <tr v-if="!rows.length">
              <td colspan="7" class="empty">这个项目还没有环境，先建一个。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <header>
          <h2>编辑环境 #{{ editing.id }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="editing = null">关闭</button>
        </header>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="env-form">
          <input v-model="editForm.name" placeholder="环境名称" maxlength="80" />
          <select v-model="editForm.kind">
            <option v-for="item in KINDS" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
          <input v-model="editForm.base_url" placeholder="Base URL" />
          <textarea v-model="editForm.variables" rows="4" class="mono" placeholder="变量 JSON" />
          <input v-model="editForm.note" placeholder="备注" />
        </div>
        <footer>
          <button class="btn ghost" @click="editing = null">取消</button>
          <button class="btn" @click="saveEdit">保存</button>
        </footer>
      </div>
    </div>
  </section>
</template>

<style scoped>
.env-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: flex-start;
}

.env-form input,
.env-form select,
.env-form textarea {
  flex: 1 1 200px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}

.env-form textarea {
  flex: 1 1 100%;
}

.env-form .btn {
  flex: 0 0 auto;
}

.modal {
  width: min(620px, 100%);
}
</style>
