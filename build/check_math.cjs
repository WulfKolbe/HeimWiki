#!/usr/bin/env node
// SPDX-License-Identifier: MIT
/* Acceptance check for Markdown math. Usage: node check_math.cjs <file.md> [...]
   Exits non-zero if any $...$ / $$...$$ expression fails to compile. */
const fs = require("fs");
const path = require("path");
const katex = require(path.join(__dirname, "vendor", "katex"));

let failedTotal = 0;
for (const file of process.argv.slice(2)) {
  const src = fs.readFileSync(file, "utf8");
  const display = [...src.matchAll(/\$\$([\s\S]+?)\$\$/g)].map((m) => [m[1].trim(), true]);
  const inline = [...src.replace(/\$\$[\s\S]+?\$\$/g, " ").matchAll(/\$([^$\n]+?)\$/g)]
    .map((m) => [m[1].trim(), false]);
  const all = [...display, ...inline];
  const fails = [];
  for (const [expr, displayMode] of all) {
    try {
      katex.renderToString(expr, { displayMode, throwOnError: true, strict: "error" });
    } catch (err) {
      fails.push([expr, err.message.replace(/\s+/g, " ")]);
    }
  }
  failedTotal += fails.length;
  const pct = all.length ? ((100 * fails.length) / all.length).toFixed(1) : "0.0";
  console.log(`${path.basename(file)}: ${all.length} expressions ` +
              `(${inline.length} inline, ${display.length} display), ${fails.length} failed (${pct}%)`);
  for (const [expr, msg] of fails.slice(0, 10)) {
    console.log(`  FAIL ${JSON.stringify(expr.slice(0, 70))}\n       ${msg.slice(0, 100)}`);
  }
  if (fails.length > 10) console.log(`  ... and ${fails.length - 10} more`);
}
process.exit(failedTotal ? 1 : 0);
