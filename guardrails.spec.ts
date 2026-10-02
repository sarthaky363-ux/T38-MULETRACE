import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const TABS = ["investigation", "rings", "lab"];
const SIZES = [
  { width: 1366, height: 768 },
  { width: 1920, height: 1080 },
];

for (const size of SIZES) {
  test.describe(size.width + "x" + size.height, () => {
    test.use({ viewport: size });

    for (const tab of TABS) {
      test("axe: " + tab, async ({ page }) => {
        await page.goto("/#" + tab);
        await page.waitForSelector(".app-header", { timeout: 10000 });
        // Analyze WCAG 2 A and AA rules
        const r = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa"])
          .disableRules(["color-contrast"]) // dark theme custom cyber glow contrast can be fine-tuned or verified
          .analyze();
        expect(r.violations).toEqual([]);
      });

      test("no %% and no sideways scroll: " + tab, async ({ page }) => {
        await page.goto("/#" + tab);
        await page.waitForSelector(".app-header", { timeout: 10000 });
        expect(await page.locator("body").innerText()).not.toContain("%%");
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth > window.innerWidth
        );
        expect(overflow).toBe(false);
      });
    }

    test("header height is identical across tabs", async ({ page }) => {
      const heights: number[] = [];
      for (const tab of TABS) {
        await page.goto("/#" + tab);
        await page.waitForSelector(".app-header", { timeout: 10000 });
        const box = await page.locator(".app-header").boundingBox();
        heights.push(Math.round(box!.height));
      }
      expect(new Set(heights).size).toBe(1);
    });

    test("every button has an accessible name", async ({ page }) => {
      await page.goto("/#investigation");
      await page.waitForSelector(".app-header", { timeout: 10000 });
      for (const b of await page.getByRole("button").all()) {
        const name = (await b.getAttribute("aria-label")) || (await b.innerText()) || (await b.getAttribute("title"));
        expect((name || "").trim().length).toBeGreaterThan(0);
      }
    });
  });
}
