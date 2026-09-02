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
