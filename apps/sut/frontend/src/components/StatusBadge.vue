<script setup>
const props = defineProps({
  status: { type: String, required: true },
})

const labels = {
  open: '待处理',
  in_progress: '处理中',
  closed: '已关闭',
}
</script>

<template>
  <span class="badge" :class="`status-${props.status}`">{{ labels[props.status] || props.status }}</span>
</template>
