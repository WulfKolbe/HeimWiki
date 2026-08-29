#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Turn ~/PGA/wiki/**/*.md into TiddlyWiki .tid files.

Tiddler title == markdown file stem, so [[WikiLinks]] resolve directly.
Relative markdown links (concepts/Foo.md) are rewritten to [[Text|Foo]].
"""
import re, sys, json, base64, pathlib, shutil, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
OUT = ROOT / "build" / "tw" / "tiddlers"

FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)
MDLINK = re.compile(r"\[([^\]]+)\]\((?:\./)?(?:[\w./-]*/)?([\w.-]+)\.md\)")
# A markdown image on its own line starts with "!", which TiddlyWiki reads as a
# heading before markdown-it sees it. Emit the image widget directly instead —
# same reason the math goes out as <$latex/>.
IMGSRC = re.compile(r"!\[([^\]]*)\]\((?:\.\./)?crops/([\w.-]+\.jpg)\)")


def frontmatter(text):
    m = FM.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, text[m.end():]


def tw_tags(meta, kind):
    raw = meta.get("tags", "").strip("[]")
    tags = [t.strip() for t in raw.split(",") if t.strip()]
    tags.append(kind)
    return " ".join(f"[[{t}]]" if " " in t else t for t in dict.fromkeys(tags))


def write_tid(title, body, tags, ttype="text/x-markdown", extra=None):
    OUT.mkdir(parents=True, exist_ok=True)
    head = [f"title: {title}", f"type: {ttype}", f"tags: {tags}"]
    for k, v in (extra or {}).items():
        head.append(f"{k}: {v}")
    safe = re.sub(r"[^\w.-]", "_", title)
    (OUT / f"{safe}.tid").write_text("\n".join(head) + "\n\n" + body, encoding="utf-8")


def prerender_math(docs):
    """Hand every markdown body to KaTeX; get HTML back plus the inlined stylesheet."""
    proc = subprocess.run(
        ["node", str(ROOT / "build" / "prerender_math.cjs")],
        input=json.dumps({"files": [{"path": k, "text": v} for k, v in docs.items()]}),
        capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit("math prerender failed:\n" + proc.stderr)
    return json.loads(proc.stdout)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)

    docs = {}
    for p in sorted(WIKI.rglob("*.md")):
        docs[p.as_posix()] = p.read_text(encoding="utf-8")
    rendered = prerender_math(docs)
    bodies = {f["path"]: f["text"] for f in rendered["files"]}

    n = 0
    for p in sorted(WIKI.rglob("*.md")):
        meta, body = frontmatter(bodies[p.as_posix()])
        kind = meta.get("type", {"index": "index", "log": "log"}.get(p.stem, "note"))
        title = {"index": "Index", "overview": "Overview", "log": "Log"}.get(p.stem, p.stem)
        body = IMGSRC.sub(
            lambda m: f'<$image source="crops/{m.group(2)}" tooltip="{m.group(1)}" class="pga-scan"/>',
            body)
        body = MDLINK.sub(lambda m: f"[[{m.group(1)}|{ {'index':'Index','overview':'Overview','log':'Log'}.get(m.group(2), m.group(2)) }]]", body)
        write_tid(title, body.strip() + "\n", tw_tags(meta, kind),
                  extra={"caption": meta["title"]} if meta.get("title") else None)
        n += 1

    # the immutable sources, so the single file is self-contained
    for p in sorted(RAW.glob("*.md")):
        write_tid(f"raw/{p.stem}", p.read_text(encoding="utf-8").strip() + "\n",
                  "raw source", ttype="text/plain",
                  extra={"caption": f"{p.name} (unmodified source)"})
        n += 1

    # wiki chrome
    write_tid("$:/SiteTitle", "Heim Wiki", "", ttype="text/vnd.tiddlywiki")
    write_tid("$:/SiteSubtitle", "Elementarstrukturen der Materie \u2014 bilingual", "", ttype="text/vnd.tiddlywiki")
    write_tid("$:/DefaultTiddlers", "[[Overview]]\n[[Index]]", "", ttype="text/vnd.tiddlywiki")
    write_tid("$:/config/markdown/renderWikiText", "true", "", ttype="text/vnd.tiddlywiki")

    # one tiddler per formula; the pages transclude these (see prerender_math.cjs)
    for title, latex in (rendered.get("math") or {}).items():
        write_tid(title, latex + "\n", "math", ttype="text/plain")
    if rendered.get("math"):
        print(f"math tiddlers: {len(rendered['math'])}")

    # crops referenced by the cite-into blocks, as real image tiddlers
    crops = sorted((WIKI / "crops").glob("*.jpg"))
    for c in crops:
        write_tid(f"crops/{c.name}", base64.b64encode(c.read_bytes()).decode(),
                  "gold crop", ttype="image/jpeg")
    if crops:
        print(f"images: {len(crops)} scan crops embedded as tiddlers")

    # the katex plugin ships its own stylesheet and inlines its fonts via <<datauri>>
    write_tid("$:/PGA/math.css",
              ".pga-math-display{margin:1em 0;overflow-x:auto}\n"
              ".pga-scan{display:block;max-width:100%;margin:.6em 0;padding:6px 10px;"
              "background:#fff;border:1px solid rgba(128,128,128,.35);border-radius:4px}\n"
              ".katex{font-size:1.05em}\n",
              "$:/tags/Stylesheet", ttype="text/css")

    print(f"wrote {n} content tiddlers + 5 system tiddlers")
    print(f"math: {rendered['inline']} inline + {rendered['display']} display "
          f"-> <$latex/> widgets, all compiled by KaTeX {rendered['katexVersion']}")


if __name__ == "__main__":
    main()
