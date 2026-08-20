#!/usr/bin/env python3
"""Russia Air Force expansion on PR #370 golden baseline.

PHASE ORDER (mandatory):
  1) Import donor ART visual families (already staged under patch/Art)
  2) Apply Russia gameplay systems (B-2A / B-52 / E-3 / E-737 / Chinook reuse)

HARD RULES:
  - Start ONLY from complete #370 runtime BIG pair
  - Expected DATA SHA256 = c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05
  - USA / other factions FROZEN (never modify B-2A, B-52, E-3, E-737, Chinook Objects)
  - Donor ART = YES; donor gameplay DATA = NO
  - Rebuild FULL _SPEC_DATA_ONE.big + _SPEC_ART_ONE.big from complete #370 + Russia delta

This script refuses to pack if #370 BIG pair is missing or hash-mismatched.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
MASTER = PATCH / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_russia_airforce_expansion"
VERIFY = MASTER / "_extract_russia_airforce_expansion_verify"
OUT_DIR = PATCH / "Release/SPECTER_MASTER_RUSSIA_AIRFORCE_EXPANSION"
ZIP_OUT = OUT_DIR / "SPECTER_MASTER_RUSSIA_AIRFORCE_EXPANSION.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_AIRFORCE_EXPANSION_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_AIRFORCE_EXPANSION_HASHES.txt"

EXPECTED_DATA_SHA = "c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05"

AF = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
SP_KEY = r"Data\INI\SpecialPower.ini"
CHINOOK_KEY = r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini"
USA_SYS = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"

OBJ = {
    "tu160": (AF + r"\RussiaJetTU160Clean.ini", "RussiaJetTU160Clean"),
    "tu95": (AF + r"\RussiaJetTu95Visual.ini", "RussiaJetTu95Visual"),
    "an124": (AF + r"\RussiaJetAn124Visual.ini", "RussiaJetAn124Visual"),
    "an225": (AF + r"\RussiaJetAn225Visual.ini", "RussiaJetAn225Visual"),
    "a50": (AF + r"\RussiaJetA50Visual.ini", "RussiaJetA50Visual"),
    "avion": (AF + r"\RussiaJetAvionIL76Visual.ini", "RussiaJetAvionIL76Visual"),
    "cargo": (AF + r"\RussiaJetCargoIL76Visual.ini", "RussiaJetCargoIL76Visual"),
}

ART_FILES = [
    # Tu-160
    "Art/W3D/LSFRussiaTu160.W3D",
    "Art/W3D/LSFRussiaTu160d.W3D",
    "Art/W3D/LSFRussiaTu160k.W3D",
    "Art/Textures/LSFRussiaTU160.dds",
    "Art/Textures/LSFRussiaTU160d.dds",
    "Art/Textures/LSFRussiaTU160k.dds",
    "Art/Textures/TU-160.tga",
    "Art/Textures/TU160TB.tga",
    # Tu-95
    "Art/W3D/CWCruTu95.W3D",
    "Art/W3D/CWCruTu95_d.W3D",
    "Art/W3D/CWCruTu95_k.W3D",
    "Art/Textures/CWCruTu95.dds",
    "Art/Textures/CWCruTu95_d.dds",
    "Art/Textures/CWCruTu95_k.dds",
    "Art/Textures/CWCruTU95.dds",
    "Art/Textures/CWCruTU95_d.dds",
    "Art/Textures/CWCruTU95_k.dds",
    "Art/Textures/CWCgenPropellor.dds",
    "Art/Textures/CWCgenPropellor.tga",
    "Art/Textures/CWCgenReflective.dds",
    "Art/Textures/CWCgenReflective.tga",
    "Art/Textures/Tu95.tga",
    "Art/Textures/Tu95TB.tga",
    # An-124
    "Art/W3D/CWCruAn124.W3D",
    "Art/W3D/CWCruAn124_b.W3D",
    "Art/Textures/CWCruAn124.dds",
    "Art/Textures/CWCruAn124Nav.dds",
    "Art/Textures/CWCruAn124NavL.dds",
    "Art/Textures/CWCruAn124NavR.dds",
    "Art/Textures/AN124.tga",
    "Art/Textures/AN124TB.tga",
    # An-225
    "Art/W3D/A_AN225_100.W3D",
    "Art/W3D/A_E-3_100.W3D",
    "Art/Textures/A_AN225_100.tga",
    "Art/Textures/A_E-3_100.tga",
    "Art/Textures/RussiaAN225.tga",
    "Art/Textures/RussiaAN225TB.tga",
    # A-50
    "Art/W3D/CWCruA50.W3D",
    "Art/Textures/CWCruA50.dds",
    "Art/Textures/CWCruA50.tga",
    "Art/Textures/RussiaA50.tga",
    "Art/Textures/RussiaA50TB.tga",
    # avionIL76
    "Art/W3D/Yier76.W3D",
    "Art/Textures/yier76.tga",
    "Art/Textures/yier76TB.tga",
    "Art/Textures/yujing1.dds",
    "Art/Textures/yujing1.tga",
    # cargoIL76
    "Art/W3D/LSFRussiaYR76.W3D",
    "Art/W3D/LSFRussiaYR76d.W3D",
    "Art/W3D/LSFRussiaYR76k.W3D",
    "Art/Textures/LSFRussiaYR76.tga",
    "Art/Textures/LSFRussiaYR76d.tga",
    "Art/Textures/LSFRussiaYR76k.tga",
    "Art/Textures/CargoIL76Russia.tga",
    "Art/Textures/CargoIL76RussiaTB.tga",
]


def sha256(p: Path | bytes) -> str:
    data = p if isinstance(p, bytes) else Path(p).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def require_baseline() -> tuple[str, str]:
    if not DATA_BIG.is_file() or not ART_BIG.is_file():
        raise SystemExit(
            "BLOCKED: place PR #370 complete runtime at\n"
            f"  {DATA_BIG}\n  {ART_BIG}\n"
            f"Expected DATA SHA256={EXPECTED_DATA_SHA}\n"
            "Gofile https://gofile.io/d/TU7azwGX is premium-locked from this agent."
        )
    dsha = sha256(DATA_BIG)
    asha = sha256(ART_BIG)
    if dsha != EXPECTED_DATA_SHA:
        raise SystemExit(
            f"BLOCKED: DATA SHA mismatch.\n"
            f"  got  {dsha}\n"
            f"  want {EXPECTED_DATA_SHA}\n"
            "Refusing to pack from a non-#370 baseline."
        )
    return dsha, asha


def pack_art_from_patch(art_map: dict[str, bytes]) -> list[str]:
    imported = []
    for rel in ART_FILES:
        src = PATCH / rel
        if not src.is_file():
            raise SystemExit(f"Missing staged donor ART: {src}")
        key = rel.replace("/", "\\")
        art_map[key] = src.read_bytes()
        imported.append(key)
    return imported


def main() -> int:
    dsha, asha = require_baseline()
    print(f"Baseline DATA OK {dsha}")
    print(f"Baseline ART  {asha}")

    data_map = read_big(DATA_BIG)
    art_map = read_big(ART_BIG)

    # Freeze checks — USA objects must exist and will be hashed before/after
    usa_watch = []
    for key in data_map:
        lk = key.lower()
        if any(
            x in lk
            for x in [
                "americajetb2a",
                "americajetb52h",
                "americajete737",
                "americajete3",
                "americavehiclechinook",
                "ch47f.ini",
            ]
        ):
            usa_watch.append(key)
    usa_before = {k: sha256(data_map[k]) for k in usa_watch}

    imported = pack_art_from_patch(art_map)
    print(f"Phase1 ART imported: {len(imported)}")

    # Phase 2 gameplay is applied only after baseline USA chains are traced live
    # from this exact #370 DATA map. Implementation continues once baseline is present.
    # Placeholder: pack ART-only delta is NOT allowed by task (needs full DATA gameplay).
    # For now, stop after ART stage verification scaffolding when gameplay helpers absent.
    raise SystemExit(
        "Baseline #370 verified and ART stage ready, but Phase-2 gameplay packer "
        "requires live trace of AmericaJetB2A / AmericaB52FifteenBombLine / "
        "AmericaJetE3 / AmericaJetE737 / Chinook from this DATA map. "
        "Re-run after Phase-2 implementation is completed against the live #370 tree."
    )


if __name__ == "__main__":
    sys.exit(main())
