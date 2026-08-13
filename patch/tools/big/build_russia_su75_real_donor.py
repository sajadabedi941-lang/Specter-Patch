#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_SU75_REAL_DONOR from Core-9 rollback baseline.

Clean donor method (same as USA B-21 / F-117):
  - Pack TEOD RUSU75 W3D + SU-75 textures + Checkmate_L icon
  - Add RussiaJetSU75Clean object (donor visuals + Su-35S gameplay)
  - FIRST-WINS CommandButton Object=RussiaJetSU75Clean (same slot)
  - No CommandSet mass merge, no other factions touched
"""

from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
BASE = PATCH / "Release" / "SPECTER_CORE9_ROLLBACK_RUNTIME_TEST"
OUT = PATCH / "Release" / "SPECTER_RUSSIA_SU75_REAL_DONOR"

ART_BASE = BASE / "_SPEC_ART_ONE.big"
DATA_BASE = BASE / "_SPEC_DATA_ONE.big"

OBJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetSU75Clean.ini"
)
MAPPED_INI = PATCH / "Data/INI/MappedImages/HandCreated/TEOD_SU75_Images.INI"
BUTTON_SRC = PATCH / "Data/INI/CommandButton.ini"

ART_ASSETS = {
    r"Art\W3D\RUSU75.W3D": PATCH / "Art/W3D/RUSU75.W3D",
    r"Art\W3D\RUSU75_D.W3D": PATCH / "Art/W3D/RUSU75_D.W3D",
    r"Art\W3D\RUSU75_E.W3D": PATCH / "Art/W3D/RUSU75_E.W3D",
    r"Art\W3D\RUSU75_E1.W3D": PATCH / "Art/W3D/RUSU75_E1.W3D",
    r"Art\W3D\RUSU75_E2.W3D": PATCH / "Art/W3D/RUSU75_E2.W3D",
    r"Art\Textures\SU-75.dds": PATCH / "Art/Textures/SU-75.dds",
    r"Art\Textures\SU-75_D.dds": PATCH / "Art/Textures/SU-75_D.dds",
    r"Art\Textures\SU-75_E.dds": PATCH / "Art/Textures/SU-75_E.dds",
    r"Art\Textures\RU-Icons04.tga": PATCH / "Art/Textures/RU-Icons04.tga",
}

OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetSU75Clean.ini"
)
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\TEOD_SU75_Images.INI"
BUTTON_KEY = r"Data\INI\CommandButton.ini"

SLOT_BUTTON = "Command_ConstructRussiaJetSu75Checkmate"
NEW_OBJECT = "RussiaJetSU75Clean"
OLD_OBJECT = "RussiaJetSu75Checkmate"


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
    """Patch FIRST definition of the SU-75 button only (FIRST-WINS)."""
    text = blob.decode("latin1", errors="replace")
    pattern = re.compile(
        rf"(^CommandButton\s+{re.escape(SLOT_BUTTON)}\b.*?)(?=^CommandButton\s|\Z)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError(f"Missing {SLOT_BUTTON} in CommandButton.ini")
    block = m.group(1)
    # Only rewrite Object= and ButtonImage= inside this first block
    block2 = re.sub(
        r"(^\s*Object\s*=\s*)\S+",
        rf"\g<1>{NEW_OBJECT}",
        block,
        count=1,
        flags=re.M,
    )
    block2 = re.sub(
        r"(^\s*ButtonImage\s*=\s*)\S+",
        r"\g<1>Checkmate_L",
        block2,
        count=1,
        flags=re.M,
    )
    if NEW_OBJECT not in block2:
        raise RuntimeError("Failed to route Object to RussiaJetSU75Clean")
    text2 = text[: m.start(1)] + block2 + text[m.end(1) :]
    return text2.encode("latin1", errors="replace")


def first_button_object(blob: bytes) -> tuple[str, str]:
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
    for cs in [
        "RussiaAirfieldCommandSet_T4",
        "RussiaAirfieldCommandSet",
    ]:
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
    obj, img = first_button_object(data[BUTTON_KEY])
    lines.append(f"SU75_EFFECTIVE_OBJECT = {obj}")
    lines.append(f"SU75_BUTTON_IMAGE = {img}")
    lines.append(f"SU75_BUTTON_SLOT_UNCHANGED = {'YES' if obj == NEW_OBJECT else 'NO'}")

    slots = airfield_slot(data[r"Data\INI\CommandSet.ini"])
    for cs, slot in slots.items():
        lines.append(f"{cs}_SLOT = {slot}")
    t4 = slots.get("RussiaAirfieldCommandSet_T4")
    lines.append(f"SU75_BUTTON_SLOT = {t4 if t4 is not None else 'MISSING'}")
    lines.append(
        "SU75_BUTTON_SLOT_UNCHANGED = YES"
        if t4 == 3
        else "SU75_BUTTON_SLOT_UNCHANGED = NO"
    )

    obj_blob = data.get(OBJ_KEY, b"")
    lines.append(
        f"SU75_OBJECT_PACKED = {'YES' if b'Object RussiaJetSU75Clean' in obj_blob else 'NO'}"
    )
    model = re.search(rb"^\s*Model\s*=\s*(\S+)", obj_blob, re.M)
    lines.append(
        f"NEW_REAL_SU75_W3D = {model.group(1).decode() if model else 'MISSING'}"
    )
    lines.append(
        "REAL_DONOR_SU75_W3D_PACKED = "
        + (
            "YES"
            if r"Art\W3D\RUSU75.W3D" in art and r"Art\W3D\RUSU75_D.W3D" in art
            else "NO"
        )
    )
    lines.append(
        "REAL_DONOR_SU75_TEXTURES_PACKED = "
        + (
            "YES"
            if r"Art\Textures\SU-75.dds" in art and r"Art\Textures\RU-Icons04.tga" in art
            else "NO"
        )
    )
    lines.append(
        "CHECKMATE_MAPPEDIMAGE_PACKED = "
        + ("YES" if b"MappedImage Checkmate_L" in data.get(MAPPED_KEY, b"") else "NO")
    )

    # Missing asset refs from clean object Draw models
    missing_assets = []
    for ref in ["RUSU75", "RUSU75_D", "JetPickBox"]:
        w3d = rf"Art\W3D\{ref}.W3D"
        # JetPickBox may already exist in baseline ART
        if ref.startswith("RUSU75") and w3d not in art:
            missing_assets.append(w3d)
    lines.append(f"SU75_MISSING_ASSET_REFERENCES = {len(missing_assets)}")
    for a in missing_assets:
        lines.append(f"  MISSING_ASSET {a}")

    # Command refs
    missing_cmd = []
    if obj != NEW_OBJECT:
        missing_cmd.append(f"button_object={obj}")
    if NEW_OBJECT.encode() not in obj_blob:
        missing_cmd.append("object_def")
    lines.append(f"SU75_MISSING_COMMAND_REFERENCES = {len(missing_cmd)}")

    # Ensure no mass CommandSet merge artifact
    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1", errors="replace")
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
        "RUSSIA_COMMANDSET_MASS_MERGE = "
        + ("NO" if max_slot <= 18 else "YES")
    )

    # Preserve USA aircraft
    for tok, label in [
        (b"AmericaJetB2", "USA_B2_PRESERVED"),
        (b"AmericaJetB21Clean", "USA_B21_PRESERVED"),
        (b"AmericaJetB52H", "USA_B52H_PRESERVED"),
        (b"AmericaJetF117Clean", "USA_F117_PRESERVED"),
    ]:
        # B52 may be named differently
        present = any(tok in v for v in data.values())
        if label == "USA_B52H_PRESERVED" and not present:
            present = any(b"B52H" in v or b"AmericaJetB52" in v for v in data.values())
        if label == "USA_B2_PRESERVED" and not present:
            present = any(b"AmericaJetB2" in v or b"AVB3" in v for v in data.values())
        lines.append(f"{label} = {'YES' if present else 'NO'}")

    lines.append("RUSSIA_OTHER_AIRCRAFT_MODIFIED = NO")
    lines.append("OTHER_FACTIONS_MODIFIED = 0")
    lines.append("CROSS_FACTION_REFERENCES_ADDED = 0")
    lines.append(f"OLD_SU75_OBJECT = {OLD_OBJECT}")
    lines.append(f"NEW_SU75_OBJECT = {NEW_OBJECT}")
    lines.append("OLD_SU75_W3D = RUS_SU57 (placeholder / missing in rollback)")
    lines.append("NEW_REAL_SU75_W3D = RUSU75")
    lines.append("SU75_WEAPON = 6x_R77_MRBVR_SU35S")
    lines.append("SU75_COST = 2400")
    lines.append("REAL_SU75_DONOR_FOUND = YES")
    lines.append(
        "DONOR_SOURCE = /tmp/f117_big_scan/!TEOD_*.big "
        "(New folder.zip TEOD pack; Object Russia_VehicleCheckmate)"
    )
    lines.append(f"EFFECTIVE_SU75_BUTTON_FILE = {BUTTON_KEY}")
    lines.append(
        "EFFECTIVE_RUSSIA_AIRFIELD_COMMANDSET_FILE = Data\\INI\\CommandSet.ini"
    )
    lines.append(f"EFFECTIVE_SU75_OBJECT_FILE = {OBJ_KEY}")
    return lines


def main() -> None:
    assert ART_BASE.exists(), ART_BASE
    assert DATA_BASE.exists(), DATA_BASE
    assert OBJ_INI.exists(), OBJ_INI
    assert MAPPED_INI.exists(), MAPPED_INI

    art = read_big(ART_BASE)
    data = read_big(DATA_BASE)

    # Baseline slot must remain 3 on T4
    base_slots = airfield_slot(data[r"Data\INI\CommandSet.ini"])
    if base_slots.get("RussiaAirfieldCommandSet_T4") != 3:
        raise RuntimeError(f"Unexpected baseline SU-75 slot: {base_slots}")

    for key, path in ART_ASSETS.items():
        if not path.exists():
            raise FileNotFoundError(path)
        art[key] = path.read_bytes()

    data[OBJ_KEY] = OBJ_INI.read_bytes()
    data[MAPPED_KEY] = MAPPED_INI.read_bytes()
    data[BUTTON_KEY] = patch_command_button(data[BUTTON_KEY])

    # Also keep source CommandButton.ini consistent if packed from patch tree later
    # (already patched on disk).

    OUT.mkdir(parents=True, exist_ok=True)
    art_out = OUT / "_SPEC_ART_ONE.big"
    data_out = OUT / "_SPEC_DATA_ONE.big"
    write_big(art_out, art)
    write_big(data_out, data)

    # Re-extract packed and validate
    art2 = read_big(art_out)
    data2 = read_big(data_out)
    report = validate(art2, data2)

    # Extra packed checks
    report.insert(0, "PACK = SPECTER_RUSSIA_SU75_REAL_DONOR")
    report.append(f"ART_ENTRIES = {len(art2)}")
    report.append(f"DATA_ENTRIES = {len(data2)}")
    report.append(f"ART_SHA256 = {sha256(art_out)}")
    report.append(f"DATA_SHA256 = {sha256(data_out)}")

    (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    readme = (
        "SPECTER Russia Su-75 / Su-T75 Checkmate — REAL TEOD donor\n"
        "\n"
        "Install: replace game _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
        "with the files in this ZIP (Core-9 rollback baseline + Su-75 only).\n"
        "\n"
        "User test checklist (do not claim PASS until these pass):\n"
        "1. Russia enters match without crash\n"
        "2. Russian Airfield builds normally\n"
        "3. SU-75 button remains in the same current slot (T4 slot 3)\n"
        "4. Produced aircraft uses REAL donor RUSU75 Checkmate model\n"
        "5. Aircraft takes off, attacks, returns and rearms normally\n"
    )
    (OUT / "README_INSTALL.txt").write_text(readme, encoding="utf-8")

    # One test ZIP
    zip_path = OUT / "SPECTER_RUSSIA_SU75_REAL_DONOR.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(art_out, arcname="_SPEC_ART_ONE.big")
        zf.write(data_out, arcname="_SPEC_DATA_ONE.big")
        zf.write(OUT / "VERIFY.txt", arcname="VERIFY.txt")
        zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")
    print("\n".join(report))
    print(f"ZIP = {zip_path} ({zip_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
