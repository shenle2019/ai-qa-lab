<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import { pickProjectSmart, saveProjectId } from '../../utils/project'
import { askConfirm } from '../../composables/confirm'

const PROJECT_KEY = 'aiqa.modules.project'

const projects = ref([])
const projectId = ref(null)
const modules = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const form = reactive({ name: '', owner: '', description: '' })
const editing = ref(null)

const owners = computed(() => modules.value.filter((item) => item.owner).length)

function loadProjects() {
  return api.platformProjects().then(async (rows) => {
    projects.value = rows
    const picked = await pickProjectSmart(rows, PROJECT_KEY, () => api.platformCases())
    projectId.value = picked?.id ?? null
  })
}

async function refresh() {
  if (!projectId.value) return
  loading.value = true
  error.value = ''
  try {
    modules.value = await api.projectModules(projectId.value)
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

async function create() {
  if (!form.name.trim()) {
    error.value = '请输入模块名称'
    return
  }
  error.value = ''
  try {
    await api.createProjectModule({
      project_id: projectId.value,
      name: form.name.trim(),
      owner: form.owner.trim(),
      description: form.description.trim(),
    })
    form.name = ''
    form.owner = ''
    form.description = ''
    notice.value = '模块已创建'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

function openEdit(item) {
  editing.value = { ...item }
}

async function saveEdit() {
  error.value = ''
  try {
    await api.updateProjectModule(editing.value.id, {
      name: editing.value.name,
      owner: editing.value.owner,
      description: editing.value.description,
    })
    editing.value = null
    notice.value = '已保存'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function remove(item) {
  if (!(await askConfirm({ message: `删除模块「${item.name}」？` }))) return
  error.value = ''
  try {
    await api.deleteProjectModule(item.id)
    notice.value = '已删除'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(async () => {
  try {
    await loadProjects()
    await refresh()
  } catch (err) {
    error.value = err.message
  }
})
</script>

<template>
  <section class="stack">
    <header class="hero">
      <div>
        <p class="eyebrow">MODULES</p>
        <h1>模块管理</h1>
        <p class="muted">模块是用例、接口、UI 用例的分组单位；一个项目下可以有多个模块。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ modules.length }}</strong><span>模块</span></div>
        <div><strong>{{ owners }}</strong><span>已指派负责人</span></div>
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

    <article class="card">
      <div class="card-head">
        <div><h2>新建模块</h2><p class="muted">同名模块会提示已存在。</p></div>
      </div>
      <div class="inline-form">
        <input v-model="form.name" maxlength="80" placeholder="模块名称，例如：工单中心" />
        <input v-model="form.owner" maxlength="60" placeholder="负责人（可选）" />
        <input v-model="form.description" placeholder="一句话说明（可选）" />
        <button class="btn" @click="create">新建模块</button>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div><h2>模块列表</h2><p class="muted">共 {{ modules.length }} 个</p></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>模块</th><th>负责人</th><th>说明</th><th>创建时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in modules" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td>{{ item.owner || '未指派' }}</td>
              <td class="muted">{{ item.description || '—' }}</td>
              <td class="muted">{{ (item.created_at || '').replace('T', ' ').slice(0, 19) }}</td>
              <td class="row-actions">
                <button class="btn ghost tiny" @click="openEdit(item)">编辑</button>
                <button class="btn ghost tiny danger" @click="remove(item)">删除</button>
              </td>
            </tr>
            <tr v-if="!modules.length"><td colspan="6" class="empty">还没有模块，先建一个。</td></tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <header>
          <h2>编辑模块 #{{ editing.id }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="editing = null">关闭</button>
        </header>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label>名称<input v-model="editing.name" /></label>
          <label>负责人<input v-model="editing.owner" /></label>
          <label>说明<textarea v-model="editing.description" rows="3" /></label>
          <div class="form-actions">
            <button class="btn" @click="saveEdit">保存</button>
            <button class="btn ghost" @click="editing = null">取消</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.toolbar select { width: auto; min-width: 190px; }
.hero-metrics { display: flex; gap: 30px; }
.hero-metrics div { display: flex; flex-direction: column; }
.hero-metrics strong { font-size: 26px; }
.hero-metrics span { font-size: 12px; color: var(--muted); }
.inline-form { display: flex; flex-wrap: wrap; gap: 8px; }
.inline-form input {
  flex: 1 1 180px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.form-stack { display: flex; flex-direction: column; gap: 12px; }
.form-stack label { display: flex; flex-direction: column; gap: 6px; font-size: 12.5px; color: var(--muted); }
.form-stack input,
.form-stack textarea {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.form-actions { display: flex; gap: 10px; }
.alert.ok { color: #4ade80; }
.modal-mask {
  position: fixed; inset: 0; background: rgba(3, 6, 12, 0.72);
  display: flex; align-items: center; justify-content: center; z-index: 40; padding: 24px;
}
.modal {
  width: min(620px, 100%); max-height: 88vh; overflow-y: auto;
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 18px 20px;
}
.modal header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.modal header h2 { font-size: 18px; margin: 0; }
</style>
