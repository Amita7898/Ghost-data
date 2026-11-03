import { test, expect } from "@playwright/test";

test("genuine replay, evidence navigation, history and persisted reload work offline", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Replay ready · model offline")).toBeVisible();
  await page.getByRole("button", { name: /Prose receipt audit/ }).click();
  await expect(
    page.getByText("RECORDED REPLAY", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Show all", exact: true }).click();
  await expect(page.getByText("Hypothesis checked").first()).toBeVisible();
  await expect(
    page.getByText("verified within scope", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect supporting source" })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator(".source-code")).toContainText(
    "Observed state: ABSENT",
  );
  await page.getByRole("button", { name: "Close evidence inspector" }).click();
  const url = page.url();
  await page.reload();
  await expect(
    page.getByText("verified within scope", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Hypothesis checked").first()).toBeVisible();
  await page.getByText("Hypothesis checked").first().scrollIntoViewIfNeeded();
  await page.screenshot({
    path: "../docs/screenshots/workspace-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Evidence", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Observation inventory" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/evidence-explorer.png",
    fullPage: true,
  });
  await expect(
    page.getByRole("button", { name: /prose_receipt.json/ }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Run history", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Run ledger" })).toBeVisible();
  const download = page.waitForEvent("download");
  await page
    .getByRole("link", { name: /Export report/ })
    .first()
    .click();
  expect((await download).suggestedFilename()).toMatch(/\.md$/);
  await page.goto("/");
  await page.screenshot({
    path: "../docs/screenshots/dashboard-desktop.png",
    fullPage: true,
  });
  await page.goto(url);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByText("RECORDED REPLAY", { exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../docs/screenshots/workspace-mobile.png",
    fullPage: true,
  });
});

test("creation uploads an actual JSON example and validates unsupported evidence", async ({
  page,
}) => {
  await page.goto("/new");
  await page.getByLabel("Synthetic example").selectOption("replica");
  await expect(page.getByLabel("Investigation title")).not.toHaveValue("");
  await page
    .getByLabel("Investigation title")
    .fill("Browser-created replica audit");
  await page.screenshot({
    path: "../docs/screenshots/new-investigation.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Create investigation", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Browser-created replica audit",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start live", exact: true }),
  ).toBeDisabled();
  await expect(page.locator(".offline-notice")).toContainText("Offline mode");
  await page.goto("/new");
  await page.getByLabel("Upload evidence JSON").setInputFiles({
    name: "unsafe.html",
    mimeType: "text/html",
    buffer: Buffer.from("<script>alert(1)</script>"),
  });
  await expect(page.getByRole("alert")).toContainText("Only structured JSON");
});
