<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useTaskStore } from '../stores/tasks.js'

const api = useApi()
const taskStore = useTaskStore()
const taskTypes = ref([])
const recentByType = ref({})
const loading = ref(true)
const search = ref('')
const viewMode = ref('cards')
let refreshInterval = null

const filtered = computed(() => {
  const base = mergedTaskTypes.value
  if (!search.value) return base
  const q = search.value.toLowerCase()
  return base.filter((tt) => tt.name.toLowerCase().includes(q))
})

// Merge API stats with live WS updates for real-time counters
const mergedTaskTypes = computed(() => {
  // Build live stats from the task store
  const liveStats = {}
  for (const task of taskStore.liveTasks.values()) {
    if (!task.name) continue
    if (!liveStats[task.name]) {
      liveStats[task.name] = { total: 0, success: 0, failure: 0 }
    }
    liveStats[task.name].total++
    if (task.state === 'SUCCESS') liveStats[task.name].success++
    if (task.state === 'FAILURE') liveStats[task.name].failure++
  }

  // Start from API data, overlay live deltas
  const result = taskTypes.value.map((tt) => {
    const live = liveStats[tt.name]
    if (!live) return tt
    return {
      ...tt,
      total_count: Math.max(tt.total_count, live.total),
      success_count: Math.max(tt.success_count, live.success),
      failure_count: Math.max(tt.failure_count, live.failure),
      failure_rate: Math.max(tt.total_count, live.total) > 0
        ? Math.max(tt.failure_count, live.failure) / Math.max(tt.total_count, live.total)
        : 0,
    }
  })

  // Add any new task types seen via WS but not yet in API data
  const known = new Set(taskTypes.value.map((tt) => tt.name))
  for (const [name, counts] of Object.entries(liveStats)) {
    if (!known.has(name)) {
      result.push({
        name,
        total_count: counts.total,
        success_count: counts.success,
        failure_count: counts.failure,
        failure_rate: counts.total > 0 ? counts.failure / counts.total : 0,
        avg_runtime: null,
        p95_runtime: null,
      })
    }
  }

  return result
})

// Update recent tasks for a type when we get a WS event for it
const liveTasksSize = computed(() => taskStore.liveTasks.size)
watch(liveTasksSize, () => {
  for (const task of taskStore.liveTasks.values()) {
    if (!task.name) continue
    const recent = recentByType.value[task.name]
    if (!recent) {
      recentByType.value[task.name] = [task]
      continue
    }
    const idx = recent.findIndex((t) => t.uuid === task.uuid)
    if (idx >= 0) {
      // Update existing entry in place
      recent[idx] = { ...recent[idx], ...task, last_updated: task.timestamp || recent[idx].last_updated }
    } else {
      // Prepend and cap at 5
      recent.unshift(task)
      if (recent.length > 5) recent.pop()
    }
  }
})

async function fetchTaskTypes() {
  try {
    taskTypes.value = await api.getTaskTypeStats()
    // Fetch 5 most recent tasks for each type in parallel
    const fetches = taskTypes.value.map(async (tt) => {
      try {
        const result = await api.getTasks({
          name: tt.name,
          page_size: 5,
          sort_by: 'last_updated',
          sort_order: 'desc',
        })
        recentByType.value[tt.name] = result.items
      } catch (e) {
        recentByType.value[tt.name] = []
      }
    })
    await Promise.all(fetches)
  } catch (e) {
    console.error('Failed to fetch task types', e)
  }
  loading.value = false
}

function formatDuration(seconds) {
  if (!seconds) return '--'
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`
  return `${seconds.toFixed(3)}s`
}

function formatRate(rate) {
  return `${(rate * 100).toFixed(1)}%`
}

function formatTime(dt) {
  if (!dt) return '--'
  return new Date(dt).toLocaleTimeString()
}

function stateBadge(state) {
  const map = {
    PENDING: 'badge-ghost',
    RECEIVED: 'badge-info',
    STARTED: 'badge-primary',
    SUCCESS: 'badge-success',
    FAILURE: 'badge-error',
    RETRY: 'badge-warning',
    REVOKED: 'badge-neutral',
    REJECTED: 'badge-neutral',
  }
  return map[state] || 'badge-ghost'
}

onMounted(() => {
  fetchTaskTypes()
  // Periodic full refresh for accurate aggregate stats (avg/p95 runtime)
  refreshInterval = setInterval(fetchTaskTypes, 15000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Task Types</h1>
      <div class="flex gap-2">
        <input
          v-model="search"
          type="text"
          placeholder="Filter task types..."
          class="input input-bordered input-sm w-64"
        />
        <div class="join">
          <button
            class="join-item btn btn-sm"
            :class="viewMode === 'cards' ? 'btn-active' : ''"
            @click="viewMode = 'cards'"
          >Cards</button>
          <button
            class="join-item btn btn-sm"
            :class="viewMode === 'list' ? 'btn-active' : ''"
            @click="viewMode = 'list'"
          >List</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="filtered.length === 0" class="text-center py-12 text-base-content/50">
      {{ taskTypes.length === 0 ? 'No task types recorded yet' : 'No matching task types' }}
    </div>

    <!-- Card view -->
    <div v-else-if="viewMode === 'cards'" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="tt in filtered"
        :key="tt.name"
        class="bg-base-100 rounded-box shadow p-4"
      >
        <div class="flex justify-between items-start mb-3">
          <h3 class="font-mono text-sm font-semibold break-all">{{ tt.name }}</h3>
          <span
            v-if="tt.failure_rate > 0.1"
            class="badge badge-error badge-sm"
          >{{ formatRate(tt.failure_rate) }} fail</span>
        </div>

        <!-- Stats row -->
        <div class="flex gap-4 text-sm mb-4">
          <div>
            <span class="opacity-50">Total</span>
            <span class="ml-1 font-semibold">{{ tt.total_count }}</span>
          </div>
          <div>
            <span class="opacity-50">OK</span>
            <span class="ml-1 text-success font-semibold">{{ tt.success_count }}</span>
          </div>
          <div>
            <span class="opacity-50">Fail</span>
            <span class="ml-1 text-error font-semibold">{{ tt.failure_count }}</span>
          </div>
          <div>
            <span class="opacity-50">Avg</span>
            <span class="ml-1">{{ formatDuration(tt.avg_runtime) }}</span>
          </div>
          <div>
            <span class="opacity-50">p95</span>
            <span class="ml-1">{{ formatDuration(tt.p95_runtime) }}</span>
          </div>
        </div>

        <!-- Recent tasks -->
        <div class="border-t border-base-content/10 pt-3">
          <div class="text-xs opacity-50 mb-2">Recent tasks</div>
          <div v-if="!recentByType[tt.name] || recentByType[tt.name].length === 0" class="text-xs opacity-30">
            No recent tasks
          </div>
          <div v-else class="space-y-1">
            <div
              v-for="task in recentByType[tt.name]"
              :key="task.uuid"
              class="flex items-center justify-between text-xs"
            >
              <div class="flex items-center gap-2">
                <span class="badge badge-xs" :class="stateBadge(task.state)">{{ task.state }}</span>
                <router-link :to="`/tasks/${task.uuid}`" class="link link-primary font-mono">
                  {{ task.uuid.slice(0, 8) }}
                </router-link>
              </div>
              <div class="flex items-center gap-3 opacity-60">
                <span>{{ task.runtime ? formatDuration(task.runtime) : '--' }}</span>
                <span>{{ formatTime(task.last_updated) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- List view -->
    <div v-else class="bg-base-100 rounded-box shadow overflow-x-auto">
      <table class="table">
        <thead>
          <tr>
            <th>Task Name</th>
            <th>Total</th>
            <th>Succeeded</th>
            <th>Failed</th>
            <th>Failure Rate</th>
            <th>Avg Runtime</th>
            <th>p95 Runtime</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tt in filtered" :key="tt.name" class="hover">
            <td class="font-mono text-sm">{{ tt.name }}</td>
            <td>{{ tt.total_count }}</td>
            <td class="text-success">{{ tt.success_count }}</td>
            <td class="text-error">{{ tt.failure_count }}</td>
            <td>
              <span :class="tt.failure_rate > 0.1 ? 'text-error font-bold' : ''">
                {{ formatRate(tt.failure_rate) }}
              </span>
            </td>
            <td>{{ formatDuration(tt.avg_runtime) }}</td>
            <td>{{ formatDuration(tt.p95_runtime) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
