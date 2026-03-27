<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useWorkerStore } from '../stores/workers.js'

const api = useApi()
const workerStore = useWorkerStore()

const workers = ref([])
const loading = ref(true)
const pinging = ref(false)
let pollInterval = null

async function fetchWorkers() {
  try {
    workers.value = await api.getWorkers()
    loading.value = false
  } catch (e) {
    console.error('Failed to fetch workers', e)
  }
}

async function pingAll() {
  pinging.value = true
  try {
    await api.pingWorkers()
    await fetchWorkers()
  } catch (e) {
    console.error('Failed to ping workers', e)
  }
  pinging.value = false
}

function formatTimestamp(dt) {
  if (!dt) return '--'
  return new Date(dt).toLocaleString()
}

function timeSince(dt) {
  if (!dt) return '--'
  const seconds = Math.floor((Date.now() - new Date(dt).getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  return `${Math.floor(seconds / 3600)}h ago`
}

onMounted(() => {
  fetchWorkers()
  pollInterval = setInterval(fetchWorkers, 10000)
})

onUnmounted(() => {
  clearInterval(pollInterval)
})
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Workers</h1>
      <button class="btn btn-primary btn-sm" :disabled="pinging" @click="pingAll">
        <span v-if="pinging" class="loading loading-spinner loading-xs"></span>
        Ping All
      </button>
    </div>

    <div v-if="loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="workers.length === 0" class="text-center py-12 text-base-content/50">
      No workers detected yet
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="w in workers"
        :key="w.hostname"
        class="bg-base-100 rounded-box shadow p-4"
      >
        <div class="flex justify-between items-start mb-3">
          <div>
            <h3 class="font-semibold">{{ w.hostname }}</h3>
            <span class="text-xs opacity-70">{{ w.sw_ident }} {{ w.sw_ver }} ({{ w.sw_sys }})</span>
          </div>
          <span
            class="badge"
            :class="w.status === 'online' ? 'badge-success' : 'badge-error'"
          >
            {{ w.status }}
          </span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <span class="opacity-70">PID</span><span>{{ w.pid || '--' }}</span>
          <span class="opacity-70">Active Tasks</span><span>{{ w.active_tasks }}</span>
          <span class="opacity-70">Processed</span><span>{{ w.processed }}</span>
          <span class="opacity-70">Heartbeat Freq</span><span>{{ w.freq ? `${w.freq}s` : '--' }}</span>
          <span class="opacity-70">Last Heartbeat</span><span>{{ timeSince(w.last_heartbeat) }}</span>
          <span class="opacity-70">First Seen</span><span>{{ formatTimestamp(w.first_seen) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
