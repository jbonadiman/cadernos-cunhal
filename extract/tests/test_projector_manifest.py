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
