import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Same origin as in production (CloudFront), so the SameSite=Strict, Path=/api cookie works without CORS.
  server: { proxy: { "/api": "http://localhost:8000" } },
});
