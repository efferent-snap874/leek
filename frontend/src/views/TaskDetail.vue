<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useApi } from '../composables/useApi.js'

const route = useRoute()
const api = useApi()

const task = ref(null)
const events = ref([])
const loading = ref(true)
const revoking = ref(false)

async function fetchTask() {
  try {
    const [t, e] = await Promise.all([
      api.getTask(route.params.id),
      api.getTaskEvents(route.params.id),
    ])
    task.value = t
    events.value = e
  } catch (e) {
    console.error('Failed to fetch task', e)
  }
  loading.value = false
}

async function revoke(terminate = false) {
  if (!confirm(`${terminate ? 'Terminate' : 'Revoke'} this task?`)) return
  revoking.value = true
  try {
    await api.revokeTask(route.params.id, terminate)
    await fetchTask()
  } catch (e) {
    console.error('Failed to revoke task', e)
  }
  revoking.value = false
}

function formatTimestamp(dt) {
  if (!dt) return '--'
  return new Date(dt).toLocaleString()
}

function formatDuration(seconds) {
  if (!seconds) return '--'
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`
  return `${seconds.toFixed(3)}s`
}

onMounted(fetchTask)
</script>

<template>
  <div>
    <div class="flex items-center gap-4 mb-6">
      <router-link to="/tasks" class="btn btn-ghost btn-sm">&larr; Tasks</router-link>
      <h1 class="text-2xl font-bold">Task Detail</h1>
    </div>

    <div v-if="loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="!task" class="alert alert-error">Task not found</div>

    <div v-else>
      <!-- Header -->
      <div class="bg-base-100 rounded-box shadow p-6 mb-6">
        <div class="flex justify-between items-start">
          <div>
            <h2 class="text-xl font-semibold">{{ task.name || 'Unknown Task' }}</h2>
            <p class="font-mono text-sm opacity-70 mt-1">{{ task.uuid }}</p>
          </div>
          <div class="flex gap-2">
            <span class="badge badge-lg" :class="stateBadge(task.state)">{{ task.state }}</span>
            <button
              v-if="task.state === 'STARTED'"
              class="btn btn-warning btn-sm"
              :disabled="revoking"
              @click="revoke(false)"
            >
              Revoke
            </button>
            <button
              v-if="task.state === 'STARTED'"
              class="btn btn-error btn-sm"
              :disabled="revoking"
              @click="revoke(true)"
            >
              Terminate
            </button>
          </div>
        </div>
      </div>

      <!-- Info grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div class="bg-base-100 rounded-box shadow p-4">
          <h3 class="font-semibold mb-3">Details</h3>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <span class="opacity-70">Worker</span><span>{{ task.worker || '--' }}</span>
            <span class="opacity-70">Queue</span><span>{{ task.queue || '--' }}</span>
            <span class="opacity-70">Runtime</span><span>{{ formatDuration(task.runtime) }}</span>
            <span class="opacity-70">Retries</span><span>{{ task.retries }}</span>
            <span class="opacity-70">Root ID</span>
            <span class="font-mono text-xs">{{ task.root_id || '--' }}</span>
            <span class="opacity-70">Parent ID</span>
            <span class="font-mono text-xs">{{ task.parent_id || '--' }}</span>
          </div>
        </div>

        <div class="bg-base-100 rounded-box shadow p-4">
          <h3 class="font-semibold mb-3">Timeline</h3>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <span class="opacity-70">Sent</span><span>{{ formatTimestamp(task.sent_at) }}</span>
            <span class="opacity-70">Received</span><span>{{ formatTimestamp(task.received_at) }}</span>
            <span class="opacity-70">Started</span><span>{{ formatTimestamp(task.started_at) }}</span>
            <span class="opacity-70">Succeeded</span><span>{{ formatTimestamp(task.succeeded_at) }}</span>
            <span class="opacity-70">Failed</span><span>{{ formatTimestamp(task.failed_at) }}</span>
            <span class="opacity-70">Revoked</span><span>{{ formatTimestamp(task.revoked_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Arguments -->
      <div v-if="task.args || task.kwargs" class="bg-base-100 rounded-box shadow p-4 mb-6">
        <h3 class="font-semibold mb-3">Arguments</h3>
        <div v-if="task.args" class="mb-2">
          <span class="text-sm opacity-70">args: </span>
          <code class="text-sm bg-base-300 px-2 py-1 rounded">{{ task.args }}</code>
        </div>
        <div v-if="task.kwargs">
          <span class="text-sm opacity-70">kwargs: </span>
          <code class="text-sm bg-base-300 px-2 py-1 rounded">{{ task.kwargs }}</code>
        </div>
      </div>

      <!-- Result or Exception -->
      <div v-if="task.result" class="bg-base-100 rounded-box shadow p-4 mb-6">
        <h3 class="font-semibold mb-3">Result</h3>
        <pre class="text-sm bg-base-300 p-3 rounded overflow-x-auto">{{ task.result }}</pre>
      </div>

      <div v-if="task.exception" class="bg-base-100 rounded-box shadow p-4 mb-6">
        <h3 class="font-semibold mb-3 text-error">Exception</h3>
        <pre class="text-sm bg-base-300 p-3 rounded overflow-x-auto text-error">{{ task.exception }}</pre>
        <pre v-if="task.traceback" class="text-xs bg-base-300 p-3 rounded overflow-x-auto mt-2 opacity-80">{{ task.traceback }}</pre>
      </div>

      <!-- Event history -->
      <div class="bg-base-100 rounded-box shadow p-4">
        <h3 class="font-semibold mb-3">Event History</h3>
        <div v-if="events.length === 0" class="text-base-content/50 text-center py-4">No events recorded</div>
        <ul v-else class="timeline timeline-vertical timeline-compact">
          <li v-for="(evt, i) in events" :key="evt.id">
            <div class="timeline-start text-xs opacity-70">{{ formatTimestamp(evt.timestamp) }}</div>
            <div class="timeline-middle">
              <div class="w-3 h-3 rounded-full" :class="eventDot(evt.event_type)"></div>
            </div>
            <div class="timeline-end text-sm">{{ evt.event_type }}</div>
            <hr v-if="i < events.length - 1" />
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    stateBadge(state) {
      const map = {
        PENDING: 'badge-ghost', RECEIVED: 'badge-info', STARTED: 'badge-primary',
        SUCCESS: 'badge-success', FAILURE: 'badge-error', RETRY: 'badge-warning',
        REVOKED: 'badge-neutral', REJECTED: 'badge-neutral',
      }
      return map[state] || 'badge-ghost'
    },
    eventDot(type) {
      if (type.includes('succeeded')) return 'bg-success'
      if (type.includes('failed')) return 'bg-error'
      if (type.includes('started')) return 'bg-primary'
      if (type.includes('retried')) return 'bg-warning'
      if (type.includes('revoked')) return 'bg-neutral'
      return 'bg-info'
    },
  },
}
</script>
