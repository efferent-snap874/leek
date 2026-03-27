<script setup>
import { useWebSocket } from './composables/useWebSocket.js'

// Connect WebSocket on app mount
useWebSocket()
</script>

<template>
  <div class="flex h-screen">
    <!-- Sidebar -->
    <aside class="w-56 bg-base-300 flex flex-col p-4 gap-1">
      <div class="text-2xl font-bold mb-6 px-2 text-primary">leek</div>
      <router-link
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="btn btn-ghost btn-sm justify-start gap-2"
        active-class="btn-active"
      >
        <span>{{ item.icon }}</span>
        {{ item.label }}
      </router-link>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto p-6">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  data() {
    return {
      nav: [
        { to: '/', icon: '\u25A3', label: 'Dashboard' },
        { to: '/tasks', icon: '\u2630', label: 'Tasks' },
        { to: '/task-types', icon: '\u2261', label: 'Task Types' },
        { to: '/workers', icon: '\u2699', label: 'Workers' },
        { to: '/events', icon: '\u21C5', label: 'Events' },
      ],
    }
  },
}
</script>
