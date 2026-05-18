// @ts-check
import { defineConfig, devices } from '@playwright/test'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:6273'
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:6173'

export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.js',
  timeout: 30000,
  retries: 0,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],

  use: {
    baseURL: FRONTEND_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'api',
      testMatch: 'api-smoke.spec.js',
      use: { baseURL: BACKEND_URL },
    },
    {
      name: 'chromium',
      testMatch: 'frontend-smoke.spec.js',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
