/*
 * Runs one CSS assertion-based test case against a candidate's submitted
 * CSS, rendered into the question's HTML scaffold via a real headless
 * Chromium (Playwright). Expects /work/scaffold.html, /work/candidate.css,
 * /work/assertion.js mounted read-only by the caller (css_grader.py).
 * Always prints exactly one JSON line to stdout - {"passed": bool,
 * "message": str} - same convention as react_grader/run-test.js.
 *
 * Scaffold convention: the question's harness_fixture is a full HTML
 * document containing a `{{CSS}}` placeholder inside a <style> tag, which
 * gets replaced with the candidate's submitted CSS before rendering.
 *
 * Assertion script convention: plain statements using an in-scope `page`
 * (Playwright Page, already loaded with the rendered HTML) and `assert`
 * (Node's built-in assert module), e.g.:
 *   const display = await page.$eval('.card', el => getComputedStyle(el).display);
 *   assert.strictEqual(display, 'flex');
 */

const fs = require("fs");
const assert = require("assert");
const { chromium } = require("playwright");

function output(result) {
  process.stdout.write(JSON.stringify(result) + "\n");
  process.exit(0);
}

(async () => {
  let browser;
  try {
    const scaffold = fs.readFileSync("/work/scaffold.html", "utf-8");
    const css = fs.readFileSync("/work/candidate.css", "utf-8");
    const assertionSource = fs.readFileSync("/work/assertion.js", "utf-8");
    const html = scaffold.replace("{{CSS}}", css);

    browser = await chromium.launch();
    const page = await browser.newPage();
    await page.setContent(html);

    const runAssertion = new Function(
      "page", "assert",
      `return (async () => { ${assertionSource} })();`
    );
    await runAssertion(page, assert);

    await browser.close();
    output({ passed: true, message: "OK" });
  } catch (e) {
    if (browser) { try { await browser.close(); } catch (_) {} }
    output({ passed: false, message: String((e && e.message) || e) });
  }
})();
