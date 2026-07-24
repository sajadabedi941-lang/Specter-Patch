#!/usr/bin/env python3
"""Merge Cursor patch Data/Art into Specter _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Preserves all original BIG entries. Skips overwriting stock cores:
  Weapon.ini, CommandButton.ini, CommandSet.ini, Armor.ini, Locomotor.ini

Usage:
  python3 merge_patch_into_spec_big.py \\
    --data-big /path/_SPEC_DATA_ONE.big \\
    --art-big /path/_SPEC_ART_ONE.big \\
    --patch-root /path/to/patch \\
    --out-dir /path/out
"""

from __future__ import annotations

import argparse
import hashlib
import struct
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
        raise ValueError(f"Not a BIGF archive: {path}")
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
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    total_size = offset
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", total_size)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--art-big", type=Path, required=True)
    ap.add_argument("--patch-root", type=Path, required=True, help="Folder containing Data/ and Art/")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    patch_data = args.patch_root / "Data"
    patch_art = args.patch_root / "Art"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    data_entries, data_raw = read_big(args.data_big)
    art_entries, art_raw = read_big(args.art_big)

    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys: list[str] = []
    for name, off, size in data_entries:
        key = norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])

    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys: list[str] = []
    for name, off, size in art_entries:
        key = norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    added = updated = skipped_stock = 0

    def merge_data(big_path: str, content: bytes) -> None:
        nonlocal added, updated, skipped_stock
        key = norm_key(big_path)
        if key in STOCK_SKIP:
            skipped_stock += 1
            return
        display = big_path.replace("/", "\\")
        if key in data_map:
            old_name, old = data_map[key]
            if old == content or old.rstrip(b"\x00") == content.rstrip(b"\x00"):
                return
            data_map[key] = (old_name, content)
            updated += 1
        else:
            data_map[key] = (display, content)
            added += 1

    for path in sorted((patch_data).rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(patch_data).as_posix()
        merge_data("Data\\" + rel.replace("/", "\\"), path.read_bytes())

    art_added = art_updated = 0
    if patch_art.exists():
        for path in sorted(patch_art.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(args.patch_root).as_posix()
            big_path = rel.replace("/", "\\")
            key = norm_key(big_path)
            content = path.read_bytes()
            if key in art_map:
                old_name, old = art_map[key]
                if old != content and old.rstrip(b"\x00") != content.rstrip(b"\x00"):
                    art_map[key] = (old_name, content)
                    art_updated += 1
            else:
                art_map[key] = (big_path, content)
                art_added += 1

    def finalize(order_keys, amap):
        final = {}
        seen = set()
        for key in order_keys:
            name, content = amap[key]
            final[name] = content
            seen.add(key)
        for key, (name, content) in sorted(amap.items(), key=lambda kv: kv[0]):
            if key not in seen:
                final[name] = content
        return final

    final_data = finalize(data_keys, data_map)
    final_art = finalize(art_keys, art_map)

    out_data = args.out_dir / "_SPEC_DATA_ONE.big"
    out_art = args.out_dir / "_SPEC_ART_ONE.big"
    data_bytes = build_big(final_data)
    art_bytes = build_big(final_art)
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    print(f"DATA: preserved={len(data_entries)} added={added} updated={updated} skipped_stock={skipped_stock} final={len(final_data)}")
    print(f"ART:  preserved={len(art_entries)} added={art_added} updated={art_updated} final={len(final_art)}")
    print(f"Wrote {out_data} ({len(data_bytes)} bytes) SHA256={hashlib.sha256(data_bytes).hexdigest()}")
    print(f"Wrote {out_art} ({len(art_bytes)} bytes) SHA256={hashlib.sha256(art_bytes).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
