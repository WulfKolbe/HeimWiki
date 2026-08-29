#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Parse the bilingual Begriffsregister out of BH3FR (pages 80-99).

English is the parsing authority: German capitalises every noun, so a
Title-case scan over the German absorbs the previous definition's tail into the
next term. Entry boundaries come from the English; the German term is then the
matching number of trailing words before its colon, and any prefix that scan
would have stolen is handed back to the previous German definition.
"""
import json, re, pathlib, sys, difflib, unicodedata

LIB = pathlib.Path.home() / "pdfdrill-library"
REG_FIRST, REG_LAST = 80, 99

ENTRY = re.compile(
    r"(?:(?<=\s)|^)([A-ZÄÖÜ][A-Za-zÄÖÜäöüß’'\-]*(?:[ ,\-][A-Za-zÄÖÜäöüß’'\-]+){0,4}):\s"
    r"(?=[A-ZÄÖÜa-zäöüß(\\])")


def split_entries(txt):
    txt = re.sub(r"\s+", " ", txt or "").strip()
    hits = list(ENTRY.finditer(txt))
    out = []
    for i, h in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(txt)
        out.append([h.group(1).strip(), txt[h.end():end].strip()])
    return out


def repair_german(de):
    """Move a stolen prefix off each German term back onto the previous definition."""
    for i in range(1, len(de)):
        words = de[i][0].split()
        if len(words) > 1:
            keep = min(len(words), max(1, len(de[i][0].split())))
            # a German register term is at most 3 words; anything longer is contamination
            if len(words) > 3:
                stolen, term = words[:-3], words[-3:]
                de[i - 1][1] = (de[i - 1][1] + " " + " ".join(stolen)).strip()
                de[i][0] = " ".join(term)
    return de


def align(en, de, en_terms_wordcount):
    """Trim each German term to the word count of its English counterpart."""
    for i, (term, _) in enumerate(de):
        if i < len(en_terms_wordcount):
            n = en_terms_wordcount[i]
            words = term.split()
            if len(words) > n:
                stolen, keep = words[:-n], words[-n:]
                if i > 0:
                    de[i - 1][1] = (de[i - 1][1] + " " + " ".join(stolen)).strip()
                de[i][0] = " ".join(keep)
    return de


def load():
    m = json.load(open(LIB / "BH3FR" / "model.docmodel.json"))
    objs = m["objects"]; objs = list(objs.values()) if isinstance(objs, dict) else objs
    return sorted(
        [x for x in objs if x["type"] in ("Paragraph", "ListItem")
         and REG_FIRST <= (x["props"].get("page") or 0) <= REG_LAST],
        key=lambda z: (z["props"].get("page", 0), z["props"].get("flow_index", 0)))


def fold(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def sim(a, b):
    return difflib.SequenceMatcher(None, fold(a), fold(b)).ratio()


def dp_align(en, de, gap=-0.35):
    """Needleman-Wunsch over the two ordered term lists; cognates anchor it."""
    n, m = len(en), len(de)
    S = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1): S[i][0] = S[i - 1][0] + gap
    for j in range(1, m + 1): S[0][j] = S[0][j - 1] + gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            S[i][j] = max(S[i - 1][j - 1] + sim(en[i - 1][0], de[j - 1][0]),
                          S[i - 1][j] + gap, S[i][j - 1] + gap)
    i, j, pairs = n, m, []
    while i > 0 and j > 0:
        if S[i][j] == S[i - 1][j - 1] + sim(en[i - 1][0], de[j - 1][0]):
            pairs.append((en[i - 1], de[j - 1])); i -= 1; j -= 1
        elif S[i][j] == S[i - 1][j] + gap:
            pairs.append((en[i - 1], None)); i -= 1
        else:
            j -= 1
    while i > 0:
        pairs.append((en[i - 1], None)); i -= 1
    return list(reversed(pairs))


def parse_all():
    entries, dropped = [], 0
    for obj in load():
        p = obj["props"]
        en = split_entries(p.get("text"))
        de = split_entries(p.get("text_source"))
        de = repair_german(de)
        if len(en) == len(de):
            de = align(en, de, [len(t.split()) for t, _ in en])
            for (te, dfe), (td, dfd) in zip(en, de):
                entries.append(dict(term_en=te, def_en=dfe, term_de=td, def_de=dfd,
                                    page=p.get("page")))
        else:
            for e, d in dp_align(en, de):
                if d is None:
                    entries.append(dict(term_en=e[0], def_en=e[1], term_de=None,
                                        def_de=None, page=p.get("page")))
                    dropped += 1
                else:
                    words = d[0].split()
                    n = len(e[0].split())
                    term_de = " ".join(words[-n:]) if len(words) > n else d[0]
                    entries.append(dict(term_en=e[0], def_en=e[1], term_de=term_de,
                                        def_de=d[1], page=p.get("page")))
    return entries, dropped


if __name__ == "__main__":
    e, d = parse_all()
    print(f"entries: {len(e)}   bilingual: {sum(1 for x in e if x['term_de'])}   english-only: {d}")
    for x in e[:6]:
        print(f"  {x['term_en']:34} | {x['term_de'] or '-'}")
    json.dump(e, open(pathlib.Path.home()/"HeimWiki"/"build"/"register.json", "w"),
              ensure_ascii=False, indent=1)
