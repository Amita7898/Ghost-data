import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: process.env.GHOST_DATA_WEB_URL || "http://127.0.0.1:8000",
    channel: process.env.CI ? undefined : "chrome",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
  },
  reporter: "list",
});
