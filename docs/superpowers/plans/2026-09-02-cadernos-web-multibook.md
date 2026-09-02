# Cadernos Web Multi-Book Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Peniche-pilot extraction pipeline and viewer to the
remaining four books (Caderno 1, Caderno 28, Caderno 43, Inventário),
add the previously-missed background-audio feature to all five books,
and replace the single-book viewer with a shared library landing page +
parameterized viewer.

**Architecture:** A new automated, tested `extract/projector_manifest.py`
module recovers each book's page manifest directly from its projector
`.exe` (replacing the pilot's one-off hand-typed manifest as the
*method*, while keeping the existing hand-authored Peniche list as a
regression check). The three existing pipeline scripts
(`build_manifest.py`, `extract_images.py`, `extract_transcriptions.py`)
are parameterized to loop over a small book registry instead of being
hardcoded to Peniche. The viewer becomes two pages: `index.html` (a
library landing page listing all five books) and `viewer.html` (the
existing viewer, now reading a `?book=` query param to know which
book's data to load), plus a shared `<audio>` background-music feature
with an explicit toggle and a one-time dismissible banner.

**Tech Stack:** Python 3 (stdlib + Pillow), pytest, `ffdec` CLI,
vanilla HTML/CSS/JS (no framework, no build step).

**Spec:** `docs/superpowers/specs/2026-09-02-cadernos-web-multibook-design.md`

## Global Constraints

- No raw `.swf`/`.exe` source files are ever committed — only derived
  output (`web/books/**`, `web/audio/sitesound.mp3`).
- Zero framework, zero build step, zero CDN for anything under `web/`.
- No automated JS test framework — manual browser QA only for viewer
  changes; Python changes get pytest coverage.
- All work happens on the existing `peniche-pilot` branch and feeds the
  already-open PR #1 — never push to `main` directly.
- `transcriptions.json`'s flat page-number-to-string schema (no
  `jump_table`/frame nesting) must be preserved for every book.
- The audio toggle must be a **labeled** control (not icon-only), and
  the first-visit banner must be dismissible and never reappear once
  dismissed (via `localStorage`).
- Background audio starts **muted by default** on every page load
  (browser autoplay restrictions); the toggle is the explicit opt-in.

---

### Task 1: Move the Peniche manifest into a `manifests` package

**Files:**
- Create: `extract/manifests/__init__.py`
- Create: `extract/manifests/peniche.py`
- Delete: `extract/peniche_manifest.py`
- Move: `extract/tests/test_peniche_manifest.py` → `extract/tests/test_manifests_peniche.py`
- Modify: `extract/build_manifest.py`
- Modify: `extract/extract_images.py`
- Modify: `extract/extract_transcriptions.py`

**Interfaces:**
- Produces: `extract.manifests.peniche.PAGES` (`list[dict]`, same shape
  as the old `PENICHE_PAGES`: `{"source": str, "type": str}`), for
  every later task.

- [ ] **Step 1: Create the `manifests` package with Peniche's data, renamed to `PAGES`**

Create `extract/manifests/__init__.py` (empty file, makes this a package).

Create `extract/manifests/peniche.py` with the exact content of the old
`extract/peniche_manifest.py`, renaming the constant from
`PENICHE_PAGES` to `PAGES` and updating the module docstring:

```python
"""Recovered page order and per-page type for Documentos de Peniche,
hand-derived from the disc's projector executable. See
extract/tests/test_manifests_peniche.py for the invariants this list
is expected to satisfy, and extract/projector_manifest.py for the
automated method used to derive (and regression-check) this list for
every other book."""

PAGES = [
    # ... copy the exact list of {"source": ..., "type": ...} dicts
    # from the current extract/peniche_manifest.py's PENICHE_PAGES,
    # unchanged.
]
```

Run: `git show HEAD:extract/peniche_manifest.py` to get the exact
current list to copy — do not retype it by hand, copy it verbatim
(only the constant name and docstring change).

- [ ] **Step 2: Delete the old module and rename its test file**

```bash
git rm extract/peniche_manifest.py
git mv extract/tests/test_peniche_manifest.py extract/tests/test_manifests_peniche.py
```

Edit `extract/tests/test_manifests_peniche.py` to import from the new
location and use the new name (all four existing assertions are
otherwise unchanged):

```python
from extract.manifests.peniche import PAGES


def test_total_page_count_is_28():
    assert len(PAGES) == 28


def test_first_and_last_pages():
    assert PAGES[0] == {"source": "237", "type": "transcription"}
    assert PAGES[-1] == {"source": "263", "type": "transcription"}


def test_exactly_one_blank_page():
    blanks = [p for p in PAGES if p["type"] == "blank"]
    assert blanks == [{"source": "branco", "type": "blank"}]


def test_no_plain_pages_in_this_book():
    # every non-blank Peniche page carries a transcription overlay
    assert all(p["type"] in ("transcription", "blank") for p in PAGES)
```

- [ ] **Step 3: Update the three pipeline scripts' imports**

In `extract/build_manifest.py`, `extract/extract_images.py`, and
`extract/extract_transcriptions.py`, replace:

```python
from extract.peniche_manifest import PENICHE_PAGES
```

with:

```python
from extract.manifests.peniche import PAGES as PENICHE_PAGES
```

(Keep the local name `PENICHE_PAGES` for now — Task 9 replaces these
scripts' Peniche-only logic with the multi-book loop and removes this
import entirely. This step is a pure rename, not a behavior change.)

- [ ] **Step 4: Run the full test suite and confirm everything still passes**

Run: `cd extract/.. && .venv/bin/python -m pytest extract/tests/ -v`
Expected: PASS, same test count as before this task (the rename moved
tests, it did not add or remove any).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Move Peniche manifest into extract/manifests package"
```

---

### Task 2: Book registry (`extract/books.py`)

**Files:**
- Create: `extract/books.py`
- Test: `extract/tests/test_books.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `extract.books.BOOKS` (`dict[str, dict]`), keyed by slug
  (`"peniche"`, `"caderno1"`, `"caderno28"`, `"caderno43"`,
  `"inventario"`), each value a dict with `"exe"` (`pathlib.Path` to
  the projector executable) and `"title"` (`str`, display title). Used
  by Task 7 (manifest generation) and Task 9 (pipeline parameterization).

- [ ] **Step 1: Write the failing test**

Create `extract/tests/test_books.py`:

```python
from extract.books import BOOKS


def test_registry_has_all_five_books():
    assert set(BOOKS.keys()) == {
        "peniche", "caderno1", "caderno28", "caderno43", "inventario",
    }


def test_every_entry_has_an_exe_path_and_a_title():
    for slug, entry in BOOKS.items():
        assert entry["exe"].suffix == ".exe"
        assert entry["title"]


def test_peniche_title_is_the_full_book_name():
    assert BOOKS["peniche"]["title"] == "Documentos de Peniche"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest extract/tests/test_books.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.books'`

- [ ] **Step 3: Write the registry**

Create `extract/books.py`:

```python
"""Registry of the five standalone book projectors on the disc: each
book's projector executable and its display title. Does not hold page
manifests directly (see extract/manifests/__init__.py's PAGES_BY_SLUG,
populated once every book's manifest exists)."""

from pathlib import Path

DISC_ROOT = Path("/run/media/user/Cadernos")

BOOKS = {
    "peniche": {
        "exe": DISC_ROOT / "4.Peniche.exe",
        "title": "Documentos de Peniche",
    },
    "caderno1": {
        "exe": DISC_ROOT / "1.Caderno_1.exe",
        "title": "Caderno 1",
    },
    "caderno28": {
        "exe": DISC_ROOT / "2.Caderno_28.exe",
        "title": "Caderno 28",
    },
    "caderno43": {
        "exe": DISC_ROOT / "3.Caderno_43.exe",
        "title": "Caderno 43",
    },
    "inventario": {
        "exe": DISC_ROOT / "5.Inventario.exe",
        "title": "Inventário",
    },
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest extract/tests/test_books.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add extract/books.py extract/tests/test_books.py
git commit -m "Add book registry mapping slugs to projector exe paths and titles"
```

---

### Task 3: Extract a book's movie SWF from its projector `.exe`

**Files:**
- Create: `extract/projector_manifest.py`
- Test: `extract/tests/test_projector_manifest.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `extract.projector_manifest.extract_book_movie(exe_path: Path) -> bytes`,
  used by Task 6.

- [ ] **Step 1: Write the failing test**

Create `extract/tests/test_projector_manifest.py`:

```python
import struct

import pytest

from extract.projector_manifest import extract_book_movie


def test_extracts_swf_bytes_using_trailer_offset(tmp_path):
    swf_body = b"FWS" + b"\x08" + b"fake swf content here"
    junk_prefix = b"\x00" * 100
    trailer = b"\x56\x34\x12\xfa" + struct.pack("<I", len(swf_body))
    exe_path = tmp_path / "fake.exe"
    exe_path.write_bytes(junk_prefix + swf_body + trailer)

    result = extract_book_movie(exe_path)

    assert result == swf_body


def test_raises_when_no_trailer_magic_present(tmp_path):
    exe_path = tmp_path / "no_trailer.exe"
    exe_path.write_bytes(b"just some random bytes, no magic here")
    with pytest.raises(ValueError):
        extract_book_movie(exe_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.projector_manifest'`

- [ ] **Step 3: Write the minimal implementation**

Create `extract/projector_manifest.py`:

```python
"""Recover a book's page manifest directly from its "make projector"
.exe, replacing the one-off manual process used for the Peniche pilot
with a repeatable, tested tool. See extract/manifests/peniche.py's
hand-authored list for the regression target this module is checked
against (Task 7)."""

import struct
from pathlib import Path

TRAILER_MAGIC = b"\x56\x34\x12\xfa"


def extract_book_movie(exe_path: Path) -> bytes:
    """Extract the embedded book movie SWF from a "make projector" .exe,
    using its trailer: a 4-byte magic number followed by a 4-byte
    little-endian length of the appended movie, located at the very end
    of the file."""
    data = exe_path.read_bytes()
    trailer_idx = data.rfind(TRAILER_MAGIC)
    if trailer_idx == -1:
        raise ValueError(f"no projector trailer found in {exe_path}")
    length = struct.unpack("<I", data[trailer_idx + 4:trailer_idx + 8])[0]
    swf_start = trailer_idx - length
    return data[swf_start:trailer_idx]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add extract/projector_manifest.py extract/tests/test_projector_manifest.py
git commit -m "Add projector trailer extraction (extract_book_movie)"
```

---

### Task 4: Parse the embedded page order from a book's movie

**Files:**
- Modify: `extract/projector_manifest.py`
- Modify: `extract/tests/test_projector_manifest.py`

**Interfaces:**
- Consumes: nothing new (operates on raw `bytes`, independent of Task 3).
- Produces: `extract.projector_manifest.parse_page_order(movie_bytes: bytes) -> list[str]`,
  used by Task 6.

- [ ] **Step 1: Write the failing test**

Append to `extract/tests/test_projector_manifest.py`:

```python
from extract.projector_manifest import parse_page_order


def test_parses_ordered_source_filenames_from_embedded_xml():
    movie_bytes = (
        b"some binary noise before it \x00\x01\x02"
        b'<pages url_config="cfg/ip.cfg">'
        b'<item thumb="cfg/7.swf" smoothing="false"/>'
        b'<item thumb="cfg/branco.swf" smoothing="false"/>'
        b'<item thumb="cfg/8.swf" smoothing="false"/>'
        b"</pages>"
        b"more binary noise after it"
    )

    result = parse_page_order(movie_bytes)

    assert result == ["7", "branco", "8"]


def test_raises_when_no_pages_block_present():
    with pytest.raises(ValueError):
        parse_page_order(b"no pages block in here at all")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: FAIL with `ImportError: cannot import name 'parse_page_order'`

- [ ] **Step 3: Write the minimal implementation**

Add to `extract/projector_manifest.py` (below the existing imports, add
`import re`; below `extract_book_movie`, add):

```python
PAGES_BLOCK_RE = re.compile(rb'<pages url_config="cfg/ip\.cfg">(.*?)</pages>', re.S)
ITEM_RE = re.compile(rb'thumb="cfg/([^"]+)\.swf"')


def parse_page_order(movie_bytes: bytes) -> list[str]:
    """Extract the ordered list of page source filenames (without the
    "cfg/" prefix or ".swf" suffix) from the <pages> XML embedded as
    literal ASCII text in a book's uncompressed movie SWF."""
    match = PAGES_BLOCK_RE.search(movie_bytes)
    if match is None:
        raise ValueError("no <pages> block found in movie bytes")
    items = ITEM_RE.findall(match.group(1))
    return [item.decode("ascii") for item in items]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add extract/projector_manifest.py extract/tests/test_projector_manifest.py
git commit -m "Add page-order XML parsing (parse_page_order)"
```

---

### Task 5: Classify a page's type from its own `.swf` tags

**Files:**
- Modify: `extract/projector_manifest.py`
- Modify: `extract/tests/test_projector_manifest.py`

**Interfaces:**
- Consumes: `extract.swf_tags.scan_tag_types(swf_path: str) -> set[int]`
  and `extract.swf_tags.DEFINE_BUTTON2` (both already exist, unchanged).
- Produces: `extract.projector_manifest.classify_page_type(swf_path: Path) -> str`
  (one of `"blank"`, `"plain"`, `"transcription"`), used by Task 6.

- [ ] **Step 1: Write the failing test**

Append to `extract/tests/test_projector_manifest.py`:

```python
from extract.projector_manifest import classify_page_type
from extract.tests.test_swf_tags import build_test_swf


def test_page_with_no_image_tag_is_blank(tmp_path):
    swf = build_test_swf([(9, b"\xff\xff\xff")])  # SetBackgroundColor only
    path = tmp_path / "blank.swf"
    path.write_bytes(swf)
    assert classify_page_type(path) == "blank"


def test_page_with_image_and_no_button_is_plain(tmp_path):
    swf = build_test_swf([(21, b"fake jpeg data")])  # DefineBitsJPEG2
    path = tmp_path / "plain.swf"
    path.write_bytes(swf)
    assert classify_page_type(path) == "plain"


def test_page_with_image_and_button2_is_transcription(tmp_path):
    swf = build_test_swf([(21, b"fake jpeg data"), (34, b"\x11\x22\x33")])
    path = tmp_path / "transcription.swf"
    path.write_bytes(swf)
    assert classify_page_type(path) == "transcription"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: FAIL with `ImportError: cannot import name 'classify_page_type'`

- [ ] **Step 3: Write the minimal implementation**

Add `from extract.swf_tags import scan_tag_types, DEFINE_BUTTON2` to the
top of `extract/projector_manifest.py`, and add:

```python
IMAGE_TAGS = {6, 20, 21, 35, 36, 90}  # DefineBits(JPEG)(2/3/4)/DefineBitsLossless(2)


def classify_page_type(swf_path: Path) -> str:
    """Classify a page .swf as "blank" (no image tag at all),
    "transcription" (image + clickable DefineButton2 overlay), or
    "plain" (image only, no overlay)."""
    tag_types = scan_tag_types(str(swf_path))
    if not (tag_types & IMAGE_TAGS):
        return "blank"
    if DEFINE_BUTTON2 in tag_types:
        return "transcription"
    return "plain"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add extract/projector_manifest.py extract/tests/test_projector_manifest.py
git commit -m "Add page-type classification (classify_page_type)"
```

---

### Task 6: Assemble a full book manifest from an exe + a page pool

**Files:**
- Modify: `extract/projector_manifest.py`
- Modify: `extract/tests/test_projector_manifest.py`

**Interfaces:**
- Consumes: `extract_book_movie` (Task 3), `parse_page_order` (Task 4),
  `classify_page_type` (Task 5) — all from this same module.
- Produces: `extract.projector_manifest.build_manifest_for_book(exe_path: Path, source_dir: Path) -> list[dict]`
  (same shape as `extract.manifests.peniche.PAGES`), used by Task 7.

- [ ] **Step 1: Write the failing test**

Append to `extract/tests/test_projector_manifest.py`:

```python
from extract.projector_manifest import build_manifest_for_book


def test_builds_manifest_from_exe_trailer_and_page_pool(tmp_path):
    source_dir = tmp_path / "cfg"
    source_dir.mkdir()
    (source_dir / "7.swf").write_bytes(build_test_swf([(9, b"\xff\xff\xff")]))
    (source_dir / "8.swf").write_bytes(build_test_swf([(21, b"jpeg")]))
    (source_dir / "9.swf").write_bytes(
        build_test_swf([(21, b"jpeg"), (34, b"btn")])
    )

    movie_bytes = (
        b'<pages url_config="cfg/ip.cfg">'
        b'<item thumb="cfg/7.swf"/><item thumb="cfg/8.swf"/><item thumb="cfg/9.swf"/>'
        b"</pages>"
    )
    trailer = b"\x56\x34\x12\xfa" + struct.pack("<I", len(movie_bytes))
    exe_path = tmp_path / "fake.exe"
    exe_path.write_bytes(movie_bytes + trailer)

    result = build_manifest_for_book(exe_path, source_dir)

    assert result == [
        {"source": "7", "type": "blank"},
        {"source": "8", "type": "plain"},
        {"source": "9", "type": "transcription"},
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_manifest_for_book'`

- [ ] **Step 3: Write the minimal implementation**

Add to `extract/projector_manifest.py`:

```python
def build_manifest_for_book(exe_path: Path, source_dir: Path) -> list[dict]:
    """Recover a book's ordered page manifest directly from its
    projector .exe and the pool of page .swf files in source_dir."""
    movie_bytes = extract_book_movie(exe_path)
    sources = parse_page_order(movie_bytes)
    pages = []
    for source in sources:
        swf_path = source_dir / f"{source}.swf"
        page_type = classify_page_type(swf_path)
        pages.append({"source": source, "type": page_type})
    return pages
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest extract/tests/test_projector_manifest.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Run the full suite and commit**

Run: `.venv/bin/python -m pytest extract/tests/ -v`
Expected: PASS, no regressions.

```bash
git add extract/projector_manifest.py extract/tests/test_projector_manifest.py
git commit -m "Add build_manifest_for_book, completing the projector_manifest tool"
```

---

### Task 7: Generate manifests for the four new books, with a Peniche regression check

**Files:**
- Create: `extract/manifests/caderno1.py`
- Create: `extract/manifests/caderno28.py`
- Create: `extract/manifests/caderno43.py`
- Create: `extract/manifests/inventario.py`
- Modify: `extract/manifests/__init__.py`

**Interfaces:**
- Consumes: `extract.books.BOOKS` (Task 2), `extract.projector_manifest.build_manifest_for_book` (Task 6).
- Produces: `extract.manifests.{caderno1,caderno28,caderno43,inventario}.PAGES`
  and `extract.manifests.PAGES_BY_SLUG` (`dict[str, list[dict]]`, one
  entry per slug in `extract.books.BOOKS`), used by Task 9.

This task runs the new tool against the real disc and, unlike prior
tasks, is not itself TDD (there is no new pure function to test — it is
a one-time generation + verification run, same pattern as the pilot's
original real-disc extraction task).

- [ ] **Step 1: Run the tool for all five books and print the results**

Run this from the repo root (with the disc mounted at
`/run/media/user/Cadernos`):

```bash
.venv/bin/python -c "
import json
from extract.books import BOOKS
from extract.projector_manifest import build_manifest_for_book

source_dir = BOOKS['peniche']['exe'].parent / 'cfg'
for slug, entry in BOOKS.items():
    pages = build_manifest_for_book(entry['exe'], source_dir)
    print(f'--- {slug}: {len(pages)} pages ---')
    print(json.dumps(pages, ensure_ascii=False))
"
```

- [ ] **Step 2: Regression-check the Peniche result against the hand-authored list**

Run:

```bash
.venv/bin/python -c "
from extract.books import BOOKS
from extract.manifests.peniche import PAGES
from extract.projector_manifest import build_manifest_for_book

source_dir = BOOKS['peniche']['exe'].parent / 'cfg'
derived = build_manifest_for_book(BOOKS['peniche']['exe'], source_dir)
assert derived == PAGES, 'mismatch between derived and hand-authored Peniche manifest'
print('Peniche regression check passed:', len(derived), 'pages')
"
```

Expected: prints `Peniche regression check passed: 28 pages` with no
`AssertionError`. If it fails, stop and investigate the mismatch before
proceeding — do not paper over a real discrepancy between the tool and
the known-good Peniche list.

- [ ] **Step 3: Save each of the four new books' output as a manifest module**

Using the exact `caderno1`/`caderno28`/`caderno43`/`inventario` output
from Step 1, create `extract/manifests/caderno1.py` (repeat the same
shape for the other three, each with the matching printed list from
Step 1):

```python
"""Page order and per-page type for Caderno 1, recovered automatically
from the disc's projector executable via extract/projector_manifest.py."""

PAGES = [
    # ... paste the exact list printed for "caderno1" in Step 1
]
```

- [ ] **Step 4: Populate the manifests package's slug-to-pages mapping**

Edit `extract/manifests/__init__.py` (currently empty) to:

```python
"""Per-book recovered page manifests, keyed by the same slugs used in
extract.books.BOOKS."""

from extract.manifests import caderno1, caderno28, caderno43, inventario, peniche

PAGES_BY_SLUG = {
    "peniche": peniche.PAGES,
    "caderno1": caderno1.PAGES,
    "caderno28": caderno28.PAGES,
    "caderno43": caderno43.PAGES,
    "inventario": inventario.PAGES,
}
```

- [ ] **Step 5: Sanity-check page counts match the reverse-engineering findings**

Run:

```bash
.venv/bin/python -c "
from extract.manifests import PAGES_BY_SLUG
for slug, pages in PAGES_BY_SLUG.items():
    print(slug, len(pages))
"
```

Expected: `peniche 28`, `caderno1 62`, `caderno28 80`, `caderno43 94`,
`inventario 4` — matching the table in the design spec. If any count is
off, re-check that step 1's exe path / source_dir was correct for that
book before proceeding.

- [ ] **Step 6: Run the full test suite and commit**

Run: `.venv/bin/python -m pytest extract/tests/ -v`
Expected: PASS, no regressions (this task adds no new tests, only data
modules).

```bash
git add extract/manifests/
git commit -m "Generate page manifests for the four remaining books

Derived automatically via extract/projector_manifest.py from each
book's projector .exe. Cross-checked: re-deriving Peniche's own
manifest through the same tool matches the existing hand-authored
list exactly."
```

---

### Task 8: Extract the shared background-audio asset

**Files:**
- Create: `extract/extract_audio.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `extract.extract_audio.extract_sound(swf_path: Path, linkage_name: str, dest_path: Path) -> None`,
  used by Task 11.

This function wraps an external `ffdec` subprocess call, the same way
`extract_images.py`'s `export_page_image` and
`extract_transcriptions.py`'s `_read_char_id_texts` already do — those
are verified only by real extraction runs, not unit tests, and this
follows the same established convention (there is no pure, deterministic
logic here worth isolating for a unit test beyond a subprocess call and
a glob).

- [ ] **Step 1: Write the module**

Create `extract/extract_audio.py`:

```python
"""Extract an embedded sound asset (by its SWF linkage/export name) from
a SWF file as a standalone playable file.

Usage:
    python3 -m extract.extract_audio SWF_PATH LINKAGE_NAME DEST_PATH
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def extract_sound(swf_path: Path, linkage_name: str, dest_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffdec", "-export", "sound", tmp, str(swf_path)],
            check=True,
            capture_output=True,
        )
        matches = [
            p for p in Path(tmp).glob(f"*{linkage_name}*") if p.suffix != ".wav"
        ]
        if not matches:
            raise RuntimeError(
                f"no exported sound matching '{linkage_name}' found for {swf_path}"
            )
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(matches[0], dest_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("swf_path", type=Path)
    parser.add_argument("linkage_name")
    parser.add_argument("dest_path", type=Path)
    args = parser.parse_args()
    extract_sound(args.swf_path, args.linkage_name, args.dest_path)
    print(f"wrote {args.dest_path}")
```

- [ ] **Step 2: Verify the module imports cleanly**

Run: `.venv/bin/python -c "import extract.extract_audio"`
Expected: no output, exit code 0.

- [ ] **Step 3: Run the full test suite and commit**

Run: `.venv/bin/python -m pytest extract/tests/ -v`
Expected: PASS, no regressions.

```bash
git add extract/extract_audio.py
git commit -m "Add extract_sound helper for pulling the shared audio asset"
```

---

### Task 9: Parameterize the pipeline scripts for all five books

**Files:**
- Modify: `extract/build_manifest.py`
- Modify: `extract/tests/test_build_manifest.py`
- Modify: `extract/extract_images.py`
- Modify: `extract/extract_transcriptions.py`

**Interfaces:**
- Consumes: `extract.books.BOOKS` (Task 2), `extract.manifests.PAGES_BY_SLUG` (Task 7).
- Produces: `build_manifest_data(pages: list[dict], title: str) -> dict`
  (title added to the existing signature), and `main(slugs: list[str] | None = None, ...)`
  on all three scripts, defaulting to every book in `BOOKS` when
  `slugs` is omitted. Used by Task 10 (real pipeline runs) and by the
  viewer's `manifest.json` consumers (Task 12).

- [ ] **Step 1: Write the failing test for the new `title` field**

Edit `extract/tests/test_build_manifest.py` to pass and assert on
`title`:

```python
from extract.build_manifest import build_manifest_data


def test_produces_one_entry_per_page_with_sequential_numbering():
    pages = [
        {"source": "237", "type": "transcription"},
        {"source": "branco", "type": "blank"},
        {"source": "238", "type": "transcription"},
    ]
    data = build_manifest_data(pages, "Documentos de Peniche")
    assert data["title"] == "Documentos de Peniche"
    assert data["page_count"] == 3
    assert data["pages"] == [
        {"number": 1, "image": "pages/1.jpg", "type": "transcription"},
        {"number": 2, "image": "pages/2.jpg", "type": "blank"},
        {"number": 3, "image": "pages/3.jpg", "type": "transcription"},
    ]


def test_image_filenames_are_zero_padded_to_total_width():
    pages = [{"source": str(i), "type": "plain"} for i in range(1, 11)]
    data = build_manifest_data(pages, "Some Book")
    assert data["pages"][0]["image"] == "pages/01.jpg"
    assert data["pages"][9]["image"] == "pages/10.jpg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest extract/tests/test_build_manifest.py -v`
Expected: FAIL with `TypeError: build_manifest_data() missing 1 required positional argument: 'title'`

- [ ] **Step 3: Rewrite `build_manifest.py`**

Replace the full content of `extract/build_manifest.py` with:

```python
"""Build web/books/<slug>/manifest.json for one or more books.

Usage:
    python3 -m extract.build_manifest [--book SLUG ...]

Omitting --book builds the manifest for every book in the registry.
"""

import argparse
import json
from pathlib import Path

from extract.books import BOOKS
from extract.extract_images import output_filename
from extract.manifests import PAGES_BY_SLUG

WEB_BOOKS_DIR = Path(__file__).parent.parent / "web" / "books"


def build_manifest_data(pages: list[dict], title: str) -> dict:
    total = len(pages)
    return {
        "title": title,
        "page_count": total,
        "pages": [
            {
                "number": index,
                "image": f"pages/{output_filename(index, total)}",
                "type": page["type"],
            }
            for index, page in enumerate(pages, start=1)
        ],
    }


def main(slugs: list[str] | None = None, web_books_dir: Path = WEB_BOOKS_DIR) -> None:
    for slug in slugs or BOOKS.keys():
        data = build_manifest_data(PAGES_BY_SLUG[slug], BOOKS[slug]["title"])
        output_path = web_books_dir / slug / "manifest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"wrote manifest for {slug}: {data['page_count']} pages -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", action="append", dest="slugs", choices=list(BOOKS.keys()))
    args = parser.parse_args()
    main(args.slugs)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest extract/tests/test_build_manifest.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Rewrite `extract_images.py`'s multi-book plumbing**

In `extract/extract_images.py`, keep `output_filename`,
`export_page_image`, `write_blank_placeholder`, and every existing
import (`argparse`, `shutil`, `subprocess`, `tempfile`, `pathlib.Path`,
`PIL.Image`) exactly as they are. Replace only the
`from extract.manifests.peniche import PAGES as PENICHE_PAGES` import
line (added in Task 1), the constants below it, `main()`, and the
`if __name__ == "__main__":` block, with:

```python
from extract.books import BOOKS
from extract.manifests import PAGES_BY_SLUG

DEFAULT_SOURCE_DIR = Path("/run/media/user/Cadernos/cfg")
WEB_BOOKS_DIR = Path(__file__).parent.parent / "web" / "books"
BLANK_PAGE_SIZE = (656, 856)  # matches the real facsimile scan dimensions


def main(slugs: list[str] | None = None, source_dir: Path = DEFAULT_SOURCE_DIR,
          web_books_dir: Path = WEB_BOOKS_DIR) -> None:
    for slug in slugs or BOOKS.keys():
        pages = PAGES_BY_SLUG[slug]
        output_dir = web_books_dir / slug / "pages"
        output_dir.mkdir(parents=True, exist_ok=True)
        total = len(pages)
        failures = []
        for index, page in enumerate(pages, start=1):
            dest = output_dir / output_filename(index, total)
            try:
                if page["type"] == "blank":
                    write_blank_placeholder(dest)
                else:
                    export_page_image(source_dir / f"{page['source']}.swf", dest)
                print(f"[{slug} {index}/{total}] {page['source']}.swf -> {dest.name}")
            except Exception as exc:
                print(f"warning: skipping {slug} page {index} ({page['source']}.swf): {exc}")
                failures.append(page["source"])
        if failures:
            print(f"{slug}: completed with {len(failures)} skipped page(s): {failures}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", action="append", dest="slugs", choices=list(BOOKS.keys()))
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    args = parser.parse_args()
    main(args.slugs, args.source)
```

(Remove the now-unused `from extract.manifests.peniche import PAGES as
PENICHE_PAGES` and old `DEFAULT_OUTPUT_DIR` constant from Task 1's
rename — this task supersedes them.)

- [ ] **Step 6: Rewrite `extract_transcriptions.py`'s multi-book plumbing**

In `extract/extract_transcriptions.py`, keep
`assemble_page_transcription`, `_read_char_id_texts`,
`build_transcription_for_page`, and every existing import (`argparse`,
`json`, `subprocess`, `tempfile`, `pathlib.Path`,
`extract.frame_mapping.map_char_ids_to_frames`,
`extract.swf_tags.decompress_swf`/`tags_start_offset`,
`extract.text_filters.is_navigation_label`) exactly as they are.
Replace only the
`from extract.manifests.peniche import PAGES as PENICHE_PAGES` import
line (added in Task 1), the constants below it, `main()`, and the
`if __name__ == "__main__":` block, with:

```python
from extract.books import BOOKS
from extract.manifests import PAGES_BY_SLUG

DEFAULT_SOURCE_DIR = Path("/run/media/user/Cadernos/cfg")
WEB_BOOKS_DIR = Path(__file__).parent.parent / "web" / "books"


def main(slugs: list[str] | None = None, source_dir: Path = DEFAULT_SOURCE_DIR,
          web_books_dir: Path = WEB_BOOKS_DIR) -> None:
    for slug in slugs or BOOKS.keys():
        pages = PAGES_BY_SLUG[slug]
        total = len(pages)
        result = {}
        failures = []
        for index, page in enumerate(pages, start=1):
            if page["type"] != "transcription":
                continue
            swf_path = source_dir / f"{page['source']}.swf"
            try:
                result[str(index)] = build_transcription_for_page(swf_path)
                print(f"[{slug} {index}/{total}] {page['source']}.swf transcription built")
            except Exception as exc:
                print(f"warning: skipping transcription for {slug} page {index} ({page['source']}.swf): {exc}")
                failures.append(page["source"])
        output_path = web_books_dir / slug / "transcriptions.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if failures:
            print(f"{slug}: completed with {len(failures)} skipped page(s): {failures}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", action="append", dest="slugs", choices=list(BOOKS.keys()))
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    args = parser.parse_args()
    main(args.slugs, args.source)
```

(Remove the now-unused `from extract.manifests.peniche import PAGES as
PENICHE_PAGES` and old `DEFAULT_OUTPUT_PATH` constant.)

- [ ] **Step 7: Run the full test suite**

Run: `.venv/bin/python -m pytest extract/tests/ -v`
Expected: PASS, no regressions (`test_extract_images.py` and
`test_extract_transcriptions.py` only exercise the pure helper
functions left untouched by this task).

- [ ] **Step 8: Commit**

```bash
git add extract/build_manifest.py extract/extract_images.py extract/extract_transcriptions.py extract/tests/test_build_manifest.py
git commit -m "Parameterize pipeline scripts to loop over all books"
```

---

### Task 10: Run the pipeline for the four new books against the real disc

**Files:**
- Create: `web/books/caderno1/manifest.json`, `web/books/caderno1/pages/*.jpg`, `web/books/caderno1/transcriptions.json`
- Create: `web/books/caderno28/manifest.json`, `web/books/caderno28/pages/*.jpg`, `web/books/caderno28/transcriptions.json`
- Create: `web/books/caderno43/manifest.json`, `web/books/caderno43/pages/*.jpg`, `web/books/caderno43/transcriptions.json`
- Create: `web/books/inventario/manifest.json`, `web/books/inventario/pages/*.jpg`, `web/books/inventario/transcriptions.json`

**Interfaces:**
- Consumes: `main()` from `build_manifest.py`, `extract_images.py`,
  `extract_transcriptions.py` (all from Task 9).
- Produces: the on-disk `web/books/<slug>/**` data every viewer task
  from here on reads.

- [ ] **Step 1: Run image extraction for the four new books**

Run: `.venv/bin/python -m extract.extract_images --book caderno1 --book caderno28 --book caderno43 --book inventario`

Expected: prints a `[slug N/total] ... -> ...jpg` line per page for
each of the four books, with any `warning: skipping` lines investigated
before continuing (a skipped page means a page image will 404 in the
viewer).

- [ ] **Step 2: Run transcription extraction for the four new books**

Run: `.venv/bin/python -m extract.extract_transcriptions --book caderno1 --book caderno28 --book caderno43 --book inventario`

Expected: prints a `[slug N/total] ... transcription built` line for
every `transcription`-type page in each book (Inventário has none, so
it should print nothing and produce an empty `{}` transcriptions.json).

- [ ] **Step 3: Run manifest generation for the four new books**

Run: `.venv/bin/python -m extract.build_manifest --book caderno1 --book caderno28 --book caderno43 --book inventario`

Expected: prints `wrote manifest for <slug>: N pages -> ...` for each,
with page counts matching Task 7 Step 5's sanity check (62/80/94/4).

- [ ] **Step 4: Spot-check the generated output**

Run:

```bash
for slug in caderno1 caderno28 caderno43 inventario; do
  echo "--- $slug ---"
  ls web/books/$slug/pages | wc -l
  cat web/books/$slug/manifest.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['title'], d['page_count'])"
  cat web/books/$slug/transcriptions.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)), 'transcriptions')"
done
```

Expected page counts: `caderno1` 62, `caderno28` 80, `caderno43` 94,
`inventario` 4. Expected transcription counts: `caderno1` 26,
`caderno28` 42, `caderno43` 56, `inventario` 0 (matching the table in
the design spec).

- [ ] **Step 5: Commit the generated assets**

```bash
git add web/books/caderno1 web/books/caderno28 web/books/caderno43 web/books/inventario
git commit -m "Generate extracted pages, transcriptions, and manifests for the four new books"
```

---

### Task 11: Extract and commit the shared background-audio asset

**Files:**
- Create: `web/audio/sitesound.mp3`

**Interfaces:**
- Consumes: `extract.projector_manifest.extract_book_movie` (Task 3),
  `extract.extract_audio.extract_sound` (Task 8), `extract.books.BOOKS` (Task 2).
- Produces: `web/audio/sitesound.mp3`, consumed by the viewer (Task 13).

- [ ] **Step 1: Extract the audio from Peniche's movie**

Run:

```bash
.venv/bin/python -c "
from pathlib import Path
from extract.books import BOOKS
from extract.projector_manifest import extract_book_movie
from extract.extract_audio import extract_sound

movie_bytes = extract_book_movie(BOOKS['peniche']['exe'])
tmp_movie = Path('/tmp/peniche_movie.swf')
tmp_movie.write_bytes(movie_bytes)
extract_sound(tmp_movie, 'sitesound', Path('web/audio/sitesound.mp3'))
print('done')
"
```

Expected: prints `done`, and `web/audio/sitesound.mp3` exists.

- [ ] **Step 2: Verify it is a valid, playable MP3**

Run: `file web/audio/sitesound.mp3`
Expected: output mentions `MPEG ADTS, layer III` (or similar MP3
signature). If `file` reports something else (e.g. a `.wav` got picked
up instead), check `extract_sound`'s glob filter in Task 8.

- [ ] **Step 3: Commit**

```bash
git add web/audio/sitesound.mp3
git commit -m "Add extracted shared background-audio asset (sitesound.mp3)"
```

---

### Task 12: Parameterize the viewer for multiple books

**Files:**
- Move: `web/index.html` → `web/viewer.html`
- Modify: `web/js/viewer.js`
- Modify: `web/css/style.css`

**Interfaces:**
- Consumes: `manifest.json`'s new `"title"` field (Task 9/10).
- Produces: `viewer.html?book=<slug>&page=<n>` URL contract, consumed
  by Task 14's library page links.

- [ ] **Step 1: Rename the viewer HTML and update its header**

```bash
git mv web/index.html web/viewer.html
```

Replace `web/viewer.html`'s `<title>` and `#book-header` block:

```html
<title>Cadernos — Álvaro Cunhal</title>
```

```html
<header id="book-header">
  <a id="library-link" href="index.html">&larr; Biblioteca</a>
  <h1 id="book-title"></h1>
  <p>Álvaro Cunhal</p>
</header>
```

(The rest of `viewer.html` — `#reading-area`, `#toolbar`, and the
`<script src="js/viewer.js">` tag — is unchanged by this step; Task 13
adds more to `#toolbar`.)

- [ ] **Step 2: Read `?book=` and `&page=` from the URL in `viewer.js`**

At the very top of `web/js/viewer.js`, before the existing `const
state = {...}` line, add:

```javascript
const params = new URLSearchParams(location.search);
const bookSlug = params.get("book");

if (!bookSlug) {
  location.href = "index.html";
}

const bookTitle = document.getElementById("book-title");
```

- [ ] **Step 3: Load book data from the book-specific path**

In `renderCurrentPage()`, change:

```javascript
pageImage.src = `books/peniche/${page.image}`;
```

to:

```javascript
pageImage.src = `books/${bookSlug}/${page.image}`;
```

Change the transcription fetch:

```javascript
fetch("books/peniche/transcriptions.json")
```

to:

```javascript
fetch(`books/${bookSlug}/transcriptions.json`)
```

Change the manifest fetch's whole `.then` chain from:

```javascript
fetch("books/peniche/manifest.json")
  .then((response) => response.json())
  .then((manifest) => {
    state.manifest = manifest;
    pageInput.max = manifest.page_count;
    goToPage(1);
  });
```

to:

```javascript
fetch(`books/${bookSlug}/manifest.json`)
  .then((response) => response.json())
  .then((manifest) => {
    state.manifest = manifest;
    pageInput.max = manifest.page_count;
    document.title = `${manifest.title} — Álvaro Cunhal`;
    bookTitle.textContent = manifest.title;
    const initialPage = parseInt(params.get("page"), 10) || 1;
    goToPage(initialPage);
  });
```

- [ ] **Step 4: Add a "back to library" link style**

In `web/css/style.css`, change `#book-header` to be positioned so the
link can sit in its corner:

```css
#book-header {
  padding: 0.6rem 1rem;
  background: var(--bg-darker);
  border-bottom: 1px solid #2c2c2c;
  text-align: center;
  position: relative;
}
```

Add:

```css
#library-link {
  position: absolute;
  left: 1rem;
  top: 0.6rem;
  color: var(--accent);
  text-decoration: none;
  font-size: 0.85rem;
}

#library-link:hover {
  text-decoration: underline;
}
```

- [ ] **Step 5: Verify syntax and smoke-test manually**

Run: `node --check web/js/viewer.js`
Expected: no output, exit code 0.

Serve the `web/` directory locally (e.g. `python3 -m http.server 8000`
from inside `web/`) and open `http://localhost:8000/viewer.html?book=peniche&page=5`
in a browser. Confirm: the header shows "Documentos de Peniche", the
page shown is page 5, and navigating with the arrow buttons still
works. Then open `http://localhost:8000/viewer.html` (no `book` param)
and confirm it redirects to `index.html` (expect a 404 for now — Task
14 creates that file; confirming the redirect *attempt* happens is
enough at this step).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Parameterize viewer for multiple books via ?book= and &page="
```

---

### Task 13: Add the background-audio feature to the viewer

**Files:**
- Modify: `web/viewer.html`
- Modify: `web/js/viewer.js`
- Modify: `web/css/style.css`

**Interfaces:**
- Consumes: `web/audio/sitesound.mp3` (Task 11).
- Produces: nothing consumed by later tasks (leaf feature).

- [ ] **Step 1: Add the audio element, toggle button, and banner to `viewer.html`**

In `web/viewer.html`, add the toggle button to `#toolbar`, right after
the `fullscreen` button:

```html
    <button id="fullscreen" aria-label="Ecrã completo">&#9974;</button>
    <button id="toggle-audio" aria-label="Música"></button>
```

Add the audio element and banner right after the closing `</div>` of
`#toolbar` but still inside `#viewer` (i.e. as its own top-level
sibling before `</div>` that closes `#viewer`... concretely: insert
this block immediately **before** the `<div id="toolbar">` opening
tag, so the banner sits between the header and the reading area):

```html
    <div id="audio-banner" hidden>
      <p>A edição original desta obra incluía música de fundo — pode ativá-la no botão "Música" da barra de ferramentas.</p>
      <button id="dismiss-audio-banner" aria-label="Fechar">&times;</button>
    </div>
```

And add the `<audio>` element right before the closing `</div>` of
`#viewer` (after `#toolbar`'s closing `</div>`, before `</div>` that
closes `#viewer`):

```html
    <audio id="background-audio" src="audio/sitesound.mp3" loop></audio>
```

- [ ] **Step 2: Add the toggle/banner behavior to `viewer.js`**

Append to the end of `web/js/viewer.js`:

```javascript
const backgroundAudio = document.getElementById("background-audio");
const toggleAudioButton = document.getElementById("toggle-audio");
const audioBanner = document.getElementById("audio-banner");
const AUDIO_BANNER_DISMISSED_KEY = "cadernos-audio-banner-dismissed";

function updateAudioButtonLabel() {
  toggleAudioButton.textContent = backgroundAudio.muted ? "🔇 Música" : "🔊 Música";
}

function toggleAudio() {
  backgroundAudio.muted = !backgroundAudio.muted;
  if (!backgroundAudio.muted) {
    backgroundAudio.play().catch(() => {});
  }
  updateAudioButtonLabel();
}

toggleAudioButton.addEventListener("click", toggleAudio);
backgroundAudio.muted = true;
backgroundAudio.play().catch(() => {});
updateAudioButtonLabel();

if (localStorage.getItem(AUDIO_BANNER_DISMISSED_KEY) !== "true") {
  audioBanner.hidden = false;
}

document.getElementById("dismiss-audio-banner").addEventListener("click", () => {
  audioBanner.hidden = true;
  localStorage.setItem(AUDIO_BANNER_DISMISSED_KEY, "true");
});
```

- [ ] **Step 3: Style the banner**

Append to `web/css/style.css`:

```css
#audio-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.6rem 1rem;
  background: var(--accent);
  color: #1c1c1c;
  font-size: 0.9rem;
}

#audio-banner[hidden] {
  display: none;
}

#audio-banner p {
  margin: 0;
}

#dismiss-audio-banner {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  color: #1c1c1c;
  flex-shrink: 0;
}
```

- [ ] **Step 4: Verify syntax and smoke-test manually**

Run: `node --check web/js/viewer.js`
Expected: no output, exit code 0.

With the local server still running, reload
`http://localhost:8000/viewer.html?book=peniche`. Confirm: the banner
appears with the mute-explanation text and a working `×` close button;
after closing it, reloading the page does *not* show it again (check
`localStorage.getItem("cadernos-audio-banner-dismissed")` is `"true"`
in devtools). Confirm clicking "🔇 Música" changes it to "🔊 Música" and
starts audible playback; clicking it again mutes and relabels back.

- [ ] **Step 5: Commit**

```bash
git add web/viewer.html web/js/viewer.js web/css/style.css
git commit -m "Add background-audio toggle and first-visit banner to the viewer"
```

---

### Task 14: Library landing page

**Files:**
- Create: `web/index.html`
- Create: `web/js/library.js`
- Modify: `web/css/style.css`

**Interfaces:**
- Consumes: `web/books/<slug>/manifest.json`'s `title`, `page_count`,
  and `pages[0].image` fields (Task 9/10).
- Produces: nothing consumed by later tasks (leaf feature; this is the
  entry point users land on).

- [ ] **Step 1: Create the landing page HTML**

Create `web/index.html`:

```html
<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cadernos — Álvaro Cunhal</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <div id="library">
    <header id="library-header">
      <h1>Cadernos</h1>
      <p>Escritos de Álvaro Cunhal na Prisão de Peniche</p>
    </header>
    <div id="book-list"></div>
  </div>
  <script src="js/library.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create the landing page script**

Create `web/js/library.js`:

```javascript
const BOOK_SLUGS = ["caderno1", "caderno28", "caderno43", "peniche", "inventario"];

const bookList = document.getElementById("book-list");

BOOK_SLUGS.forEach((slug) => {
  fetch(`books/${slug}/manifest.json`)
    .then((response) => response.json())
    .then((manifest) => {
      const card = document.createElement("a");
      card.className = "book-card";
      card.href = `viewer.html?book=${slug}`;

      const cover = document.createElement("img");
      cover.className = "book-cover";
      cover.src = `books/${slug}/${manifest.pages[0].image}`;
      cover.alt = "";

      const title = document.createElement("h2");
      title.textContent = manifest.title;

      const pageCount = document.createElement("p");
      pageCount.textContent = `${manifest.page_count} páginas`;

      card.append(cover, title, pageCount);
      bookList.appendChild(card);
    });
});
```

- [ ] **Step 3: Style the landing page**

Append to `web/css/style.css`:

```css
#library {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 1rem;
}

#library-header {
  text-align: center;
  margin-bottom: 2rem;
}

#library-header h1 {
  margin: 0;
  font-size: 2rem;
  letter-spacing: 0.03em;
}

#library-header p {
  color: var(--accent);
  margin: 0.3rem 0 0;
}

#book-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.5rem;
  max-width: 960px;
  width: 100%;
}

.book-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: var(--text-light);
  background: var(--bg-darker);
  border: 1px solid #2c2c2c;
  border-radius: 6px;
  padding: 1rem;
  transition: border-color 0.15s ease;
}

.book-card:hover {
  border-color: var(--accent);
}

.book-cover {
  width: 100%;
  max-width: 140px;
  aspect-ratio: 656 / 856;
  object-fit: cover;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  margin-bottom: 0.75rem;
}

.book-card h2 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  text-align: center;
}

.book-card p {
  margin: 0;
  font-size: 0.85rem;
  color: #aaa;
}
```

- [ ] **Step 4: Verify syntax and smoke-test manually**

Run: `node --check web/js/library.js`
Expected: no output, exit code 0.

With the local server running, open `http://localhost:8000/index.html`.
Confirm: all five books appear as cards with a cover image, title, and
page count, in the order Caderno 1 / Caderno 28 / Caderno 43 /
Documentos de Peniche / Inventário; clicking any card navigates to that
book's viewer at page 1. Then re-test the redirect from Task 12 Step 5:
`http://localhost:8000/viewer.html` (no `book` param) should now
successfully redirect to this landing page instead of 404ing.

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/js/library.js web/css/style.css
git commit -m "Add library landing page listing all five books"
```

---

### Task 15: Manual QA pass across all five books and PR wrap-up

**Files:** none (verification + housekeeping only)

- [ ] **Step 1: Run the full pytest suite one final time**

Run: `.venv/bin/python -m pytest extract/tests/ -v`
Expected: PASS, full suite green.

- [ ] **Step 2: Manually QA each book in a browser**

With the local server running, for each of the five books
(`?book=peniche`, `caderno1`, `caderno28`, `caderno43`, `inventario`):
open the viewer, page through from page 1 to the last page, and
confirm: images load, transcription text (where present) renders
readably, blank pages show as plain white without errors, and — for
Inventário specifically — confirm all 4 `plain`-type pages render as
plain facsimile images with no transcription pane shown (this exercises
the `plain` page-type code path for the first time in this project).
Resize the browser window to a narrow/mobile width and confirm the
two-column layout stacks vertically. Toggle the audio button and
confirm playback starts/stops audibly.

- [ ] **Step 3: Update the PR description to reflect the expanded scope**

Run: `tea pulls edit 1` (or the equivalent `tea` command for editing a
pull request's description) to update PR #1's title/description,
noting it now covers all five books plus the background-audio feature,
not just the Peniche pilot.

- [ ] **Step 4: Push the final state**

```bash
git push origin peniche-pilot
```

Expected: push succeeds, PR #1 shows all new commits.
