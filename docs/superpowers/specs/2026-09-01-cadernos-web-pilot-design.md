# Cadernos Web — Pilot Design (Documentos de Peniche)

## Background

The source material is a 2010 Flash Player 8 CD-ROM ("Cadernos") containing
digitized facsimiles of Álvaro Cunhal's prison writings, produced during his
1949–1960 imprisonment (largely at the Peniche fortress). The disc ships five
"books" as separate Flash projector executables (Caderno 1, Caderno 28,
Caderno 43, Documentos de Peniche, Inventário), plus a combined "Cadernos"
compilation, all sharing one pool of ~281 page `.swf` files under `cfg/`.

The original app cannot run on modern hardware (Flash Player is dead;
Bottles/Wine did not get it running). This project reverse-engineers the
page assets and rebuilds the reader in plain HTML5, starting with the
smallest book that still exercises every core feature — **Documentos de
Peniche** (28 pages) — as a pilot before committing to the other four books.

## What the original does (from Manual.pdf + SWF inspection)

- Page-flip navigation: prev/next arrows, keyboard arrows, jump-to-page
  input box, total page counter.
- Zoom in/out, fullscreen toggle, page rotation (source pages are scans of
  handwritten notebooks, sometimes rotated for reading).
- A "transcriptions" panel: typed text of the handwritten page, with
  clickable page-number links that jump between transcription pages within
  the same document; already-visited/earlier pages render grayed out.
- Background audio toggle (Chopin recording) — confirmed to live in the
  combined "Cadernos" compilation only, not in the individual Peniche book.
  Out of scope for this pilot.
- An "índice interactivo" (interactive index) — confirmed to be a feature
  of the combined compilation app, not present in Peniche's own page list.
  Out of scope for this pilot.

## Reverse-engineering findings

Each book projector `.exe` is a standard Flash "make projector" binary: a
player stub followed by the movie's own SWF, addressable via the trailer at
the end of the file (magic `56 34 12 fa` + 4-byte little-endian length of
the appended SWF). That per-book SWF embeds a literal page-order manifest,
e.g. for Peniche:

```xml
<pages url_config="cfg/ip.cfg">
  <item thumb="cfg/237.swf" .../>
  <item thumb="cfg/238.swf" .../>
  ...
  <item thumb="cfg/263.swf" .../>
  <item thumb="cfg/branco.swf" .../> <!-- one blank page mid-book -->
</pages>
```

This gives an exact, authoritative page order without guessing from
filenames.

Each page `.swf` is one of two shapes, confirmed by tag-level inspection:

- **Plain page**: a single `DefineBitsJPEG2` (the full-page facsimile scan)
  placed once, one frame. No interactivity.
- **Transcription page**: the same background JPEG, plus a `DefineSprite`
  containing one Flash timeline frame per transcription page, each frame
  holding `DefineText` (the transcribed copy) and `DefineButton2` instances
  whose `on(press)` handlers are plain `gotoAndStop(N)` calls — i.e. the
  page-number links in the transcription panel are just an internal
  frame-jump table, trivial to recover.

`ffdec` (JPEXS Free Flash Decompiler, installed via `ffdec-bin` AUR package)
cleanly exports:
- the background JPEG as-is (`-export image`)
- transcription text as accurate, correctly-accented Portuguese Unicode
  text runs (`-export text`) — spot-checked against page 250/run 9, which
  reproduced a full, readable Cunhal legal petition
- button `on(press)` handlers as readable ActionScript (`-export script`),
  confirming the `gotoAndStop(N)` jump-table pattern above

Text runs export in character-ID order, not reading order, so the
extraction pipeline must reorder runs using each run's frame + placement
(depth/Y position) before writing final transcription text.

## Architecture

Two independent pieces, deliberately decoupled so the viewer has zero
runtime dependency on Flash tooling:

1. **Extraction pipeline** (offline, one-time per book): Python scripts
   driving the `ffdec` CLI headlessly, plus the already-recovered page
   manifests, producing static output files checked into the repo.
2. **Viewer** (what you actually use): a static site — plain HTML, CSS,
   and vanilla JavaScript. No framework, no bundler, no build step, no
   external CDN dependency. This is the direct answer to "simplest,
   most compatible, lasts a long time" — plain browser-native code has no
   dependency chain to rot.

### Extraction pipeline

```
extract/
  manifest_peniche.py     # hardcoded page order, recovered from the exe (above)
  extract_images.py       # ffdec -export image per page swf -> web/books/peniche/pages/NNN.jpg
  extract_transcriptions.py  # ffdec -export text + -export script per page swf,
                              # reorders text runs by frame/Y position,
                              # builds the gotoAndStop() jump table
  build_manifest.py       # writes web/books/peniche/manifest.json
```

Output, committed to the repo under `web/books/peniche/`:
- `pages/001.jpg` … `pages/028.jpg` — sequential, re-numbered from the
  original page manifest order (not the original swf filenames, which are
  non-sequential/global across all five books)
- `manifest.json` — ordered page list; each entry flags `type: "plain" |
  "blank" | "transcription"` and page dimensions
- `transcriptions.json` — for `transcription`-type pages: reconstructed
  text keyed by transcription-frame number, plus the frame jump table

### Viewer

```
web/
  index.html
  css/style.css
  js/viewer.js
```

`viewer.js` fetches `manifest.json` on load and renders the current page
image; all subsequent interaction is client-side only:

- prev/next buttons + `ArrowLeft`/`ArrowRight` keys
- jump-to-page number input + Enter, with a live "N / 28" counter
- zoom in/out via CSS `transform: scale()`
- rotate via CSS `transform: rotate()`
- fullscreen via the native Fullscreen API
- for `transcription`-type pages, a panel toggle that renders
  `transcriptions.json` text for the current page, with in-text page
  links wired to the recovered jump table; visited pages get a `.visited`
  CSS class (grayed out), tracked in-memory for the session

## Error handling

- **Build-time**: if a button's `gotoAndStop(N)` target isn't a valid
  frame in that page's transcription, log a warning and drop that one
  link rather than failing the whole page or book export.
- **Build-time**: if a page's SWF fails to parse (unexpected tag
  structure), skip that page with a warning, don't abort the batch — this
  lets us inspect and fix that one file without re-running everything.
- **Runtime**: if a page image 404s, show a plain "page unavailable"
  placeholder in the viewer instead of a broken-image icon.

## Testing

This is static content, not application logic, so testing is intentionally
lightweight:

- **Build-time validation**: `manifest.json` page count matches the
  expected 28; no dangling jump-table targets after the drop-and-warn step
  above.
- **Manual verification**: spot-check a sample of extracted transcription
  pages against the original swf's exported text output (already done for
  page 250 during design validation).
- **Manual browser walkthrough**: navigation (buttons, keyboard, jump box),
  zoom, rotate, fullscreen, and transcription panel (open/close, jump
  links, visited styling) in one current browser before calling the pilot
  done.

No automated test framework (e.g. Playwright) for the pilot — would be
disproportionate to a single 28-page static book. Worth reconsidering if
this pipeline is extended to all five books later.

## Explicitly out of scope for this pilot

- Background audio (Chopin track) — lives in the combined compilation app,
  not in Peniche's own pages.
- Interactive index ("índice interactivo") — same, belongs to the
  compilation app.
- The other four books (Caderno 1, Caderno 28, Caderno 43, Inventário) —
  pipeline should generalize to them once the pilot is validated, but
  building them out is a follow-up, not part of this design.
- Mobile/responsive layout — original was a desktop CD-ROM app; not a
  stated requirement here.
