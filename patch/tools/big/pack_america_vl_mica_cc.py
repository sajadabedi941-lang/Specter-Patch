#!/usr/bin/env python3
"""Pack America VL MICA onto the live America Command Center CommandSet."""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/agent/repos/Specter-Patch")
SRC_BIG = ROOT / "patch/Release/SPECTER_VIETNAM_VL_MICA_FINAL_BUTTON_FIX/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_VIETNAM_VL_MICA_TEST/_SPEC_ART_TWO.big"
OUT_DIR = ROOT / "patch/Release/SPECTER_AMERICA_VL_MICA_COMMAND_CENTER"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ART = OUT_DIR / "_SPEC_ART_TWO.big"
OUT_ZIP = OUT_DIR / "SPECTER_AMERICA_VL_MICA_COMMAND_CENTER.zip"

USAPAC3_SHA = "296a2c6bfb4191cb9440db6b31e85f4a07401c0a1bdfda599018d55a1034e7a2"
VLMICA_SHA = "310213d0a3d80fe852c6101d5d1dd20d9e8ad3d27bac4c716b880c70abea9ba6"

NEW_FILES = {
    r"Data\INI\Weapon_America_VLMICA.ini": ROOT / "patch/Data/INI/Weapon_America_VLMICA.ini",
    r"Data\INI\Locomotor_America_VLMICA.ini": ROOT / "patch/Data/INI/Locomotor_America_VLMICA.ini",
    r"Data\INI\Armor_America_VLMICA.ini": ROOT / "patch/Data/INI/Armor_America_VLMICA.ini",
    r"Data\INI\SpecialPower_America_VLMICA.ini": ROOT / "patch/Data/INI/SpecialPower_America_VLMICA.ini",
    r"Data\INI\ObjectCreationList_America_VLMICA.ini": ROOT / "patch/Data/INI/ObjectCreationList_America_VLMICA.ini",
    r"Data\INI\CommandSet_America_VLMICA.ini": ROOT / "patch/Data/INI/CommandSet_America_VLMICA.ini",
    r"Data\INI\MappedImages\HandCreated\America_VL_MICA_Images.INI": ROOT
    / "patch/Data/INI/MappedImages/HandCreated/America_VL_MICA_Images.INI",
    r"Data\INI\Object\Specter\United States Of America\AirDefense\America_VL_MICA.ini": ROOT
    / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/America_VL_MICA.ini",
    r"Data\English\FactionExpansion_America_VLMICA_Strings.txt": ROOT
    / "patch/Data/English/FactionExpansion_America_VLMICA_Strings.txt",
}

BUTTON_BLOCK = """
; America VL MICA construct lives in this file so AmericaCommandCenterCommandSet
; slot 2 can resolve it (same pattern as Command_ConstructUSAPAC3).

CommandButton Command_ConstructAmerica_VL_MICA
  Command            = UNIT_BUILD
  Object             = America_VL_MICA
  TextLabel          = CONTROLBAR:ConstructAmerica_VL_MICA
  ButtonImage        = America_VL_MICA
  ButtonBorderType   = BUILD
  DescriptLabel      = CONTROLBAR:ToolTipConstructAmerica_VL_MICA
End

CommandButton Command_America_VL_MICA_Deploy
  Command = SPECIAL_POWER
  SpecialPower = SpecialAbilityAmerica_VL_MICA_Unpack
  Options = NEED_SPECIAL_POWER_SCIENCE OK_FOR_MULTI_SELECT
  TextLabel = CONTROLBAR:America_VL_MICA_Deploy
  ButtonImage = America_VL_MICA_Deploy
  ButtonBorderType = SYSTEM
  DescriptLabel = CONTROLBAR:ToolTipAmerica_VL_MICA_Deploy
End

CommandButton Command_America_VL_MICA_Relocate
  Command = SPECIAL_POWER
  SpecialPower = SpecialAbilityAmerica_VL_MICA_Pack
  Options = NEED_SPECIAL_POWER_SCIENCE OK_FOR_MULTI_SELECT
  TextLabel = CONTROLBAR:America_VL_MICA_Relocate
  ButtonImage = America_VL_MICA_Relocate
  ButtonBorderType = SYSTEM
  DescriptLabel = CONTROLBAR:ToolTipAmerica_VL_MICA_Relocate
End
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries[name] = data[off : off + size]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def patch_commandset(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    line = nl(text)
    pattern = (
        r"(CommandSet AmericaCommandCenterCommandSet"
        + line
        + r"  1  = Command_ConstructAmericaDozer"
        + line
        + r")"
    )
    repl = r"\1  2  = Command_ConstructAmerica_VL_MICA" + line
    new, n = re.subn(pattern, repl, text, count=1)
    if n != 1:
        raise SystemExit("failed to patch AmericaCommandCenterCommandSet slot 2")
    if new.count("CommandSet AmericaCommandCenterCommandSet") != text.count(
        "CommandSet AmericaCommandCenterCommandSet"
    ):
        raise SystemExit("AmericaCommandCenterCommandSet count changed")
    for other in (
        "AirF_AmericaCommandCenterCommandSet",
        "SupW_AmericaCommandCenterCommandSet",
        "Lazr_AmericaCommandCenterCommandSet",
    ):
        if text.split(f"CommandSet {other}")[1].split("End")[0] != new.split(f"CommandSet {other}")[1].split("End")[0]:
            raise SystemExit(f"{other} was modified")
    return new.encode("latin1")


def patch_commandbutton(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    line = nl(text)
    block = BUTTON_BLOCK.replace("\n", line).strip(line) + line
    if "Command_ConstructAmerica_VL_MICA" in text:
        raise SystemExit("construct button already present")
    return (text.rstrip("\x00") + line + block).encode("latin1")


def main() -> int:
    entries = read_big(SRC_BIG)
    by_key = {key(n): n for n in entries}

    cs_name = by_key[key(r"Data\INI\CommandSet.ini")]
    cb_name = by_key[key(r"Data\INI\CommandButton.ini")]
    entries[cs_name] = patch_commandset(entries[cs_name])
    entries[cb_name] = patch_commandbutton(entries[cb_name])

    for big_path, src in NEW_FILES.items():
        blob = src.read_bytes()
        k = key(big_path)
        if k in by_key:
            entries[by_key[k]] = blob
        else:
            entries[big_path] = blob

    def blob_endswith(suffix: str) -> bytes:
        for n, b in entries.items():
            if key(n).endswith(suffix):
                return b
        raise SystemExit(f"missing {suffix}")

    usapac3 = blob_endswith(r"airdefense\usapac3.ini")
    vlmica = blob_endswith("vietnam_vl_mica.ini")
    if sha256(usapac3) != USAPAC3_SHA:
        raise SystemExit("USAPAC3.ini changed")
    if sha256(vlmica) != VLMICA_SHA:
        raise SystemExit("Vietnam_VL_MICA.ini changed")

    cs = entries[cs_name].decode("latin1")
    m = re.search(
        r"CommandSet AmericaCommandCenterCommandSet\s*\r?\n(?:.*\r?\n)*?End", cs
    )
    if not m:
        raise SystemExit("America CC CommandSet missing after pack")
    body = m.group(0)
    for keep in (
        "Command_ConstructAmericaDozer",
        "Command_ConstructUSAPAC3",
        "Command_ConstructAmericaVehicleUH60",
        "Command_ConstructAmericaVehicleM2A3BuskIIIMech",
        "Command_Sell",
        "Command_ConstructAmerica_VL_MICA",
    ):
        if keep not in body:
            raise SystemExit(f"CC set missing {keep}")
    if "  2  = Command_ConstructAmerica_VL_MICA" not in body:
        raise SystemExit("VL MICA not in slot 2")

    cb = entries[cb_name].decode("latin1")
    if "CommandButton Command_ConstructAmerica_VL_MICA" not in cb:
        raise SystemExit("construct button missing from CommandButton.ini")
    if "Object             = America_VL_MICA" not in cb:
        raise SystemExit("construct button Object mismatch")
    if "Command            = UNIT_BUILD" not in cb.split("Command_ConstructAmerica_VL_MICA")[1][:400]:
        raise SystemExit("construct button not UNIT_BUILD")

    obj = blob_endswith(r"airdefense\america_vl_mica.ini").decode("latin1")
    if "Side = Vietnam" in obj:
        raise SystemExit("America object still has Side=Vietnam")
    if "Object Vietnam_" in obj:
        raise SystemExit("America object still references Vietnam objects")
    if "Side = America" not in obj:
        raise SystemExit("America object missing Side=America")
    if "FS_BASE_DEFENSE" in obj.split("Object America_VL_MICA")[1]:
        raise SystemExit("America_VL_MICA still has FS_BASE_DEFENSE")
    if "Object America_VL_MICA" not in obj:
        raise SystemExit("Object America_VL_MICA missing")

    vn_cs = blob_endswith("commandset_vietnam.ini").decode("latin1")
    if "Command_ConstructAmerica_VL_MICA" in vn_cs:
        raise SystemExit("Vietnam CommandSet was modified")

    packed = build_big(entries)
    if packed[:4] != b"BIGF":
        raise SystemExit("not BIGF")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIG.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT_ART)

    readme = """SPECTER America VL MICA — Command Center
=======================================

Adds an independent America VL MICA (New Donor LSFziyuan launcher) to the
main America Command Center. Vietnam files are not modified.
Patriot / USAPAC3 / AirF / Laser / Superweapon Command Centers are not modified.

Live chain (packed DATA)
------------------------
PlayerTemplate FactionAmerica
  StartingBuilding = AmericaCommandCenter
Object AmericaCommandCenter
  CommandSet = AmericaCommandCenterCommandSet
Packed Data\\INI\\CommandSet.ini  (this is the live CC set; overlay CommandSet.ini
  does not contain USAPAC3 and is not the file the game shows)
  1  Dozer
  2  VL MICA          <-- added, previously empty
  6  USAPAC3          unchanged
 12  UH60             unchanged
 13  M2A3             unchanged
 14  Sell             unchanged
Packed Data\\INI\\CommandButton.ini
  Command_ConstructAmerica_VL_MICA  UNIT_BUILD  Object=America_VL_MICA
  (same file as the working Command_ConstructUSAPAC3)

Install
-------
1. Extract into SPECTER FINAL (folder with generals.exe).
2. Replace:
     _SPEC_DATA_ONE.big
     _SPEC_ART_TWO.big
   ART TWO carries LSFziyuan / VlmicaTB / CWCruS300_m from the VL MICA art pack.
3. Do not drop a loose CommandSet.ini or CommandButton.ini over these BIGs.

Use
---
America Command Center slot 2 -> VL MICA. Deploy before it fires.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
"""
    report = """SPECTER America VL MICA Command Center
=====================================
Static validation only. Generals.exe was not launched.

0. Proven live America chain (packed _SPEC_DATA_ONE.big)
-------------------------------------------------------
PlayerTemplate FactionAmerica
  StartingBuilding = AmericaCommandCenter
Object Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\CommandCenter.ini
  Object AmericaCommandCenter
  Side = America
  CommandSet = AmericaCommandCenterCommandSet
CommandSet Data\\INI\\CommandSet.ini  AmericaCommandCenterCommandSet
  slot 6 already UNIT_BUILD Object USAPAC3 (working in SPECTER)
CommandButton Data\\INI\\CommandButton.ini
  Command_ConstructUSAPAC3 UNIT_BUILD Object=USAPAC3

Overlay patch/Data/INI/CommandSet.ini AmericaCommandCenterCommandSet does NOT
contain USAPAC3, so it is not the live bar. This pack edits the packed
CommandSet.ini / CommandButton.ini, the same files USAPAC3 uses.

AirF / SupW / Lazr AmericaCommandCenterCommandSet blocks were not edited.

1. America object
-----------------
Object America_VL_MICA
  Side = America
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT
           CAN_CAST_REFLECTIONS VEHICLE SCORE
  (USAPAC3-style; no FS_BASE_DEFENSE / POWERED)
  Model = LSFziyuan / d / k  Deploy = RiderChangeContain RIDER1/RIDER2
  Weapon = America_VL_MICA_TEL (New Donor CWCruTEL stats)

No Vietnam names, no Side=Vietnam.

2. Command Center button
------------------------
Empty visible slot 2 used. Slots 1/6/12/13/14 untouched.
Command_ConstructAmerica_VL_MICA injected into packed CommandButton.ini.

3. Not changed
--------------
Vietnam_VL_MICA.ini, CommandSet_Vietnam.ini, USAPAC3.ini,
AirF/Lazr/SupW Command Centers, Patriot objects.

4. Hashes
---------
See HASHES.txt. unzip -t. Generals.exe was not run.
"""
    (OUT_DIR / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    (OUT_DIR / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / ".gitignore").write_text("*.big\n*.zip\n", encoding="utf-8")

    art = OUT_ART.read_bytes()
    lines = [
        f"this pack _SPEC_DATA_ONE.big  {len(packed)}  {sha256(packed)}",
        f"this pack _SPEC_ART_TWO.big   {len(art)}  {sha256(art)}  (VL MICA art, unchanged from specter-vietnam-vl-mica-test)",
        f"USAPAC3.ini (unchanged)  {len(usapac3)}  {sha256(usapac3)}",
        f"Vietnam_VL_MICA.ini (unchanged)  {len(vlmica)}  {sha256(vlmica)}",
        f"America_VL_MICA.ini  {len(NEW_FILES[r'Data\\\\INI\\\\Object\\\\Specter\\\\United States Of America\\\\AirDefense\\\\America_VL_MICA.ini'].read_bytes()) if False else len((ROOT / 'patch/Data/INI/Object/Specter/United States Of America/AirDefense/America_VL_MICA.ini').read_bytes())}  {sha256((ROOT / 'patch/Data/INI/Object/Specter/United States Of America/AirDefense/America_VL_MICA.ini').read_bytes())}",
    ]
    (OUT_DIR / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(OUT_BIG, "_SPEC_DATA_ONE.big")
        zf.write(OUT_ART, "_SPEC_ART_TWO.big")
        zf.write(OUT_DIR / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT_DIR / "REPORT.txt", "REPORT.txt")
        zf.write(OUT_DIR / "HASHES.txt", "HASHES.txt")

    zbytes = OUT_ZIP.read_bytes()
    lines.append(
        f"ZIP SPECTER_AMERICA_VL_MICA_COMMAND_CENTER.zip  {len(zbytes)}  {sha256(zbytes)}"
    )
    (OUT_DIR / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "ZIP.sha256").write_text(sha256(zbytes) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        bad = zf.testzip()
        names = zf.namelist()
    if bad:
        raise SystemExit(f"zip corrupt: {bad}")
    print("zip", names)
    print("DATA", len(packed), sha256(packed))
    print("ART", len(art), sha256(art))
    print("ZIP", len(zbytes), sha256(zbytes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
