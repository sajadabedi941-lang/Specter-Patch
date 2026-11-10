#!/usr/bin/env python3
"""Patch Vietnam Command Center last-win CommandSet into the VL MICA DATA BIG."""
from __future__ import annotations

import hashlib
import struct
import zipfile
from pathlib import Path

ROOT = Path("/agent/repos/Specter-Patch")
SRC_BIG = ROOT / "patch/Release/SPECTER_VIETNAM_VL_MICA_TEST/_SPEC_DATA_ONE.big"
OUT_DIR = ROOT / "patch/Release/SPECTER_VIETNAM_VL_MICA_COMMAND_BUTTON_FIX"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ZIP = OUT_DIR / "SPECTER_VIETNAM_VL_MICA_COMMAND_BUTTON_FIX.zip"

PATCHES = {
    r"Data\INI\CommandSet_Vietnam.ini": ROOT / "patch/Data/INI/CommandSet_Vietnam.ini",
    r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini": ROOT
    / "patch/Data/INI/CommandSet_ZZZZ_CommandCenterMatchStart.ini",
    r"Data\INI\CommandSet_ZZZZ_ZZZZZZVietnam_VL_MICA_CC.ini": ROOT
    / "patch/Data/INI/CommandSet_ZZZZ_ZZZZZZVietnam_VL_MICA_CC.ini",
}

USAPAC3_SHA = "296a2c6bfb4191cb9440db6b31e85f4a07401c0a1bdfda599018d55a1034e7a2"
VLMICA_SHA = "310213d0a3d80fe852c6101d5d1dd20d9e8ad3d27bac4c716b880c70abea9ba6"

KEEP = (
    "Command_ConstructVietnam_Worker",
    "Command_ConstructVietnam_VT72B",
    "Command_ConstructVietnam_IL-76",
    "Command_ConstructVietnam_Alhussaien",
    "Command_SetRallyPoint",
    "Command_Sell",
    "Command_ConstructVietnam_VL_MICA",
)


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
    index = []
    blobs = []
    offset = header_size
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


def require_cc(text: str, label: str) -> None:
    if "CommandSet Vietnam_CommandCenterCommandSet" not in text:
        raise SystemExit(f"{label}: missing Vietnam_CommandCenterCommandSet")
    for token in KEEP:
        if token not in text:
            raise SystemExit(f"{label}: missing {token}")


def main() -> int:
    entries = read_big(SRC_BIG)
    by_key = {key(n): n for n in entries}
    changed = []
    for big_path, src in PATCHES.items():
        blob = src.read_bytes()
        k = key(big_path)
        if k in by_key:
            old_name = by_key[k]
            entries[old_name] = blob
            changed.append(f"replace {old_name}")
        else:
            entries[big_path] = blob
            by_key[k] = big_path
            changed.append(f"add {big_path}")

    obj_usapac3 = vlmica = button = None
    for n, b in entries.items():
        kn = key(n)
        if kn.endswith(r"airdefense\usapac3.ini"):
            obj_usapac3 = b
        elif kn.endswith(r"vietnam_vl_mica.ini"):
            vlmica = b
        elif kn.endswith("commandbutton_vietnam_vlmica.ini"):
            button = b.decode("latin1")
    if obj_usapac3 is None or vlmica is None or button is None:
        raise SystemExit("missing USAPAC3 / Vietnam_VL_MICA / CommandButton")
    if sha256(obj_usapac3) != USAPAC3_SHA:
        raise SystemExit(f"USAPAC3.ini changed: {sha256(obj_usapac3)}")
    if sha256(vlmica) != VLMICA_SHA:
        raise SystemExit(f"Vietnam_VL_MICA.ini changed: {sha256(vlmica)}")
    for token in (
        "Command_ConstructVietnam_VL_MICA",
        "UNIT_BUILD",
        "Object        = Vietnam_VL_MICA",
        "ButtonImage   = Vietnam_VL_MICA",
        "ButtonBorderType = BUILD",
        "DescriptLabel = CONTROLBAR:ToolTipConstructVietnam_VL_MICA",
    ):
        if token not in button:
            raise SystemExit(f"CommandButton missing {token}")

    packed = build_big(entries)
    if packed[:4] != b"BIGF":
        raise SystemExit("packed header not BIGF")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIG.write_bytes(packed)
    roundtrip = read_big(OUT_BIG)
    if packed[:4] != b"BIGF" or struct.unpack(">I", packed[8:12])[0] != len(roundtrip):
        raise SystemExit("BIG header mismatch")

    vn = roundtrip[by_key[key(r"Data\INI\CommandSet_Vietnam.ini")]].decode("latin1")
    match = roundtrip[by_key[key(r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini")]].decode(
        "latin1"
    )
    last = roundtrip[by_key[key(r"Data\INI\CommandSet_ZZZZ_ZZZZZZVietnam_VL_MICA_CC.ini")]].decode(
        "latin1"
    )
    require_cc(vn, "CommandSet_Vietnam.ini")
    require_cc(match, "MatchStart")
    require_cc(last, "ZZZZZZVietnam")
    for other in ("SaudiArabia", "UAE", "Syria", "India", "Pakistan", "SouthAfrica", "Libya"):
        if f"CommandSet {other}_CommandCenterCommandSet" not in match:
            raise SystemExit(f"MatchStart lost {other}")
        if f"Command_Construct{other}_VL_MICA" in match:
            raise SystemExit(f"VL MICA leaked to {other}")

    readme = """SPECTER Vietnam VL MICA — Command Center button fix
====================================================

Baseline: GitHub release specter-vietnam-vl-mica-test
Fixes the missing VL MICA construct button on Vietnam Command Center.

The unit, art, weapons, and Patriot/ABM files are unchanged.
ART TWO is unchanged — keep the VL MICA test ART BIG.

Install
-------
1. Extract this ZIP into SPECTER FINAL (the folder with generals.exe).
2. Replace only:
     _SPEC_DATA_ONE.big
3. Keep the existing _SPEC_ART_TWO.big from specter-vietnam-vl-mica-test.
4. Do not copy loose INI over the BIG. CommandSet last-win is packed.

Build
-----
Vietnam Command Center slot 3 = Command_ConstructVietnam_VL_MICA
Worker / VT72B / IL-76 / Rally / Sell / Alhussaien stay in their slots.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
"""
    report = """SPECTER Vietnam VL MICA Command Center button fix
=================================================
Static validation only. Generals / Zero Hour was not launched.

0. Live Object
--------------
Packed Object:
  Data\\INI\\Object\\Specter\\Vietnam People's Armed Forces\\Buildings\\Vietnam_CommandCenter.ini
  Object Vietnam_CommandCenter
  Side = Vietnam
  CommandSet = Vietnam_CommandCenterCommandSet

1. What the game actually loaded (why the previous pack had no UI)
------------------------------------------------------------------
CommandSet is last-win in this SPECTER tree (see the comment on
CommandSet_ZZZZ_CommandCenterMatchStart.ini).

Alphabetical load of the Vietnam CC name:

  CommandSet.ini
    1 = VT72B
    2 = VL MICA          <-- previous pack patched THIS file
    13 = Rally
    14 = Sell
    (no Worker / IL-76 / Alhussaien)

  CommandSet_Vietnam.ini
    NOT packed in specter-vietnam-vl-mica-test.
    Loose SPECTER overlay Data\\INI\\CommandSet_Vietnam.ini still existed
    from the base install (Worker / VT72B / IL-76 / Rally / Sell /
    Alhussaien, no VL MICA). Same path as a packed file would use, so
    the loose original last-won that filename.

  CommandSet_ZZZZ_CommandCenterMatchStart.ini
    SPECTER last-win for constructible Command Centers.
    Had Saudi / UAE / Syria / India / Pakistan / SouthAfrica / Libya
    with Worker + VT72B + IL-76 + Rally + Sell + Alhussaien.
    Vietnam was omitted, so Vietnam kept falling through to
    CommandSet_Vietnam.ini.

Player-visible buttons therefore came from CommandSet_Vietnam.ini
(the full CC), not from packed CommandSet.ini. Patching CommandSet.ini
never reached the UI. CommandButton_Vietnam_VLMICA.ini was already
valid and packed.

2. Fix (this pack)
------------------
Packed into _SPEC_DATA_ONE.big:

  Data\\INI\\CommandSet_Vietnam.ini
    slot 3 = Command_ConstructVietnam_VL_MICA
    slots 1 Worker, 2 VT72B, 12 IL-76, 13 Rally, 14 Sell, 15 Alhussaien

  Data\\INI\\CommandSet_ZZZZ_CommandCenterMatchStart.ini
    Vietnam_CommandCenterCommandSet added with the same slots.
    Other countries in that file keep the same buttons.

  Data\\INI\\CommandSet_ZZZZ_ZZZZZZVietnam_VL_MICA_CC.ini
    Vietnam-only last-win; loads after MatchStart and after a leftover
    loose CommandSet_Vietnam.ini.

Winning CommandSet after this pack:
  CommandSet_ZZZZ_ZZZZZZVietnam_VL_MICA_CC.ini
  CommandSet Vietnam_CommandCenterCommandSet

3. CommandButton (unchanged, already correct)
---------------------------------------------
CommandButton Command_ConstructVietnam_VL_MICA
  Command          = UNIT_BUILD
  Object           = Vietnam_VL_MICA
  TextLabel        = CONTROLBAR:ConstructVietnam_VL_MICA
  ButtonImage      = Vietnam_VL_MICA
  ButtonBorderType = BUILD
  DescriptLabel    = CONTROLBAR:ToolTipConstructVietnam_VL_MICA

SPECTER construct buttons use TextLabel, not ButtonText
(same as Command_ConstructVietnam_Worker / VT72B). Side = Vietnam.
Prerequisites on Object Vietnam_VL_MICA are empty.

4. Not changed
--------------
Object Vietnam_VL_MICA (sha 310213d0...)
USAPAC3.ini (sha 296a2c6b...)
ART TWO, weapons, damage, deploy, model, texture
Other countries' Command Center slots

5. Hashes
---------
See HASHES.txt. unzip -t on the ZIP. Generals.exe was not run.
"""
    (OUT_DIR / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    (OUT_DIR / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / ".gitignore").write_text("*.big\n*.zip\n", encoding="utf-8")

    cs_vn = PATCHES[r"Data\INI\CommandSet_Vietnam.ini"].read_bytes()
    cs_ms = PATCHES[r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini"].read_bytes()
    cs_last = PATCHES[r"Data\INI\CommandSet_ZZZZ_ZZZZZZVietnam_VL_MICA_CC.ini"].read_bytes()
    lines = [
        "baseline specter-vietnam-vl-mica-test",
        "  _SPEC_DATA_ONE.big  374132752  5bf61295ae2a05b89fbc9b95cc9724c667a342997ff89ebc7c4ca238704b57dd",
        "  _SPEC_ART_TWO.big   318295306  4f5566d7764550c0df84f8d5a685f8fea28af214ab7aa3c8b64ac43f70397303  (unchanged, not in this ZIP)",
        f"this pack _SPEC_DATA_ONE.big  {len(packed)}  {sha256(packed)}",
        f"USAPAC3.ini (unchanged)  {len(obj_usapac3)}  {sha256(obj_usapac3)}",
        f"Vietnam_VL_MICA.ini (unchanged)  {len(vlmica)}  {sha256(vlmica)}",
        f"Data/INI/CommandSet_Vietnam.ini  {len(cs_vn)}  {sha256(cs_vn)}",
        f"Data/INI/CommandSet_ZZZZ_CommandCenterMatchStart.ini  {len(cs_ms)}  {sha256(cs_ms)}",
        f"Data/INI/CommandSet_ZZZZ_ZZZZZZVietnam_VL_MICA_CC.ini  {len(cs_last)}  {sha256(cs_last)}",
    ]
    (OUT_DIR / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(OUT_BIG, "_SPEC_DATA_ONE.big")
        zf.write(OUT_DIR / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT_DIR / "REPORT.txt", "REPORT.txt")
        zf.write(OUT_DIR / "HASHES.txt", "HASHES.txt")

    zip_bytes = OUT_ZIP.read_bytes()
    lines.append(f"ZIP SPECTER_VIETNAM_VL_MICA_COMMAND_BUTTON_FIX.zip  {len(zip_bytes)}  {sha256(zip_bytes)}")
    (OUT_DIR / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "ZIP.sha256").write_text(sha256(zip_bytes) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        bad = zf.testzip()
        names = zf.namelist()
    if bad:
        raise SystemExit(f"zip corrupt: {bad}")

    print("changed:", changed)
    print("zip members:", names)
    print("DATA", len(packed), sha256(packed))
    print("ZIP", len(zip_bytes), sha256(zip_bytes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
