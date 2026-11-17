#!/usr/bin/env python3
"""Print install identity for SPECTER Zero Hour folders.

Run this on every multiplayer PC (or point --root at a copy of the
game folder) and compare the four outputs. Different hashes mean the
clients are not simulating the same INI/BIG set.

This script does not modify files.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

WATCH_LOOSE = (
    "Data/INI/CommandSet.ini",
    "Data/INI/CommandButton.ini",
    "Data/INI/PlayerTemplate.ini",
    "Data/INI/Weapon.ini",
    "Data/INI/ObjectCreationList.ini",
    "Data/INI/GameData.ini",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default=".",
        help="Zero Hour / SPECTER folder (contains generals.exe)",
    )
    args = ap.parse_args()
    root = Path(args.root).resolve()
    print("SPECTER MP install identity")
    print("root", root)
    exe = root / "generals.exe"
    if not exe.is_file() and not (root / "Generals.exe").is_file():
        print("WARN: generals.exe not in root (still hashing)")
    bigs = sorted(root.glob("*.big"), key=lambda p: p.name.lower())
    print("big_count", len(bigs))
    for p in bigs:
        print(f"BIG {p.name} {p.stat().st_size} {sha256(p)}")
    print("loose_ini")
    for rel in WATCH_LOOSE:
        p = root / rel.replace("/", "\\")
        if not p.is_file():
            p = root / rel
        if p.is_file():
            print(f"LOOSE {rel} {p.stat().st_size} {sha256(p)}")
        else:
            print(f"LOOSE {rel} MISSING")
    obj = root / "Data" / "INI" / "Object"
    if obj.is_dir():
        files = [p for p in obj.rglob("*") if p.is_file()]
        print("loose_object_files", len(files))
        if files:
            digest = hashlib.sha256()
            for p in sorted(files, key=lambda q: str(q).lower()):
                rel = p.relative_to(root).as_posix()
                digest.update(rel.encode("utf-8", "replace"))
                digest.update(b"\0")
                digest.update(p.read_bytes())
            print("loose_object_tree_sha256", digest.hexdigest())
            for p in files[:40]:
                print("LOOSEOBJ", p.relative_to(root).as_posix())
            if len(files) > 40:
                print("LOOSEOBJ ...", len(files) - 40, "more")
    else:
        print("loose_object_files", 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
