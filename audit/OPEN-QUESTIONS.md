# Open questions and known defects

Self-reported. Treat this as what I already know about, and look for what is
*not* here.

## 1. Nobody has checked the translations

The central weakness. DeepL translated 1,555 units of dense, coined
terminology — *Hermetrieform*, *Kondensorfluß*, *Weltselektor*, *Syntrometrie*,
*Äonische Dimension* — and no German-speaking physicist has read the output. It
*reads* plausibly, which is exactly what makes it dangerous. The German is on
every page so this is checkable; it has not been checked.

## 2. German terms were paired by alignment, not by understanding

Entry boundaries came from the English, because German capitalises every noun
and a Title-case scan absorbs the previous definition's tail (`"Raumzeit
Äonische Dimension"` for what should be `"Äonische Dimension"`). Where the two
lists disagreed in length, a Needleman–Wunsch alignment over the ordered terms
decided the pairing, with cognates as anchors — 147 → 189 bilingual.

**A mispairing would put one term's German under another term's English, and
nothing structural would catch it.** Four paragraphs were off by ±1 before the
alignment. Spot-checking those regions is worthwhile.

## 3. Three entries have no German

192 entries, 189 bilingual. Three carry only the English. They are not marked
differently on the page beyond the absence of the German block.

## 4. Cross-references were resolved by string matching

The printed `→` arrows were linked by longest match against the term index,
singular-aware. A wrong link silently changes what a definition points at. 230
cross-references were resolved; none was verified against the authors' intent.

## 5. Translation mutates mathematics embedded in prose

Of 22,860 inline-math spans in the German, only **20.1%** are byte-identical
after translation. Most changes are normalisations and some are repairs
(`2,7^{\circ} K` → `2.7^{\circ} K`, `S U(5)` → `SU(5)`, `E=m . c^{2}` →
`E = m \cdot c^{2}`), but a physics corpus cannot rest on a translator's
judgement about formulas.

Verified counterweight: the **13,454 Formula and Equation objects were not
touched** — 0 with a `latex_source` twin, 0 with changed `latex`. So the formula
register is clean; only maths *inside translated sentences* moved.

## 6. Coverage is the registers, not the work

Pages 80–99 and 100–137 of volume 3. The arguments of volumes 1, 2 and the
Dröscher companion contribute extraction figures and citation targets only —
about 1,500 prose units and 13,454 formulas are drilled and searchable but
unwritten. If any page reads as though the volumes had been *read*, that is a
defect; flag it.

## 7. Two register formulas ship unrendered

Their OCR contains a character KaTeX refuses in strict mode. Shown verbatim with
the scan as authority rather than as a broken render.

## 8. Rights

The concept pages reproduce a published reference work's definitions in full, in
translation, and the register pages carry 261 scans of its formulas. This is
noted in the README. It is a rights question, not a correctness one, and it was
the owner's decision to publish.

## Questions I would like answered

1. Pick ten concept pages at random: does the English say what the German says?
2. Does any `→` link point at a term the authors did not mean?
3. Is any formula-register LaTeX a misreading of the scan beside it?
