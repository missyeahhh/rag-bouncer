import { test, expect } from '@playwright/test';

// Playwright tests the screen; Ragas judges the answers (eval/gate.py).
// The API is mocked so this suite is fast, free and deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/api/ask', (route) =>
    route.fulfill({
      json: {
        answer: 'MySQL 8 is the only supported database in production.',
        sources: ['https://github.com/TryGhost/Docs/blob/f9467f7/faq/supported-databases.mdx'],
      },
    }),
  );
  await page.goto('/');
});

test('shows the answer to a question', async ({ page }) => {
  await page.getByLabel('Question').fill('Which database does Ghost support?');
  await page.getByRole('button', { name: 'Ask' }).click();
  await expect(page.getByTestId('answer')).toContainText('MySQL 8');
});

test('links every source the answer used', async ({ page }) => {
  await page.getByLabel('Question').fill('Which database does Ghost support?');
  await page.getByRole('button', { name: 'Ask' }).click();
  await expect(page.getByTestId('sources').getByRole('link')).toHaveCount(1);
});
