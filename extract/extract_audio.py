"""Extract an embedded sound asset (by its SWF linkage/export name) from
a SWF file as a standalone playable file.

Usage:
    python3 -m extract.extract_audio SWF_PATH LINKAGE_NAME DEST_PATH
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def extract_sound(swf_path: Path, linkage_name: str, dest_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffdec", "-export", "sound", tmp, str(swf_path)],
            check=True,
            capture_output=True,
        )
        matches = [
            p for p in Path(tmp).glob(f"*{linkage_name}*") if p.suffix != ".wav"
        ]
        if not matches:
            raise RuntimeError(
                f"no exported sound matching '{linkage_name}' found for {swf_path}"
            )
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(matches[0], dest_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("swf_path", type=Path)
    parser.add_argument("linkage_name")
    parser.add_argument("dest_path", type=Path)
    args = parser.parse_args()
    extract_sound(args.swf_path, args.linkage_name, args.dest_path)
    print(f"wrote {args.dest_path}")
