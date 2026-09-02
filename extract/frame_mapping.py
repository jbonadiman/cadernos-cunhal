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
