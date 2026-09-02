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

from extract.books import BOOKS
from extract.manifests import PAGES_BY_SLUG

DEFAULT_SOURCE_DIR = Path("/run/media/user/Cadernos/cfg")
WEB_BOOKS_DIR = Path(__file__).parent.parent / "web" / "books"
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
