<script setup>
defineProps({
  title: { type: String, required: true },
  phase: { type: String, default: 'Phase 1' },
  description: { type: String, default: '' },
  features: { type: Array, default: () => [] },
  skill: { type: String, default: '' },
})
</script>

<template>
  <section class="stack">
    <div class="card hero">
      <p class="eyebrow">MODULE</p>
      <h2 style="margin: 6px 0 8px">{{ title }}</h2>
      <p class="muted" style="margin: 0">{{ description }}</p>
      <div style="margin-top: 14px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap">
        <span class="badge">{{ phase }}</span>
        <span v-if="skill" class="mono muted">skill: {{ skill }}</span>
      </div>
    </div>
    <div class="card">
      <div class="card-head">
        <h3>规划中的能力</h3>
        <span class="muted">随 Phase 推进逐项落地</span>
      </div>
      <ul class="feature-list">
        <li v-for="(item, index) in features" :key="index">{{ item }}</li>
      </ul>
    </div>
  </section>
</template>
