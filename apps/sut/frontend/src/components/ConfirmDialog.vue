<script setup>
import { nextTick, ref, watch } from 'vue'
import { confirmState, settleConfirm } from '../composables/confirm'

const confirmButton = ref(null)
let lastFocused = null

function onKeydown(event) {
  if (!confirmState.open) return
  if (event.key === 'Escape') {
    event.preventDefault()
    settleConfirm(false)
  }
}

watch(
  () => confirmState.open,
  async (open) => {
    if (open) {
      lastFocused = document.activeElement
      window.addEventListener('keydown', onKeydown)
      await nextTick()
      confirmButton.value?.focus()
    } else {
      window.removeEventListener('keydown', onKeydown)
      if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus()
      lastFocused = null
    }
  },
)
</script>

<template>
  <div v-if="confirmState.open" class="modal-mask" role="presentation" @click.self="settleConfirm(false)">
    <div class="modal confirm-modal" role="dialog" aria-modal="true" :aria-label="confirmState.title">
      <header>
        <h2>{{ confirmState.title }}</h2>
      </header>
      <p class="confirm-message">{{ confirmState.message }}</p>
      <footer>
        <button class="btn ghost" type="button" @click="settleConfirm(false)">{{ confirmState.cancelText }}</button>
        <button
          ref="confirmButton"
          class="btn"
          :class="{ danger: confirmState.danger }"
          type="button"
          @click="settleConfirm(true)"
        >
          {{ confirmState.confirmText }}
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.confirm-modal {
  width: min(420px, calc(100vw - 32px));
  padding: 22px 24px 20px;
}

.confirm-modal header h2 {
  font-size: 15px;
}

.confirm-message {
  margin: 8px 0 20px;
  color: var(--ink-2);
  font-size: 13.5px;
  line-height: 1.75;
  overflow-wrap: anywhere;
}

.confirm-modal footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 0;
  border-top: 0;
}
</style>
