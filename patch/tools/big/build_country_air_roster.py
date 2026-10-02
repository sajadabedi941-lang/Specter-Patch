#!/usr/bin/env python3
"""Apply JP/SK/VN aircraft only through country CommandSets.

Never mutates CommandCenter, Dozer, VT72B, PlayerTemplate, or Science.
Never packs overlay CommandSet_Japan/SouthKorea/Vietnam.ini as extra files.
Never copies Iraq aircraft.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_air_roster import (
    COUNTRIES,
    DO_NOT_PACK_OVERLAY,
    LOCKED_BIG_PATHS,
    LOCKED_COMMANDSETS,
    all_aircraft,
    button_text,
    commandset_text,
    is_iraq_name,
)

SRC_DATA = Path("/tmp/vietnam_air_buttons/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/vietnam_air_buttons/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/country_air_roster")


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


def to_nl(block: str, newline: str) -> str:
    return block.replace("\r\n", "\n").replace("\n", newline).strip("\n") + newline


def named(text: str, kind: str, name: str):
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$", text)
    return m.group(0) if m else None


def replace_named_block(text: str, kind: str, name: str, replacement: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIGs", file=sys.stderr)
        return 1

    src_entries = parse_big(SRC_DATA)
    entries = list(src_entries)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_names = [n for n, _ in entries]

    for banned in DO_NOT_PACK_OVERLAY:
        if norm(banned) in index:
            raise SystemExit(f"refusing to keep overlay poison file {banned}")

    locked_before = {norm(p): src_entries[index[norm(p)]][1] for p in LOCKED_BIG_PATHS}
    src_cs = src_entries[index[norm(r"Data\INI\CommandSet.ini")]][1].decode("latin1")
    locked_cs_before = {name: named(src_cs, "CommandSet", name) for name in LOCKED_COMMANDSETS}

    def mut(path: str, fn):
        key = norm(path)
        if key in {norm(p) for p in LOCKED_BIG_PATHS}:
            raise SystemExit(f"refusing to mutate locked faction file {path}")
        i = index[key]
        name, blob = entries[i]
        old = blob.decode("latin1")
        new = fn(old)
        if new == old:
            print("unchanged", path)
            return
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    def patch_commandset(text: str) -> str:
        for country in COUNTRIES:
            text = replace_named_block(text, "CommandSet", country.air_cs, commandset_text(country.air_cs, country.fighters))
            text = replace_named_block(text, "CommandSet", country.heavy_cs, commandset_text(country.heavy_cs, country.heavy))
        after = {name: named(text, "CommandSet", name) for name in LOCKED_COMMANDSETS}
        for name, before in locked_cs_before.items():
            if after[name] != before:
                raise SystemExit(f"locked CommandSet mutated: {name}")
        for country in COUNTRIES:
            for row in (*country.fighters, *country.heavy):
                if is_iraq_name(row.obj) or is_iraq_name(row.button):
                    raise SystemExit(f"roster has Iraq aircraft {row}")
        return text

    def patch_commandbutton(text: str) -> str:
        extra = []
        for country, _kind, row in all_aircraft():
            if is_iraq_name(row.obj) or is_iraq_name(row.button) or is_iraq_name(row.image):
                raise SystemExit(f"refusing Iraq button {row}")
            blk = named(text, "CommandButton", row.button)
            wanted = button_text(row)
            if not blk:
                extra.append(wanted)
                print("  add button", row.button, "->", row.obj)
                continue
            obj = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", blk)
            img = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", blk)
            cmd = re.search(r"(?m)^\s*Command\s*=\s*(\S+)", blk)
            if obj and is_iraq_name(obj.group(1)):
                raise SystemExit(f"{row.button} still builds Iraq {obj.group(1)}")
            needs = False
            if not obj or obj.group(1) != row.obj:
                needs = True
            if not cmd or cmd.group(1) != "UNIT_BUILD":
                needs = True
            if img and (img.group(1).lower().startswith("irq_") or img.group(1) != row.image):
                if img.group(1).lower().startswith("irq_") or img.group(1) != row.image:
                    needs = True
            if needs:
                text = replace_named_block(text, "CommandButton", row.button, wanted)
                print("  retarget button", row.button, "->", row.obj, row.image)
        if extra:
            newline = nl(text)
            text = text.rstrip("\r\n") + newline + newline + "".join(
                to_nl(b, newline) for b in extra
            )
        return text

    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)

    for (n, old), (_, new) in zip(src_entries, entries):
        key = norm(n)
        if key in {norm(p) for p in LOCKED_BIG_PATHS} and old != new:
            raise SystemExit(f"locked faction file changed {n}")
        if key not in (norm(r"Data\INI\CommandSet.ini"), norm(r"Data\INI\CommandButton.ini")):
            if old != new:
                raise SystemExit(f"unexpected mutation {n}")

    if [n for n, _ in entries] != original_names:
        raise SystemExit("DATA entry order/names changed")

    for p, before in locked_before.items():
        if entries[index[p]][1] != before:
            raise SystemExit(f"locked blob changed {p}")

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
