<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useTicketStore } from '../stores/tickets'
import StatusBadge from '../components/StatusBadge.vue'

const store = useTicketStore()
const search = ref('')
const statusFilter = ref('all')
const priorityFilter = ref('all')
const showForm = ref(false)
const submitting = ref(false)
const formError = ref('')
const form = reactive({ title: '', description: '', priority: 'medium' })

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

onMounted(() => {
  if (!store.items.length) store.fetchAll()
})

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
  try {
    await store.update(ticket.id, { status: event.target.value })
  } catch (error) {
    alert(error.message)
  }
}

async function changePriority(ticket, event) {
  try {
    await store.update(ticket.id, { priority: event.target.value })
  } catch (error) {
    alert(error.message)
  }
}

async function removeTicket(ticket) {
  if (!window.confirm(`删除工单 #${ticket.id}？`)) return
  try {
    await store.remove(ticket.id)
  } catch (error) {
    alert(error.message)
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
            <tr v-for="ticket in filtered" :key="ticket.id">
              <td class="mono">#{{ ticket.id }}</td>
              <td>
                <strong>{{ ticket.title }}</strong>
                <p v-if="ticket.description" class="cell-sub">{{ ticket.description }}</p>
              </td>
              <td>
                <select :value="ticket.priority" class="mini-select" @change="changePriority(ticket, $event)">
                  <option v-for="item in priorityOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
                </select>
              </td>
              <td>
                <select :value="ticket.status" class="mini-select" @change="changeStatus(ticket, $event)">
                  <option v-for="item in statusOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
                </select>
              </td>
              <td class="muted">{{ new Date(ticket.created_at).toLocaleString('zh-CN', { hour12: false }) }}</td>
              <td><StatusBadge :status="ticket.status" /> <button class="btn ghost delete-ticket" @click="removeTicket(ticket)">删除</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>

    <div v-if="showForm" class="modal-mask" @click.self="showForm = false">
      <div class="modal card">
        <div class="card-head">
          <div>
            <h2>新建工单</h2>
            <p>创建后会立即出现在列表和仪表盘</p>
          </div>
          <button class="icon-btn" @click="showForm = false">×</button>
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
            <button type="button" class="btn ghost" @click="showForm = false">取消</button>
            <button class="btn" :disabled="submitting">{{ submitting ? '创建中…' : '创建' }}</button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>
