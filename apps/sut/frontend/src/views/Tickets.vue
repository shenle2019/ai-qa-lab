<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useTicketStore } from '../stores/tickets'
import StatusBadge from '../components/StatusBadge.vue'
import { askConfirm } from '../composables/confirm'

const store = useTicketStore()
const search = ref('')
const statusFilter = ref('all')
const priorityFilter = ref('all')
const showForm = ref(false)
const submitting = ref(false)
const formError = ref('')
const form = reactive({ title: '', description: '', priority: 'medium' })
const editing = ref(null)
const editError = ref('')
const editForm = reactive({ title: '', description: '', priority: 'medium', status: 'open' })
const actionError = ref('')
const notice = ref('')
const page = ref(1)
const PAGE_SIZE = 20
let noticeTimer = null

const statusOptions = [
  { value: 'open', label: '待处理' },
  { value: 'in_progress', label: '处理中' },
  { value: 'closed', label: '已关闭' },
]
const priorityOptions = [
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
]

const filtered = computed(() =>
  store.items.filter((ticket) => {
    if (statusFilter.value !== 'all' && ticket.status !== statusFilter.value) return false
    if (priorityFilter.value !== 'all' && ticket.priority !== priorityFilter.value) return false
    const keyword = search.value.trim().toLowerCase()
    if (!keyword) return true
    return (
      ticket.title.toLowerCase().includes(keyword) ||
      ticket.description.toLowerCase().includes(keyword)
    )
  }),
)

const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))
const paged = computed(() => filtered.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

watch([search, statusFilter, priorityFilter], () => {
  page.value = 1
})

watch(pageCount, (value) => {
  if (page.value > value) page.value = value
})

function flash(message) {
  notice.value = message
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    notice.value = ''
  }, 2500)
}

function resetForm() {
  form.title = ''
  form.description = ''
  form.priority = 'medium'
  formError.value = ''
}

async function closeCreate() {
  if (form.title.trim() || form.description.trim()) {
    if (!(await askConfirm({ message: '放弃已填写的内容？' }))) return
  }
  resetForm()
  showForm.value = false
}

async function closeEdit() {
  const changed =
    editing.value &&
    (editForm.title !== editing.value.title ||
      editForm.description !== editing.value.description ||
      editForm.priority !== editing.value.priority ||
      editForm.status !== editing.value.status)
  if (changed && !(await askConfirm({ message: '放弃未保存的修改？' }))) return
  editing.value = null
  editError.value = ''
}

onMounted(() => {
  if (!store.items.length) store.fetchAll()
})

onUnmounted(() => clearTimeout(noticeTimer))

async function createTicket() {
  if (!form.title.trim()) {
    formError.value = '标题不能为空'
    return
  }
  submitting.value = true
  formError.value = ''
  try {
    await store.create({
      title: form.title.trim(),
      description: form.description.trim(),
      priority: form.priority,
    })
    form.title = ''
    form.description = ''
    form.priority = 'medium'
    showForm.value = false
  } catch (error) {
    formError.value = error.message
  } finally {
    submitting.value = false
  }
}

async function changeStatus(ticket, event) {
  const previous = ticket.status
  actionError.value = ''
  try {
    await store.update(ticket.id, { status: event.target.value })
    flash(`已更新工单 #${ticket.id} 的状态`)
  } catch (error) {
    event.target.value = previous
    actionError.value = error.message
  }
}

async function changePriority(ticket, event) {
  const previous = ticket.priority
  actionError.value = ''
  try {
    await store.update(ticket.id, { priority: event.target.value })
    flash(`已更新工单 #${ticket.id} 的优先级`)
  } catch (error) {
    event.target.value = previous
    actionError.value = error.message
  }
}

function openEdit(ticket) {
  editing.value = ticket
  editError.value = ''
  Object.assign(editForm, {
    title: ticket.title,
    description: ticket.description,
    priority: ticket.priority,
    status: ticket.status,
  })
}

async function saveEdit() {
  if (!editForm.title.trim()) {
    editError.value = '标题不能为空'
    return
  }
  try {
    await store.update(editing.value.id, {
      title: editForm.title.trim(),
      description: editForm.description.trim(),
      priority: editForm.priority,
      status: editForm.status,
    })
    editing.value = null
  } catch (error) {
    editError.value = error.message
  }
}

async function removeTicket(ticket) {
  if (!(await askConfirm({ message: `删除工单 #${ticket.id}？` }))) return
  actionError.value = ''
  try {
    await store.remove(ticket.id)
    flash(`已删除工单 #${ticket.id}`)
  } catch (error) {
    actionError.value = error.message
  }
}
</script>

<template>
  <section class="stack">
    <div class="toolbar card">
      <div class="filters">
        <input v-model="search" class="search" placeholder="搜索标题或描述…" />
        <select v-model="statusFilter">
          <option value="all">全部状态</option>
          <option v-for="item in statusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
        <select v-model="priorityFilter">
          <option value="all">全部优先级</option>
          <option v-for="item in priorityOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
      </div>
      <div class="toolbar-actions">
        <span class="muted">{{ filtered.length }} / {{ store.items.length }} 条</span>
        <button class="btn" @click="showForm = true">+ 新建工单</button>
      </div>
    </div>

    <p v-if="store.error" class="alert error">{{ store.error }}</p>
    <p v-if="actionError" class="alert error">{{ actionError }}</p>
    <p v-if="notice" class="alert">{{ notice }}</p>

    <article class="card">
      <div v-if="store.loading" class="muted">加载中…</div>
      <div v-else-if="!filtered.length" class="empty">没有匹配的工单。</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>标题 / 描述</th>
              <th>优先级</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ticket in paged" :key="ticket.id">
              <td class="mono">#{{ ticket.id }}</td>
              <td>
                <strong>{{ ticket.title }}</strong>
                <p v-if="ticket.description" class="cell-sub">{{ ticket.description }}</p>
              </td>
              <td>
                <select :value="ticket.priority" class="mini-select" :title="`修改工单 #${ticket.id} 的优先级`" :aria-label="`修改工单 #${ticket.id} 的优先级`" @change="changePriority(ticket, $event)">
                  <option v-for="item in priorityOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
                </select>
              </td>
              <td>
                <select :value="ticket.status" class="mini-select" :title="`修改工单 #${ticket.id} 的状态`" :aria-label="`修改工单 #${ticket.id} 的状态`" @change="changeStatus(ticket, $event)">
                  <option v-for="item in statusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
                </select>
              </td>
              <td class="muted">{{ new Date(ticket.created_at).toLocaleString('zh-CN', { hour12: false }) }}</td>
              <td>
                <StatusBadge :status="ticket.status" />
                <button class="btn ghost edit-ticket" @click="openEdit(ticket)">编辑</button>
                <button class="btn ghost delete-ticket" @click="removeTicket(ticket)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="pageCount > 1" class="pager">
      <button class="btn ghost" :disabled="page === 1" @click="page -= 1">上一页</button>
      <span class="muted">第 {{ page }} / {{ pageCount }} 页</span>
      <button class="btn ghost" :disabled="page === pageCount" @click="page += 1">下一页</button>
    </div>

    <div v-if="showForm" class="modal-mask" @click.self="closeCreate">
      <div class="modal card">
        <div class="card-head">
          <div>
            <h2>新建工单</h2>
            <p>创建后会立即出现在列表和仪表盘</p>
          </div>
          <button class="icon-btn" @click="closeCreate">×</button>
        </div>
        <form class="stack-sm" @submit.prevent="createTicket">
          <label>
            <span>标题</span>
            <input v-model="form.title" maxlength="200" placeholder="一句话描述问题" />
          </label>
          <label>
            <span>描述</span>
            <textarea v-model="form.description" rows="4" maxlength="5000" placeholder="复现步骤、期望结果、实际结果"></textarea>
          </label>
          <label>
            <span>优先级</span>
            <select v-model="form.priority">
              <option v-for="item in priorityOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>
          <p v-if="formError" class="alert error">{{ formError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn ghost" @click="closeCreate">取消</button>
            <button class="btn" :disabled="submitting">{{ submitting ? '创建中…' : '创建' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="closeEdit">
      <div class="modal card">
        <div class="card-head">
          <div>
            <h2>编辑工单 #{{ editing.id }}</h2>
            <p>修改标题、描述、优先级和状态</p>
          </div>
          <button class="icon-btn" @click="closeEdit">×</button>
        </div>
        <form class="stack-sm" @submit.prevent="saveEdit">
          <label>
            <span>标题</span>
            <input v-model="editForm.title" maxlength="200" />
          </label>
          <label>
            <span>描述</span>
            <textarea v-model="editForm.description" rows="4" maxlength="5000"></textarea>
          </label>
          <label>
            <span>优先级</span>
            <select v-model="editForm.priority">
              <option v-for="item in priorityOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>
          <label>
            <span>状态</span>
            <select v-model="editForm.status">
              <option v-for="item in statusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>
          <p v-if="editError" class="alert error">{{ editError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn ghost" @click="closeEdit">取消</button>
            <button class="btn">保存</button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pager {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}
</style>
