<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useTaskStore } from '../stores/tasks.js'

const api = useApi()
const taskStore = useTaskStore()

const apiTasks = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(false)
let refreshInterval = null

// Filters
const stateFilter = ref('')
const nameFilter = ref('')
const searchQuery = ref('')
const sortBy = ref('last_updated')
const sortOrder = ref('desc')
const taskNames = ref([])

const states = ['PENDING', 'RECEIVED', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED', 'REJECTED']

// Merge API results with live WebSocket updates
const tasks = computed(() => {
  return apiTasks.value.map((task) => {
    const live = taskStore.liveTasks.get(task.uuid)
    if (live) {
      return {
        ...task,
        state: live.state || task.state,
        worker: live.worker || task.worker,
        runtime: live.runtime ?? task.runtime,
        last_updated: live.timestamp || task.last_updated,
      }
    }
    return task
  })
})

async function fetchTasks() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    }
    if (stateFilter.value) params.state = stateFilter.value
    if (nameFilter.value) params.name = nameFilter.value
    if (searchQuery.value) params.search = searchQuery.value

    const result = await api.getTasks(params)
    apiTasks.value = result.items
    total.value = result.total
  } catch (e) {
    console.error('Failed to fetch tasks', e)
  }
  loading.value = false
}

async function fetchTaskNames() {
  try {
    taskNames.value = await api.getTaskNames()
  } catch (e) {
    console.error('Failed to fetch task names', e)
  }
}

watch([stateFilter, nameFilter, searchQuery, sortBy, sortOrder], () => {
  page.value = 1
  fetchTasks()
})

watch(page, fetchTasks)

onMounted(() => {
  fetchTasks()
  fetchTaskNames()
  // Re-fetch periodically so new tasks appear and order stays fresh
  refreshInterval = setInterval(fetchTasks, 3000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
})

const totalPages = () => Math.ceil(total.value / pageSize.value)

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
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Tasks</h1>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search by name or UUID..."
        class="input input-bordered input-sm w-64"
      />
      <select v-model="stateFilter" class="select select-bordered select-sm">
        <option value="">All states</option>
        <option v-for="s in states" :key="s" :value="s">{{ s }}</option>
      </select>
      <select v-model="nameFilter" class="select select-bordered select-sm">
        <option value="">All task types</option>
        <option v-for="n in taskNames" :key="n" :value="n">{{ n }}</option>
      </select>
      <select v-model="sortBy" class="select select-bordered select-sm">
        <option value="last_updated">Last Updated</option>
        <option value="started_at">Started</option>
        <option value="runtime">Runtime</option>
        <option value="state">State</option>
      </select>
      <button class="btn btn-ghost btn-sm" @click="sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'">
        {{ sortOrder === 'desc' ? '\u2193' : '\u2191' }}
      </button>
    </div>

    <!-- Table -->
    <div class="bg-base-100 rounded-box shadow overflow-x-auto">
      <table class="table table-sm">
        <thead>
          <tr>
            <th>UUID</th>
            <th>Name</th>
            <th>State</th>
            <th>Worker</th>
            <th>Runtime</th>
            <th>Last Updated</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && apiTasks.length === 0">
            <td colspan="6" class="text-center py-8">
              <span class="loading loading-spinner loading-md"></span>
            </td>
          </tr>
          <tr v-else-if="tasks.length === 0">
            <td colspan="6" class="text-center py-8 text-base-content/50">No tasks found</td>
          </tr>
          <tr v-for="task in tasks" :key="task.uuid" class="hover">
            <td>
              <router-link :to="`/tasks/${task.uuid}`" class="link link-primary font-mono text-xs">
                {{ task.uuid.slice(0, 8) }}...
              </router-link>
            </td>
            <td>{{ task.name || '--' }}</td>
            <td>
              <span class="badge badge-sm" :class="stateBadge(task.state)">{{ task.state }}</span>
            </td>
            <td class="text-xs opacity-70">{{ task.worker || '--' }}</td>
            <td>{{ task.runtime ? `${task.runtime.toFixed(3)}s` : '--' }}</td>
            <td class="text-xs">{{ formatTime(task.last_updated) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex justify-between items-center mt-4" v-if="total > pageSize">
      <span class="text-sm opacity-70">{{ total }} tasks</span>
      <div class="join">
        <button class="join-item btn btn-sm" :disabled="page <= 1" @click="page--">Prev</button>
        <span class="join-item btn btn-sm btn-disabled">{{ page }} / {{ totalPages() }}</span>
        <button class="join-item btn btn-sm" :disabled="page >= totalPages()" @click="page++">Next</button>
      </div>
    </div>
  </div>
</template>
