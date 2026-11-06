<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { api } from '../../api/client'

const route = useRoute()
const summary = ref(null)
const skills = ref([])
const loading = ref(false)
const error = ref('')

const stats = computed(() => {
  const s = summary.value
  if (!s) return []
  return [
    { key: 'projects', label: '项目', value: s.projects, hint: '全平台项目数' },
    { key: 'cases', label: '用例', value: s.cases, hint: '含 AI 生成草稿' },
    { key: 'plans', label: '测试计划', value: s.plans, hint: '按项目组织' },
    {
      key: 'executions',
      label: '执行记录',
      value: s.executions,
      hint: '全平台累计执行次数',
    },
    { key: 'defects', label: '缺陷', value: s.defects, hint: `未关闭 ${s.open_defects}` },
    {
      key: 'pass_rate',
      label: '通过率',
      value: `${Math.round((s.pass_rate || 0) * 100)}%`,
      hint: `按用例结果统计 · ${s.results_passed ?? 0} 通过 / ${s.results_failed ?? 0} 失败`,
    },
  ]
})

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [s, k] = await Promise.all([api.platformSummary(), api.platformSkills()])
    summary.value = s
    skills.value = k
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
    <article class="hero card">
      <div>
        <p class="eyebrow">PROJECT OVERVIEW</p>
        <h2>项目概览</h2>
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
    </div>

    <article class="card">
      <div class="card-head">
        <div><h2>平台能力（Skills）</h2><p>所有测试能力都以 skill 形式注册，前端按 category 渲染</p></div>
        <RouterLink class="btn ghost" to="/system-ai">系统 AI 配置</RouterLink>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>名称</th><th>分类</th><th>说明</th></tr></thead>
          <tbody>
            <tr v-for="item in skills" :key="item.id">
              <td class="mono">{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td><span class="badge">{{ item.category }}</span></td>
              <td class="muted">{{ item.description }}</td>
            </tr>
            <tr v-if="!skills.length && !loading"><td colspan="4" class="empty">暂未注册任何 skill。</td></tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>
