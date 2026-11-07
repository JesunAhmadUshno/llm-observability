import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// The site reads ../level-*/ results, store and source files at build time, so every number on the page is generated, never typed.
export default defineConfig({
  base: '/llm-observability/',
  plugins: [react()],
  server: { fs: { allow: ['..'] } },
});
