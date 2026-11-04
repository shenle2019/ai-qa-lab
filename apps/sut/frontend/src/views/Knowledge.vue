<script setup>
import { ref } from 'vue'
import { api } from '../api/client'

const question = ref('工单如何升级优先级？')
const topK = ref(3)
const loading = ref(false)
const error = ref('')
const answer = ref('')
const latency = ref(null)
const history = ref([])

const suggestions = [
  '工单如何升级优先级？',
  '如何关闭一个工单？',
  '知识库支持哪些数据源？',
]

async function ask() {
  if (!question.value.trim()) return
  loading.value = true
  error.value = ''
  answer.value = ''
  const started = performance.now()
  try {
    const result = await api.queryKnowledge({ question: question.value, top_k: Number(topK.value) })
    answer.value = result.answer
    latency.value = Math.round(performance.now() - started)
    history.value.unshift({
      question: question.value,
      answer: result.answer,
      topK: result.top_k,
      latency: latency.value,
      at: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
    })
    history.value = history.value.slice(0, 8)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function useSuggestion(text) {
  question.value = text
  ask()
}
</script>

<template>
  <section class="stack">
    <article class="hero card">
      <div>
        <p class="eyebrow">KNOWLEDGE BASE</p>
        <h2>用问题驱动知识检索</h2>
        <p class="muted">当前基于工单与内置知识做词法检索，返回真实来源；向量检索与自动评测是后续项。</p>
      </div>
      <div class="hero-metric">
        <strong>{{ latency ?? '—' }}</strong>
        <span>ms 最近耗时</span>
      </div>
    </article>

    <div class="split-grid">
      <article class="card">
        <div class="card-head">
          <div>
            <h2>提问</h2>
            <p>调用 POST /api/kb/query</p>
          </div>
        </div>
        <form class="stack-sm" @submit.prevent="ask">
          <label>
            <span>问题</span>
            <textarea v-model="question" rows="4" maxlength="1000" placeholder="输入你要问知识库的问题"></textarea>
          </label>
          <label>
            <span>Top K</span>
            <input v-model="topK" type="number" min="1" max="10" />
          </label>
          <button class="btn" :disabled="loading">{{ loading ? '检索中…' : '提交问题' }}</button>
        </form>
        <div class="suggestions">
          <button v-for="item in suggestions" :key="item" class="chip" @click="useSuggestion(item)">{{ item }}</button>
        </div>
      </article>

      <article class="card">
        <div class="card-head">
          <div>
            <h2>回答</h2>
            <p>结构化结果，后续接真实模型</p>
          </div>
          <span v-if="latency !== null" class="badge status-in_progress">{{ latency }} ms</span>
        </div>
        <p v-if="error" class="alert error">{{ error }}</p>
        <div v-if="answer" class="answer-box">
          <span class="answer-tag">answer</span>
          <p>{{ answer }}</p>
        </div>
        <div v-else class="empty">提交问题后显示回答。</div>
      </article>
    </div>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>本次会话历史</h2>
          <p>最近 8 次提问</p>
        </div>
      </div>
      <div v-if="!history.length" class="empty">还没有提问记录。</div>
      <ul v-else class="history">
        <li v-for="(item, index) in history" :key="index">
          <div class="history-head">
            <strong>{{ item.question }}</strong>
            <span class="muted">{{ item.at }} · top_k={{ item.topK }} · {{ item.latency }}ms</span>
          </div>
          <p>{{ item.answer }}</p>
        </li>
      </ul>
    </article>
  </section>
</template>
