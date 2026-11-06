<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'

const view = ref('list')
const projects = ref([])
const items = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

const projectId = ref('')
const statusFilter = ref('')
const keyword = ref('')

const showCreate = ref(false)
const creating = ref(false)
const uploadFile = ref(null)
const form = reactive({ title: '', body: '', status: 'draft', priority: 'medium' })

const active = ref(null)
const tab = ref('features')
const analyzing = ref(false)
const planning = ref(false)
const chatting = ref(false)
const chatInput = ref('')
const attachmentInput = ref(null)

const statusText = { draft: '草稿', analyzed: '已分析', planned: '已排期' }
const priorityText = { low: '低', medium: '中', high: '高', urgent: '紧急' }

const analysis = computed(() => active.value?.analysis || null)
const plan = computed(() => active.value?.plan || null)

const filtered = computed(() => {
  const q = keyword.value.trim()
  return items.value.filter((item) => {
    if (statusFilter.value && item.status !== statusFilter.value) return false
    if (q && !item.title.includes(q)) return false
    return true
  })
})

const analysedCount = computed(() => items.value.filter((i) => i.analysis).length)

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    if (!projects.value.length) projects.value = await api.platformProjects()
    if (!projectId.value && projects.value.length) projectId.value = projects.value[0].id
    if (projectId.value) items.value = await api.platformRequirements(projectId.value)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.title = ''
  form.body = ''
  form.status = 'draft'
  form.priority = 'medium'
  uploadFile.value = null
  showCreate.value = true
}

async function create() {
  error.value = ''
  notice.value = ''
  if (!form.title.trim()) {
    error.value = '请填写需求标题'
    return
  }
  if (!projectId.value) {
    error.value = '请先选择项目'
    return
  }
  creating.value = true
  try {
    const created = await api.createPlatformRequirement({
      project_id: Number(projectId.value),
      title: form.title.trim(),
      body: form.body,
      status: form.status,
      priority: form.priority,
    })
    let uploadNote = ''
    if (uploadFile.value) {
      const attachment = await api.uploadRequirementAttachment(created.id, uploadFile.value)
      uploadNote = attachment.extract_note || ''
    }
    showCreate.value = false
    notice.value = uploadNote ? `需求已创建；${uploadNote}` : '需求已创建'
    await refresh()
    await open(created.id)
  } catch (err) {
    error.value = err.message
  } finally {
    creating.value = false
  }
}

async function open(id) {
  try {
    active.value = await api.platformRequirement(id)
    tab.value = active.value.analysis ? 'features' : 'plan'
    view.value = 'detail'
    chatInput.value = ''
  } catch (err) {
    error.value = err.message
  }
}

function back() {
  view.value = 'list'
  active.value = null
  refresh()
}

async function analyze() {
  if (!active.value) return
  analyzing.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await api.analyzeRequirement(active.value.id)
    active.value = result.requirement
    tab.value = 'features'
    notice.value = `需求分析完成（模型 ${result.model_name || '-'}）`
  } catch (err) {
    error.value = err.message
  } finally {
    analyzing.value = false
  }
}

async function makePlan() {
  if (!active.value) return
  planning.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await api.planRequirement(active.value.id, { create_plan: true })
    active.value = result.requirement
    tab.value = 'plan'
    notice.value = result.test_plan
      ? `测试计划已生成，并创建「${result.test_plan.name}」`
      : '测试计划已生成'
  } catch (err) {
    error.value = err.message
  } finally {
    planning.value = false
  }
}

async function send() {
  const message = chatInput.value.trim()
  if (!message || !active.value) return
  chatting.value = true
  error.value = ''
  try {
    const result = await api.chatRequirement(active.value.id, message)
    active.value = result.requirement
    chatInput.value = ''
    if (result.analysis_updated) notice.value = '助手已更新分析结果'
  } catch (err) {
    error.value = err.message
  } finally {
    chatting.value = false
  }
}

async function addAttachment(event) {
  const file = event.target.files?.[0]
  if (!file || !active.value) return
  error.value = ''
  try {
    const result = await api.uploadRequirementAttachment(active.value.id, file)
    active.value = await api.platformRequirement(active.value.id)
    notice.value = result.extract_note || `已上传 ${result.filename}`
  } catch (err) {
    error.value = err.message
  } finally {
    if (attachmentInput.value) attachmentInput.value.value = ''
  }
}

async function removeAttachment(attachmentId) {
  if (!active.value) return
  try {
    await api.deleteRequirementAttachment(active.value.id, attachmentId)
    active.value = await api.platformRequirement(active.value.id)
  } catch (err) {
    error.value = err.message
  }
}

async function removeRequirement(item) {
  if (!window.confirm(`删除需求「${item.title}」？分析结果和对话记录会一起删除。`)) return
  try {
    await api.deletePlatformRequirement(item.id)
    if (active.value?.id === item.id) back()
    else await refresh()
  } catch (err) {
    error.value = err.message
  }
}

const formatTime = (value) => (value ? String(value).replace('T', ' ').slice(0, 16) : '-')

onMounted(refresh)
</script>

<template>
  <section class="stack">
    <template v-if="view === 'list'">
      <article class="hero card">
        <div>
          <p class="eyebrow">REQUIREMENT</p>
          <h2>需求管理</h2>
          <p class="muted">
            上传 md / txt / pdf / docx，AI 拆出功能清单、界面描述与待澄清项，右侧助手可当场改分析，再一键生成测试计划。
          </p>
        </div>
        <div class="hero-metrics">
          <div><strong>{{ items.length }}</strong><span>需求总数</span></div>
          <div><strong>{{ analysedCount }}</strong><span>已分析</span></div>
        </div>
      </article>

      <p v-if="error" class="alert error">{{ error }}</p>
      <p v-if="notice" class="alert">{{ notice }}</p>

      <article class="card">
        <div class="card-head">
          <div><h2>需求列表</h2><p>共 {{ filtered.length }} 条</p></div>
          <button class="btn" @click="openCreate">新建需求</button>
        </div>
        <div class="toolbar">
          <select v-model="projectId" @change="refresh">
            <option value="" disabled>选择项目</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">#{{ p.id }} {{ p.name }}</option>
          </select>
          <select v-model="statusFilter">
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="analyzed">已分析</option>
            <option value="planned">已排期</option>
          </select>
          <input v-model="keyword" type="search" maxlength="80" placeholder="搜索标题（最多 80 字）" />
          <button class="btn ghost" :disabled="loading" @click="refresh">{{ loading ? '加载中' : '刷新' }}</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>标题</th><th>状态</th><th>优先级</th><th>附件</th><th>更新时间</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="loading && !filtered.length">
                <tr v-for="n in 6" :key="`sk-${n}`" class="skeleton-row">
                  <td><span class="skeleton" style="width: 32px" /></td>
                  <td><span class="skeleton" style="width: 72%" /></td>
                  <td><span class="skeleton" style="width: 48px" /></td>
                  <td><span class="skeleton" style="width: 44px" /></td>
                  <td><span class="skeleton" style="width: 20px" /></td>
                  <td><span class="skeleton" style="width: 84px" /></td>
                  <td><span class="skeleton" style="width: 92px" /></td>
                </tr>
              </template>
              <tr v-for="item in filtered" :key="item.id">
                <td class="mono">#{{ item.id }}</td>
                <td class="req-title" :class="`pr-${item.priority}`">
                  <button class="link req-link" @click="open(item.id)">{{ item.title }}</button>
                  <div class="cell-sub">{{ item.body ? item.body.slice(0, 48) : '无正文' }}</div>
                </td>
                <td>
                  <span class="badge" :class="item.status === 'draft' ? 'module-planned' : 'module-done'">
                    {{ statusText[item.status] || item.status }}
                  </span>
                </td>
                <td><span class="badge" :class="`priority-${item.priority}`">{{ priorityText[item.priority] || item.priority }}</span></td>
                <td class="muted">{{ item.attachments?.length || 0 }}</td>
                <td class="muted">{{ formatTime(item.updated_at) }}</td>
                <td class="row-actions">
                  <button class="btn ghost" @click="open(item.id)">打开</button>
                  <button class="btn ghost danger" @click="removeRequirement(item)">删除</button>
                </td>
              </tr>
              <tr v-if="!filtered.length && !loading"><td colspan="7" class="empty">还没有需求，点右上角「新建需求」。</td></tr>
            </tbody>
          </table>
        </div>
      </article>
    </template>

    <template v-else-if="active">
      <div class="detail-head">
        <button class="btn ghost" @click="back">← 返回列表</button>
        <div class="detail-title">
          <h2>{{ active.title }}</h2>
          <p class="muted">
            #{{ active.id }} · {{ statusText[active.status] || active.status }} ·
            {{ formatTime(active.updated_at) }}
          </p>
        </div>
        <div class="detail-actions">
          <button class="btn" :disabled="analyzing" @click="analyze">{{ analyzing ? '分析中…' : '需求分析' }}</button>
          <button class="btn ghost" :disabled="planning || !analysis" @click="makePlan">
            {{ planning ? '生成中…' : '生成测试计划' }}
          </button>
        </div>
      </div>

      <p v-if="error" class="alert error">{{ error }}</p>
      <p v-if="notice" class="alert">{{ notice }}</p>

      <div class="detail-grid">
        <div class="col">
          <article class="card">
            <div class="card-head"><div><h2>需求正文</h2><p>Markdown</p></div></div>
            <pre class="body-view">{{ active.body || '（无正文，可上传附件后直接分析）' }}</pre>
          </article>

          <article class="card">
            <div class="card-head">
              <div><h2>附件</h2><p>单文件 ≤ 20MB</p></div>
              <label class="btn ghost file-btn">
                上传附件
                <input ref="attachmentInput" type="file" accept=".md,.markdown,.txt,.pdf,.docx" @change="addAttachment" />
              </label>
            </div>
            <ul class="attach-list">
              <li v-for="file in active.attachments" :key="file.id">
                <div>
                  <strong>{{ file.filename }}</strong>
                  <div class="cell-sub">
                    {{ Math.round(file.size / 1024) }} KB · 提取 {{ file.chars }} 字
                    <span v-if="file.extract_note" class="warn"> · {{ file.extract_note }}</span>
                  </div>
                </div>
                <button class="btn ghost danger" @click="removeAttachment(file.id)">移除</button>
              </li>
              <li v-if="!active.attachments?.length" class="empty">没有附件</li>
            </ul>
          </article>
        </div>

        <div class="col">
          <article class="card">
            <div class="tabs">
              <button class="tab" :class="{ active: tab === 'features' }" @click="tab = 'features'">功能清单</button>
              <button class="tab" :class="{ active: tab === 'ui' }" @click="tab = 'ui'">界面描述</button>
              <button class="tab" :class="{ active: tab === 'clarifications' }" @click="tab = 'clarifications'">待澄清</button>
              <button class="tab" :class="{ active: tab === 'risks' }" @click="tab = 'risks'">风险</button>
              <button class="tab" :class="{ active: tab === 'plan' }" @click="tab = 'plan'">测试计划</button>
            </div>

            <div v-if="tab === 'features'" class="tab-body">
              <p v-if="analysis?.summary" class="summary">{{ analysis.summary }}</p>
              <div v-for="(item, index) in analysis?.features || []" :key="index" class="feature-item">
                <div class="feature-head">
                  <strong>{{ index + 1 }}. {{ item.name }}</strong>
                  <span class="badge" :class="`priority-${item.priority}`">{{ priorityText[item.priority] || item.priority }}</span>
                </div>
                <p class="muted">{{ item.description }}</p>
                <p v-if="item.acceptance" class="acceptance">验收：{{ item.acceptance }}</p>
              </div>
              <p v-if="!analysis?.features?.length" class="empty">还没有分析结果，点上方「需求分析」。</p>
            </div>

            <div v-else-if="tab === 'ui'" class="tab-body">
              <div v-for="(item, index) in analysis?.ui || []" :key="index" class="feature-item">
                <strong>{{ item.page }}</strong>
                <p class="muted">{{ item.description }}</p>
                <ul class="chip-list">
                  <li v-for="element in item.elements" :key="element">{{ element }}</li>
                </ul>
              </div>
              <p v-if="!analysis?.ui?.length" class="empty">暂无界面描述。</p>
            </div>

            <div v-else-if="tab === 'clarifications'" class="tab-body">
              <div v-for="(item, index) in analysis?.clarifications || []" :key="index" class="feature-item">
                <strong>Q{{ index + 1 }}. {{ item.question }}</strong>
                <p v-if="item.why" class="muted">风险：{{ item.why }}</p>
              </div>
              <p v-if="!analysis?.clarifications?.length" class="empty">没有待澄清项。</p>
            </div>

            <div v-else-if="tab === 'risks'" class="tab-body">
              <ul class="feature-list">
                <li v-for="(item, index) in analysis?.risks || []" :key="index">{{ item }}</li>
              </ul>
              <p v-if="!analysis?.risks?.length" class="empty">没有记录风险。</p>
            </div>

            <div v-else class="tab-body">
              <template v-if="plan">
                <div class="plan-head">
                  <div>
                    <p class="muted">测试目标</p>
                    <strong>{{ plan.goal }}</strong>
                  </div>
                  <div class="plan-days"><strong>{{ plan.person_days }}</strong><span>人天</span></div>
                </div>
                <div class="plan-grid">
                  <div>
                    <p class="muted">覆盖范围</p>
                    <ul class="feature-list"><li v-for="item in plan.scope_in" :key="item">{{ item }}</li></ul>
                  </div>
                  <div>
                    <p class="muted">不覆盖</p>
                    <ul class="feature-list"><li v-for="item in plan.scope_out" :key="item">{{ item }}</li></ul>
                  </div>
                </div>
                <p class="muted">策略：{{ plan.approach }}</p>
                <div class="table-wrap">
                  <table>
                    <thead><tr><th>阶段</th><th>人天</th><th>交付物</th></tr></thead>
                    <tbody>
                      <tr v-for="item in plan.milestones" :key="item.name">
                        <td>{{ item.name }}</td><td class="mono">{{ item.days }}</td><td class="muted">{{ item.deliverable }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div class="plan-grid">
                  <div>
                    <p class="muted">环境</p>
                    <ul class="feature-list"><li v-for="item in plan.environments" :key="item">{{ item }}</li></ul>
                  </div>
                  <div>
                    <p class="muted">测试数据</p>
                    <ul class="feature-list"><li v-for="item in plan.test_data" :key="item">{{ item }}</li></ul>
                  </div>
                </div>
              </template>
              <p v-else class="empty">还没有测试计划，先完成需求分析再点「生成测试计划」。</p>
            </div>
          </article>
        </div>

        <div class="col">
          <article class="card chat-card">
            <div class="card-head"><div><h2>需求助手</h2><p>可以要求它补充或修改分析</p></div></div>
            <div class="chat-log">
              <div v-for="msg in active.messages" :key="msg.id" class="bubble" :class="msg.role">
                <div class="bubble-role">{{ msg.role === 'user' ? '我' : '助手' }}</div>
                <div class="bubble-text">{{ msg.content }}</div>
              </div>
              <p v-if="!active.messages?.length" class="empty">
                例如：「导出是否要包含已关闭工单？」「把待澄清项补上权限问题」。
              </p>
            </div>
            <div class="chat-input">
              <textarea v-model="chatInput" rows="3" placeholder="向助手提问，或要求修改分析……" @keydown.ctrl.enter="send" />
              <button class="btn" :disabled="chatting || !chatInput.trim()" @click="send">
                {{ chatting ? '思考中…' : '发送' }}
              </button>
            </div>
          </article>
        </div>
      </div>
    </template>

    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <article class="modal card">
        <div class="card-head">
          <div><h2>新建需求</h2><p>正文与附件二选一必填</p></div>
          <button class="btn ghost" data-modal-close @click="showCreate = false">关闭</button>
        </div>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label>
            <span class="muted">标题 *</span>
            <input v-model="form.title" type="text" placeholder="例如：工单列表支持状态筛选与 CSV 导出" />
          </label>
          <label>
            <span class="muted">正文（Markdown）</span>
            <textarea v-model="form.body" rows="7" placeholder="粘贴需求内容，或上传附件……" />
          </label>
          <label>
            <span class="muted">附件</span>
            <input type="file" accept=".md,.markdown,.txt,.pdf,.docx" @change="uploadFile = $event.target.files?.[0] || null" />
            <span class="cell-sub">支持 md / txt / pdf / docx，单文件 ≤ 20MB</span>
          </label>
          <div class="form-row">
            <label>
              <span class="muted">状态</span>
              <select v-model="form.status">
                <option value="draft">草稿</option>
                <option value="analyzed">已分析</option>
                <option value="planned">已排期</option>
              </select>
            </label>
            <label>
              <span class="muted">优先级</span>
              <select v-model="form.priority">
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
                <option value="urgent">紧急</option>
              </select>
            </label>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn ghost" @click="showCreate = false">取消</button>
          <button class="btn" :disabled="creating" @click="create">{{ creating ? '创建中…' : '确定' }}</button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.toolbar select,
.toolbar input { padding: 7px 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
.toolbar input[type='search'] { flex: 1 1 180px; }
.link { padding: 0; border: 0; background: none; color: var(--text); font: inherit; text-align: left; cursor: pointer; }
.link:hover { color: var(--accent); }
.btn.danger { color: #fca5a5; }
.detail-head { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.detail-title { flex: 1; min-width: 220px; }
.detail-title h2 { margin: 0 0 2px; font-size: 20px; }
.detail-actions { display: flex; gap: 8px; }
.detail-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr) minmax(0, 0.95fr); gap: 16px; align-items: start; }
.col { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.body-view { margin: 0; padding: 12px; border: 1px solid var(--line); border-radius: 10px; background: rgba(4, 8, 16, 0.45); white-space: pre-wrap; word-break: break-word; font-size: 12.5px; line-height: 1.75; max-height: 360px; overflow: auto; }
.file-btn { position: relative; overflow: hidden; }
.file-btn input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.attach-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.attach-list li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 10px; border: 1px solid var(--line); border-radius: 10px; }
.warn { color: #fbbf24; }
.tab-body { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; max-height: 460px; overflow: auto; }
.summary { margin: 0; padding: 10px 12px; border-left: 3px solid var(--accent); background: rgba(56, 189, 248, 0.08); border-radius: 0 8px 8px 0; font-size: 13px; }
.feature-item { padding: 10px 12px; border: 1px solid var(--line); border-radius: 10px; }
.feature-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.feature-item p { margin: 6px 0 0; font-size: 12.5px; }
.acceptance { color: #a7f3d0; }
.chip-list { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 0; padding: 0; list-style: none; }
.chip-list li { padding: 3px 8px; border-radius: 999px; background: rgba(148, 163, 184, 0.14); font-size: 11px; }
.plan-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.plan-days { text-align: right; }
.plan-days strong { display: block; font-size: 22px; color: var(--accent); }
.plan-days span { font-size: 11px; color: var(--muted); }
.plan-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.chat-card { display: flex; flex-direction: column; min-height: 420px; }
.chat-log { flex: 1; display: flex; flex-direction: column; gap: 10px; margin: 10px 0; max-height: 380px; overflow: auto; }
.bubble { padding: 8px 10px; border-radius: 10px; border: 1px solid var(--line); }
.bubble.user { background: rgba(56, 189, 248, 0.1); }
.bubble.assistant { background: rgba(15, 23, 42, 0.6); }
.bubble-role { font-size: 10px; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 4px; }
.bubble-text { font-size: 12.5px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
.chat-input { display: flex; flex-direction: column; gap: 8px; }
.chat-input textarea { padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); resize: vertical; }
.form-stack { display: flex; flex-direction: column; gap: 12px; margin: 12px 0; }
.form-stack label { display: flex; flex-direction: column; gap: 6px; font-size: 12.5px; }
.form-stack input,
.form-stack select,
.form-stack textarea { padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 1200px) {
  .detail-grid { grid-template-columns: 1fr; }
}
</style>
