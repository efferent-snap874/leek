import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://leek:8585',
      '/ws': {
        target: 'ws://leek:8585',
        ws: true,
      },
    },
  },
})
