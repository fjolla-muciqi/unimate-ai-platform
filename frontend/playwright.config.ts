import { defineConfig } from "@playwright/test";

/**
 * Testet end-to-end ekzekutohen kundrejt sistemit që po punon në Docker
 * (`docker compose up`), me të dhënat demo të seed-it:
 *
 *     npx playwright test
 *
 * Asnjë test nuk arrin te Claude: chat-i provohet vetëm me kërkesa që
 * Guardrail Agent-i i bllokon para modelit, prandaj nuk kushtojnë.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: 0,
  reporter: "list",

  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",

    // Edge-i i instaluar në Windows; në Linux/CI vendos PW_CHANNEL=chromium.
    channel: process.env.PW_CHANNEL ?? "msedge",

    trace: "retain-on-failure",
  },
});
