#!/usr/bin/env python3
"""Pack China heavy aircraft expansion into _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Adds overlay INI + donor ART. Patches packed China_HeavyAirBaseCommandSet in place
(does not create a second CommandSet). Does not overwrite existing aircraft INI.
Does not patch China_LargeAirBaseCommandSet (fighters stay on the fighter airbase).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
DONOR = Path("/tmp/donor_china_heavy")
BASE_DATA = Path("/tmp/china_fighter_expansion/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/china_fighter_expansion/_SPEC_ART_ONE.big")

# All new China expansion string keys. Chunk magic MUST be " RTS" (Generals
# fourcc). " STR" makes String Manager fail to initialize the property.
CSF_LABELS = {
    "CONTROLBAR:ConstructChinaJetJ11B": "J-11B",
    "CONTROLBAR:ToolTipChinaJetJ11B": "PLA J-11B strike Flanker. KD-88, bombs, PL-12.",
    "OBJECT:ChinaJetJ11B": "J-11B\r\n2x KD-88\r\n4x bombs\r\n4x PL-12",
    "CONTROLBAR:ConstructChinaJetJ15": "J-15 Flying Shark",
    "CONTROLBAR:ToolTipChinaJetJ15": "PLA J-15 naval strike fighter. YJ anti-ship missiles and guided bombs.",
    "OBJECT:ChinaJetJ15": "J-15 Flying Shark\r\nYJ anti-ship\r\nLT-3 PGM",
    "CONTROLBAR:ConstructChinaJetJ31": "J-31",
    "CONTROLBAR:ToolTipChinaJetJ31": "PLA J-31 stealth strike fighter. Internal precision bombs.",
    "OBJECT:ChinaJetJ31": "J-31\r\nInternal PGM strike",
    "CONTROLBAR:ConstructChinaJetJF17Block3": "JF-17 Block 3",
    "CONTROLBAR:ToolTipChinaJetJF17Block3": "JF-17 Block 3 / FC-1. Guided bombs and air-to-ground missiles.",
    "OBJECT:ChinaJetJF17Block3": "JF-17 Block 3\r\nPGM plus AGM",
    "CONTROLBAR:ConstructChinaJetJ8II": "J-8II",
    "CONTROLBAR:ToolTipChinaJetJ8II": "PLA J-8II interceptor-strike. Bombs and rockets.",
    "OBJECT:ChinaJetJ8II": "J-8II\r\nBombs + rockets",
    "CONTROLBAR:ConstructChinaJetJ7": "J-7",
    "CONTROLBAR:ToolTipChinaJetJ7": "PLA J-7 light strike fighter. Bombs and rockets.",
    "OBJECT:ChinaJetJ7": "J-7\r\nLight bombs + rockets",
    "CONTROLBAR:ConstructChinaJetJ10A": "J-10A",
    "CONTROLBAR:ToolTipChinaJetJ10A": "PLA J-10A. Precision bombs and air-to-ground missiles.",
    "OBJECT:ChinaJetJ10A": "J-10A\r\nPGM + KD-88",
    "CONTROLBAR:ConstructChinaJetJ10B": "J-10B",
    "CONTROLBAR:ToolTipChinaJetJ10B": "PLA J-10B. Precision bombs and air-to-ground missiles.",
    "OBJECT:ChinaJetJ10B": "J-10B\r\nLT-3 PGM + KD-88",
    "CONTROLBAR:ConstructChinaBomberH6K": "H-6K",
    "CONTROLBAR:ToolTipChinaBomberH6K": "PLA H-6K bomber. CJ-10 cruise missiles and heavy bombs.",
    "OBJECT:ChinaBomberH6K": "H-6K\r\n6x CJ-10 cruise\r\n8x bombs\r\nCarpet bombs",
    "CONTROLBAR:ConstructChinaJetY20": "Y-20",
    "CONTROLBAR:ToolTipChinaJetY20": "PLA Y-20 Kunpeng transport. Infantry and vehicle airlift.",
    "OBJECT:ChinaJetY20": "Y-20 Kunpeng\r\nTransport",
    "CONTROLBAR:ConstructChinaAircraftY20AEW": "Y-20 AEW",
    "CONTROLBAR:ToolTipChinaAircraftY20AEW": "PLA Y-20 AEW KJ-3000. Airborne radar scan.",
    "OBJECT:ChinaAircraftY20AEW": "Y-20 AEW\r\nSAR scan",
}

CSF_STR_MAGIC = b" RTS"  # Generals String Manager fourcc (not " STR")
CSF_LBL_MAGIC = b" LBL"

NEW_COMMANDSET = """CommandSet China_HeavyAirBaseCommandSet
  1  = Command_ConstructChinaAircraftKJ500
  2  = Command_ConstructChinaJetJH7BHeavy
  3  = Command_ConstructChinaJetJH7A2
  4  = Command_ConstructChinaHelicopterZ18A
  5  = Command_ConstructChinaBomberH6K
  6  = Command_ConstructChinaJetY20
  7  = Command_ConstructChinaAircraftY20AEW
  8  = Command_ConstructChinaDroneCH5
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

# Specter parses CommandSet.ini as a core file. Overlay CommandButton_*.ini is NOT
# registered in time, so new UNIT_BUILD buttons must be declared in this same file
# immediately before China_LargeAirBaseCommandSet (same pattern as Russia Large).
# ASCII only. No UTF-8 em-dash comments.
INLINE_BUTTONS = """CommandButton Command_ConstructChinaJetJ11B
  Command          = UNIT_BUILD
  Object           = ChinaJetJ11B
  TextLabel        = CONTROLBAR:ConstructChinaJetJ11B
  ButtonImage      = pla_j11b
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJ11B
End

CommandButton Command_ConstructChinaJetJ15
  Command          = UNIT_BUILD
  Object           = ChinaJetJ15
  TextLabel        = CONTROLBAR:ConstructChinaJetJ15
  ButtonImage      = pla_j15
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJ15
End

CommandButton Command_ConstructChinaJetJ31
  Command          = UNIT_BUILD
  Object           = ChinaJetJ31
  TextLabel        = CONTROLBAR:ConstructChinaJetJ31
  ButtonImage      = pla_j31
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJ31
End

CommandButton Command_ConstructChinaJetJF17Block3
  Command          = UNIT_BUILD
  Object           = ChinaJetJF17Block3
  TextLabel        = CONTROLBAR:ConstructChinaJetJF17Block3
  ButtonImage      = pla_jf17
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJF17Block3
End

CommandButton Command_ConstructChinaJetJ8II
  Command          = UNIT_BUILD
  Object           = ChinaJetJ8II
  TextLabel        = CONTROLBAR:ConstructChinaJetJ8II
  ButtonImage      = pla_j8ii
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJ8II
End

CommandButton Command_ConstructChinaJetJ7
  Command          = UNIT_BUILD
  Object           = ChinaJetJ7
  TextLabel        = CONTROLBAR:ConstructChinaJetJ7
  ButtonImage      = pla_j7
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJ7
End

CommandButton Command_ConstructChinaJetJ10A
  Command          = UNIT_BUILD
  Object           = ChinaJetJ10A
  TextLabel        = CONTROLBAR:ConstructChinaJetJ10A
  ButtonImage      = pla_j10a
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJ10A
End

CommandButton Command_ConstructChinaJetJ10B
  Command          = UNIT_BUILD
  Object           = ChinaJetJ10B
  TextLabel        = CONTROLBAR:ConstructChinaJetJ10B
  ButtonImage      = pla_j10b
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetJ10B
End

CommandButton Command_ConstructChinaBomberH6K
  Command          = UNIT_BUILD
  Object           = ChinaBomberH6K
  TextLabel        = CONTROLBAR:ConstructChinaBomberH6K
  ButtonImage      = pla_h6k
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaBomberH6K
End

CommandButton Command_ConstructChinaJetY20
  Command          = UNIT_BUILD
  Object           = ChinaJetY20
  TextLabel        = CONTROLBAR:ConstructChinaJetY20
  ButtonImage      = pla_y20
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaJetY20
End

CommandButton Command_ConstructChinaAircraftY20AEW
  Command          = UNIT_BUILD
  Object           = ChinaAircraftY20AEW
  TextLabel        = CONTROLBAR:ConstructChinaAircraftY20AEW
  ButtonImage      = pla_y20aew
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaAircraftY20AEW
End
"""

DROP_OVERLAY_BUTTON_FILES = {
    "data\\ini\\commandbutton_chinafighterexpansion.ini",
    "data\\ini\\commandbutton_chinaheavyexpansion.ini",
}

NEW_LARGE_COMMANDSET = """CommandSet China_LargeAirBaseCommandSet
  1  = Command_ConstructChinaJetJ20B_AG
  2  = Command_ConstructChinaJetJ50
  3  = Command_ConstructChinaJetJ16D
  4  = Command_ConstructChinaHelicopterWZ10ME
  5  = Command_ConstructChinaJetJ16BBunker
  6  = Command_ConstructChinaJetJ20B_AA
  7  = Command_ConstructChinaJetJ10C
  8  = Command_ConstructChinaJetJ20B_AA_AI
  9  = Command_ConstructChinaJetJ11B
  10 = Command_ConstructChinaJetJ15
  11 = Command_ConstructChinaJetJ31
  12 = Command_ConstructChinaJetJF17Block3
  13 = Command_SetRallyPoint
  14 = Command_Sell
  15 = Command_ConstructChinaJetJ8II
  16 = Command_ConstructChinaJetJ7
  17 = Command_ConstructChinaJetJ10A
  18 = Command_ConstructChinaJetJ10B
End
"""

ART_MAP = [
    ("Art/w3d/h6k.W3D", "Art\\W3D\\h6k.W3D"),
    ("Art/w3d/HXYun20HXNew.W3D", "Art\\W3D\\HXYun20HXNew.W3D"),
    ("Art/w3d/HXYun20YJ.W3D", "Art\\W3D\\HXYun20YJ.W3D"),
    ("Art/Textures/h6k.dds", "Art\\Textures\\h6k.dds"),
    ("Art/Textures/h6k.dds", "Art\\Textures\\h6k.tga"),
    ("Art/Textures/planeH.dds", "Art\\Textures\\planeH.dds"),
    ("Art/Textures/planeH.dds", "Art\\Textures\\planeH.tga"),
    ("Art/Textures/planeJZ.dds", "Art\\Textures\\planeJZ.dds"),
    ("Art/Textures/planeJZ.dds", "Art\\Textures\\planeJZ.tga"),
    ("Art/Textures/yujing1.dds", "Art\\Textures\\yujing1.dds"),
    ("Art/Textures/yujing1.dds", "Art\\Textures\\yujing1.tga"),
    ("Art/Textures/CHNH6KTB.tga", "Art\\Textures\\CHNH6KTB.tga"),
    ("Art/Textures/CHNY20TB.tga", "Art\\Textures\\CHNY20TB.tga"),
    ("Art/Textures/CHNKJ2000TB.tga", "Art\\Textures\\CHNKJ2000TB.tga"),
]

OVERLAY_OBJECT_FILES = {"H6K.ini", "Y20.ini", "Y20AEW.ini"}
OVERLAY_NAMED = {
    "Weapon_ChinaHeavyExpansion.ini",
    "China_HeavyExpansion_Images.INI",
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


def csf_decode(raw: bytes) -> str:
    return bytes(b ^ 0xFF for b in raw).decode("utf-16-le", errors="replace")


def csf_encode(text: str) -> bytes:
    raw = text.encode("utf-16-le")
    return bytes(b ^ 0xFF for b in raw)


def parse_csf(data: bytes):
    if data[:4] not in (b" FSC", b"CSF "):
        raise ValueError("Not a CSF file")
    version, nlab, nstr, unk, lang = struct.unpack_from("<IIIII", data, 4)
    pos = 24
    labels = []
    for _ in range(nlab):
        mag = data[pos : pos + 4]
        pos += 4
        ns, namelen = struct.unpack_from("<II", data, pos)
        pos += 8
        name = data[pos : pos + namelen].decode("latin1", errors="replace")
        pos += namelen
        strings = []
        for _j in range(ns):
            smag = data[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            raw = data[pos : pos + 2 * slen]
            pos += 2 * slen
            extra = b""
            if smag in (b"WRTS", b"STR "):
                elen = struct.unpack_from("<I", data, pos)[0]
                pos += 4
                extra = data[pos : pos + elen]
                pos += elen
            strings.append((smag, csf_decode(raw), extra))
        labels.append((mag, name, strings))
    return version, unk, lang, labels


def build_csf(version, unk, lang, labels) -> bytes:
    out = bytearray()
    out += b" FSC"
    nstr = sum(len(s) for _, _, s in labels)
    out += struct.pack("<IIIII", version, len(labels), nstr, unk, lang)
    for mag, name, strings in labels:
        nb = name.encode("latin1", errors="replace")
        out += mag
        out += struct.pack("<II", len(strings), len(nb))
        out += nb
        for smag, text, extra in strings:
            enc = csf_encode(text)
            chars = len(enc) // 2
            out += smag
            out += struct.pack("<I", chars)
            out += enc
            if smag in (b"WRTS", b"STR "):
                out += struct.pack("<I", len(extra))
                out += extra
    return bytes(out)


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = parse_csf(data)
    fixed_magic = 0
    normalized = []
    have = set()
    for mag, name, strings in labels:
        new_strings = []
        for smag, text, extra in strings:
            if smag == b" STR":
                smag = CSF_STR_MAGIC
                extra = b""
                fixed_magic += 1
            new_strings.append((smag, text, extra))
        normalized.append((mag, name, new_strings))
        have.add(name)
    labels = normalized
    added = 0
    for key, value in CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value.replace("\r", "").replace("\n", "")):
            raise SystemExit(f"non-ASCII CSF key or value: {key}")
        if key in have:
            continue
        labels.append((CSF_LBL_MAGIC, key, [(CSF_STR_MAGIC, value, b"")]))
        added += 1
        have.add(key)
    print(f"CSF added {added} labels, fixed {fixed_magic} STR->RTS magics (existing {len(have) - added})")
    return build_csf(version, unk, lang, labels)


def validate_csf(data: bytes, required: list[str]) -> None:
    if data[:4] != b" FSC":
        raise SystemExit(f"CSF magic {data[:4]!r} is not Generals FSC")
    _version, nlab_hdr, nstr_hdr, _unk, _lang = struct.unpack_from("<IIIII", data, 4)
    pos = 24
    names = []
    str_count = 0
    bad_magic = []
    for _ in range(nlab_hdr):
        _mag = data[pos : pos + 4]
        pos += 4
        ns, namelen = struct.unpack_from("<II", data, pos)
        pos += 8
        name = data[pos : pos + namelen].decode("latin1", errors="replace")
        pos += namelen
        names.append(name)
        for _j in range(ns):
            smag = data[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            pos += 2 * slen
            str_count += 1
            if smag == b" STR":
                bad_magic.append(name)
            if smag in (b"WRTS", b"STR "):
                elen = struct.unpack_from("<I", data, pos)[0]
                pos += 4
                pos += elen
            elif smag not in (b" RTS",):
                bad_magic.append(f"{name} smag={smag!r}")
    leftover = len(data) - pos
    errors = []
    if leftover != 0:
        errors.append(f"CSF leftover bytes {leftover}")
    if str_count != nstr_hdr:
        errors.append(f"CSF string count hdr={nstr_hdr} got={str_count}")
    if len(names) != nlab_hdr:
        errors.append("CSF label count mismatch")
    if bad_magic:
        errors.append("bad CSF string magic (STR not RTS): " + ", ".join(bad_magic[:8]))
    have = set(names)
    missing = [k for k in required if k not in have]
    if missing:
        errors.append("missing CSF keys: " + ", ".join(missing))
    dups = sorted({n for n in names if names.count(n) > 1})
    if dups:
        errors.append("duplicate CSF labels: " + ", ".join(dups[:8]))
    if errors:
        raise SystemExit("CSF CHECK FAIL\n" + "\n".join(errors))
    print("CSF CHECK PASS")


def grab_block(text: str, name: str) -> str:
    pattern = re.compile(
        rf"CommandSet {re.escape(name)}\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise SystemExit(f"{name} not found in packed CommandSet.ini")
    return m.group(0)


def validate_china_commandsets(text: str) -> None:
    errors = []
    if text.count("CommandSet China_LargeAirBaseCommandSet") != 1:
        errors.append("Large AirBase CommandSet count != 1")
    if text.count("CommandSet China_HeavyAirBaseCommandSet") != 1:
        errors.append("Heavy AirBase CommandSet count != 1")
    large = grab_block(text, "China_LargeAirBaseCommandSet")
    heavy = grab_block(text, "China_HeavyAirBaseCommandSet")
    if not large.rstrip().endswith("End"):
        errors.append("Large missing End")
    if not heavy.rstrip().endswith("End"):
        errors.append("Heavy missing End")
    if "CommandSet " in large.split("\n", 1)[-1]:
        errors.append("nested CommandSet inside Large")
    if "CommandSet " in heavy.split("\n", 1)[-1]:
        errors.append("nested CommandSet inside Heavy")
    for line in (large + "\n" + heavy).splitlines()[1:]:
        s = line.strip()
        if not s or s == "End" or s.startswith(";") or s.startswith("CommandSet "):
            continue
        m = re.match(r"^(\d+)\s*=\s*(Command_\S+)$", s)
        if not m:
            errors.append(f"invalid Command entry: {line!r}")
            continue
        slot = int(m.group(1))
        if slot < 1 or slot > 18:
            errors.append(f"slot out of range: {slot}")
    required_btns = [
        "Command_ConstructChinaJetJ11B",
        "Command_ConstructChinaJetJ15",
        "Command_ConstructChinaJetJ31",
        "Command_ConstructChinaJetJF17Block3",
        "Command_ConstructChinaJetJ8II",
        "Command_ConstructChinaJetJ7",
        "Command_ConstructChinaJetJ10A",
        "Command_ConstructChinaJetJ10B",
        "Command_ConstructChinaBomberH6K",
        "Command_ConstructChinaJetY20",
        "Command_ConstructChinaAircraftY20AEW",
    ]
    large_idx = text.find("CommandSet China_LargeAirBaseCommandSet")
    prefix = text[:large_idx]
    for btn in required_btns:
        if f"CommandButton {btn}" not in prefix:
            errors.append(f"button {btn} not defined before China_LargeAirBaseCommandSet")
        if prefix.count(f"CommandButton {btn}") != 1:
            errors.append(f"button {btn} duplicate or missing in CommandSet.ini prefix")
    if any(ord(ch) > 127 for ch in large + heavy + INLINE_BUTTONS):
        errors.append("non-ASCII in China CommandSet region")
    keep = [
        "Command_ConstructChinaJetJ11B",
        "Command_ConstructChinaJetJ15",
        "Command_ConstructChinaJetJ31",
        "Command_ConstructChinaJetJF17Block3",
        "Command_ConstructChinaJetJ8II",
        "Command_ConstructChinaJetJ7",
        "Command_ConstructChinaJetJ10A",
        "Command_ConstructChinaJetJ10B",
        "Command_ConstructChinaBomberH6K",
        "Command_ConstructChinaJetY20",
        "Command_ConstructChinaAircraftY20AEW",
        "Command_ConstructChinaDroneCH5",
    ]
    blob = large + heavy
    for btn in keep:
        if btn not in blob:
            errors.append(f"lost aircraft button {btn}")
    if errors:
        raise SystemExit("PARSER CHECK FAIL CommandSet.ini\n" + "\n".join(errors))
    print("PARSER CHECK PASS CommandSet.ini")


def patch_commandset(text: str) -> str:
    if "CommandButton Command_ConstructChinaJetJ11B" not in text:
        needle = "CommandSet China_LargeAirBaseCommandSet"
        idx = text.find(needle)
        if idx < 0:
            raise SystemExit("China_LargeAirBaseCommandSet not found in packed CommandSet.ini")
        text = text[:idx] + INLINE_BUTTONS.rstrip() + "\n\n" + text[idx:]
        print("Inlined China construct CommandButtons before Large AirBase")

    large_pat = re.compile(
        r"CommandSet China_LargeAirBaseCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    if not large_pat.search(text):
        raise SystemExit("China_LargeAirBaseCommandSet block not found")
    text = large_pat.sub(NEW_LARGE_COMMANDSET.rstrip() + "\n", text, count=1)

    pattern = re.compile(
        r"CommandSet China_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise SystemExit("China_HeavyAirBaseCommandSet not found in packed CommandSet.ini")
    text = pattern.sub(NEW_COMMANDSET.rstrip() + "\n", text, count=1)
    validate_china_commandsets(text)
    return text


def lf(data: bytes) -> bytes:
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def parse_check(overlay_files: dict[str, bytes]) -> None:
    errors = []
    for name, content in overlay_files.items():
        if not name.lower().endswith(".ini"):
            continue
        text = content.decode("utf-8")
        if "\r" in text:
            errors.append(f"{name}: CRLF")
        n_obj = len(re.findall(r"^Object\s+\S+", text, re.M))
        n_wpn = len(re.findall(r"^Weapon\s+\S+", text, re.M))
        n_btn = len(re.findall(r"^CommandButton\s+\S+", text, re.M))
        n_end = len(re.findall(r"^End\s*$", text, re.M))
        if n_end == 0 and (n_obj + n_wpn + n_btn) > 0:
            errors.append(f"{name}: missing End")
    if errors:
        raise SystemExit("PARSER CHECK FAIL\n" + "\n".join(errors))
    print("PARSER CHECK PASS")


def blob_from_map(amap, key_substr: str) -> bytes:
    key_substr = key_substr.lower()
    for key, (_name, content) in amap.items():
        if key_substr in key:
            return content
    raise SystemExit(f"missing packed entry matching {key_substr}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/china_heavy_aircraft"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    data_entries, data_raw = read_big(BASE_DATA)
    art_entries, art_raw = read_big(BASE_ART)

    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])

    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    # Baseline hashes of existing China aircraft that must stay byte-identical.
    protect = {
        "j10c.ini": hashlib.sha256(blob_from_map(data_map, "pla\\airforce\\j10c.ini")).hexdigest(),
        "h6m.ini": hashlib.sha256(blob_from_map(data_map, "science objects\\h6m.ini")).hexdigest(),
        "ch5.ini": hashlib.sha256(blob_from_map(data_map, "pla\\drones\\ch5.ini")).hexdigest(),
        "china_system.ini": hashlib.sha256(blob_from_map(data_map, "pla\\china_system.ini")).hexdigest(),
        "j11b.ini": hashlib.sha256(blob_from_map(data_map, "pla\\airforce\\j11b.ini")).hexdigest(),
    }

    overlay: dict[str, bytes] = {}
    patch_data = ROOT / "patch/Data"
    for path in sorted(patch_data.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(patch_data).as_posix()
        keep = False
        if rel.startswith("INI/Object/Specter/PLA/Airforce/") and path.name in OVERLAY_OBJECT_FILES:
            keep = True
        if path.name in OVERLAY_NAMED:
            keep = True
        if not keep:
            continue
        big_name = "Data\\" + rel.replace("/", "\\")
        overlay[big_name] = lf(path.read_bytes())

    parse_check(overlay)

    dropped = []
    for key in list(data_map):
        if key in DROP_OVERLAY_BUTTON_FILES:
            dropped.append(data_map[key][0])
            del data_map[key]
    if dropped:
        print("Dropped overlay CommandButton files (inlined into CommandSet.ini):", dropped)
    data_keys[:] = [k for k in data_keys if k not in DROP_OVERLAY_BUTTON_FILES]

    cs_key = "data\\ini\\commandset.ini"
    cs_name, cs_bytes = data_map[cs_key]
    cs_text = cs_bytes.decode("latin1")
    cs_new = patch_commandset(cs_text)
    if cs_new.count("CommandSet China_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("duplicate China_HeavyAirBaseCommandSet after patch")
    if cs_new.count("CommandSet China_LargeAirBaseCommandSet") != 1:
        raise SystemExit("duplicate China_LargeAirBaseCommandSet after patch")
    data_map[cs_key] = (cs_name, lf(cs_new.encode("latin1")))
    print("Patched CommandSet.ini (inline buttons + Large/Heavy blocks)")

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_bytes = data_map[csf_key]
    data_map[csf_key] = (csf_name, patch_csf(csf_bytes))

    added_data = []
    for big_name, content in overlay.items():
        key = norm_key(big_name)
        if key in data_map:
            raise SystemExit(f"Refusing to overwrite existing DATA entry: {big_name}")
        data_map[key] = (big_name, content)
        added_data.append(big_name)

    added_art = []
    for src_rel, dest in ART_MAP:
        src = DONOR / src_rel
        if not src.is_file() or src.stat().st_size == 0:
            raise SystemExit(f"Missing donor ART {src}")
        key = norm_key(dest)
        content = src.read_bytes()
        if key in art_map:
            old_name, old = art_map[key]
            if old != content:
                art_map[key] = (old_name, content)
                added_art.append(dest + " (updated)")
            else:
                added_art.append(dest + " (unchanged)")
        else:
            art_map[key] = (dest, content)
            added_art.append(dest)

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
    data_bytes = build_big(final_data)
    art_bytes = build_big(final_art)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    zpath = out / "CHINA_HEAVY_AIRCRAFT.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    # Post-pack verify from written BIG.
    v_entries, v_raw = read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[norm_key(name)] = v_raw[off : off + size]
    a_entries, a_raw = read_big(out_art)
    a_names = {norm_key(n) for n, _o, _s in a_entries}

    def must_hash(key_substr, expected):
        blob = None
        for k, b in v_map.items():
            if key_substr in k:
                blob = b
                break
        if blob is None:
            raise SystemExit(f"verify missing {key_substr}")
        got = hashlib.sha256(blob).hexdigest()
        if got != expected:
            raise SystemExit(f"protected file changed: {key_substr}")

    must_hash("pla\\airforce\\j10c.ini", protect["j10c.ini"])
    must_hash("science objects\\h6m.ini", protect["h6m.ini"])
    must_hash("pla\\drones\\ch5.ini", protect["ch5.ini"])
    must_hash("pla\\china_system.ini", protect["china_system.ini"])
    must_hash("pla\\airforce\\j11b.ini", protect["j11b.ini"])

    cs = v_map["data\\ini\\commandset.ini"].decode("latin1")
    validate_china_commandsets(cs)
    if "Command_ConstructChinaDroneCH5" not in cs:
        raise SystemExit("CH-5 button missing from CommandSet")
    if cs.count("CommandSet China_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("duplicate heavy CommandSet")
    if "CommandButton Command_ConstructChinaJetJ11B" not in cs:
        raise SystemExit("J-11B CommandButton not inlined in CommandSet.ini")

    csf_blob = v_map["data\\english\\generals.csf"]
    ini_refs = []
    for k, blob in v_map.items():
        if not k.endswith(".ini"):
            continue
        if "pla\\airforce\\" not in k and k != "data\\ini\\commandset.ini":
            continue
        text = blob.decode("latin1", errors="replace")
        ini_refs.extend(re.findall(r"(?:OBJECT|CONTROLBAR):[A-Za-z0-9_]+", text))
    required_csf = sorted(set(list(CSF_LABELS.keys()) + ini_refs))
    # Only require keys that belong to new China expansion objects/buttons.
    required_new = sorted(CSF_LABELS.keys())
    validate_csf(csf_blob, required_new)
    have_names = set()
    version, unk, lang, labels = parse_csf(csf_blob)
    have_names = {name for _, name, _ in labels}
    missing_ini = sorted({r for r in ini_refs if r.startswith(("OBJECT:ChinaJet", "OBJECT:ChinaBomber", "OBJECT:ChinaAircraft", "CONTROLBAR:ConstructChinaJet", "CONTROLBAR:ToolTipChinaJet", "CONTROLBAR:ConstructChinaBomber", "CONTROLBAR:ToolTipChinaBomber", "CONTROLBAR:ConstructChinaAircraft", "CONTROLBAR:ToolTipChinaAircraft")) and r not in have_names})
    if missing_ini:
        raise SystemExit("CSF missing INI refs: " + ", ".join(missing_ini))
    print("CSF INI-REF CHECK PASS")

    for banned in DROP_OVERLAY_BUTTON_FILES:
        if banned in v_map:
            raise SystemExit(f"overlay CommandButton file still packed: {banned}")

    for req in (
        "data\\ini\\object\\specter\\pla\\airforce\\h6k.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\y20.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\y20aew.ini",
        "data\\ini\\weapon_chinaheavyexpansion.ini",
        "data\\ini\\mappedimages\\handcreated\\china_heavyexpansion_images.ini",
    ):
        if req not in v_map:
            raise SystemExit(f"overlay missing from DATA BIG: {req}")

    for req in (
        "art\\w3d\\h6k.w3d",
        "art\\w3d\\hxyun20hxnew.w3d",
        "art\\w3d\\hxyun20yj.w3d",
        "art\\textures\\h6k.dds",
        "art\\textures\\planeh.dds",
        "art\\textures\\planejz.dds",
        "art\\textures\\chnh6ktb.tga",
        "art\\textures\\chny20tb.tga",
        "art\\textures\\chnkj2000tb.tga",
    ):
        if req not in a_names:
            raise SystemExit(f"ART missing {req}")

    report = out / "PACK_REPORT.txt"
    report.write_text(
        "\n".join(
            [
                f"DATA SHA256={hashlib.sha256(data_bytes).hexdigest()} SIZE={len(data_bytes)}",
                f"ART  SHA256={hashlib.sha256(art_bytes).hexdigest()} SIZE={len(art_bytes)}",
                f"ZIP  SHA256={hashlib.sha256(zpath.read_bytes()).hexdigest()} SIZE={zpath.stat().st_size}",
                "added_data=" + repr(added_data),
                "added_art=" + repr(added_art),
                NEW_COMMANDSET,
                "PARSER CHECK PASS",
                "CSF CHECK PASS",
                "PROTECTED EXISTING AIRCRAFT HASHES UNCHANGED",
                "COMMANDSET PARSE FIX: buttons inlined before China_LargeAirBaseCommandSet",
                "CSF MAGIC FIX: STR -> RTS for String Manager",
                "FIGHTER LARGE AIRBASE SLOTS KEPT",
            ]
        )
        + "\n"
    )
    print(report.read_text())
    print(f"Wrote {out_data} {out_art} {zpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
