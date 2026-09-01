# Cadernos Web Pilot (Documentos de Peniche) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the "Documentos de Peniche" book from the original Flash CD-ROM as a static HTML5 page-flip viewer with transcription overlays, reverse-engineered from the original `.swf` assets.

**Architecture:** A one-time offline Python extraction pipeline (driving the `ffdec` CLI plus custom SWF tag parsing) converts the 28 source `.swf` pages into static JPEGs and JSON, committed to the repo. A dependency-free static HTML/CSS/vanilla-JS viewer renders that output entirely client-side.

**Tech Stack:** Python 3 + pytest (extraction pipeline), `ffdec` CLI (JPEXS Free Flash Decompiler, already installed via `ffdec-bin`), Pillow (placeholder image generation), plain HTML5/CSS3/vanilla JavaScript (viewer, no framework/bundler).

**Spec:** `docs/superpowers/specs/2026-09-01-cadernos-web-pilot-design.md`

## Global Constraints

- Viewer has zero build step, zero framework, zero external CDN dependency — plain files only.
- Extraction pipeline runs against the source disc mounted at `/run/media/user/Cadernos` (path is a CLI default, overridable) — raw `.swf` files are never committed to the repo, only their extracted derivatives.
- Only the 28 pages belonging to "Documentos de Peniche" are in scope (source files `cfg/237.swf`–`cfg/263.swf` plus `cfg/branco.swf`, exact order below).
- Background audio and interactive index are explicitly out of scope for this pilot (per spec).
- Responsive/mobile layout is in scope (per spec).
- No automated test framework for the viewer — manual browser walkthrough only, including a mobile viewport pass (per spec). The Python extraction pipeline does get real automated tests (pytest).

---

## File Structure

```
extract/
  peniche_manifest.py        # hardcoded, recovered page order + per-page type
  swf_tags.py                 # decompress + walk SWF tag streams
  frame_mapping.py            # map character IDs -> timeline frame number
  goto_parser.py               # parse gotoAndStop(N) targets from decompiled button scripts
  text_filters.py              # heuristic to drop non-prose UI text (page-number footer)
  extract_images.py           # CLI: export + renumber page JPEGs (+ blank-page placeholder)
  extract_transcriptions.py   # CLI: export text/scripts, reorder, build transcriptions.json
  build_manifest.py           # CLI: writes web/books/peniche/manifest.json
  requirements.txt
  tests/
    test_peniche_manifest.py
    test_swf_tags.py
    test_frame_mapping.py
    test_goto_parser.py
    test_text_filters.py
    test_extract_images.py
    test_extract_transcriptions.py
    test_build_manifest.py
web/
  index.html
  css/style.css
  js/viewer.js
  books/peniche/
    pages/001.jpg ... 028.jpg   # generated
    manifest.json                # generated
    transcriptions.json          # generated
```

---

### Task 1: Peniche page manifest (recovered page order + type)

**Files:**
- Create: `extract/peniche_manifest.py`
- Test: `extract/tests/test_peniche_manifest.py`

**Interfaces:**
- Produces: `PENICHE_PAGES: list[dict]`, each `{"source": str, "type": "plain" | "transcription" | "blank"}`. Consumed by every later extraction script and by `build_manifest.py`.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_peniche_manifest.py
from extract.peniche_manifest import PENICHE_PAGES

def test_total_page_count_is_28():
    assert len(PENICHE_PAGES) == 28

def test_first_and_last_pages():
    assert PENICHE_PAGES[0] == {"source": "237", "type": "transcription"}
    assert PENICHE_PAGES[-1] == {"source": "263", "type": "transcription"}

def test_exactly_one_blank_page():
    blanks = [p for p in PENICHE_PAGES if p["type"] == "blank"]
    assert blanks == [{"source": "branco", "type": "blank"}]

def test_no_plain_pages_in_this_book():
    # every non-blank Peniche page carries a transcription overlay
    assert all(p["type"] in ("transcription", "blank") for p in PENICHE_PAGES)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/sources/cadernos-cunhal-web && python3 -m pytest extract/tests/test_peniche_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.peniche_manifest'`

- [ ] **Step 3: Write the implementation**

This exact order and per-page type was recovered from the page-list XML embedded in `4.Peniche.exe`'s appended movie, cross-checked against tag-level SWF inspection (every non-blank page contains a `DefineButton2` tag, i.e. a transcription overlay).

```python
# extract/peniche_manifest.py
"""Recovered page manifest for 'Documentos de Peniche'.

Order and source filenames come from the <pages> XML embedded in the
original 4.Peniche.exe projector. Page type was determined by scanning
each page .swf for a DefineButton2 tag (tag type 34): its presence means
the page carries a transcription overlay with clickable page-jump buttons.
"""

PENICHE_PAGES = [
    {"source": "237", "type": "transcription"},
    {"source": "238", "type": "transcription"},
    {"source": "239", "type": "transcription"},
    {"source": "240", "type": "transcription"},
    {"source": "241", "type": "transcription"},
    {"source": "242", "type": "transcription"},
    {"source": "243", "type": "transcription"},
    {"source": "branco", "type": "blank"},
    {"source": "244", "type": "transcription"},
    {"source": "245", "type": "transcription"},
    {"source": "246", "type": "transcription"},
    {"source": "247", "type": "transcription"},
    {"source": "248", "type": "transcription"},
    {"source": "249", "type": "transcription"},
    {"source": "250", "type": "transcription"},
    {"source": "251", "type": "transcription"},
    {"source": "252", "type": "transcription"},
    {"source": "253", "type": "transcription"},
    {"source": "254", "type": "transcription"},
    {"source": "255", "type": "transcription"},
    {"source": "256", "type": "transcription"},
    {"source": "257", "type": "transcription"},
    {"source": "258", "type": "transcription"},
    {"source": "259", "type": "transcription"},
    {"source": "260", "type": "transcription"},
    {"source": "261", "type": "transcription"},
    {"source": "262", "type": "transcription"},
    {"source": "263", "type": "transcription"},
]
```

Create `extract/__init__.py` and `extract/tests/__init__.py` (empty files) so `extract` is importable as a package from the repo root.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_peniche_manifest.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add extract/peniche_manifest.py extract/__init__.py extract/tests/__init__.py extract/tests/test_peniche_manifest.py
git commit -m "Add recovered Peniche page manifest"
```

---

### Task 2: SWF tag stream parsing primitives

**Files:**
- Create: `extract/swf_tags.py`
- Test: `extract/tests/test_swf_tags.py`

**Interfaces:**
- Consumes: nothing (pure, stdlib only: `struct`, `zlib`).
- Produces: `decompress_swf(data: bytes) -> bytes`, `iter_tags(body: bytes, start: int) -> Iterator[tuple[int, int, int]]` (yields `(tag_type, content_start, tag_len)`), `tags_start_offset(body: bytes) -> int` (byte offset of the first tag after the RECT/framerate/framecount header), `scan_tag_types(swf_path: str) -> set[int]`, `has_transcription_overlay(swf_path: str) -> bool`. Consumed by `frame_mapping.py`, `extract_images.py`, `extract_transcriptions.py`.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_swf_tags.py
import struct
from extract.swf_tags import decompress_swf, iter_tags, tags_start_offset, scan_tag_types, has_transcription_overlay

def build_test_swf(tags: list[tuple[int, bytes]]) -> bytes:
    """Build a minimal valid uncompressed (FWS) SWF for tests: RECT(nbits=0),
    2-byte frame rate, 2-byte frame count, then the given tags, then an End tag."""
    rect = bytes([0x00])
    header_rest = struct.pack("<HH", 0, 1)
    body = rect + header_rest
    for tag_type, content in tags:
        tag_len = len(content)
        if tag_len < 0x3F:
            code = (tag_type << 6) | tag_len
            body += struct.pack("<H", code) + content
        else:
            code = (tag_type << 6) | 0x3F
            body += struct.pack("<H", code) + struct.pack("<I", tag_len) + content
    body += struct.pack("<H", 0)  # End tag
    return b"FWS" + bytes([8]) + struct.pack("<I", 0) + body

def test_decompress_uncompressed_swf_strips_header():
    swf = build_test_swf([(1, b"")])
    body = decompress_swf(swf)
    assert body[:1] == b"\x00"  # RECT byte we built

def test_decompress_rejects_unknown_signature():
    import pytest
    with pytest.raises(ValueError):
        decompress_swf(b"XXX\x08\x00\x00\x00\x00")

def test_iter_tags_yields_type_and_length():
    swf = build_test_swf([(34, b"\x11\x22\x33"), (1, b"")])
    body = decompress_swf(swf)
    start = tags_start_offset(body)
    tags = list(iter_tags(body, start))
    types = [t for t, _, _ in tags]
    assert types == [34, 1, 0]
    button_type, button_start, button_len = tags[0]
    assert button_len == 3
    assert body[button_start:button_start + button_len] == b"\x11\x22\x33"

def test_scan_tag_types_plain_page(tmp_path):
    swf = build_test_swf([(1, b"")])
    path = tmp_path / "plain.swf"
    path.write_bytes(swf)
    assert scan_tag_types(str(path)) == {0, 1}

def test_has_transcription_overlay_true_when_define_button2_present(tmp_path):
    swf = build_test_swf([(34, b"\x11\x22\x33"), (1, b"")])
    path = tmp_path / "button.swf"
    path.write_bytes(swf)
    assert has_transcription_overlay(str(path)) is True

def test_has_transcription_overlay_false_for_plain_page(tmp_path):
    swf = build_test_swf([(1, b"")])
    path = tmp_path / "plain.swf"
    path.write_bytes(swf)
    assert has_transcription_overlay(str(path)) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest extract/tests/test_swf_tags.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.swf_tags'`

- [ ] **Step 3: Write the implementation**

```python
# extract/swf_tags.py
"""Minimal SWF tag-stream parsing, enough to classify pages and locate
placement data. Implements the relevant parts of the public SWF File
Format Specification (RECT header, tag headers, PlaceObject2) needed to
reverse-engineer this specific disc's content for personal archival use."""

import struct
import zlib
from typing import Iterator

DEFINE_BUTTON2 = 34
END_TAG = 0


def decompress_swf(data: bytes) -> bytes:
    """Return the tag body of a SWF file, decompressing if needed."""
    sig = data[:3]
    if sig == b"CWS":
        return zlib.decompress(data[8:])
    if sig == b"FWS":
        return data[8:]
    raise ValueError(f"unsupported SWF signature: {sig!r}")


def tags_start_offset(body: bytes) -> int:
    """Byte offset of the first tag, i.e. past the RECT + frame rate +
    frame count header that follows the 8-byte file signature/version/length."""
    nbits = body[0] >> 3
    rect_bytes = (5 + nbits * 4 + 7) // 8
    return rect_bytes + 4  # + 2-byte frame rate + 2-byte frame count


def iter_tags(body: bytes, start: int) -> Iterator[tuple[int, int, int]]:
    """Yield (tag_type, content_start_offset, content_length) for each tag
    starting at `start`, stopping after yielding the End tag."""
    pos = start
    n = len(body)
    while pos < n - 1:
        tag_code_and_len = struct.unpack("<H", body[pos:pos + 2])[0]
        tag_type = tag_code_and_len >> 6
        short_len = tag_code_and_len & 0x3F
        pos += 2
        if short_len == 0x3F:
            tag_len = struct.unpack("<I", body[pos:pos + 4])[0]
            pos += 4
        else:
            tag_len = short_len
        yield tag_type, pos, tag_len
        pos += tag_len
        if tag_type == END_TAG:
            return


def scan_tag_types(swf_path: str) -> set[int]:
    with open(swf_path, "rb") as f:
        data = f.read()
    body = decompress_swf(data)
    start = tags_start_offset(body)
    return {tag_type for tag_type, _, _ in iter_tags(body, start)}


def has_transcription_overlay(swf_path: str) -> bool:
    return DEFINE_BUTTON2 in scan_tag_types(swf_path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_swf_tags.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add extract/swf_tags.py extract/tests/test_swf_tags.py
git commit -m "Add SWF tag stream parsing primitives"
```

---

### Task 3: Character-ID-to-frame mapping

**Files:**
- Create: `extract/frame_mapping.py`
- Test: `extract/tests/test_frame_mapping.py`

**Interfaces:**
- Consumes: `iter_tags`, `tags_start_offset` from `extract/swf_tags.py`.
- Produces: `map_char_ids_to_frames(body: bytes, tags_start: int) -> dict[int, set[int]]` (frame number -> set of character IDs first placed in that frame). Consumed by `extract_transcriptions.py`.

This was validated directly against the real disc during design (page `cfg/250.swf`): the top-level timeline (not a nested sprite) has 17 frames, and character IDs known to be transcription text (from `ffdec -export text`) land in the frame their `PlaceObject2` tag first appears in, confirming the recovered frame boundaries line up with the transcription pages navigated via the buttons' `gotoAndStop(N)` targets.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_frame_mapping.py
import struct
from extract.swf_tags import decompress_swf, tags_start_offset
from extract.frame_mapping import map_char_ids_to_frames

def build_test_swf(tags: list[tuple[int, bytes]]) -> bytes:
    rect = bytes([0x00])
    header_rest = struct.pack("<HH", 0, 1)
    body = rect + header_rest
    for tag_type, content in tags:
        tag_len = len(content)
        if tag_len < 0x3F:
            code = (tag_type << 6) | tag_len
            body += struct.pack("<H", code) + content
        else:
            code = (tag_type << 6) | 0x3F
            body += struct.pack("<H", code) + struct.pack("<I", tag_len) + content
    body += struct.pack("<H", 0)
    return b"FWS" + bytes([8]) + struct.pack("<I", 0) + body

def place_object2(depth: int, char_id: int) -> bytes:
    flags = 0x02  # PlaceFlagHasCharacter
    return bytes([flags]) + struct.pack("<H", depth) + struct.pack("<H", char_id)

def test_maps_characters_to_the_frame_they_first_appear_in():
    tags = [
        (26, place_object2(1, 5)),
        (1, b""),                    # end of frame 1
        (26, place_object2(2, 9)),
        (26, place_object2(3, 10)),
        (1, b""),                    # end of frame 2
    ]
    swf = build_test_swf(tags)
    body = decompress_swf(swf)
    start = tags_start_offset(body)

    result = map_char_ids_to_frames(body, start)

    assert result == {1: {5}, 2: {9, 10}}

def test_place_object2_without_has_character_flag_is_ignored():
    move_only = bytes([0x01]) + struct.pack("<H", 1)  # PlaceFlagMove only, no character id
    tags = [(26, move_only), (1, b"")]
    swf = build_test_swf(tags)
    body = decompress_swf(swf)
    start = tags_start_offset(body)

    result = map_char_ids_to_frames(body, start)

    assert result == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest extract/tests/test_frame_mapping.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.frame_mapping'`

- [ ] **Step 3: Write the implementation**

```python
# extract/frame_mapping.py
"""Map SWF character IDs to the timeline frame they are first placed in.

Used to figure out which extracted DefineText run belongs to which
transcription "page" (each timeline frame is one transcription page in
the original content, selected via gotoAndStop(N) from a button)."""

import struct
from extract.swf_tags import iter_tags

SHOW_FRAME = 1
PLACE_OBJECT2 = 26
HAS_CHARACTER_FLAG = 0x02


def map_char_ids_to_frames(body: bytes, tags_start: int) -> dict[int, set[int]]:
    frame_to_chars: dict[int, set[int]] = {}
    frame_counter = 1
    for tag_type, content_start, tag_len in iter_tags(body, tags_start):
        if tag_type == SHOW_FRAME:
            frame_counter += 1
            continue
        if tag_type == PLACE_OBJECT2:
            tag_body = body[content_start:content_start + tag_len]
            flags = tag_body[0]
            if flags & HAS_CHARACTER_FLAG:
                char_id = struct.unpack("<H", tag_body[3:5])[0]
                frame_to_chars.setdefault(frame_counter, set()).add(char_id)
    return frame_to_chars
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_frame_mapping.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add extract/frame_mapping.py extract/tests/test_frame_mapping.py
git commit -m "Add character-ID-to-frame mapping for transcription pages"
```

---

### Task 4: Parse `gotoAndStop(N)` targets from decompiled button scripts

**Files:**
- Create: `extract/goto_parser.py`
- Test: `extract/tests/test_goto_parser.py`

**Interfaces:**
- Consumes: nothing (pure, stdlib `re` only).
- Produces: `parse_goto_target(action_script: str) -> int | None`. Consumed by `extract_transcriptions.py` to build the page-jump table from `ffdec -export script` output.

Verified during design against real `ffdec`-decompiled output from `cfg/250.swf`: every transcription-page button decompiles to exactly `on(press){\n   gotoAndStop(N);\n}`.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_goto_parser.py
from extract.goto_parser import parse_goto_target

def test_parses_gotoandstop_target():
    script = "on(press){\n   gotoAndStop(8);\n}"
    assert parse_goto_target(script) == 8

def test_parses_target_regardless_of_whitespace():
    assert parse_goto_target("on(press){gotoAndStop( 12 );}") == 12

def test_returns_none_for_scripts_without_gotoandstop():
    assert parse_goto_target("stop();") is None

def test_returns_none_for_other_goto_variants():
    # this dataset only ever uses gotoAndStop; anything else is unexpected
    # and should surface as "no target found" rather than a wrong guess
    assert parse_goto_target("on(press){ gotoAndPlay(3); }") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest extract/tests/test_goto_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.goto_parser'`

- [ ] **Step 3: Write the implementation**

```python
# extract/goto_parser.py
"""Extract the frame target from a decompiled Flash button action script.

This dataset's page-jump buttons decompile (via ffdec) to exactly:
    on(press){
       gotoAndStop(N);
    }
so we only need to recognize that one call form."""

import re

_GOTO_AND_STOP_RE = re.compile(r"gotoAndStop\(\s*(\d+)\s*\)")


def parse_goto_target(action_script: str) -> int | None:
    match = _GOTO_AND_STOP_RE.search(action_script)
    if match is None:
        return None
    return int(match.group(1))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_goto_parser.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add extract/goto_parser.py extract/tests/test_goto_parser.py
git commit -m "Add gotoAndStop target parser for transcription page links"
```

---

### Task 5: Filter out non-prose UI text (page-number footer)

**Files:**
- Create: `extract/text_filters.py`
- Test: `extract/tests/test_text_filters.py`

**Interfaces:**
- Consumes: nothing (pure, stdlib only).
- Produces: `is_navigation_label(text: str) -> bool`. Consumed by `extract_transcriptions.py` to exclude the always-visible page-number row (e.g. `"1  2  3  4 ... 16"`) from the reconstructed prose text — that row shares a frame with the actual paragraph text (both first appear on frame 2) but is UI chrome, not part of the transcription.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_text_filters.py
from extract.text_filters import is_navigation_label

def test_digit_and_whitespace_only_is_a_navigation_label():
    assert is_navigation_label("1    2    3    4    5") is True

def test_single_digit_is_a_navigation_label():
    assert is_navigation_label("1") is True

def test_prose_text_is_not_a_navigation_label():
    text = "Álvaro Barreirinhas Cunhal, natural de Coimbra, de 43 anos de idade"
    assert is_navigation_label(text) is False

def test_prose_containing_digits_is_not_a_navigation_label():
    assert is_navigation_label("acórdão de 9 de Maio de 1950 do Tribunal") is False

def test_empty_or_whitespace_only_is_not_treated_as_navigation():
    assert is_navigation_label("   ") is False
    assert is_navigation_label("") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest extract/tests/test_text_filters.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.text_filters'`

- [ ] **Step 3: Write the implementation**

```python
# extract/text_filters.py
"""Heuristics to separate transcribed prose from static UI text runs that
live in the same SWF frame (e.g. the always-visible page-number footer)."""

import re

_DIGITS_AND_WHITESPACE_RE = re.compile(r"^[\d\s]+$")


def is_navigation_label(text: str) -> bool:
    """True for text runs that are purely digits/whitespace, e.g. the
    "1  2  3 ... 16" page-number footer. Empty/whitespace-only text is not
    considered a navigation label (it's just empty, not a footer)."""
    stripped = text.strip()
    if not stripped:
        return False
    return bool(_DIGITS_AND_WHITESPACE_RE.match(stripped))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_text_filters.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add extract/text_filters.py extract/tests/test_text_filters.py
git commit -m "Add navigation-label filter for transcription text reconstruction"
```

---

### Task 6: Extract and renumber page images

**Files:**
- Create: `extract/extract_images.py`
- Test: `extract/tests/test_extract_images.py`
- Create: `extract/requirements.txt`

**Interfaces:**
- Consumes: `PENICHE_PAGES` from `extract/peniche_manifest.py`.
- Produces: `output_filename(index: int, total: int) -> str`; `main(source_dir: Path, output_dir: Path) -> None` CLI entry point. Produces the files `web/books/peniche/pages/NNN.jpg` consumed by `build_manifest.py` and the viewer.

Blank pages (`branco.swf`) have no embeddable JPEG in the original asset — confirmed during design: the blank page's SWF has only a `DefineShape` + `SetBackgroundColor`, no `DefineBitsJPEG2`. For those, we generate a plain white placeholder at the same dimensions as the real scans (656×856, confirmed from `cfg/250.swf`'s exported JPEG) instead of invoking `ffdec`.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_extract_images.py
from extract.extract_images import output_filename

def test_output_filename_zero_pads_to_total_width():
    assert output_filename(1, 28) == "01.jpg"
    assert output_filename(28, 28) == "28.jpg"

def test_output_filename_adapts_width_to_total():
    assert output_filename(1, 5) == "1.jpg"
    assert output_filename(1, 100) == "001.jpg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest extract/tests/test_extract_images.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.extract_images'`

- [ ] **Step 3: Write the implementation**

```
# extract/requirements.txt
Pillow>=10.0
```

```python
# extract/extract_images.py
"""Export one JPEG per Peniche page, renumbered into reading order.

Usage:
    python3 -m extract.extract_images [--source DIR] [--output DIR]
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from extract.peniche_manifest import PENICHE_PAGES

DEFAULT_SOURCE_DIR = Path("/run/media/user/Cadernos/cfg")
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "web" / "books" / "peniche" / "pages"
BLANK_PAGE_SIZE = (656, 856)  # matches the real facsimile scan dimensions


def output_filename(index: int, total: int) -> str:
    width = len(str(total))
    return f"{index:0{width}d}.jpg"


def export_page_image(swf_path: Path, dest_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffdec", "-export", "image", tmp, str(swf_path)],
            check=True,
            capture_output=True,
        )
        exported = sorted(Path(tmp).glob("*.jpg")) + sorted(Path(tmp).glob("*.jpeg"))
        if not exported:
            raise RuntimeError(f"no image exported for {swf_path}")
        shutil.copyfile(exported[0], dest_path)


def write_blank_placeholder(dest_path: Path) -> None:
    Image.new("RGB", BLANK_PAGE_SIZE, color="white").save(dest_path, "JPEG")


def main(source_dir: Path = DEFAULT_SOURCE_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(PENICHE_PAGES)
    failures = []
    for index, page in enumerate(PENICHE_PAGES, start=1):
        dest = output_dir / output_filename(index, total)
        try:
            if page["type"] == "blank":
                write_blank_placeholder(dest)
            else:
                export_page_image(source_dir / f"{page['source']}.swf", dest)
            print(f"[{index}/{total}] {page['source']}.swf -> {dest.name}")
        except Exception as exc:
            print(f"warning: skipping page {index} ({page['source']}.swf): {exc}")
            failures.append(page["source"])
    if failures:
        print(f"completed with {len(failures)} skipped page(s): {failures}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    main(args.source, args.output)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_extract_images.py -v`
Expected: PASS (2 tests)

Install Pillow before the next step: `pip install --user -r extract/requirements.txt` (or use a venv, whichever this environment already uses for Python deps).

- [ ] **Step 5: Commit**

```bash
git add extract/extract_images.py extract/requirements.txt extract/tests/test_extract_images.py
git commit -m "Add page image extraction with blank-page placeholder handling"
```

---

### Task 7: Extract and reconstruct transcription text

**Files:**
- Create: `extract/extract_transcriptions.py`
- Test: `extract/tests/test_extract_transcriptions.py`

**Interfaces:**
- Consumes: `PENICHE_PAGES` (`peniche_manifest.py`), `decompress_swf`/`tags_start_offset` (`swf_tags.py`), `map_char_ids_to_frames` (`frame_mapping.py`), `parse_goto_target` (`goto_parser.py`), `is_navigation_label` (`text_filters.py`).
- Produces: `assemble_page_transcription(frame_to_chars: dict[int, set[int]], text_by_char_id: dict[int, str], goto_targets: dict[int, int]) -> dict`; `main(source_dir: Path, output_path: Path) -> None`. Produces `web/books/peniche/transcriptions.json`, consumed by the viewer's transcription panel.

`assemble_page_transcription` is the pure, fully-testable core: given (a) which character IDs live in which frame, (b) each character ID's already-extracted text (from `ffdec -export text`, keyed by character ID as ffdec names its output files), and (c) each button's frame target (from `goto_parser`), it produces one ordered block of prose per frame, with navigation-label text runs dropped, and exposes the button jump table keyed by frame number.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_extract_transcriptions.py
from extract.extract_transcriptions import assemble_page_transcription

def test_builds_ordered_prose_per_frame_and_drops_navigation_labels():
    frame_to_chars = {
        1: {2, 4},
        2: {9, 10, 12},
        3: {32, 33},
    }
    text_by_char_id = {
        9: "Álvaro Barreirinhas Cunhal, natural de Coimbra",
        10: "1    2    3    4",       # page-number footer, must be dropped
        12: "licenciado em Direito, preso político na Cadeia do Forte de Peniche",
        32: "elementos para ajuizar tanto da pessoa como dos factos",
        33: "válida, para o estudo de alguém",
    }
    goto_targets = {19: 3}  # button character 19 jumps to frame 3 (a real frame)

    result = assemble_page_transcription(frame_to_chars, text_by_char_id, goto_targets)

    assert result["frames"][2] == (
        "Álvaro Barreirinhas Cunhal, natural de Coimbra\n"
        "licenciado em Direito, preso político na Cadeia do Forte de Peniche"
    )
    assert result["frames"][3] == (
        "elementos para ajuizar tanto da pessoa como dos factos\n"
        "válida, para o estudo de alguém"
    )
    assert 1 not in result["frames"]  # frame 1 has no text characters at all
    assert result["jump_table"] == {"19": 3}

def test_frame_with_no_text_characters_is_omitted():
    frame_to_chars = {1: {2, 4}}
    result = assemble_page_transcription(frame_to_chars, text_by_char_id={}, goto_targets={})
    assert result["frames"] == {}

def test_dangling_goto_target_is_dropped_with_a_warning(capsys):
    # button points at frame 99, which does not exist on this page
    frame_to_chars = {1: {2}, 2: {9}}
    text_by_char_id = {9: "Um parágrafo qualquer de texto transcrito aqui."}
    goto_targets = {19: 99}

    result = assemble_page_transcription(frame_to_chars, text_by_char_id, goto_targets)

    assert result["jump_table"] == {}
    assert "dangling gotoAndStop target" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest extract/tests/test_extract_transcriptions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.extract_transcriptions'`

- [ ] **Step 3: Write the implementation**

```python
# extract/extract_transcriptions.py
"""Reconstruct per-frame transcription text and the button jump table for
each Peniche page that has a transcription overlay.

Usage:
    python3 -m extract.extract_transcriptions [--source DIR] [--output FILE]
"""

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from extract.frame_mapping import map_char_ids_to_frames
from extract.goto_parser import parse_goto_target
from extract.peniche_manifest import PENICHE_PAGES
from extract.swf_tags import decompress_swf, tags_start_offset
from extract.text_filters import is_navigation_label

DEFAULT_SOURCE_DIR = Path("/run/media/user/Cadernos/cfg")
DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "web" / "books" / "peniche" / "transcriptions.json"


def assemble_page_transcription(
    frame_to_chars: dict[int, set[int]],
    text_by_char_id: dict[int, str],
    goto_targets: dict[int, int],
) -> dict:
    frames: dict[int, str] = {}
    for frame_number, char_ids in sorted(frame_to_chars.items()):
        lines = []
        for char_id in sorted(char_ids):
            text = text_by_char_id.get(char_id)
            if text is None or is_navigation_label(text):
                continue
            lines.append(text)
        if lines:
            frames[frame_number] = "\n".join(lines)

    jump_table = {}
    for button_char_id, target_frame in goto_targets.items():
        if target_frame not in frame_to_chars:
            print(f"warning: dangling gotoAndStop target frame {target_frame} "
                  f"for button {button_char_id}, dropping this link")
            continue
        jump_table[str(button_char_id)] = target_frame

    return {"frames": frames, "jump_table": jump_table}


def _read_char_id_texts(swf_path: Path) -> dict[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffdec", "-export", "text", tmp, str(swf_path)],
            check=True,
            capture_output=True,
        )
        texts = {}
        for txt_file in Path(tmp).glob("*.txt"):
            char_id = int(txt_file.stem)
            runs = txt_file.read_text(encoding="utf-8").split("--- RECORDSEPARATOR ---")
            texts[char_id] = "".join(run.strip("\n") for run in runs).strip()
        return texts


_BUTTON_CHAR_ID_RE = re.compile(r"DefineButton2_(\d+)")


def _read_button_goto_targets(swf_path: Path) -> dict[int, int]:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffdec", "-export", "script", tmp, str(swf_path)],
            check=True,
            capture_output=True,
        )
        targets = {}
        for script_path in Path(tmp).glob("scripts/DefineButton2_*/*.as"):
            match = _BUTTON_CHAR_ID_RE.search(str(script_path.parent))
            if match is None:
                continue
            target = parse_goto_target(script_path.read_text(encoding="utf-8"))
            if target is not None:
                targets[int(match.group(1))] = target
        return targets


def build_transcription_for_page(swf_path: Path) -> dict:
    data = swf_path.read_bytes()
    body = decompress_swf(data)
    start = tags_start_offset(body)
    frame_to_chars = map_char_ids_to_frames(body, start)
    text_by_char_id = _read_char_id_texts(swf_path)
    goto_targets = _read_button_goto_targets(swf_path)
    return assemble_page_transcription(frame_to_chars, text_by_char_id, goto_targets)


def main(source_dir: Path = DEFAULT_SOURCE_DIR, output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(PENICHE_PAGES)
    result = {}
    failures = []
    for index, page in enumerate(PENICHE_PAGES, start=1):
        if page["type"] != "transcription":
            continue
        swf_path = source_dir / f"{page['source']}.swf"
        try:
            result[str(index)] = build_transcription_for_page(swf_path)
            print(f"[{index}/{total}] {page['source']}.swf transcription built")
        except Exception as exc:
            print(f"warning: skipping transcription for page {index} ({page['source']}.swf): {exc}")
            failures.append(page["source"])
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if failures:
        print(f"completed with {len(failures)} skipped page(s): {failures}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    main(args.source, args.output)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_extract_transcriptions.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add extract/extract_transcriptions.py extract/tests/test_extract_transcriptions.py
git commit -m "Add transcription text reconstruction and jump table extraction"
```

---

### Task 8: Build the page manifest JSON

**Files:**
- Create: `extract/build_manifest.py`
- Test: `extract/tests/test_build_manifest.py`

**Interfaces:**
- Consumes: `PENICHE_PAGES` (`peniche_manifest.py`).
- Produces: `build_manifest_data(pages: list[dict]) -> dict`; `main(output_path: Path) -> None`. Produces `web/books/peniche/manifest.json`, consumed by `js/viewer.js`.

- [ ] **Step 1: Write the failing test**

```python
# extract/tests/test_build_manifest.py
from extract.build_manifest import build_manifest_data

def test_produces_one_entry_per_page_with_sequential_numbering():
    pages = [
        {"source": "237", "type": "transcription"},
        {"source": "branco", "type": "blank"},
        {"source": "238", "type": "transcription"},
    ]
    data = build_manifest_data(pages)
    assert data["page_count"] == 3
    assert data["pages"] == [
        {"number": 1, "image": "pages/1.jpg", "type": "transcription"},
        {"number": 2, "image": "pages/2.jpg", "type": "blank"},
        {"number": 3, "image": "pages/3.jpg", "type": "transcription"},
    ]

def test_image_filenames_are_zero_padded_to_total_width():
    pages = [{"source": str(i), "type": "plain"} for i in range(1, 11)]
    data = build_manifest_data(pages)
    assert data["pages"][0]["image"] == "pages/01.jpg"
    assert data["pages"][9]["image"] == "pages/10.jpg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest extract/tests/test_build_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'extract.build_manifest'`

- [ ] **Step 3: Write the implementation**

```python
# extract/build_manifest.py
"""Build web/books/peniche/manifest.json from the recovered page manifest.

Usage:
    python3 -m extract.build_manifest [--output FILE]
"""

import argparse
import json
from pathlib import Path

from extract.extract_images import output_filename
from extract.peniche_manifest import PENICHE_PAGES

DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "web" / "books" / "peniche" / "manifest.json"


def build_manifest_data(pages: list[dict]) -> dict:
    total = len(pages)
    return {
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


def main(output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    data = build_manifest_data(PENICHE_PAGES)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote manifest for {data['page_count']} pages to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    main(args.output)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest extract/tests/test_build_manifest.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add extract/build_manifest.py extract/tests/test_build_manifest.py
git commit -m "Add manifest.json builder"
```

---

### Task 9: Run the full pipeline against the real disc and commit generated assets

**Files:**
- Modify (generated, not hand-written): `web/books/peniche/pages/*.jpg`, `web/books/peniche/manifest.json`, `web/books/peniche/transcriptions.json`

**Interfaces:**
- Consumes: everything from Tasks 1–8.
- Produces: the static book bundle the viewer (Tasks 10–13) reads.

- [ ] **Step 1: Run the full extraction pipeline** (disc must be mounted at `/run/media/user/Cadernos`, adjust `--source` if it differs)

```bash
cd ~/sources/cadernos-cunhal-web
python3 -m extract.extract_images
python3 -m extract.extract_transcriptions
python3 -m extract.build_manifest
```

- [ ] **Step 2: Sanity-check the output**

```bash
python3 -c "
import json
m = json.load(open('web/books/peniche/manifest.json'))
assert m['page_count'] == 28
t = json.load(open('web/books/peniche/transcriptions.json'))
assert len(t) == 27  # every non-blank page
print('manifest and transcriptions look structurally correct')
"
ls web/books/peniche/pages | wc -l   # expect 28
```

- [ ] **Step 3: Spot-check transcription text for readability**

```bash
python3 -c "
import json
t = json.load(open('web/books/peniche/transcriptions.json'))
# page 14 in the manifest corresponds to source cfg/250.swf, already
# manually verified during design to contain a readable Cunhal petition
print(list(t['14']['frames'].items())[0][1][:300])
"
```

Expected: readable, correctly-accented Portuguese prose (not garbled text, not a page-number footer). If any spot-checked page reads wrong, fix the relevant pure function's test in Tasks 3–5 and re-run — do not hand-edit the generated JSON.

- [ ] **Step 4: Commit the generated book bundle**

```bash
git add web/books/peniche/
git commit -m "Generate Documentos de Peniche book bundle from source disc"
git push origin main
```

---

### Task 10: Viewer shell — load manifest, render current page, navigate

**Files:**
- Create: `web/index.html`
- Create: `web/css/style.css`
- Create: `web/js/viewer.js`

**Interfaces:**
- Consumes: `web/books/peniche/manifest.json`.
- Produces: a working page viewer with prev/next, keyboard arrows, jump-to-page, and a page counter. Later tasks (11–13) extend `viewer.js` and `style.css` without changing this task's structure.

- [ ] **Step 1: Write `web/index.html`**

```html
<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Documentos de Peniche — Álvaro Cunhal</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <div id="viewer">
    <div id="page-area">
      <img id="page-image" alt="">
      <div id="page-unavailable" hidden>Página indisponível</div>
    </div>
    <div id="toolbar">
      <button id="prev-page" aria-label="Página anterior">&larr;</button>
      <input id="page-input" type="number" min="1" value="1">
      <span id="page-count"></span>
      <button id="next-page" aria-label="Página seguinte">&rarr;</button>
      <button id="zoom-out" aria-label="Reduzir">&minus;</button>
      <button id="zoom-in" aria-label="Ampliar">&plus;</button>
      <button id="rotate" aria-label="Rodar">&#8635;</button>
      <button id="fullscreen" aria-label="Ecrã completo">&#9974;</button>
      <button id="toggle-transcription" aria-label="Transcrição">T</button>
    </div>
    <div id="transcription-panel" hidden>
      <button id="close-transcription" aria-label="Fechar">&times;</button>
      <div id="transcription-text"></div>
    </div>
  </div>
  <script src="js/viewer.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write base `web/css/style.css`**

```css
* { box-sizing: border-box; }

body {
  margin: 0;
  background: #222;
  color: #eee;
  font-family: Verdana, sans-serif;
}

#viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

#page-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

#page-image {
  max-height: 100%;
  max-width: 100%;
  transition: transform 0.15s ease;
}

#page-unavailable {
  font-size: 1.2rem;
  color: #aaa;
}

#page-unavailable[hidden] {
  display: none;
}

#toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #111;
}

#toolbar button {
  font-size: 1rem;
  padding: 0.4rem 0.7rem;
  cursor: pointer;
}

#page-input {
  width: 4rem;
}

#transcription-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100%;
  background: #fafafa;
  color: #111;
  padding: 1rem;
  overflow-y: auto;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.4);
}

#transcription-panel[hidden] {
  display: none;
}

#close-transcription {
  float: right;
  font-size: 1.2rem;
  cursor: pointer;
}

.transcription-jump {
  color: #0056b3;
  cursor: pointer;
  text-decoration: underline;
}

.transcription-jump.visited {
  color: #888;
}
```

- [ ] **Step 3: Write `web/js/viewer.js`** (navigation core only — zoom/rotate/fullscreen and transcription panel are wired in Tasks 11–12)

```javascript
const state = {
  manifest: null,
  currentPage: 1,
};

const pageImage = document.getElementById("page-image");
const pageUnavailable = document.getElementById("page-unavailable");
const pageInput = document.getElementById("page-input");
const pageCount = document.getElementById("page-count");

function renderCurrentPage() {
  const page = state.manifest.pages[state.currentPage - 1];
  pageImage.hidden = false;
  pageUnavailable.hidden = true;
  pageImage.src = `books/peniche/${page.image}`;
  pageImage.alt = `Página ${state.currentPage}`;
  pageInput.value = state.currentPage;
  pageCount.textContent = `/ ${state.manifest.page_count}`;
}

function goToPage(number) {
  const clamped = Math.min(Math.max(number, 1), state.manifest.page_count);
  state.currentPage = clamped;
  renderCurrentPage();
}

function nextPage() {
  goToPage(state.currentPage + 1);
}

function prevPage() {
  goToPage(state.currentPage - 1);
}

document.getElementById("next-page").addEventListener("click", nextPage);
document.getElementById("prev-page").addEventListener("click", prevPage);

pageInput.addEventListener("change", () => {
  goToPage(parseInt(pageInput.value, 10) || 1);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight") nextPage();
  if (event.key === "ArrowLeft") prevPage();
});

pageImage.addEventListener("error", () => {
  pageImage.hidden = true;
  pageUnavailable.hidden = false;
});

fetch("books/peniche/manifest.json")
  .then((response) => response.json())
  .then((manifest) => {
    state.manifest = manifest;
    pageInput.max = manifest.page_count;
    goToPage(1);
  });
```

- [ ] **Step 4: Manually verify in a browser**

```bash
cd ~/sources/cadernos-cunhal-web/web
python3 -m http.server 8080
```

Open `http://localhost:8080` and confirm: page 1 image loads, next/prev buttons work, `ArrowLeft`/`ArrowRight` keys work, typing a page number and pressing Enter jumps there, the counter shows "N / 28", and navigating past page 28 or before page 1 clamps instead of erroring.

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/css/style.css web/js/viewer.js
git commit -m "Add viewer shell with manifest loading and page navigation"
```

---

### Task 11: Zoom, rotate, fullscreen

**Files:**
- Modify: `web/js/viewer.js`
- Modify: `web/css/style.css`

**Interfaces:**
- Consumes: `state`, `pageImage` from Task 10 (same module scope, appended to the same file).
- Produces: working zoom in/out, rotate, and fullscreen toggle buttons.

- [ ] **Step 1: Add zoom/rotate/fullscreen state and handlers to `web/js/viewer.js`**

```javascript
const transform = {
  zoom: 1,
  rotation: 0,
};

function applyTransform() {
  pageImage.style.transform = `scale(${transform.zoom}) rotate(${transform.rotation}deg)`;
}

function zoomIn() {
  transform.zoom = Math.min(transform.zoom + 0.2, 3);
  applyTransform();
}

function zoomOut() {
  transform.zoom = Math.max(transform.zoom - 0.2, 0.4);
  applyTransform();
}

function rotate() {
  transform.rotation = (transform.rotation + 90) % 360;
  applyTransform();
}

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else {
    document.getElementById("viewer").requestFullscreen();
  }
}

document.getElementById("zoom-in").addEventListener("click", zoomIn);
document.getElementById("zoom-out").addEventListener("click", zoomOut);
document.getElementById("rotate").addEventListener("click", rotate);
document.getElementById("fullscreen").addEventListener("click", toggleFullscreen);
```

Reset `transform.zoom = 1; transform.rotation = 0; applyTransform();` at the top of `goToPage` so zoom/rotation don't carry over oddly between pages — add that line inside the existing `goToPage` function body from Task 10.

- [ ] **Step 2: Manually verify in a browser**

Reload `http://localhost:8080`. Confirm zoom in/out buttons scale the image up to a visible max/min, rotate cycles 0°→90°→180°→270°→0°, and fullscreen toggles the browser into/out of fullscreen on the viewer.

- [ ] **Step 3: Commit**

```bash
git add web/js/viewer.js web/css/style.css
git commit -m "Add zoom, rotate, and fullscreen controls"
```

---

### Task 12: Transcription panel with page-jump links

**Files:**
- Modify: `web/js/viewer.js`

**Interfaces:**
- Consumes: `web/books/peniche/transcriptions.json`, `state.currentPage`.
- Produces: transcription panel open/close, rendered prose with clickable frame-jump links (visited links styled via the `.visited` CSS class already defined in Task 10's stylesheet).

The original app's "click a page number to jump within the transcription" behavior maps directly to the recovered `jump_table`: each key is a button character ID, but what the user actually clicks is the rendered label for that jump target, so the panel renders one link per frame present in `jump_table`'s **values**, in ascending order, labeled by frame number.

- [ ] **Step 1: Add transcription loading and rendering to `web/js/viewer.js`**

```javascript
const transcriptionPanel = document.getElementById("transcription-panel");
const transcriptionText = document.getElementById("transcription-text");
const visitedFrames = new Set();

let transcriptions = null;

fetch("books/peniche/transcriptions.json")
  .then((response) => response.json())
  .then((data) => {
    transcriptions = data;
  });

function renderTranscription() {
  const entry = transcriptions ? transcriptions[String(state.currentPage)] : undefined;
  if (!entry) {
    transcriptionText.textContent = "Sem transcrição para esta página.";
    return;
  }

  const frameNumbers = [...new Set(Object.values(entry.jump_table))].sort((a, b) => a - b);
  const nav = document.createElement("div");
  frameNumbers.forEach((frameNumber) => {
    const link = document.createElement("span");
    link.textContent = frameNumber;
    link.className = "transcription-jump" + (visitedFrames.has(frameNumber) ? " visited" : "");
    link.addEventListener("click", () => {
      visitedFrames.add(frameNumber);
      showFrame(frameNumber);
    });
    nav.appendChild(link);
    nav.appendChild(document.createTextNode(" "));
  });

  const body = document.createElement("p");
  const firstFrame = Object.keys(entry.frames)[0];
  body.textContent = entry.frames[firstFrame] || "";

  transcriptionText.replaceChildren(nav, body);
  currentTranscriptionEntry = entry;
}

let currentTranscriptionEntry = null;

function showFrame(frameNumber) {
  const body = transcriptionText.querySelector("p");
  body.textContent = currentTranscriptionEntry.frames[frameNumber] || "";
  transcriptionText
    .querySelectorAll(".transcription-jump")
    .forEach((el) => {
      if (parseInt(el.textContent, 10) === frameNumber) el.classList.add("visited");
    });
}

document.getElementById("toggle-transcription").addEventListener("click", () => {
  transcriptionPanel.hidden = !transcriptionPanel.hidden;
  if (!transcriptionPanel.hidden) renderTranscription();
});

document.getElementById("close-transcription").addEventListener("click", () => {
  transcriptionPanel.hidden = true;
});
```

Add `if (!transcriptionPanel.hidden) renderTranscription();` at the end of the existing `goToPage` function (from Task 10) so the panel content refreshes if it's already open when the user navigates to a different page.

- [ ] **Step 2: Manually verify in a browser**

Reload, navigate to a page with a transcription (any page other than the blank one), click the "T" button — the panel opens showing prose text and a row of frame-number links; clicking a link swaps the displayed prose and grays out that link; closing and reopening the panel keeps the visited styling for the current session.

- [ ] **Step 3: Commit**

```bash
git add web/js/viewer.js
git commit -m "Add transcription panel with page-jump links"
```

---

### Task 13: Responsive/mobile layout and touch navigation

**Files:**
- Modify: `web/css/style.css`
- Modify: `web/js/viewer.js`

**Interfaces:**
- Consumes: existing `#toolbar`, `#transcription-panel`, `nextPage`/`prevPage` from earlier tasks.
- Produces: a toolbar that collapses to icon-only below 600px width, a full-screen transcription overlay on mobile instead of a side panel, and swipe-left/right gestures for page navigation.

- [ ] **Step 1: Add a mobile breakpoint to `web/css/style.css`**

```css
@media (max-width: 600px) {
  #toolbar {
    flex-wrap: wrap;
    gap: 0.25rem;
    padding: 0.35rem;
  }

  #toolbar button {
    font-size: 0.85rem;
    padding: 0.3rem 0.5rem;
  }

  #page-input {
    width: 3rem;
  }

  #transcription-panel {
    width: 100%;
    height: 100%;
  }
}
```

- [ ] **Step 2: Add swipe navigation to `web/js/viewer.js`**

```javascript
let touchStartX = null;

document.getElementById("page-area").addEventListener("touchstart", (event) => {
  touchStartX = event.changedTouches[0].clientX;
});

document.getElementById("page-area").addEventListener("touchend", (event) => {
  if (touchStartX === null) return;
  const deltaX = event.changedTouches[0].clientX - touchStartX;
  const SWIPE_THRESHOLD = 50;
  if (deltaX > SWIPE_THRESHOLD) prevPage();
  if (deltaX < -SWIPE_THRESHOLD) nextPage();
  touchStartX = null;
});
```

- [ ] **Step 3: Manually verify with browser dev tools device emulation**

Open dev tools, switch to a mobile device emulation (e.g. a 375px-wide viewport), reload the page, and confirm: the toolbar wraps/shrinks to fit without horizontal scrolling, opening the transcription panel covers the full screen, and simulated touch swipes (dev tools supports drag-to-simulate-touch) move to the next/previous page. If a physical phone is handy, load the same `http://<your-lan-ip>:8080` URL there and repeat the check.

- [ ] **Step 4: Commit**

```bash
git add web/css/style.css web/js/viewer.js
git commit -m "Add responsive layout and touch swipe navigation"
```

---

### Task 14: Full manual QA pass and final push

**Files:** none (verification only)

- [ ] **Step 1: Run the complete extraction test suite one more time**

```bash
cd ~/sources/cadernos-cunhal-web
python3 -m pytest extract/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Full desktop walkthrough**

Serve `web/` locally and, in a desktop browser, walk every page 1–28: confirm each facsimile image loads, the blank page (page 8) shows a plain white page instead of a broken image, every transcription page's panel opens with readable Portuguese text (not garbled, not a bare list of digits), and page-jump links move between the reconstructed frames correctly. Note and fix (by revisiting the relevant Task 3–7 function) any page that misbehaves.

- [ ] **Step 3: Full mobile walkthrough**

Repeat step 2 at a mobile viewport width (dev tools emulation, plus a real phone on the same LAN if convenient), confirming the responsive toolbar, full-screen transcription overlay, and swipe navigation all work end to end.

- [ ] **Step 4: Final push**

```bash
git push origin main
```

- [ ] **Step 5: Report back**

Summarize to the user: pilot complete, URL to browse the repo, and a recommendation on whether the same pipeline should be extended to the remaining four books (Caderno 1, Caderno 28, Caderno 43, Inventário) as a follow-up.
