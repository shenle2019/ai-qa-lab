import { reactive } from 'vue'

/**
 * 全局确认弹层状态。
 *
 * 视图里用 `await askConfirm({ ... })` 代替 `window.confirm`，
 * 由挂载在 App 根部的 <ConfirmDialog /> 渲染，保证弹层样式与全站一致。
 */
export const confirmState = reactive({
  open: false,
  title: '请确认',
  message: '',
  confirmText: '确认',
  cancelText: '取消',
  danger: true,
})

let pending = null

export function askConfirm(options = {}) {
  const { title = '请确认', message = '', confirmText = '确认', cancelText = '取消', danger = true } = options
  confirmState.title = title
  confirmState.message = message
  confirmState.confirmText = confirmText
  confirmState.cancelText = cancelText
  confirmState.danger = danger
  confirmState.open = true

  if (pending) pending(false)
  return new Promise((resolve) => {
    pending = resolve
  })
}

export function settleConfirm(result) {
  confirmState.open = false
  const resolve = pending
  pending = null
  if (resolve) resolve(Boolean(result))
}
