<script setup>
import { ref, computed, onMounted } from 'vue'
import { useEventStore } from '../stores/events.js'
import { useApi } from '../composables/useApi.js'

const eventStore = useEventStore()
const api = useApi()

const filterType = ref('')
const historicalEvents = ref([])
const showHistorical = ref(false)

const filteredLiveEvents = computed(() => {
  if (!filterType.value) return eventStore.events
  return eventStore.events.filter((e) => {
    const eventType = e.data?.event_type || e.type || ''
    return eventType.includes(filterType.value)
  })
})

async function loadHistorical() {
  try {
    const params = { limit: 200 }
    if (filterType.value) params.event_type = filterType.value
    historicalEvents.value = await api.getEvents(params)
    showHistorical.value = true
  } catch (e) {
    console.error('Failed to load historical events', e)
  }
}

function formatTimestamp(dt) {
  if (!dt) return '--'
  return new Date(dt).toLocaleTimeString()
}

function eventLabel(event) {
  const type = event.data?.event_type || event.type || 'unknown'
  const name = event.data?.name || event.data?.hostname || ''
  const uuid = event.data?.uuid ? event.data.uuid.slice(0, 8) : ''
  return `${type} ${name} ${uuid}`.trim()
}

function eventColor(event) {
  const type = event.data?.event_type || event.type || ''
  if (type.includes('failed')) return 'text-error'
  if (type.includes('succeeded')) return 'text-success'
  if (type.includes('started')) return 'text-primary'
  if (type.includes('retried') || type.includes('retry')) return 'text-warning'
  if (type.includes('worker')) return 'text-info'
  return ''
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Event Stream</h1>
      <div class="flex gap-2">
        <select v-model="filterType" class="select select-bordered select-sm">
          <option value="">All events</option>
          <option value="task-sent">task-sent</option>
          <option value="task-received">task-received</option>
          <option value="task-started">task-started</option>
          <option value="task-succeeded">task-succeeded</option>
          <option value="task-failed">task-failed</option>
          <option value="task-retried">task-retried</option>
          <option value="task-revoked">task-revoked</option>
          <option value="worker-online">worker-online</option>
          <option value="worker-offline">worker-offline</option>
          <option value="worker-heartbeat">worker-heartbeat</option>
        </select>
        <button class="btn btn-ghost btn-sm" @click="loadHistorical">Load History</button>
        <button class="btn btn-ghost btn-sm" @click="eventStore.clear()">Clear</button>
      </div>
    </div>

    <!-- Live events -->
    <div class="bg-base-100 rounded-box shadow p-4">
      <h2 class="text-sm font-semibold mb-3 opacity-70">
        Live Events ({{ filteredLiveEvents.length }})
      </h2>
      <div v-if="filteredLiveEvents.length === 0" class="text-center py-8 text-base-content/50">
        Waiting for events...
      </div>
      <div v-else class="space-y-1 max-h-96 overflow-y-auto font-mono text-sm">
        <div
          v-for="(evt, i) in filteredLiveEvents.slice(0, 200)"
          :key="i"
          class="flex gap-3 py-1 border-b border-base-200"
        >
          <span class="opacity-50 w-20 shrink-0">{{ formatTimestamp(evt._received_at) }}</span>
          <span :class="eventColor(evt)">{{ eventLabel(evt) }}</span>
        </div>
      </div>
    </div>

    <!-- Historical events -->
    <div v-if="showHistorical" class="bg-base-100 rounded-box shadow p-4 mt-6">
      <h2 class="text-sm font-semibold mb-3 opacity-70">
        Historical Events ({{ historicalEvents.length }})
      </h2>
      <div class="space-y-1 max-h-96 overflow-y-auto font-mono text-sm">
        <div
          v-for="evt in historicalEvents"
          :key="evt.id"
          class="flex gap-3 py-1 border-b border-base-200"
        >
          <span class="opacity-50 w-20 shrink-0">{{ formatTimestamp(evt.timestamp) }}</span>
          <span>{{ evt.event_type }}</span>
          <router-link
            :to="`/tasks/${evt.task_uuid}`"
            class="link link-primary text-xs"
          >
            {{ evt.task_uuid.slice(0, 8) }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
