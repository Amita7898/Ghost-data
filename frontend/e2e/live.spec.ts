import { test, expect } from "@playwright/test";

test("actual local LLM investigation streams real events and survives browser reload", async ({
  page,
  request,
}) => {
  test.skip(
    process.env.GHOST_DATA_LIVE_WEB !== "1",
    "Opt-in real local model integration",
  );
  test.setTimeout(520000);
  await page.goto("/new");
  await page.getByLabel("Synthetic example").selectOption("replica");
  await page
    .getByLabel("Investigation title")
    .fill("Live browser investigation");
  await page
    .getByRole("button", { name: "Create investigation", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start live", exact: true }),
  ).toBeEnabled({ timeout: 10000 });
  await page.getByRole("button", { name: "Start live", exact: true }).click();
  await expect(page.getByText("live", { exact: true })).toBeVisible();
  await expect(page.getByText("Local model investigating").first()).toBeVisible(
    { timeout: 30000 },
  );
  const runId = new URL(page.url()).searchParams.get("run");
  expect(runId).toBeTruthy();
  await page.reload();
  await expect(
    page.getByText("Local model investigating").first(),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/live-investigation.png",
    fullPage: true,
  });
  await expect
    .poll(
      async () => {
        const r = await request.get("/api/v1/runs/" + runId);
        return (await r.json()).status;
      },
      { timeout: 360000, intervals: [1000, 2000, 3000] },
    )
    .toBe("completed");
  const run = await (await request.get("/api/v1/runs/" + runId)).json();
  expect(run.usage.model_calls).toBeGreaterThan(0);
  expect(run.report.conclusion).toBe("NON_COMPLIANT");
  const events = await (
    await request.get("/api/v1/runs/" + runId + "/events")
  ).json();
  expect(events.some((e: any) => e.kind === "tool_requested")).toBeTruthy();
  await expect(page.getByText("non compliant", { exact: true })).toBeVisible({
    timeout: 10000,
  });
  await page.screenshot({
    path: "../docs/screenshots/live-completed.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Start live", exact: true }).click();
  await expect(page.getByText("Local model investigating").first()).toBeVisible(
    { timeout: 30000 },
  );
  await expect.poll(() => new URL(page.url()).searchParams.get("run")).not.toBe(runId);
  const cancelId = new URL(page.url()).searchParams.get("run");
  expect(cancelId).not.toBe(runId);
  await page.getByRole("button", { name: "Cancel run", exact: true }).click();
  await expect
    .poll(
      async () => {
        const r = await request.get("/api/v1/runs/" + cancelId);
        return (await r.json()).status;
      },
      { timeout: 150000, intervals: [1000, 2000] },
    )
    .toBe("cancelled");
  await expect(page.getByText("cancelled", { exact: true })).toBeVisible({
    timeout: 10000,
  });
});
