<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { api } from '../../api/client'

const route = useRoute()
const summary = ref(null)
const skills = ref([])
const executions = ref([])
const loading = ref(false)
const error = ref('')

const passRate = computed(() => Math.round((summary.value?.pass_rate || 0) * 100))

const donut = computed(() => {
  const radius = 16
  const circumference = 2 * Math.PI * radius
  const filled = (circumference * passRate.value) / 100
  return {
    circumference,
    dash: `${filled} ${circumference - filled}`,
    offset: `${circumference / 4}`,
  }
})

const stats = computed(() => {
  const s = summary.value
  if (!s) return []
  return [
    { key: 'projects', label: '项目', value: s.projects, hint: '全平台项目数' },
    { key: 'cases', label: '用例', value: s.cases, hint: '含 AI 生成草稿' },
    { key: 'plans', label: '测试计划', value: s.plans, hint: '按项目组织' },
    { key: 'executions', label: '执行记录', value: s.executions, hint: '累计执行次数' },
    { key: 'defects', label: '缺陷', value: s.defects, hint: `未关闭 ${s.open_defects}` },
  ]
})

const skillGroups = computed(() => {
  const groups = new Map()
  for (const item of skills.value) {
    const key = item.category || 'other'
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(item)
  }
  return Array.from(groups, ([category, items]) => ({ category, items }))
})

const recent = computed(() => executions.value.slice(0, 6))

function statusText(item) {
  if (item.status === 'passed') return '通过'
  if (item.status === 'failed') return '失败'
  if (item.status === 'running') return '运行中'
  return item.status || '未知'
}

function statusClass(item) {
  if (item.status === 'passed') return 'dot ok'
  if (item.status === 'failed') return 'dot bad'
  return 'dot'
}

function when(value) {
  return (value || '').replace('T', ' ').slice(5, 16) || '—'
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [s, k, e] = await Promise.all([
      api.platformSummary(),
      api.platformSkills(),
      api.platformExecutions(),
    ])
    summary.value = s
    skills.value = k
    executions.value = e || []
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section class="stack">
    <article class="hero">
      <div>
        <p class="eyebrow">PROJECT OVERVIEW</p>
        <h1>项目概览</h1>
        <p class="muted">
          <template v-if="route.query.project">项目 #{{ route.query.project }} 的整体状态。</template>
          <template v-else>全平台聚合视角（未指定具体项目）。</template>
          数据来自平台真实记录，刷新即最新。
        </p>
      </div>
      <div class="hero-metrics">
        <div><strong>{{ skills.length }}</strong><span>可用能力</span></div>
      </div>
    </article>

    <p v-if="error" class="alert error">{{ error }}</p>

    <div class="stats-grid">
      <div v-for="item in stats" :key="item.key" class="stat-card">
        <p class="stat-label">{{ item.label }}</p>
        <strong class="stat-value">{{ item.value }}</strong>
        <span class="stat-hint">{{ item.hint }}</span>
      </div>

      <div class="stat-card donut-card">
        <div>
          <p class="stat-label">通过率</p>
          <strong class="stat-value">{{ passRate }}%</strong>
          <span class="stat-hint">
            {{ summary?.results_passed ?? 0 }} 通过 / {{ summary?.results_failed ?? 0 }} 失败
          </span>
        </div>
        <svg class="donut" viewBox="0 0 42 42" aria-hidden="true">
          <circle class="donut-track" cx="21" cy="21" r="16" />
          <circle
            class="donut-value"
            cx="21"
            cy="21"
            r="16"
            :stroke-dasharray="donut.dash"
            :stroke-dashoffset="donut.offset"
          />
        </svg>
      </div>
    </div>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>平台能力（Skills）</h2>
          <p class="muted">按 category 分组，前端只负责渲染，能力本身全部来自注册表</p>
        </div>
        <RouterLink class="btn ghost tiny" to="/system-ai">系统 AI 配置</RouterLink>
      </div>

      <div class="skill-groups">
        <div v-for="group in skillGroups" :key="group.category" class="skill-group">
          <span class="cat-chip">{{ group.category }}</span>
          <div class="skill-chips">
            <span v-for="item in group.items" :key="item.id" class="skill-chip" :title="item.description">
              <b>{{ item.name }}</b>
              <em>{{ item.id }}</em>
            </span>
          </div>
        </div>
        <p v-if="!skills.length && !loading" class="empty">暂未注册任何 skill。</p>
      </div>
    </article>

    <article class="card">
      <div class="card-head">
        <div>
          <h2>最近执行</h2>
          <p class="muted">最近 6 次执行，失败的在执行记录里可以点 AI 归因</p>
        </div>
        <RouterLink class="btn ghost tiny" to="/api-automation">执行记录</RouterLink>
      </div>

      <ol v-if="recent.length" class="timeline">
        <li v-for="item in recent" :key="item.id">
          <span :class="statusClass(item)" />
          <div class="tl-main">
            <strong>{{ item.plan_name || `执行 #${item.id}` }}</strong>
            <span class="tl-sub">
              {{ statusText(item) }} · {{ item.passed ?? 0 }} 通过 / {{ item.failed ?? 0 }} 失败
            </span>
          </div>
          <time class="tl-time">{{ when(item.started_at) }}</time>
        </li>
      </ol>
      <p v-else-if="!loading" class="empty">还没有执行记录，先去接口自动化跑一条用例。</p>
    </article>
  </section>
</template>

<style scoped>
.donut-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.donut {
  width: 62px;
  height: 62px;
  flex: none;
  transform: rotate(-90deg);
}

.donut circle {
  fill: none;
  stroke-width: 4;
}

.donut-track {
  stroke: var(--line);
}

.donut-value {
  stroke: var(--lime);
  stroke-linecap: round;
  transition: stroke-dasharray 0.4s ease;
}

.skill-groups {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.skill-group {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.cat-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 10px;
  border: 1px solid var(--lime-line);
  border-radius: 999px;
  background: var(--lime-soft);
  color: var(--lime-deep);
  font-size: 11px;
  font-weight: 700;
}

.skill-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 7px;
  padding: 5px 10px;
  border: 1px solid var(--line);
  border-radius: 9px;
  background: var(--bg);
}

.skill-chip b {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--ink);
}

.skill-chip em {
  font-family: var(--font-mono);
  font-size: 10.5px;
  font-style: normal;
  color: var(--muted);
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.timeline li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 2px;
  border-bottom: 1px dashed var(--line);
}

.timeline li:last-child {
  border-bottom: 0;
}

.dot {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 50%;
  background: var(--line-strong);
}

.dot.ok {
  background: var(--ok);
  box-shadow: 0 0 0 3px var(--ok-soft);
}

.dot.bad {
  background: var(--danger);
  box-shadow: 0 0 0 3px var(--danger-soft);
}

.tl-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.tl-main strong {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
}

.tl-sub {
  font-size: 11.5px;
  color: var(--muted);
}

.tl-time {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 720px) {
  .skill-group {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
