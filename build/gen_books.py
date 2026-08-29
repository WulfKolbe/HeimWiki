#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bring all four Heim volumes into the wiki, not just the register volume.

Two page kinds, both machine-produced and both carrying their evidence:

  register/<bibkey>/pNNN.md   every NUMBERED equation on that page, with the
                              scan it was read from. No inference: a printed
                              equation number and a crop, or the equation is
                              not included.

  passages/<bibkey>/pNNN.md   the bilingual prose of a page the Begriffsregister
                              actually cites, English over German. Driven by the
                              authors' own (vol, page) cross-references, so the
                              register's citations resolve to the text they name.

Chapter pages are deliberately absent: these three volumes carry no Abstract
objects, and matching TOC titles against page text confirmed 0, 0 and 1 of them,
so a chapter boundary here would be a guess.
"""
import json
import pathlib
import re
import shutil
import subprocess
from collections import defaultdict

HOME = pathlib.Path.home()
LIB = HOME / "pdfdrill-library"
ROOT = HOME / "HeimWiki"
W = ROOT / "wiki"
TODAY = "2026-08-29"

BOOKS = {
    "BH1org_OCR": ("Elementary Structures of Matter, Volume 1", "1"),
    "bh2": ("Elementary Structures of Matter, Volume 2", "2"),
    "BH3FR": ("Introduction, with index of terms and formulas", "3"),
    "WDorg4": ("Walter Dröscher — companion volume", "4"),
}
VOL_TO_KEY = {v[1]: k for k, v in BOOKS.items()}


def okf_equations(bibkey):
    d = LIB / bibkey / "okf" / bibkey / "equations"
    out = []
    for f in sorted(d.glob("*.md")):
        t = f.read_text(encoding="utf-8")
        fm = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
        if not fm:
            continue
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M))
        if not (meta.get("page") and (meta.get("refnum") or "").strip()):
            continue          # numbered equations only
        lat = re.search(r"\$\$([\s\S]*?)\$\$", fm.group(2))
        out.append(dict(title=meta["title"], page=int(meta["page"]),
                        ref=meta["refnum"],
                        latex=(lat.group(1).strip() if lat else meta.get("description", ""))))
    return out


def unrenderable(items):
    r = subprocess.run(["node", str(ROOT / "build" / "validate_latex.cjs")], text=True,
                       capture_output=True,
                       input=json.dumps({"items": [{"id": i["title"], "latex": i["latex"]}
                                                   for i in items]}))
    return set(json.loads(r.stdout)["bad"]) if r.returncode == 0 else set()


def bad_expressions(texts):
    """Which inline expressions will KaTeX refuse? Validated in one batch."""
    exprs, seen = [], set()
    for s in texts:
        for e in re.findall(r"\$([^$\n]+?)\$", s):
            if e not in seen:
                seen.add(e); exprs.append(e)
    if not exprs:
        return set()
    r = subprocess.run(["node", str(ROOT / "build" / "validate_latex.cjs")], text=True,
                       capture_output=True,
                       input=json.dumps({"items": [{"id": e, "latex": e} for e in exprs]}))
    return set(json.loads(r.stdout)["bad"]) if r.returncode == 0 else set()


def demote_bad_math(txt, bad):
    """An OCR reading KaTeX refuses is shown as literal text, not as a broken render."""
    return re.sub(r"\$([^$\n]+?)\$",
                  lambda m: f"`{m.group(1)}`" if m.group(1) in bad else m.group(0), txt)


def math_to_dollar(txt):
    txt = re.sub(r"\\\((.+?)\\\)", lambda m: f"${m.group(1).strip()}$", txt or "", flags=re.S)
    return re.sub(r"\\\[(.+?)\\\]", lambda m: f"$$\n{m.group(1).strip()}\n$$", txt, flags=re.S)


def gen_register(bibkey):
    eqs = okf_equations(bibkey)
    if not eqs:
        return []
    bad = unrenderable(eqs)
    crops_src = LIB / bibkey / "report-crops"
    by_page = defaultdict(list)
    for e in eqs:
        by_page[e["page"]].append(e)
    out_dir = W / "register" / bibkey
    out_dir.mkdir(parents=True, exist_ok=True)
    title_en, vol = BOOKS[bibkey]
    made = []
    for page, items in sorted(by_page.items()):
        o = ["---", f'title: "Formulas — {bibkey} p. {page}"', "type: register",
             "tags: [heim, formulas]", f"sources: [{bibkey}]", f"page: {page}",
             f"volume: {vol}", f"last_updated: {TODAY}", "---", "",
             f"# Formulas — {title_en}, page {page}", "",
             f"{len(items)} numbered equation(s) from "
             f"[{title_en}](../../sources/{bibkey}.md). The LaTeX is the MathPix reading of "
             "the printed equation; the unit id under each one locates the scan in the "
             "drill folder.", ""]
        for e in items:
            o += [f"### ({e['ref']})", ""]
            if e["title"] in bad:
                o += ["The reading contains a character KaTeX will not typeset; shown as "
                      "extracted, with the scan as authority.", "", "```latex", e["latex"], "```", ""]
            else:
                o += ["$$", e["latex"], "$$", ""]
            # No scan images in the wiki: every equation here is LaTeX, and the
            # crops were indexed as separate documents, flooding Recent with
            # jpgs whose relative paths resolve to no wiki page. The unit id
            # below still points at the crop in the drill folder.
            o += [f"*Unit `{e['title']}`, page {page}.*", ""]
        (out_dir / f"p{page}.md").write_text("\n".join(o), encoding="utf-8")
        made.append((page, len(items)))
    return made


def cited_pages():
    """(volume, printed page) pairs the Begriffsregister itself cites."""
    want = defaultdict(set)
    for p in (W / "concepts").glob("*.md"):
        for vol, pages in re.findall(r"\[\(vol\.\s*([1-4]),\s*p\.\s*([\d\s]+)\)\]",
                                     p.read_text(encoding="utf-8")):
            for one in pages.split():
                want[vol].add(int(one))
    return want


def gen_passages(bibkey, pages, offset=0):
    """Bilingual prose for the pages the register cites."""
    m = json.load(open(LIB / bibkey / "model.docmodel.json"))
    objs = m["objects"]
    objs = list(objs.values()) if isinstance(objs, dict) else objs
    by_page = defaultdict(list)
    for x in objs:
        if x["type"] != "Paragraph":
            continue
        pr = x["props"]
        if pr.get("page") and (pr.get("text") or "").strip():
            by_page[pr["page"]].append(pr)
    out_dir = W / "passages" / bibkey
    out_dir.mkdir(parents=True, exist_ok=True)
    title_en, vol = BOOKS[bibkey]
    texts = []
    for printed in sorted(pages):
        for pr in by_page.get(printed + offset, []):
            texts.append(math_to_dollar(pr.get("text") or ""))
            texts.append(math_to_dollar(pr.get("text_source") or ""))
    bad = bad_expressions(texts)
    made = []
    for printed in sorted(pages):
        pdfp = printed + offset
        paras = by_page.get(pdfp) or []
        if not paras:
            continue
        o = ["---", f'title: "{bibkey} p. {printed}"', "type: passage",
             "tags: [heim, passage]", f"sources: [{bibkey}]",
             f"printed_page: {printed}", f"page: {pdfp}", f"volume: {vol}",
             "lang: EN-US", "lang_source: de", f"last_updated: {TODAY}", "---", "",
             f"# {title_en} — page {printed}", "",
             f"Cited from the Begriffsregister as `({vol}, {printed})`. "
             f"English is a DeepL translation; the German original follows each block "
             f"and is the authority.", ""]
        for pr in paras:
            o += [demote_bad_math(math_to_dollar(pr["text"]), bad).strip(), ""]
            src = (pr.get("text_source") or "").strip()
            if src and src != pr["text"]:
                q = "\n".join("> " + l if l.strip() else ">"
                              for l in demote_bad_math(math_to_dollar(src), bad).strip().split("\n"))
                o += ['<!--okf:source lang="de"-->', "> **Original (German)**", ">", q,
                      "<!--/okf:source-->", ""]
        o += ["## Source", "", f"[{title_en}](../../sources/{bibkey}.md), printed page {printed} "
              f"(PDF page {pdfp}).", ""]
        (out_dir / f"p{printed}.md").write_text("\n".join(o), encoding="utf-8")
        made.append(printed)
    return made


if __name__ == "__main__":
    (W / "crops").mkdir(parents=True, exist_ok=True)
    total_reg = 0
    for bk in BOOKS:
        made = gen_register(bk)
        total_reg += len(made)
        print(f"  register {bk:12} {len(made):3} pages, {sum(n for _, n in made):4} numbered equations")
    want = cited_pages()
    for vol, pages in sorted(want.items()):
        bk = VOL_TO_KEY[vol]
        made = gen_passages(bk, pages)
        print(f"  passages {bk:12} {len(made):3} of {len(pages)} cited pages resolved")
    print(f"  register pages total: {total_reg}")


# ---------------------------------------------------------------- chrome

def gen_chrome():
    """Rebuild index, overview and the four source pages for the new layout."""
    import collections
    concepts = sorted((W / "concepts").glob("*.md"), key=lambda p: p.stem.lower())
    reg = {bk: sorted((W / "register" / bk).glob("*.md"),
                      key=lambda p: int(p.stem[1:])) for bk in BOOKS}
    pas = {bk: sorted((W / "passages" / bk).glob("*.md"),
                      key=lambda p: int(p.stem[1:]))
           for bk in BOOKS if (W / "passages" / bk).exists()}

    def eqcount(bk):
        return sum(len(re.findall(r"^### \(", f.read_text(encoding="utf-8"), re.M))
                   for f in reg[bk])

    # --- source pages -------------------------------------------------
    for bk, (title_en, vol) in BOOKS.items():
        m = json.load(open(LIB / bk / "model.docmodel.json"))
        o = m["objects"]; o = list(o.values()) if isinstance(o, dict) else o
        c = collections.Counter(x["type"] for x in o)
        tr = sum(1 for x in o if "text_source" in (x.get("props") or {}))
        out = ["---", f'title: "{title_en}"', "type: source", "tags: [heim, source]",
               f"bibkey: {bk}", f"volume: {vol}", "lang: EN-US", "lang_source: de",
               f"last_updated: {TODAY}", "---", "", f"# {title_en}", "",
               f"Volume {vol}. Drilled with `pdfdrill` (bibkey `{bk}`) and translated to "
               "English with DeepL; the German original is kept on every translated unit.", "",
               "## Extraction", "", "| | |", "|---|---|",
               f"| pages | {c.get('Page', 0)} |",
               f"| paragraphs | {c.get('Paragraph', 0)} |",
               f"| display equations | {c.get('Equation', 0)} |",
               f"| inline formulas | {c.get('Formula', 0)} |",
               f"| units carrying both languages | {tr} |", ""]
        out += ["## In this wiki", "",
                f"- **Formulas** — {len(reg[bk])} pages, {eqcount(bk)} numbered equations, "
                "each with its scan: "
                + ", ".join(f"[p{p.stem[1:]}](../register/{bk}/{p.name})" for p in reg[bk][:10])
                + (", …" if len(reg[bk]) > 10 else "")]
        if bk in pas:
            out += [f"- **Cited passages** — {len(pas[bk])} pages the Begriffsregister names, "
                    "bilingual: "
                    + ", ".join(f"[p{p.stem[1:]}](../passages/{bk}/{p.name})" for p in pas[bk][:10])
                    + (", …" if len(pas[bk]) > 10 else "")]
        if bk == "BH3FR":
            out += ["- **Concepts** — the Begriffsregister, one page per term; see "
                    "[the index](../index.md)."]
        out += ["", "## What is not here", "",
                "The argument of this volume is not written up. Its prose is drilled, "
                "translated and searchable, but only the pages listed above are in the wiki.", "",
                "## Translation integrity", "",
                "The translation touched prose only — Formula and Equation objects carry the "
                "author's LaTeX unchanged. Inline maths *inside translated prose* was normalised "
                "by the translator and is not byte-identical to the German; cite formulas from "
                "the formula pages or the German original, never from translated prose.", ""]
        (W / "sources" / f"{bk}.md").write_text("\n".join(out), encoding="utf-8")

    # --- index --------------------------------------------------------
    letters = collections.defaultdict(list)
    for p in concepts:
        t = p.read_text(encoding="utf-8")
        title = re.search(r'^title:\s*"(.*)"', t, re.M).group(1)
        de = re.search(r'^term_de:\s*"(.*)"', t, re.M)
        letters[title[0].upper()].append((title, de.group(1) if de else "", p.stem))
    idx = ["# Heim Wiki — Index", "", "## Overview", "",
           "- [Overview](overview.md) — what this wiki is and how to read it", "",
           "## The four volumes", ""]
    for bk, (title_en, vol) in BOOKS.items():
        idx.append(f"- [{title_en}](sources/{bk}.md) — vol. {vol}; "
                   f"{len(reg[bk])} formula pages ({eqcount(bk)} equations)"
                   + (f", {len(pas[bk])} cited passages" if bk in pas else ""))
    idx += ["", "## Concepts — Begriffsregister", "",
            f"{len(concepts)} terms as defined by Heim & Dröscher.", ""]
    for L in sorted(letters):
        idx += [f"### {L}", ""]
        for title, de, stem in letters[L]:
            idx.append(f"- [{title}](concepts/{stem}.md)" + (f" · *{de}*" if de else ""))
        idx.append("")
    idx += ["## Formulas by volume", ""]
    for bk, (title_en, vol) in BOOKS.items():
        idx.append(f"### {title_en} — {len(reg[bk])} pages")
        idx.append("")
        idx.append(", ".join(f"[p{p.stem[1:]}](register/{bk}/{p.name})" for p in reg[bk]))
        idx.append("")
    if pas:
        idx += ["## Cited passages", ""]
        for bk, ps in pas.items():
            idx.append(f"### {BOOKS[bk][0]} — {len(ps)} pages")
            idx.append("")
            idx.append(", ".join(f"[p{p.stem[1:]}](passages/{bk}/{p.name})" for p in ps))
            idx.append("")
    (W / "index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    return {bk: (len(reg[bk]), eqcount(bk), len(pas.get(bk, []))) for bk in BOOKS}
