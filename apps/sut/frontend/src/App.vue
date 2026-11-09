<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { api } from './api/client'
import NavIcon from './components/NavIcon.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'

const route = useRoute()
const router = useRouter()
const online = ref(false)
const checking = ref(true)
const menuOpen = ref(false)
const docsOnline = ref(false)
const serverVersion = ref('')
const title = computed(() => route.meta.title || 'AI 测试平台')
const healthNotice = ref('')
const heroOwnsTitle = ref(false)
const searchBox = ref(null)
const query = ref('')
let healthTimer = null
let noticeTimer = null

const NAV = [
  {
    group: '工作台',
    items: [
      { to: '/projects', icon: 'projects', label: '项目管理' },
      { to: '/system-ai', icon: 'ai-config', label: '系统 AI 配置' },
      { to: '/ai-logs', icon: 'logs', label: 'AI 调用日志' },
      { to: '/users', icon: 'users', label: '用户管理' },
    ],
  },
  { group: '当前项目', items: [{ to: '/overview', icon: 'overview', label: '项目概览' }] },
  {
    group: '测试',
    items: [
      { to: '/requirements', icon: 'requirements', label: '需求管理' },
      { to: '/functional', icon: 'functional', label: '功能测试' },
      { to: '/kb', icon: 'kb', label: '知识库' },
    ],
  },
  {
    group: '自动化',
    items: [
      { to: '/environments', icon: 'environments', label: '环境管理' },
      { to: '/api-automation', icon: 'api', label: '接口自动化' },
      { to: '/ui-automation', icon: 'ui', label: 'UI 自动化' },
    ],
  },
  {
    group: '项目',
    items: [
      { to: '/modules', icon: 'modules', label: '模块管理' },
      { to: '/members', icon: 'members', label: '成员管理' },
    ],
  },
  { group: '其他', items: [{ to: '/tools', icon: 'tools', label: '工具与旧版入口' }] },
]

const flatNav = NAV.flatMap((group) => group.items.map((item) => ({ ...item, group: group.group })))

const currentGroup = computed(() => {
  const hit = flatNav.find((item) => route.path === item.to)
  return hit ? hit.group : '工作台'
})

const matches = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword) return []
  return flatNav
    .filter((item) => item.label.toLowerCase().includes(keyword) || item.to.includes(keyword))
    .slice(0, 6)
})

// Pages that render their own hero already show the page title. Keeping the
// topbar title as well printed every heading twice, so the hero wins and the
// topbar falls back to a breadcrumb.
function detectHero() {
  heroOwnsTitle.value = Boolean(document.querySelector('.content .hero h1, .content .hero h2'))
}

watch(
  () => route.fullPath,
  async () => {
    await nextTick()
    detectHero()
    query.value = ''
  },
)

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
    serverVersion.value = body?.version || ''
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

function go(item) {
  query.value = ''
  router.push(item.to)
}

function submitSearch() {
  if (matches.value.length) {
    go(matches.value[0])
    return
  }
  const keyword = query.value.trim()
  if (keyword) router.push({ path: '/projects', query: { q: keyword } })
}

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
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    searchBox.value?.focus()
  }
}

onMounted(() => {
  checkHealth()
  healthTimer = setInterval(checkHealth, 30000)
  window.addEventListener('keydown', onKeydown)
  nextTick(detectHero)
})

onUnmounted(() => {
  if (healthTimer) clearInterval(healthTimer)
  clearTimeout(noticeTimer)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="shell" :class="{ 'menu-open': menuOpen }">
    <div v-if="menuOpen" class="scrim" aria-hidden="true" @click="menuOpen = false" />
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">QA</div>
        <div>
          <strong>AI 测试平台</strong>
          <span class="brand-sub">shenle</span>
        </div>
      </div>

      <nav class="nav" @click="menuOpen = false">
        <div v-for="group in NAV" :key="group.group" class="nav-group">
          <p class="nav-group-title">{{ group.group }}</p>
          <RouterLink v-for="item in group.items" :key="item.to" :to="item.to" class="nav-item">
            <NavIcon :name="item.icon" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
      </nav>

      <div class="sidebar-foot">
        <div class="env-chip">
          <span class="dot" :class="online ? 'ok' : 'bad'"></span>
          {{ checking ? '检测中' : online ? 'SUT 在线' : 'SUT 离线' }}
        </div>
        <RouterLink to="/login" class="nav-item nav-key">
          <NavIcon name="key" />
          <span>访问密钥</span>
        </RouterLink>
        <p class="version">v{{ serverVersion || '1.2.1' }} · citrus-lab</p>
      </div>
    </aside>

    <div class="main" :class="{ 'has-hero': heroOwnsTitle }">
      <header class="topbar">
        <button
          class="menu-toggle"
          type="button"
          :aria-expanded="menuOpen"
          aria-label="切换导航菜单"
          @click="menuOpen = !menuOpen"
        >
          ☰
        </button>

        <p class="crumbs">
          <span>{{ currentGroup }}</span>
          <span class="crumb-sep">/</span>
          <b>{{ title }}</b>
        </p>

        <div class="search-wrap">
          <label class="search">
            <NavIcon name="search" :size="15" />
            <input
              ref="searchBox"
              v-model="query"
              type="search"
              placeholder="搜索页面、用例、接口…"
              @keydown.enter.prevent="submitSearch"
              @keydown.esc="query = ''"
            />
            <span class="kbd">⌘K</span>
          </label>
          <ul v-if="matches.length" class="search-pop">
            <li v-for="item in matches" :key="item.to">
              <button type="button" @click="go(item)">
                <NavIcon :name="item.icon" :size="14" />
                <span>{{ item.label }}</span>
                <em>{{ item.group }}</em>
              </button>
            </li>
          </ul>
        </div>

        <div class="topbar-actions">
          <span v-if="healthNotice" class="health-note">{{ healthNotice }}</span>
          <a v-if="showDocs" class="btn ghost" href="/docs" target="_blank" rel="noreferrer">API 文档</a>
          <button class="btn ghost" :disabled="checking" @click="checkHealth(true)">
            {{ checking ? '检测中…' : '检测服务' }}
          </button>
          <div class="avatar" title="沈乐">沈</div>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
    <ConfirmDialog />
  </div>
</template>
