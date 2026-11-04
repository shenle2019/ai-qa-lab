<script setup>
import { computed, onMounted, ref } from 'vue'

const catalog = ref(null)
const loading = ref(true)
const error = ref('')
const query = ref('')
const status = ref('all')
const category = ref('all')

const categories = computed(() => catalog.value?.categories || [])

const rows = computed(() => {
  if (!catalog.value) return []
  const keyword = query.value.trim().toLowerCase()
  return categories.value
    .filter((item) => category.value === 'all' || item.name === category.value)
    .flatMap((item) =>
      item.cases.map((test) => ({ ...test, category: item.name, method: item.method })),
    )
    .filter((item) => status.value === 'all' || item.status === status.value)
    .filter((item) => !keyword || item.name.toLowerCase().includes(keyword))
})

const summary = computed(() => ({
  total: catalog.value?.total || 0,
  passed: catalog.value?.passed || 0,
  skipped: catalog.value?.skipped || 0,
  failed: catalog.value?.failed || 0,
}))

function statusClass(value) {
  if (value === 'passed') return 'module-done'
  if (value === 'failed') return 'module-planned'
  return ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch('/portfolio/test-cases.json', { cache: 'no-store' })
    if (!response.ok) throw new Error(`加载失败：${response.status}`)
    catalog.value = await response.json()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">TEST CATALOG</p>
        <h2>全部测试用例一览</h2>
        <p class="muted">按类别、状态和关键字筛选；数据来自最近一次执行结果，不是手写清单。</p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ summary.total }}</strong><span>用例总数</span></div>
        <div><strong>{{ summary.passed }}</strong><span>通过</span></div>
        <div><strong>{{ summary.skipped }}</strong><span>跳过</span></div>
        <div><strong>{{ summary.failed }}</strong><span>失败</span></div>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>

    <div class="toolbar card">
      <div class="filters">
        <input v-model="query" class="search" placeholder="搜索用例名…" />
        <select v-model="status">
          <option value="all">全部状态</option>
          <option value="passed">通过</option>
          <option value="skipped">跳过</option>
          <option value="failed">失败</option>
        </select>
        <select v-model="category">
          <option value="all">全部类别</option>
          <option v-for="item in categories" :key="item.name" :value="item.name">{{ item.name }}</option>
        </select>
      </div>
      <div class="toolbar-actions">
        <span class="muted">{{ rows.length }} / {{ summary.total }} 条</span>
        <a class="btn ghost" :href="catalog?.report_url || '/portfolio/test-report-2026-11-04.html'" target="_blank" rel="noreferrer">完整报告</a>
        <button class="btn ghost" :disabled="loading" @click="load">{{ loading ? '刷新中' : '刷新' }}</button>
      </div>
    </div>

    <div class="cat-grid">
      <button
        v-for="item in categories"
        :key="item.name"
        class="cat-card"
        :class="{ active: category === item.name }"
        @click="category = category === item.name ? 'all' : item.name"
      >
        <strong>{{ item.name }}</strong>
        <span>{{ item.total }} 条 · 通过 {{ item.passed }} · 跳过 {{ item.skipped }}</span>
        <small>{{ item.method }}</small>
      </button>
    </div>

    <article class="card">
      <div class="card-head">
        <div><h2>用例明细</h2><p>通过、跳过、失败与耗时</p></div>
      </div>
      <div v-if="loading" class="muted">加载中…</div>
      <div v-else-if="!rows.length" class="empty">没有匹配的用例。</div>
      <div v-else class="table-wrap">
        <table>
          <thead><tr><th>类别</th><th>用例名</th><th>状态</th><th>耗时</th></tr></thead>
          <tbody>
            <tr v-for="item in rows" :key="`${item.category}-${item.name}`">
              <td>{{ item.category }}</td>
              <td class="mono">{{ item.name }}</td>
              <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
              <td>{{ item.duration_ms }} ms</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<style scoped>
.cat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.cat-card { display: flex; flex-direction: column; gap: 4px; padding: 14px 16px; text-align: left; border: 1px solid var(--line); border-radius: 12px; color: var(--text); background: rgba(14, 23, 40, 0.6); cursor: pointer; }
.cat-card span { color: var(--muted); font-size: 12px; }
.cat-card small { color: rgba(159, 176, 201, 0.75); font-size: 11px; }
.cat-card.active { border-color: var(--accent); background: rgba(56, 189, 248, 0.08); }
</style>
