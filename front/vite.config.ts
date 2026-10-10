import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Vite 설정: React와 Tailwind(CSS 도구)를 사용한다.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
});
