<script setup>
import { ref } from 'vue'
import { clearApiKey, getApiKey, setApiKey } from '../api/client'

const key = ref(getApiKey())
const saved = ref(false)

function save() {
  setApiKey(key.value.trim())
  saved.value = true
  setTimeout(() => {
    window.location.hash = '#/'
  }, 600)
}

function remove() {
  clearApiKey()
  key.value = ''
  saved.value = false
}
</script>

<template>
  <section class="stack">
    <article class="card auth-card">
      <p class="eyebrow">ACCESS KEY</p>
      <h2>访问密钥</h2>
      <p class="muted">
        生产环境的写操作需要访问密钥。只读浏览不需要密钥；没有密钥时新建、修改、执行等操作会返回 401。
        密钥只保存在本机浏览器 localStorage，不会上传到服务器。
      </p>
      <label class="auth-field">
        <span>APP_API_KEY</span>
        <input v-model="key" type="password" placeholder="粘贴服务端配置的访问密钥" />
      </label>
      <div class="auth-actions">
        <button class="btn" @click="save">保存</button>
        <button class="btn ghost" @click="remove">清除</button>
      </div>
      <p v-if="saved" class="alert">已保存，正在返回首页…</p>
    </article>
  </section>
</template>

<style scoped>
.auth-card { max-width: 640px; }
.auth-field { display: flex; flex-direction: column; gap: 6px; margin: 18px 0; }
.auth-field span { color: var(--muted); font-size: 12px; }
.auth-field input { padding: 10px 12px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
.auth-actions { display: flex; gap: 8px; }
</style>
