<script setup>
import NavIcon from './NavIcon.vue'

defineProps({
  icon: { type: String, default: 'overview' },
  title: { type: String, default: '这里还没有内容' },
  hint: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <div class="empty-state" :class="{ compact }">
    <span class="empty-icon"><NavIcon :name="icon" :size="compact ? 22 : 30" /></span>
    <div class="empty-text">
      <strong>{{ title }}</strong>
      <p v-if="hint">{{ hint }}</p>
    </div>
    <div v-if="$slots.action" class="empty-action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 34px 20px;
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--bg-tint);
  text-align: center;
}

.empty-state.compact {
  flex-direction: row;
  justify-content: flex-start;
  padding: 16px 18px;
  text-align: left;
}

.empty-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border: 1px solid var(--lime-line);
  border-radius: 50%;
  background: var(--lime-soft);
  color: var(--lime-deep);
}

.compact .empty-icon {
  width: 36px;
  height: 36px;
  flex: none;
}

.empty-text strong {
  display: block;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--ink);
}

.empty-text p {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: var(--muted);
  max-width: 46ch;
}

.empty-action {
  margin-top: 4px;
}
</style>
