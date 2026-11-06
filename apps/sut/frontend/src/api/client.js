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

async function fetchOnce(url, options, timeoutMs = TIMEOUT_MS) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
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
  const isForm = typeof FormData !== 'undefined' && options.formData instanceof FormData
  if (options.body !== undefined && !isForm) headers['Content-Type'] = 'application/json'

  const init = {
    method,
    headers,
    body: isForm
      ? options.formData
      : options.body !== undefined
        ? JSON.stringify(options.body)
        : undefined,
  }
  const timeoutMs = options.timeoutMs || TIMEOUT_MS

  let response
  try {
    response = await fetchOnce(`${API_BASE}${path}`, init, timeoutMs)
  } catch (error) {
    if (method === 'GET') {
      try {
        response = await fetchOnce(`${API_BASE}${path}`, init, timeoutMs)
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
  platformCase: (id) => request(`/api/platform/cases/${id}`),
  updatePlatformCase: (id, payload) =>
    request(`/api/platform/cases/${id}`, { method: 'PATCH', body: payload }),
  deletePlatformCase: (id) => request(`/api/platform/cases/${id}`, { method: 'DELETE' }),
  batchPlatformCases: (payload) =>
    request('/api/platform/cases/batch', { method: 'POST', body: payload }),
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

  platformModels: (kind = '') =>
    request(`/api/platform/models${kind ? `?kind=${encodeURIComponent(kind)}` : ''}`),
  createPlatformModel: (payload) =>
    request('/api/platform/models', { method: 'POST', body: payload }),
  updatePlatformModel: (id, payload) =>
    request(`/api/platform/models/${id}`, { method: 'PATCH', body: payload }),
  testPlatformModel: (id) =>
    request(`/api/platform/models/${id}/test`, { method: 'POST' }),
  platformModelCalls: (limit = 20) => request(`/api/platform/model-calls?limit=${limit}`),

  // Pluggable skills (Phase 0): every new test capability is a skill.
  platformSkills: (category) =>
    request(`/api/platform/skills${category ? `?category=${encodeURIComponent(category)}` : ''}`),
  platformSkill: (id) => request(`/api/platform/skills/${encodeURIComponent(id)}`),
  runPlatformSkill: (id, payload = {}) =>
    request(`/api/platform/skills/${encodeURIComponent(id)}/run`, { method: 'POST', body: payload }),

  // Requirement management (Phase 1)
  platformRequirements: (projectId) =>
    request(`/api/platform/requirements${projectId ? `?project_id=${projectId}` : ''}`),
  createPlatformRequirement: (payload) =>
    request('/api/platform/requirements', { method: 'POST', body: payload }),
  platformRequirement: (id) => request(`/api/platform/requirements/${id}`),
  updatePlatformRequirement: (id, payload) =>
    request(`/api/platform/requirements/${id}`, { method: 'PATCH', body: payload }),
  deletePlatformRequirement: (id) =>
    request(`/api/platform/requirements/${id}`, { method: 'DELETE' }),
  uploadRequirementAttachment: (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request(`/api/platform/requirements/${id}/attachments`, {
      method: 'POST',
      formData,
      timeoutMs: 60000,
    })
  },
  deleteRequirementAttachment: (id, attachmentId) =>
    request(`/api/platform/requirements/${id}/attachments/${attachmentId}`, { method: 'DELETE' }),
  analyzeRequirement: (id) =>
    request(`/api/platform/requirements/${id}/analyze`, {
      method: 'POST',
      body: {},
      timeoutMs: 150000,
    }),
  planRequirement: (id, payload = {}) =>
    request(`/api/platform/requirements/${id}/plan`, {
      method: 'POST',
      body: payload,
      timeoutMs: 150000,
    }),
  chatRequirement: (id, message) =>
    request(`/api/platform/requirements/${id}/chat`, {
      method: 'POST',
      body: { message },
      timeoutMs: 150000,
    }),
  requirementAttachmentUrl: (id, attachmentId) =>
    `${API_BASE}/api/platform/requirements/${id}/attachments/${attachmentId}/download`,

  // Knowledge base (Phase 3)
  knowledgeBases: (projectId) =>
    request(`/api/platform/knowledge-bases${projectId ? `?project_id=${projectId}` : ''}`),
  createKnowledgeBase: (payload) =>
    request('/api/platform/knowledge-bases', { method: 'POST', body: payload }),
  knowledgeBase: (id) => request(`/api/platform/knowledge-bases/${id}`),
  updateKnowledgeBase: (id, payload) =>
    request(`/api/platform/knowledge-bases/${id}`, { method: 'PATCH', body: payload }),
  deleteKnowledgeBase: (id) =>
    request(`/api/platform/knowledge-bases/${id}`, { method: 'DELETE' }),
  knowledgeDocuments: (kbId) =>
    request(`/api/platform/knowledge-bases/${kbId}/documents`),
  addKnowledgeText: (kbId, payload) =>
    request(`/api/platform/knowledge-bases/${kbId}/documents/text`, {
      method: 'POST',
      body: payload,
    }),
  uploadKnowledgeDocument: (kbId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request(`/api/platform/knowledge-bases/${kbId}/documents`, {
      method: 'POST',
      formData,
      timeoutMs: 60000,
    })
  },
  deleteKnowledgeDocument: (documentId) =>
    request(`/api/platform/knowledge-documents/${documentId}`, { method: 'DELETE' }),
  knowledgeChunks: (documentId, offset = 0, limit = 50) =>
    request(`/api/platform/knowledge-documents/${documentId}/chunks?offset=${offset}&limit=${limit}`),
  searchKnowledgeBase: (kbId, payload) =>
    request(`/api/platform/knowledge-bases/${kbId}/search`, { method: 'POST', body: payload }),

  // 接口自动化
  apiAssets: (projectId) => request(`/api/platform/api-assets?project_id=${projectId}`),
  importApiSpec: (payload) =>
    request('/api/platform/api-assets/import', { method: 'POST', body: payload }),
  deleteApiAsset: (id) => request(`/api/platform/api-assets/${id}`, { method: 'DELETE' }),
  apiEndpoints: (projectId, filters = {}) => {
    const params = new URLSearchParams({ project_id: String(projectId) })
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) params.set(key, String(value))
    })
    return request(`/api/platform/api-endpoints?${params.toString()}`)
  },
  apiModules: (projectId) =>
    request(`/api/platform/api-endpoints/modules?project_id=${projectId}`),
  createApiEndpoint: (payload) =>
    request('/api/platform/api-endpoints', { method: 'POST', body: payload }),
  updateApiEndpoint: (id, payload) =>
    request(`/api/platform/api-endpoints/${id}`, { method: 'PATCH', body: payload }),
  deleteApiEndpoint: (id) =>
    request(`/api/platform/api-endpoints/${id}`, { method: 'DELETE' }),
  debugApiEndpoint: (id, payload) =>
    request(`/api/platform/api-endpoints/${id}/debug`, {
      method: 'POST',
      body: payload,
      timeoutMs: 60000,
    }),
  apiCases: (projectId, filters = {}) => {
    const params = new URLSearchParams({ project_id: String(projectId) })
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) params.set(key, String(value))
    })
    return request(`/api/platform/api-cases?${params.toString()}`)
  },
  createApiCase: (payload) =>
    request('/api/platform/api-cases', { method: 'POST', body: payload }),
  updateApiCase: (id, payload) =>
    request(`/api/platform/api-cases/${id}`, { method: 'PATCH', body: payload }),
  deleteApiCase: (id) => request(`/api/platform/api-cases/${id}`, { method: 'DELETE' }),
  runApiCase: (id) =>
    request(`/api/platform/api-cases/${id}/run`, { method: 'POST', timeoutMs: 120000 }),
  generateApiCases: (payload) =>
    request('/api/platform/api-cases/generate', {
      method: 'POST',
      body: payload,
      timeoutMs: 180000,
    }),
  generateApiScenario: (payload) =>
    request('/api/platform/api-cases/generate-scenario', {
      method: 'POST',
      body: payload,
      timeoutMs: 180000,
    }),
  apiRuns: (projectId, limit = 50) =>
    request(`/api/platform/api-runs?project_id=${projectId}&limit=${limit}`),
  apiRun: (id) => request(`/api/platform/api-runs/${id}`),
  diagnoseApiRun: (id) =>
    request(`/api/platform/api-runs/${id}/diagnose`, { method: 'POST', timeoutMs: 120000 }),
  uiCases: (projectId, status = '') => {
    const params = new URLSearchParams({ project_id: String(projectId) })
    if (status) params.set('status', status)
    return request(`/api/platform/ui-cases?${params.toString()}`)
  },
  createUiCase: (payload) =>
    request('/api/platform/ui-cases', { method: 'POST', body: payload }),
  uiCase: (id) => request(`/api/platform/ui-cases/${id}`),
  updateUiCase: (id, payload) =>
    request(`/api/platform/ui-cases/${id}`, { method: 'PATCH', body: payload }),
  deleteUiCase: (id) => request(`/api/platform/ui-cases/${id}`, { method: 'DELETE' }),
  uiCaseScript: (id) => request(`/api/platform/ui-cases/${id}/script`),
  runUiCase: (id) =>
    request(`/api/platform/ui-cases/${id}/run`, { method: 'POST', timeoutMs: 180000 }),
  uiRuns: (projectId, limit = 30) =>
    request(`/api/platform/ui-runs?project_id=${projectId}&limit=${limit}`),
  uiRun: (id) => request(`/api/platform/ui-runs/${id}`),
  uiRunScreenshotUrl: (id) => `${API_BASE}/api/platform/ui-runs/${id}/screenshot`,
  exploreUi: (payload) =>
    request('/api/platform/ui-explore', { method: 'POST', body: payload, timeoutMs: 240000 }),
  uiChat: (payload) =>
    request('/api/platform/ui-chat', { method: 'POST', body: payload, timeoutMs: 150000 }),
  projectModules: (projectId) =>
    request(`/api/platform/modules?project_id=${projectId}`),
  createProjectModule: (payload) =>
    request('/api/platform/modules', { method: 'POST', body: payload }),
  updateProjectModule: (id, payload) =>
    request(`/api/platform/modules/${id}`, { method: 'PATCH', body: payload }),
  deleteProjectModule: (id) => request(`/api/platform/modules/${id}`, { method: 'DELETE' }),
  projectMembers: (projectId) =>
    request(`/api/platform/members?project_id=${projectId}`),
  createProjectMember: (payload) =>
    request('/api/platform/members', { method: 'POST', body: payload }),
  updateProjectMember: (id, payload) =>
    request(`/api/platform/members/${id}`, { method: 'PATCH', body: payload }),
  deleteProjectMember: (id) => request(`/api/platform/members/${id}`, { method: 'DELETE' }),
  platformUsers: () => request('/api/platform/users'),
  createPlatformUser: (payload) => request('/api/platform/users', { method: 'POST', body: payload }),
  updatePlatformUser: (id, payload) =>
    request(`/api/platform/users/${id}`, { method: 'PATCH', body: payload }),
  deletePlatformUser: (id) => request(`/api/platform/users/${id}`, { method: 'DELETE' }),
  environments: (projectId) =>
    request(`/api/platform/environments${projectId ? `?project_id=${projectId}` : ''}`),
  createEnvironment: (payload) =>
    request('/api/platform/environments', { method: 'POST', body: payload }),
  updateEnvironment: (id, payload) =>
    request(`/api/platform/environments/${id}`, { method: 'PATCH', body: payload }),
  deleteEnvironment: (id) => request(`/api/platform/environments/${id}`, { method: 'DELETE' }),
}
