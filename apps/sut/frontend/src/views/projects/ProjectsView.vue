<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../../api/client'

const projects = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const view = ref('cards')
const drawerOpen = ref(false)
const creating = ref(false)
const form = reactive({ name: '', description: '' })
const summary = ref(null)

const withDescription = computed(() => projects.value.filter((item) => item.description).length)

const stats = computed(() => [
  { label: '项目总数', value: projects.value.length, hint: '全平台项目数' },
  { label: '填写了描述', value: withDescription.value, hint: '方便团队识别' },
  { label: '用例总数', value: summary.value?.cases ?? '—', hint: '含 AI 生成草稿' },
  { label: '通过率', value: summary.value ? `${Math.round((summary.value.pass_rate || 0) * 100)}%` : '—', hint: '按最近用例结果统计' },
])

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    projects.value = await api.platformProjects()
    summary.value = await api.platformSummary()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openDrawer() {
  drawerOpen.value = true
  error.value = ''
  notice.value = ''
}

function closeDrawer() {
  drawerOpen.value = false
  form.name = ''
  form.description = ''
}

async function create() {
  if (!form.name.trim()) {
    error.value = '请输入项目名称'
    return
  }
  error.value = ''
  creating.value = true
  try {
    const project = await api.createPlatformProject({
      name: form.name.trim(),
      description: form.description.trim(),
    })
    notice.value = `项目「${project.name}」已就绪（#${project.id}）`
    closeDrawer()
    await refresh()
  } catch (err) {
    error.value = err.message
  } finally {
    creating.value = false
  }
}

function createdAt(item) {
  return (item.created_at || '').slice(0, 10) || '—'
}

onMounted(refresh)
</script>

<template>
  <section class="stack">
    <article class="hero">
      <div>
        <p class="eyebrow">WORKSPACE</p>
        <h1>项目管理</h1>
        <p class="muted">项目是平台的核心载体：需求、用例、接口资产、自动化脚本、执行记录都挂在项目下。</p>
      </div>
      <button class="btn" type="button" @click="openDrawer">＋ 新建项目</button>
    </article>

    <p v-if="error && !drawerOpen" class="alert error">{{ error }}</p>
    <p v-if="notice" class="alert info">{{ notice }}</p>

    <div class="stats-grid">
      <div v-for="item in stats" :key="item.label" class="stat-card">
        <p class="stat-label">{{ item.label }}</p>
        <p class="stat-value">{{ item.value }}</p>
        <p class="stat-hint">{{ item.hint }}</p>
      </div>
    </div>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>项目列表</h2>
          <p class="muted">共 {{ projects.length }} 个</p>
        </div>
        <div class="head-tools">
          <div class="segmented">
            <button type="button" :class="{ on: view === 'cards' }" @click="view = 'cards'">卡片</button>
            <button type="button" :class="{ on: view === 'table' }" @click="view = 'table'">表格</button>
          </div>
          <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '刷新中…' : '刷新' }}</button>
        </div>
      </div>

      <div v-if="view === 'cards'" class="project-grid">
        <RouterLink
          v-for="item in projects"
          :key="item.id"
          class="project-card"
          :to="{ path: '/overview', query: { project: item.id } }"
        >
          <div class="project-top">
            <span class="id-badge">#{{ item.id }}</span>
            <strong>{{ item.name }}</strong>
          </div>
          <p class="project-desc">{{ item.description || '还没有描述' }}</p>
          <div class="project-foot">
            <span>创建于 {{ createdAt(item) }}</span>
            <span class="enter">进入 →</span>
          </div>
        </RouterLink>

        <button v-if="!projects.length && !loading" type="button" class="project-card ghost-card" @click="openDrawer">
          <span class="plus">＋</span>
          <strong>新建第一个项目</strong>
          <p class="project-desc">从「电商后台 / 客服工单 / IoT 设备」这类模板开始最快</p>
        </button>
      </div>

      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>项目</th><th>描述</th><th>创建时间</th><th class="right">操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in projects" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td class="muted">{{ item.description || '—' }}</td>
              <td class="muted">{{ createdAt(item) }}</td>
              <td class="row-actions">
                <RouterLink class="btn ghost tiny" :to="{ path: '/overview', query: { project: item.id } }">概览</RouterLink>
                <RouterLink class="btn tiny" :to="{ path: '/functional', query: { project: item.id } }">生成用例</RouterLink>
              </td>
            </tr>
            <tr v-if="!projects.length && !loading"><td colspan="5" class="empty">还没有项目，先在上方创建一个。</td></tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="drawerOpen" class="modal-mask drawer-mask" @click.self="closeDrawer">
      <aside class="drawer-panel">
        <header>
          <div>
            <p class="eyebrow">NEW PROJECT</p>
            <h2>新建项目</h2>
          </div>
          <button class="btn ghost tiny" type="button" data-modal-close @click="closeDrawer">关闭</button>
        </header>
        <p class="drawer-hint">同名项目会复用已有记录，不会重复创建。</p>
        <p v-if="error" class="alert error">{{ error }}</p>
        <label class="field">
          <span>项目名称</span>
          <input v-model="form.name" maxlength="80" placeholder="例如：电商后台" />
        </label>
        <label class="field">
          <span>一句话描述（可选）</span>
          <input v-model="form.description" maxlength="120" placeholder="例如：商品、订单、履约与售后的中台" />
        </label>
        <footer>
          <button class="btn ghost" type="button" @click="closeDrawer">取消</button>
          <button class="btn" type="button" :disabled="creating" @click="create">{{ creating ? '创建中…' : '创建项目' }}</button>
        </footer>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.head-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.segmented {
  display: inline-flex;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--bg);
}

.segmented button {
  padding: 4px 12px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--muted);
  font-family: var(--font);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.segmented button.on {
  background: var(--panel);
  color: var(--ink);
  box-shadow: var(--shadow-1);
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.project-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 18px;
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--panel);
  color: var(--ink);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.project-card:hover {
  transform: translateY(-2px);
  border-color: var(--line-strong);
  box-shadow: 0 12px 28px -16px rgba(77, 124, 15, 0.35);
}

.project-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-top strong {
  font-size: 14px;
  font-weight: 800;
}

.id-badge {
  padding: 2px 7px;
  border: 1px solid var(--lime-line);
  border-radius: 6px;
  background: var(--lime-soft);
  color: var(--lime-deep);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
}

.project-desc {
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.5;
  min-height: 38px;
}

.project-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
}

.enter {
  color: var(--lime-deep);
  font-weight: 700;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.project-card:hover .enter {
  opacity: 1;
}

.ghost-card {
  align-items: center;
  justify-content: center;
  text-align: center;
  border-style: dashed;
  background: var(--bg);
}

.ghost-card .plus {
  font-size: 22px;
  font-weight: 800;
  color: var(--lime-deep);
}

.drawer-mask {
  justify-content: flex-end;
  align-items: stretch;
  padding: 0;
}

.drawer-panel {
  width: min(420px, 100%);
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px 24px;
  background: var(--panel);
  border-left: 4px solid var(--lime);
  box-shadow: -20px 0 50px -30px rgba(28, 38, 7, 0.45);
  overflow-y: auto;
}

.drawer-panel header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.drawer-panel header h2 {
  margin: 4px 0 0;
  font-size: 19px;
  font-weight: 800;
}

.drawer-hint {
  margin: 0;
  color: var(--muted);
  font-size: 12.5px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
}

.field input {
  width: 100%;
}

.drawer-panel footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}

@media (max-width: 1180px) {
  .project-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .project-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
