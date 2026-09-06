#!/usr/bin/env python3
"""Make Vietnam air production reachable.

Japan / South Korea CommandSets, buttons, and aircraft INIs are not touched.
Vietnam aircraft INIs and ART are not touched.

Adds the missing Command_ConstructVietnamJet* UNIT_BUILD buttons and points
Vietnam_LargeAirBase / Vietnam_HeavyAirBase at the required Vietnam list.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/jp_sk_vn_faction_chain/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/jp_sk_vn_faction_chain/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/vietnam_air_buttons")

# Required fighters. MiG-29 already has Command_ConstructVietnamAir_Mig29S;
# add the Jet-named alias so the airfield bar is all Command_ConstructVietnamJet*.
FIGHTER_BUTTONS = [
    ("Command_ConstructVietnamJetMig29S", "VietnamJetMig29S", "irq_mig29a"),
    ("Command_ConstructVietnamJetMig21", "VietnamJetMig21", "SPEC_VietnamJetMig21"),
    ("Command_ConstructVietnamJetSu22", "VietnamJetSu22", "SPEC_VietnamJetSu22"),
    ("Command_ConstructVietnamJetSu27", "VietnamJetSu27", "SPEC_VietnamJetSu27"),
    ("Command_ConstructVietnamJetSu30", "VietnamJetSu30", "SPEC_VietnamJetSu30"),
    ("Command_ConstructVietnamJetYak130", "VietnamJetYak130", "SPEC_VietnamJetYak130"),
    ("Command_ConstructVietnamJetF5E", "VietnamJetF5E", "SPEC_VietnamJetF5E"),
]

HEAVY_BUTTONS = [
    ("Command_ConstructVietnamJetMi8", "VietnamJetMi8"),
    ("Command_ConstructVietnamJetMi17", "VietnamJetMi17"),
    ("Command_ConstructVietnamJetIL76", "VietnamJetIL76"),
]

AIRFIELD_CS = """
CommandSet Vietnam_AirfieldCommandSet
  1 = Command_ConstructVietnamJetMig29S
  2 = Command_ConstructVietnamJetMig21
  3 = Command_ConstructVietnamJetSu22
  4 = Command_ConstructVietnamJetSu27
  5 = Command_ConstructVietnamJetSu30
  6 = Command_ConstructVietnamJetYak130
  7 = Command_ConstructVietnamJetF5E
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

HEAVY_CS = """
CommandSet Vietnam_HeavyAirBaseCommandSet
  1 = Command_ConstructVietnamJetMi8
  2 = Command_ConstructVietnamJetMi17
  3 = Command_ConstructVietnamJetIL76
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

FORBIDDEN_MUTATIONS = (
    r"data\ini\object\specter\japan self-defense forces\airforce",
    r"data\ini\object\specter\republic of korea armed forces\airforce",
    r"data\ini\object\specter\vietnam people's army\airforce",
    r"data\ini\object\specter\vietnam people's armed forces\airforce",
)

PROTECTED_COMMANDSETS = (
    "Japan_AirfieldCommandSet",
    "Japan_HeavyAirBaseCommandSet",
    "SouthKorea_AirfieldCommandSet",
    "SouthKorea_HeavyAirBaseCommandSet",
    "Japan_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
)


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


def replace_named_block(text: str, kind: str, name: str, replacement: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def button_block(name: str, obj: str, image: str) -> str:
    short = name[len("Command_Construct") :]
    return (
        f"CommandButton {name}\r\n"
        f"  Command       = UNIT_BUILD\r\n"
        f"  Object        = {obj}\r\n"
        f"  TextLabel     = CONTROLBAR:Construct{short}\r\n"
        f"  ButtonImage   = {image}\r\n"
        f"  ButtonBorderType = BUILD\r\n"
        f"  DescriptLabel = CONTROLBAR:ToolTip{short}\r\n"
        f"End\r\n"
    )


def named(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$", text)
    return m.group(0) if m else None


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIGs", file=sys.stderr)
        return 1

    src_entries = parse_big(SRC_DATA)
    entries = list(src_entries)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_names = [n for n, _ in entries]
    src_cs = src_entries[index[norm(r"Data\INI\CommandSet.ini")]][1].decode("latin1")
    protected_before = {name: named(src_cs, "CommandSet", name) for name in PROTECTED_COMMANDSETS}

    def mut(path: str, fn):
        key = norm(path)
        if any(key.startswith(p) for p in FORBIDDEN_MUTATIONS):
            raise SystemExit(f"refusing to touch aircraft INI {path}")
        i = index[key]
        name, blob = entries[i]
        old = blob.decode("latin1")
        new = fn(old)
        if new == old:
            raise SystemExit(f"no change {path}")
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    def patch_commandbutton(text: str) -> str:
        extra = []
        for name, obj, image in FIGHTER_BUTTONS:
            if f"CommandButton {name}" not in text:
                extra.append(button_block(name, obj, image))
                print("  add button", name, "->", obj)
            else:
                print("  keep button", name)
        if not extra:
            raise SystemExit("all fighter buttons already present")
        newline = nl(text)
        return (
            text.rstrip("\r\n")
            + newline
            + newline
            + "".join(b.replace("\r\n", newline) for b in extra)
            + newline
        )

    def patch_commandset(text: str) -> str:
        text = replace_named_block(text, "CommandSet", "Vietnam_AirfieldCommandSet", AIRFIELD_CS)
        text = replace_named_block(text, "CommandSet", "Vietnam_HeavyAirBaseCommandSet", HEAVY_CS)
        after = {name: named(text, "CommandSet", name) for name in PROTECTED_COMMANDSETS}
        for name, before in protected_before.items():
            if after[name] != before:
                raise SystemExit(f"protected CommandSet mutated: {name}")
        return text

    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)
    mut(r"Data\INI\CommandSet.ini", patch_commandset)

    for (n, old), (_, new) in zip(src_entries, entries):
        key = norm(n)
        if any(key.startswith(p) for p in FORBIDDEN_MUTATIONS):
            if old != new:
                raise SystemExit(f"aircraft INI mutated {n}")
        if key not in (norm(r"Data\INI\CommandButton.ini"), norm(r"Data\INI\CommandSet.ini")):
            if old != new:
                raise SystemExit(f"unexpected mutation {n}")

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
