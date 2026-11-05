const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
const KEY_STORAGE = 'sut_api_key'
const TIMEOUT_MS = 15000

const ERROR_TEXT = {
  400: '请求参数不合法',
  401: '访问密钥无效或未填写，请到左侧“访问密钥”页面保存后重试',
  403: '没有权限执行该操作',
  404: '请求的资源不存在',
  409: '数据冲突，请刷新后重试',
  422: '参数校验失败，请检查输入',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  502: '上游服务不可用',
  503: '服务暂时不可用',
}

export function getApiKey() {
  return localStorage.getItem(KEY_STORAGE) || ''
}

export function setApiKey(value) {
  if (value) localStorage.setItem(KEY_STORAGE, value)
  else localStorage.removeItem(KEY_STORAGE)
}

export function clearApiKey() {
  localStorage.removeItem(KEY_STORAGE)
}

async function fetchOnce(url, options) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    return await fetch(url, { ...options, signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
}

async function request(path, options = {}) {
  const method = options.method || 'GET'
  const headers = { ...(options.headers || {}) }
  const key = getApiKey()
  if (key) headers.Authorization = `Bearer ${key}`
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  const init = {
    method,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  }

  let response
  try {
    response = await fetchOnce(`${API_BASE}${path}`, init)
  } catch (error) {
    if (method === 'GET') {
      try {
        response = await fetchOnce(`${API_BASE}${path}`, init)
      } catch {
        throw new Error('网络请求失败，请检查网络或服务状态')
      }
    } else {
      throw new Error(error.name === 'AbortError' ? '请求超时，请稍后重试' : '网络请求失败，请检查网络或服务状态')
    }
  }

  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body)
    } catch {
      detail = ''
    }
    // Keep the user on the current page so form input survives a 401. A wrong
    // key is cleared here; the caller shows the message inline.
    if (response.status === 401) clearApiKey()
    throw new Error(ERROR_TEXT[response.status] || detail || `${response.status} ${response.statusText}`)
  }

  return response.status === 204 ? null : response.json()
}

export const api = {
  health: () => request('/health'),
  ready: () => request('/ready'),
  verifyKey: () => request('/api/auth/verify', { method: 'POST', body: {} }),
  listTickets: () => request('/api/tickets'),
  createTicket: (payload) => request('/api/tickets', { method: 'POST', body: payload }),
  updateTicket: (id, payload) =>
    request(`/api/tickets/${id}`, { method: 'PATCH', body: payload }),
  deleteTicket: (id) => request(`/api/tickets/${id}`, { method: 'DELETE' }),
  queryKnowledge: (payload) =>
    request('/api/kb/query', { method: 'POST', body: payload }),

  platformSummary: () => request('/api/platform/summary'),
  platformProjects: () => request('/api/platform/projects'),
  createPlatformProject: (payload) =>
    request('/api/platform/projects', { method: 'POST', body: payload }),
  platformCases: () => request('/api/platform/cases'),
  createPlatformCase: (payload) =>
    request('/api/platform/cases', { method: 'POST', body: payload }),
  generatePlatformCases: (payload) =>
    request('/api/platform/generate-cases', { method: 'POST', body: payload }),
  submitPlatformCase: (id) =>
    request(`/api/platform/cases/${id}/submit-review`, { method: 'POST' }),
  reviewPlatformCase: (id, payload) =>
    request(`/api/platform/cases/${id}/review`, { method: 'POST', body: payload }),
  platformPlans: () => request('/api/platform/plans'),
  createPlatformPlan: (payload) =>
    request('/api/platform/plans', { method: 'POST', body: payload }),
  executePlatformPlan: (id, payload = {}) =>
    request(`/api/platform/plans/${id}/execute`, { method: 'POST', body: payload }),
  platformExecutions: () => request('/api/platform/executions'),
  platformExecution: (id) => request(`/api/platform/executions/${id}`),
  platformDefects: () => request('/api/platform/defects'),
  createPlatformDefect: (payload) =>
    request('/api/platform/defects', { method: 'POST', body: payload }),
  updatePlatformDefect: (id, payload) =>
    request(`/api/platform/defects/${id}`, { method: 'PATCH', body: payload }),
  seedPlatform: () => request('/api/platform/seed', { method: 'POST' }),

  platformModels: () => request('/api/platform/models'),
  createPlatformModel: (payload) =>
    request('/api/platform/models', { method: 'POST', body: payload }),
  updatePlatformModel: (id, payload) =>
    request(`/api/platform/models/${id}`, { method: 'PATCH', body: payload }),
  testPlatformModel: (id) =>
    request(`/api/platform/models/${id}/test`, { method: 'POST' }),
  platformModelCalls: (limit = 20) => request(`/api/platform/model-calls?limit=${limit}`),
}
