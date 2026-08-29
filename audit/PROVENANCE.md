# Provenance — who wrote each sentence

Short answer: **not me.** Unlike a wiki of summaries, almost nothing here is
synthesis. That is the point of building it from the authors' own registers.

| directory | pages | written by | from |
|---|---|---|---|
| `wiki/concepts/` | 192 | **Heim & Dröscher**, DeepL-translated | Begriffsregister, vol. 3 pp. 80–99 |
| `wiki/register/` | 38 | machine | Formelregister, vol. 3 pp. 100–137, with scans |
| `wiki/sources/` | 4 | me | extraction figures and caveats |
| `wiki/overview.md`, `index.md` | 2 | me | — |

So six pages are mine. The other 230 are the authors' text or machine output.

## The chain

1. **Extraction** — `pdfdrill` over the four PDFs; MathPix OCR. Equations and
   formulas become first-class objects carrying the author's LaTeX.
2. **Translation** — `pdfdrill translate --to EN-US --from DE` (DeepL Pro).
   1,555 of 1,582 prose units reach the model carrying both languages:
   `text` = translation, `text_source` = original.
3. **Register parsing** — the Begriffsregister arrives as 23 undifferentiated
   `Paragraph` blobs. 192 `Term: definition` entries were split out of them;
   English is the parsing authority (see `audit/README.md` §2).
4. **Pairing** — German entries aligned to English by Needleman–Wunsch over the
   two ordered term lists, cognates as anchors. 147 → 189 bilingual.
5. **Linking** — printed `→` cross-references resolved by longest match against
   the term index; `(2, 21)` volume-page citations linked to the source pages.
6. **Build** — Markdown → single-file TiddlyWiki, every expression compiled by
   the same KaTeX the renderer uses.

## Conventions that carry meaning

- A definition with German beneath it: the German is the authority, the English
  is a machine translation of it.
- A formula with a scan beneath it: the scan is the authority, the LaTeX is a
  reading of it.
- A formula in a fenced ```latex block instead of rendered: the extraction
  contains a character KaTeX refuses. Shown verbatim rather than broken.
- `lang:` / `lang_source:` in frontmatter: the body is a translation.
