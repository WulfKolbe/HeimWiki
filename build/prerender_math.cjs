#!/usr/bin/env node
// SPDX-License-Identifier: MIT
/* Read {files:[{path,text}]} on stdin; replace $...$ / $$...$$ with TiddlyWiki
   <$latex/> widgets that TRANSCLUDE the LaTeX from a per-formula tiddler.

   Putting the LaTeX in an attribute cannot work here: real mathematics contains
   <, > and & (& is the alignment character inside `aligned`), none of which
   survive a TiddlyWiki attribute, and & cannot be escaped without breaking the
   environment. Transclusion sidesteps the attribute entirely, keeps the LaTeX
   editable in its own tiddler, and is the pattern pdfdrill's own EQBLOCK uses.

   Every expression is still compiled with KaTeX here, so a bad one fails the
   build instead of rendering red. */
const fs = require("fs");
const path = require("path");
const katex = require(path.join(__dirname, "vendor", "katex"));

const math = {};           // tiddler title -> latex
let seq = 0;

function store(expr) {
  const title = `math/${String(++seq).padStart(4, "0")}`;
  math[title] = expr;
  return title;
}

function check(expr, displayMode, where) {
  try {
    katex.renderToString(expr, { displayMode, throwOnError: true, strict: "error" });
  } catch (err) {
    console.error(`KaTeX rejected ${JSON.stringify(expr.slice(0, 70))} in ${where}:\n  ${err.message}`);
    process.exit(1);
  }
}

function convert(text, where) {
  let inline = 0, display = 0;
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, e) => {
    const expr = e.trim();
    check(expr, true, where); display++;
    return `<$latex text={{${store(expr)}}} displayMode="true"/>`;
  });
  text = text.replace(/\$([^$\n]+?)\$/g, (_, e) => {
    const expr = e.trim();
    check(expr, false, where); inline++;
    return `<$latex text={{${store(expr)}}}/>`;
  });
  return { text, inline, display };
}

const input = JSON.parse(fs.readFileSync(0, "utf8"));
let inline = 0, display = 0;
const files = input.files.map((f) => {
  const r = convert(f.text, f.path);
  inline += r.inline; display += r.display;
  return { path: f.path, text: r.text };
});
process.stdout.write(JSON.stringify({ files, inline, display, math, katexVersion: katex.version }));
