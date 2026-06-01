import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 将以 /api 开头的请求转发到 FastAPI 后端
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // 不需要 rewrite，后端已添加 /api 前缀
      },
    },
  },
})
