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
