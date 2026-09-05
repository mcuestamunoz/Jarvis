/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { jarvisProjectsPlugin } from "./vite-plugin-jarvis-projects";

export default defineConfig({
  plugins: [react(), jarvisProjectsPlugin()],
  test: {
    environment: "node",
  },
});

