<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../../api/client'

const projects = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const form = reactive({ name: '', description: '' })

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    projects.value = await api.platformProjects()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.name.trim()) {
    error.value = '请输入项目名称'
    return
  }
  error.value = ''
  try {
    const project = await api.createPlatformProject({
      name: form.name.trim(),
      description: form.description.trim(),
    })
    notice.value = `项目「${project.name}」已就绪（#${project.id}）`
    form.name = ''
    form.description = ''
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
        <p class="eyebrow">WORKSPACE</p>
        <h2>项目管理</h2>
        <p class="muted">项目是平台的核心载体：需求、用例、接口资产、自动化脚本、执行记录都挂在项目下。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ projects.length }}</strong><span>项目</span></div>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="notice" class="alert">{{ notice }}</p>

    <article class="card">
      <div class="card-head">
        <div><h2>新建项目</h2><p>同名项目会复用已有记录</p></div>
      </div>
      <form class="inline-form" @submit.prevent="create">
        <input v-model="form.name" maxlength="80" placeholder="项目名称，例如：电商后台" />
        <input v-model="form.description" placeholder="一句话描述（可选）" />
        <button class="btn">创建项目</button>
      </form>
    </article>

    <article class="card">
      <div class="card-head">
        <div><h2>项目列表</h2><p>共 {{ projects.length }} 个</p></div>
        <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '刷新中' : '刷新' }}</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>项目</th><th>描述</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in projects" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td class="muted">{{ item.description || '—' }}</td>
              <td class="row-actions">
                <RouterLink class="btn ghost" :to="{ path: '/overview', query: { project: item.id } }">概览</RouterLink>
                <RouterLink class="btn ghost" :to="{ path: '/functional', query: { project: item.id } }">生成用例</RouterLink>
              </td>
            </tr>
            <tr v-if="!projects.length && !loading"><td colspan="4" class="empty">还没有项目，先在上方创建一个。</td></tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<style scoped>
.inline-form { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.inline-form input { flex: 1 1 220px; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
.row-actions { display: flex; gap: 6px; }
</style>
