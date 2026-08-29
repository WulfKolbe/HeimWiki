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

- **192 concept pages** (189 bilingual) — the Begriffsregister, pages 80–99.
  English body, German original beneath it. The `→` cross-references of the
  printed register are live links; each page also lists what refers back to it.
- **38 formula-register pages** — 261 formulas from pages 100–137, each with the
  scan it was read from.
- **4 source pages** — one per volume, with its extraction figures.

Roughly 1,500 translated prose units and 13,454 formulas across the four volumes
are drilled and searchable but **not** written up. `wiki/overview.md` says so on
the page rather than leaving it to be inferred.

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
register pages carry 261 scans of their printed formulas. That is a reproduction
of the substance of a copyrighted book, not an excerpt from it. The verbatim
full-text extractions are excluded from this repository (`raw/`, gitignored),
but that does not change what the register pages are. Anyone reusing this
material is responsible for their own rights position.
