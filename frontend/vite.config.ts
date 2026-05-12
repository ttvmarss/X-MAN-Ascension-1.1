import { defineConfig } from 'vite'

/**
 * Dev mode: Vite on port 8340 proxies WebSocket + API to backend on 8000.
 * Production: run `npm run build`, then `python server.py` serves dist/ directly.
 */
export default defineConfig({
  server: {
    port: 8340,
    host: '0.0.0.0',  // accept LAN connections (phone testing)
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
