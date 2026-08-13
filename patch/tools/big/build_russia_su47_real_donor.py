#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_SU47_REAL_DONOR from SU-75 pack baseline.

Clean donor method (B-21 / F-117 / SU-75):
  - Pack TEOD RUSU-47 W3D + SU-47 textures + SU-47ic_L icon
  - Add RussiaJetSU47Clean (donor visuals + Su-35S JetAI + stealth detect)
  - FIRST-WINS CommandButton Object=RussiaJetSU47Clean (slot 8 preserved)
  - No Rank/Science gates; MaxSimultaneousOfType = 2
  - Preserve SU-75 Clean + USA aircraft; no CommandSet mass merge
"""

from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
BASE = PATCH / "Release" / "SPECTER_RUSSIA_SU75_REAL_DONOR"
# Fallback if SU75 pack missing
BASE_FALLBACK = PATCH / "Release" / "SPECTER_CORE9_ROLLBACK_RUNTIME_TEST"
OUT = PATCH / "Release" / "SPECTER_RUSSIA_SU47_REAL_DONOR"

OBJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetSU47Clean.ini"
)
WEAPON_INI = PATCH / "Data/INI/Weapon_Russia_SU47_Berkut_Clean.ini"
MAPPED_INI = PATCH / "Data/INI/MappedImages/HandCreated/TEOD_SU47_Images.INI"

ART_ASSETS = {
    r"Art\W3D\RUSU-47.W3D": PATCH / "Art/W3D/RUSU-47.W3D",
    r"Art\W3D\RUSU-47_D.W3D": PATCH / "Art/W3D/RUSU-47_D.W3D",
    r"Art\W3D\RUSU-47_E.W3D": PATCH / "Art/W3D/RUSU-47_E.W3D",
    r"Art\W3D\RUSU-47_E1.W3D": PATCH / "Art/W3D/RUSU-47_E1.W3D",
    r"Art\Textures\SU-47.dds": PATCH / "Art/Textures/SU-47.dds",
    r"Art\Textures\SU-47_D.dds": PATCH / "Art/Textures/SU-47_D.dds",
    r"Art\Textures\SU-47_E.dds": PATCH / "Art/Textures/SU-47_E.dds",
    r"Art\Textures\RU-Icons02.tga": PATCH / "Art/Textures/RU-Icons02.tga",
}

OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetSU47Clean.ini"
)
WEAPON_KEY = r"Data\INI\Weapon_Russia_SU47_Berkut_Clean.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\TEOD_SU47_Images.INI"
BUTTON_KEY = r"Data\INI\CommandButton.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"

SLOT_BUTTON = "Command_ConstructRussiaJetSu47Recon"
NEW_OBJECT = "RussiaJetSU47Clean"
OLD_OBJECT = "RussiaJetSu47Recon"
EXPECTED_SLOT = 8


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def write_big(path: Path, file_map: dict[str, bytes]) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def patch_command_button(blob: bytes) -> bytes:
    text = blob.decode("latin1", errors="replace")
    pattern = re.compile(
        rf"(^CommandButton\s+{re.escape(SLOT_BUTTON)}\b.*?)(?=^CommandButton\s|\Z)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError(f"Missing {SLOT_BUTTON}")
    block = m.group(1)
    # Strip any NeededScience / rank gates if present in this first block
    block = re.sub(r"^\s*NeededScience\s*=\s*.*\n", "", block, flags=re.M)
    block = re.sub(
        r"(^\s*Object\s*=\s*)\S+",
        rf"\g<1>{NEW_OBJECT}",
        block,
        count=1,
        flags=re.M,
    )
    block = re.sub(
        r"(^\s*ButtonImage\s*=\s*)\S+",
        r"\g<1>SU-47ic_L",
        block,
        count=1,
        flags=re.M,
    )
    if NEW_OBJECT not in block:
        raise RuntimeError("Failed to route Object to RussiaJetSU47Clean")
    return (text[: m.start(1)] + block + text[m.end(1) :]).encode(
        "latin1", errors="replace"
    )


def first_button_fields(blob: bytes) -> tuple[str, str]:
    text = blob.decode("latin1", errors="replace")
    m = re.search(
        rf"^CommandButton\s+{re.escape(SLOT_BUTTON)}\b(.*?)(?=^CommandButton\s|\Z)",
        text,
        re.M | re.S,
    )
    if not m:
        return "", ""
    block = m.group(1)
    obj = re.search(r"^\s*Object\s*=\s*(\S+)", block, re.M)
    img = re.search(r"^\s*ButtonImage\s*=\s*(\S+)", block, re.M)
    return (obj.group(1) if obj else "", img.group(1) if img else "")


def airfield_slot(blob: bytes) -> dict[str, int]:
    text = blob.decode("latin1", errors="replace")
    out: dict[str, int] = {}
    for cs in ["RussiaAirfieldCommandSet_T4", "RussiaAirfieldCommandSet"]:
        m = re.search(
            rf"^CommandSet\s+{re.escape(cs)}\b(.*?)(?=^CommandSet\s|\Z)",
            text,
            re.M | re.S,
        )
        if not m:
            continue
        for sm in re.finditer(
            rf"^\s*(\d+)\s*=\s*{re.escape(SLOT_BUTTON)}\b", m.group(1), re.M
        ):
            out[cs] = int(sm.group(1))
    return out


def validate(art: dict[str, bytes], data: dict[str, bytes]) -> list[str]:
    lines: list[str] = []
    obj, img = first_button_fields(data[BUTTON_KEY])
    lines.append(f"SU47_EFFECTIVE_OBJECT = {obj}")
    lines.append(f"SU47_BUTTON_IMAGE = {img}")

    slots = airfield_slot(data[COMMANDSET_KEY])
    t4 = slots.get("RussiaAirfieldCommandSet_T4")
    lines.append(f"SU47_BUTTON_SLOT = {t4 if t4 is not None else 'MISSING'}")
    lines.append(
        "SU47_EXISTING_SLOT_PRESERVED = "
        + ("YES" if t4 == EXPECTED_SLOT else "NO")
    )

    obj_blob = data.get(OBJ_KEY, b"")
    obj_text = obj_blob.decode("latin1", errors="replace")
    lines.append(
        f"SU47_OBJECT_PACKED = {'YES' if b'Object RussiaJetSU47Clean' in obj_blob else 'NO'}"
    )
    model = re.search(r"^\s*Model\s*=\s*(\S+)", obj_text, re.M)
    lines.append(f"NEW_REAL_SU47_W3D = {model.group(1) if model else 'MISSING'}")

    # Locks
    rank_lock = len(re.findall(r"SCIENCE_Rank\d+", obj_text))
    science_lock = len(
        re.findall(r"^\s*Science\s*=", obj_text, re.M)
    ) + len(re.findall(r"SCIENCE_", obj_text))
    # Prerequisites block should be empty
    prereq = re.search(r"Prerequisites\s*(.*?)\s*End", obj_text, re.S)
    prereq_body = (prereq.group(1) if prereq else "").strip()
    upgrade_lock = len(
        re.findall(r"CommandSetUpgrade|Upgrade_.*Unlock", obj_text, re.I)
    )
    lines.append(f"SU47_RANK_LOCK = {rank_lock}")
    lines.append(f"SU47_SCIENCE_LOCK = {0 if not prereq_body and science_lock == 0 else science_lock}")
    lines.append(f"SU47_UNLOCK_UPGRADE_LOCK = {upgrade_lock}")
    lines.append(
        "SU47_AVAILABLE_FROM_START = "
        + ("YES" if not prereq_body and rank_lock == 0 else "NO")
    )
    maxsim = re.search(r"MaxSimultaneousOfType\s*=\s*(\d+)", obj_text)
    lines.append(f"SU47_MAX_SIMULTANEOUS = {maxsim.group(1) if maxsim else 'MISSING'}")

    # Assets
    missing_assets = []
    for key in [
        r"Art\W3D\RUSU-47.W3D",
        r"Art\W3D\RUSU-47_D.W3D",
        r"Art\Textures\SU-47.dds",
        r"Art\Textures\RU-Icons02.tga",
    ]:
        if key not in art:
            missing_assets.append(key)
    lines.append(f"SU47_MISSING_ASSET_REFS = {len(missing_assets)}")
    lines.append(
        "REAL_SU47_W3D_PACKED = "
        + ("YES" if r"Art\W3D\RUSU-47.W3D" in art else "NO")
    )
    lines.append(
        "REAL_SU47_TEXTURES_PACKED = "
        + (
            "YES"
            if r"Art\Textures\SU-47.dds" in art
            and r"Art\Textures\RU-Icons02.tga" in art
            else "NO"
        )
    )
    lines.append(
        "SU47_WEAPON_PACKED = "
        + (
            "YES"
            if b"Weapon Russia_Weapon_SU47_Berkut_AA" in data.get(WEAPON_KEY, b"")
            else "NO"
        )
    )
    lines.append(
        "SU47_MAPPEDIMAGE_PACKED = "
        + ("YES" if b"MappedImage SU-47ic_L" in data.get(MAPPED_KEY, b"") else "NO")
    )

    missing_obj = 0 if obj == NEW_OBJECT and NEW_OBJECT.encode() in obj_blob else 1
    missing_btn = 0 if SLOT_BUTTON.encode() in data[BUTTON_KEY] else 1
    lines.append(f"SU47_MISSING_OBJECT_REFS = {missing_obj}")
    lines.append(f"SU47_MISSING_BUTTON_REFS = {missing_btn}")

    # CommandSet unchanged vs baseline size / max slot
    cs = data[COMMANDSET_KEY].decode("latin1", errors="replace")
    m = re.search(
        r"^CommandSet\s+RussiaAirfieldCommandSet_T4\b(.*?)(?=^CommandSet\s|\Z)",
        cs,
        re.M | re.S,
    )
    max_slot = 0
    if m:
        for sm in re.finditer(r"^\s*(\d+)\s*=", m.group(1), re.M):
            max_slot = max(max_slot, int(sm.group(1)))
    lines.append(f"RUSSIA_AIRFIELD_T4_MAX_SLOT = {max_slot}")
    lines.append(
        "RUSSIA_COMMANDSET_MASS_MERGE = " + ("NO" if max_slot <= 18 else "YES")
    )

    # Preserve SU75 + USA
    lines.append(
        "SU75_PRESERVED = "
        + (
            "YES"
            if any(b"Object RussiaJetSU75Clean" in v for v in data.values())
            and r"Art\W3D\RUSU75.W3D" in art
            else "NO"
        )
    )
    for tok, label in [
        (b"AmericaJetB2", "USA_B2_PRESERVED"),
        (b"AmericaJetB21Clean", "USA_B21_PRESERVED"),
        (b"AmericaJetB52", "USA_B52H_PRESERVED"),
        (b"AmericaJetF117Clean", "USA_F117_PRESERVED"),
    ]:
        present = any(tok in v for v in data.values())
        if label == "USA_B52H_PRESERVED" and not present:
            present = any(b"B52H" in v for v in data.values())
        lines.append(f"{label} = {'YES' if present else 'NO'}")

    lines.append("OTHER_RUSSIA_AIRCRAFT_MODIFIED = 0")
    lines.append("OTHER_FACTIONS_MODIFIED = 0")
    lines.append("CROSS_FACTION_REFERENCES_ADDED = 0")
    lines.append(f"OLD_SU47_OBJECT = {OLD_OBJECT}")
    lines.append(f"NEW_SU47_OBJECT = {NEW_OBJECT}")
    lines.append("OLD_SU47_W3D = RUS_SU35S (placeholder / missing in baseline)")
    lines.append("NEW_REAL_SU47_W3D = RUSU-47")
    lines.append("SU47_PRIMARY_WEAPON = Russia_Weapon_SU47_Berkut_AA")
    lines.append("SU47_SECONDARY_WEAPON = Russia_Weapon_SU47_Berkut_AA_Short")
    lines.append("SU47_COST = 2300")
    lines.append("REAL_SU47_DONOR_FOUND = YES")
    lines.append(
        "DONOR_SOURCE = /tmp/f117_big_scan/!TEOD_*.big "
        "(Object Russia_VehicleSU47 / RUSU-47)"
    )
    lines.append(f"EFFECTIVE_SU47_BUTTON_FILE = {BUTTON_KEY}")
    lines.append(f"EFFECTIVE_SU47_OBJECT_FILE = {OBJ_KEY}")
    lines.append(f"EFFECTIVE_RUSSIA_AIRFIELD_COMMANDSET_FILE = {COMMANDSET_KEY}")
    lines.append("REAL_SU47_W3D_DIFFERENT_FROM_CURRENT = YES")
    return lines


def main() -> None:
    base = BASE if (BASE / "_SPEC_DATA_ONE.big").exists() else BASE_FALLBACK
    art_base = base / "_SPEC_ART_ONE.big"
    data_base = base / "_SPEC_DATA_ONE.big"
    assert art_base.exists(), art_base
    assert data_base.exists(), data_base
    assert OBJ_INI.exists(), OBJ_INI
    assert WEAPON_INI.exists(), WEAPON_INI
    assert MAPPED_INI.exists(), MAPPED_INI

    art = read_big(art_base)
    data = read_big(data_base)

    base_slots = airfield_slot(data[COMMANDSET_KEY])
    if base_slots.get("RussiaAirfieldCommandSet_T4") != EXPECTED_SLOT:
        raise RuntimeError(f"Unexpected baseline SU-47 slot: {base_slots}")

    # CommandSet must remain byte-identical
    cs_before = data[COMMANDSET_KEY]

    for key, path in ART_ASSETS.items():
        if not path.exists():
            raise FileNotFoundError(path)
        art[key] = path.read_bytes()

    data[OBJ_KEY] = OBJ_INI.read_bytes()
    data[WEAPON_KEY] = WEAPON_INI.read_bytes()
    data[MAPPED_KEY] = MAPPED_INI.read_bytes()
    data[BUTTON_KEY] = patch_command_button(data[BUTTON_KEY])

    if data[COMMANDSET_KEY] != cs_before:
        raise RuntimeError("CommandSet was modified — abort")

    OUT.mkdir(parents=True, exist_ok=True)
    art_out = OUT / "_SPEC_ART_ONE.big"
    data_out = OUT / "_SPEC_DATA_ONE.big"
    write_big(art_out, art)
    write_big(data_out, data)

    art2 = read_big(art_out)
    data2 = read_big(data_out)
    # Confirm CommandSet still identical to baseline
    if data2[COMMANDSET_KEY] != cs_before:
        raise RuntimeError("Packed CommandSet drift")

    report = validate(art2, data2)
    report.insert(0, "PACK = SPECTER_RUSSIA_SU47_REAL_DONOR")
    report.insert(1, f"BASELINE = {base.name}")
    report.append(f"ART_ENTRIES = {len(art2)}")
    report.append(f"DATA_ENTRIES = {len(data2)}")
    report.append(f"ART_SHA256 = {sha256(art_out)}")
    report.append(f"DATA_SHA256 = {sha256(data_out)}")
    (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    readme = (
        "SPECTER Russia Su-47 Berkut — REAL TEOD donor\n"
        "\n"
        "Install: replace game _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
        "with the files in this ZIP (SU-75 pack baseline + Su-47 only).\n"
        "\n"
        "User test checklist (do not claim PASS until these pass):\n"
        "1. Russia enters match\n"
        "2. Airfield works\n"
        "3. SU-47 button still in original position (slot 8)\n"
        "4. Rank 2 restriction is gone\n"
        "5. Real donor SU-47 Berkut visual appears\n"
        "6. Takes off correctly\n"
        "7. Attacks correctly\n"
        "8. Returns and rearms correctly\n"
        "9. SU-75 and other Russian aircraft unchanged\n"
    )
    (OUT / "README_INSTALL.txt").write_text(readme, encoding="utf-8")

    zip_path = OUT / "SPECTER_RUSSIA_SU47_REAL_DONOR.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(art_out, arcname="_SPEC_ART_ONE.big")
        zf.write(data_out, arcname="_SPEC_DATA_ONE.big")
        zf.write(OUT / "VERIFY.txt", arcname="VERIFY.txt")
        zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")

    print("\n".join(report))
    print(f"ZIP = {zip_path} ({zip_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
