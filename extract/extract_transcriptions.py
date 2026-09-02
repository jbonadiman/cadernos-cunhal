"""Reconstruct the transcription prose for each Peniche page that has a
transcription overlay.

Usage:
    python3 -m extract.extract_transcriptions [--source DIR] [--output FILE]
"""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from extract.frame_mapping import map_char_ids_to_frames
from extract.books import BOOKS
from extract.manifests import PAGES_BY_SLUG
from extract.swf_tags import decompress_swf, tags_start_offset
from extract.text_filters import is_navigation_label

DEFAULT_SOURCE_DIR = Path("/run/media/user/Cadernos/cfg")
WEB_BOOKS_DIR = Path(__file__).parent.parent / "web" / "books"


def assemble_page_transcription(
    frame_to_chars: dict[int, set[int]],
    text_by_char_id: dict[int, str],
) -> str:
    frame_texts = []
    for frame_number, char_ids in sorted(frame_to_chars.items()):
        lines = []
        for char_id in sorted(char_ids):
            text = text_by_char_id.get(char_id)
            if text is None or is_navigation_label(text):
                continue
            lines.append(text)
        if lines:
            frame_texts.append("\n".join(lines))

    return "\n".join(frame_texts)


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


def build_transcription_for_page(swf_path: Path) -> str:
    data = swf_path.read_bytes()
    body = decompress_swf(data)
    start = tags_start_offset(body)
    frame_to_chars = map_char_ids_to_frames(body, start)
    text_by_char_id = _read_char_id_texts(swf_path)
    return assemble_page_transcription(frame_to_chars, text_by_char_id)


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
