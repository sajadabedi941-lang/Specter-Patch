#!/usr/bin/env python3
"""Strip non-USA Specter faction entries from a DATA BIG. Does not edit CommandSet.ini."""
from __future__ import annotations
import argparse, re, struct
from pathlib import Path

def read_big(path: Path):
    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off = struct.unpack(">I", data[pos:pos+4])[0]
        sz = struct.unpack(">I", data[pos+4:pos+8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off:off+sz]))
    return entries

def build_big(file_map: dict) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)

def should_kill(name: str) -> bool:
    low = name.replace("/", "\\").lower()
    if "united states of america" in low or "aaa_usa" in low or "commandbutton_usa_" in low or "commandset_usa_" in low:
        return False
    # Multi-faction aircraft overlays redefine USA heavies (incl. E3) and other countries.
    if low.endswith("aircraft_aab_global.ini") or low.endswith("aircraft_airforcefinal.ini"):
        return True
    if low.endswith("aircraft_aab_strategicbombers.ini"):
        return True
    # AllFactions/FutureFactions AAB redefine America_AdvancedAirBase and wipe ABAirF2 3x2 bones.
    if low.endswith("advancedairbase_allfactions.ini") or low.endswith("advancedairbase_futurefactions.ini"):
        return True
    # Keep only America drones under PatchSystems/Drones.
    if "\\patchsystems\\drones\\" in low:
        base = low.rsplit("\\", 1)[-1]
        if not base.startswith("america_"):
            return True
    if "playertemplate_specterpatch" in low or "commandbutton_factionexpansion" in low:
        return True
    if "object\\specter\\" in low:
        first = low.split("object\\specter\\", 1)[1].split("\\", 1)[0]
        if first in ("united states of america", "patchsystems"):
            return False
        return True
    for term in ["egypt","britain","france","germany","india","pakistan","saudi","uae","turkey","ukraine","japan","taiwan","korea","sweden","italy","syria","libya","vietnam","southafrica","united nations","nato","russia","iran","iraq","israel","arabic","factionexpansion"]:
        if term in low and "civilian" not in low:
            return True
    return False

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()
    kept = {}
    killed = 0
    for name, blob in read_big(args.data_big):
        if should_kill(name):
            killed += 1
            continue
        kept[name] = blob
    args.out_big.write_bytes(build_big(kept))
    print(f"killed={killed} kept={len(kept)} -> {args.out_big}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
