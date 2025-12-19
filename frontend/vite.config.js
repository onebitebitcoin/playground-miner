import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 6173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:6273',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:6273',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      input: {
        main: './index.html'
      }
    }
  }
})
