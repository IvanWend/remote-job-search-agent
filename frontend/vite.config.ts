import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Dev only: the API runs on :8000, the dev server on :5173. Relative
    // fetches to /ask and /health are proxied so the code stays same-origin
    // and works unchanged when FastAPI serves the built dist/.
    proxy: {
      '/ask': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
