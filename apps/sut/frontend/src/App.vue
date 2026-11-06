<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { api } from './api/client'

const route = useRoute()
const online = ref(false)
const checking = ref(true)
const menuOpen = ref(false)
const docsOnline = ref(false)
const title = computed(() => route.meta.title || 'AI 测试平台')
const healthNotice = ref('')
let healthTimer = null
let noticeTimer = null

function announce(text) {
  healthNotice.value = text
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    healthNotice.value = ''
  }, 4000)
}

async function checkHealth(announceResult = false) {
  checking.value = true
  try {
    const body = await api.health()
    online.value = true
    docsOnline.value = Boolean(body?.docs)
  } catch {
    online.value = false
    docsOnline.value = false
  } finally {
    checking.value = false
    if (announceResult) {
      const stamp = new Date().toLocaleTimeString('zh-CN', { hour12: false })
      announce(online.value ? `服务正常 · ${stamp}` : `服务不可达 · ${stamp}`)
    }
  }
}

const showDocs = computed(
  () => ['localhost', '127.0.0.1'].includes(window.location.hostname) || docsOnline.value,
)

function closeTopModal() {
  const masks = Array.from(document.querySelectorAll('.modal-mask')).filter(
    (node) => node.offsetParent !== null || getComputedStyle(node).position === 'fixed',
  )
  const mask = masks[masks.length - 1]
  if (!mask) return
  const buttons = Array.from(mask.querySelectorAll('button'))
  const closer =
    mask.querySelector('[data-modal-close]') ||
    buttons.find((item) => ['关闭', '取消', '返回列表'].includes(item.textContent.trim()))
  if (closer) {
    closer.click()
  } else if (mask.dataset.closable !== 'false') {
    mask.click()
  }
}

function onKeydown(event) {
  if (event.key === 'Escape') closeTopModal()
}

onMounted(() => {
  checkHealth()
  healthTimer = setInterval(checkHealth, 30000)
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  if (healthTimer) clearInterval(healthTimer)
  clearTimeout(noticeTimer)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="shell" :class="{ 'menu-open': menuOpen }">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">QA</div>
        <div>
          <strong>AI 测试平台</strong>
          <span style="text-transform: none; letter-spacing: 0">shenle</span>
        </div>
      </div>

      <nav class="nav" @click="menuOpen = false">
        <div class="nav-group">
          <p class="nav-group-title">工作台</p>
          <RouterLink to="/projects" class="nav-item"><span class="nav-icon">◫</span>项目管理</RouterLink>
          <RouterLink to="/system-ai" class="nav-item"><span class="nav-icon">◍</span>系统 AI 配置</RouterLink>
          <RouterLink to="/ai-logs" class="nav-item"><span class="nav-icon">◷</span>AI 调用日志</RouterLink>
          <RouterLink to="/users" class="nav-item"><span class="nav-icon">☺</span>用户管理</RouterLink>
        </div>

        <div class="nav-group">
          <p class="nav-group-title">当前项目</p>
          <RouterLink to="/overview" class="nav-item"><span class="nav-icon">◉</span>项目概览</RouterLink>
        </div>

        <div class="nav-group">
          <p class="nav-group-title">测试</p>
          <RouterLink to="/requirements" class="nav-item"><span class="nav-icon">▤</span>需求管理</RouterLink>
          <RouterLink to="/functional" class="nav-item"><span class="nav-icon">☑</span>功能测试</RouterLink>
          <RouterLink to="/kb" class="nav-item"><span class="nav-icon">✦</span>知识库</RouterLink>
        </div>

        <div class="nav-group">
          <p class="nav-group-title">自动化</p>
          <RouterLink to="/environments" class="nav-item"><span class="nav-icon">⚙</span>环境管理</RouterLink>
          <RouterLink to="/api-automation" class="nav-item"><span class="nav-icon">⌁</span>接口自动化</RouterLink>
          <RouterLink to="/ui-automation" class="nav-item"><span class="nav-icon">▣</span>UI 自动化</RouterLink>
        </div>

        <div class="nav-group">
          <p class="nav-group-title">项目</p>
          <RouterLink to="/modules" class="nav-item"><span class="nav-icon">▦</span>模块管理</RouterLink>
          <RouterLink to="/members" class="nav-item"><span class="nav-icon">⚇</span>成员管理</RouterLink>
        </div>

        <details class="nav-group nav-more">
          <summary class="nav-group-title">旧版页面（V1）</summary>
          <RouterLink to="/dashboard" class="nav-item nav-legacy"><span class="nav-icon">↩</span>仪表盘</RouterLink>
          <RouterLink to="/tickets" class="nav-item nav-legacy"><span class="nav-icon">↩</span>工单管理</RouterLink>
          <RouterLink to="/workbench" class="nav-item nav-legacy"><span class="nav-icon">↩</span>API 工作台</RouterLink>
          <RouterLink to="/knowledge" class="nav-item nav-legacy"><span class="nav-icon">↩</span>知识库问答</RouterLink>
          <RouterLink to="/platform" class="nav-item nav-legacy"><span class="nav-icon">↩</span>测试平台</RouterLink>
          <RouterLink to="/models" class="nav-item nav-legacy"><span class="nav-icon">↩</span>模型中心</RouterLink>
          <RouterLink to="/testcases" class="nav-item nav-legacy"><span class="nav-icon">↩</span>测试用例</RouterLink>
          <RouterLink to="/methodology" class="nav-item nav-legacy"><span class="nav-icon">↩</span>方法论</RouterLink>
          <RouterLink to="/report" class="nav-item nav-legacy"><span class="nav-icon">↩</span>项目报告</RouterLink>
          <RouterLink to="/portfolio" class="nav-item nav-legacy"><span class="nav-icon">↩</span>模块验收</RouterLink>
        </details>
      </nav>

      <div class="sidebar-foot">
        <div class="env-chip">
          <span class="dot" :class="online ? 'ok' : 'bad'"></span>
          {{ checking ? '检测中' : online ? 'SUT 在线' : 'SUT 离线' }}
        </div>
        <RouterLink to="/login" class="nav-item"><span class="nav-icon">⚿</span>访问密钥</RouterLink>
        <p>v1.2.1 · Raina 结构对齐</p>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar-title">
          <button
            class="menu-toggle"
            type="button"
            :aria-expanded="menuOpen"
            aria-label="切换导航菜单"
            @click="menuOpen = !menuOpen"
          >
            ☰
          </button>
          <div>
            <p class="eyebrow">AI QUALITY ENGINEERING</p>
            <h1>{{ title }}</h1>
          </div>
        </div>
        <div class="topbar-actions">
          <span v-if="healthNotice" class="muted">{{ healthNotice }}</span>
          <button class="btn ghost" :disabled="checking" @click="checkHealth(true)">
            {{ checking ? '检测中…' : '检测服务' }}
          </button>
          <a v-if="showDocs" class="btn" href="/docs" target="_blank" rel="noreferrer">API 文档</a>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
