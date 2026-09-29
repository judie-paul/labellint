import { test, expect } from "@playwright/test";

test("sample audit, evidence, filters, annotators and charts", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Record review" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Run sample" }).first().click();
  await expect(page.locator("tbody tr").first()).toBeVisible({
    timeout: 45000,
  });
  await page.screenshot({
    path: `test-results/${info.project.name}-review.png`,
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("button", { name: /^Review syn_/ })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evidence" })).toBeVisible();
  await page.getByRole("button", { name: "Close record", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Search records" })
    .fill("no-such-record");
  await expect(page.getByText("No matching records")).toBeVisible();
  await page.getByRole("textbox", { name: "Search records" }).fill("");
  await page.getByRole("button", { name: "Annotators", exact: true }).click();
  await page.getByRole("button", { name: "View records" }).first().click();
  await expect(
    page.getByRole("textbox", { name: "Search records" }),
  ).toHaveValue(/ann_/);
  await page.getByRole("button", { name: "Evaluation", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Against ground truth" }),
  ).toBeVisible();
  await expect(page.locator(".recharts-bar-rectangle").first()).toBeVisible();
  await page.screenshot({
    path: `test-results/${info.project.name}-evaluation.png`,
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("upload canonical JSONL and surface malformed data", async ({ page }) => {
  await page.goto("/");
  await page.locator("input[type=file]").setInputFiles({
    name: "invalid.jsonl",
    mimeType: "application/json",
    buffer: Buffer.from("{}"),
  });
  await expect(page.getByRole("alert")).toContainText("invalid annotation");
  const row = {
    record_id: "uploaded-1",
    item_id: "item-1",
    source: "local",
    prompt: "Explain testing",
    response: "Tests check behavior",
    aspect: "helpfulness",
    annotator_id: "reviewer-1",
    rating: 5,
    rationale: "Clear and accurate",
    time_spent_sec: 45,
  };
  await page.locator("input[type=file]").setInputFiles({
    name: "annotations.jsonl",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(row)),
  });
  await expect(page.getByText("Complete", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Record review", exact: true })
    .click();
  await page.getByLabel("Flagged only").uncheck();
  await expect(
    page.getByRole("button", { name: "uploaded-1", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Evaluation", exact: true }).click();
  await expect(
    page.getByText("Ground truth unavailable for this audit"),
  ).toBeVisible();
});
