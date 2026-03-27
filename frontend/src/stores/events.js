import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useEventStore = defineStore('events', () => {
  const events = ref([])
  const MAX_EVENTS = 500

  function addEvent(event) {
    events.value.unshift({
      ...event,
      _received_at: new Date().toISOString(),
    })
    if (events.value.length > MAX_EVENTS) {
      events.value = events.value.slice(0, MAX_EVENTS)
    }
  }

  function clear() {
    events.value = []
  }

  return { events, addEvent, clear }
})
