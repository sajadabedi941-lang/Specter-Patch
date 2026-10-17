#!/usr/bin/env python3
"""Surgical USA Air Force correction pass into packed _SPEC_DATA_ONE.big.

Base: last bug-fix DATA (2782 files). Preserves entry order.
Does not pack overlay CommandSet.ini as a whole file.
Does not overwrite F22A_AA.ini / F22A_AG.ini loadouts (Buildable flag only).
Does not restore C17GlobalMasterCommandSet fire button (Russia An-124/IL-76 share it).
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_bugfix_pass/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/usa_correction_pass")
PATCH = Path("/workspace/patch/Data/INI")

OBJECT_REPLACEMENTS = {
    r"Data\INI\Object\Specter\United States Of America\Drones\AmericaUAVGlobalHawk.ini":
        PATCH / "Object/Specter/United States Of America/Drones/AmericaUAVGlobalHawk.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini":
        PATCH / "Object/Specter/United States Of America/AmericaJetC17Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F35C_AA.ini":
        PATCH / "Object/Specter/United States Of America/Airforce/F35C_AA.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetAuterF22.ini":
        PATCH / "Object/Specter/United States Of America/Airforce/AmericaJetAuterF22.ini",
}

B52_POINT_OCL = """
ObjectCreationList OCL_AmericaB52TargetCarpetLine
  CreateObject
    Offset = X:0 Y:0 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:94
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:98
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:102
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:106
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:110
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:114
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:118
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:122
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:126
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:130
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:0 Z:134
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
End
"""

C17_SHARED_RESTORE = """CommandSet C17GlobalMasterCommandSet
  1 = Command_TransportExit
  2 = Command_TransportExit
  3 = Command_TransportExit
  4 = Command_TransportExit
  5 = Command_TransportExit
  6 = Command_TransportExit
  7 = Command_TransportExit
  8 = Command_TransportExit
  9 = Command_TransportExit
  10 = Command_TransportExit
  11 = Command_ChinookUnload
  13 = Command_Guard
  14 = Command_Stop
End
"""

C17_USA_COMMANDSET = """
CommandSet AmericaC17StarlifterCommandSet
  1 = Command_AmericaC17ParaDrop
  2 = Command_TransportExit
  3 = Command_TransportExit
  4 = Command_TransportExit
  5 = Command_TransportExit
  6 = Command_TransportExit
  7 = Command_TransportExit
  8 = Command_TransportExit
  9 = Command_ChinookUnload
  10 = Command_CombatDrop
  13 = Command_Guard
  14 = Command_Stop
End
"""

AUTER_BUTTON = """
CommandButton Command_ConstructAmericaJetAuterF22
  Command       = UNIT_BUILD
  Object        = AmericaJetAuterF22
  TextLabel     = CONTROLBAR:ConstructAmericaJetAuterF22
  ButtonImage   = us_f22a
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipAmericaJetAuterF22
End
"""

C17_DROP_BUTTON = """
CommandButton Command_AmericaC17ParaDrop
  Command           = SPECIAL_POWER
  SpecialPower      = SpecialPowerAmericaC17ParaDrop
  Options           = OK_FOR_MULTI_SELECT NEED_TARGET_POS
  TextLabel         = CONTROLBAR:CombatDrop
  ButtonImage       = SSChinookDrop
  ButtonBorderType  = ACTION
  DescriptLabel     = CONTROLBAR:ToolTipUSACombatDrop
  RadiusCursorType  = PARADROP
  InvalidCursorName = GenericInvalid
End
"""

C17_SPECIALPOWER = """
SpecialPower SpecialPowerAmericaC17ParaDrop
  Enum               = SPECIAL_HELIX_NAPALM_BOMB
  ReloadTime         = 8000
  RadiusCursorRadius = 80
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
    encoded = []
    for name, blob in entries:
        nb = name.encode("latin1")
        encoded.append((nb, blob))
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
    return block.replace("\r\n", "\n").replace("\n", newline)


def replace_block(text: str, start_pat: str, replacement: str) -> str:
    m = re.search(start_pat, text, re.S | re.M)
    if not m:
        raise SystemExit(f"block not found: {start_pat}")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def append_if_missing(text: str, needle: str, block: str) -> str:
    if needle in text:
        return text
    newline = nl(text)
    return text.rstrip("\r\n") + newline + to_nl(block, newline) + newline


def patch_weapon(text: str) -> str:
    m = re.search(
        r"^Weapon AmericaGlobalHawk_4xAGM\s*.*?^End\s*",
        text,
        re.S | re.M,
    )
    if not m:
        raise SystemExit("AmericaGlobalHawk_4xAGM not found")
    block = m.group(0)
    new_block, n = re.subn(
        r"AttackRange\s+=\s+\S+",
        "AttackRange                 = 1100",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit("Global Hawk AttackRange not patched")
    if "ClipSize                    = 4" not in new_block and "ClipSize = 4" not in new_block:
        raise SystemExit("Global Hawk ClipSize 4 missing")
    if "AGM114N_Object_DL" not in new_block:
        raise SystemExit("Global Hawk guided projectile missing")
    return text[: m.start()] + new_block + text[m.end() :]


def patch_ocl(text: str) -> str:
    if "OCL_AmericaB52TargetCarpetLine" not in text:
        raise SystemExit("OCL_AmericaB52TargetCarpetLine missing")
    return replace_block(
        text,
        r"ObjectCreationList OCL_AmericaB52TargetCarpetLine\s*.*?^End\s*(?=ObjectCreationList|\Z)",
        B52_POINT_OCL,
    )


def patch_commandset(text: str) -> str:
    text = replace_block(
        text,
        r"CommandSet C17GlobalMasterCommandSet\s*.*?^End",
        C17_SHARED_RESTORE,
    )
    text = append_if_missing(text, "CommandSet AmericaC17StarlifterCommandSet", C17_USA_COMMANDSET)
    m = re.search(
        r"CommandSet America_LargeAirBaseCommandSet\s*.*?^End",
        text,
        re.S | re.M,
    )
    if not m:
        raise SystemExit("America_LargeAirBaseCommandSet not found")
    block = m.group(0)
    block2, n = re.subn(
        r"14\s*=\s*Command_ConstructAmericaJetStealthFighter",
        "14 = Command_ConstructAmericaJetAuterF22",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit("LargeAirBase slot 14 not replaced")
    if "Command_ConstructAmericaJetF35C_AA" not in block2:
        raise SystemExit("F35 construct button missing from LargeAirBase")
    return text[: m.start()] + block2 + text[m.end() :]


def patch_commandbutton(text: str) -> str:
    # Point the old F-35C_AA build button at the replacement object.
    old = text
    text, n = re.subn(
        r"(CommandButton Command_ConstructAmericaJetF35C_AA\s*.*?Object\s*=\s*)AmericaJetF35C_AA",
        r"\1AmericaJetF35BJSF",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("F35C_AA construct button Object not retargeted")
    text, n = re.subn(
        r"(CommandButton Command_ConstructAmericaJetF35C_AA\s*.*?TextLabel\s*=\s*)\S+",
        r"\1CONTROLBAR:ConstructAmericaJetF35BJSF",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("F35 construct TextLabel not updated")
    text = append_if_missing(text, "Command_ConstructAmericaJetAuterF22", AUTER_BUTTON)
    text = append_if_missing(text, "Command_AmericaC17ParaDrop", C17_DROP_BUTTON)
    if text == old and "Command_ConstructAmericaJetAuterF22" not in text:
        raise SystemExit("CommandButton patch produced no new buttons")
    return text


def patch_specialpower(text: str) -> str:
    return append_if_missing(text, "SpecialPowerAmericaC17ParaDrop", C17_SPECIALPOWER)


def patch_f22a_ag_buildable(text: str) -> str:
    # Insert after the first Prerequisites closer only. `^End` hits the object
    # closer and leaves file-scope `Buildable = No` (startup crash, no last
    # error). Greedy `[ \t]+(?!End)` backtracks one space on `  End` and lands
    # on a later ArmorSet closer instead of the Prerequisites closer.
    start = re.search(r"(?m)^[ \t]+Prerequisites[ \t]*\r?\n", text)
    if not start:
        raise SystemExit("F22A_AG Prerequisites not found")
    closer = re.search(r"(?m)^[ \t]+End[ \t]*\r?\n", text[start.end() :])
    if not closer:
        raise SystemExit("F22A_AG Prerequisites End not found")
    insert_at = start.end() + closer.end()
    if re.match(r"[ \t]+Buildable", text[insert_at:]):
        return text
    nl = "\r\n" if text[insert_at - 2 : insert_at] == "\r\n" else "\n"
    new = text[:insert_at] + f"  Buildable = No{nl}" + text[insert_at:]
    if re.search(r"^End\s*\r?\n\s*Buildable", new, re.M):
        raise SystemExit("F22A_AG Buildable landed after object End")
    return new


def xor_csf_utf16(s: str) -> bytes:
    raw = s.encode("utf-16-le")
    return bytes(b ^ 0xFF for b in raw)


def append_csf_labels(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    version, nlabels, nstrings = struct.unpack_from("<III", blob, 4)
    extra = bytearray()
    add_labels = 0
    add_strings = 0
    existing = blob.upper()
    for name, value in labels.items():
        key = name.encode("latin1")
        if key.upper() in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xor_csf_utf16(value)
        add_labels += 1
        add_strings += 1
    if add_labels == 0:
        return blob
    out = bytearray(blob)
    struct.pack_into("<I", out, 8, nlabels + add_labels)
    struct.pack_into("<I", out, 12, nstrings + add_strings)
    out += extra
    return bytes(out)


def main() -> int:
    if not SRC_DATA.is_file():
        print("missing source DATA BIG", SRC_DATA, file=sys.stderr)
        return 1
    entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_count = len(entries)
    original_names = [n for n, _ in entries]

    for big_name, src in OBJECT_REPLACEMENTS.items():
        key = norm(big_name)
        if key not in index:
            raise SystemExit(f"missing packed file {big_name}")
        if not src.is_file():
            raise SystemExit(f"missing overlay {src}")
        entries[index[key]] = (entries[index[key]][0], src.read_bytes())
        print("replaced", big_name, "bytes", len(entries[index[key]][1]))

    def mut(path: str, fn):
        key = norm(path)
        i = index[key]
        name, blob = entries[i]
        text = blob.decode("latin1")
        new = fn(text)
        if new == text:
            raise SystemExit(f"no change applied to {path}")
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(text))

    mut(r"Data\INI\Weapon.ini", patch_weapon)
    mut(r"Data\INI\ObjectCreationList.ini", patch_ocl)
    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)
    mut(r"Data\INI\SpecialPower.ini", patch_specialpower)
    mut(
        r"Data\INI\Object\Specter\United States Of America\Airforce\F22A_AG.ini",
        patch_f22a_ag_buildable,
    )

    csf_key = norm(r"Data\English\generals.csf")
    i = index[csf_key]
    name, blob = entries[i]
    new_csf = append_csf_labels(
        blob,
        {
            "OBJECT:AmericaJetF35BJSF": "F-35B JSF",
            "CONTROLBAR:ConstructAmericaJetF35BJSF": "F-35B JSF",
            "OBJECT:AmericaJetAuterF22": "Auter F-22",
            "CONTROLBAR:ConstructAmericaJetAuterF22": "Auter F-22",
            "CONTROLBAR:ToolTipAmericaJetAuterF22": "Build Auter F-22 air-superiority fighter",
        },
    )
    entries[i] = (name, new_csf)
    print("patched CSF", len(new_csf) - len(blob))

    if len(entries) < original_count:
        raise SystemExit("entry count shrank")
    if [n for n, _ in entries][:original_count] != original_names:
        raise SystemExit("original entry order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(entries)
    out_big.write_bytes(packed)
    sha = hashlib.sha256(packed).hexdigest()
    print("wrote", out_big, "size", len(packed), "files", len(entries), "sha", sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
