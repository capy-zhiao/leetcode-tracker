import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 开发时把 /api 请求转发到后端,前端代码里就不用写完整 URL,也没有跨域问题
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true,
                rewrite: (p) => p.replace(/^\/api/, '') },
    },
  },
})
