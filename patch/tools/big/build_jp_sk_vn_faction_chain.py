#!/usr/bin/env python3
"""Restore unique Japan / South Korea / Vietnam faction load chains.

Does not touch aircraft INIs, air CommandSets, weapons, or ART meshes.

Fixes the last-wins VT72B override so each country dozer keeps its own
CommandSet, then detaches PlayerTemplate from BaseSide=Iraq / SCIENCE_Iraq.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_visual_correction/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/usa_visual_correction/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/jp_sk_vn_faction_chain")

VT72B_OVERRIDES = [
    (
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\VT72B.ini",
        "Japan_VT72B",
        "Japan_VT72B_UnusedIraqOverride",
    ),
    (
        r"Data\INI\Object\Specter\South Korean Armed Forces\Tracked\VT72B.ini",
        "SouthKorea_VT72B",
        "SouthKorea_VT72B_UnusedIraqOverride",
    ),
    (
        r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Tracked\VT72B.ini",
        "Vietnam_VT72B",
        "Vietnam_VT72B_UnusedIraqOverride",
    ),
]

CC_OVERRIDES = [
    (
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_CommandCenter.ini",
        "Japan_CommandCenter",
        "Japan_CommandCenter_UnusedIraqOverride",
    ),
    (
        r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_CommandCenter.ini",
        "SouthKorea_CommandCenter",
        "SouthKorea_CommandCenter_UnusedIraqOverride",
    ),
    (
        r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_CommandCenter.ini",
        "Vietnam_CommandCenter",
        "Vietnam_CommandCenter_UnusedIraqOverride",
    ),
]

FACTIONS = {
    "FactionJapan": ("Japan", "SCIENCE_Japan"),
    "FactionSouthKorea": ("SouthKorea", "SCIENCE_SouthKorea"),
    "FactionVietnam": ("Vietnam", "SCIENCE_Vietnam"),
}

SCIENCE_BLOCK = """
Science SCIENCE_Japan
  PrerequisiteSciences = None
  SciencePurchasePointCost = 0
  IsGrantable = No
End

Science SCIENCE_SouthKorea
  PrerequisiteSciences = None
  SciencePurchasePointCost = 0
  IsGrantable = No
End

Science SCIENCE_Vietnam
  PrerequisiteSciences = None
  SciencePurchasePointCost = 0
  IsGrantable = No
End
"""


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def unused_stub(obj: str) -> str:
    return (
        f"Object {obj}\r\n"
        f"  Buildable = No\r\n"
        f"  Side = Neutral\r\n"
        f"  EditorSorting = SYSTEM\r\n"
        f"  KindOf = PRELOAD IGNORED_IN_GUI\r\n"
        f"  Body = ActiveBody ModuleTag_01\r\n"
        f"    MaxHealth = 1.0\r\n"
        f"    InitialHealth = 1.0\r\n"
        f"  End\r\n"
        f"  Geometry = Box\r\n"
        f"  GeometryMajorRadius = 1.0\r\n"
        f"  GeometryMinorRadius = 1.0\r\n"
        f"  GeometryHeight = 1.0\r\n"
        f"End\r\n"
    )


def replace_object_with_stub(text: str, live_obj: str, stub_obj: str) -> str:
    pat = rf"(?ms)^Object\s+{re.escape(live_obj)}\s*\r?\n.*?(?=^Object\s|\Z)"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"Object {live_obj} missing")
    stub = unused_stub(stub_obj)
    if "\r\n" in text:
        stub = stub
    else:
        stub = stub.replace("\r\n", "\n")
    return text[: m.start()] + stub + text[m.end() :]


def retarget_player_template(text: str, faction: str, side: str, science: str) -> str:
    pat = rf"(?ms)^PlayerTemplate\s+{re.escape(faction)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{faction} missing")
    block = m.group(0)
    block = re.sub(
        r"(?m)^(\s*BaseSide\s*=\s*)\S+",
        rf"\1{side}",
        block,
    )
    block = re.sub(
        r"(?m)^(\s*IntrinsicSciences\s*=\s*)\S+",
        rf"\1{science}",
        block,
    )
    if "BaseSide          = Iraq" in block or "SCIENCE_Iraq" in block:
        raise SystemExit(f"{faction} still has Iraq after retarget")
    return text[: m.start()] + block + text[m.end() :]


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIGs", file=sys.stderr)
        return 1

    entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_names = [n for n, _ in entries]

    forbidden_air = (
        r"data\ini\object\specter\japan self-defense forces\airforce",
        r"data\ini\object\specter\republic of korea armed forces\airforce",
        r"data\ini\object\specter\vietnam people's army\airforce",
    )

    def mut(path: str, fn):
        key = norm(path)
        if any(key.startswith(p) for p in forbidden_air):
            raise SystemExit(f"refusing to touch aircraft INI {path}")
        i = index[key]
        name, blob = entries[i]
        old = blob.decode("latin1")
        new = fn(old)
        if new == old:
            raise SystemExit(f"no change {path}")
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    for path, live, stub in VT72B_OVERRIDES:
        mut(path, lambda t, live=live, stub=stub: replace_object_with_stub(t, live, stub))
        print("  neutralized", live, "->", stub)

    for path, live, stub in CC_OVERRIDES:
        mut(path, lambda t, live=live, stub=stub: replace_object_with_stub(t, live, stub))
        print("  neutralized CC duplicate", live, "->", stub)

    def patch_pt(text: str) -> str:
        for faction, (side, science) in FACTIONS.items():
            text = retarget_player_template(text, faction, side, science)
        return text

    mut(r"Data\INI\PlayerTemplate.ini", patch_pt)

    def patch_science(text: str) -> str:
        if "Science SCIENCE_Japan" in text:
            return text
        newline = nl(text)
        block = SCIENCE_BLOCK.replace("\n", newline).strip(newline) + newline
        return text.rstrip("\r\n") + newline + newline + block

    mut(r"Data\INI\Science.ini", patch_science)

    # Guard: aircraft INI bytes unchanged vs source.
    src_entries = parse_big(SRC_DATA)
    for (n, old), (_, new) in zip(src_entries, entries):
        key = norm(n)
        if any(key.startswith(p) for p in forbidden_air):
            if old != new:
                raise SystemExit(f"aircraft INI mutated {n}")

    if [n for n, _ in entries] != original_names:
        raise SystemExit("DATA entry order/names changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packed = build_big_ordered(entries)
    out_data = OUT_DIR / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    print("wrote", out_data, "size", len(packed), "files", len(entries), "sha", hashlib.sha256(packed).hexdigest())

    art = SRC_ART.read_bytes()
    out_art = OUT_DIR / "_SPEC_ART_ONE.big"
    out_art.write_bytes(art)
    print("copied ART", out_art, "size", len(art), "sha", hashlib.sha256(art).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
