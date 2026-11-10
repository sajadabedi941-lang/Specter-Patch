#!/usr/bin/env python3
"""Pack America VL MICA from New Donor FranceVlmica + USAPAC3 THAAD fire only.

Starts from SPECTER_VIETNAM_VL_MICA_FINAL_BUTTON_FIX DATA (last healthy pack),
strips previous Vietnam/America VL MICA, injects the New Donor America clone.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/agent/repos/Specter-Patch")
SRC_BIG = ROOT / "patch/Release/SPECTER_VIETNAM_VL_MICA_FINAL_BUTTON_FIX/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_AMERICA_VL_MICA_TOMAHAWK_FIX/_SPEC_ART_TWO.big"
OUT_DIR = ROOT / "patch/Release/SPECTER_AMERICA_VL_MICA_NEW_DONOR_THAAD"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ART = OUT_DIR / "_SPEC_ART_TWO.big"
OUT_ZIP = OUT_DIR / "SPECTER_AMERICA_VL_MICA_NEW_DONOR_THAAD.zip"

USAPAC3_SHA = "296a2c6bfb4191cb9440db6b31e85f4a07401c0a1bdfda599018d55a1034e7a2"

DATA_ROOT = ROOT / "patch/Data"
ADD_FILES = {
    r"Data\INI\Object\Specter\United States Of America\AirDefense\America_VL_MICA.ini": DATA_ROOT
    / "INI/Object/Specter/United States Of America/AirDefense/America_VL_MICA.ini",
    r"Data\INI\Locomotor_America_VLMICA.ini": DATA_ROOT / "INI/Locomotor_America_VLMICA.ini",
    r"Data\INI\Armor_America_VLMICA.ini": DATA_ROOT / "INI/Armor_America_VLMICA.ini",
    r"Data\INI\SpecialPower_America_VLMICA.ini": DATA_ROOT / "INI/SpecialPower_America_VLMICA.ini",
    r"Data\INI\ObjectCreationList_America_VLMICA.ini": DATA_ROOT
    / "INI/ObjectCreationList_America_VLMICA.ini",
    r"Data\INI\CommandSet_America_VLMICA.ini": DATA_ROOT / "INI/CommandSet_America_VLMICA.ini",
    r"Data\INI\MappedImages\HandCreated\America_VL_MICA_Images.INI": DATA_ROOT
    / "INI/MappedImages/HandCreated/America_VL_MICA_Images.INI",
    r"Data\English\FactionExpansion_America_VLMICA_Strings.txt": DATA_ROOT
    / "English/FactionExpansion_America_VLMICA_Strings.txt",
}

DROP_KEYS = (
    "vietnam_vl_mica",
    "vietnam_vlmica",
    "america_vl_mica",
    "america_vlmica",
)

BUTTONS = DATA_ROOT / "INI/CommandButton_America_VLMICA.ini"
CS_VIETNAM_OVERLAY = DATA_ROOT / "INI/CommandSet_Vietnam.ini"


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


def find_name(entries: dict[str, bytes], suffix: str) -> str:
    s = key(suffix)
    for n in entries:
        if key(n) == s or key(n).endswith("\\" + s) or key(n).endswith(s):
            return n
    raise SystemExit(f"missing {suffix}")


def to_crlf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


def strip_vietnam_append(text: str, marker: str) -> str:
    idx = text.find(marker)
    if idx < 0:
        idx = text.find(marker.replace("SPECTER ", ""))
    if idx < 0:
        return text
    return text[:idx].rstrip() + ("\r\n" if "\r\n" in text else "\n")


def patch_america_cc(cs: str) -> str:
    m = re.search(
        r"(CommandSet AmericaCommandCenterCommandSet\r?\n)(  1  = Command_ConstructAmericaDozer\r?\n)",
        cs,
    )
    if not m:
        raise SystemExit("AmericaCommandCenterCommandSet dozer line missing")
    if "Command_ConstructAmerica_VL_MICA" in m.group(0):
        return cs
    insert = m.group(1) + m.group(2) + "  2  = Command_ConstructAmerica_VL_MICA\r\n"
    return cs[: m.start()] + insert + cs[m.end() :]


def patch_vietnam_cc(cs: str) -> str:
    return re.sub(
        r"(CommandSet Vietnam_CommandCenterCommandSet\r?\n  1  = Command_ConstructVietnam_VT72B\r?\n)  2  = Command_ConstructVietnam_VL_MICA\r?\n",
        r"\1",
        cs,
        count=1,
    )


def main() -> int:
    entries = read_big(SRC_BIG)
    orig_count = len(entries)

    dropped = []
    for n in list(entries):
        kn = key(n)
        if any(tok in kn for tok in DROP_KEYS):
            dropped.append(n)
            del entries[n]

    cs_name = find_name(entries, r"data\ini\commandset.ini")
    cb_name = find_name(entries, r"data\ini\commandbutton.ini")
    loco_name = find_name(entries, r"data\ini\locomotor.ini")
    armor_name = find_name(entries, r"data\ini\armor.ini")
    csvn_name = find_name(entries, r"data\ini\commandset_vietnam.ini")
    usapac3_name = find_name(entries, r"airdefense\usapac3.ini")

    airf = entries[cs_name]
    cs_txt = airf.decode("latin1")
    airf_block = re.search(
        r"(?ms)^CommandSet AirF_AmericaCommandCenterCommandSet\r?\n.*?\r?\nEnd", cs_txt
    ).group(0)
    lazr_block = re.search(
        r"(?ms)^CommandSet Lazr_AmericaCommandCenterCommandSet\r?\n.*?\r?\nEnd", cs_txt
    ).group(0)
    supw_block = re.search(
        r"(?ms)^CommandSet SupW_AmericaCommandCenterCommandSet\r?\n.*?\r?\nEnd", cs_txt
    ).group(0)

    cs_txt = patch_vietnam_cc(cs_txt)
    cs_txt = patch_america_cc(cs_txt)
    if "  2  = Command_ConstructAmerica_VL_MICA" not in cs_txt:
        raise SystemExit("America CC slot 2 not inserted")
    if "Command_ConstructUSAPAC3" not in cs_txt:
        raise SystemExit("USAPAC3 slot lost")
    if "Vietnam_VL_MICA" in cs_txt:
        raise SystemExit("Vietnam_VL_MICA leftover in CommandSet.ini")
    entries[cs_name] = cs_txt.encode("latin1")

    if re.search(
        r"(?ms)^CommandSet AirF_AmericaCommandCenterCommandSet\r?\n.*?\r?\nEnd",
        cs_txt,
    ).group(0) != airf_block:
        raise SystemExit("AirF CC changed")
    if re.search(
        r"(?ms)^CommandSet Lazr_AmericaCommandCenterCommandSet\r?\n.*?\r?\nEnd",
        cs_txt,
    ).group(0) != lazr_block:
        raise SystemExit("Lazr CC changed")
    if re.search(
        r"(?ms)^CommandSet SupW_AmericaCommandCenterCommandSet\r?\n.*?\r?\nEnd",
        cs_txt,
    ).group(0) != supw_block:
        raise SystemExit("SupW CC changed")

    entries[csvn_name] = CS_VIETNAM_OVERLAY.read_bytes()
    if b"Vietnam_VL_MICA" in entries[csvn_name]:
        raise SystemExit("CommandSet_Vietnam.ini still has VL MICA")

    loco_txt = entries[loco_name].decode("latin1")
    loco_txt = strip_vietnam_append(loco_txt, "; SPECTER Vietnam VL MICA")
    if "Vietnam_VL_MICA" in loco_txt:
        raise SystemExit("Vietnam locos remain in Locomotor.ini")
    loco_extra = (DATA_ROOT / "INI/Locomotor_America_VLMICA.ini").read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in loco_txt else "\n"
    entries[loco_name] = (loco_txt.rstrip() + nl + nl + loco_extra.replace("\r\n", "\n").replace("\n", nl)).encode(
        "latin1"
    )

    armor_txt = entries[armor_name].decode("latin1")
    armor_txt = strip_vietnam_append(armor_txt, "; SPECTER Vietnam VL MICA")
    if "Vietnam_VL_MICA" in armor_txt:
        raise SystemExit("Vietnam armor remains in Armor.ini")
    armor_extra = (DATA_ROOT / "INI/Armor_America_VLMICA.ini").read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in armor_txt else "\n"
    entries[armor_name] = (
        armor_txt.rstrip() + nl + nl + armor_extra.replace("\r\n", "\n").replace("\n", nl)
    ).encode("latin1")

    cb = entries[cb_name]
    if b"Command_ConstructAmerica_VL_MICA" in cb:
        raise SystemExit("CommandButton.ini already has America VL MICA")
    buttons = to_crlf(BUTTONS.read_text(encoding="utf-8")).encode("latin1")
    if not cb.endswith(b"\r\n"):
        cb += b"\r\n"
    entries[cb_name] = cb + b"\r\n" + buttons

    for big_path, src in ADD_FILES.items():
        blob = src.read_bytes()
        entries[big_path] = blob

    if sha256(entries[usapac3_name]) != USAPAC3_SHA:
        raise SystemExit("USAPAC3.ini changed")

    obj = entries[
        r"Data\INI\Object\Specter\United States Of America\AirDefense\America_VL_MICA.ini"
    ]
    try:
        obj.decode("ascii")
    except UnicodeDecodeError as e:
        raise SystemExit(f"America_VL_MICA.ini not ASCII: {e}") from e
    otxt = obj.decode("ascii")
    if "DeployStyleAIUpdate" in otxt:
        raise SystemExit("DeployStyleAIUpdate leaked into New Donor object")
    if "America_VL_MICA_FakeRider" in otxt or "GenericFakeRider" in otxt:
        raise SystemExit("Tomahawk FakeRider leftover")
    if "ResetTurretBeforePacking" in otxt:
        raise SystemExit("Tomahawk turret flag leftover")
    if "Weapon = PRIMARY America_VL_MICA_THAAD" not in otxt:
        raise SystemExit("THAAD weapon not on RIDER2 WeaponSet")
    if re.search(r"(?m)^\s*Weapon\s*=\s*PRIMARY\s+CWCruTEL\b", otxt):
        raise SystemExit("New Donor CWCruTEL name leaked (must be unique America THAAD weapon)")
    if "AllowInsideKindOf = INFANTRY" not in otxt:
        raise SystemExit("New Donor AllowInsideKindOf INFANTRY missing")
    if "RiderChangeContain" not in otxt:
        raise SystemExit("RiderChangeContain missing")
    if "OCLSpecialPower" not in otxt:
        raise SystemExit("New Donor OCLSpecialPower deploy missing")
    vehicle_kindof = re.search(
        r"(?ms)^Object America_VL_MICA\s*\n.*?\n  KindOf = ([^\r\n]+)",
        otxt,
    )
    if not vehicle_kindof:
        raise SystemExit("America_VL_MICA KindOf missing")
    if vehicle_kindof.group(1) != (
        "CAN_ATTACK CAN_CAST_REFLECTIONS DONT_AUTO_CRUSH_INFANTRY "
        "HUGE_VEHICLE PRELOAD SCORE SELECTABLE VEHICLE"
    ):
        raise SystemExit(f"America_VL_MICA KindOf mismatch: {vehicle_kindof.group(1)!r}")
    if "FS_BASE_DEFENSE" in vehicle_kindof.group(1) or "POWERED" in vehicle_kindof.group(1):
        raise SystemExit("America_VL_MICA KindOf still has FS_BASE_DEFENSE or POWERED")
    if "InitialPayload = America_VL_MICA_RiderPacked 1" in otxt.replace(";", ""):
        # commented payload in donor must stay commented
        pass
    if re.search(r"(?m)^\s*InitialPayload\s*=", otxt):
        raise SystemExit("InitialPayload is active; New Donor has it commented")
    if not re.search(r"(?m)^\s*Model\s*=\s*PAC-3\s*$", otxt):
        raise SystemExit("THAAD projectile model missing")
    if not re.search(r"(?m)^\s*Model\s*=\s*LSFziyuan\s*$", otxt):
        raise SystemExit("New Donor LSFziyuan missing")
    if "Side = Vietnam" in otxt:
        raise SystemExit("Vietnam side leftover")
    if "Side = America" not in otxt:
        raise SystemExit("America side missing")

    packed_blob = b"".join(entries.values())
    if b"Vietnam_VL_MICA" in packed_blob:
        hits = [n for n, b in entries.items() if b"Vietnam_VL_MICA" in b]
        raise SystemExit(f"Vietnam_VL_MICA leftover in {hits}")
    if b"Command_ConstructVietnam_VL_MICA" in packed_blob:
        raise SystemExit("Vietnam construct button leftover")

    packed = build_big(entries)
    if packed[:4] != b"BIGF":
        raise SystemExit("not BIGF")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIG.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT_ART)

    art = OUT_ART.read_bytes()
    readme = """SPECTER America VL MICA -- New Donor + THAAD fire
=================================================

Rebuilds VL MICA from New Donor Object FranceVlmica.
Previous America/Vietnam VL MICA implementations are removed.

The launcher, riders, deploy/pack, Draw, KindOf, Geometry, and locos
are the New Donor system. Only the fire chain is the live USAPAC3 THAAD
interceptor (weapon / projectile / fuze / MissileAI).

Install
-------
Extract into SPECTER FINAL (generals.exe folder). Replace:
  _SPEC_DATA_ONE.big
  _SPEC_ART_TWO.big

Do not drop a loose CommandSet.ini or CommandButton.ini over these BIGs.

America Command Center slot 2 builds America_VL_MICA (USAPAC3 is slot 6).
Air Force / Laser / Superweapon CCs are unchanged.

Generals.exe was not run on the pack machine.
"""
    report = """SPECTER America VL MICA New Donor rebuild
========================================
Static validation only. Generals.exe was not launched.

Cleanup
-------
Removed previous Vietnam_VL_MICA and America Tomahawk/CC hybrid objects,
weapons, locos, OCLs, specials, mapped images, strings, and CC buttons.

Source
------
New Donor Object FranceVlmica (00PMBeta993 France.ini):
  LSFziyuan Draw / RiderChangeContain / INFANTRY riders / OCLSpecialPower
  KindOf New Donor minus FS_BASE_DEFENSE POWERED (America CC UNIT_BUILD)
  InitialPayload left commented (as in New Donor)
  CWCruS300 locos (unique America names)

Fire chain (THAAD only)
-----------------------
Copied from live packed USAPAC3.ini:
  Weapon America_VL_MICA_THAAD  <- USAPAC3_THAADMissile_ABM
  Object America_VL_MICA_Missile <- USAPAC3_THAAD_ABM_OBJECT
  Weapon America_VL_MICA_ABM_Fuze
  Locomotor THAAD_ABM_MissileLocomotor (shared, not duplicated)
AntiAirborneVehicle=Yes kept from New Donor CWCruTEL so RIDER2
PreferredAgainst AIRCRAFT still has a legal AA shot.

Command Center
--------------
Packed CommandSet.ini AmericaCommandCenterCommandSet slot 2
= Command_ConstructAmerica_VL_MICA (UNIT_BUILD, same file as USAPAC3).
Slot 6 USAPAC3 unchanged. AirF / Lazr / SupW unchanged.
Vietnam CC VL MICA button removed.

Generals.exe was not run.
"""
    (OUT_DIR / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    (OUT_DIR / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / ".gitignore").write_text("*.big\n*.zip\n", encoding="utf-8")

    lines = [
        f"this pack _SPEC_DATA_ONE.big  {len(packed)}  {sha256(packed)}",
        f"this pack _SPEC_ART_TWO.big   {len(art)}  {sha256(art)}",
        f"source DATA files {orig_count} -> {len(entries)} (dropped {len(dropped)})",
        f"USAPAC3.ini  {len(entries[usapac3_name])}  {sha256(entries[usapac3_name])}",
        f"America_VL_MICA.ini  {len(obj)}  {sha256(obj)}",
        f"CommandSet.ini  {len(entries[cs_name])}  {sha256(entries[cs_name])}",
        f"CommandButton.ini  {len(entries[cb_name])}  {sha256(entries[cb_name])}",
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
        f"ZIP SPECTER_AMERICA_VL_MICA_NEW_DONOR_THAAD.zip  {len(zbytes)}  {sha256(zbytes)}"
    )
    (OUT_DIR / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "ZIP.sha256").write_text(sha256(zbytes) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        bad = zf.testzip()
        names = zf.namelist()
    if bad:
        raise SystemExit(f"zip corrupt: {bad}")
    if packed[:4] != b"BIGF":
        raise SystemExit("packed not BIGF")
    print("dropped", dropped)
    print("zip", names)
    print("DATA", len(packed), sha256(packed))
    print("ART", len(art), sha256(art))
    print("ZIP", len(zbytes), sha256(zbytes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
