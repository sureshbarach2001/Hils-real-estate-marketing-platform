import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Approach:
//   1. Standard React + Vite setup, dev server on :5173 (matches CORS_ORIGINS).
//   2. `@/...` resolves to `src/` so imports stay short and refactor-friendly.
//   3. `@shared/...` reaches into the repo's /shared folder for cross-cutting
//      constants and helpers used by both the frontend and the backend.

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@shared': path.resolve(__dirname, '..', 'shared'),
    },
  },
  server: {
    port: 5173,
    host: 'localhost',
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
