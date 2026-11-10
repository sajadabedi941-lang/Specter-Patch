#!/usr/bin/env python3
"""Pack the live Vietnam CommandSet into DATA BIG + loose ZIP path."""
from __future__ import annotations

import hashlib
import struct
import zipfile
from pathlib import Path

ROOT = Path("/agent/repos/Specter-Patch")
SRC_BIG = ROOT / "patch/Release/SPECTER_VIETNAM_VL_MICA_TEST/_SPEC_DATA_ONE.big"
CS_SRC = ROOT / "patch/Data/INI/CommandSet_Vietnam.ini"
OUT_DIR = ROOT / "patch/Release/SPECTER_VIETNAM_VL_MICA_FINAL_BUTTON_FIX"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ZIP = OUT_DIR / "SPECTER_VIETNAM_VL_MICA_FINAL_BUTTON_FIX.zip"
CS_BIG_PATH = r"Data\INI\CommandSet_Vietnam.ini"

USAPAC3_SHA = "296a2c6bfb4191cb9440db6b31e85f4a07401c0a1bdfda599018d55a1034e7a2"
VLMICA_SHA = "310213d0a3d80fe852c6101d5d1dd20d9e8ad3d27bac4c716b880c70abea9ba6"
KEEP = (
    "Command_ConstructVietnam_Worker",
    "Command_ConstructVietnam_VT72B",
    "Command_ConstructVietnam_VL_MICA",
    "Command_ConstructVietnam_IL-76",
    "Command_SetRallyPoint",
    "Command_Sell",
    "Command_ConstructVietnam_Alhussaien",
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


def block(text: str, name: str) -> str:
    marker = f"CommandSet {name}"
    i = text.find(marker)
    if i < 0:
        raise SystemExit(f"missing {name}")
    j = text.find("\nEnd", i)
    body = text[i : j + 4]
    for token in KEEP:
        if token not in body:
            raise SystemExit(f"{name} missing {token}")
    if "  3 = Command_ConstructVietnam_VL_MICA" not in body:
        raise SystemExit(f"{name} VL MICA not in slot 3")
    return body


def main() -> int:
    cs = CS_SRC.read_bytes()
    text = cs.decode("latin1")
    block(text, "Vietnam_CommandCenterCommandSet")
    block(text, "Vietnam_MilitaryHQCommandSet")

    entries = read_big(SRC_BIG)
    by_key = {key(n): n for n in entries}
    k = key(CS_BIG_PATH)
    if k in by_key:
        entries[by_key[k]] = cs
        action = f"replace {by_key[k]}"
    else:
        entries[CS_BIG_PATH] = cs
        action = f"add {CS_BIG_PATH}"

    # Do not pack the failed ZZZZ last-win files.
    drop = [
        n
        for n in list(entries)
        if key(n).endswith("commandset_zzzz_zzzzzzvietnam_vl_mica_cc.ini")
    ]
    for n in drop:
        del entries[n]

    obj_usapac3 = vlmica = button = cc_obj = None
    for n, b in entries.items():
        kn = key(n)
        if kn.endswith(r"airdefense\usapac3.ini"):
            obj_usapac3 = b
        elif kn.endswith("vietnam_vl_mica.ini"):
            vlmica = b
        elif kn.endswith("commandbutton_vietnam_vlmica.ini"):
            button = b.decode("latin1")
        elif kn.endswith("vietnam_commandcenter.ini"):
            cc_obj = b.decode("latin1")
    if not all((obj_usapac3, vlmica, button, cc_obj)):
        raise SystemExit("missing packed object/button")
    if sha256(obj_usapac3) != USAPAC3_SHA:
        raise SystemExit("USAPAC3.ini changed")
    if sha256(vlmica) != VLMICA_SHA:
        raise SystemExit("Vietnam_VL_MICA.ini changed")
    if "Vietnam_CommandCenterCommandSet" not in cc_obj:
        raise SystemExit("CC object CommandSet mismatch")
    if "Side" not in cc_obj or "Vietnam" not in cc_obj:
        raise SystemExit("CC object Side mismatch")
    for token in (
        "Command_ConstructVietnam_VL_MICA",
        "UNIT_BUILD",
        "Object        = Vietnam_VL_MICA",
        "ButtonImage   = Vietnam_VL_MICA",
        "ButtonBorderType = BUILD",
        "DescriptLabel",
    ):
        if token not in button:
            raise SystemExit(f"CommandButton missing {token}")

    packed = build_big(entries)
    if packed[:4] != b"BIGF":
        raise SystemExit("not BIGF")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "Data" / "INI").mkdir(parents=True, exist_ok=True)
    loose = OUT_DIR / "Data" / "INI" / "CommandSet_Vietnam.ini"
    loose.write_bytes(cs)
    OUT_BIG.write_bytes(packed)

    rt = read_big(OUT_BIG)
    packed_cs = rt[by_key.get(k, CS_BIG_PATH)].decode("latin1")
    block(packed_cs, "Vietnam_CommandCenterCommandSet")
    block(packed_cs, "Vietnam_MilitaryHQCommandSet")
    if any(key(n).endswith("commandset_zzzz_zzzzzzvietnam_vl_mica_cc.ini") for n in rt):
        raise SystemExit("ZZZZ last-win file still packed")

    readme = """SPECTER Vietnam VL MICA — final Command Center button fix
=========================================================

Baseline: specter-vietnam-vl-mica-command-button-fix still had no button.
This pack installs the CommandSet the game actually uses.

Install (both steps)
--------------------
1. Extract this ZIP into SPECTER FINAL (the folder with generals.exe).
2. Replace:
     _SPEC_DATA_ONE.big
3. Copy/overwrite the loose file at this exact path:
     Data\\INI\\CommandSet_Vietnam.ini
   Loose Data\\INI always beats the same path inside a BIG.
   If that loose file is left as the original SPECTER overlay, the
   packed CommandSet never appears.

Keep _SPEC_ART_TWO.big from specter-vietnam-vl-mica-test.

What you should see
-------------------
Vietnam starting Command Center / MilitaryHQ slot 3 = VL MICA.
Worker, VT72B, IL-76, Rally, Sell, Alhussaien stay in their slots.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
"""
    report = """SPECTER Vietnam VL MICA final button fix — load-order diagnosis
==============================================================
Static validation only. Generals.exe was not launched.

0. Live chain (packed DATA, then overlay)
-----------------------------------------
Packed PlayerTemplate.ini:
  PlayerTemplate FactionVietnam
  StartingBuilding = Vietnam_CommandCenter

Packed Object:
  Data\\INI\\Object\\Specter\\Vietnam People's Armed Forces\\Buildings\\Vietnam_CommandCenter.ini
  Object Vietnam_CommandCenter
  Side = Vietnam
  CommandSet = Vietnam_CommandCenterCommandSet

Overlay (unique path, not in INIZH):
  PlayerTemplate_SpecterPatch.ini FactionVietnam
  StartingBuilding = Vietnam_MilitaryHQ
  Object Vietnam_MilitaryHQ
  CommandSet = Vietnam_MilitaryHQCommandSet
  (Vietnam_MilitaryHQ.ini is NOT packed in _SPEC_DATA_ONE.big)

Visible buttons reported in-game:
  Worker, VT72B, IL-76, Rally, Sell, Alhussaien
match BOTH:
  CommandSet_Vietnam.ini  Vietnam_CommandCenterCommandSet  (original, no VL MICA)
  CommandSet_Vietnam.ini  Vietnam_MilitaryHQCommandSet     (slot 3 empty)
and do NOT match packed CommandSet.ini (VT72B + VL MICA + Rally + Sell only).

1. Real load order (SPECTER_BASELINE_REPORT + this tree)
--------------------------------------------------------
Zero Hour loads every *.big in the game folder, case-insensitive
alphabetical order. Later same-path wins. Loose Data\\ beats every BIG.

Typical SPECTER folder:
  _SPEC_ART_ONE.big -> _SPEC_DATA_ONE.big -> ... -> INIZH.big
INIZH.big wins the stock paths:
  Data\\INI\\CommandSet.ini
  Data\\INI\\CommandButton.ini

Consequences proven here:
- Packed CommandSet.ini inside _SPEC_DATA_ONE.big is NOT the live
  Vietnam bar. Pack 1 put VL MICA there; the UI never showed that
  minimal CC (no Worker / IL-76 / Alhussaien).
- CommandSet / CommandButton names must not be redefined in a second
  file (already defined). Unique-path files may ADD new names.
  ZZZZ last-win files that re-declare Vietnam_CommandCenterCommandSet
  are ignored (first definition wins) and are not packed in this ZIP.
- Unique path Data\\INI\\CommandSet_Vietnam.ini is the SPECTER file
  that actually defines Vietnam_CommandCenterCommandSet and
  Vietnam_MilitaryHQCommandSet. INIZH does not own that filename.
- If a loose Data\\INI\\CommandSet_Vietnam.ini exists (SPECTER overlay),
  it replaces the packed file of the same path. Pack 2 packed the
  updated CommandSet_Vietnam.ini and told the user not to copy loose
  INI, so the original loose overlay (no VL MICA) stayed in front.

2. Why the two previous packs had no UI
---------------------------------------
Pack specter-vietnam-vl-mica-test:
  Edited packed CommandSet.ini (INIZH-owned path, wrong/minimal CC)
  and added slot 3 on CommandCenter inside repo CommandSet_Vietnam.ini
  but did not pack that file. README said replace BIGs only.

Pack specter-vietnam-vl-mica-command-button-fix:
  Packed CommandSet_Vietnam.ini (CommandCenter slot 3 only) and added
  ZZZZ last-win files. Loose overlay still beat the packed unique path.
  Vietnam_MilitaryHQCommandSet slot 3 was still empty. ZZZZ redefines
  were not the winning CommandSet.

3. This pack
------------
Single source of truth:
  Data\\INI\\CommandSet_Vietnam.ini

  CommandSet Vietnam_CommandCenterCommandSet
    1 Worker  2 VT72B  3 VL MICA  12 IL-76  13 Rally  14 Sell  15 Alhussaien

  CommandSet Vietnam_MilitaryHQCommandSet
    1 Worker  2 VT72B  3 VL MICA  12 IL-76  13 Rally  14 Sell  15 Alhussaien

Shipped twice so either VFS winner is covered:
  - loose  Data\\INI\\CommandSet_Vietnam.ini   (beats BIG)
  - packed Data\\INI\\CommandSet_Vietnam.ini   inside _SPEC_DATA_ONE.big

No new ZZZZ CommandSet files.

4. CommandButton (unchanged, already packed)
--------------------------------------------
CommandButton Command_ConstructVietnam_VL_MICA
  Command = UNIT_BUILD
  Object = Vietnam_VL_MICA
  TextLabel / ButtonImage / ButtonBorderType=BUILD / DescriptLabel
SPECTER construct buttons use TextLabel, not ButtonText.
Object Vietnam_VL_MICA Side=Vietnam, empty Prerequisites.

5. Not changed
--------------
Object Vietnam_VL_MICA, art, weapons, deploy, Patriot/ABM.
USAPAC3.ini sha 296a2c6b...
ControlBar shows slots 1-14; slot 3 is empty and visible.

6. Hashes
---------
See HASHES.txt. unzip -t. Generals.exe was not run.
"""
    (OUT_DIR / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    (OUT_DIR / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / ".gitignore").write_text("*.big\n*.zip\n", encoding="utf-8")

    lines = [
        "baseline specter-vietnam-vl-mica-test + command-button-fix diagnosis",
        "  previous DATA (button-fix)  374142421  4843a5579a5dfaf2780a73bce0c3bf744b40b9de91fac8faf63456ed965399fd",
        f"this pack _SPEC_DATA_ONE.big  {len(packed)}  {sha256(packed)}",
        f"Data/INI/CommandSet_Vietnam.ini  {len(cs)}  {sha256(cs)}",
        f"USAPAC3.ini (unchanged)  {len(obj_usapac3)}  {sha256(obj_usapac3)}",
        f"Vietnam_VL_MICA.ini (unchanged)  {len(vlmica)}  {sha256(vlmica)}",
    ]
    (OUT_DIR / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(OUT_BIG, "_SPEC_DATA_ONE.big")
        zf.write(loose, r"Data/INI/CommandSet_Vietnam.ini")
        zf.write(OUT_DIR / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT_DIR / "REPORT.txt", "REPORT.txt")
        zf.write(OUT_DIR / "HASHES.txt", "HASHES.txt")

    zbytes = OUT_ZIP.read_bytes()
    lines.append(
        f"ZIP SPECTER_VIETNAM_VL_MICA_FINAL_BUTTON_FIX.zip  {len(zbytes)}  {sha256(zbytes)}"
    )
    (OUT_DIR / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "ZIP.sha256").write_text(sha256(zbytes) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        bad = zf.testzip()
        names = zf.namelist()
    if bad:
        raise SystemExit(f"zip corrupt: {bad}")
    if r"Data/INI/CommandSet_Vietnam.ini" not in names and r"Data\INI\CommandSet_Vietnam.ini" not in names:
        raise SystemExit(f"loose path missing in zip: {names}")

    print("action:", action)
    print("zip:", names)
    print("DATA", len(packed), sha256(packed))
    print("ZIP", len(zbytes), sha256(zbytes))
    print("CS", sha256(cs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
