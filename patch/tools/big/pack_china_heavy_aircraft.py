#!/usr/bin/env python3
"""Pack China air force expansion into _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Adds overlay INI + donor ART. Patches packed CommandSets in place.
Inlines expansion weapons into core Weapon.ini.
Removes China aircraft science/rank prereqs.
Does not overwrite packed ChinaJetJ10C or ChinaBomberH6M.
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
BASE_DATA = Path("/tmp/china_h20/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/china_h20/_SPEC_ART_ONE.big")
# This cleanup pass is DATA-only. ART (NVH20 / H-20.dds) stays from china_h20.
REBUILD_ART = False

# All new China expansion string keys. Chunk magic MUST be " RTS" (Generals
# fourcc). " STR" makes String Manager fail to initialize the property.
CSF_LABELS = {
    "CONTROLBAR:ConstructChinaJetJ11B": "J-11B",
    "CONTROLBAR:ToolTipChinaJetJ11B": "PLA J-11B strike Flanker. KD-88 and bombs.",
    "OBJECT:ChinaJetJ11B": "J-11B\r\n2x KD-88\r\n6x bombs",
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
    "CONTROLBAR:ToolTipChinaBomberH6K": "PLA H-6K strategic bomber. Drops a large carpet-bomb payload in one run.",
    "OBJECT:ChinaBomberH6K": "H-6K\r\nStrategic bomber\r\nCarpet bomb run",
    "CONTROLBAR:ConstructChinaJetY20": "Y-20",
    "CONTROLBAR:ToolTipChinaJetY20": "PLA Y-20 Kunpeng transport. Infantry and vehicle airlift.",
    "OBJECT:ChinaJetY20": "Y-20 Kunpeng\r\nTransport",
    "CONTROLBAR:ConstructChinaAircraftY20AEW": "Y-20 AEW",
    "CONTROLBAR:ToolTipChinaAircraftY20AEW": "PLA Y-20 AEW KJ-3000. Long-range airborne radar and larger SAR scan.",
    "OBJECT:ChinaAircraftY20AEW": "Y-20 AEW\r\nLong-range radar",
    "CONTROLBAR:ConstructChinaBomberH20": "H-20",
    "CONTROLBAR:ToolTipChinaBomberH20": "PLA H-20 stealth bomber. Stand-off cruise missiles and heavy bombs.",
    "OBJECT:ChinaBomberH20": "H-20\r\nStealth flying wing\r\n6x cruise\r\n8x bombs",
    "CONTROLBAR:ConstructChinaBomberH20A": "H-20A",
    "CONTROLBAR:ToolTipChinaBomberH20A": "PLA H-20A stealth bomber. Single heavy 10-ton bomb.",
    "OBJECT:ChinaBomberH20A": "H-20A\r\nStealth flying wing\r\n1x 10-ton bomb",
    "CONTROLBAR:ConstructChinaAirfield": "Fighter Airbase",
    "CONTROLBAR:ToolTipChinaBuildAirField": "Builds the PLA fighter airbase. Produces fighters after the airbase exists.",
    "CONTROLBAR:ConstructChina_HeavyAirBase": "Heavy Airbase",
    "CONTROLBAR:ToolTipChina_HeavyAirBase": "Builds the PLA heavy airbase. Produces bombers and transports.",
    "OBJECT:China_LargeAirBase": "Fighter Airbase",
    "OBJECT:China_HeavyAirBase": "Heavy Airbase",
}

CSF_STR_MAGIC = b" RTS"  # Generals String Manager fourcc (not " STR")
CSF_LBL_MAGIC = b" LBL"

NEW_COMMANDSET = """CommandSet China_HeavyAirBaseCommandSet
  1  = Command_ConstructChinaJetJH7A2
  2  = Command_ConstructChinaHelicopterZ18A
  3  = Command_ConstructChinaBomberH6K
  4  = Command_ConstructChinaJetY20
  5  = Command_ConstructChinaAircraftY20AEW
  6  = Command_ConstructChinaDroneCH5
  7  = Command_ConstructChinaBomberH20
  8  = Command_ConstructChinaBomberH20A
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

CommandButton Command_ConstructChinaBomberH20
  Command          = UNIT_BUILD
  Object           = ChinaBomberH20
  TextLabel        = CONTROLBAR:ConstructChinaBomberH20
  ButtonImage      = pla_h20
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaBomberH20
End

CommandButton Command_ConstructChinaBomberH20A
  Command          = UNIT_BUILD
  Object           = ChinaBomberH20A
  TextLabel        = CONTROLBAR:ConstructChinaBomberH20A
  ButtonImage      = pla_h20
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipChinaBomberH20A
End
"""

DROP_OVERLAY_BUTTON_FILES = {
    "data\\ini\\commandbutton_chinafighterexpansion.ini",
    "data\\ini\\commandbutton_chinaheavyexpansion.ini",
}

NEW_LARGE_COMMANDSET = """CommandSet China_LargeAirBaseCommandSet
  1  = Command_ConstructChinaJetJ20B_AG
  2  = Command_ConstructChinaJetJ16D
  3  = Command_ConstructChinaHelicopterWZ10ME
  4  = Command_ConstructChinaJetJ20B_AA
  5  = Command_ConstructChinaJetJ10C
  6  = Command_ConstructChinaJetJ11B
  7  = Command_ConstructChinaJetJ15
  8  = Command_ConstructChinaJetJ31
  9  = Command_ConstructChinaJetJF17Block3
  10 = Command_ConstructChinaJetJ8II
  11 = Command_ConstructChinaJetJ7
  12 = Command_ConstructChinaJetJ10A
  13 = Command_SetRallyPoint
  14 = Command_Sell
  15 = Command_ConstructChinaJetJ10B
End
"""

NEW_PLA_AIRFIELD_COMMANDSET = """CommandSet PLAAirfieldCommandSet
  1  = Command_ConstructChinaJetJ20B_AG
  2  = Command_ConstructChinaJetJ16D
  3  = Command_ConstructChinaHelicopterWZ10ME
  4  = Command_ConstructChinaJetJ20B_AA
  5  = Command_ConstructChinaJetJ10C
  6  = Command_ConstructChinaJetJ11B
  7  = Command_ConstructChinaJetJ15
  8  = Command_ConstructChinaJetJ31
  9  = Command_ConstructChinaJetJF17Block3
  10 = Command_ConstructChinaJetJ8II
  11 = Command_ConstructChinaJetJ7
  12 = Command_ConstructChinaJetJ10A
  13 = Command_SetRallyPoint
  14 = Command_Sell
  15 = Command_ConstructChinaJetJ10B
End
"""

REMOVED_CONSTRUCT_BUTTONS = [
    "Command_ConstructChinaAircraftKJ500",
    "Command_ConstructChinaJetJH7BHeavy",
    "Command_ConstructChinaJetJ50",
    "Command_ConstructChinaJetJ16BBunker",
    "Command_ConstructChinaJetJ20B_AA_AI",
]
REMOVE_CHINA_OBJECTS = {
    "ChinaAircraftKJ500",
    "ChinaJetJH7B_HeavyBunker",
    "ChinaJetJ50",
    "ChinaJetJ16B_Bunker",
}
NEW_Y20AEW_OCL = """ObjectCreationList OCL_ChinaY20AEWTargetedSARScan
  CreateObject
    ObjectNames = ChinaY20AEWSARRevealPing
    Count = 1
  End
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
    ("Art/w3d/NVH20.W3D", "Art\\W3D\\NVH20.W3D"),
    ("Art/Textures/H-20.dds", "Art\\Textures\\H-20.dds"),
    ("Art/Textures/H-20.dds", "Art\\Textures\\H-20.tga"),
]

OVERLAY_OBJECT_FILES = {
    "H6K.ini",
    "Y20.ini",
    "Y20AEW.ini",
    "J11B.ini",
    "J15.ini",
    "J31.ini",
    "JF17.ini",
    "H20.ini",
    "H20A.ini",
}
OVERLAY_NAMED = {
    "China_HeavyExpansion_Images.INI",
}
OVERLAY_BUILDING_FILES = {
    "China_LargeAirBase.ini",
    "China_HeavyAirBase.ini",
}
# Weapons are inlined into packed Weapon.ini (core parse). Do not pack overlay
# Weapon_*.ini or they can duplicate if both load.
WEAPON_OVERLAY_FILES = [
    "Weapon_ChinaFighterExpansion.ini",
    "Weapon_ChinaHeavyExpansion.ini",
]
DROP_OVERLAY_WEAPON_FILES = {
    "data\\ini\\weapon_chinafighterexpansion.ini",
    "data\\ini\\weapon_chinaheavyexpansion.ini",
}
ALLOW_OVERWRITE = {
    "data\\ini\\object\\specter\\pla\\airforce\\h6k.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\y20.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\y20aew.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\j11b.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\j15.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\j31.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\jf17.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\h20.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\h20a.ini",
    "data\\ini\\object\\specter\\pla\\buildings\\china_largeairbase.ini",
    "data\\ini\\object\\specter\\pla\\buildings\\china_heavyairbase.ini",
    "data\\ini\\mappedimages\\handcreated\\china_heavyexpansion_images.ini",
}

CHINA_AIRCRAFT_UNLOCK_OBJECTS = {
    "ChinaJetJ16D",
    "ChinaJetJ20B_AG",
    "ChinaJetJ20B_AA",
    "ChinaJetJH7A2",
    "ChinaDroneCH5",
    "ChinaDroneAsn301",
    "ChinaDroneCH7",
    "ChinaDroneJXDS",
    "ChinaDroneWZ8",
    "ChinaDroneFH97",
}
UNLOCK_OBJECT_KEYS = [
    "data\\ini\\object\\specter\\pla\\airforce\\j16d.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\j20b.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\j20b_aa.ini",
    "data\\ini\\object\\specter\\pla\\airforce\\jh7a2.ini",
    "data\\ini\\object\\specter\\pla\\drones\\ch5.ini",
    "data\\ini\\object\\specter\\pla\\drones\\asn301.ini",
    "data\\ini\\object\\specter\\pla\\china_system.ini",
]
UNLOCK_BUTTONS = [
    "Command_ConstructChinaDroneCH7",
    "Command_ConstructChinaDroneJXDS",
    "Command_ConstructChinaDroneWZ8",
    "Command_ConstructChinaDroneFH97",
]
FIRE_WEAPONS = [
    "China_Weapon_KD88_J11B",
    "China_Weapon_FAB_J11B",
    "China_Weapon_FAB2_J11B",
    "China_Weapon_YJ83_J15",
    "China_Weapon_LT3_J15",
    "China_Weapon_YJ12_J15",
    "China_Weapon_LS6_J31",
    "China_Weapon_FT7_J31",
    "China_Weapon_LS6B_J31",
    "China_Weapon_LT2_JF17",
    "China_Weapon_CM802_JF17",
    "China_Weapon_MK82_JF17",
    "China_Weapon_CJ10_H6K",
    "China_Weapon_FAB_H6K",
    "China_Weapon_CJ100_H20",
    "China_Weapon_FAB_H20",
    "China_Weapon_Carpet_H6K",
    "China_Weapon_10Ton_H20A",
]



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
    updated = 0
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    for key, value in CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value.replace("\r", "").replace("\n", "")):
            raise SystemExit(f"non-ASCII CSF key or value: {key}")
        if key in have_idx:
            i = have_idx[key]
            mag, name, strings = labels[i]
            labels[i] = (mag, name, [(CSF_STR_MAGIC, value, b"")])
            updated += 1
            continue
        labels.append((CSF_LBL_MAGIC, key, [(CSF_STR_MAGIC, value, b"")]))
        added += 1
        have.add(key)
    print(f"CSF added {added} labels, updated {updated}, fixed {fixed_magic} STR->RTS magics")
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
    if text.count("CommandSet PLAAirfieldCommandSet") != 1:
        errors.append("PLAAirfield CommandSet count != 1")
    large = grab_block(text, "China_LargeAirBaseCommandSet")
    heavy = grab_block(text, "China_HeavyAirBaseCommandSet")
    pla = grab_block(text, "PLAAirfieldCommandSet")
    if not large.rstrip().endswith("End"):
        errors.append("Large missing End")
    if not heavy.rstrip().endswith("End"):
        errors.append("Heavy missing End")
    if not pla.rstrip().endswith("End"):
        errors.append("PLAAirfield missing End")
    if "CommandSet " in large.split("\n", 1)[-1]:
        errors.append("nested CommandSet inside Large")
    if "CommandSet " in heavy.split("\n", 1)[-1]:
        errors.append("nested CommandSet inside Heavy")
    for line in (large + "\n" + heavy + "\n" + pla).splitlines()[1:]:
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
        "Command_ConstructChinaBomberH20",
        "Command_ConstructChinaBomberH20A",
    ]
    large_idx = text.find("CommandSet China_LargeAirBaseCommandSet")
    prefix = text[:large_idx]
    for btn in required_btns:
        if f"CommandButton {btn}" not in prefix:
            errors.append(f"button {btn} not defined before China_LargeAirBaseCommandSet")
        if prefix.count(f"CommandButton {btn}") != 1:
            errors.append(f"button {btn} duplicate or missing in CommandSet.ini prefix")
    if any(ord(ch) > 127 for ch in large + heavy + pla + INLINE_BUTTONS):
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
        "Command_ConstructChinaBomberH20",
        "Command_ConstructChinaBomberH20A",
        "Command_ConstructChinaJetJ20B_AA",
        "Command_ConstructChinaJetJ20B_AG",
        "Command_ConstructChinaJetJ10C",
    ]
    blob = large + heavy
    for btn in keep:
        if btn not in blob:
            errors.append(f"lost aircraft button {btn}")
    china_air = large + heavy + pla
    for btn in REMOVED_CONSTRUCT_BUTTONS:
        if btn in china_air:
            errors.append(f"removed unit still on China airbase menu: {btn}")
    russia = grab_block(text, "ChinaAirfieldCommandSet")
    if "Command_ConstructRussian_Su35" not in russia:
        errors.append("ChinaAirfieldCommandSet Russia baseline was modified")
    if errors:
        raise SystemExit("PARSER CHECK FAIL CommandSet.ini\n" + "\n".join(errors))
    print("PARSER CHECK PASS CommandSet.ini")


def ensure_inline_buttons(text: str) -> str:
    needle = "CommandSet China_LargeAirBaseCommandSet"
    idx = text.find(needle)
    if idx < 0:
        raise SystemExit("China_LargeAirBaseCommandSet not found in packed CommandSet.ini")
    missing = []
    for m in re.finditer(
        r"CommandButton (\S+)\s*\n.*?^End\s*$",
        INLINE_BUTTONS,
        re.M | re.S,
    ):
        btn = m.group(1)
        if f"CommandButton {btn}" not in text:
            missing.append(m.group(0).rstrip() + "\n\n")
    if missing:
        text = text[:idx] + "".join(missing) + text[idx:]
        print(f"Inlined {len(missing)} China construct CommandButtons before Large AirBase")
    return text


def patch_commandset(text: str) -> str:
    text = ensure_inline_buttons(text)

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

    pla_pat = re.compile(
        r"CommandSet PLAAirfieldCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    if not pla_pat.search(text):
        raise SystemExit("PLAAirfieldCommandSet not found in packed CommandSet.ini")
    text = pla_pat.sub(NEW_PLA_AIRFIELD_COMMANDSET.rstrip() + "\n", text, count=1)
    validate_china_commandsets(text)
    return text


def strip_named_objects(text: str, names: set[str]) -> str:
    parts = re.split(r"(?=^Object )", text, flags=re.M)
    out = []
    removed = []
    for part in parts:
        m = re.match(r"Object (\S+)", part)
        if m and m.group(1) in names:
            removed.append(m.group(1))
            continue
        out.append(part)
    print("Removed Object blocks:", removed)
    return "".join(out)


def strip_named_commandbuttons(text: str, names: list[str]) -> str:
    for btn in names:
        pat = re.compile(
            rf"CommandButton {re.escape(btn)}\s*\n.*?^End\s*\n?",
            re.M | re.S,
        )
        text, n = pat.subn("", text, count=1)
        if n:
            print(f"Removed CommandButton {btn}")
        else:
            print(f"WARNING: CommandButton {btn} not found to remove")
    return text


def patch_airbase_construct_buttons(text: str) -> str:
    heavy_pat = re.compile(
        r"CommandButton Command_ConstructChina_HeavyAirBase\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    m = heavy_pat.search(text)
    if not m:
        raise SystemExit("Command_ConstructChina_HeavyAirBase not found")
    block = m.group(0)
    block = re.sub(
        r"(?m)^([ \t]*TextLabel[ \t]*=[ \t]*).*$",
        r"\1CONTROLBAR:ConstructChina_HeavyAirBase",
        block,
        count=1,
    )
    block = re.sub(
        r"(?m)^([ \t]*ButtonImage[ \t]*=[ \t]*).*$",
        r"\1pla_airfield",
        block,
        count=1,
    )
    block = re.sub(
        r"(?m)^([ \t]*DescriptLabel[ \t]*=[ \t]*).*$",
        r"\1CONTROLBAR:ToolTipChina_HeavyAirBase",
        block,
        count=1,
    )
    if "Object        = China_HeavyAirBase" not in block and "Object = China_HeavyAirBase" not in block:
        raise SystemExit("Heavy AirBase construct button Object is not China_HeavyAirBase")
    text = heavy_pat.sub(block, text, count=1)

    fighter_pat = re.compile(
        r"CommandButton Command_ConstructChinaAirfield\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    fm = fighter_pat.search(text)
    if not fm:
        raise SystemExit("Command_ConstructChinaAirfield not found")
    fblock = fm.group(0)
    if "Object        = China_LargeAirBase" not in fblock and "Object = China_LargeAirBase" not in fblock:
        raise SystemExit("Fighter Airbase construct button Object is not China_LargeAirBase")
    if "pla_airfield" not in fblock:
        raise SystemExit("Fighter Airbase construct button missing pla_airfield")
    print("Patched China Fighter/Heavy Airbase construct CommandButtons")
    return text


def patch_y20aew_ocl(text: str) -> str:
    marker = "ObjectCreationList OCL_ChinaY20AEWTargetedSARScan"
    if marker in text:
        return text
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + NEW_Y20AEW_OCL
    print("Added OCL_ChinaY20AEWTargetedSARScan")
    return text


def strip_object_science(text: str, names: set[str]) -> str:
    parts = re.split(r"(?=^Object )", text, flags=re.M)
    out = []
    for part in parts:
        m = re.match(r"Object (\S+)", part)
        if not (m and m.group(1) in names):
            out.append(part)
            continue
        part = re.sub(
            r"(?m)^[ \t]*Science\s*=\s*SCIENCE_(?:Rank\d+|ChinaStealthTech|ChinaDrones)[ \t]*\r?\n",
            "",
            part,
        )
        if not re.search(r"(?m)^[ \t]*Buildable\s*=", part):
            if re.search(r"(?m)^[ \t]*Prerequisites\s*$", part):
                part = re.sub(
                    r"(?ms)^([ \t]*Prerequisites[ \t]*\r?\n)(.*?)(^[ \t]*End[ \t]*\r?$)",
                    r"\1\2\3\n  Buildable = Ignore_Prerequisites",
                    part,
                    count=1,
                )
            else:
                part = re.sub(
                    r"(?m)^([ \t]*BuildCost)",
                    "  Prerequisites\n  End\n  Buildable = Ignore_Prerequisites\n\\1",
                    part,
                    count=1,
                )
        out.append(part)
    return "".join(out)


def unlock_commandbuttons(text: str) -> str:
    for btn in UNLOCK_BUTTONS:
        pat = re.compile(
            rf"(CommandButton {re.escape(btn)}\s*\n.*?^End\s*$)",
            re.M | re.S,
        )
        m = pat.search(text)
        if not m:
            print(f"WARNING: unlock button {btn} not found")
            continue
        block = re.sub(
            r"(?m)^[ \t]*Science\s*=\s*SCIENCE_(?:Rank\d+|ChinaStealthTech|ChinaDrones)[ \t]*\r?\n",
            "",
            m.group(1),
        )
        text = text[: m.start(1)] + block + text[m.end(1) :]
    return text


def inline_weapons(weapon_ini: str) -> str:
    blobs = []
    patch_ini = ROOT / "patch/Data/INI"
    for name in WEAPON_OVERLAY_FILES:
        path = patch_ini / name
        if not path.is_file():
            raise SystemExit(f"missing weapon overlay {path}")
        blobs.append(lf(path.read_bytes()).decode("utf-8"))
    combined = "\n".join(blobs)
    if any(ord(ch) > 127 for ch in combined):
        raise SystemExit("non-ASCII in China weapon overlay (Weapon.ini is latin1)")
    missing = [w for w in FIRE_WEAPONS if f"Weapon {w}" not in combined]
    if missing:
        raise SystemExit("overlay weapons missing: " + ", ".join(missing))
    # Replace previously inlined block if re-packing.
    marker_start = "; ===== SPECTER CHINA AIR EXPANSION WEAPONS BEGIN ====="
    marker_end = "; ===== SPECTER CHINA AIR EXPANSION WEAPONS END ====="
    block = marker_start + "\n" + combined.strip() + "\n" + marker_end + "\n"
    if marker_start in weapon_ini:
        weapon_ini = re.sub(
            re.escape(marker_start) + r".*?" + re.escape(marker_end) + r"\n?",
            block,
            weapon_ini,
            count=1,
            flags=re.S,
        )
    else:
        if not weapon_ini.endswith("\n"):
            weapon_ini += "\n"
        weapon_ini += "\n" + block
    for w in FIRE_WEAPONS:
        if weapon_ini.count(f"Weapon {w}") != 1:
            raise SystemExit(f"Weapon.ini count for {w} is {weapon_ini.count('Weapon ' + w)}")
    print("Inlined China expansion weapons into Weapon.ini")
    return weapon_ini


def validate_unlocks(v_map: dict[str, bytes]) -> None:
    errors = []
    for key in UNLOCK_OBJECT_KEYS:
        if key not in v_map:
            errors.append(f"missing unlock file {key}")
            continue
        text = v_map[key].decode("latin1", errors="replace")
        parts = re.split(r"(?=^Object )", text, flags=re.M)
        for part in parts:
            m = re.match(r"Object (\S+)", part)
            if not (m and m.group(1) in CHINA_AIRCRAFT_UNLOCK_OBJECTS):
                continue
            if re.search(r"(?m)^[ \t]*Science\s*=\s*SCIENCE_(?:Rank\d+|ChinaStealthTech|ChinaDrones)", part):
                errors.append(f"{m.group(1)} still has science/rank prereq")
            if "Ignore_Prerequisites" not in part:
                errors.append(f"{m.group(1)} missing Buildable Ignore_Prerequisites")
    cb = v_map["data\\ini\\commandbutton.ini"].decode("latin1", errors="replace")
    for btn in UNLOCK_BUTTONS:
        m = re.search(
            rf"CommandButton {re.escape(btn)}\s*\n.*?^End\s*$",
            cb,
            re.M | re.S,
        )
        if not m:
            errors.append(f"button {btn} missing")
            continue
        if re.search(r"(?m)^[ \t]*Science\s*=", m.group(0)):
            errors.append(f"button {btn} still has Science")
    if errors:
        raise SystemExit("UNLOCK CHECK FAIL\n" + "\n".join(errors))
    print("UNLOCK CHECK PASS")


def validate_fire_and_scale(v_map: dict[str, bytes]) -> None:
    errors = []
    weapon = v_map["data\\ini\\weapon.ini"].decode("latin1", errors="replace")
    for w in FIRE_WEAPONS:
        if f"Weapon {w}" not in weapon:
            errors.append(f"Weapon.ini missing {w}")
    banned_a2a = ["China_Weapon_PL12_J11B"]
    for w in banned_a2a:
        if f"Weapon {w}" in weapon:
            errors.append(f"A2A weapon still present: {w}")
    fighters = {
        "data\\ini\\object\\specter\\pla\\airforce\\j31.ini": "China_Weapon_LS6_J31",
        "data\\ini\\object\\specter\\pla\\airforce\\j11b.ini": "China_Weapon_KD88_J11B",
        "data\\ini\\object\\specter\\pla\\airforce\\j15.ini": "China_Weapon_YJ83_J15",
        "data\\ini\\object\\specter\\pla\\airforce\\jf17.ini": "China_Weapon_LT2_JF17",
    }
    for key, primary in fighters.items():
        text = v_map[key].decode("latin1", errors="replace")
        if "GenericTacticalBomberCommandSet" not in text:
            errors.append(f"{key} not on GenericTacticalBomberCommandSet")
        if "GenericMultiRoleFighter_AG_CommandSet" in text:
            errors.append(f"{key} still on GMRF AG commandset")
        if f"PRIMARY    {primary}" not in text and f"PRIMARY {primary}" not in text:
            errors.append(f"{key} missing PRIMARY {primary}")
        if "WeaponLaunchBone    = PRIMARY   WeaponA" not in text:
            errors.append(f"{key} missing PRIMARY WeaponA launch bone")
        if "AntiGround" in text:
            pass
        if "China_Weapon_PL12" in text:
            errors.append(f"{key} still uses PL-12 A2A")
    scales = {
        "data\\ini\\object\\specter\\pla\\airforce\\h6k.ini": "0.85",
        "data\\ini\\object\\specter\\pla\\airforce\\y20.ini": "1.00",
        "data\\ini\\object\\specter\\pla\\airforce\\y20aew.ini": "0.90",
        "data\\ini\\object\\specter\\pla\\airforce\\h20.ini": "1.15",
        "data\\ini\\object\\specter\\pla\\airforce\\h20a.ini": "1.15",
        "data\\ini\\object\\specter\\pla\\airforce\\j31.ini": "1.15",
    }
    for key, scale in scales.items():
        text = v_map[key].decode("latin1", errors="replace")
        if f"Scale = {scale}" not in text:
            errors.append(f"{key} scale is not {scale}")
    h20 = v_map.get("data\\ini\\object\\specter\\pla\\airforce\\h20.ini", b"").decode("latin1", errors="replace")
    if not h20:
        errors.append("H20.ini missing from DATA")
    else:
        if "Model               = NVH20" not in h20 and "Model = NVH20" not in h20:
            errors.append("H-20 Draw Model is not NVH20")
        if "AVB21" in h20 or "AVB3bmbr" in h20:
            errors.append("H-20 INI still references B-2 model")
        if "StealthUpdate" not in h20 or "InnateStealth = Yes" not in h20:
            errors.append("H-20 missing innate StealthUpdate")
        if "GenericTacticalBomberCommandSet" not in h20:
            errors.append("H-20 not on GenericTacticalBomberCommandSet")
        if "China_Weapon_CJ100_H20" not in h20:
            errors.append("H-20 missing PRIMARY cruise weapon")
        if "WeaponLaunchBone    = PRIMARY   WEAPONA01" not in h20:
            errors.append("H-20 missing PRIMARY WEAPONA01 launch bone")
        if "Buildable           = Ignore_Prerequisites" not in h20:
            errors.append("H-20 still has science/rank lock")
    h20a = v_map.get("data\\ini\\object\\specter\\pla\\airforce\\h20a.ini", b"").decode("latin1", errors="replace")
    if not h20a:
        errors.append("H20A.ini missing from DATA")
    else:
        if "Object ChinaBomberH20A" not in h20a:
            errors.append("H-20A object name missing")
        if "Model               = NVH20" not in h20a and "Model = NVH20" not in h20a:
            errors.append("H-20A Draw Model is not NVH20")
        if "AVB21" in h20a or "AVB3bmbr" in h20a:
            errors.append("H-20A INI still references B-2 model")
        if "China_Weapon_10Ton_H20A" not in h20a:
            errors.append("H-20A missing B-2A style 10-ton PRIMARY")
        if "China_Weapon_CJ100_H20" in h20a:
            errors.append("H-20A must not reuse H-20 cruise PRIMARY")
        if "GenericTacticalBomberCommandSet" not in h20a:
            errors.append("H-20A not on GenericTacticalBomberCommandSet")
        if "WeaponLaunchBone    = PRIMARY   WEAPONA01" not in h20a:
            errors.append("H-20A missing PRIMARY WEAPONA01 launch bone")
    h6k = v_map.get("data\\ini\\object\\specter\\pla\\airforce\\h6k.ini", b"").decode("latin1", errors="replace")
    if "PRIMARY    China_Weapon_Carpet_H6K" not in h6k and "PRIMARY China_Weapon_Carpet_H6K" not in h6k:
        errors.append("H-6K PRIMARY is not carpet bomb weapon")
    if "Model               = h6k" not in h6k and "Model = h6k" not in h6k:
        errors.append("H-6K model changed")
    if "FireOCL = OCL_AmericaB52FifteenBombLine" not in weapon:
        errors.append("H-6K carpet weapon missing B-52 bomb-line FireOCL")
    if "ProjectileObject        = AmericaB2A10TonBombProjectile" not in weapon:
        errors.append("H-20A 10-ton weapon missing B-2A projectile")
    y20 = v_map.get("data\\ini\\object\\specter\\pla\\airforce\\y20aew.ini", b"").decode("latin1", errors="replace")
    if "VisionRange = 1100" not in y20:
        errors.append("Y-20 AEW VisionRange not increased")
    if "ShroudClearingRange = 1200" not in y20:
        errors.append("Y-20 AEW ShroudClearingRange not increased")
    if "DetectionRange = 3600" not in y20:
        errors.append("Y-20 AEW DetectionRange not increased")
    if "OCL_ChinaY20AEWTargetedSARScan" not in y20:
        errors.append("Y-20 AEW missing unique larger SAR OCL")
    if "HXYun20YJ" not in y20:
        errors.append("Y-20 AEW model changed")
    large_ab = v_map.get("data\\ini\\object\\specter\\pla\\buildings\\china_largeairbase.ini", b"").decode("latin1", errors="replace")
    heavy_ab = v_map.get("data\\ini\\object\\specter\\pla\\buildings\\china_heavyairbase.ini", b"").decode("latin1", errors="replace")
    if "SelectPortrait         = pla_airfield" not in large_ab:
        errors.append("Fighter Airbase portrait is not pla_airfield")
    if "DisplayName      = OBJECT:China_LargeAirBase" not in large_ab:
        errors.append("Fighter Airbase DisplayName not unique")
    if "CommandSet          = China_LargeAirBaseCommandSet" not in large_ab:
        errors.append("Fighter Airbase CommandSet wrong")
    if "SelectPortrait         = pla_airfield" not in heavy_ab:
        errors.append("Heavy Airbase portrait is not pla_airfield")
    if "DisplayName      = OBJECT:China_HeavyAirBase" not in heavy_ab:
        errors.append("Heavy Airbase DisplayName not unique")
    if "CommandSet          = China_HeavyAirBaseCommandSet" not in heavy_ab:
        errors.append("Heavy Airbase CommandSet wrong")
    if errors:
        raise SystemExit("FIRE/SCALE CHECK FAIL\n" + "\n".join(errors))
    print("FIRE/SCALE CHECK PASS")


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
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/china_airforce_cleanup"))
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
        if rel.startswith("INI/Object/Specter/PLA/Buildings/") and path.name in OVERLAY_BUILDING_FILES:
            keep = True
        if path.name in OVERLAY_NAMED:
            keep = True
        if not keep:
            continue
        big_name = "Data\\" + rel.replace("/", "\\")
        overlay[big_name] = lf(path.read_bytes())

    parse_check(overlay)

    dropped = []
    drop_keys = DROP_OVERLAY_BUTTON_FILES | DROP_OVERLAY_WEAPON_FILES
    for key in list(data_map):
        if key in drop_keys:
            dropped.append(data_map[key][0])
            del data_map[key]
    if dropped:
        print("Dropped overlay CommandButton/Weapon files (inlined):", dropped)
    data_keys[:] = [k for k in data_keys if k not in drop_keys]

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

    cb_key = "data\\ini\\commandbutton.ini"
    cb_name, cb_bytes = data_map[cb_key]
    cb_text = unlock_commandbuttons(cb_bytes.decode("latin1"))
    cb_text = strip_named_commandbuttons(cb_text, REMOVED_CONSTRUCT_BUTTONS)
    cb_text = patch_airbase_construct_buttons(cb_text)
    data_map[cb_key] = (cb_name, lf(cb_text.encode("latin1")))
    print("Unlocked remaining China aircraft/drone construct CommandButtons")

    for key in UNLOCK_OBJECT_KEYS:
        if key not in data_map:
            raise SystemExit(f"missing packed unlock target {key}")
        name, blob = data_map[key]
        text = lf(blob).decode("latin1")
        data_map[key] = (name, lf(strip_object_science(text, CHINA_AIRCRAFT_UNLOCK_OBJECTS).encode("latin1")))
    print("Removed science/rank prereqs from China aircraft objects")

    sys_key = "data\\ini\\object\\specter\\pla\\china_system.ini"
    sys_name, sys_blob = data_map[sys_key]
    sys_text = lf(sys_blob).decode("latin1")
    sys_text = strip_named_objects(sys_text, REMOVE_CHINA_OBJECTS)
    data_map[sys_key] = (sys_name, lf(sys_text.encode("latin1")))

    w_key = "data\\ini\\weapon.ini"
    w_name, w_bytes = data_map[w_key]
    w_text = inline_weapons(w_bytes.decode("latin1"))
    data_map[w_key] = (w_name, lf(w_text.encode("latin1")))

    ocl_key = "data\\ini\\objectcreationlist.ini"
    ocl_name, ocl_bytes = data_map[ocl_key]
    ocl_text = patch_y20aew_ocl(ocl_bytes.decode("latin1"))
    data_map[ocl_key] = (ocl_name, lf(ocl_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_bytes = data_map[csf_key]
    data_map[csf_key] = (csf_name, patch_csf(csf_bytes))

    added_data = []
    for big_name, content in overlay.items():
        key = norm_key(big_name)
        if key in data_map:
            if key not in ALLOW_OVERWRITE:
                raise SystemExit(f"Refusing to overwrite existing DATA entry: {big_name}")
            data_map[key] = (data_map[key][0], content)
            added_data.append(big_name + " (updated)")
        else:
            data_map[key] = (big_name, content)
            added_data.append(big_name)

    added_art = []
    if REBUILD_ART:
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
    else:
        added_art.append("ART unchanged (DATA-only cleanup; reuse china_h20 ART)")

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
    data_bytes = build_big(final_data)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(data_bytes)

    zpath = out / "CHINA_AIRFORCE_CLEANUP.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")

    # Post-pack verify from written DATA + reused china_h20 ART.
    v_entries, v_raw = read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[norm_key(name)] = v_raw[off : off + size]
    a_entries, a_raw = read_big(BASE_ART)
    a_names = {norm_key(n) for n, _o, _s in a_entries}
    art_bytes = BASE_ART.read_bytes()

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

    cs = v_map["data\\ini\\commandset.ini"].decode("latin1")
    validate_china_commandsets(cs)
    if "Command_ConstructChinaDroneCH5" not in cs:
        raise SystemExit("CH-5 button missing from CommandSet")
    if cs.count("CommandSet China_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("duplicate heavy CommandSet")
    if "CommandButton Command_ConstructChinaBomberH20A" not in cs:
        raise SystemExit("H-20A CommandButton not inlined in CommandSet.ini")
    heavy_block = grab_block(cs, "China_HeavyAirBaseCommandSet")
    if "Command_ConstructChinaBomberH20" not in heavy_block:
        raise SystemExit("H-20 missing from China_HeavyAirBaseCommandSet")
    if "Command_ConstructChinaBomberH20A" not in heavy_block:
        raise SystemExit("H-20A missing from China_HeavyAirBaseCommandSet")
    large_block = grab_block(cs, "China_LargeAirBaseCommandSet")
    if "Command_ConstructChinaJetJ20B_AA" not in large_block:
        raise SystemExit("J-20B AA missing from Fighter Airbase")
    if "Command_ConstructChinaJetJ20B_AA_AI" in large_block:
        raise SystemExit("duplicate J-20B AA_AI still on Fighter Airbase")

    csf_blob = v_map["data\\english\\generals.csf"]
    ini_refs = []
    for k, blob in v_map.items():
        if not k.endswith(".ini"):
            continue
        if (
            "pla\\airforce\\" not in k
            and "pla\\buildings\\china_" not in k
            and k not in ("data\\ini\\commandset.ini", "data\\ini\\commandbutton.ini")
        ):
            continue
        text = blob.decode("latin1", errors="replace")
        ini_refs.extend(re.findall(r"(?:OBJECT|CONTROLBAR):[A-Za-z0-9_]+", text))
    required_new = sorted(CSF_LABELS.keys())
    validate_csf(csf_blob, required_new)
    version, unk, lang, labels = parse_csf(csf_blob)
    have_names = {name for _, name, _ in labels}
    prefixes = (
        "OBJECT:ChinaJet",
        "OBJECT:ChinaBomber",
        "OBJECT:ChinaAircraft",
        "OBJECT:China_LargeAirBase",
        "OBJECT:China_HeavyAirBase",
        "CONTROLBAR:ConstructChinaJet",
        "CONTROLBAR:ToolTipChinaJet",
        "CONTROLBAR:ConstructChinaBomber",
        "CONTROLBAR:ToolTipChinaBomber",
        "CONTROLBAR:ConstructChinaAircraft",
        "CONTROLBAR:ToolTipChinaAircraft",
        "CONTROLBAR:ConstructChinaAirfield",
        "CONTROLBAR:ToolTipChinaBuildAirField",
        "CONTROLBAR:ConstructChina_HeavyAirBase",
        "CONTROLBAR:ToolTipChina_HeavyAirBase",
    )
    missing_ini = sorted({r for r in ini_refs if r.startswith(prefixes) and r not in have_names})
    if missing_ini:
        raise SystemExit("CSF missing INI refs: " + ", ".join(missing_ini))
    print("CSF INI-REF CHECK PASS")

    for banned in DROP_OVERLAY_BUTTON_FILES | DROP_OVERLAY_WEAPON_FILES:
        if banned in v_map:
            raise SystemExit(f"overlay file still packed: {banned}")

    for req in (
        "data\\ini\\object\\specter\\pla\\airforce\\h6k.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\y20.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\y20aew.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\j11b.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\j15.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\j31.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\jf17.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\h20.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\h20a.ini",
        "data\\ini\\object\\specter\\pla\\buildings\\china_largeairbase.ini",
        "data\\ini\\object\\specter\\pla\\buildings\\china_heavyairbase.ini",
        "data\\ini\\mappedimages\\handcreated\\china_heavyexpansion_images.ini",
        "data\\ini\\weapon.ini",
        "data\\ini\\objectcreationlist.ini",
    ):
        if req not in v_map:
            raise SystemExit(f"overlay missing from DATA BIG: {req}")

    validate_unlocks(v_map)
    validate_fire_and_scale(v_map)

    cb = v_map["data\\ini\\commandbutton.ini"].decode("latin1")
    for btn in REMOVED_CONSTRUCT_BUTTONS:
        if f"CommandButton {btn}" in cb:
            raise SystemExit(f"removed CommandButton still packed: {btn}")
    if "CONTROLBAR:ConstructChina_HeavyAirBase" not in cb:
        raise SystemExit("Heavy Airbase construct button missing China CSF key")
    if "ButtonImage   = pla_airfield" not in cb and "ButtonImage = pla_airfield" not in cb:
        raise SystemExit("no pla_airfield construct ButtonImage in CommandButton.ini")
    heavy_btn = re.search(
        r"CommandButton Command_ConstructChina_HeavyAirBase\s*\n.*?^End\s*$",
        cb,
        re.M | re.S,
    )
    if not heavy_btn or "pla_airfield" not in heavy_btn.group(0):
        raise SystemExit("Heavy Airbase construct button icon is not pla_airfield")
    sys_txt = v_map["data\\ini\\object\\specter\\pla\\china_system.ini"].decode("latin1")
    for obj in REMOVE_CHINA_OBJECTS:
        if re.search(rf"^Object {re.escape(obj)}\b", sys_txt, re.M):
            raise SystemExit(f"removed object still in china_system.ini: {obj}")
    ocl = v_map["data\\ini\\objectcreationlist.ini"].decode("latin1")
    if "ObjectCreationList OCL_ChinaY20AEWTargetedSARScan" not in ocl:
        raise SystemExit("Y-20 AEW SAR OCL missing from ObjectCreationList.ini")
    print("CLEANUP CHECK PASS")

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
        "art\\w3d\\nvh20.w3d",
        "art\\textures\\h-20.dds",
        "art\\textures\\h-20.tga",
        "art\\textures\\avb3bmbr.dds",
    ):
        if req not in a_names:
            raise SystemExit(f"ART missing {req}")

    nvh = None
    avb3 = None
    for name, off, size in a_entries:
        low = name.lower().replace("/", "\\")
        if low == "art\\w3d\\nvh20.w3d":
            nvh = a_raw[off : off + size]
        elif low == "art\\w3d\\avb3bmbr.w3d":
            avb3 = a_raw[off : off + size]
    if nvh is None or len(nvh) != 42121:
        raise SystemExit(f"NVH20.W3D missing or wrong size {0 if nvh is None else len(nvh)}")
    if avb3 is not None and nvh == avb3:
        raise SystemExit("NVH20.W3D is a copy of AVB3bmbr.W3D (B-2 fake)")
    if b"H-20" not in nvh or b"NVH20" not in nvh:
        raise SystemExit("NVH20.W3D missing H-20/NVH20 texture or hierarchy strings")

    report = out / "PACK_REPORT.txt"
    report.write_text(
        "\n".join(
            [
                f"DATA SHA256={hashlib.sha256(data_bytes).hexdigest()} SIZE={len(data_bytes)}",
                f"ART  SHA256={hashlib.sha256(art_bytes).hexdigest()} SIZE={len(art_bytes)} (unchanged china_h20 ART, not in ZIP)",
                f"ZIP  SHA256={hashlib.sha256(zpath.read_bytes()).hexdigest()} SIZE={zpath.stat().st_size}",
                "PACKAGING=DATA_ONLY _SPEC_DATA_ONE.big",
                "added_data=" + repr(added_data),
                "added_art=" + repr(added_art),
                NEW_LARGE_COMMANDSET,
                NEW_COMMANDSET,
                "PARSER CHECK PASS",
                "CSF CHECK PASS",
                "UNLOCK CHECK PASS",
                "FIRE/SCALE CHECK PASS",
                "CLEANUP CHECK PASS",
                "PROTECTED J10C AND H6M HASHES UNCHANGED",
                "REMOVED KJ500 JH7BHeavy J50 J16BBunker from China airbases",
                "REMOVED duplicate J-20B AA_AI loadout button; kept ChinaJetJ20B_AA",
                "H-20 SCALE 1.15; H-20A ADDED (NVH20 + B-2A 10-ton bomb)",
                "H-6K PRIMARY carpet FireOCL OCL_AmericaB52FifteenBombLine",
                "Y-20 AEW radar/scan increased; unique SAR ping Vision 520",
                "J-31 SCALE 1.15 visual only",
                "FIGHTER/HEAVY AIRBASE construct buttons: pla_airfield + China CSF",
                "RUSSIA BASELINE UNTOUCHED (ChinaAirfieldCommandSet kept)",
            ]
        )
        + "\n"
    )
    print(report.read_text())
    print(f"Wrote {out_data} {zpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
