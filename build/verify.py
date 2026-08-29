#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Emit audit/verification.json — the checks an auditor would otherwise re-derive.

Everything here is measured from the working tree. Run it before publishing:

    python3 build/verify.py
"""
import json
import pathlib
import posixpath
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = ROOT / "wiki"


def pages():
    return {p.relative_to(W).as_posix(): p for p in W.rglob("*.md")}


def link_check(ps):
    broken = []
    for rel, p in ps.items():
        base = str(pathlib.PurePosixPath(rel).parent)
        txt = p.read_text(encoding="utf-8")
        for _, tgt in re.findall(r"\[([^\]]*)\]\(([^)]+\.md)\)", txt):
            if posixpath.normpath(posixpath.join(base, tgt)) not in ps:
                broken.append({"page": rel, "target": tgt, "kind": "link"})
        for _, src in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", txt):
            if not (W / posixpath.normpath(posixpath.join(base, src))).exists():
                broken.append({"page": rel, "target": src, "kind": "image"})
    return broken


def math_check(ps):
    files = [str(p) for p in ps.values()]
    r = subprocess.run(["node", str(ROOT / "build" / "check_math.cjs"), *files],
                       capture_output=True, text=True)
    total = failed = 0
    for line in r.stdout.splitlines():
        m = re.search(r"(\d+) expressions .*?, (\d+) failed", line)
        if m:
            total += int(m.group(1))
            failed += int(m.group(2))
    return {"expressions": total, "failed": failed, "exit_code": r.returncode}


def by_kind(ps):
    out = {}
    for rel in ps:
        out[rel.split("/")[0] if "/" in rel else "root"] = \
            out.get(rel.split("/")[0] if "/" in rel else "root", 0) + 1
    return out


def orphans_and_backlinks(ps):
    targets = set()
    for rel, p in ps.items():
        base = str(pathlib.PurePosixPath(rel).parent)
        for _, tgt in re.findall(r"\[([^\]]*)\]\(([^)]+\.md)\)", p.read_text(encoding="utf-8")):
            targets.add(posixpath.normpath(posixpath.join(base, tgt)))
    return sorted(r for r in ps if r not in targets and r not in ("index.md", "overview.md"))


def main():
    ps = pages()
    built = ROOT / "HeimWiki.html"
    result = {
        "generated_by": "build/verify.py",
        "wiki": {
            "markdown_pages": len(ps),
            "pages_by_section": by_kind(ps),
            "crops": len(list((W / "crops").glob("*.jpg"))) + len(list((W / "gold" / "crops").glob("*.jpg"))),
        },
        "math": math_check(ps),
        "links": {"broken": link_check(ps)},
        "unreferenced_pages": orphans_and_backlinks(ps),
        "built_artifact": {
            "path": "HeimWiki.html",
            "exists": built.exists(),
            "bytes": built.stat().st_size if built.exists() else None,
        },
        "not_published": {
            "raw/": "verbatim third-party source extractions (copyrighted); gitignored",
            ".llmwiki/": "derived search index",
            "build/tw/": "TiddlyWiki working tree, rebuildable",
        },
    }
    out = ROOT / "audit" / "verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    m, l = result["math"], result["links"]["broken"]
    print(f"pages {len(ps)}  math {m['expressions']} expressions / {m['failed']} failed  "
          f"broken links {len(l)}  unreferenced {len(result['unreferenced_pages'])}")
    return 1 if (m["failed"] or l) else 0


if __name__ == "__main__":
    sys.exit(main())
