<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'

defineProps({
  items: { type: Array, required: true },
})

const open = ref(false)
const root = ref(null)

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function onDocClick(event) {
  if (!root.value?.contains(event.target)) close()
}

function onKeydown(event) {
  if (event.key === 'Escape') close()
}

watch(open, (value) => {
  if (value) window.addEventListener('keydown', onKeydown)
  else window.removeEventListener('keydown', onKeydown)
})

document.addEventListener('click', onDocClick)
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div ref="root" class="row-menu">
    <button class="btn ghost tiny" type="button" :aria-expanded="open" aria-haspopup="menu" @click.stop="toggle">⋯</button>
    <ul v-if="open" class="row-menu-pop">
      <li v-for="item in items" :key="item.label">
        <button type="button" :class="{ danger: item.danger }" @click.stop="close(); item.run()">
          {{ item.label }}
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.row-menu {
  position: relative;
}

.row-menu-pop {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 20;
  min-width: 132px;
  margin: 0;
  padding: 5px;
  list-style: none;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--panel);
  box-shadow: var(--shadow-2);
}

.row-menu-pop button {
  width: 100%;
  padding: 7px 10px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--ink-2);
  font-family: var(--font);
  font-size: 12.5px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.row-menu-pop button:hover {
  background: var(--bg);
  color: var(--ink);
}

.row-menu-pop button.danger {
  color: var(--danger);
}

.row-menu-pop button.danger:hover {
  background: var(--danger-soft);
}
</style>
