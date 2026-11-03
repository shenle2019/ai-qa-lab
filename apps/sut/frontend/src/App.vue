<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api/client'

const route = useRoute()
const online = ref(false)
const checking = ref(true)
const title = computed(() => route.meta.title || 'AI全栈测试开发平台-shenle')

async function checkHealth() {
  checking.value = true
  try {
    await api.health()
    online.value = true
  } catch {
    online.value = false
  } finally {
    checking.value = false
  }
}

onMounted(checkHealth)
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
        <RouterLink to="/report" class="nav-item"><span class="nav-icon">▦</span>项目报告</RouterLink>
        <RouterLink to="/portfolio" class="nav-item"><span class="nav-icon">▣</span>模块验收</RouterLink>
      </nav>

      <div class="sidebar-foot">
        <div class="env-chip">
          <span class="dot" :class="online ? 'ok' : 'bad'"></span>
          {{ checking ? '检测中' : online ? 'SUT 在线' : 'SUT 离线' }}
        </div>
        <p>v0.2.0 · FastAPI + Vue 3</p>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div>
          <p class="eyebrow">AI QUALITY ENGINEERING</p>
          <h1>{{ title }}</h1>
        </div>
        <div class="topbar-actions">
          <button class="btn ghost" :disabled="checking" @click="checkHealth">刷新状态</button>
          <a class="btn" href="/docs" target="_blank" rel="noreferrer">API 文档</a>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
