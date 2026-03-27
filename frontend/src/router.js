import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from './views/Dashboard.vue'
import TaskExplorer from './views/TaskExplorer.vue'
import TaskDetail from './views/TaskDetail.vue'
import Workers from './views/Workers.vue'
import TaskTypes from './views/TaskTypes.vue'
import EventStream from './views/EventStream.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/tasks', name: 'tasks', component: TaskExplorer },
  { path: '/tasks/:id', name: 'task-detail', component: TaskDetail },
  { path: '/workers', name: 'workers', component: Workers },
  { path: '/task-types', name: 'task-types', component: TaskTypes },
  { path: '/events', name: 'events', component: EventStream },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
