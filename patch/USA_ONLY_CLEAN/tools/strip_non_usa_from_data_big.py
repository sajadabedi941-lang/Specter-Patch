#!/usr/bin/env python3
"""USA DATA cleaner focused on String Manager + CommandSet crash sources.

Does NOT delete USA aircraft INIs.
Does NOT edit CommandSet.ini.

Kills only:
- Broken English *.txt overlays (STRINGS_TO_ADD, FactionFramework, FactionExpansion, ...)
- Multi-faction CommandSet_AdvancedAirBase.ini (hundreds of unresolved button refs)
- Multi-faction AAB overlays that redefine America heavies / runway bones
  (Aircraft_AAB_Global, Aircraft_AAB_StrategicBombers, AdvancedAirBase_AllFactions,
   AdvancedAirBase_FutureFactions, CommandButton_AdvancedAirBase_SpecterFactions)

USA aircraft objects that lived only in AAB_Global are provided by
Aircraft_USA_AAB_Fighters.ini in USA_ONLY_CLEAN.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

KEEP_ENGLISH_TXT = {
    "advancedairbase_strings.txt",
    "advancedawacs_strings.txt",
    "usa_heavyaircraft_strings.txt",
}

# Exact relative paths (normalized) that redefine USA heavies / break AAB.
KILL_EXACT = {
    "data\\ini\\object\\specter\\patchsystems\\advancedairbase\\aircraft_aab_global.ini",
    "data\\ini\\object\\specter\\patchsystems\\advancedairbase\\aircraft_aab_strategicbombers.ini",
    "data\\ini\\object\\specter\\patchsystems\\advancedairbase_allfactions.ini",
    "data\\ini\\object\\specter\\patchsystems\\advancedairbase_futurefactions.ini",
    "data\\ini\\commandbutton_advancedairbase_specterfactions.ini",
    "data\\ini\\commandset_advancedairbase.ini",
}


def read_big(path: Path):
    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        sz = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + sz]))
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


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def should_kill(name: str) -> bool:
    low = norm(name)

    # Never touch stock CommandSet.ini
    if low == "data\\ini\\commandset.ini":
        return False

    if low in KILL_EXACT:
        return True

    # English string dumps: whitelist USA ASCII overlays only.
    if "\\english\\" in low and low.endswith(".txt"):
        base = low.rsplit("\\", 1)[-1]
        if base in KEEP_ENGLISH_TXT:
            return False
        # Known String Manager crash sources
        if (
            base == "strings_to_add.txt"
            or base == "factionframework_strings.txt"
            or base.startswith("factionexpansion_")
            or base.startswith("airforce")
            or "faction" in base
            or "turkey" in base
        ):
            return True
        # Any other English .txt overlay is unsafe for String Manager init.
        return True

    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()
    kept = {}
    killed = []
    for name, blob in read_big(args.data_big):
        if should_kill(name):
            killed.append(name)
            continue
        kept[name] = blob
    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    args.out_big.write_bytes(build_big(kept))
    print(f"killed={len(killed)} kept={len(kept)} -> {args.out_big}")
    for n in sorted(killed):
        print("  kill", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
