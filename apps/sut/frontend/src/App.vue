<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api/client'

const route = useRoute()
const online = ref(false)
const checking = ref(true)
const title = computed(() => route.meta.title || 'AI全栈测试开发平台-shenle')
const showDocs = ['localhost', '127.0.0.1'].includes(window.location.hostname)
const healthNotice = ref('')
let healthTimer = null
let noticeTimer = null

async function checkHealth(announce = false) {
  checking.value = true
  try {
    await api.health()
    online.value = true
  } catch {
    online.value = false
  } finally {
    checking.value = false
    if (announce) {
      healthNotice.value = online.value ? '已刷新：SUT 在线' : '已刷新：SUT 离线'
      clearTimeout(noticeTimer)
      noticeTimer = setTimeout(() => {
        healthNotice.value = ''
      }, 2000)
    }
  }
}

onMounted(() => {
  checkHealth()
  healthTimer = setInterval(checkHealth, 30000)
})

onUnmounted(() => {
  if (healthTimer) clearInterval(healthTimer)
  clearTimeout(noticeTimer)
})
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">QA</div>
        <div>
          <strong>AI全栈测试开发平台</strong>
          <span style="text-transform:none;letter-spacing:0">shenle</span>
        </div>
      </div>

      <nav class="nav">
        <RouterLink to="/" class="nav-item"><span class="nav-icon">◎</span>仪表盘</RouterLink>
        <RouterLink to="/tickets" class="nav-item"><span class="nav-icon">▤</span>工单管理</RouterLink>
        <RouterLink to="/workbench" class="nav-item"><span class="nav-icon">⌘</span>API 工作台</RouterLink>
        <RouterLink to="/knowledge" class="nav-item"><span class="nav-icon">✦</span>知识库问答</RouterLink>
        <RouterLink to="/platform" class="nav-item"><span class="nav-icon">▥</span>测试平台</RouterLink>
        <RouterLink to="/models" class="nav-item"><span class="nav-icon">◎</span>模型中心</RouterLink>
        <RouterLink to="/testcases" class="nav-item"><span class="nav-icon">☑</span>测试用例</RouterLink>
        <RouterLink to="/methodology" class="nav-item"><span class="nav-icon">◈</span>方法论</RouterLink>
        <RouterLink to="/report" class="nav-item"><span class="nav-icon">▦</span>项目报告</RouterLink>
        <RouterLink to="/portfolio" class="nav-item"><span class="nav-icon">▣</span>模块验收</RouterLink>
      </nav>

      <div class="sidebar-foot">
        <div class="env-chip">
          <span class="dot" :class="online ? 'ok' : 'bad'"></span>
          {{ checking ? '检测中' : online ? 'SUT 在线' : 'SUT 离线' }}
        </div>
        <RouterLink to="/login" class="nav-item"><span class="nav-icon">⚿</span>访问密钥</RouterLink>
        <p>v1.1.0 · FastAPI + Vue 3</p>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div>
          <p class="eyebrow">AI QUALITY ENGINEERING</p>
          <h1>{{ title }}</h1>
        </div>
        <div class="topbar-actions">
          <span v-if="healthNotice" class="muted">{{ healthNotice }}</span>
          <button class="btn ghost" :disabled="checking" @click="checkHealth(true)">{{ checking ? '检测中…' : '刷新状态' }}</button>
          <a v-if="showDocs" class="btn" href="/docs" target="_blank" rel="noreferrer">API 文档</a>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
