# Cadernos — Álvaro Cunhal's Prison Notebooks

A static, dependency-free web viewer for the facsimile notebooks Álvaro Cunhal
wrote while imprisoned in the Peniche fortress (1949–1960), rebuilt from an
old Flash CD-ROM release that no longer runs on modern machines.

Five books are included:

| Book                     | Pages |
| ------------------------ | ----: |
| Documentos de Peniche    |    28 |
| Caderno 1                |    62 |
| Caderno 28               |    80 |
| Caderno 43               |    94 |
| Inventário               |     4 |

## Why this exists

The original disc shipped each book as a Shockwave Flash projector — a
format that's effectively unplayable today without emulation. This project
reverse-engineers the projector executables and their embedded `.swf` page
files, extracts the page images and transcribed text they contain, and
serves the result as a plain web page that will keep working for as long as
browsers render HTML.

## Viewing the books

The site is pure static HTML/CSS/vanilla JavaScript — no framework, no
build step, no CDN dependency. Serve the `web/` directory with any static
file server and open it:

```sh
cd web
python3 -m http.server 8000
```

Then open `http://localhost:8000/` for the library landing page, or jump
straight into a book:

```
http://localhost:8000/viewer.html?book=peniche
http://localhost:8000/viewer.html?book=caderno1&page=12
```

Valid `book` slugs: `peniche`, `caderno1`, `caderno28`, `caderno43`,
`inventario`.

Each page shows the original facsimile image; pages that had a
transcription overlay in the original disc show the transcribed prose
alongside it. The original disc's background music is available via the
"Música" toggle in the viewer toolbar (muted by default).

## Project layout

```
web/                     the site — everything here is what gets served
  index.html             library landing page (lists all five books)
  viewer.html            the book viewer
  js/, css/              vanilla JS and stylesheets
  audio/sitesound.mp3    the disc's shared background-audio track
  books/<slug>/          per-book generated assets:
    manifest.json          page count, title, per-page type
    transcriptions.json    page number -> transcribed text
    pages/                 page facsimile images (JPEG)

extract/                 the extraction pipeline (Python)
  swf_tags.py              SWF tag-stream parsing primitives
  frame_mapping.py         character-ID-to-frame mapping
  text_filters.py          navigation-label filtering
  projector_manifest.py    recovers a book's page manifest directly from
                           its projector .exe and page pool
  extract_images.py        exports page images (with blank-page handling)
  extract_transcriptions.py  reconstructs transcription text
  extract_audio.py          extracts the shared background-audio track
  build_manifest.py         writes manifest.json
  books.py                  registry of all five books (slug -> exe path, title)
  manifests/                recovered page structure for each book
  tests/                    pytest suite (35 tests)
```

The raw `.swf`/`.exe` source files from the original disc are never
committed here — only the derived output (images, text, manifests) that the
pipeline produces from them.

## Running the extraction pipeline

Requires the source disc mounted locally and [JPEXS Free Flash
Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) (`ffdec`) on
your `PATH`. The pipeline itself only needs Pillow:

```sh
python3 -m venv .venv
.venv/bin/pip install -r extract/requirements.txt
```

Run the full pipeline for every book, or a single one with `--book`:

```sh
.venv/bin/python -m extract.build_manifest [--book <slug>]
.venv/bin/python -m extract.extract_images [--book <slug>]
.venv/bin/python -m extract.extract_transcriptions [--book <slug>]
```

Output is written into `web/books/<slug>/`.

## Testing

```sh
.venv/bin/python -m pytest extract/tests/
```

35 tests, covering the SWF parsing primitives and the manifest-recovery
pipeline. The viewer has no automated test suite by design (no framework,
no build step) — it's tested manually in-browser.

## Design history

`docs/superpowers/specs/` and `docs/superpowers/plans/` document how this
project was scoped and built: a single-book pilot (Documentos de Peniche)
first, then expanded to all five books plus the background-audio feature
once the pipeline proved out.

## License

Licensed under the [GNU Affero General Public License v3.0](LICENSE).
