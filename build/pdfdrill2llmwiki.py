#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""pdfdrill2llmwiki — project a drilled document into an llmwiki workspace.

pdfdrill already builds a COMPLETE projection of the document: `<bibkey>.tiddlers.json`
holds every paragraph, formula, equation, table, figure, footnote and reference,
with the reading order expressed as transclusion markers inside the prose:

    ... the transcoordinates {{bh2_FO0001||FO}} and {{bh2_FO0002||FO}} are ...

This reads that projection and re-expresses it in llmwiki's dialect: standard
markdown links, `$…$` maths, one page per document page, and a separate page for
every non-textual element. Nothing is re-derived from the PDF and nothing is
summarised — the wiki is the document's own structure.

    pdfdrill2llmwiki --doc <drill-folder> --wiki <workspace>/wiki [--lang en]

Marker handling (pdfdrill template -> llmwiki):

    ||FO       inline formula      -> $latex$ in the prose
    ||EQBLOCK  display equation    -> $$latex$$ + link to its own page
    ||TAB      table               -> link to its own page
    ||DIA/PIC  figure              -> link to its own page
    ||SN/FN    side/foot-note      -> link to its own page
    ||CIT      citation            -> link to the reference page
    ||PARA/LI  prose               -> inlined in reading order

Inline formulas are inlined rather than given pages of their own: there are
9,744 of them in one volume, and a formula inside a sentence is part of the
sentence. Everything that stands alone on the printed page gets a page here.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
from collections import defaultdict

MARKER = re.compile(r"\{\{([^}|]+)\|\|([A-Z]+)\}\}")
ELEMENT_KINDS = {                      # tag -> (folder, human name)
    "equation": ("equations", "Equation"),
    "table": ("tables", "Table"),
    "diagram": ("figures", "Diagram"),
    "picture": ("figures", "Figure"),
    "footnote": ("notes", "Footnote"),
    "sidenote": ("notes", "Sidenote"),
}


def tags_of(t):
    return set((t.get("tags") or "").split())


def load(doc):
    files = sorted(doc.glob("*.tiddlers.json"))
    if not files:
        sys.exit(f"no <bibkey>.tiddlers.json in {doc} — run: pdfdrill tiddlers <pdf>")
    tids = json.load(open(files[0], encoding="utf-8"))
    return tids, {t["title"]: t for t in tids}


def math_to_dollar(s):
    s = re.sub(r"\\\((.+?)\\\)", lambda m: f"${m.group(1).strip()}$", s or "", flags=re.S)
    return re.sub(r"\\\[(.+?)\\\]", lambda m: f"$$\n{m.group(1).strip()}\n$$", s, flags=re.S)


def validate(exprs, vendor):
    """Ask KaTeX which readings it refuses; those are shown as text, not broken renders."""
    if not exprs:
        return set()
    r = subprocess.run(["node", str(vendor)], text=True, capture_output=True,
                       input=json.dumps({"items": [{"id": e, "latex": e} for e in exprs]}))
    return set(json.loads(r.stdout)["bad"]) if r.returncode == 0 else set()


def resolve(text, by, page_of, bad, depth):
    """Replace pdfdrill's transclusion markers with llmwiki equivalents."""
    up = "../" * depth
    used = set()

    def repl(m):
        title, tpl = m.group(1).strip(), m.group(2)
        t = by.get(title)
        if t is None:
            return ""
        if tpl == "FO":
            lx = (t.get("latex") or "").strip()
            if not lx:
                return ""
            return f"`{lx}`" if lx in bad else f"${lx}$"
        if tpl in ("PARA", "LI"):
            return resolve(t.get("text") or "", by, page_of, bad, depth)[0]
        folder = ELEMENT_KINDS.get(next((k for k in ELEMENT_KINDS if k in tags_of(t)), ""), None)
        if folder:
            used.add(title)
            label = t.get("refnum") or t.get("caption") or title
            return f"[{label}]({up}{folder[0]}/{title}.md)"
        if tpl == "CIT":
            used.add(title)
            return f"[{t.get('citekey') or title}]({up}references/{title}.md)"
        return ""

    return MARKER.sub(repl, text or ""), used


def write(path, front, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = ["---"] + [f"{k}: {v}" for k, v in front.items() if v not in (None, "")] + ["---", ""]
    path.write_text("\n".join(fm) + "\n".join(body).rstrip() + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--doc", required=True, help="drilled folder under the pdfdrill library")
    ap.add_argument("--wiki", required=True, help="the workspace's wiki/ directory")
    ap.add_argument("--title", default=None, help="human title for the document")
    ap.add_argument("--vendor", default=None, help="path to validate_latex.cjs")
    a = ap.parse_args()

    doc, W = pathlib.Path(a.doc).expanduser(), pathlib.Path(a.wiki).expanduser()
    tids, by = load(doc)
    bib = next((t for t in tids if "document" in tags_of(t)), {})
    key = (bib.get("title") or doc.name).split("_")[0]
    bibkey = next((t.get("tags", "").split()[-1] for t in tids if "page" in tags_of(t)), doc.name)
    title = a.title or doc.name
    vendor = pathlib.Path(a.vendor or (pathlib.Path(__file__).parent / "validate_latex.cjs"))

    # every inline formula, validated once
    bad = validate(sorted({(t.get("latex") or "").strip() for t in tids
                           if (t.get("latex") or "").strip()}), vendor)

    paras = [t for t in tids if {"paragraph", "listitem"} & tags_of(t)]
    page_of = {t["title"]: (t.get("page") or "").lstrip("0") or "0" for t in tids}
    by_page = defaultdict(list)
    for p in paras:
        by_page[p.get("page") or "000"].append(p)
    heads = defaultdict(list)
    for s in tids:
        if "section" in tags_of(s) and s.get("caption"):
            heads[s.get("page") or "000"].append(s)

    root = W / bibkey
    n_pages = n_elem = n_ref = 0
    referenced = set()

    for page in sorted(by_page):
        body = []
        for s in heads.get(page, []):
            body += ["#" * min(int(s.get("level") or 1), 4) + " " + s["caption"].strip(), ""]
        for p in by_page[page]:
            txt, used = resolve(p.get("text") or "", by, page_of, bad, 1)
            referenced |= used
            body += [math_to_dollar(txt).strip(), ""]
            src = (p.get("text_source") or "").strip()
            if src and src != (p.get("text") or ""):
                s2, _ = resolve(src, by, page_of, bad, 1)
                q = "\n".join("> " + l if l.strip() else ">"
                              for l in math_to_dollar(s2).strip().split("\n"))
                body += ['<!--okf:source lang="de"-->', "> **Original**", ">", q,
                         "<!--/okf:source-->", ""]
        if not any(b.strip() for b in body):
            continue
        lang = next((p.get("translated_lang") for p in by_page[page] if p.get("translated_lang")), None)
        write(root / "pages" / f"p{page}.md",
              {"title": f'"{title} — page {int(page)}"', "type": "page",
               "tags": f"[{bibkey}, page]", "sources": f"[{bibkey}]", "page": int(page),
               "lang": lang, "lang_source": "de" if lang else None},
              body + ["", "## Source", "",
                      f"[{title}](../../sources/{bibkey}.md), page {int(page)}."])
        n_pages += 1

    # a page for every element that stands alone on the printed page
    for t in tids:
        kind = next((k for k in ELEMENT_KINDS if k in tags_of(t)), None)
        if not kind:
            continue
        folder, human = ELEMENT_KINDS[kind]
        pg = (t.get("page") or "").lstrip("0")
        body = [f"# {human} {t.get('refnum') or t['title']}", ""]
        lx = (t.get("latex") or "").strip()
        if lx:
            body += (["```latex", lx, "```"] if lx in bad else ["$$", lx, "$$"]) + [""]
        elif t.get("text"):
            txt, _ = resolve(t["text"], by, page_of, bad, 1)
            body += [math_to_dollar(txt).strip(), ""]
        if t.get("caption"):
            body += [f"*{t['caption'].strip()}*", ""]
        has_page = pg and (root / "pages" / f"p{t.get('page')}.md").exists()
        body += ["## Appears on", "",
                 f"[page {pg}](../pages/p{t.get('page')}.md)" if has_page
                 else (f"page {pg} (no prose on that page)" if pg else "—"),
                 "", "## Source", "",
                 f"[{title}](../../sources/{bibkey}.md)"]
        write(root / folder / f"{t['title']}.md",
              {"title": f'"{t["title"]}"', "type": kind, "tags": f"[{bibkey}, {kind}]",
               "sources": f"[{bibkey}]", "page": int(pg) if pg else None,
               "refnum": f'"{t.get("refnum")}"' if t.get("refnum") else None}, body)
        n_elem += 1

    # references, with their BibTeX
    for t in tids:
        if "citation" not in tags_of(t) and not t.get("citekey"):
            continue
        body = [f"# {t.get('citekey') or t['title']}", ""]
        if t.get("text"):
            body += [t["text"].strip(), ""]
        bt = t.get("bibtex")
        if bt:
            body += ["## BibTeX", "", "```bibtex", bt.strip(), "```", ""]
        body += ["## Source", "", f"[{title}](../../sources/{bibkey}.md)"]
        write(root / "references" / f"{t['title']}.md",
              {"title": f'"{t.get("citekey") or t["title"]}"', "type": "reference",
               "tags": f"[{bibkey}, reference]", "sources": f"[{bibkey}]",
               "citekey": t.get("citekey")}, body)
        n_ref += 1

    # the document's own source page
    counts = {}
    for k in ELEMENT_KINDS:
        d = root / ELEMENT_KINDS[k][0]
        counts[k] = len(list(d.glob(f"*.md"))) if d.exists() else 0
    body = [f"# {title}", "",
            f"Projected from a `pdfdrill` docmodel (bibkey `{bibkey}`) by "
            "`pdfdrill2llmwiki`. The wiki *is* the document's structure — every page "
            "below is the document's own text, and nothing was summarised.", "",
            "## What is here", "", "| | |", "|---|---|",
            f"| document pages | {n_pages} |",
            f"| equations | {counts.get('equation', 0)} |",
            f"| tables | {counts.get('table', 0)} |",
            f"| figures | {counts.get('diagram', 0) + counts.get('picture', 0)} |",
            f"| notes | {counts.get('footnote', 0) + counts.get('sidenote', 0)} |",
            f"| references | {n_ref} |", "",
            "Inline formulas are set in the prose as `$…$` rather than given pages of "
            "their own; everything that stands alone on the printed page has a page here.", "",
            "## Pages", "",
            ", ".join(f"[p{int(f.stem[1:])}](../{bibkey}/pages/{f.name})"
                      for f in sorted((root / "pages").glob("*.md"))[:40])
            + (", …" if n_pages > 40 else ""), ""]
    if n_ref:
        body += ["## References", "",
                 ", ".join(f"[{f.stem.split('REF_')[-1]}](../{bibkey}/references/{f.name})"
                           for f in sorted((root / "references").glob("*.md"))), ""]
    write(W / "sources" / f"{bibkey}.md",
          {"title": f'"{title}"', "type": "source", "tags": f"[{bibkey}, source]",
           "bibkey": bibkey}, body)

    print(f"{bibkey}: {n_pages} document pages, {n_elem} element pages, {n_ref} references"
          f"  ({len(bad)} formula readings KaTeX refuses, shown as text)")
    return dict(bibkey=bibkey, pages=n_pages, elements=n_elem, references=n_ref)


if __name__ == "__main__":
    main()
