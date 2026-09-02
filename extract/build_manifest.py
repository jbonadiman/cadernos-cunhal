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
