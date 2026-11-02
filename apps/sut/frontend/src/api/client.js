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
  queryKnowledge: (payload) =>
    request('/api/kb/query', { method: 'POST', body: JSON.stringify(payload) }),
}
