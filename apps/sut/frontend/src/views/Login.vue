<script setup>
import { ref } from 'vue'
import { api, clearApiKey, getApiKey, setApiKey } from '../api/client'

const key = ref(getApiKey())
const saved = ref(false)
const keyError = ref('')
const checking = ref(false)

async function save() {
  const value = key.value.trim()
  saved.value = false
  keyError.value = ''
  if (!value) {
    keyError.value = '请输入访问密钥'
    return
  }
  checking.value = true
  setApiKey(value)
  try {
    await api.verifyKey()
    saved.value = true
    setTimeout(() => {
      window.location.hash = '#/'
    }, 600)
  } catch (error) {
    clearApiKey()
    keyError.value = `密钥验证失败：${error.message}`
  } finally {
    checking.value = false
  }
}

function remove() {
  clearApiKey()
  key.value = ''
  saved.value = false
  keyError.value = ''
}
</script>

<template>
  <section class="stack">
    <article class="card auth-card">
      <p class="eyebrow">ACCESS KEY</p>
      <h2>访问密钥</h2>
      <p class="muted">
        生产环境的写操作需要访问密钥；浏览页面和知识库问答不需要。没有有效密钥时，新建、修改、执行等操作会提示并保留当前输入。
        密钥只保存在本机浏览器 localStorage，不会上传到服务器。
      </p>
      <label class="auth-field">
        <span>APP_API_KEY</span>
        <input v-model="key" type="password" maxlength="512" placeholder="粘贴服务端配置的访问密钥" />
      </label>
      <div class="auth-actions">
        <button class="btn" :disabled="checking" @click="save">{{ checking ? '验证中…' : '保存' }}</button>
        <button class="btn ghost" @click="remove">清除</button>
      </div>
      <p v-if="saved" class="alert">密钥已验证并保存，正在返回首页…</p>
      <p v-if="keyError" class="alert error">{{ keyError }}</p>
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
