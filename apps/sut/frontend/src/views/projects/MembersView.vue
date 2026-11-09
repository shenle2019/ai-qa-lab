<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import { pickProjectSmart, saveProjectId } from '../../utils/project'
import { askConfirm } from '../../composables/confirm'

const PROJECT_KEY = 'aiqa.members.project'
const ROLES = ['测试', '开发', '产品', '运维', '负责人']

const projects = ref([])
const projectId = ref(null)
const members = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const form = reactive({ name: '', role: '测试', email: '' })
const editing = ref(null)

const roleCount = computed(() => new Set(members.value.map((item) => item.role)).size)

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
    members.value = await api.projectMembers(projectId.value)
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
    error.value = '请输入成员姓名'
    return
  }
  error.value = ''
  try {
    await api.createProjectMember({
      project_id: projectId.value,
      name: form.name.trim(),
      role: form.role,
      email: form.email.trim(),
    })
    form.name = ''
    form.email = ''
    notice.value = '成员已添加'
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
    await api.updateProjectMember(editing.value.id, {
      name: editing.value.name,
      role: editing.value.role,
      email: editing.value.email,
    })
    editing.value = null
    notice.value = '已保存'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function remove(item) {
  if (!(await askConfirm({ message: `移除成员「${item.name}」？` }))) return
  error.value = ''
  try {
    await api.deleteProjectMember(item.id)
    notice.value = '已移除'
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
        <p class="eyebrow">MEMBERS</p>
        <h1>成员管理</h1>
        <p class="muted">按项目维护成员与角色；角色决定后续谁可以审批用例、执行计划。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ members.length }}</strong><span>成员</span></div>
        <div><strong>{{ roleCount }}</strong><span>角色数</span></div>
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
        <div><h2>添加成员</h2><p class="muted">同名成员会提示已存在。</p></div>
      </div>
      <div class="inline-form">
        <input v-model="form.name" maxlength="60" placeholder="姓名" />
        <select v-model="form.role">
          <option v-for="role in ROLES" :key="role" :value="role">{{ role }}</option>
        </select>
        <input v-model="form.email" maxlength="120" placeholder="邮箱（可选）" />
        <button class="btn" @click="create">添加成员</button>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div><h2>成员列表</h2><p class="muted">共 {{ members.length }} 人</p></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>姓名</th><th>角色</th><th>邮箱</th><th>加入时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in members" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td><span class="badge">{{ item.role }}</span></td>
              <td class="muted">{{ item.email || '—' }}</td>
              <td class="muted">{{ (item.created_at || '').replace('T', ' ').slice(0, 19) }}</td>
              <td class="row-actions">
                <button class="btn ghost tiny" @click="openEdit(item)">编辑</button>
                <button class="btn ghost tiny danger" @click="remove(item)">移除</button>
              </td>
            </tr>
            <tr v-if="!members.length"><td colspan="6" class="empty">还没有成员。</td></tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <header>
          <h2>编辑成员 #{{ editing.id }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="editing = null">关闭</button>
        </header>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label>姓名<input v-model="editing.name" /></label>
          <label>角色
            <select v-model="editing.role">
              <option v-for="role in ROLES" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>
          <label>邮箱<input v-model="editing.email" /></label>
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
.inline-form input,
.inline-form select {
  flex: 1 1 160px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.inline-form select { flex: 0 0 120px; }
.form-stack { display: flex; flex-direction: column; gap: 12px; }
.form-stack label { display: flex; flex-direction: column; gap: 6px; font-size: 12.5px; color: var(--muted); }
.form-stack input,
.form-stack select {
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
