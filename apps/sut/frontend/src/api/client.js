async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })

  if (!response.ok) {
    let detail
    try {
      const body = await response.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body)
    } catch {
      detail = `${response.status} ${response.statusText}`
    }
    throw new Error(detail)
  }

  return response.status === 204 ? null : response.json()
}

export const api = {
  health: () => request('/health'),
  listTickets: () => request('/api/tickets'),
  createTicket: (payload) =>
    request('/api/tickets', { method: 'POST', body: JSON.stringify(payload) }),
  updateTicket: (id, payload) =>
    request(`/api/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteTicket: (id) => request(`/api/tickets/${id}`, { method: 'DELETE' }),
  queryKnowledge: (payload) =>
    request('/api/kb/query', { method: 'POST', body: JSON.stringify(payload) }),

  platformSummary: () => request('/api/platform/summary'),
  platformProjects: () => request('/api/platform/projects'),
  createPlatformProject: (payload) =>
    request('/api/platform/projects', { method: 'POST', body: JSON.stringify(payload) }),
  platformCases: () => request('/api/platform/cases'),
  createPlatformCase: (payload) =>
    request('/api/platform/cases', { method: 'POST', body: JSON.stringify(payload) }),
  platformPlans: () => request('/api/platform/plans'),
  createPlatformPlan: (payload) =>
    request('/api/platform/plans', { method: 'POST', body: JSON.stringify(payload) }),
  platformExecutions: () => request('/api/platform/executions'),
  platformDefects: () => request('/api/platform/defects'),
  createPlatformDefect: (payload) =>
    request('/api/platform/defects', { method: 'POST', body: JSON.stringify(payload) }),
  updatePlatformDefect: (id, payload) =>
    request(`/api/platform/defects/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  seedPlatform: () => request('/api/platform/seed', { method: 'POST' }),

  platformModels: () => request('/api/platform/models'),
  createPlatformModel: (payload) =>
    request('/api/platform/models', { method: 'POST', body: JSON.stringify(payload) }),
  updatePlatformModel: (id, payload) =>
    request(`/api/platform/models/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  testPlatformModel: (id) =>
    request(`/api/platform/models/${id}/test`, { method: 'POST' }),
  platformModelCalls: (limit = 20) => request(`/api/platform/model-calls?limit=${limit}`),
}
