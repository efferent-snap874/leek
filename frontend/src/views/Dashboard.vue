<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useTaskStore } from '../stores/tasks.js'
import { useWorkerStore } from '../stores/workers.js'

const api = useApi()
const taskStore = useTaskStore()
const workerStore = useWorkerStore()

const stats = ref(null)
const throughput = ref([])
const loading = ref(true)
const eventsReceived = ref(false)
let pollInterval = null

const CHART_MINUTES = 60

const STATE_COLORS = {
  SUCCESS: '#36d399',   // green
  FAILURE: '#f87272',   // red
  STARTED: '#7480ff',   // primary/blue
  RETRY: '#fbbd23',     // warning/yellow
  RECEIVED: '#3abff8',  // info/cyan
  PENDING: '#a6adbb',   // ghost/gray
  REVOKED: '#6b7280',   // neutral
  REJECTED: '#6b7280',
}

// Stack order — bottom to top
const STACK_ORDER = ['SUCCESS', 'STARTED', 'RECEIVED', 'PENDING', 'RETRY', 'FAILURE', 'REVOKED', 'REJECTED']

// Pad throughput to always show 60 bars, right-aligned to current time
const paddedThroughput = computed(() => {
  const lookup = new Map()
  for (const p of throughput.value) {
    lookup.set(p.minute, p.states || {})
  }

  const now = new Date()
  const bars = []
  for (let i = CHART_MINUTES - 1; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 60000)
    const key = d.toISOString().slice(0, 16)
    const states = lookup.get(key) || {}
    const total = Object.values(states).reduce((a, b) => a + b, 0)
    bars.push({ minute: key, states, total })
  }
  return bars
})

const maxThroughput = computed(() =>
  Math.max(1, ...paddedThroughput.value.map((p) => p.total))
)

const hasData = computed(() =>
  paddedThroughput.value.some((p) => p.total > 0)
)

const recentTasks = computed(() => taskStore.getRecentTasks(20))

function formatMinute(minute) {
  if (!minute) return ''
  const parts = minute.split('T')
  return parts[1] || minute
}

function barSegments(bar) {
  if (bar.total === 0) return []
  return STACK_ORDER
    .filter((state) => bar.states[state])
    .map((state) => ({
      state,
      count: bar.states[state],
      pct: (bar.states[state] / maxThroughput.value) * 100,
      color: STATE_COLORS[state],
    }))
}

function tooltipText(bar) {
  if (bar.total === 0) return `${formatMinute(bar.minute)} — 0 tasks`
  const parts = STACK_ORDER
    .filter((s) => bar.states[s])
    .map((s) => `${s}: ${bar.states[s]}`)
  return `${formatMinute(bar.minute)} — ${bar.total} tasks\n${parts.join(', ')}`
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
  }
  return map[state] || 'badge-ghost'
}

async function fetchStats() {
  try {
    const [dashStats, tp] = await Promise.all([
      api.getDashboardStats(),
      api.getThroughput(60),
    ])
    stats.value = dashStats
    throughput.value = tp
    eventsReceived.value = dashStats.events_received
    loading.value = false
  } catch (e) {
    console.error('Failed to fetch dashboard stats', e)
  }
}

onMounted(() => {
  fetchStats()
  pollInterval = setInterval(fetchStats, 5000)
})

onUnmounted(() => {
  clearInterval(pollInterval)
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Dashboard</h1>

    <!-- No events warning -->
    <div v-if="!loading && !eventsReceived" class="alert alert-warning mb-6">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
      <div>
        <h3 class="font-bold">No events received yet</h3>
        <p class="text-sm">Make sure your Celery workers have events enabled: <code class="bg-base-300 px-1 rounded">celery -A app worker -E</code> or set <code class="bg-base-300 px-1 rounded">worker_send_task_events = True</code></p>
      </div>
    </div>

    <!-- Stats cards -->
    <div v-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Active Tasks</div>
        <div class="stat-value text-primary">{{ stats.active_tasks }}</div>
      </div>
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Succeeded</div>
        <div class="stat-value text-success">{{ stats.succeeded_tasks }}</div>
      </div>
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Failed</div>
        <div class="stat-value text-error">{{ stats.failed_tasks }}</div>
      </div>
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Tasks/min</div>
        <div class="stat-value">{{ stats.tasks_per_minute }}</div>
      </div>
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Workers Online</div>
        <div class="stat-value text-success">{{ stats.workers_online }}</div>
      </div>
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Workers Offline</div>
        <div class="stat-value text-warning">{{ stats.workers_offline }}</div>
      </div>
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Total Tasks</div>
        <div class="stat-value">{{ stats.total_tasks }}</div>
      </div>
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">WebSocket Clients</div>
        <div class="stat-value text-info">{{ workerStore.workerList.length > 0 ? 'Live' : '--' }}</div>
      </div>
    </div>

    <!-- Throughput chart -->
    <div class="bg-base-100 rounded-box shadow p-4 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Throughput (tasks/min)</h2>
        <!-- Legend -->
        <div class="flex gap-3 text-xs">
          <span class="flex items-center gap-1" v-for="s in ['SUCCESS', 'FAILURE', 'STARTED', 'RETRY']" :key="s">
            <span class="w-2.5 h-2.5 rounded-sm inline-block" :style="{ backgroundColor: STATE_COLORS[s] }"></span>
            {{ s }}
          </span>
        </div>
      </div>
      <div v-if="!hasData" class="text-base-content/50 text-center py-8">
        No throughput data yet
      </div>
      <div v-else class="flex">
        <!-- Y-axis labels -->
        <div class="flex flex-col justify-between items-end pr-2 text-xs opacity-50 h-40">
          <span>{{ maxThroughput }}</span>
          <span>{{ Math.round(maxThroughput / 2) }}</span>
          <span>0</span>
        </div>
        <!-- Chart area -->
        <div class="flex-1">
          <div class="flex items-end gap-px h-40 border-b border-l border-base-content/10">
            <div
              v-for="bar in paddedThroughput"
              :key="bar.minute"
              class="flex-1 min-w-0 flex flex-col justify-end h-full relative group"
            >
              <!-- Stacked segments -->
              <div
                v-for="seg in barSegments(bar)"
                :key="seg.state"
                class="w-full transition-all"
                :style="{ height: `${Math.max(seg.pct > 0 ? 1.5 : 0, seg.pct)}%`, backgroundColor: seg.color }"
              ></div>
              <!-- Tooltip -->
              <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block bg-base-300 text-xs rounded px-2 py-1 whitespace-pre z-10 shadow pointer-events-none">
                {{ tooltipText(bar) }}
              </div>
            </div>
          </div>
          <!-- X-axis labels -->
          <div class="flex justify-between text-xs opacity-50 mt-1 px-1">
            <span>{{ formatMinute(paddedThroughput[0]?.minute) }}</span>
            <span>{{ formatMinute(paddedThroughput[Math.floor(CHART_MINUTES / 2)]?.minute) }}</span>
            <span>{{ formatMinute(paddedThroughput[CHART_MINUTES - 1]?.minute) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent tasks from live feed -->
    <div class="bg-base-100 rounded-box shadow p-4">
      <h2 class="text-lg font-semibold mb-4">Recent Activity</h2>
      <div v-if="recentTasks.length === 0" class="text-base-content/50 text-center py-4">
        Waiting for events...
      </div>
      <table v-else class="table table-sm">
        <thead>
          <tr>
            <th>Task</th>
            <th>State</th>
            <th>Worker</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in recentTasks" :key="task.uuid">
            <td>
              <router-link :to="`/tasks/${task.uuid}`" class="link link-primary">
                {{ task.name || task.uuid.slice(0, 8) }}
              </router-link>
            </td>
            <td>
              <span class="badge badge-sm" :class="stateBadge(task.state)">{{ task.state }}</span>
            </td>
            <td class="text-xs opacity-70">{{ task.worker || '--' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
