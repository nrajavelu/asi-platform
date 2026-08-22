/*
 * Runs one React assertion-based test case against a candidate's submitted
 * component. Expects /work/candidate.jsx and /work/assertion.js mounted
 * read-only by the caller (react_grader.py). Always prints exactly one
 * JSON line to stdout - {"passed": bool, "message": str} - and exits 0,
 * so the caller parses the result instead of relying on exit codes (which
 * Docker/Node can produce for reasons unrelated to pass/fail).
 *
 * Candidate convention: submission defines a function named `Component`
 * (JSX allowed) - no imports/exports required.
 */

const fs = require("fs");
const assert = require("assert");
const esbuild = require("esbuild");
const { JSDOM } = require("jsdom");

function output(result) {
  process.stdout.write(JSON.stringify(result) + "\n");
  process.exit(0);
}

try {
  const candidateSource = fs.readFileSync("/work/candidate.jsx", "utf-8");
  const assertionSource = fs.readFileSync("/work/assertion.js", "utf-8");

  // esbuild's CJS transform only exports symbols the candidate explicitly
  // `export`s - a bare `function Component(...) {}` (the convention we ask
  // candidates to follow) stays a plain hoisted declaration in scope, never
  // attached to module.exports. Capture it by name afterwards instead of
  // requiring candidates to write an export statement themselves.
  const candidateJs =
    esbuild.transformSync(candidateSource, { loader: "jsx", format: "cjs" }).code +
    "\ntry { module.exports.Component = Component; } catch (e) {}\n";
  const assertionJs = esbuild.transformSync(assertionSource, { loader: "jsx", format: "cjs" }).code;

  const dom = new JSDOM("<!doctype html><html><body></body></html>");
  global.window = dom.window;
  global.document = dom.window.document;
  global.navigator = dom.window.navigator;

  const React = require("react");
  const ReactDOM = require("react-dom");

  const candidateModule = { exports: {} };
  const runCandidate = new Function("module", "exports", "React", "require", candidateJs);
  runCandidate(candidateModule, candidateModule.exports, React, require);

  const Component = candidateModule.exports.Component || candidateModule.exports.default || candidateModule.exports;
  if (typeof Component !== "function") {
    output({ passed: false, message: "Your code must define a `Component` function, e.g. `function Component(props) { ... }`." });
  }

  const runAssertion = new Function("React", "ReactDOM", "Component", "assert", "document", assertionJs);
  runAssertion(React, ReactDOM, Component, assert, document);

  output({ passed: true, message: "OK" });
} catch (e) {
  output({ passed: false, message: String((e && e.message) || e) });
}
