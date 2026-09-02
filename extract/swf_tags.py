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
