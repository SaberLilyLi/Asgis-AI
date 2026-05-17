import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 配置保持轻量，开发时通过环境变量覆盖后端地址。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
  },
})

