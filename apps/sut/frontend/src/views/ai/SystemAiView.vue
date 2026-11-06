<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'

const tabs = [
  { key: 'llm', label: '大模型管理', kind: 'chat' },
  { key: 'embedding', label: '向量模型配置', kind: 'embedding' },
  { key: 'midscene', label: 'Midscene', kind: 'vision' },
]

const KIND_META = {
  chat: {
    title: '大模型管理',
    hint: '兼容 OpenAI 的 chat completions 接口，用例生成、需求分析、AI 归因都走这里。',
    defaults: { base_url: 'https://api.deepseek.com', model_name: 'deepseek-chat' },
    empty: '还没有大模型，先注册一套。',
  },
  embedding: {
    title: '向量模型配置',
    hint: '用于知识库检索的 embedding 模型。当前知识库走词面检索，配置好后可在此登记备用模型。',
    defaults: { base_url: 'https://api.siliconflow.cn/v1', model_name: 'BAAI/bge-m3' },
    empty: '还没有向量模型。',
  },
  vision: {
    title: 'Midscene',
    hint: 'UI 自动化的视觉识别模型（API Base / 模型名 / model family），用于不依赖选择器的操作。',
    defaults: { base_url: 'https://api.openai.com/v1', model_name: 'gpt-4o' },
    empty: '还没有视觉模型。',
  },
}

const tab = ref('llm')
const models = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

const meta = computed(() => KIND_META[tabs.find((item) => item.key === tab.value)?.kind || 'chat'])
const kind = computed(() => tabs.find((item) => item.key === tab.value)?.kind || 'chat')

const form = reactive({ name: '', provider: 'deepseek', base_url: '', model_name: '' })

function applyDefaults() {
  form.base_url = meta.value.defaults.base_url
  form.model_name = meta.value.defaults.model_name
  form.name = ''
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    models.value = await api.platformModels(kind.value)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function saveModel() {
  if (!form.name.trim()) {
    error.value = '请输入配置名称'
    return
  }
  error.value = ''
  notice.value = ''
  try {
    await api.createPlatformModel({
      name: form.name.trim(),
      kind: kind.value,
      provider: form.provider,
      base_url: form.base_url,
      model_name: form.model_name,
    })
    notice.value = `${meta.value.title}已保存；密钥只从服务端环境变量读取`
    applyDefaults()
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

watch(tab, () => {
  applyDefaults()
  notice.value = ''
  refresh()
})

onMounted(async () => {
  applyDefaults()
  await refresh()
})
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">SYSTEM AI</p>
        <h2>系统 AI 配置</h2>
        <p class="muted">
          可配置多套大模型 / 向量模型 / Midscene，并分别启用其一。未填写密钥时回退服务端环境变量。
        </p>
      </div>
    </article>

    <div class="tabs">
      <button v-for="item in tabs" :key="item.key" class="tab" :class="{ active: tab === item.key }" @click="tab = item.key">
        {{ item.label }}
      </button>
    </div>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="notice" class="alert">{{ notice }}</p>

    <article class="card">
      <div class="card-head">
        <div><h2>注册{{ meta.title.replace('管理', '').replace('配置', '') }}</h2><p>{{ meta.hint }}</p></div>
      </div>
      <form class="inline-form" @submit.prevent="saveModel">
        <input v-model="form.name" maxlength="80" placeholder="配置名称" />
        <input v-model="form.base_url" placeholder="Base URL" />
        <input v-model="form.model_name" placeholder="模型名" />
        <button class="btn">保存</button>
      </form>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>{{ meta.title }}列表</h2>
          <p>该分类共 {{ models.length }} 套，启用 {{ models.filter((m) => m.enabled).length }} 套</p>
        </div>
        <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '刷新中' : '刷新' }}</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>名称</th><th>模型</th><th>Base URL</th><th>密钥</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="item in models" :key="item.id">
              <td class="mono">#{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td class="mono">{{ item.model_name }}</td>
              <td class="mono muted">{{ item.base_url }}</td>
              <td>{{ item.api_key_masked || '环境变量' }}</td>
              <td><span class="badge" :class="item.enabled ? 'module-done' : 'module-planned'">{{ item.enabled ? '启用' : '停用' }}</span></td>
              <td class="row-actions">
                <button class="btn ghost tiny" @click="toggleModel(item)">{{ item.enabled ? '停用' : '启用' }}</button>
              </td>
            </tr>
            <tr v-if="!models.length && !loading"><td colspan="7" class="empty">{{ meta.empty }}</td></tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<style scoped>
.inline-form { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.inline-form input {
  flex: 1 1 180px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.row-actions { display: flex; gap: 6px; }
</style>
