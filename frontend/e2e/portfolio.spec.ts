import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "@playwright/test";

async function accessible(page: any) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
}

test("portfolio screens pass scoped accessibility checks and source dialog keeps keyboard focus", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Replay ready · model offline")).toBeVisible();
  await accessible(page);
  await page.goto("/new");
  await page.getByLabel("Synthetic example").selectOption("receipt");
  await accessible(page);
  await page.goto("/");
  await page.getByRole("button", { name: /Prose receipt audit/ }).click();
  await page.getByRole("button", { name: "Show all", exact: true }).click();
  await expect(
    page.getByText("verified within scope", { exact: true }),
  ).toBeVisible();
  await accessible(page);
  const opener = page
    .getByRole("button", { name: "Inspect supporting source" })
    .first();
  await opener.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Close evidence inspector" }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(dialog.getByRole("link")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Close evidence inspector" }),
  ).toBeFocused();
  await accessible(page);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(opener).toBeFocused();
  await page.getByRole("link", { name: "Evidence", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Observation inventory" }),
  ).toBeVisible();
  await accessible(page);
  await page.getByRole("link", { name: "Run history", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Run ledger" })).toBeVisible();
  await accessible(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await accessible(page);
});

test("runtime connection failure is not labeled replay-ready", async ({
  page,
}) => {
  await page.route("**/api/v1/runtime", (route) => route.abort());
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: /Backend unavailable/ }),
  ).toBeVisible();
  await expect(
    page.getByText("Replay ready · model offline"),
  ).not.toBeVisible();
});

test("genuine conflict recording exposes rejected proposals and uncertainty", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Conflicting readbacks/ }).click();
  await page.getByRole("button", { name: "Show all", exact: true }).click();
  await expect(page.locator(".event-card.rejected")).toHaveCount(2);
  await expect(page.getByText("inconclusive", { exact: true })).toBeVisible();
  await expect(
    page.getByText("RECORDED REPLAY", { exact: true }),
  ).toBeVisible();
});
