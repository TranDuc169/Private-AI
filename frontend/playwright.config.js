import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 45000,
  expect: { timeout: 10000 },
  outputDir: process.env.E2E_OUTPUT_DIR || "/tmp/private-ai-browser-results",
  reporter: "list",
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:5173",
    headless: true,
    launchOptions: process.env.CHROMIUM_PATH
      ? { executablePath: process.env.CHROMIUM_PATH }
      : {},
    screenshot: "only-on-failure",
  },
});
