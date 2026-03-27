const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export function useApi() {
  return {
    // Dashboard
    getDashboardStats: () => request('/stats/dashboard'),
    getThroughput: (minutes = 60) => request(`/stats/throughput?minutes=${minutes}`),

    // Tasks
    getTasks: (params = {}) => {
      const qs = new URLSearchParams(params).toString()
      return request(`/tasks?${qs}`)
    },
    getTaskNames: () => request('/tasks/names'),
    getTask: (id) => request(`/tasks/${id}`),
    getTaskEvents: (id) => request(`/tasks/${id}/events`),
    revokeTask: (id, terminate = false) =>
      request(`/tasks/${id}/revoke?terminate=${terminate}`, { method: 'POST' }),

    // Workers
    getWorkers: () => request('/workers'),
    getWorker: (hostname) => request(`/workers/${encodeURIComponent(hostname)}`),
    getWorkerTasks: (hostname) =>
      request(`/workers/${encodeURIComponent(hostname)}/tasks`),
    pingWorkers: () => request('/workers/ping', { method: 'POST' }),

    // Events
    getEvents: (params = {}) => {
      const qs = new URLSearchParams(params).toString()
      return request(`/events?${qs}`)
    },

    // Task types
    getTaskTypeStats: () => request('/stats/task-types'),

    // Health
    getHealth: () => request('/health'),
  }
}
