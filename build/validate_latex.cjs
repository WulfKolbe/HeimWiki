#!/usr/bin/env node
// SPDX-License-Identifier: MIT
/* stdin: {"items":[{"id":..,"latex":..}]} -> stdout: {"bad":[ids]} */
const katex = require(require("path").join(__dirname, "vendor", "katex"));
const input = JSON.parse(require("fs").readFileSync(0, "utf8"));
const bad = [];
for (const it of input.items) {
  try { katex.renderToString(it.latex, {displayMode: true, throwOnError: true, strict: "error"}); }
  catch (e) { bad.push(it.id); }
}
process.stdout.write(JSON.stringify({bad}));
