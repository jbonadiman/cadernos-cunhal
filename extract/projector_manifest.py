"""Recover a book's page manifest directly from its "make projector"
.exe, replacing the one-off manual process used for the Peniche pilot
with a repeatable, tested tool. See extract/manifests/peniche.py's
hand-authored list for the regression target this module is checked
against (Task 7)."""

import re
import struct
from pathlib import Path

from extract.swf_tags import scan_tag_types, DEFINE_BUTTON2

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
