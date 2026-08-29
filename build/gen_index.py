#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate wiki/index.md from the wiki itself.

314 found this page had no generator: it was written once by a shell heredoc
that was never saved, so the build consumed an input nothing could rebuild.
This is that generator, reconstructed to reproduce the page byte-for-byte.

    python3 build/gen_index.py [--check]

--check regenerates into memory and diffs against the file on disk, exiting
non-zero if they differ — so CI can prove the page is still derivable.
"""
import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = ROOT / "wiki"

BOOKS = {
    "BH1org_OCR": ("Elementary Structures of Matter, Volume 1", "1"),
    "bh2": ("Elementary Structures of Matter, Volume 2", "2"),
    "BH3FR": ("Introduction, with index of terms and formulas", "3"),
    "WDorg4": ("Walter Dröscher — companion volume", "4"),
}


def count(bibkey, sub):
    d = W / bibkey / sub
    return len(list(d.glob("*.md"))) if d.exists() else 0


def build() -> str:
    rows = []
    for bk, (title, vol) in BOOKS.items():
        rows.append((bk, title, vol,
                     count(bk, "pages"), count(bk, "equations"), count(bk, "tables"),
                     count(bk, "figures"), count(bk, "notes"), count(bk, "references")))

    concepts = sorted((W / "concepts").glob("*.md"), key=lambda p: p.stem.lower())
    letters = collections.defaultdict(list)
    for p in concepts:
        t = p.read_text(encoding="utf-8")
        title = re.search(r'^title:\s*"(.*)"', t, re.M).group(1)
        de = re.search(r'^term_de:\s*"(.*)"', t, re.M)
        letters[title[0].upper()].append((title, de.group(1) if de else "", p.stem))

    out = ["# Heim Wiki — Index", "", "- [Overview](overview.md)", "",
           "## The four volumes", "",
           "| volume | pages | equations | tables | figures | notes | refs |",
           "|---|---|---|---|---|---|---|"]
    for bk, title, vol, pg, eq, tb, fg, nt, rf in rows:
        out.append(f"| [{title}](sources/{bk}.md) | {pg} | {eq} | {tb} | {fg} | {nt} | {rf} |")
    out += ["", f"Every page of every volume is here: {sum(r[3] for r in rows)} document pages "
            f"carrying the text itself, {sum(r[4] for r in rows)} equations, "
            f"{sum(r[5] for r in rows)} tables, {sum(r[6] for r in rows)} figures and "
            f"{sum(r[7] for r in rows)} notes on pages of their own.", "",
            "## Concepts — Begriffsregister", "",
            f"{len(concepts)} terms as defined by Heim & Dröscher in volume 3.", ""]
    for L in sorted(letters):
        out += [f"### {L}", ""]
        for title, de, stem in letters[L]:
            out.append(f"- [{title}](concepts/{stem}.md)" + (f" · *{de}*" if de else ""))
        out.append("")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="diff against the file on disk instead of writing it")
    a = ap.parse_args()
    text = build()
    target = W / "index.md"
    if a.check:
        on_disk = target.read_text(encoding="utf-8") if target.exists() else ""
        if on_disk == text:
            print(f"index.md is reproducible ({len(text):,} bytes, byte-identical)")
            return 0
        print("index.md DIFFERS from what the generator produces", file=sys.stderr)
        import difflib
        for line in list(difflib.unified_diff(on_disk.splitlines(), text.splitlines(),
                                              "on disk", "generated", lineterm=""))[:20]:
            print(line, file=sys.stderr)
        return 1
    target.write_text(text, encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)} ({len(text):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
