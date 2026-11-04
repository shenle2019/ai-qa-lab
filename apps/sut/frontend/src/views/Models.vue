<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api/client'

const models = ref([])
const calls = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

const form = reactive({
  name: 'DeepSeek 默认',
  provider: 'deepseek',
  base_url: 'https://api.deepseek.com',
  model_name: 'deepseek-chat',
  api_key: '',
})

const totalTokens = computed(() =>
  calls.value.reduce((sum, item) => sum + item.prompt_tokens + item.completion_tokens, 0),
)

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [m, c] = await Promise.all([api.platformModels(), api.platformModelCalls()])
    models.value = m
    calls.value = c
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createModel() {
  if (!form.name.trim()) return
  error.value = ''
  try {
    await api.createPlatformModel({ ...form, name: form.name.trim() })
    form.api_key = ''
    notice.value = '模型已保存，密钥仅保存在服务端'
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function toggleModel(item) {
  try {
    await api.updatePlatformModel(item.id, { enabled: !item.enabled })
    await refresh()
  } catch (err) {
    error.value = err.message
  }
}

async function testModel(item) {
  notice.value = `正在测试 ${item.name}…`
  try {
    const result = await api.testPlatformModel(item.id)
    notice.value = result.ok ? `连接成功，${result.latency_ms} ms` : `连接失败：${result.message}`
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
        <p class="eyebrow">MODEL CENTER</p>
        <h2>模型注册、连通性测试与调用记录</h2>
        <p class="muted">模型配置只保存在服务端，接口只返回掩码。每次调用都记录用途、耗时与 token，便于核账。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ models.length }}</strong><span>模型</span></div>
        <div><strong>{{ calls.length }}</strong><span>最近调用</span></div>
        <div><strong>{{ totalTokens }}</strong><span>token（最近）</span></div>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="notice" class="alert">{{ notice }}</p>

    <article class="card">
      <div class="card-head">
        <div><h2>注册模型</h2><p>兼容 OpenAI 格式的 chat completions 接口</p></div>
      </div>
      <form class="model-form" @submit.prevent="createModel">
        <input v-model="form.name" placeholder="配置名称" />
        <input v-model="form.base_url" placeholder="Base URL" />
        <input v-model="form.model_name" placeholder="模型名" />
        <input v-model="form.api_key" type="password" placeholder="API Key（留空则读环境变量）" />
        <button class="btn">保存模型</button>
      </form>
    </article>

    <article class="card">
      <div class="card-head">
        <div><h2>模型列表</h2><p>启停与连通性测试</p></div>
        <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '刷新中' : '刷新' }}</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>名称</th><th>模型</th><th>密钥</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in models" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong><p class="cell-sub">{{ item.base_url }}</p></td>
              <td class="mono">{{ item.model_name }}</td>
              <td>{{ item.api_key_masked || (item.has_api_key ? '环境变量' : '未配置') }}</td>
              <td><span class="badge" :class="item.enabled ? 'module-done' : 'module-planned'">{{ item.enabled ? '启用' : '停用' }}</span></td>
              <td class="row-actions">
                <button class="btn ghost" @click="testModel(item)">测试</button>
                <button class="btn ghost" @click="toggleModel(item)">{{ item.enabled ? '停用' : '启用' }}</button>
              </td>
            </tr>
            <tr v-if="!models.length"><td colspan="6" class="empty">还没有模型配置。</td></tr>
          </tbody>
        </table>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div><h2>调用记录</h2><p>最近 20 次，含失败原因</p></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>时间</th><th>模型</th><th>用途</th><th>状态</th><th>耗时</th><th>token</th></tr></thead>
          <tbody>
            <tr v-for="item in calls" :key="item.id">
              <td class="muted">{{ formatTime(item.created_at) }}</td>
              <td class="mono">{{ item.model_name }}</td>
              <td>{{ item.purpose }}<p v-if="item.error" class="cell-sub">{{ item.error }}</p></td>
              <td><span class="badge" :class="item.status === 'ok' ? 'module-done' : 'module-planned'">{{ item.status }}</span></td>
              <td>{{ item.duration_ms }} ms</td>
              <td>{{ item.prompt_tokens + item.completion_tokens }}</td>
            </tr>
            <tr v-if="!calls.length"><td colspan="6" class="empty">还没有调用记录。</td></tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<style scoped>
.model-form { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.model-form input { flex: 1 1 180px; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
.row-actions { display: flex; gap: 6px; }
</style>
