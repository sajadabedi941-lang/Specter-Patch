#!/usr/bin/env python3
"""Restore Japan / South Korea air rosters on current packed DATA + ART.

- Does not edit USA or Russia aircraft INIs.
- Reuses AmericaJetV22Visual, AmericaJetE2Visual, AmericaUAVGlobalHawk.
- Uses existing packed JP/SK objects; fixes Buildable=NoScale corruption.
- Donor ART (meshes/textures only) is injected into _SPEC_ART_ONE.big.
- Missing JP/KR silhouettes get uniquely named ART clones from the closest
  real mesh. Never Model= E-3G, C-17, Hawkeye, C-130, or Lynx as those units.
- DATA Draw modules point at those donor / cloned visuals. Donor DATA is not copied.
- STOCK cores are surgically patched (CommandSet / CommandButton / CSF).
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/c17_b52_jp_kr_pass/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/usa_airforce_final/_SPEC_ART_ONE.big")
DONOR_ART = Path("/tmp/donor_jp_kr_art")
OUT_DIR = Path("/tmp/japan_korea_airforce")

# Donor ART to inject (W3D + matching textures). Never copy donor DATA.
DONOR_INJECT = [
    "Art/w3d/LSFJapanAH64D.W3D",
    "Art/w3d/LSFJapanAH64Dd.W3D",
    "Art/w3d/LSFJPUH60.W3D",
    "Art/w3d/LSFJPUH60d.W3D",
    "Art/w3d/LSFJPUH60k.W3D",
    "Art/w3d/LSFKoreaF4.W3D",
    "Art/w3d/LSFKoreaF4d.W3D",
    "Art/w3d/LSFKoreaF4k.W3D",
    "Art/w3d/LSFKoreaF4r.W3D",
    "Art/w3d/LSFKoreaF5.W3D",
    "Art/w3d/LSFKoreaF5d.W3D",
    "Art/w3d/LSFKoreaF5k.W3D",
    "Art/w3d/LSFKoreaF5r.W3D",
    "Art/w3d/LSFKoreaUH60.W3D",
    "Art/w3d/LSFKoreaUH60d.W3D",
    "Art/w3d/LSFKoreaUH60k.W3D",
    "Art/Textures/LSFJPAH64D.dds",
    "Art/Textures/LSFJPAH64Dd.dds",
    "Art/Textures/LSFJPUH60.dds",
    "Art/Textures/LSFJPUH60d.dds",
    "Art/Textures/LSFJPUH60k.dds",
    "Art/Textures/LSFSKUH60.dds",
    "Art/Textures/LSFSKUH60d.dds",
    "Art/Textures/LSFSKUH60k.dds",
    "Art/Textures/LSFKF4.dds",
    "Art/Textures/LSFKF4d.dds",
    "Art/Textures/LSFKF4k.dds",
    "Art/Textures/LSFKF5.dds",
    "Art/Textures/LSFKF5d.dds",
    "Art/Textures/LSFKF5k.dds",
    "Art/Textures/LSFF15Kd.dds",
    # Twin-engine tactical transport (C-160 class) — no Kawasaki C-2 / CN-235 mesh exists.
    "Art/w3d/LSFGERC160.W3D",
    "Art/w3d/LSFGERC160d.W3D",
    "Art/w3d/LSFGERC160k.W3D",
    "Art/Textures/LSFGERC160.tga",
    "Art/Textures/LSFGERC160d.tga",
    "Art/Textures/LSFGERC160k.tga",
    # Light attack helicopter (AH-6 / MD 500 class) — no Korean LAH mesh exists.
    "Art/w3d/LSFAH6.W3D",
    "Art/w3d/LSFAH6d.W3D",
    "Art/w3d/LSFAH6k.W3D",
    "Art/Textures/LSFAH6.dds",
    "Art/Textures/LSFAH6d.dds",
    "Art/Textures/LSFAH6k.dds",
    # Small twin-engine recon airframe — no Hawker 800 / RC-800 mesh exists.
    "Art/w3d/SAAB340.W3D",
    "Art/w3d/SAAB340_d.W3D",
    "Art/Textures/Saab340.dds",
    "Art/Textures/Saab340_d.dds",
    "Art/Textures/LakeduskMetal.dds",
    "Art/Textures/TP84 Blades.tga",
    "Art/Textures/coplight.dds",
]

# Unique JP/SK W3D stems cloned from the closest real mesh. DATA must never
# Model= US_E3G, IUAC17HXNew, AVHawk, AVCargoPln, or LSFLynxAHMK for these units.
# Source is a packed ART name after DONOR_INJECT (or already in SRC_ART).
ART_CLONES = [
    # E-767: no 767 exists. Closest is Boeing AEW&C with rotodome (E-737), not E-3.
    ("Art\\W3D\\JP_E767.W3D", "Art\\W3D\\KVE737.W3D"),
    # C-2: no twin-jet transport exists. Twin-engine high-wing ramp (C-160), not C-17.
    ("Art\\W3D\\JP_C2.W3D", "Art\\W3D\\LSFGERC160.W3D"),
    ("Art\\W3D\\JP_C2d.W3D", "Art\\W3D\\LSFGERC160d.W3D"),
    ("Art\\W3D\\JP_C2k.W3D", "Art\\W3D\\LSFGERC160k.W3D"),
    # CN-235: twin-turboprop tactical transport. C-160 class, not C-130.
    ("Art\\W3D\\SK_CN235.W3D", "Art\\W3D\\LSFGERC160.W3D"),
    ("Art\\W3D\\SK_CN235d.W3D", "Art\\W3D\\LSFGERC160d.W3D"),
    ("Art\\W3D\\SK_CN235k.W3D", "Art\\W3D\\LSFGERC160k.W3D"),
    # RC-800: small twin-engine recon, not E-2 Hawkeye.
    ("Art\\W3D\\SK_RC800.W3D", "Art\\W3D\\SAAB340.W3D"),
    ("Art\\W3D\\SK_RC800d.W3D", "Art\\W3D\\SAAB340_d.W3D"),
    # KUH-1 Surion: UH-60-derived, unique stem so it is not the UH-60P object.
    ("Art\\W3D\\SK_KUH1.W3D", "Art\\W3D\\LSFKoreaUH60.W3D"),
    ("Art\\W3D\\SK_KUH1d.W3D", "Art\\W3D\\LSFKoreaUH60d.W3D"),
    ("Art\\W3D\\SK_KUH1k.W3D", "Art\\W3D\\LSFKoreaUH60k.W3D"),
    # LAH: light attack heli class (AH-6), not Lynx.
    ("Art\\W3D\\SK_LAH.W3D", "Art\\W3D\\LSFAH6.W3D"),
    ("Art\\W3D\\SK_LAHd.W3D", "Art\\W3D\\LSFAH6d.W3D"),
    ("Art\\W3D\\SK_LAHk.W3D", "Art\\W3D\\LSFAH6k.W3D"),
]

# SAAB340 W3Ds embed .tga names; donor ships matching .dds (same basename length).
SAAB_TEX_FIX = (
    (b"Saab340.tga", b"Saab340.dds"),
    (b"Saab340_d.tga", b"Saab340_d.dds"),
    (b"LakeduskMetal.tga", b"LakeduskMetal.dds"),
    (b"coplight.tga", b"coplight.dds"),
)

# Existing JP/SK objects whose Draw currently points at a generic/wrong mesh.
EXISTING_MODEL_MAP = {
    "JapanJetF15J": {
        "LSFUSAF15C": "LSFJPF15J",
        "LSFUSAF15Cd": "LSFJPF15Jd",
        "LSFUSAF15Ck": "LSFJPF15Jk",
    },
    "SouthKoreaJetF15KSlam": {
        "LSFUSAF15E": "LSFF15K",
        "LSFUSAF15ED": "LSFF15Kd",
        "LSFUSAF15EK": "LSFF15Kd",
    },
    "SouthKoreaJetF4E": {
        "JPF4": "LSFKoreaF4",
        "JPF4D": "LSFKoreaF4d",
        "JPF4K": "LSFKoreaF4k",
    },
    "SouthKoreaJetF5E": {
        "AVHawk_P": "LSFKoreaF5",
        "AVHawk_D1": "LSFKoreaF5k",
        "AVHawk_D": "LSFKoreaF5d",
    },
    "SouthKoreaJetT50": {
        "AVHawk_P": "LSFT50d",
        "AVHawk_D": "LSFT50k",
        "AVHawk": "LSFT50",
    },
    "SouthKoreaJetUH60P": {
        "US_UH60": "LSFKoreaUH60",
    },
}

BONE_MISSILEA = {"SouthKoreaJetF4E", "SouthKoreaJetF5E"}

JAPAN_FIGHTER_YES = {
    "JapanJetF35A",
    "JapanJetF35B",
    "JapanJetF15J",
    "JapanJetF15DJ",
    "JapanJetF2A",
    "JapanJetF2B",
    "JapanJetF2Kai",
    "JapanJetF4EJKai",
    "JapanJetX2Shinshin",
    "JapanJetFX",
}
JAPAN_SUPPORT_YES = {"JapanJetC130H", "JapanUAVRQ4"}
SK_FIGHTER_YES = {
    "SouthKoreaJetF35A",
    "SouthKoreaJetKF21",
    "SouthKoreaJetF15KSlam",
    "SouthKoreaJetF16C",
    "SouthKoreaJetF16D",
    "SouthKoreaJetFA50",
    "SouthKoreaJetT50",
    "SouthKoreaJetF4E",
    "SouthKoreaJetF5E",
    "SouthKoreaJetKF21Blk2",
    "SouthKoreaJetKF16",
}
SK_SUPPORT_YES = {
    "SouthKoreaJetAH64E",
    "SouthKoreaJetCH47",
    "SouthKoreaJetUH60P",
    "SouthKoreaJetE737",
    "SouthKoreaJetC130H",
}

JAPAN_AIRFIELD = """
CommandSet Japan_AirfieldCommandSet
  1 = Command_ConstructJapanJetF35A
  2 = Command_ConstructJapanJetF35B
  3 = Command_ConstructJapanJetF15J
  4 = Command_ConstructJapanJetF15DJ
  5 = Command_ConstructJapanJetF2A
  6 = Command_ConstructJapanJetF2B
  7 = Command_ConstructJapanJetF2Kai
  8 = Command_ConstructJapanJetF4EJKai
  9 = Command_ConstructJapanJetX2Shinshin
  10 = Command_ConstructJapanJetF16
  11 = Command_ConstructJapanJetFA18
  12 = Command_ConstructJapanJetFX
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

JAPAN_HEAVY = """
CommandSet Japan_HeavyAirBaseCommandSet
  1 = Command_ConstructJapanJetE767
  2 = Command_ConstructJapanJetE2D
  3 = Command_ConstructJapanJetC2
  4 = Command_ConstructJapanJetC130H
  5 = Command_ConstructJapanUAVRQ4
  6 = Command_ConstructJapanHelicopterAH64D
  7 = Command_ConstructJapanHelicopterUH60J
  8 = Command_ConstructJapanHelicopterCH47J
  9 = Command_ConstructJapanJetV22
  10 = Command_UpgradeJapan_AircraftWeapons
  11 = Command_UpgradeJapan_AircraftCountermeasures
  12 = Command_UpgradeJapan_F35Integration
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SK_AIRFIELD = """
CommandSet SouthKorea_AirfieldCommandSet
  1 = Command_ConstructSouthKoreaJetF35A
  2 = Command_ConstructSouthKoreaJetF35B
  3 = Command_ConstructSouthKoreaJetKF21
  4 = Command_ConstructSouthKoreaJetF15KSlam
  5 = Command_ConstructSouthKoreaJetF16C
  6 = Command_ConstructSouthKoreaJetF16D
  7 = Command_ConstructSouthKoreaJetFA50
  8 = Command_ConstructSouthKoreaJetFA50Blk20
  9 = Command_ConstructSouthKoreaJetT50
  10 = Command_ConstructSouthKoreaJetF4E
  11 = Command_ConstructSouthKoreaJetF5E
  12 = Command_ConstructSouthKoreaJetKF21Blk2
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SK_HEAVY = """
CommandSet SouthKorea_HeavyAirBaseCommandSet
  1 = Command_ConstructSouthKoreaJetE737
  2 = Command_ConstructSouthKoreaJetRC800
  3 = Command_ConstructSouthKoreaJetC130H
  4 = Command_ConstructSouthKoreaJetCN235
  5 = Command_ConstructSouthKoreaUAVRQ4
  6 = Command_ConstructSouthKoreaJetAH64E
  7 = Command_ConstructSouthKoreaJetUH60P
  8 = Command_ConstructSouthKoreaHelicopterKUH1
  9 = Command_ConstructSouthKoreaJetCH47
  10 = Command_ConstructSouthKoreaHelicopterLAH
  11 = Command_UpgradeSouthKorea_AircraftWeapons
  12 = Command_UpgradeSouthKorea_AircraftCountermeasures
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

BUTTONS = [
    ("Command_ConstructJapanJetF35A", "JapanJetF35A", "SPEC_JapanJetF35A", "F-35A Lightning II"),
    ("Command_ConstructJapanJetF35B", "JapanJetF35B", "SPEC_JapanJetF35B", "F-35B Lightning II"),
    ("Command_ConstructJapanJetF15J", "JapanJetF15J", "SPEC_JapanF15J", "F-15J Eagle"),
    ("Command_ConstructJapanJetF15DJ", "JapanJetF15DJ", "SPEC_JapanJetF15DJ", "F-15DJ Eagle"),
    ("Command_ConstructJapanJetF2A", "JapanJetF2A", "SPEC_JapanF2A", "Mitsubishi F-2A"),
    ("Command_ConstructJapanJetF2B", "JapanJetF2B", "SPEC_JapanF2B", "Mitsubishi F-2B"),
    ("Command_ConstructJapanJetF2Kai", "JapanJetF2Kai", "SPEC_JapanF2Kai", "F-2 Anti-Ship"),
    ("Command_ConstructJapanJetF4EJKai", "JapanJetF4EJKai", "SPEC_JapanF4EJKai", "F-4EJ Kai"),
    ("Command_ConstructJapanJetX2Shinshin", "JapanJetX2Shinshin", "SPEC_JapanX2Shinshin", "X-2 Shinshin"),
    ("Command_ConstructJapanJetF16", "JapanJetF16", "SPEC_SouthKoreaJetF16C", "F-16 Japan"),
    ("Command_ConstructJapanJetFA18", "JapanJetFA18", "SPEC_JapanJetFX", "F/A-18 Japan"),
    ("Command_ConstructJapanJetFX", "JapanJetFX", "SPEC_JapanJetFX", "Future Fighter FX"),
    ("Command_ConstructJapanJetE767", "JapanJetE767", "E2avionHE", "E-767 AWACS"),
    ("Command_ConstructJapanJetE2D", "AmericaJetE2Visual", "E2avionHE", "E-2D Hawkeye"),
    ("Command_ConstructJapanJetC2", "JapanJetC2", "SPEC_JapanC130H", "Kawasaki C-2"),
    ("Command_ConstructJapanJetC130H", "JapanJetC130H", "SPEC_JapanC130H", "C-130 Hercules"),
    ("Command_ConstructJapanUAVRQ4", "JapanUAVRQ4", "SPEC_JapanRQ4", "RQ-4 Global Hawk"),
    ("Command_ConstructJapanHelicopterAH64D", "JapanHelicopterAH64D", "Nat_ah64e", "AH-64D Apache"),
    ("Command_ConstructJapanHelicopterUH60J", "JapanHelicopterUH60J", "SSChinookUnload", "UH-60J Black Hawk"),
    ("Command_ConstructJapanHelicopterCH47J", "JapanHelicopterCH47J", "SSChinookUnload", "CH-47J Chinook"),
    ("Command_ConstructJapanJetV22", "AmericaJetV22Visual", "C17GlobalMaster", "V-22 Osprey"),
    ("Command_ConstructSouthKoreaJetF35A", "SouthKoreaJetF35A", "SPEC_SouthKoreaJetF35A", "F-35A Lightning II"),
    ("Command_ConstructSouthKoreaJetF35B", "SouthKoreaJetF35B", "SPEC_SouthKoreaJetF35A", "F-35B Lightning II"),
    ("Command_ConstructSouthKoreaJetKF21", "SouthKoreaJetKF21", "SPEC_SouthKoreaJetKF21", "KF-21 Boramae"),
    ("Command_ConstructSouthKoreaJetF15KSlam", "SouthKoreaJetF15KSlam", "SPEC_SouthKoreaJetF15KSlam", "F-15K Slam Eagle"),
    ("Command_ConstructSouthKoreaJetF16C", "SouthKoreaJetF16C", "SPEC_SouthKoreaJetF16C", "KF-16C"),
    ("Command_ConstructSouthKoreaJetF16D", "SouthKoreaJetF16D", "SPEC_SouthKoreaJetF16D", "KF-16D"),
    ("Command_ConstructSouthKoreaJetFA50", "SouthKoreaJetFA50", "SPEC_SouthKoreaJetFA50", "FA-50 Fighting Eagle"),
    ("Command_ConstructSouthKoreaJetFA50Blk20", "SouthKoreaJetFA50Blk20", "SPEC_SouthKoreaJetFA50", "FA-50 Block 20"),
    ("Command_ConstructSouthKoreaJetT50", "SouthKoreaJetT50", "SPEC_SouthKoreaJetT50", "TA-50"),
    ("Command_ConstructSouthKoreaJetF4E", "SouthKoreaJetF4E", "SPEC_SouthKoreaJetF4E", "F-4E Phantom"),
    ("Command_ConstructSouthKoreaJetF5E", "SouthKoreaJetF5E", "SPEC_SouthKoreaJetF5E", "F-5E Tiger II"),
    ("Command_ConstructSouthKoreaJetKF21Blk2", "SouthKoreaJetKF21Blk2", "SPEC_SouthKoreaJetKF21Blk2", "KF-21 Block II"),
    ("Command_ConstructSouthKoreaJetRC800", "SouthKoreaJetRC800", "E2avionHE", "RC-800 Recon"),
    ("Command_ConstructSouthKoreaJetCN235", "SouthKoreaJetCN235", "SPEC_JapanC130H", "CN-235 Transport"),
    ("Command_ConstructSouthKoreaUAVRQ4", "AmericaUAVGlobalHawk", "SPEC_JapanRQ4", "RQ-4 Global Hawk"),
    ("Command_ConstructSouthKoreaHelicopterKUH1", "SouthKoreaHelicopterKUH1", "SSChinookUnload", "KUH-1 Surion"),
    ("Command_ConstructSouthKoreaHelicopterLAH", "SouthKoreaHelicopterLAH", "Nat_ah64e", "LAH"),
]


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
        extra += b"\x00\x00"
        add_labels += 1
        add_strings += 1
    if add_labels == 0:
        return blob
    out = bytearray(blob)
    struct.pack_into("<I", out, 8, nlabels + add_labels)
    struct.pack_into("<I", out, 12, nstrings + add_strings)
    out += extra
    return bytes(out)


def packed_art_name(rel: str) -> str:
    rel = rel.replace("/", "\\")
    low = rel.lower()
    if low.startswith("art\\w3d\\"):
        return "Art\\W3D\\" + rel.split("\\", 2)[2]
    if low.startswith("art\\textures\\"):
        return "Art\\Textures\\" + rel.split("\\", 2)[2]
    return rel


def remap_models(text: str, mapping: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        old = m.group(2)
        return m.group(1) + mapping.get(old, old)

    text = re.sub(r"(?m)^(\s*Model\s*=\s*)(\S+)", repl, text)
    # Donor UH-60 meshes have no US_UH60.US_UH60 clip.
    text = re.sub(r"(?m)^\s*Animation\s*=\s*US_UH60(?:\.\S+)?\s*\r?\n", "", text)
    text = re.sub(r"(?m)^\s*AnimationMode\s*=\s*LOOP\s*\r?\n", "", text)
    return text


def retarget_f16_draw(text: str, default: str, damaged: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    cond = "DEFAULT"
    for line in lines:
        if re.match(r"^\s*DefaultConditionState\b", line):
            cond = "DEFAULT"
        cm = re.match(r"^\s*ConditionState\s*=\s*(.*)$", line)
        if cm:
            cond = cm.group(1)
        mm = re.match(r"^(\s*Model\s*=\s*)(\S+)", line)
        if mm and re.search(r"US_F16", mm.group(2), re.I):
            new = damaged if ("REALLYDAMAGED" in cond or "RUBBLE" in cond) else default
            line = mm.group(1) + new + line[mm.end() :]
        out.append(line)
    return "".join(out)


def retarget_launch_bones(text: str) -> str:
    text = re.sub(
        r"(?m)^(\s*WeaponLaunchBone\s*=\s*PRIMARY\s+)\S+",
        r"\1MISSILEA01",
        text,
    )
    text = re.sub(
        r"(?m)^(\s*WeaponLaunchBone\s*=\s*SECONDARY\s+)\S+",
        r"\1MISSILEA01",
        text,
    )
    text = re.sub(
        r"(?m)^(\s*WeaponLaunchBone\s*=\s*TERTIARY\s+)\S+",
        r"\1MISSILEA01",
        text,
    )
    return text


def models3(model: str | tuple[str, str, str]) -> tuple[str, str, str]:
    if isinstance(model, tuple):
        return model
    return model, model, model


def fix_buildable_scale(text: str, buildable: str) -> str:
    text = re.sub(
        r"(?m)^(?P<ind>[ \t]*)Buildable[ \t]*=[ \t]*NoScale[ \t]*=[ \t]*(?P<sc>[\d.]+)\s*$",
        rf"\g<ind>Buildable = {buildable}\n\g<ind>Scale = \g<sc>",
        text,
    )
    text = re.sub(
        r"(?m)^(?P<ind>[ \t]*)Buildable[ \t]*=[ \t]*\S+",
        rf"\g<ind>Buildable = {buildable}",
        text,
        count=1,
    )
    if not re.search(r"(?m)^[ \t]*Buildable[ \t]*=", text):
        text = re.sub(
            r"(?m)^(Object\s+\S+[ \t]*\r?\n)",
            rf"\1  Buildable = {buildable}\n",
            text,
            count=1,
        )
    return text


def patch_f35_draw_and_weapons(text: str) -> str:
    # USA V-variant visible donor. JP_F35B is housecolor-only (invisible).
    text = text.replace("ENF35A", "LSFUSAF35A")
    text = re.sub(
        r"(ConditionState\s+=\s+REALLYDAMAGED(?:\s+\S+){0,6}\s+Model\s+=\s+)LSFUSAF35A\b",
        r"\1LSFUSAF35Ad",
        text,
    )
    text = re.sub(
        r"(ConditionState\s+=\s+RUBBLE(?:\s+\S+){0,6}\s+Model\s+=\s+)LSFUSAF35A\b",
        r"\1LSFUSAF35Ak",
        text,
    )
    text = text.replace("PRIMARY   Weapon01", "PRIMARY   MISSILEA01")
    text = text.replace("SECONDARY Weapon02", "SECONDARY MISSILEA01")
    text = text.replace("TERTIARY  Weapon01", "TERTIARY  MISSILEA01")
    return text


def set_f35_weapons(text: str) -> str:
    return re.sub(
        r"(?ms)^  WeaponSet\s*\r?\n.*?^  End\s*$",
        "  WeaponSet\r\n"
        "    Conditions = None\r\n"
        "    Weapon              = PRIMARY    AmericaF35C_AA_AIM120\r\n"
        "    PreferredAgainst    = PRIMARY    AIRCRAFT\r\n"
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\r\n"
        "    Weapon              = SECONDARY  GBU_31V2_JDAM_F35C\r\n"
        "    PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE\r\n"
        "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI\r\n"
        "  End",
        text,
        count=1,
    )


def set_f2kai_antiship(text: str) -> str:
    text = text.replace("Japan_Weapon_AAM5_F2Kai", "Japan_Weapon_ASM2_F2A")
    return text


def arm_japan_rq4(text: str) -> str:
    if "AmericaGlobalHawk_4xAGM" in text:
        return text
    text = text.replace(
        "KindOf                 = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT",
        "KindOf                 = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT",
    )
    text = text.replace(
        "CommandSet              = C17GlobalMasterCommandSet",
        "CommandSet              = GenericTacticalBomberCommandSet",
    )
    insert = (
        "  WeaponSet\n"
        "    Conditions = None\n"
        "    Weapon              = PRIMARY    AmericaGlobalHawk_4xAGM\n"
        "    PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE\n"
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "  End\n"
    )
    text = re.sub(r"(?m)^  ArmorSet\s*$", insert + "  ArmorSet", text, count=1)
    return text


def fighter_ini(
    obj: str,
    side: str,
    portrait: str,
    models: tuple[str, str, str],
    primary: str,
    secondary: str,
    scale: str,
    cost: str,
    time: str,
    bones: tuple[str, str] = ("WeaponA", "WeaponA"),
    display: str | None = None,
) -> str:
    dmg, rub = models[1], models[2]
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  UpgradeCameo1 = Upgrade_AmericaCountermeasures
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {models[0]}
      WeaponLaunchBone = PRIMARY {bones[0]}
      WeaponLaunchBone = SECONDARY {bones[1]}
    End
    ConditionState = JETEXHAUST
      ParticleSysBone = Wingtip01 JetContrail
      ParticleSysBone = Wingtip02 JetContrail
    End
    ConditionState = JETEXHAUST JETAFTERBURNER
      ParticleSysBone = Wingtip01 JetContrail
      ParticleSysBone = Wingtip02 JetContrail
      ParticleSysBone = Engine01 JetLenzflare
    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
      ParticleSysBone = Engine01 JetEngineDamagedSmoke
    End
    ConditionState = REALLYDAMAGED JETEXHAUST
      Model = {dmg}
      ParticleSysBone = Engine01 JetEngineDamagedSmoke
      ParticleSysBone = Wingtip01 JetContrail
      ParticleSysBone = Wingtip02 JetContrail
    End
    ConditionState = RUBBLE
      Model = {rub}
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:{display or obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 720.0
  ShroudClearingRange = 240.0
  WeaponSet
    Conditions = None
    Weapon = PRIMARY {primary}
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY {secondary}
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  BuildCost = {cost}
  BuildTime = {time}
  ExperienceValue = 50 50 100 150
  ExperienceRequired = 0 100 200 400
  IsTrainable = Yes
  CommandSet = F22A_AA_CommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceAttack = RaptorVoiceAttack
  VoiceGuard = RaptorVoiceAirPatrol
  SoundAmbient = RaptorAmbientLoop
  KindOf = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT
  Body = ActiveBody ModuleTag_02
    MaxHealth = 480.0
    InitialHealth = 480.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
    FallHowFast = 110.0%
    FXInitialDeath = FX_RaptorDeathInitial
    OCLInitialDeath = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath = 500
    FXSecondary = FX_JetDeathSecondary
    OCLSecondary = OCL_RaptorDeathSecondary
    FXHitGround = FX_JetDeathHitGround
    OCLHitGround = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround = 200
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp
  End
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 500.0
  End
  Behavior = JetAIUpdate ModuleTag_09ai
    OutOfAmmoDamagePerSecond = 0%
    TakeoffDistForMaxLift = 0%
    TakeoffPause = 500
    MinHeight = 5
    ParkingOffset = 3
    ReturnToBaseIdleTime = 10000
    AutoAcquireEnemiesWhenIdle = Yes
    NeedsRunway = Yes
  End
  Locomotor = SET_NORMAL Snecma_M88_4E
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Geometry = Box
  GeometryIsSmall = Yes
  GeometryMajorRadius = 14.0
  GeometryMinorRadius = 7.0
  GeometryHeight = 5.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def transport_ini(obj: str, side: str, portrait: str, models: tuple[str, str, str], scale: str, cost: str, time: str, geo: tuple[str, str, str]) -> str:
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {models[0]}
    End
    ConditionState = JETEXHAUST
      Model = {models[0]}
    End
    ConditionState = REALLYDAMAGED
      Model = {models[1]}
    End
    ConditionState = RUBBLE
      Model = {models[2]}
    End
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 300.0
  BuildCost = {cost}
  BuildTime = {time}
  IsTrainable = No
  CommandSet = C17GlobalMasterCommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_02
    MaxHealth = 700.0
    InitialHealth = 700.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
    FallHowFast = 110.0%
    FXInitialDeath = FX_RaptorDeathInitial
    OCLInitialDeath = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath = 500
    FXSecondary = FX_JetDeathSecondary
    OCLSecondary = OCL_RaptorDeathSecondary
    FXHitGround = FX_JetDeathHitGround
    OCLHitGround = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround = 200
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp
  End
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 700.0
  End
  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End
  Locomotor = SET_NORMAL D30-F6_JetLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Behavior = TransportContain ModuleTag_Cargo
    Slots = 24
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY VEHICLE
    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE
    ExitDelay = 100
    NumberOfExitPaths = 1
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = {geo[0]}
  GeometryMinorRadius = {geo[1]}
  GeometryHeight = {geo[2]}
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def awacs_ini(obj: str, side: str, portrait: str, model: str, scale: str) -> str:
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {model}
    End
    ConditionState = JETEXHAUST
      Model = {model}
    End
    ConditionState = REALLYDAMAGED
      Model = {model}
    End
    ConditionState = RUBBLE
      Model = {model}
    End
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 900.0
  ShroudClearingRange = 900.0
  BuildCost = 8000
  BuildTime = 40.0
  IsTrainable = No
  CommandSet = AmericaE2AWACSCommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT REVEALS_ENEMY_PATHS
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_02
    MaxHealth = 800.0
    InitialHealth = 800.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
    FallHowFast = 110.0%
    FXInitialDeath = FX_RaptorDeathInitial
    OCLInitialDeath = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath = 500
    FXSecondary = FX_JetDeathSecondary
    OCLSecondary = OCL_RaptorDeathSecondary
    FXHitGround = FX_JetDeathHitGround
    OCLHitGround = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround = 200
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp
  End
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 500.0
  End
  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End
  Locomotor = SET_NORMAL F100_PW_229_E2AEW
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Behavior = StealthDetectorUpdate ModuleTag_AWACS
    DetectionRate = 1800
    DetectionRange = 2700
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 30.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 8.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def fix_saab_texture_refs(blob: bytes) -> bytes:
    for old, new in SAAB_TEX_FIX:
        if len(old) != len(new):
            raise SystemExit(f"SAAB tex rename length mismatch {old!r} {new!r}")
        blob = blob.replace(old, new)
    return blob


def recon_ini(obj: str, side: str, portrait: str, model: str | tuple[str, str, str]) -> str:
    alive, dmg, rub = models3(model)
    return f"""Object {obj}
  Buildable = Yes
  Scale = 1.10
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {alive}
    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
    End
    ConditionState = RUBBLE
      Model = {rub}
    End
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 1000.0
  ShroudClearingRange = 1000.0
  BuildCost = 3500
  BuildTime = 22.0
  IsTrainable = No
  CommandSet = GenericCommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT REVEALS_ENEMY_PATHS
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_02
    MaxHealth = 400.0
    InitialHealth = 400.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
    FallHowFast = 110.0%
    FXInitialDeath = FX_RaptorDeathInitial
    OCLInitialDeath = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath = 500
    FXSecondary = FX_JetDeathSecondary
    OCLSecondary = OCL_RaptorDeathSecondary
    FXHitGround = FX_JetDeathHitGround
    OCLHitGround = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround = 200
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp
  End
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 400.0
  End
  Behavior = JetAIUpdate ModuleTag_09
    NeedsRunway = Yes
    AutoAcquireEnemiesWhenIdle = No
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    MinHeight = 1
  End
  Locomotor = SET_NORMAL D30-F6_JetLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Geometry = Box
  GeometryIsSmall = Yes
  GeometryMajorRadius = 16.0
  GeometryMinorRadius = 7.0
  GeometryHeight = 5.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def heli_attack_ini(
    obj: str,
    side: str,
    portrait: str,
    model: str | tuple[str, str, str],
    scale: str,
    primary: str,
    secondary: str,
    tertiary: str | None,
) -> str:
    wpn = (
        f"    Weapon = PRIMARY {primary}\n"
        f"    PreferredAgainst = PRIMARY INFANTRY VEHICLE\n"
        f"    Weapon = SECONDARY {secondary}\n"
        f"    PreferredAgainst = SECONDARY VEHICLE STRUCTURE\n"
    )
    if tertiary:
        wpn += (
            f"    Weapon = TERTIARY {tertiary}\n"
            f"    PreferredAgainst = TERTIARY INFANTRY VEHICLE\n"
        )
    alive, dmg, rub = models3(model)
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {alive}
    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
    End
    ConditionState = RUBBLE
      Model = {rub}
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 350.0
  ShroudClearingRange = 250.0
  WeaponSet
    Conditions = None
{wpn}  End
  ArmorSet
    Conditions = None
    Armor = ChinookArmor
    DamageFX = None
  End
  BuildCost = 1800
  BuildTime = 18.0
  IsTrainable = No
  CommandSet = GenericAttackHelicopterHoverCommandSet
  VoiceSelect = ChinookVoiceSelect
  VoiceMove = ChinookVoiceMove
  VoiceAttack = ChinookVoiceAttack
  KindOf = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD
  Body = ActiveBody ModuleTag_03
    MaxHealth = 500.0
    InitialHealth = 500.0
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = JetAIUpdate ModuleTag_09ai
    MinHeight = 10
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    AutoAcquireEnemiesWhenIdle = Yes
  End
  Locomotor = SET_NORMAL T700_GE_701D_B2
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 50.0
  End
  Behavior = HelicopterSlowDeathBehavior ModuleTag_08
    DestructionDelay = 99999999
    SpiralOrbitTurnRate = 140.0
    SpiralOrbitForwardSpeed = 350.0
    SpiralOrbitForwardSpeedDamping = .9999
    MaxBraking = 190
    SoundDeathLoop = ComancheDamagedLoop
    MinSelfSpin = 100
    MaxSelfSpin = 300
    SelfSpinUpdateDelay = 100
    SelfSpinUpdateAmount = 10
    FallHowFast = 12.0%
    MinBladeFlyOffDelay = 1500
    MaxBladeFlyOffDelay = 1500
    FXHitGround = FX_HelicopterHitGround
    OCLHitGround = OCL_HelicopterHitGround
    FXFinalBlowUp = FX_GroundedHelicopterBlowUp
    OCLFinalBlowUp = OCL_GroundedHelicopterBlowUp
    DelayFromGroundToFinalDeath = 1500
    FinalRubbleObject = ChinookRubbleHull
  End
  Geometry = BOX
  GeometryMajorRadius = 20.0
  GeometryMinorRadius = 6.0
  GeometryHeight = 12.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def heli_transport_ini(
    obj: str,
    side: str,
    portrait: str,
    model: str | tuple[str, str, str],
    scale: str,
    slots: str,
) -> str:
    alive, dmg, rub = models3(model)
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {alive}
    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
    End
    ConditionState = RUBBLE
      Model = {rub}
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 200.0
  ShroudClearingRange = 200.0
  ArmorSet
    Conditions = None
    Armor = ChinookArmor
    DamageFX = None
  End
  BuildCost = 1400
  BuildTime = 16.0
  IsTrainable = No
  CommandSet = AmericaVehicleChinookCommandSet
  VoiceSelect = ChinookVoiceSelect
  VoiceMove = ChinookVoiceMove
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD
  Body = ActiveBody ModuleTag_03
    MaxHealth = 480.0
    InitialHealth = 480.0
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = JetAIUpdate ModuleTag_09ai
    MinHeight = 10
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    AutoAcquireEnemiesWhenIdle = No
  End
  Locomotor = SET_NORMAL ChinookLocomotor
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 50.0
  End
  Behavior = HelicopterSlowDeathBehavior ModuleTag_08
    DestructionDelay = 99999999
    SpiralOrbitTurnRate = 140.0
    SpiralOrbitForwardSpeed = 350.0
    SpiralOrbitForwardSpeedDamping = .9999
    MaxBraking = 190
    SoundDeathLoop = ComancheDamagedLoop
    MinSelfSpin = 100
    MaxSelfSpin = 300
    SelfSpinUpdateDelay = 100
    SelfSpinUpdateAmount = 10
    FallHowFast = 12.0%
    MinBladeFlyOffDelay = 1500
    MaxBladeFlyOffDelay = 1500
    FXHitGround = FX_HelicopterHitGround
    OCLHitGround = OCL_HelicopterHitGround
    FXFinalBlowUp = FX_GroundedHelicopterBlowUp
    OCLFinalBlowUp = OCL_GroundedHelicopterBlowUp
    DelayFromGroundToFinalDeath = 1500
    FinalRubbleObject = ChinookRubbleHull
  End
  Behavior = TransportContain ModuleTag_Cargo
    Slots = {slots}
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY VEHICLE
    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE
    ExitDelay = 100
    NumberOfExitPaths = 1
  End
  Geometry = BOX
  GeometryMajorRadius = 20.0
  GeometryMinorRadius = 6.0
  GeometryHeight = 12.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def new_objects() -> dict[str, str]:
    jp = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce"
    sk = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce"
    return {
        rf"{jp}\JapanJetF16.ini": fighter_ini(
            "JapanJetF16", "Japan", "SPEC_SouthKoreaJetF16C",
            ("US_F16CJ_blk52", "US_F16CJ_blk52", "US_F16CJ_blk52"),
            "AmericaF35C_AA_AIM120", "Japan_Weapon_AAM5_F15JBase",
            "0.88", "2000", "12.0",
        ),
        rf"{jp}\JapanJetFA18.ini": fighter_ini(
            "JapanJetFA18", "Japan", "SPEC_JapanJetFX",
            ("US_FA18E", "US_FA18E", "US_FA18E"),
            "AmericaF35C_AA_AIM120", "GBU_31V2_JDAM_F35C",
            "0.92", "2300", "14.0",
        ),
        rf"{jp}\JapanJetE767.ini": awacs_ini("JapanJetE767", "Japan", "E2avionHE", "JP_E767", "1.28"),
        rf"{jp}\JapanJetC2.ini": transport_ini(
            "JapanJetC2", "Japan", "SPEC_JapanC130H",
            ("JP_C2", "JP_C2d", "JP_C2k"),
            "1.00", "3200", "28.0", ("36.0", "11.0", "10.0"),
        ),
        rf"{jp}\JapanHelicopterAH64D.ini": heli_attack_ini(
            "JapanHelicopterAH64D", "Japan", "Nat_ah64e",
            ("LSFJapanAH64D", "LSFJapanAH64Dd", "LSFJapanAH64Dd"), "0.90",
            "GenericHeliGunnerSight", "8x_MRATGM_AGM114L", "70mm_Hydra_AH64E",
        ),
        rf"{jp}\JapanHelicopterUH60J.ini": heli_transport_ini(
            "JapanHelicopterUH60J", "Japan", "SSChinookUnload",
            ("LSFJPUH60", "LSFJPUH60d", "LSFJPUH60k"), "0.86", "8",
        ),
        rf"{jp}\JapanHelicopterCH47J.ini": heli_transport_ini(
            "JapanHelicopterCH47J", "Japan", "SSChinookUnload", "US_CH47F", "0.88", "16",
        ),
        rf"{sk}\SouthKoreaJetF35B.ini": fighter_ini(
            "SouthKoreaJetF35B", "SouthKorea", "SPEC_SouthKoreaJetF35A",
            ("LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak"),
            "AmericaF35C_AA_AIM120", "GBU_31V2_JDAM_F35C",
            "0.88", "2800", "15.0", ("MISSILEA01", "MISSILEA01"),
        ),
        rf"{sk}\SouthKoreaJetFA50Blk20.ini": fighter_ini(
            "SouthKoreaJetFA50Blk20", "SouthKorea", "SPEC_SouthKoreaJetFA50",
            ("LSFT50", "LSFT50d", "LSFT50k"),
            "SouthKoreaJetFA50_WpnGun", "GBU_31V2_JDAM_F35C",
            "0.84", "1900", "12.0", ("Weapon01", "Weapon01"),
        ),
        rf"{sk}\SouthKoreaJetRC800.ini": recon_ini(
            "SouthKoreaJetRC800", "SouthKorea", "E2avionHE",
            ("SK_RC800", "SK_RC800d", "SK_RC800d"),
        ),
        rf"{sk}\SouthKoreaJetCN235.ini": transport_ini(
            "SouthKoreaJetCN235", "SouthKorea", "SPEC_JapanC130H",
            ("SK_CN235", "SK_CN235d", "SK_CN235k"),
            "0.82", "2400", "24.0", ("28.0", "9.0", "8.0"),
        ),
        rf"{sk}\SouthKoreaHelicopterKUH1.ini": heli_transport_ini(
            "SouthKoreaHelicopterKUH1", "SouthKorea", "SSChinookUnload",
            ("SK_KUH1", "SK_KUH1d", "SK_KUH1k"), "0.88", "10",
        ),
        rf"{sk}\SouthKoreaHelicopterLAH.ini": heli_attack_ini(
            "SouthKoreaHelicopterLAH", "SouthKorea", "Nat_ah64e",
            ("SK_LAH", "SK_LAHd", "SK_LAHk"), "0.78",
            "GenericHeliGunnerSight", "70mm_Hydra_AH64E", None,
        ),
    }


def button_block(name: str, obj: str, image: str, label: str) -> str:
    return (
        f"CommandButton {name}\r\n"
        f"  Command       = UNIT_BUILD\r\n"
        f"  Object        = {obj}\r\n"
        f"  TextLabel     = CONTROLBAR:Construct{name[len('Command_Construct'):] if name.startswith('Command_Construct') else obj}\r\n"
        f"  ButtonImage   = {image}\r\n"
        f"  ButtonBorderType = BUILD\r\n"
        f"  DescriptLabel = CONTROLBAR:ToolTip{name[len('Command_Construct'):] if name.startswith('Command_Construct') else obj}\r\n"
        f"End\r\n"
    )


def patch_commandset(text: str) -> str:
    text = replace_named_block(text, "CommandSet", "Japan_AirfieldCommandSet", JAPAN_AIRFIELD)
    text = replace_named_block(text, "CommandSet", "Japan_HeavyAirBaseCommandSet", JAPAN_HEAVY)
    text = replace_named_block(text, "CommandSet", "SouthKorea_AirfieldCommandSet", SK_AIRFIELD)
    text = replace_named_block(text, "CommandSet", "SouthKorea_HeavyAirBaseCommandSet", SK_HEAVY)
    return text


def patch_commandbutton(text: str) -> str:
    extra = []
    for name, obj, image, _label in BUTTONS:
        if f"CommandButton {name}" not in text:
            extra.append(button_block(name, obj, image, _label))
    if not extra:
        return text
    newline = nl(text)
    return text.rstrip("\r\n") + newline + newline + "".join(
        b.replace("\r\n", newline) for b in extra
    ) + newline


def main() -> int:
    if not SRC_DATA.is_file():
        print("missing source DATA", SRC_DATA, file=sys.stderr)
        return 1
    entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_names = [n for n, _ in entries]
    original_count = len(entries)

    air_dirs = (
        r"data\ini\object\specter\japan self-defense forces\airforce" + "\\",
        r"data\ini\object\specter\republic of korea armed forces\airforce" + "\\",
        r"data\ini\object\specter\south korean armed forces\airforce" + "\\",
    )
    yes = JAPAN_FIGHTER_YES | JAPAN_SUPPORT_YES | SK_FIGHTER_YES | SK_SUPPORT_YES
    for i, (name, blob) in enumerate(entries):
        key = norm(name)
        if not key.endswith(".ini") or not any(key.startswith(d) for d in air_dirs):
            continue
        text = blob.decode("latin1")
        objs = re.findall(r"(?m)^Object\s+(\S+)", text)
        buildable = "No"
        if any(o in yes for o in objs) and not any(
            o.startswith("JapanAir_") or o.startswith("SouthKoreaAir_") or o.startswith("JapanJetSu")
            or o.startswith("JapanJetMig") or o.startswith("JapanJetJ") or o.startswith("JapanHelicopter")
            or o.startswith("SouthKoreaJetSu") or o.startswith("SouthKoreaJetMig") or o.startswith("SouthKoreaJetJ")
            or o.startswith("SouthKoreaHelicopter")
            for o in objs
        ):
            if objs and objs[0] in yes:
                buildable = "Yes"
        # files whose first/real aircraft is a roster unit
        if objs and objs[0] in yes:
            buildable = "Yes"
        text = fix_buildable_scale(text, buildable)
        if objs and objs[0] in ("JapanJetF35A", "JapanJetF35B", "SouthKoreaJetF35A"):
            if objs[0] == "JapanJetF35B":
                text = patch_f35_draw_and_weapons(text)
            text = set_f35_weapons(text)
        if objs and objs[0] == "JapanJetF2Kai":
            text = set_f2kai_antiship(text)
        if objs and objs[0] == "JapanUAVRQ4":
            text = arm_japan_rq4(text)
        if objs and objs[0] in EXISTING_MODEL_MAP:
            text = remap_models(text, EXISTING_MODEL_MAP[objs[0]])
            if objs[0] in BONE_MISSILEA:
                text = retarget_launch_bones(text)
            print("retargeted draw", objs[0])
        if objs and objs[0] == "SouthKoreaJetF16C":
            text = retarget_f16_draw(text, "LSFKF16", "LSFKF16d")
            print("retargeted draw", objs[0])
        if objs and objs[0] == "SouthKoreaJetF16D":
            text = retarget_f16_draw(text, "LSFKF16", "LSFKF16d")
            print("retargeted draw", objs[0])
        entries[i] = (name, text.encode("latin1"))
        print("patched air", name, "Buildable", buildable)

    added = new_objects()
    for packed_name, content in added.items():
        key = norm(packed_name)
        raw = content.replace("\n", "\r\n").encode("latin1")
        if key in index:
            entries[index[key]] = (entries[index[key]][0], raw)
            print("replaced new", packed_name)
        else:
            entries.append((packed_name, raw))
            index[key] = len(entries) - 1
            print("added", packed_name)

    def mut(path: str, fn):
        key = norm(path)
        i = index[key]
        name, blob = entries[i]
        new = fn(blob.decode("latin1"))
        if new == blob.decode("latin1"):
            raise SystemExit(f"no change {path}")
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)

    labels = {}
    for name, obj, _img, pretty in BUTTONS:
        short = name[len("Command_Construct") :]
        labels[f"CONTROLBAR:Construct{short}"] = pretty
        labels[f"CONTROLBAR:ToolTip{short}"] = f"Build {pretty}"
        labels[f"OBJECT:{obj}"] = pretty
    i = index[norm(r"Data\English\generals.csf")]
    name, blob = entries[i]
    new_csf = append_csf_labels(blob, labels)
    entries[i] = (name, new_csf)
    print("patched CSF", len(new_csf) - len(blob))

    if [n for n, _ in entries][:original_count] != original_names:
        raise SystemExit("original entry order changed")
    if len(entries) < original_count:
        raise SystemExit("entry count shrank")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(entries)
    out_big.write_bytes(packed)
    print(
        "wrote",
        out_big,
        "size",
        len(packed),
        "files",
        len(entries),
        "sha",
        hashlib.sha256(packed).hexdigest(),
    )

    if not SRC_ART.is_file():
        print("missing source ART", SRC_ART, file=sys.stderr)
        return 1
    art_entries = parse_big(SRC_ART)
    art_index = {norm(n): i for i, (n, _) in enumerate(art_entries)}
    art_original_names = [n for n, _ in art_entries]
    art_original_count = len(art_entries)
    added_art = 0
    for rel in DONOR_INJECT:
        src = DONOR_ART / rel
        if not src.is_file() or src.stat().st_size == 0:
            print("missing donor ART", src, file=sys.stderr)
            return 1
        packed_name = packed_art_name(rel)
        key = norm(packed_name)
        blob = src.read_bytes()
        if packed_name.lower().endswith(".w3d") and b"Saab340.tga" in blob:
            blob = fix_saab_texture_refs(blob)
        if key in art_index:
            print("art already present", packed_name)
            continue
        art_entries.append((packed_name, blob))
        art_index[key] = len(art_entries) - 1
        added_art += 1
        print("added art", packed_name, len(blob))
    for dest_name, src_name in ART_CLONES:
        src_key = norm(src_name)
        if src_key not in art_index:
            print("missing clone source", src_name, file=sys.stderr)
            return 1
        dest_key = norm(dest_name)
        blob = art_entries[art_index[src_key]][1]
        if dest_name.lower().endswith(".w3d") and b"Saab340.tga" in blob:
            blob = fix_saab_texture_refs(blob)
        if dest_key in art_index:
            print("art clone already present", dest_name)
            continue
        art_entries.append((dest_name, blob))
        art_index[dest_key] = len(art_entries) - 1
        added_art += 1
        print("cloned art", dest_name, "from", src_name, len(blob))
    if [n for n, _ in art_entries][:art_original_count] != art_original_names:
        raise SystemExit("ART original entry order changed")
    out_art = OUT_DIR / "_SPEC_ART_ONE.big"
    packed_art = build_big_ordered(art_entries)
    out_art.write_bytes(packed_art)
    print(
        "wrote",
        out_art,
        "size",
        len(packed_art),
        "files",
        len(art_entries),
        "added",
        added_art,
        "sha",
        hashlib.sha256(packed_art).hexdigest(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
