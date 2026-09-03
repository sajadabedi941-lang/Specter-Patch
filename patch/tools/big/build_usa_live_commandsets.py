#!/usr/bin/env python3
"""Build the LIVE USA CommandSet/CommandButton files the game actually loads.

INIZH.big wins Data\\INI\\CommandSet.ini and CommandButton.ini over
_SPEC_DATA_ONE.big. Unique _USAAirForce CommandSets are unused because
INIZH FactionBuilding.ini owns AmericaCommandCenter / AmericaAirfield.

This writes a patched copy of those INIZH files and packs them into
INIZHZ.big (loads after INIZH.big) plus loose Data\\INI\\ copies.
"""

from __future__ import annotations

import re
import struct
from pathlib import Path

INIZH = Path("/tmp/zh_game/SPECTER FINAL (GeneralsMode.com)/INIZH.big")
OUT_DIR = Path("/workspace/patch/tools/installer/usa_live")
BUTTON_SRC = Path("/workspace/patch/Data/INI/CommandButton_USA_AirForce.ini")

CC_SET = """CommandSet AmericaCommandCenterCommandSet
  1  = Command_ConstructAmericaDozer
  2  = Command_SpectreGunship
  3  = Command_UpgradeAmerica_AirForceBombs
  4  = Command_LeafletDrop
  5  = Command_A10ThunderboltMissileStrike
  6  = Command_Paradrop
  7  = Command_SpyDrone
  8  = Command_EmergencyRepair
  9  = Command_DaisyCutter       ;NOTE THIS GETS UPGRADED BELOW
 10  = Command_SpySatelliteScan
 13 = Command_SetRallyPoint
 14 = Command_Sell
End
"""

AIR_SET = """CommandSet AmericaAirfieldCommandSet
  1 = Command_ConstructAmericaJetRaptor
  2 = Command_ConstructAmericaVehicleComanche
  3 = Command_ConstructAmericaJetAurora
  4 = Command_ConstructAmericaJetStealthFighter
  5 = Command_ConstructAmericaJetF35C_AA
  6 = Command_ConstructAmerica_AuterF22
  7 = Command_UpgradeComancheRocketPods
  8 = Command_UpgradeAmericaLaserMissiles
  9 = Command_UpgradeAmericaCountermeasures
 10 = Command_UpgradeAmericaBunkerBusters
 13 = Command_SetRallyPoint
 14 = Command_Sell
End
"""

HANGAR_SET = """CommandSet America_LargeAirBaseCommandSet
  1  = Command_ConstructAmericaJetRaptor
  2  = Command_ConstructAmericaVehicleComanche
  3  = Command_ConstructAmericaJetAurora
  4  = Command_ConstructAmericaJetA10C
  5  = Command_ConstructAmericaJetF-16C_AG
  6  = Command_ConstructAmericaJetF-15E_AA
  7  = Command_ConstructAmericaJetF-22A_AA
  8  = Command_UpgradeAmericaCountermeasures
  9  = Command_ConstructAmerica_B21A
  10 = Command_ConstructAmericaJetEA18
  11 = Command_ConstructAmericaJetF35C
  12 = Command_ConstructAmericaJetF35C_AA
  13 = Command_ConstructAmericaJetF117
  14 = Command_Sell
End
"""


def read_big_file(path: Path, inner: str) -> bytes:
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    want = inner.replace("/", "\\").lower()
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        if name.replace("/", "\\").lower() == want:
            return data[off : off + size]
    raise FileNotFoundError(inner)


def replace_set(text: str, name: str, new_block: str) -> str:
    pat = re.compile(
        rf"^CommandSet\s+{re.escape(name)}\s*$.*?^End\s*$",
        re.M | re.S,
    )
    if not pat.search(text):
        raise SystemExit(f"missing CommandSet {name} in INIZH CommandSet.ini")
    return pat.sub(new_block.rstrip() + "\r\n", text, count=1)


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    offset = header_size
    index = []
    blobs = []
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


def existing_buttons(text: str) -> set[str]:
    return set(re.findall(r"^CommandButton\s+(\S+)\s*$", text, re.M))


def extra_button_blocks() -> str:
    src = BUTTON_SRC.read_text("latin1")
    # Keep only the buttons the live USA sets need (visible slots).
    keep = {
        "Command_ConstructAmerica_AuterF22",
        "Command_ConstructAmerica_B21A",
        "Command_UpgradeAmerica_AirForceBombs",
        "Command_ConstructAmericaJetF35C_AA",
        "Command_ConstructAmericaJetF35C",
        "Command_ConstructAmericaJetA10C",
        "Command_ConstructAmericaJetF-16C_AG",
        "Command_ConstructAmericaJetF-15E_AA",
        "Command_ConstructAmericaJetF-22A_AA",
        "Command_ConstructAmericaJetEA18",
        "Command_ConstructAmericaJetF117",
    }
    blocks = []
    for m in re.finditer(r"^CommandButton\s+(\S+)\s*$", src, re.M):
        name = m.group(1)
        if name not in keep:
            continue
        rest = src[m.end() :]
        end = re.search(r"^End\s*$", rest, re.M)
        blocks.append(src[m.start() : m.end() + end.end()])
    return "\r\n\r\n".join(blocks) + "\r\n"


def main() -> int:
    cs = read_big_file(INIZH, r"Data\INI\CommandSet.ini").decode("latin1")
    cb = read_big_file(INIZH, r"Data\INI\CommandButton.ini").decode("latin1")

    cs = replace_set(cs, "AmericaCommandCenterCommandSet", CC_SET)
    cs = replace_set(cs, "AmericaAirfieldCommandSet", AIR_SET)
    if re.search(r"^CommandSet\s+America_LargeAirBaseCommandSet\s*$", cs, re.M):
        cs = replace_set(cs, "America_LargeAirBaseCommandSet", HANGAR_SET)
    else:
        cs = cs.rstrip() + "\r\n\r\n" + HANGAR_SET

    extra = extra_button_blocks()
    have = existing_buttons(cb)
    for name in re.findall(r"^CommandButton\s+(\S+)\s*$", extra, re.M):
        if name in have:
            raise SystemExit(f"refusing to redefine INIZH CommandButton {name}")
    cb = cb.rstrip() + "\r\n\r\n; SPECTER USA Air Force live buttons\r\n" + extra

    out_ini = OUT_DIR / "Data" / "INI"
    out_ini.mkdir(parents=True, exist_ok=True)
    cs_path = out_ini / "CommandSet.ini"
    cb_path = out_ini / "CommandButton.ini"
    cs_bytes = cs.encode("latin1", errors="replace")
    cb_bytes = cb.encode("latin1", errors="replace")
    cs_path.write_bytes(cs_bytes)
    cb_path.write_bytes(cb_bytes)

    big = build_big(
        {
            r"Data\INI\CommandSet.ini": cs_bytes,
            r"Data\INI\CommandButton.ini": cb_bytes,
        }
    )
    big_path = OUT_DIR / "INIZHZ.big"
    big_path.write_bytes(big)
    print(f"Wrote {cs_path} ({len(cs_bytes)} bytes)")
    print(f"Wrote {cb_path} ({len(cb_bytes)} bytes)")
    print(f"Wrote {big_path} ({len(big)} bytes)")

    # Sanity: live sets contain required visible buttons
    for label, block, must in [
        ("CC", CC_SET, "Command_UpgradeAmerica_AirForceBombs"),
        ("Airfield", AIR_SET, "Command_ConstructAmericaJetF35C_AA"),
        ("Airfield", AIR_SET, "Command_ConstructAmerica_AuterF22"),
        ("Hangar", HANGAR_SET, "Command_ConstructAmerica_B21A"),
    ]:
        if must not in block:
            raise SystemExit(f"{label} missing {must}")
        slot = re.search(rf"^\s*(\d+)\s*=\s*{re.escape(must)}", block, re.M)
        n = int(slot.group(1))
        if n < 1 or n > 14:
            raise SystemExit(f"{must} is on invisible slot {n}")
        print(f"  {label} slot {n} = {must}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
