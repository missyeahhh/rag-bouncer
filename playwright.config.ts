import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  use: { baseURL: 'http://localhost:4173' },
  webServer: {
    command: 'python3 -m http.server 4173 --directory web',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
  },
});
