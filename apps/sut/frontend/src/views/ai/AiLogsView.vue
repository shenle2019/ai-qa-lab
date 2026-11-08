<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api/client'
import EmptyState from '../../components/EmptyState.vue'

const calls = ref([])
const loading = ref(false)
const error = ref('')
const limit = ref(50)

const totalTokens = computed(() =>
  calls.value.reduce((sum, item) => sum + item.prompt_tokens + item.completion_tokens, 0),
)
const failed = computed(() => calls.value.filter((item) => item.status !== 'ok').length)

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    calls.value = await api.platformModelCalls(limit.value)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">AI CALL LOG</p>
        <h2>AI 调用日志</h2>
        <p class="muted">每次大模型调用都记录用途、耗时、token 与失败原因，方便定位是 prompt 问题还是模型问题。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ calls.length }}</strong><span>最近调用</span></div>
        <div><strong>{{ failed }}</strong><span>失败</span></div>
        <div><strong>{{ totalTokens }}</strong><span>token</span></div>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>

    <article class="card">
      <div class="card-head">
        <div><h2>调用记录</h2><p>最近 {{ limit }} 次</p></div>
        <div class="row-actions">
          <select v-model.number="limit" class="mini-select" @change="refresh">
            <option :value="20">20 条</option>
            <option :value="50">50 条</option>
            <option :value="100">100 条</option>
          </select>
          <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '刷新中' : '刷新' }}</button>
        </div>
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
            <tr v-if="!calls.length && !loading">
              <td colspan="6">
                <EmptyState
                  icon="logs"
                  title="还没有调用记录"
                  hint="跑一次需求分析、用例生成或 AI 归因，这里就会记录模型、耗时和 token。"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<style scoped>
.row-actions { display: flex; gap: 6px; align-items: center; }
.mini-select { padding: 6px 8px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
</style>
