import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 8340,
    host: 'localhost',
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  define: {
    'import.meta.env.VITE_WS_PORT': JSON.stringify('8340'),
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
