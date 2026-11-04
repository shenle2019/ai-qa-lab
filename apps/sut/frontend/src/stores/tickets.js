import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useTicketStore = defineStore('tickets', {
  state: () => ({
    items: [],
    loading: false,
    error: '',
    lastLoaded: null,
  }),
  getters: {
    counts: (state) => {
      const counts = { open: 0, in_progress: 0, closed: 0, total: state.items.length }
      for (const ticket of state.items) {
        if (counts[ticket.status] !== undefined) counts[ticket.status] += 1
      }
      return counts
    },
    highPriority: (state) =>
      state.items.filter((ticket) => ticket.priority === 'high' && ticket.status !== 'closed').length,
  },
  actions: {
    async fetchAll() {
      this.loading = true
      this.error = ''
      try {
        this.items = await api.listTickets()
        this.lastLoaded = new Date()
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    async create(payload) {
      const created = await api.createTicket(payload)
      this.items.unshift(created)
      return created
    },
    async update(id, payload) {
      const updated = await api.updateTicket(id, payload)
      const index = this.items.findIndex((ticket) => ticket.id === id)
      if (index >= 0) this.items[index] = updated
      return updated
    },
    async remove(id) {
      await api.deleteTicket(id)
      this.items = this.items.filter((ticket) => ticket.id !== id)
    },
  },
})
