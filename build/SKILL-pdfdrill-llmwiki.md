---
name: pdfdrill-llmwiki
description: |
  Put a drilled document into an llmwiki workspace, complete. Use when a PDF has
  been drilled with pdfdrill and its content should become wiki pages: every
  page of prose, every equation, table, figure, note and reference, with the
  document's own structure preserved. One command does it.
allowed-tools: [Read, Bash, Write]
---

# pdfdrill → llmwiki

**The docmodel already holds the whole document.** Do not read the PDF, do not
summarise, do not select. `pdfdrill` has parsed the structure; the job is to
re-express it in llmwiki's dialect, and `pdfdrill2llmwiki` does that in one
command.

---

## The short version

```bash
llmwiki init ~/mywiki                                   # once per workspace
pdfdrill preflight --ack DRILL-xxxxxxxx                 # once per session
pdfdrill tiddlers <pdf> --bibkey mykey                  # the complete projection
pdfdrill2llmwiki --doc <drill-folder> --wiki ~/mywiki/wiki --title "…"
llmwiki serve ~/mywiki
```

That is the whole path. Everything below is why each step is there.

---

## 1. What pdfdrill gives you

`<bibkey>.tiddlers.json` is pdfdrill's own **complete** projection — not a
summary, not a selection. For one 400-page volume it holds 6,469 units:

| unit | count | what it is |
|---|---|---|
| formula | 4,871 | inline maths, with `latex` |
| paragraph | 656 | prose, with `text`, `page`, `parent_section` |
| page | 400 | page markers |
| equation | 344 | display maths, with `refnum` |
| listitem, sidenote, footnote, table, diagram, section, citation | ~180 | the rest |

Reading order lives **inside the prose**, as transclusion markers:

```
... the transcoordinates {{bh2_FO0001||FO}} and {{bh2_FO0002||FO}} are ...
```

and templates say how each renders (`FO` → `<$latex text={{!!latex}}/>`,
`CIT` → a citekey link). One volume carries 9,744 such markers. **This is the
structure. Anything you build by re-reading the PDF is a worse copy of it.**

If a translation was run, each unit also carries `text_source` (the original)
and `translated_lang`.

## 2. What the CLI does with it

`pdfdrill2llmwiki` walks that projection and writes llmwiki markdown:

```
wiki/<bibkey>/pages/pNNN.md        one per document page: headings, prose,
                                   inline formulas set as $…$, links out
wiki/<bibkey>/equations/*.md       one per display equation, with its refnum
wiki/<bibkey>/tables/*.md
wiki/<bibkey>/figures/*.md         diagrams and pictures
wiki/<bibkey>/notes/*.md           foot- and sidenotes
wiki/<bibkey>/references/*.md      one per reference, with its BibTeX
wiki/sources/<bibkey>.md           what the document contains
```

Marker translation:

| pdfdrill | llmwiki |
|---|---|
| `{{X\|\|FO}}` | `$latex$` inline in the sentence |
| `{{X\|\|EQBLOCK}}` | link to the equation's page |
| `{{X\|\|TAB}}` `{{X\|\|DIA}}` `{{X\|\|SN}}` | link to that element's page |
| `{{X\|\|CIT}}` | link to the reference page, labelled with its citekey |
| `{{X\|\|PARA}}` `{{X\|\|LI}}` | inlined in reading order |

**Inline formulas are inlined, not given pages.** There are 9,744 in one volume
and a formula inside a sentence is part of the sentence. Everything that stands
alone on the printed page gets a page of its own.

If the document was translated, each page carries the original beneath the
translation in an `okf:source` block, so a reader can check it.

## 3. The rules that matter

**Never `pdfdrill model` to rename.** A rebuild silently drops enrichments —
measured: 105 translated units gone from a model rebuilt six days after its
translation. Use `pdfdrill rename <pdf> <name> --bibkey <key>`, which retargets
the folder, the bibkey, the crops and the OKF bundle without rebuilding.

**Convert the maths delimiters.** pdfdrill emits `\( … \)`; llmwiki forbids it
(`mcp/tools/guide.py:138` — markdown eats the backslashes). The CLI rewrites to
`$ … $`.

**Use markdown links, not `[[wikilinks]]`.** llmwiki's renderer has no wikilink
plugin and shows them as literal text (`guide.py:157`).

**Compile every expression before publishing.** OCR produces readings KaTeX
refuses — unbalanced braces, stray non-ASCII operators. The CLI validates each
one against the same KaTeX the renderer uses and demotes failures to literal
text rather than shipping a broken render. Measured on four volumes: 29 of
46,848 expressions.

**Keep build output out of the workspace.** `llmwiki init` indexes everything
not excluded by `.llmwikiignore` (falling back to `.gitignore`,
`api/domain/watcher.py:37`). A toolchain left in the workspace root gets indexed
as sources — in one case 4,927 build files against 568 wiki pages.

**No scan images.** Equations are LaTeX. Crops are indexed as separate documents
and flood the Recent view with jpgs whose paths resolve to no wiki page; carry
the unit id instead, which locates the crop in the drill folder.

## 4. What it cannot do

- **Chapters** need a signal. Where a volume has `Abstract` objects they mark
  chapter starts; where it has none, matching TOC titles against page text may
  confirm nothing (measured: 0, 0 and 1 across three volumes). Then there is no
  honest chapter boundary and the CLI does not invent one.
- **SVG** for tables and diagrams needs `pdfdrill svg`, which needs compilable
  LaTeX. On scanned German volumes the preamble pulled in `xeCJK`, which needs
  XeTeX while the svg route runs `latex` — all attempts failed. Check before
  promising SVG.
- **References** exist only where the document has a parseable reference list.
  Three of four volumes here yielded none; run `pdfdrill bibliography`, then
  `pdfdrill bibfetch` for BibTeX where there is no author `.bbl`/`.bib`.
- **Synthesis.** This produces the document, faithfully. Concept pages — the
  thing that makes a wiki worth reading — still need someone to read it.

## 5. Verifying before you publish

```bash
python3 verify.py            # pages, links, images, KaTeX
```

Three gates, all of which must pass: every expression compiles, every link and
image resolves, and the page count matches what you expect. Structural checks
say nothing about whether a *translation* or a *reading* is right — for that,
the original is on the page beneath it.
