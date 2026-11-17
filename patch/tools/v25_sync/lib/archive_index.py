"""Index filenames inside the V25 split zip without extracting ART.

Used to tell 'missing from parsed VFS/extract' apart from 'missing from the archive'.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import archive


def listing_path(cache: Path) -> Path:
    return cache / "v25_archive_listing.txt"


def build_listing(zip_path: Path, cache: Path) -> Path:
    dest = listing_path(cache)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest
    text = archive.list_archive(zip_path)
    dest.write_text(text, encoding="utf-8", errors="replace")
    return dest


def parse_listing(text: str) -> dict:
    files: list[str] = []
    stems: dict[str, list[str]] = {}
    for line in text.splitlines():
        if "Generals Silent Death V25/" not in line and "Generals Silent Death V25\\" not in line:
            # 7z listing ends with the path in the last column.
            parts = line.split()
            if not parts:
                continue
            path = parts[-1]
        else:
            path = line[line.index("Generals Silent Death V25/") :] if "Generals Silent Death V25/" in line else line.split()[-1]
        if path.endswith("/") or path.endswith("\\"):
            continue
        if "Generals Silent Death" not in path and "Data" not in path and "Art" not in path:
            if "." not in path.split("/")[-1]:
                continue
        files.append(path)
        base = path.replace("\\", "/").rsplit("/", 1)[-1]
        if "." in base:
            stem = base.rsplit(".", 1)[0].lower()
            stems.setdefault(stem, []).append(path)
    return {"file_count": len(files), "stems": stems, "files": files}


class ArchiveIndex:
    def __init__(self, zip_path: Path, cache: Path):
        listing = build_listing(zip_path, cache)
        parsed = parse_listing(listing.read_text(encoding="utf-8", errors="replace"))
        self.stems: dict[str, list[str]] = parsed["stems"]
        self.file_count = parsed["file_count"]
        self._files_l = [f.lower().replace("\\", "/") for f in parsed["files"]]
        (cache / "v25_archive_stems.json").write_text(
            json.dumps({"file_count": self.file_count, "stem_count": len(self.stems)}) + "\n"
        )

    def find_stem(self, name: str) -> list[str]:
        if not name:
            return []
        stem = name.replace("\\", "/").rsplit("/", 1)[-1]
        if "." in stem:
            stem = stem.rsplit(".", 1)[0]
        return list(self.stems.get(stem.lower(), []))

    def has_stem(self, name: str) -> bool:
        return bool(self.find_stem(name))
