#!/usr/bin/env python3
"""Build complete drop-in _SPEC_DATA_ONE.big with current patch/Data + Turkey reset.

Usage:
  python3 patch/tools/big/build_specter_full_turkey_reset_release_big.py \
    --base /path/_SPEC_DATA_ONE.big \
    --patch-root patch \
    --out-dir patch/Release/SPECTER_FULL_TURKEY_RESET_RELEASE
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STOCK_SKIP = {
    "data\\ini\\weapon.ini",
    "data\\ini\\commandbutton.ini",
    "data\\ini\\commandset.ini",
    "data\\ini\\armor.ini",
    "data\\ini\\locomotor.ini",
}


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--patch-root", type=Path, default=Path("patch"))
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_FULL_TURKEY_RESET_RELEASE"),
    )
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    entries, raw = read_big(args.base)
    data_map: dict[str, tuple[str, bytes]] = {}
    for name, off, size in entries:
        data_map[norm_key(name)] = (name.replace("/", "\\"), raw[off : off + size])

    added = updated = skipped = 0
    patch_data = args.patch_root / "Data"
    for path in sorted(patch_data.rglob("*")):
        if not path.is_file() or path.suffix.lower() in {".md", ".pyc"}:
            continue
        rel = path.relative_to(patch_data).as_posix()
        big_path = "Data\\" + rel.replace("/", "\\")
        key = norm_key(big_path)
        if key in STOCK_SKIP:
            skipped += 1
            continue
        content = path.read_bytes()
        if key in data_map:
            old_name, old = data_map[key]
            if old != content and old.rstrip(b"\x00") != content.rstrip(b"\x00"):
                data_map[key] = (old_name, content)
                updated += 1
        else:
            data_map[key] = (big_path, content)
            added += 1

    final = {name: content for _, (name, content) in sorted(data_map.items())}
    big = build_big(final)
    out_big = args.out_dir / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    print(f"added={added} updated={updated} skipped_stock={skipped} final={len(final)}")
    print(f"Wrote {out_big} ({len(big)}) SHA256={sha}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    (args.out_dir / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={sha}\nentries={len(final)}\nsize={len(big)}\n",
        encoding="utf-8",
    )
    zip_path = args.out_dir / "_SPEC_DATA_ONE_FULL_TURKEY_RESET.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_big, arcname="_SPEC_DATA_ONE.big")
        for fname in ("README_INSTALL.txt", "HASHES.txt", "VERIFY_REPORT.txt"):
            p = args.out_dir / fname
            if p.exists():
                zf.write(p, arcname=fname)
    print(f"Wrote {zip_path} ({zip_path.stat().st_size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
