#!/usr/bin/env python3
"""Replace America_VL_MICA object with TomahawkTEL rider/Guard pattern. CC slot 2 unchanged."""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/agent/repos/Specter-Patch")
SRC_BIG = ROOT / "patch/Release/SPECTER_AMERICA_VL_MICA_COMMAND_CENTER/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_AMERICA_VL_MICA_COMMAND_CENTER/_SPEC_ART_TWO.big"
OUT_DIR = ROOT / "patch/Release/SPECTER_AMERICA_VL_MICA_TOMAHAWK_FIX"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ART = OUT_DIR / "_SPEC_ART_TWO.big"
OUT_ZIP = OUT_DIR / "SPECTER_AMERICA_VL_MICA_TOMAHAWK_FIX.zip"

USAPAC3_SHA = "296a2c6bfb4191cb9440db6b31e85f4a07401c0a1bdfda599018d55a1034e7a2"
VLMICA_SHA = "310213d0a3d80fe852c6101d5d1dd20d9e8ad3d27bac4c716b880c70abea9ba6"
PREV_CS_SHA = None  # filled from source CommandSet.ini (must be unchanged)

REPLACE = {
    r"Data\INI\Object\Specter\United States Of America\AirDefense\America_VL_MICA.ini": ROOT
    / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/America_VL_MICA.ini",
    r"Data\INI\CommandSet_America_VLMICA.ini": ROOT / "patch/Data/INI/CommandSet_America_VLMICA.ini",
    r"Data\INI\ObjectCreationList_America_VLMICA.ini": ROOT
    / "patch/Data/INI/ObjectCreationList_America_VLMICA.ini",
}


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


def blob_endswith(entries: dict[str, bytes], suffix: str) -> bytes:
    for n, b in entries.items():
        if key(n).endswith(suffix):
            return b
    raise SystemExit(f"missing {suffix}")


def main() -> int:
    entries = read_big(SRC_BIG)
    by_key = {key(n): n for n in entries}
    src_cs = entries[by_key[key(r"Data\INI\CommandSet.ini")]]
    src_cb = entries[by_key[key(r"Data\INI\CommandButton.ini")]]
    cs_sha = sha256(src_cs)
    cb_sha = sha256(src_cb)

    for big_path, src in REPLACE.items():
        blob = src.read_bytes()
        k = key(big_path)
        if k not in by_key:
            raise SystemExit(f"replace target missing: {big_path}")
        entries[by_key[k]] = blob

    if sha256(entries[by_key[key(r"Data\INI\CommandSet.ini")]]) != cs_sha:
        raise SystemExit("CommandSet.ini changed")
    if sha256(entries[by_key[key(r"Data\INI\CommandButton.ini")]]) != cb_sha:
        raise SystemExit("CommandButton.ini changed")

    cs = src_cs.decode("latin1")
    m = re.search(r"CommandSet AmericaCommandCenterCommandSet\s*\r?\n(?:.*\r?\n)*?End", cs)
    if not m or "  2  = Command_ConstructAmerica_VL_MICA" not in m.group(0):
        raise SystemExit("CC slot 2 lost")
    if "Command_ConstructUSAPAC3" not in m.group(0):
        raise SystemExit("USAPAC3 slot lost")
    for other in (
        "AirF_AmericaCommandCenterCommandSet",
        "SupW_AmericaCommandCenterCommandSet",
        "Lazr_AmericaCommandCenterCommandSet",
    ):
        block = re.search(r"CommandSet " + other + r"\s*\r?\n(?:.*\r?\n)*?End", cs).group(0)
        if "VL_MICA" in block:
            raise SystemExit(f"{other} touched")

    usapac3 = blob_endswith(entries, r"airdefense\usapac3.ini")
    vlmica = blob_endswith(entries, "vietnam_vl_mica.ini")
    if sha256(usapac3) != USAPAC3_SHA:
        raise SystemExit("USAPAC3.ini changed")
    if sha256(vlmica) != VLMICA_SHA:
        raise SystemExit("Vietnam_VL_MICA.ini changed")

    obj = blob_endswith(entries, r"airdefense\america_vl_mica.ini").decode("latin1")
    main = obj.split("Object America_VL_MICA")[-1]
    if "Side = Vietnam" in obj:
        raise SystemExit("Vietnam side leftover")
    if "America_VL_MICA_RiderPacked" in obj or "INFANTRY PRELOAD" in obj:
        raise SystemExit("old INFANTRY riders still present")
    if "InitialPayload = America_VL_MICA_FakeRider1 1" not in obj:
        raise SystemExit("InitialPayload missing")
    if "AllowInsideKindOf = PRELOAD" not in obj:
        raise SystemExit("AllowInsideKindOf not PRELOAD")
    if "DeployStyleAIUpdate" not in obj:
        raise SystemExit("DeployStyleAIUpdate missing")
    if "ATTACK_NEEDS_LINE_OF_SIGHT" in main.split("KindOf")[1].split("\n")[0]:
        raise SystemExit("vehicle KindOf still has ATTACK_NEEDS_LINE_OF_SIGHT")
    if "Weapon = PRIMARY None" in obj:
        raise SystemExit("empty PRIMARY None weaponset remains")
    if obj.count("Weapon = PRIMARY America_VL_MICA_TEL") < 3:
        raise SystemExit("TEL weapon not on default+rider weaponsets")
    if "Object America_VL_MICA_FakeRider1" not in obj or "Object America_VL_MICA_FakeRider2" not in obj:
        raise SystemExit("GenericFakeRider objects missing")
    if "OCLSpecialPower" in obj:
        raise SystemExit("old OCLSpecialPower deploy still present")
    if "Geometry = CYLINDER" not in obj:
        raise SystemExit("rider Geometry missing")

    packed = build_big(entries)
    if packed[:4] != b"BIGF":
        raise SystemExit("not BIGF")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIG.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT_ART)

    readme = """SPECTER America VL MICA — TomahawkTEL rider/Guard fix
====================================================

Fixes the PR #768 crash hybrid. America Command Center slot 2 is unchanged.

After build the launcher is packed. Guard unpacks (DeployStyleAIUpdate,
same as America_TomahawkTEL). PRIMARY weapon is America_VL_MICA_TEL.

Install
-------
Extract into SPECTER FINAL (generals.exe folder). Replace:
  _SPEC_DATA_ONE.big
Keep the previous VL MICA _SPEC_ART_TWO.big (this ZIP also includes it).

Do not drop a loose CommandSet.ini or CommandButton.ini over these BIGs.

Generals.exe was not run on the pack machine.
"""
    report = """SPECTER America VL MICA TomahawkTEL crash fix
============================================
Static validation only. Generals.exe was not launched.

Cause (PR #768)
---------------
America_VL_MICA mixed USAPAC3 KindOf (ATTACK_NEEDS_LINE_OF_SIGHT) with
New Donor INFANTRY riders and no InitialPayload.

Fix
---
Object America_VL_MICA only:
  KindOf / DeployStyleAIUpdate from America_TomahawkTEL
  RiderChangeContain InitialPayload + AllowInsideKindOf = PRELOAD
  GenericFakeRider copies with Geometry
  WeaponSet PRIMARY America_VL_MICA_TEL (None/RIDER1/RIDER2)
  LSFziyuan packed/DEPLOYED animations kept

Not changed
-----------
AmericaCommandCenterCommandSet slot 2
CommandButton.ini construct button
USAPAC3.ini
Vietnam files
AirF / Lazr / SupW CommandSets

Generals.exe was not run.
"""
    (OUT_DIR / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    (OUT_DIR / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / ".gitignore").write_text("*.big\n*.zip\n", encoding="utf-8")

    art = OUT_ART.read_bytes()
    obj_src = (
        ROOT
        / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/America_VL_MICA.ini"
    ).read_bytes()
    lines = [
        f"this pack _SPEC_DATA_ONE.big  {len(packed)}  {sha256(packed)}",
        f"this pack _SPEC_ART_TWO.big   {len(art)}  {sha256(art)}  (unchanged art)",
        f"USAPAC3.ini (unchanged)  {len(usapac3)}  {sha256(usapac3)}",
        f"Vietnam_VL_MICA.ini (unchanged)  {len(vlmica)}  {sha256(vlmica)}",
        f"CommandSet.ini (unchanged vs PR768)  {len(src_cs)}  {cs_sha}",
        f"CommandButton.ini (unchanged vs PR768)  {len(src_cb)}  {cb_sha}",
        f"America_VL_MICA.ini  {len(obj_src)}  {sha256(obj_src)}",
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
        f"ZIP SPECTER_AMERICA_VL_MICA_TOMAHAWK_FIX.zip  {len(zbytes)}  {sha256(zbytes)}"
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
    print("CS", cs_sha)
    print("CB", cb_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
