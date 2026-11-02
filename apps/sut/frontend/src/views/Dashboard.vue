<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useTicketStore } from '../stores/tickets'
import { api } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'

const store = useTicketStore()
const chartEl = ref(null)
let chart = null

const kbQuestion = ref('')
const kbAnswer = ref('')
const kbLoading = ref(false)
const kbError = ref('')

const counts = computed(() => store.counts)
const recent = computed(() => store.items.slice(0, 6))

function renderChart() {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#9fb0c9' }, itemWidth: 10, itemHeight: 10 },
    series: [
      {
        type: 'pie',
        radius: ['54%', '76%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#0e1728', borderWidth: 4, borderRadius: 6 },
        label: { color: '#dbe7f7', formatter: '{b}\n{c}' },
        labelLine: { lineStyle: { color: 'rgba(148,163,184,.35)' } },
        data: [
          { name: '待处理', value: counts.value.open, itemStyle: { color: '#fbbf24' } },
          { name: '处理中', value: counts.value.in_progress, itemStyle: { color: '#38bdf8' } },
          { name: '已关闭', value: counts.value.closed, itemStyle: { color: '#34d399' } },
        ],
      },
    ],
  })
}

function resize() {
  chart?.resize()
}

onMounted(async () => {
  await store.fetchAll()
  renderChart()
  window.addEventListener('resize', resize)
})

watch(counts, renderChart, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})

async function askKnowledge() {
  if (!kbQuestion.value.trim()) return
  kbLoading.value = true
  kbError.value = ''
  kbAnswer.value = ''
  try {
    const result = await api.queryKnowledge({ question: kbQuestion.value, top_k: 3 })
    kbAnswer.value = result.answer
  } catch (error) {
    kbError.value = error.message
  } finally {
    kbLoading.value = false
  }
}
</script>

<template>
  <section class="stack">
    <div class="stats-grid">
      <article class="stat-card">
        <p class="stat-label">全部工单</p>
        <strong class="stat-value">{{ counts.total }}</strong>
        <span class="stat-hint">当前系统总量</span>
      </article>
      <article class="stat-card amber">
        <p class="stat-label">待处理</p>
        <strong class="stat-value">{{ counts.open }}</strong>
        <span class="stat-hint">等待分派或处理</span>
      </article>
      <article class="stat-card cyan">
        <p class="stat-label">处理中</p>
        <strong class="stat-value">{{ counts.in_progress }}</strong>
        <span class="stat-hint">正在跟进</span>
      </article>
      <article class="stat-card green">
        <p class="stat-label">高优先级未关闭</p>
        <strong class="stat-value">{{ store.highPriority }}</strong>
        <span class="stat-hint">需要优先处理</span>
      </article>
    </div>

    <div class="split-grid">
      <article class="card">
        <div class="card-head">
          <div>
            <h2>工单状态分布</h2>
            <p>实时统计当前工单池</p>
          </div>
          <button class="btn ghost" :disabled="store.loading" @click="store.fetchAll">刷新</button>
        </div>
        <div ref="chartEl" class="chart"></div>
      </article>

      <article class="card">
        <div class="card-head">
          <div>
            <h2>知识库快问</h2>
            <p>调用 /api/kb/query 的 mock 链路</p>
          </div>
        </div>
        <form class="inline-form" @submit.prevent="askKnowledge">
          <input v-model="kbQuestion" placeholder="例如：工单如何升级优先级？" />
          <button class="btn" :disabled="kbLoading">{{ kbLoading ? '查询中' : '查询' }}</button>
        </form>
        <p v-if="kbError" class="alert error">{{ kbError }}</p>
        <div v-if="kbAnswer" class="answer-box">
          <span class="answer-tag">mock answer</span>
          <p>{{ kbAnswer }}</p>
        </div>
        <p v-else class="muted">输入问题后，答案会显示在这里。模块 08 会替换为真实 RAG 链路。</p>
      </article>
    </div>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>最近工单</h2>
          <p>最新创建的 6 条记录</p>
        </div>
        <RouterLink to="/tickets" class="btn ghost">查看全部</RouterLink>
      </div>

      <p v-if="store.error" class="alert error">{{ store.error }}</p>
      <div v-if="store.loading" class="muted">加载中…</div>
      <div v-else-if="!recent.length" class="empty">还没有工单，去工单管理页创建第一条。</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>优先级</th>
              <th>状态</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ticket in recent" :key="ticket.id">
              <td class="mono">#{{ ticket.id }}</td>
              <td>
                <strong>{{ ticket.title }}</strong>
                <p v-if="ticket.description" class="cell-sub">{{ ticket.description }}</p>
              </td>
              <td><span class="badge" :class="`priority-${ticket.priority}`">{{ ticket.priority }}</span></td>
              <td><StatusBadge :status="ticket.status" /></td>
              <td class="muted">{{ new Date(ticket.created_at).toLocaleString('zh-CN', { hour12: false }) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>
