# Cadernos Web — Multi-Book Expansion Design

## Background

This extends the "Documentos de Peniche" pilot (see
`docs/superpowers/specs/2026-09-01-cadernos-web-pilot-design.md`) to the
remaining four standalone books on the disc: Caderno 1, Caderno 28,
Caderno 43, and Inventário. The pilot validated the extraction pipeline
and viewer approach on the smallest, most uniform book (28 pages, all
transcription pages except one blank). This design covers what changes
to generalize the pipeline and viewer to all five books, plus a
correction to a scope call the pilot spec got wrong (background audio).

## Findings: the other four books' real structure

Each book projector `.exe` embeds its own page-order manifest the same
way Peniche's does (see the pilot spec's "Reverse-engineering findings"
section for the trailer format). One correction to that recipe: the
appended movie's start offset is `trailer_idx - length`, not
`len(file) - length` — the original recipe happened to work for Peniche's
already-extracted per-page `cfg/*.swf` files, but re-deriving the
*book-level* movie from the `.exe` trailer requires the corrected offset
(verified: `trailer_idx - length` produces a valid `FWS` signature for
all five projectors; the earlier formula was off by exactly the 8-byte
trailer size).

Live extraction against the real disc found:

| Book | Pages | Plain (image only) | Transcription | Blank |
|---|---|---|---|---|
| Documentos de Peniche | 28 | 0 | 27 | 1 |
| Caderno 1 | 62 | 30 | 26 | 6 |
| Caderno 28 | 80 | 37 | 42 | 1 |
| Caderno 43 | 94 | 30 | 56 | 8 |
| Inventário | 4 | 4 | 0 | 0 |

The existing page-type model (`plain` / `transcription` / `blank`)
already covers all observed cases — no new page type is needed. Source
filenames in these books are not always sequential numbers: some carry
suffixes (`41_2`, `145_back`, `66h`, `79b`) and some numbers are skipped
entirely (e.g. Caderno 28 has no `107.swf`). This is cosmetic — the
pipeline follows whatever order each book's own `<pages>` XML specifies,
regardless of gaps or naming in the underlying filenames.

Blank pages in these books are not always named `branco`: several are
plain-numbered or suffixed files that turn out to contain only
`SetBackgroundColor` (white) with no image-defining tag, structurally
identical to Peniche's `branco.swf`. Blank-page detection therefore
generalizes to "no `DefineBits`/`DefineBitsJPEG2`/`DefineBitsJPEG3`/
`DefineBitsJPEG4`/`DefineBitsLossless`/`DefineBitsLossless2` tag
present" rather than relying on the filename.

No individual book's page pool contains an audio or interactive-index
asset — those remain confirmed out of scope for the *individual page
files* of all five books, consistent with the pilot's finding for
Peniche. However, see the correction below: the book-level *chrome*
movie (not the pages) does carry audio.

## Correction to prior scope call: background audio

The pilot spec stated background audio "lives in the combined
compilation app only, not in Peniche's own pages... out of scope." This
was incorrect. Every individual book's own top-level movie (the chrome
that hosts page navigation, not the page `.swf` files themselves)
embeds:

- A `DefineSound` tag (linkage name `"sitesound"`, ~166 KB, MP3-encoded)
  — byte-identical (same SHA-256) across all five books, so it is one
  shared asset, not five distinct tracks.
- Frame-1 ActionScript on every book's main timeline:
  `my_sound = new Sound(); my_sound.attachSound("sitesound");
  my_sound.start(0, 999); my_sound.setVolume(100);` — autoplaying,
  looping background music.
- A toolbar button (`_player_sound`, placed in the same sprite as the
  zoom/rotate/fullscreen buttons already reverse-engineered in the
  pilot) whose `on(release)` handler toggles `my_sound`'s volume between
  0 and 100 — i.e. a mute/unmute toggle, not a play/pause.

This means the already-shipped Peniche viewer is missing a real feature
from the original. This design adds it for all five books.

**Implementation:**

- Extract the shared audio once (`ffdec -export sound`, confirmed to
  produce a standard playable MP3) to `web/audio/sitesound.mp3` —
  referenced by every book's viewer instance, not duplicated per book.
- Add an `<audio loop>` element and a toolbar toggle button, in the same
  position as the original `_player_sound` button. Browsers block
  autoplaying audio with sound before user interaction, so playback
  starts **muted by default**; the toggle is the explicit opt-in
  closest to the original's "plays immediately, user can mute" behavior.
- The toggle button is **labeled**, not icon-only (e.g. "🔇 Música" /
  "🔊 Música"), so its purpose is visible without hovering.
- A **dismissible banner**, shown once per browser via `localStorage`
  (no cookies, no backend), appears on first visit to any book's viewer:
  "A edição original desta obra incluía música de fundo — pode ativá-la
  no botão 'Música' da barra de ferramentas." with a close (×) control;
  once dismissed it does not reappear.

## Manifest recovery: a new automated, tested module

Replaces the pilot's one-off manual process (hand-typed
`peniche_manifest.py`, derived from a one-time `strings` dump) with a
repeatable module: `extract/projector_manifest.py`.

Given a projector `.exe` path, it:

1. Locates the trailer (`56 34 12 fa` magic + 4-byte little-endian
   length) and extracts the embedded book movie SWF using the corrected
   offset (`trailer_idx - length`).
2. Parses the `<pages url_config="cfg/ip.cfg">...</pages>` XML embedded
   in that movie (present as literal ASCII in the SWF body, not exposed
   via `ffdec -export text`) into an ordered list of source filenames.
3. Classifies each source's page type by scanning its own `.swf`'s tags
   (reusing `extract/swf_tags.py`): no image-defining tag → `blank`;
   image tag + `DefineButton2` → `transcription`; image tag only →
   `plain`.
4. Returns the same `[{"source": ..., "type": ...}, ...]` shape
   `peniche_manifest.py` already hand-authors.

As a regression check, re-deriving Peniche's own manifest through this
module must produce a list identical to the existing hand-authored
`PENICHE_PAGES`.

## Multi-book file layout and viewer

- `web/index.html` becomes a library landing page: lists all five books
  (title, page count, a cover thumbnail reusing each book's own first
  page image), each linking to `web/viewer.html?book=<slug>`.
- The current single-book viewer (`index.html` + `viewer.js`) is renamed
  to `web/viewer.html`; `viewer.js` reads the `?book=` query param to
  determine which `web/books/<slug>/` folder to load `manifest.json`,
  `transcriptions.json`, and `pages/*.jpg` from. Slugs: `peniche`,
  `caderno1`, `caderno28`, `caderno43`, `inventario` — matching the
  existing `web/books/peniche/` folder naming.
- `manifest.json` gains one new field, `title` (e.g. "Documentos de
  Peniche"), so the library page can fetch all five `manifest.json`
  files and build its list without a separate registry file as a second
  source of truth.
- The viewer header gains a "← Biblioteca" link back to the landing
  page.
- The viewer additionally supports an optional `&page=N` query param for
  direct deep-links to a specific page, since routing is being touched
  anyway.
- `extract_images.py`, `extract_transcriptions.py`, and
  `build_manifest.py` need no logic changes — they already handle
  `plain`/`transcription`/`blank` correctly — only parameterization. A
  new small registry, e.g. `extract/books.py`, lists all five books'
  `.exe` paths and slugs; each script gains an optional `--book <slug>`
  argument and defaults to running for every book in the registry when
  omitted.

## Testing

- `projector_manifest.py` gets pytest coverage: unit tests against small
  crafted byte fixtures (trailer parsing, XML page-list parsing, type
  classification), following the existing `extract/` testing style, plus
  the Peniche-manifest regression check described above run against the
  real disc.
- No logic changes to `extract_images.py` / `extract_transcriptions.py`
  / `build_manifest.py` beyond parameterization — existing tests remain
  valid as-is.
- The library landing page and the audio feature get no automated tests,
  consistent with the existing project convention (no build step, no
  framework, no test framework for the viewer) — manual browser QA only.

## Explicitly out of scope

- The combined "Cadernos" compilation app (`Cadernos.exe`) and its
  interactive index ("índice interactivo") — confirmed to belong only to
  that separate app, not any of the five individual books.
- Per-book distinct audio — confirmed to be one shared track across all
  five books, not five distinct recordings.

## Rollout

This continues on the existing `peniche-pilot` branch, landing in the
already-open PR #1. Since scope has grown well beyond "the Peniche
pilot," the PR title and description will be updated once this work is
complete. Given the size of this change (new extraction module, four
more books' worth of data, the audio feature, and the library page),
implementation will follow a written task-by-task plan (via the
writing-plans skill) with the same per-task review process used for the
original pilot, not ad hoc changes.
