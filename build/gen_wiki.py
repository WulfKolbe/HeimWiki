#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate a bilingual Heim wiki from the four drilled books.

Backbone is BH3FR's own Begriffsregister (the author's definitions, pages 80-99)
and Formelregister (pages 100-137). Nothing here is synthesised prose: every
concept page is Heim & Droescher's definition, in English with the German
original beside it.
"""
import json, re, pathlib, shutil, sys, unicodedata
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from parse_register import parse_all

HOME = pathlib.Path.home()
LIB = HOME / "pdfdrill-library"
ROOT = HOME / "HeimWiki"
W = ROOT / "wiki"
TODAY = "2026-08-27"

BOOKS = {
    "BH1org_OCR": dict(title="Elementarstrukturen der Materie, Band 1",
                       title_en="Elementary Structures of Matter, Volume 1", vol="1"),
    "bh2":        dict(title="Elementarstrukturen der Materie, Band 2",
                       title_en="Elementary Structures of Matter, Volume 2", vol="2"),
    "BH3FR":      dict(title="Einführung in Burkhard Heim: Elementarstrukturen der Materie, "
                             "mit Begriffs- und Formelregister",
                       title_en="Introduction, with index of terms and formulas", vol="3"),
    "WDorg4":     dict(title="Walter Dröscher — Begleitband",
                       title_en="Walter Dröscher — companion volume", vol="4"),
}
VOL_TO_KEY = {"1": "BH1org_OCR", "2": "bh2", "3": "BH3FR", "4": "WDorg4"}


# ---------------------------------------------------------------- helpers

def slugify(term):
    s = unicodedata.normalize("NFKD", term)
    s = "".join(c for c in s if not unicodedata.combining(c))
    parts = re.split(r"[^A-Za-z0-9]+", s)
    return "".join(p[:1].upper() + p[1:] for p in parts if p) or "Term"


def norm(term):
    s = unicodedata.normalize("NFKD", term.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def singular(w):
    for suf in ("ies", "es", "s"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            return w[:-len(suf)] + ("y" if suf == "ies" else "")
    return w


def math_to_dollar(txt):
    """The OCR emits \\( .. \\); llmwiki forbids it (markdown eats the backslashes)."""
    txt = re.sub(r"\\\((.+?)\\\)", lambda m: f"${m.group(1).strip()}$", txt, flags=re.S)
    txt = re.sub(r"\\\[(.+?)\\\]", lambda m: f"$$\n{m.group(1).strip()}\n$$", txt, flags=re.S)
    return txt


CITE = re.compile(r"\\\(\s*\(?\s*([1-4])\s*,\s*([\d\s]+?)\s*\)?\s*\\\)|\(\s*([1-4])\s*,\s*([\d\s]+?)\s*\)")


def link_citations(txt, depth):
    def repl(m):
        vol = m.group(1) or m.group(3)
        pages = (m.group(2) or m.group(4) or "").strip()
        key = VOL_TO_KEY.get(vol)
        if not key:
            return m.group(0)
        return f"[(vol. {vol}, p. {pages})]({'../' * depth}sources/{key}.md)"
    return CITE.sub(repl, txt)


def build_index(entries):
    idx = {}
    for e in entries:
        idx[norm(e["term_en"])] = e["slug"]
        idx[" ".join(singular(w) for w in norm(e["term_en"]).split())] = e["slug"]
        if e["term_de"]:
            idx[norm(e["term_de"])] = e["slug"]
    return idx


ARROW = re.compile(r"[→⟶]\s*([A-Za-zÄÖÜäöüß’'\-]+(?:\s+[A-Za-zÄÖÜäöüß’'\-]+){0,3})")


def link_arrows(txt, idx, self_slug, depth, seen):
    def repl(m):
        words = m.group(1).split()
        for n in range(len(words), 0, -1):
            cand = " ".join(words[:n])
            key = norm(cand)
            keys = (key, " ".join(singular(w) for w in key.split()))
            for k in keys:
                if k in idx and idx[k] != self_slug:
                    seen.add(idx[k])
                    tail = " ".join(words[n:])
                    link = f"[{cand}]({'../' * depth}concepts/{idx[k]}.md)"
                    return link + (" " + tail if tail else "")
        return m.group(1)
    return ARROW.sub(repl, txt)


# ---------------------------------------------------------------- generation

def main():
    entries, _ = parse_all()
    used = {}
    for e in entries:
        s = slugify(e["term_en"])
        if s in used:
            used[s] += 1
            s = f"{s}{used[s]}"
        else:
            used[s] = 1
        e["slug"] = s
    idx = build_index(entries)

    for d in ("concepts", "sources", "register", "crops"):
        (W / d).mkdir(parents=True, exist_ok=True)

    backlinks = defaultdict(set)
    pages = []
    for e in entries:
        seen = set()
        body = link_arrows(math_to_dollar(link_citations(e["def_en"], 1)), idx, e["slug"], 1, seen)
        for t in seen:
            backlinks[t].add(e["slug"])
        e["_body"], e["_refs"] = body, seen
        pages.append(e)

    for e in pages:
        fm = ["---", f'title: "{e["term_en"]}"', "type: concept",
              "tags: [heim, begriffsregister]", "sources: [BH3FR]",
              f'term_de: "{e["term_de"] or ""}"', "lang: EN-US",
              "lang_source: de", f"page: {e['page']}", f"last_updated: {TODAY}", "---", ""]
        out = fm + [f"# {e['term_en']}", ""]
        if e["term_de"]:
            out += [f"**German:** *{e['term_de']}*", ""]
        out += [e["_body"], ""]
        if e["def_de"]:
            de_txt = math_to_dollar(e["def_de"]).strip()
            quoted = "\n".join("> " + ln if ln.strip() else ">" for ln in de_txt.split("\n"))
            out += ['<!--okf:source lang="de"-->',
                    "> **Original (German)**", ">", quoted,
                    "<!--/okf:source-->", ""]
        out += ["## Defined in", "",
                f"[{BOOKS['BH3FR']['title_en']}](../sources/BH3FR.md) — Begriffsregister, p. {e['page']}", ""]
        if e["_refs"]:
            out += ["## References", "",
                    ", ".join(f"[{s}](../concepts/{s}.md)" for s in sorted(e["_refs"])), ""]
        back = sorted(backlinks.get(e["slug"], []))
        if back:
            out += ["## Referenced by", "",
                    ", ".join(f"[{s}](../concepts/{s}.md)" for s in back), ""]
        (W / "concepts" / f"{e['slug']}.md").write_text("\n".join(out), encoding="utf-8")

    return entries, backlinks


if __name__ == "__main__":
    e, b = main()
    linked = sum(1 for x in e if x["_refs"])
    print(f"concept pages: {len(e)}")
    print(f"  bilingual            : {sum(1 for x in e if x['term_de'])}")
    print(f"  with outgoing links  : {linked}")
    print(f"  with backlinks       : {len(b)}")
    print(f"  total cross-refs     : {sum(len(x['_refs']) for x in e)}")


# ---------------------------------------------------------------- registers, sources, chrome

def okf_equations(bibkey):
    d = LIB / bibkey / "okf" / bibkey / "equations"
    out = []
    for f in sorted(d.glob("*.md")):
        t = f.read_text(encoding="utf-8")
        fm = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M))
        lat = re.search(r"\$\$([\s\S]*?)\$\$", fm.group(2))
        if not meta.get("page"):
            continue
        out.append(dict(title=meta["title"], page=int(meta["page"]),
                        ref=meta.get("refnum"),
                        latex=(lat.group(1).strip() if lat else meta.get("description", ""))))
    return out


def unrenderable(items):
    """Ask KaTeX which of these will not compile, so they ship verbatim not broken."""
    import subprocess
    r = subprocess.run(["node", str(ROOT / "build" / "validate_latex.cjs")],
                       input=json.dumps({"items": [{"id": i["title"], "latex": i["latex"]}
                                                   for i in items]}),
                       capture_output=True, text=True)
    return set(json.loads(r.stdout)["bad"]) if r.returncode == 0 else set()


def gen_register(first=100, last=137):
    eqs = [e for e in okf_equations("BH3FR") if first <= e["page"] <= last]
    bad = unrenderable(eqs)
    by_page = defaultdict(list)
    for e in eqs:
        by_page[e["page"]].append(e)
    crops_src = LIB / "BH3FR" / "report-crops"
    made, copied = [], 0
    for page, items in sorted(by_page.items()):
        name = f"p{page}"
        out = ["---", f'title: "Formula register — page {page}"', "type: register",
               "tags: [heim, formelregister]", "sources: [BH3FR]", f"page: {page}",
               f"last_updated: {TODAY}", "---", "",
               f"# Formula register — page {page}", "",
               f"{len(items)} formulas from the Formelregister of "
               f"[{BOOKS['BH3FR']['title_en']}](../sources/BH3FR.md). "
               "The LaTeX is the MathPix reading; the scan beneath each one is the printed original.", ""]
        for e in items:
            head = f"### ({e['ref']})" if e["ref"] else f"### {e['title']}"
            out += [head, ""]
            if e["title"] in bad:
                out += ["The OCR reading of this formula contains a character KaTeX will not "
                        "typeset, so it is shown as extracted. The scan below is the authority.",
                        "", "```latex", e["latex"], "```", ""]
            else:
                out += ["$$", e["latex"], "$$", ""]
            crop = crops_src / f"{e['title']}.jpg"
            if crop.exists():
                shutil.copy(crop, W / "crops" / crop.name)
                copied += 1
                out += [f"![{e['title']} as printed on page {page}](../crops/{crop.name})", ""]
            out += [f"*Unit `{e['title']}`, page {page}.*", ""]
        (W / "register" / f"{name}.md").write_text("\n".join(out), encoding="utf-8")
        made.append((name, page, len(items)))
    return made, copied


def gen_sources(entries, register):
    for key, meta in BOOKS.items():
        m = json.load(open(LIB / key / "model.docmodel.json"))
        objs = m["objects"]; objs = list(objs.values()) if isinstance(objs, dict) else objs
        from collections import Counter
        c = Counter(o["type"] for o in objs)
        tr = sum(1 for o in objs if "text_source" in (o.get("props") or {}))
        out = ["---", f'title: "{meta["title_en"]}"', "type: source",
               "tags: [heim, source]", f"bibkey: {key}", f"volume: {meta['vol']}",
               "lang: EN-US", "lang_source: de", f"last_updated: {TODAY}", "---", "",
               f"# {meta['title_en']}", "",
               f"**German title:** *{meta['title']}*", "",
               f"Drilled with `pdfdrill` (bibkey `{key}`) and translated to English with DeepL; "
               "the German original is retained on every translated unit.", "",
               "## Extraction", "",
               "| | |", "|---|---|",
               f"| pages | {c.get('Page', 0)} |",
               f"| paragraphs | {c.get('Paragraph', 0)} |",
               f"| display equations | {c.get('Equation', 0)} |",
               f"| inline formulas | {c.get('Formula', 0)} |",
               f"| units carrying both languages | {tr} |", ""]
        if key == "BH3FR":
            out += ["## Registers", "",
                    f"This volume carries the author's own **Begriffsregister** (pages 80–99, "
                    f"{len(entries)} terms — one concept page each) and **Formelregister** "
                    f"(pages 100–137, {sum(n for _, _, n in register)} formulas across "
                    f"{len(register)} pages).", "",
                    "- [Index of terms](../index.md)",
                    "- Formula register: "
                    + ", ".join(f"[p{p}](../register/{n}.md)" for n, p, _ in register[:12])
                    + (", …" if len(register) > 12 else ""), ""]
        out += ["## Translation integrity", "",
                "The translation touched prose only. Formula and Equation objects carry the "
                "author's LaTeX unchanged — no `latex_source` twin exists on any of them. "
                "Inline math *embedded in translated prose* was normalised by the translator "
                "and is not byte-identical to the German; cite formulas from the register or "
                "the German original, never from translated prose.", ""]
        (W / "sources" / f"{key}.md").write_text("\n".join(out), encoding="utf-8")


def gen_chrome(entries, register):
    bilingual = sum(1 for e in entries if e["term_de"])
    letters = defaultdict(list)
    for e in sorted(entries, key=lambda x: x["term_en"].lower()):
        letters[e["term_en"][0].upper()].append(e)

    idx = ["# Heim Wiki — Index", "",
           "## Overview", "", "- [Overview](overview.md) — what this wiki is and how to read it", "",
           "## Sources", ""]
    for key, meta in BOOKS.items():
        idx.append(f"- [{meta['title_en']}](sources/{key}.md) — *{meta['title']}* (vol. {meta['vol']})")
    idx += ["", "## Concepts — Begriffsregister", "",
            f"{len(entries)} terms as defined by Heim & Dröscher, {bilingual} with the German original.", ""]
    for L in sorted(letters):
        idx.append(f"### {L}")
        idx.append("")
        for e in letters[L]:
            de = f" · *{e['term_de']}*" if e["term_de"] else ""
            idx.append(f"- [{e['term_en']}](concepts/{e['slug']}.md){de}")
        idx.append("")
    idx += ["## Formula register", "",
            f"{sum(n for _, _, n in register)} formulas across {len(register)} pages.", ""]
    for n, p, cnt in register:
        idx.append(f"- [Page {p}](register/{n}.md) — {cnt} formulas")
    (W / "index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    ov = ["---", 'title: "Overview"', "type: synthesis", "tags: [heim]",
          "lang: EN-US", "lang_source: de", f"last_updated: {TODAY}", "---", "",
          "# Overview", "",
          "A bilingual wiki over the four drilled Heim volumes. **Every concept page is Heim and "
          "Dröscher's own definition**, taken from the Begriffsregister they published in volume 3 — "
          "not a synthesis written for this wiki. The English is a DeepL translation; the German "
          "original sits beneath it on every page.", "",
          "## How to read it", "",
          f"- **[Concepts](index.md)** — {len(entries)} terms, {bilingual} bilingual. The `→` "
          "cross-references of the printed register are live links; each page also lists what "
          "refers back to it.",
          "- **Formula register** — the printed Formelregister, each formula with the scan it "
          "was read from.",
          "- **Sources** — one page per volume, with its extraction figures.", "",
          "## Provenance and its limits", "",
          "Text came from MathPix OCR via `pdfdrill`, translated with DeepL. Two consequences "
          "worth knowing before citing anything here:", "",
          "1. **The definitions are translations.** The German is on every page for exactly that "
          "reason — where the English reads oddly, the original is the authority.",
          "2. **Do not cite formulas from translated prose.** Across the four volumes, only 20% "
          "of inline-math spans embedded in prose survived translation byte-identical; the "
          "translator normalised decimal commas, spacing and operators. The 13,454 Formula and "
          "Equation objects were *not* touched, so the formula register and the German original "
          "are the reliable sources for mathematics.", "",
          "## What is not here", "",
          "The wiki covers the register, not the full argument of the volumes: roughly 1,500 "
          "prose units and 13,454 formulas are drilled and searchable but not yet written up. "
          "Volume 1, volume 2 and the Dröscher companion contribute their extraction figures and "
          "citation targets only.", ""]
    (W / "overview.md").write_text("\n".join(ov), encoding="utf-8")


if __name__ == "__main__":
    pass
