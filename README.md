# HeimWiki — Burkhard Heim's *Elementarstrukturen der Materie*, bilingual

A single-file wiki (`HeimWiki.html`, 11.5 MB) that opens offline in any browser,
built from the Markdown under `wiki/`. The Markdown is the source of truth and
also renders in [llmwiki](https://github.com/lucasastorian/llmwiki); the HTML is
a build artifact.

## What this is, and what it is not

**Every concept page is Heim and Dröscher's own definition.** Volume 3 of the
work carries a *Begriffsregister* — the authors' index of terms — and a
*Formelregister*. Those two registers are this wiki. Nothing here is a summary
written for it, and no one has written up the argument of the volumes.

All four volumes are in it, completely — 2,222 pages:

| volume | document pages | equations | tables | figures | notes | references |
|---|---|---|---|---|---|---|
| 1 — Elementarstrukturen der Materie | 310 | 240 | 1 | 1 | 20 | 1 |
| 2 — Elementarstrukturen der Materie | 379 | 344 | 3 | 1 | 30 | 1 |
| 3 — Einführung, mit Registern | 100 | 324 | 0 | 0 | 6 | 0 |
| 4 — Dröscher, Begleitband | 161 | 78 | 0 | 0 | 6 | 25 |

Plus **192 concept pages** — the Begriffsregister of volume 3, one page per term,
189 of them bilingual.

This is not a selection. `pdfdrill` parses the whole document into a docmodel and
projects it as `<bibkey>.tiddlers.json`; `build/pdfdrill2llmwiki.py` re-expresses
that in llmwiki's dialect. Every page of prose is here, with its inline formulas
set as `$…$`, its headings, and links out to every equation, table, figure, note
and reference — each of which has a page of its own. Where a translation exists
the German original sits beneath the English on the same page.

**No scan images.** Every equation is LaTeX. 46,848 maths expressions, all of
which compile.

What is still missing is *synthesis*: concept pages for volumes 1, 2 and 4 the
way volume 3 has them. That needs someone to read the volumes.

## Provenance

Extracted with [`pdfdrill`](https://pdfdrill.info) (MathPix OCR), translated to
English with DeepL. The German original is retained on every translated unit.

**Do not cite formulas from translated prose.** Measured across the four
volumes: of 22,860 inline-math spans in the German, only **20.1%** are
byte-identical after translation — the translator normalised decimal commas
(`2,7 K` → `2.7 K`), spacing (`S U(5)` → `SU(5)`) and operators. The **13,454
Formula and Equation objects were not touched at all** (0 carry a `latex_source`
twin, 0 have changed `latex`). The formula register and the German original are
the reliable sources for mathematics.

## Build

```bash
./build/build.sh          # wiki/ -> HeimWiki.html
python3 build/verify.py   # regenerate audit/verification.json
```

Needs `node` and a TiddlyWiki install; KaTeX is vendored under `build/vendor/`,
so the build runs offline.

## Review

`audit/` is a review channel for someone working only from this repository —
start at `audit/README.md`. It records what is machine output and what is
judgement, and lists what has not been checked by anyone.

## Licence and rights

| what | licence |
|---|---|
| `build/` — the build scripts | **MIT** © 2026 Wulf Kolbe — see `build/LICENSE` |
| `build/vendor/katex/` | MIT © Khan Academy — its own LICENSE, unmodified |
| `wiki/`, `HeimWiki.html` — the content | **no licence granted** |

There is no repository-root `LICENSE`, deliberately: one would make GitHub
report the whole repository as MIT, which would be wrong about the content.

**The content reproduces a published reference work.** The concept pages carry
Heim and Dröscher's register definitions in full, in translation, and the
formula pages carry 662 of their printed equations. That is a reproduction of
the substance of a copyrighted book, not an excerpt from it. The verbatim
full-text extractions are excluded from this repository (`raw/`, gitignored),
but that does not change what the register pages are. Anyone reusing this
material is responsible for their own rights position.
