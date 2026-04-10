import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],

  root: ".",
  envPrefix: "VITE_",

  server: {
    port: 5173,
    strictPort: false,
  },

  build: {
    outDir: "dist",
    sourcemap: true,
    minify: "terser",
  },

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
