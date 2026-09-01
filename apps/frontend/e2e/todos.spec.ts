import { test, expect } from "@playwright/test";

/**
 * End-to-end test for the Todos feature (see specs/todos/design.md).
 *
 * This exercises a real login through Auth0's Universal Login page, so it
 * requires a test user in your Auth0 tenant. Configure:
 *   E2E_AUTH0_USERNAME, E2E_AUTH0_PASSWORD
 * The test is skipped automatically if these aren't set (e.g. local dev
 * without Auth0 configured yet). In CI, set them as repository secrets.
 */
const username = process.env.E2E_AUTH0_USERNAME;
const password = process.env.E2E_AUTH0_PASSWORD;

test.describe("Todos", () => {
  test.skip(!username || !password, "Set E2E_AUTH0_USERNAME/E2E_AUTH0_PASSWORD to run this test");

  test("user can create, toggle, and delete a todo", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "Log in" }).click();

    // Auth0 Universal Login (hosted page)
    await page.getByLabel(/email|username/i).fill(username!);
    await page.getByLabel(/password/i).fill(password!);
    await page.getByRole("button", { name: /continue|log in/i }).click();

    const todoTitle = `E2E todo ${Date.now()}`;

    await page.getByLabel("New todo title").fill(todoTitle);
    await page.getByRole("button", { name: "Add" }).click();

    const todoRow = page.getByText(todoTitle);
    await expect(todoRow).toBeVisible();

    await page.getByRole("checkbox").first().check();
    await expect(todoRow).toHaveClass(/line-through/);

    await page.getByRole("button", { name: `Delete ${todoTitle}` }).click();
    await expect(todoRow).not.toBeVisible();
  });
});
