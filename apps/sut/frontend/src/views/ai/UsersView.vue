<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'

const ROLES = ['管理员', '测试', '开发', '产品', '访客']
const STATUS_TEXT = { active: '启用', disabled: '停用' }

const users = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const authMode = ref('')

const form = reactive({ name: '', email: '', role: '测试', status: 'active', note: '' })
const editing = ref(null)
const editor = reactive({ email: '', role: '测试', status: 'active', note: '' })

const stats = computed(() => ({
  total: users.value.length,
  active: users.value.filter((item) => item.status === 'active').length,
  admin: users.value.filter((item) => item.role === '管理员').length,
}))

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    users.value = await api.platformUsers()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createUser() {
  if (!form.name.trim()) {
    error.value = '请输入用户名'
    return
  }
  error.value = ''
  notice.value = ''
  try {
    await api.createPlatformUser({ ...form, name: form.name.trim() })
    notice.value = `已添加 ${form.name}`
    form.name = ''
    form.email = ''
    form.note = ''
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

function openEdit(user) {
  editing.value = user
  editor.email = user.email
  editor.role = user.role
  editor.status = user.status
  editor.note = user.note
}

async function saveEdit() {
  if (!editing.value) return
  try {
    await api.updatePlatformUser(editing.value.id, { ...editor })
    editing.value = null
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function toggleStatus(user) {
  try {
    await api.updatePlatformUser(user.id, { status: user.status === 'active' ? 'disabled' : 'active' })
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function removeUser(user) {
  try {
    await api.deletePlatformUser(user.id)
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function loadAuthMode() {
  try {
    const health = await api.health()
    authMode.value = health.auth === 'production' ? '生产模式：写接口需要 Bearer 访问密钥' : '开发模式：未开启鉴权'
  } catch (err) {
    authMode.value = '无法读取鉴权状态'
  }
}

onMounted(async () => {
  await Promise.all([refresh(), loadAuthMode()])
})
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">USERS</p>
        <h2>用户管理</h2>
        <p class="muted">
          平台账号目录：谁可以进入平台、以什么角色。实际鉴权仍由服务端访问密钥控制，账号用于分配与追溯。
        </p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ stats.total }}</strong><span>账号</span></div>
        <div><strong>{{ stats.active }}</strong><span>启用</span></div>
        <div><strong>{{ stats.admin }}</strong><span>管理员</span></div>
      </div>
    </article>

    <p class="muted auth-note">当前鉴权：{{ authMode }}</p>
    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="notice" class="alert">{{ notice }}</p>

    <article class="card">
      <div class="card-head">
        <div><h2>新建账号</h2><p>同名账号会提示已存在。</p></div>
      </div>
      <form class="user-form" @submit.prevent="createUser">
        <input v-model="form.name" maxlength="60" placeholder="用户名" />
        <input v-model="form.email" maxlength="160" placeholder="邮箱（可选）" />
        <select v-model="form.role">
          <option v-for="role in ROLES" :key="role" :value="role">{{ role }}</option>
        </select>
        <input v-model="form.note" maxlength="400" placeholder="备注（可选）" />
        <button class="btn">添加</button>
      </form>
    </article>

    <article class="card">
      <div class="card-head">
        <div><h2>账号列表</h2><p>共 {{ users.length }} 个</p></div>
        <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '刷新中' : '刷新' }}</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th><th>状态</th><th>备注</th><th>创建时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td class="mono">#{{ user.id }}</td>
              <td><strong>{{ user.name }}</strong></td>
              <td class="muted">{{ user.email || '—' }}</td>
              <td><span class="badge">{{ user.role }}</span></td>
              <td>
                <span class="badge" :class="user.status === 'active' ? 'module-done' : 'module-planned'">
                  {{ STATUS_TEXT[user.status] }}
                </span>
              </td>
              <td class="muted">{{ user.note || '—' }}</td>
              <td class="cell-sub">{{ user.created_at?.slice(0, 16).replace('T', ' ') }}</td>
              <td class="row-actions">
                <button class="btn ghost tiny" @click="openEdit(user)">编辑</button>
                <button class="btn ghost tiny" @click="toggleStatus(user)">{{ user.status === 'active' ? '停用' : '启用' }}</button>
                <button class="btn ghost tiny danger" @click="removeUser(user)">删除</button>
              </td>
            </tr>
            <tr v-if="!users.length && !loading"><td colspan="8" class="empty">还没有账号，先添加一个。</td></tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <header>
          <h2>编辑账号 #{{ editing.id }}</h2>
          <button class="btn ghost tiny" data-modal-close @click="editing = null">关闭</button>
        </header>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label>邮箱<input v-model="editor.email" maxlength="160" /></label>
          <label>角色
            <select v-model="editor.role">
              <option v-for="role in ROLES" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>
          <label>状态
            <select v-model="editor.status">
              <option value="active">启用</option>
              <option value="disabled">停用</option>
            </select>
          </label>
          <label>备注<textarea v-model="editor.note" rows="3" maxlength="400"></textarea></label>
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
.user-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 12px 0;
}
.user-form input,
.user-form select {
  flex: 1 1 160px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.auth-note {
  font-size: 12px;
}
.row-actions {
  display: flex;
  gap: 6px;
}
.btn.danger {
  color: var(--red);
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
  width: min(560px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 18px 20px;
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
  margin-top: 14px;
}
.form-stack {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}
.form-stack label {
  display: grid;
  gap: 4px;
  font-size: 12.6px;
  color: var(--muted);
}
.form-stack input,
.form-stack select,
.form-stack textarea {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
</style>
