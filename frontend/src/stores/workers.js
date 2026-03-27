import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWorkerStore = defineStore('workers', () => {
  const workers = ref(new Map())

  function handleWorkerUpdate(data) {
    const existing = workers.value.get(data.hostname) || {}
    workers.value.set(data.hostname, { ...existing, ...data })
  }

  const workerList = computed(() =>
    Array.from(workers.value.values()).sort((a, b) =>
      a.hostname.localeCompare(b.hostname)
    )
  )

  const onlineCount = computed(
    () => workerList.value.filter((w) => w.status === 'online').length
  )

  const offlineCount = computed(
    () => workerList.value.filter((w) => w.status === 'offline').length
  )

  return { workers, workerList, onlineCount, offlineCount, handleWorkerUpdate }
})
