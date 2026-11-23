<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api/client'

const docs = ref([])
const active = ref('')
const markdown = ref('')
const title = ref('')
const loading = ref(false)
const error = ref('')

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function inline(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
}

const rendered = computed(() => {
  const lines = markdown.value.split('\n')
  const out = []
  let inCode = false
  let list = ''
  let table = false

  const closeList = () => {
    if (list) {
      out.push(`</${list}>`)
      list = ''
    }
  }
  const closeTable = () => {
    if (table) {
      out.push('</tbody></table>')
      table = false
    }
  }

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '')
    if (line.startsWith('```')) {
      closeList()
      closeTable()
      out.push(inCode ? '</code></pre>' : '<pre><code>')
      inCode = !inCode
      continue
    }
    if (inCode) {
      out.push(escapeHtml(raw))
      continue
    }
    if (!line.trim()) {
      closeList()
      closeTable()
      continue
    }
    const heading = /^(#{1,4})\s+(.*)$/.exec(line)
    if (heading) {
      closeList()
      closeTable()
      const level = heading[1].length
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`)
      continue
    }
    if (/^\|/.test(line)) {
      closeList()
      const cells = line.split('|').slice(1, -1).map((c) => c.trim())
      if (cells.every((c) => /^:?-+:?$/.test(c))) {
        out.push('<tbody>')
        table = true
        continue
      }
      const tag = table ? 'td' : 'th'
      if (!table) {
        out.push('<table><thead>')
      }
      out.push(`<tr>${cells.map((c) => `<${tag}>${inline(c)}</${tag}>`).join('')}</tr>`)
      if (!table) {
        out.push('</thead>')
        out.push('<tbody>')
        table = true
      }
      continue
    }
    closeTable()
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line)
    if (bullet) {
      if (list !== 'ul') {
        closeList()
        out.push('<ul>')
        list = 'ul'
      }
      out.push(`<li>${inline(bullet[1])}</li>`)
      continue
    }
    const ordered = /^\s*(\d+)[.)]\s+(.*)$/.exec(line)
    if (ordered) {
      if (list !== 'ol') {
        closeList()
        out.push('<ol>')
        list = 'ol'
      }
      out.push(`<li>${inline(ordered[2])}</li>`)
      continue
    }
    closeList()
    out.push(`<p>${inline(line)}</p>`)
  }
  closeList()
  closeTable()
  if (inCode) out.push('</code></pre>')
  return out.join('\n')
})

async function open(slug) {
  loading.value = true
  error.value = ''
  try {
    const data = await api.skillDoc(slug)
    active.value = slug
    title.value = data.title
    markdown.value = data.markdown
  } catch (err) {
    error.value = err.message || '读取失败'
  } finally {
    loading.value = false
  }
}

function downloadUrl(slug) {
  return `/api/platform/skill-docs/${encodeURIComponent(slug)}/download`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    docs.value = await api.skillDocs()
    if (docs.value.length) await open(docs.value[0].slug)
  } catch (err) {
    error.value = err.message || '读取失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="stack">
    <section class="card hero">
      <div>
        <p class="eyebrow">SKILLS</p>
        <h2>Skills 手册</h2>
        <p class="muted">
          {{ docs.length }} 个平台技能的说明与用法，直接从仓库同步过来，只读。
        </p>
      </div>
    </section>

    <p v-if="error" class="alert error">{{ error }}</p>

    <div class="doc-grid">
      <aside class="card doc-list">
        <button
          v-for="doc in docs"
          :key="doc.slug"
          class="doc-item"
          :class="{ active: doc.slug === active }"
          @click="open(doc.slug)"
        >
          <span class="doc-title">{{ doc.title }}</span>
          <span class="doc-slug mono">{{ doc.slug }}</span>
        </button>
      </aside>

      <article class="card doc-body">
        <div class="doc-head">
          <span class="doc-head-title mono">{{ title }}</span>
          <a
            v-if="active"
            class="btn ghost small"
            :href="downloadUrl(active)"
            :download="`${active}.zip`"
          >
            下载 zip
          </a>
        </div>
        <p v-if="loading" class="muted">读取中…</p>
        <div v-else class="markdown" v-html="rendered"></div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.doc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--line, rgba(0,0,0,.08));
}
.doc-head-title { font-size: 13px; color: var(--muted); }

.doc-grid {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  max-height: 75vh;
  overflow-y: auto;
}
.doc-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
  padding: 8px 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text);
  cursor: pointer;
}
.doc-item:hover {
  background: var(--surface-2, rgba(0, 0, 0, 0.04));
}
.doc-item.active {
  background: var(--accent-soft, rgba(163, 230, 53, 0.18));
}
.doc-title {
  font-size: 13px;
  font-weight: 600;
}
.doc-slug {
  font-size: 11px;
  color: var(--muted);
}
.doc-body {
  padding: 24px 28px;
  max-height: 75vh;
  overflow-y: auto;
}
.markdown :deep(h1) {
  font-size: 24px;
  margin: 0 0 12px;
}
.markdown :deep(h2) {
  font-size: 18px;
  margin: 22px 0 8px;
}
.markdown :deep(h3) {
  font-size: 15px;
  margin: 16px 0 6px;
}
.markdown :deep(p),
.markdown :deep(li) {
  font-size: 13.5px;
  line-height: 1.75;
}
.markdown :deep(code) {
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.05);
  font-size: 12.5px;
}
.markdown :deep(pre) {
  padding: 12px 14px;
  border-radius: 10px;
  background: #1e2414;
  color: #eef3df;
  overflow-x: auto;
}
.markdown :deep(pre code) {
  background: transparent;
  color: inherit;
}
.markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
  font-size: 12.5px;
}
.markdown :deep(th),
.markdown :deep(td) {
  border: 1px solid var(--line, #e4ead3);
  padding: 6px 9px;
  text-align: left;
}
@media (max-width: 900px) {
  .doc-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
