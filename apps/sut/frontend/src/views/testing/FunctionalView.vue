<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../api/client'
import EmptyState from '../../components/EmptyState.vue'
import RowMenu from '../../components/RowMenu.vue'

const tab = ref('manage')
const projects = ref([])
const requirements = ref([])
const cases = ref([])
const skills = ref([])
const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const error = ref('')
const notice = ref('')

const filter = reactive({ project_id: '', status: '', keyword: '' })
const genForm = reactive({ project_id: '', requirement_id: '', requirement: '', max_cases: 10 })
const generated = ref([])
const selected = ref([])
const editing = ref(null)

const STATUS_TEXT = {
  draft: '草稿',
  pending_review: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}
const STATUS_CLASS = {
  draft: 'module-planned',
  pending_review: '',
  approved: 'module-done',
  rejected: 'module-failed',
}
const REQ_STATUS_TEXT = { draft: '草稿', analyzed: '已分析', planned: '已排期' }

const currentProject = computed(() => projects.value.find((p) => p.id === Number(filter.project_id)))
const visibleCases = computed(() => {
  const keyword = filter.keyword.trim().toLowerCase()
  return cases.value.filter((item) => {
    if (filter.status && item.status !== filter.status) return false
    if (!keyword) return true
    return `${item.title} ${item.module}`.toLowerCase().includes(keyword)
  })
})
const stats = computed(() => ({
  total: cases.value.length,
  pending: cases.value.filter((c) => c.status === 'pending_review').length,
  approved: cases.value.filter((c) => c.status === 'approved').length,
}))
const allChecked = computed(
  () => visibleCases.value.length > 0 && visibleCases.value.every((c) => selected.value.includes(c.id)),
)
const projectRequirements = computed(() =>
  requirements.value.filter((r) => !genForm.project_id || r.project_id === Number(genForm.project_id)),
)

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [p, k, r] = await Promise.all([
      api.platformProjects(),
      api.platformSkills('case'),
      api.platformRequirements(),
    ])
    projects.value = p
    skills.value = k
    requirements.value = r
    if (!filter.project_id && p.length) filter.project_id = p[0].id
    if (!genForm.project_id && p.length) genForm.project_id = p[0].id
    await loadCases()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function loadCases() {
  if (!filter.project_id) return
  try {
    const result = await api.runPlatformSkill('case.list', { project_id: Number(filter.project_id) })
    cases.value = result.result?.cases || []
    selected.value = selected.value.filter((id) => cases.value.some((c) => c.id === id))
  } catch (err) {
    error.value = err.message
  }
}

function toggleAll(event) {
  selected.value = event.target.checked ? visibleCases.value.map((c) => c.id) : []
}

function toggleOne(id) {
  const index = selected.value.indexOf(id)
  if (index >= 0) selected.value.splice(index, 1)
  else selected.value.push(id)
}

async function runBatch(action, extra = {}) {
  if (!selected.value.length) return
  error.value = ''
  notice.value = ''
  try {
    const result = await api.batchPlatformCases({ action, ids: [...selected.value], ...extra })
    const body = result.result || {}
    const skipped = body.skipped?.length ? `，跳过 ${body.skipped.length} 条（${body.skipped[0].reason}）` : ''
    notice.value = `已处理 ${body.updated} 条${skipped}`
    selected.value = []
    await loadCases()
  } catch (err) {
    error.value = err.message
  }
}

async function openEdit(item) {
  editing.value = {
    id: item.id,
    title: item.title,
    module: item.module,
    priority: item.priority,
    steps: item.steps || '',
    expected: item.expected || '',
  }
  try {
    const detail = await api.platformCase(item.id)
    editing.value = {
      id: detail.id,
      title: detail.title,
      module: detail.module,
      priority: detail.priority,
      steps: detail.steps || '',
      expected: detail.expected || '',
    }
  } catch (err) {
    error.value = err.message
  }
}

async function saveCase() {
  if (!editing.value) return
  saving.value = true
  error.value = ''
  try {
    await api.updatePlatformCase(editing.value.id, {
      title: editing.value.title,
      module: editing.value.module,
      priority: editing.value.priority,
      steps: editing.value.steps,
      expected: editing.value.expected,
    })
    notice.value = `用例 #${editing.value.id} 已保存`
    editing.value = null
    await loadCases()
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function removeCase(item) {
  error.value = ''
  try {
    await api.deletePlatformCase(item.id)
    notice.value = `用例 #${item.id} 已删除`
    await loadCases()
  } catch (err) {
    error.value = err.message
  }
}

async function generate() {
  if (!genForm.project_id) {
    error.value = '请先选择项目'
    return
  }
  if (!genForm.requirement.trim() && !genForm.requirement_id) {
    error.value = '请输入需求内容，或选择一条已分析的需求'
    return
  }
  generating.value = true
  error.value = ''
  notice.value = ''
  generated.value = []
  try {
    const payload = {
      project_id: Number(genForm.project_id),
      max_cases: Number(genForm.max_cases) || 10,
    }
    if (genForm.requirement.trim()) payload.requirement = genForm.requirement.trim()
    if (genForm.requirement_id) payload.requirement_id = Number(genForm.requirement_id)
    const result = await api.runPlatformSkill('case.generate', payload)
    generated.value = result.result?.cases || []
    notice.value = `已生成 ${generated.value.length} 条草稿（模型 ${result.result?.model_name || '-'}），确认后可提交审核`
    await loadCases()
  } catch (err) {
    error.value = err.message
  } finally {
    generating.value = false
  }
}

function pickRequirement() {
  const req = requirements.value.find((r) => r.id === Number(genForm.requirement_id))
  if (req) genForm.project_id = req.project_id
}

onMounted(refresh)
</script>

<template>
  <section class="stack">
    <article class="hero">
      <div>
        <p class="eyebrow">FUNCTIONAL TEST</p>
        <h1>功能测试</h1>
        <p class="muted">
          AI 先生成用例草稿，你确认后提交审核；用例可批量流转、可编辑，能力全部走 skill 注册。
        </p>
      </div>
      <div class="inline-stats">
        <span class="stat-pill"><b>{{ stats.total }}</b> 当前项目用例</span>
        <span class="stat-pill"><b>{{ stats.pending }}</b> 待审核</span>
        <span class="stat-pill"><b>{{ stats.approved }}</b> 已通过</span>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="notice" class="alert">{{ notice }}</p>

    <div class="slim-banner">
      <span>当前项目 {{ currentProject ? currentProject.name : '未选择' }}</span>
      <span class="sep">·</span>
      <span>{{ visibleCases.length }} 条命中</span>
      <span class="sep">·</span>
      <span>状态筛选可批量流转草稿 → 待审核 → 已通过</span>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'manage' }" @click="tab = 'manage'">用例管理</button>
      <button class="tab" :class="{ active: tab === 'generate' }" @click="tab = 'generate'">AI 生成</button>
    </div>

    <template v-if="tab === 'manage'">
      <article class="card">
        <div class="toolbar">
          <select v-model="filter.project_id" @change="loadCases">
            <option value="" disabled>请选择项目</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">#{{ p.id }} {{ p.name }}</option>
          </select>
          <select v-model="filter.status">
            <option value="">全部状态</option>
            <option v-for="(text, key) in STATUS_TEXT" :key="key" :value="key">{{ text }}</option>
          </select>
          <input v-model="filter.keyword" type="search" maxlength="80" placeholder="搜索标题或模块（最多 80 字）" />
          <button class="btn ghost" :disabled="loading" @click="loadCases">{{ loading ? '加载中' : '刷新' }}</button>
        </div>
      </article>

      <article class="card">
        <div class="card-head">
          <div>
            <h2>用例列表</h2>
            <p>{{ currentProject ? currentProject.name : '未选择项目' }} · 共 {{ visibleCases.length }} 条</p>
          </div>
          <div v-if="selected.length" class="batch-bar">
            <span class="muted">已选 {{ selected.length }}</span>
            <button class="btn ghost" @click="runBatch('submit_review')">提交审核</button>
            <button class="btn ghost" @click="runBatch('approve')">通过</button>
            <button class="btn ghost" @click="runBatch('reject')">驳回</button>
            <button class="btn ghost" @click="runBatch('draft')">退回草稿</button>
            <button class="btn danger" @click="runBatch('delete')">删除</button>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th class="check-col"><input type="checkbox" :checked="allChecked" @change="toggleAll" /></th>
                <th>ID</th>
                <th>标题</th>
                <th>模块</th>
                <th>优先级</th>
                <th>状态</th>
                <th>来源</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="loading && !visibleCases.length">
                <tr v-for="n in 6" :key="`sk-${n}`" class="skeleton-row">
                  <td class="check-col"><span class="skeleton" style="width: 14px; height: 14px" /></td>
                  <td><span class="skeleton" style="width: 32px" /></td>
                  <td><span class="skeleton" style="width: 68%" /></td>
                  <td><span class="skeleton" style="width: 44px" /></td>
                  <td><span class="skeleton" style="width: 40px" /></td>
                  <td><span class="skeleton" style="width: 52px" /></td>
                  <td><span class="skeleton" style="width: 34px" /></td>
                  <td><span class="skeleton" style="width: 96px" /></td>
                </tr>
              </template>
              <tr v-for="item in visibleCases" :key="item.id">
                <td class="check-col">
                  <input type="checkbox" :checked="selected.includes(item.id)" @change="toggleOne(item.id)" />
                </td>
                <td class="mono">#{{ item.id }}</td>
                <td>{{ item.title }}</td>
                <td class="muted">{{ item.module }}</td>
                <td>{{ item.priority }}</td>
                <td><span class="badge" :class="STATUS_CLASS[item.status]">{{ STATUS_TEXT[item.status] || item.status }}</span></td>
                <td class="muted">{{ item.source === 'ai' ? 'AI' : '手工' }}</td>
                <td>
                  <div class="row-actions">
                    <button class="btn" @click="openEdit(item)">编辑</button>
                    <RowMenu :items="[{ label: '删除用例', danger: true, run: () => removeCase(item) }]" />
                  </div>
                </td>
              </tr>
              <tr v-if="!visibleCases.length && !loading">
                <td colspan="8">
                  <EmptyState
                    icon="functional"
                    title="这个筛选条件下没有用例"
                    hint="换个项目或状态试试，或者到「AI 生成」按需求生成一批草稿。"
                  >
                    <template #action>
                      <button class="btn tiny" type="button" @click="tab = 'generate'">去生成用例</button>
                    </template>
                  </EmptyState>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </template>

    <template v-else>
      <div class="split-grid">
        <article class="card">
          <div class="card-head"><div><h2>生成用例草稿</h2><p>基于已启用的大模型</p></div></div>
          <div class="form-stack">
            <label>
              <span class="muted">项目</span>
              <select v-model="genForm.project_id">
                <option value="" disabled>请选择项目</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">#{{ p.id }} {{ p.name }}</option>
              </select>
            </label>
            <label>
              <span class="muted">从需求库选择（可选，自动带上分析出的功能点）</span>
              <select v-model="genForm.requirement_id" @change="pickRequirement">
                <option value="">不使用需求库</option>
                <option v-for="r in projectRequirements" :key="r.id" :value="r.id">
                  #{{ r.id }} {{ r.title }}（{{ REQ_STATUS_TEXT[r.status] || r.status }}）
                </option>
              </select>
            </label>
            <label>
              <span class="muted">需求内容</span>
              <textarea v-model="genForm.requirement" rows="8" placeholder="粘贴需求片段，或直接描述要测的接口/功能点……" />
            </label>
            <label class="inline">
              <span class="muted">最多生成</span>
              <input v-model.number="genForm.max_cases" type="number" min="1" max="50" />
              <button class="btn" :disabled="generating" @click="generate">
                {{ generating ? '生成中…' : 'AI 生成用例' }}
              </button>
            </label>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div><h2>本次生成</h2><p>已写入用例管理，状态为草稿</p></div>
            <button
              class="btn ghost"
              :disabled="!generated.length"
              @click="selected = generated.map((c) => c.id); runBatch('submit_review')"
            >
              全部提交审核
            </button>
          </div>
          <div v-if="!generated.length" class="empty">还没有生成结果。</div>
          <div v-else class="gen-list">
            <article v-for="item in generated" :key="item.id" class="gen-item">
              <header>
                <strong>{{ item.title }}</strong>
                <span class="badge">{{ item.priority }}</span>
              </header>
              <p class="muted mono">{{ item.module }} · #{{ item.id }}</p>
              <pre class="steps">{{ item.steps }}</pre>
              <p class="muted">预期：{{ item.expected }}</p>
            </article>
          </div>
        </article>
      </div>
    </template>

    <article class="card">
      <div class="card-head"><div><h2>已注册的 case skill</h2><p>前端按 category=case 拉取，不写死页面逻辑</p></div></div>
      <div class="skill-chips">
        <span v-for="item in skills" :key="item.id" class="skill-chip" :title="item.description">
          <b>{{ item.name }}</b>
          <em>{{ item.id }}</em>
        </span>
      </div>
    </article>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <header>
          <h2>编辑用例 #{{ editing.id }}</h2>
          <button class="btn ghost" data-modal-close @click="editing = null">关闭</button>
        </header>
        <p v-if="error" class="alert error modal-alert">{{ error }}</p>
        <div class="form-stack">
          <label><span class="muted">标题</span><input v-model="editing.title" type="text" /></label>
          <div class="form-row">
            <label><span class="muted">模块</span><input v-model="editing.module" type="text" /></label>
            <label>
              <span class="muted">优先级</span>
              <select v-model="editing.priority">
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </label>
          </div>
          <label><span class="muted">步骤</span><textarea v-model="editing.steps" rows="8" /></label>
          <label><span class="muted">预期结果</span><textarea v-model="editing.expected" rows="3" /></label>
        </div>
        <footer>
          <button class="btn ghost" @click="editing = null">取消</button>
          <button class="btn" :disabled="saving" @click="saveCase">{{ saving ? '保存中…' : '保存' }}</button>
        </footer>
      </div>
    </div>
  </section>
</template>

<style scoped>
.toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.toolbar select { width: auto; min-width: 160px; }
.toolbar input[type='search'] { flex: 1 1 220px; width: auto; }
.toolbar select,
.toolbar input,
.form-stack select,
.form-stack input,
.form-stack textarea { padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(4, 8, 16, 0.5); color: var(--text); }
.check-col { width: 40px; }
.check-col input[type='checkbox'] { width: 14px; height: 14px; padding: 0; accent-color: var(--accent); }
.batch-bar { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.btn.danger { border-color: rgba(248, 113, 113, 0.5); color: #fca5a5; }
.form-stack { display: flex; flex-direction: column; gap: 12px; margin-top: 8px; }
.form-stack label { display: flex; flex-direction: column; gap: 6px; font-size: 12.5px; }
.form-stack label.inline { flex-direction: row; align-items: center; gap: 8px; }
.form-stack input[type='number'] { width: 90px; }
.form-row { display: grid; grid-template-columns: 1fr 140px; gap: 10px; }
.gen-list { display: flex; flex-direction: column; gap: 10px; max-height: 560px; overflow-y: auto; }
.gen-item { border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; background: rgba(4, 8, 16, 0.35); }
.gen-item header { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
.gen-item .steps { margin: 6px 0; white-space: pre-wrap; font-size: 12px; color: var(--muted); }
.modal-mask { position: fixed; inset: 0; background: rgba(3, 6, 12, 0.72); display: flex; align-items: center; justify-content: center; z-index: 40; padding: 24px; }
.modal { width: min(720px, 100%); max-height: 88vh; overflow-y: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 18px 20px; }
.modal header { display: flex; justify-content: space-between; align-items: center; }
.modal footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px; }
</style>
