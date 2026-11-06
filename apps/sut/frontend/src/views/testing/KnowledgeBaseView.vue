<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'

const bases = ref([])
const selectedId = ref(null)
const documents = ref([])
const loading = ref(false)
const error = ref('')

const creating = ref(false)
const newBase = reactive({ name: '', description: '', chunk_size: 600, chunk_overlap: 100 })

const uploadInput = ref(null)
const pasting = ref(false)
const pasteForm = reactive({ filename: 'pasted.txt', text: '' })

const query = ref('')
const topK = ref(5)
const searching = ref(false)
const searchResult = ref(null)
const searchError = ref('')

const chunkView = reactive({ open: false, document: null, chunks: [] })
const chunkLoading = ref(false)

const selected = computed(() => bases.value.find((item) => item.id === selectedId.value) || null)
const kbFilter = ref('')
const visibleBases = computed(() => {
  const term = kbFilter.value.trim().toLowerCase()
  if (!term) return bases.value
  return bases.value.filter(
    (item) =>
      item.name.toLowerCase().includes(term) || (item.description || '').toLowerCase().includes(term),
  )
})
const totalDocs = computed(() => bases.value.reduce((sum, item) => sum + item.document_count, 0))
const totalChunks = computed(() => bases.value.reduce((sum, item) => sum + item.chunk_count, 0))

function shortDate(value) {
  if (!value) return '—'
  return String(value).replace('T', ' ').slice(0, 16)
}

async function loadBases() {
  loading.value = true
  error.value = ''
  try {
    bases.value = await api.knowledgeBases()
    if (!bases.value.length) {
      selectedId.value = null
      documents.value = []
    } else if (!bases.value.some((item) => item.id === selectedId.value)) {
      selectedId.value = bases.value[0].id
      await loadDocuments()
    } else {
      await loadDocuments()
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function loadDocuments() {
  if (!selectedId.value) {
    documents.value = []
    return
  }
  try {
    documents.value = await api.knowledgeDocuments(selectedId.value)
  } catch (err) {
    error.value = err.message
  }
}

async function selectBase(id) {
  selectedId.value = id
  searchResult.value = null
  await loadDocuments()
}

async function createBase() {
  if (!newBase.name.trim()) {
    error.value = '知识库名称不能为空'
    return
  }
  try {
    const created = await api.createKnowledgeBase({
      name: newBase.name.trim(),
      description: newBase.description,
      chunk_size: Number(newBase.chunk_size) || 600,
      chunk_overlap: Number(newBase.chunk_overlap) || 100,
    })
    creating.value = false
    newBase.name = ''
    newBase.description = ''
    selectedId.value = created.id
    await loadBases()
  } catch (err) {
    error.value = err.message
  }
}

async function removeBase(item) {
  if (!window.confirm(`删除知识库「${item.name}」及其全部文档与分块？`)) return
  try {
    await api.deleteKnowledgeBase(item.id)
    if (selectedId.value === item.id) selectedId.value = null
    await loadBases()
  } catch (err) {
    error.value = err.message
  }
}

async function onUpload(event) {
  const file = event.target.files?.[0]
  if (!file || !selectedId.value) return
  try {
    await api.uploadKnowledgeDocument(selectedId.value, file)
    event.target.value = ''
    await loadBases()
  } catch (err) {
    error.value = err.message
    event.target.value = ''
  }
}

async function addPastedText() {
  if (!pasteForm.text.trim()) {
    error.value = '正文不能为空'
    return
  }
  try {
    await api.addKnowledgeText(selectedId.value, {
      filename: pasteForm.filename || 'pasted.txt',
      text: pasteForm.text,
    })
    pasting.value = false
    pasteForm.text = ''
    await loadBases()
  } catch (err) {
    error.value = err.message
  }
}

async function removeDocument(document) {
  if (!window.confirm(`删除文档「${document.filename}」？`)) return
  try {
    await api.deleteKnowledgeDocument(document.id)
    await loadBases()
  } catch (err) {
    error.value = err.message
  }
}

async function openChunks(document) {
  chunkView.open = true
  chunkView.document = document
  chunkView.chunks = []
  chunkLoading.value = true
  try {
    chunkView.chunks = await api.knowledgeChunks(document.id, 0, 100)
  } catch (err) {
    error.value = err.message
  } finally {
    chunkLoading.value = false
  }
}

async function runSearch() {
  if (!selectedId.value || !query.value.trim()) {
    searchError.value = '请输入要检索的问题'
    return
  }
  searching.value = true
  searchError.value = ''
  try {
    searchResult.value = await api.searchKnowledgeBase(selectedId.value, {
      query: query.value.trim(),
      top_k: Number(topK.value) || 5,
    })
  } catch (err) {
    searchError.value = err.message
  } finally {
    searching.value = false
  }
}

function scoreWidth(score) {
  return `${Math.max(4, Math.min(100, Math.round(score * 100)))}%`
}

onMounted(loadBases)
</script>

<template>
  <section class="stack">
    <header class="hero">
      <div>
        <p class="eyebrow">KNOWLEDGE BASE</p>
        <h1>知识库</h1>
        <p class="muted">
          项目级上下文：上传文档自动分块，用例生成和需求分析从这里取资料，减少模型凭空发挥。
        </p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ bases.length }}</strong><span>知识库</span></div>
        <div><strong>{{ totalDocs }}</strong><span>文档</span></div>
        <div><strong>{{ totalChunks }}</strong><span>分块</span></div>
      </div>
    </header>

    <div class="toolbar">
      <div class="toolbar-group">
        <button class="btn" :disabled="loading" @click="loadBases">刷新</button>
        <button class="btn ghost" @click="creating = true">新建知识库</button>
      </div>
      <span v-if="selected" class="muted toolbar-note">
        当前：{{ selected.name }} · 分块 {{ selected.chunk_size }} / 重叠 {{ selected.chunk_overlap }}
      </span>
    </div>

    <p v-if="error" class="alert">{{ error }}</p>

    <div class="kb-grid">
      <aside class="card kb-list">
        <div class="card-head">
          <h2>知识库</h2>
          <span class="muted">{{ visibleBases.length }} / {{ bases.length }} 个</span>
        </div>
        <input
          v-model="kbFilter"
          type="search"
          class="kb-filter"
          maxlength="60"
          placeholder="搜索知识库名称"
          aria-label="搜索知识库"
        />
        <p v-if="!bases.length" class="empty">还没有知识库，先创建一个。</p>
        <p v-else-if="!visibleBases.length" class="empty">没有匹配「{{ kbFilter }}」的知识库。</p>
        <ul class="kb-items">
          <li
            v-for="item in visibleBases"
            :key="item.id"
            :class="['kb-item', { active: item.id === selectedId }]"
            @click="selectBase(item.id)"
          >
            <div class="kb-item-main">
              <strong>{{ item.name }}</strong>
              <span class="cell-sub">{{ item.document_count }} 文档 · {{ item.chunk_count }} 分块</span>
            </div>
            <button class="btn ghost tiny" @click.stop="removeBase(item)">删除</button>
          </li>
        </ul>
      </aside>

      <div class="stack">
        <article class="card">
          <div class="card-head">
            <div>
              <h2>文档</h2>
              <p class="cell-sub">支持 md / txt / docx / pdf，单文件 ≤ 20MB；也可以直接粘贴文本。</p>
            </div>
            <div class="row-actions">
              <input ref="uploadInput" type="file" hidden @change="onUpload" />
              <button class="btn ghost" :disabled="!selected" @click="uploadInput?.click()">上传文件</button>
              <button class="btn ghost" :disabled="!selected" @click="pasting = true">粘贴文本</button>
            </div>
          </div>

          <p v-if="!selected" class="empty">先选择一个知识库。</p>
          <div v-else-if="loading && !documents.length" class="stack" style="gap: 8px">
            <span v-for="n in 5" :key="`sk-${n}`" class="skeleton" style="height: 36px; display: block" />
          </div>
          <p v-else-if="!documents.length" class="empty">这个知识库还没有文档。</p>
          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>文件名</th>
                  <th>来源</th>
                  <th>字符</th>
                  <th>分块</th>
                  <th>时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="document in documents" :key="document.id">
                  <td>
                    <strong>{{ document.filename }}</strong>
                    <div v-if="document.note" class="cell-sub">{{ document.note }}</div>
                  </td>
                  <td><span class="badge">{{ document.source }}</span></td>
                  <td class="mono">{{ document.char_count }}</td>
                  <td class="mono">{{ document.chunk_count }}</td>
                  <td class="cell-sub">{{ shortDate(document.created_at) }}</td>
                  <td>
                    <div class="row-actions">
                      <button class="btn ghost tiny" @click="openChunks(document)">分块</button>
                      <button class="btn ghost tiny" @click="removeDocument(document)">删除</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div>
              <h2>试检索</h2>
              <p class="cell-sub">输入问题，看命中的分块与相关度，用来判断文档切得好不好。</p>
            </div>
          </div>
          <div class="search-bar">
            <input v-model="query" placeholder="例如：导出超过 5000 条会怎样" @keyup.enter="runSearch" />
            <select v-model.number="topK">
              <option :value="3">3 条</option>
              <option :value="5">5 条</option>
              <option :value="10">10 条</option>
            </select>
            <button class="btn" :disabled="searching || !selected" @click="runSearch">
              {{ searching ? '检索中…' : '检索' }}
            </button>
          </div>
          <p v-if="searchError" class="alert">{{ searchError }}</p>
          <p v-else-if="searchResult && !searchResult.hits.length" class="empty">
            没有命中任何分块，换个说法或补充文档。
          </p>
          <div v-else-if="searchResult" class="hits">
            <p class="muted">
              命中 {{ searchResult.hits.length }} 条 · 耗时 {{ searchResult.took_ms }}ms
            </p>
            <div v-for="hit in searchResult.hits" :key="hit.chunk_id" class="hit">
              <div class="hit-head">
                <span class="mono">{{ hit.filename }} #{{ hit.seq }}</span>
                <span class="mono">{{ hit.score.toFixed(2) }}</span>
              </div>
              <div class="score-track"><div class="score-fill" :style="{ width: scoreWidth(hit.score) }" /></div>
              <p class="hit-text">{{ hit.snippet }}</p>
            </div>
          </div>
        </article>
      </div>
    </div>

    <div v-if="creating" class="modal-mask" @click.self="creating = false">
      <div class="modal">
        <header>
          <h2>新建知识库</h2>
          <button class="btn ghost tiny" data-modal-close @click="creating = false">关闭</button>
        </header>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label>名称<input v-model="newBase.name" placeholder="例如：工单系统接口文档" /></label>
          <label>描述<input v-model="newBase.description" placeholder="这个库放什么资料" /></label>
          <label>分块大小（字符）<input v-model.number="newBase.chunk_size" type="number" min="100" max="4000" /></label>
          <label>分块重叠（字符）<input v-model.number="newBase.chunk_overlap" type="number" min="0" max="1000" /></label>
        </div>
        <footer>
          <button class="btn ghost" @click="creating = false">取消</button>
          <button class="btn" @click="createBase">创建</button>
        </footer>
      </div>
    </div>

    <div v-if="pasting" class="modal-mask" @click.self="pasting = false">
      <div class="modal">
        <header>
          <h2>粘贴文本入库</h2>
          <button class="btn ghost tiny" data-modal-close @click="pasting = false">关闭</button>
        </header>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label>文件名<input v-model="pasteForm.filename" /></label>
          <label>正文<textarea v-model="pasteForm.text" rows="12" placeholder="粘贴接口文档、需求说明或历史缺陷记录" /></label>
        </div>
        <footer>
          <button class="btn ghost" @click="pasting = false">取消</button>
          <button class="btn" @click="addPastedText">入库</button>
        </footer>
      </div>
    </div>

    <div v-if="chunkView.open" class="modal-mask" @click.self="chunkView.open = false">
      <div class="modal wide">
        <header>
          <h2>{{ chunkView.document?.filename }} · 分块</h2>
          <button class="btn ghost tiny" data-modal-close @click="chunkView.open = false">关闭</button>
        </header>
        <p v-if="chunkLoading" class="muted">加载中…</p>
        <p v-else-if="!chunkView.chunks.length" class="empty">没有分块。</p>
        <div v-else class="chunk-list">
          <div v-for="chunk in chunkView.chunks" :key="chunk.id" class="chunk">
            <div class="hit-head">
              <span class="mono">#{{ chunk.seq }}</span>
              <span class="mono">{{ chunk.char_count }} 字符</span>
            </div>
            <pre>{{ chunk.text }}</pre>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.kb-grid {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}
.kb-filter {
  width: 100%;
  margin-bottom: 10px;
}
.kb-items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.kb-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  cursor: pointer;
  background: rgba(4, 8, 16, 0.35);
}
.kb-item:hover {
  border-color: rgba(56, 189, 248, 0.45);
}
.kb-item.active {
  border-color: var(--accent);
  background: rgba(56, 189, 248, 0.1);
}
.kb-item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.kb-item-main strong {
  font-size: 13.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.search-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.search-bar input {
  flex: 1 1 320px;
  padding: 9px 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.search-bar select {
  width: auto;
  min-width: 92px;
  padding: 9px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(4, 8, 16, 0.5);
  color: var(--text);
}
.hits {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}
.hit {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 12px 14px;
  background: rgba(4, 8, 16, 0.35);
}
.hit-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 11.5px;
  color: var(--muted);
}
.score-track {
  height: 4px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  margin: 8px 0 10px;
  overflow: hidden;
}
.score-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0.55), var(--accent));
}
.hit-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
}
.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 62vh;
  overflow-y: auto;
}
.chunk {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 10px 12px;
  background: rgba(4, 8, 16, 0.35);
}
.chunk pre {
  margin: 8px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--text);
  font-family: inherit;
}
.btn.tiny {
  padding: 5px 10px;
  font-size: 12px;
}
.toolbar-group {
  display: flex;
  gap: 10px;
}
.toolbar-note {
  margin-left: auto;
  font-size: 12px;
}
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(3, 6, 12, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
  padding: 24px;
}
.modal {
  width: min(720px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 18px 20px;
}
.modal.wide {
  width: min(820px, 100%);
}
.modal header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 14px;
}
@media (max-width: 1100px) {
  .kb-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
