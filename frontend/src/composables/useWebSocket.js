import { ref, onUnmounted } from 'vue'
import { useTaskStore } from '../stores/tasks.js'
import { useWorkerStore } from '../stores/workers.js'
import { useEventStore } from '../stores/events.js'

let ws = null
let reconnectTimer = null
const connected = ref(false)

export function useWebSocket() {
  if (ws && ws.readyState <= 1) {
    // Already connected or connecting
    return { connected }
  }

  function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${location.host}/ws`)

    ws.onopen = () => {
      connected.value = true
      console.log('[WS] Connected')
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleMessage(message)
      } catch (e) {
        console.error('[WS] Failed to parse message', e)
      }
    }

    ws.onclose = () => {
      connected.value = false
      console.log('[WS] Disconnected, reconnecting in 3s...')
      reconnectTimer = setTimeout(connect, 3000)
    }

    ws.onerror = (err) => {
      console.error('[WS] Error', err)
      ws.close()
    }
  }

  function handleMessage(message) {
    const taskStore = useTaskStore()
    const workerStore = useWorkerStore()
    const eventStore = useEventStore()

    if (message.type === 'task_update') {
      taskStore.handleTaskUpdate(message.data)
      eventStore.addEvent(message)
    } else if (message.type === 'worker_update') {
      workerStore.handleWorkerUpdate(message.data)
      eventStore.addEvent(message)
    }
  }

  function subscribe(filters) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ subscribe: filters }))
    }
  }

  connect()

  return { connected, subscribe }
}
