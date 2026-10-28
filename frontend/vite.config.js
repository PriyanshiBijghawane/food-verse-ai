import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    preserveSymlinks: true,
  },
  // Workaround: Vite 6.x + Node 24 + Windows Junction symlink bug.
  // The dep-optimizer resolves physical paths but stores Junction paths in
  // metadata, causing "Cannot read properties of undefined (reading 'imports')"
  // on first browser request. Disabling pre-bundling discovery is the safest fix.
  optimizeDeps: {
    include: ['react', 'react-dom', 'lucide-react'],
    force: false,
  },
  server: {
    port: 5173,
    fs: {
      // Allow serving files from symlinked real paths
      allow: ['..'],
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
