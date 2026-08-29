---
title: "Overview"
type: synthesis
tags: [heim]
lang: EN-US
lang_source: de
maintained: hand
last_updated: 2026-08-29
---

<!-- HAND-MAINTAINED. No generator produces this page: it is prose about the
     wiki, not a projection of it. Edit it directly, and edit it when the shape
     of the wiki changes — it was stale for two days after the full projection
     landed, still describing a formula register that no longer existed.
     Everything else under wiki/ is generated; see build/ and out/314.txt. -->

# Overview

A bilingual wiki over the four drilled Heim volumes — **the documents themselves,
not a summary of them.** `pdfdrill` parses each volume into a docmodel and
`build/pdfdrill2llmwiki.py` re-expresses that structure as wiki pages: every page
of prose, with its inline formulas, and a page of its own for every equation,
table, figure, note and reference.

The English is a DeepL translation; the German original sits beneath it on every
translated page.

## What is here

| | |
|---|---|
| document pages | 950 — the text of all four volumes |
| equations, tables, figures, notes | 1,054 pages |
| references | 27, with BibTeX where the volume had a reference list |
| concept pages | 192 — the Begriffsregister of volume 3, 189 bilingual |

Start at the [index](index.md).

## Provenance and its limits

Text and mathematics are MathPix OCR readings via `pdfdrill`, translated with
DeepL. Three things to know before citing anything here:

1. **The prose is a translation.** The German is on the page for that reason —
   where the English reads oddly, the original is the authority.
2. **Do not cite formulas from translated prose.** Of 22,860 inline-math spans
   in the German, only 20.1% are byte-identical after translation: the
   translator normalised decimal commas, spacing and operators. The 13,454
   Formula and Equation objects were **not** touched, so the equation pages and
   the German original are the reliable sources for mathematics.
3. **Nobody has checked the translations.** No German-speaking physicist has
   read this output. It reads plausibly, which is what makes it dangerous. See
   `audit/OPEN-QUESTIONS.md`.

## What is not here

**Synthesis.** This is the documents, faithfully projected — not a reading of
them. Volume 3 has concept pages because its authors wrote a Begriffsregister;
volumes 1, 2 and 4 have none, because writing them needs someone to read the
volumes.

No scan images: every equation is LaTeX, and each carries the unit id that
locates its crop in the drill folder.
