import { defineConfig } from "vite";

const backendPort = process.env.BACKEND_PORT ?? "8000";
const frontendPort = Number(process.env.FRONTEND_PORT ?? "5173");

export default defineConfig({
  server: {
    port: frontendPort,
    strictPort: true,
    proxy: {
      "/api": {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
  build: {
    sourcemap: true,
  },
});
