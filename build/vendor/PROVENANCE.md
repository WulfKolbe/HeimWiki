# build/vendor — what is here, where it came from, how to re-fetch it

Vendored third-party code. Nothing in this repository builds it; 314 listed it
as source for that reason. This file records enough to restore it exactly.

## katex

| | |
|---|---|
| package | `katex` |
| version | **0.16.45** |
| licence | MIT © Khan Academy — see `katex/LICENSE`, unmodified |
| files | 170 |
| size | 3.5 MB |
| `dist/katex.min.js` sha256 | `e1c5d9e1b5b906881c40faf67950585a3f5d5adb4636d10e9678b9ba74b57dcc` |

**Why vendored rather than a dependency.** Two reasons, and the second is the
one that matters: the build must run offline, and the wiki must render with the
*same* KaTeX that llmwiki renders with, so a formula that compiles here compiles
there. This copy is byte-identical to
`~/llmwiki/web/node_modules/katex` (verified on `dist/katex.min.js`).

**What was pruned.** Only `.woff2` fonts are kept; the `.ttf` and `.woff`
duplicates were deleted, since every browser that can open the built wiki
supports woff2. `dist/fonts/` therefore holds one format, not three.

## Re-fetching it

```bash
npm pack katex@0.16.45           # -> katex-0.16.45.tgz
tar xzf katex-0.16.45.tgz        # -> package/
rm -rf build/vendor/katex && mv package build/vendor/katex
rm -f build/vendor/katex/dist/fonts/*.ttf build/vendor/katex/dist/fonts/*.woff
sha256sum build/vendor/katex/dist/katex.min.js   # must match the table above
```

Or, equivalently, copy it from any install of the same version:

```bash
cp -r <somewhere>/node_modules/katex build/vendor/katex
```

## Used by

- `build/prerender_math.cjs` — compiles every expression at build time, so a
  bad reading fails the build instead of rendering red
- `build/check_math.cjs` and `build/validate_latex.cjs` — the KaTeX gates
- the `tiddlywiki/katex` plugin renders in the browser; it ships its own copy
  and inlines its own fonts, so the built HTML does not depend on this directory
