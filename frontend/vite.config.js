import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Built into the API image and served by FastAPI, so the bundle must land
  // where the backend expects it. One artifact, one deploy, no CORS.
  build: { outDir: "dist", emptyOutDir: true },
  server: {
    // Dev only: `npm run dev` proxies API calls to the container on :8000, so
    // the frontend code can use same-origin paths in BOTH dev and production.
    proxy: {
      "/orders": "http://localhost:8000",
      "/riders": "http://localhost:8000",
      "/auth": "http://localhost:8000",
      "/admin": "http://localhost:8000",
      "/ready": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/metrics": "http://localhost:8000",
      "/docs": "http://localhost:8000",
    },
  },
});
