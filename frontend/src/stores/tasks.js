import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTaskStore = defineStore('tasks', () => {
  // Live task updates from WebSocket — keyed by UUID for fast lookups
  const liveTasks = ref(new Map())

  function handleTaskUpdate(data) {
    const existing = liveTasks.value.get(data.uuid) || {}
    liveTasks.value.set(data.uuid, { ...existing, ...data })

    // Cap the live map at 5000 entries to prevent unbounded growth
    if (liveTasks.value.size > 5000) {
      const firstKey = liveTasks.value.keys().next().value
      liveTasks.value.delete(firstKey)
    }
  }

  function getRecentTasks(limit = 100) {
    return Array.from(liveTasks.value.values())
      .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
      .slice(0, limit)
  }

  function getStateCounts() {
    const counts = { PENDING: 0, RECEIVED: 0, STARTED: 0, SUCCESS: 0, FAILURE: 0, RETRY: 0, REVOKED: 0 }
    for (const task of liveTasks.value.values()) {
      if (task.state in counts) {
        counts[task.state]++
      }
    }
    return counts
  }

  return { liveTasks, handleTaskUpdate, getRecentTasks, getStateCounts }
})
