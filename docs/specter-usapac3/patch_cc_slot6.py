#!/usr/bin/env python3
"""Put Command_ConstructUSAPAC3 on live America Command Center slot 6.

Live path (unified DATA + ControlBar first-win CommandSet.ini):
  FactionAmerica.StartingBuilding = AmericaCommandCenter
  Object AmericaCommandCenter.CommandSet = AmericaCommandCenterCommandSet
  Winner = Data\\INI\\CommandSet.ini  (loose first-wins ControlBar; packed DATA
           is the same bytes when the installer copies it)

America_MilitaryHQ is NOT in live DATA. Slot 6 on America_MilitaryHQCommandSet
never drives the Command Center the player opens.

This edits ONLY AmericaCommandCenterCommandSet slot 6 inside packed
CommandSet.ini. Other CC slots, THAAD/Patriot/NASAMS objects, and ART are
untouched.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "docs/specter-usapac3/merged/_SPEC_DATA_ONE.big"
OUT_DIR = ROOT / "docs/specter-usapac3/merged"
CS_PATH = r"Data\INI\CommandSet.ini"

OLD_BLOCK = (
    b"CommandSet AmericaCommandCenterCommandSet\r\n"
    b"  1  = Command_ConstructAmericaDozer\r\n"
    b" 12  = Command_ConstructAmericaVehicleUH60\r\n"
    b" 13  = Command_ConstructAmericaVehicleM2A3BuskIIIMech\r\n"
    b" 14 = Command_Sell\r\n"
    b" 15 = Command_ConstructSpecterAI_CZDropMarker\r\n"
    b" 16 = Command_ConstrucAmericaDronesMq9AI\r\n"
    b" 17 = Command_ConstructAmericaHelicopterCh47F_AI\r\n"
    b" 18 = Command_ConstructAmericaDroneMQ4AI\r\n"
    b"End"
)
NEW_BLOCK = (
    b"CommandSet AmericaCommandCenterCommandSet\r\n"
    b"  1  = Command_ConstructAmericaDozer\r\n"
    b"  6  = Command_ConstructUSAPAC3\r\n"
    b" 12  = Command_ConstructAmericaVehicleUH60\r\n"
    b" 13  = Command_ConstructAmericaVehicleM2A3BuskIIIMech\r\n"
    b" 14 = Command_Sell\r\n"
    b" 15 = Command_ConstructSpecterAI_CZDropMarker\r\n"
    b" 16 = Command_ConstrucAmericaDronesMq9AI\r\n"
    b" 17 = Command_ConstructAmericaHelicopterCh47F_AI\r\n"
    b" 18 = Command_ConstructAmericaDroneMQ4AI\r\n"
    b"End"
)

PROTECTED_OBJECTS = (
    b"Object America_AD_THAAD",
    b"Object America_AD_Patriot",
    b"Object America_AD_NASAMS",
    b"Command_ConstructAmerica_AD_THAAD",
    b"Command_ConstructAmerica_AD_Patriot",
    b"Command_ConstructAmerica_AD_NASAMS",
)


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name.replace("/", "\\"), off, size))
    return data, entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
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
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def slots(block: bytes) -> dict[int, str]:
    out = {}
    for m in re.finditer(rb"(?m)^\s*(\d+)\s*=\s*(\S+)", block):
        out[int(m.group(1))] = m.group(2).decode("ascii")
    return out


def main() -> int:
    if not SRC_DATA.exists():
        fail(f"missing {SRC_DATA}")
    raw, entries = read_big(SRC_DATA)
    file_map = {}
    cs_name = None
    old_cs = None
    for name, off, size in entries:
        blob = raw[off : off + size]
        file_map[name] = blob
        if name.replace("/", "\\").lower() == CS_PATH.lower():
            cs_name = name
            old_cs = blob
    if cs_name is None or old_cs is None:
        fail("packed CommandSet.ini missing")
    n = old_cs.count(OLD_BLOCK)
    if n != 1:
        fail(f"AmericaCommandCenterCommandSet block count={n}")
    if old_cs.count(b"CommandSet AmericaCommandCenterCommandSet\r\n") != 1:
        fail("unexpected extra AmericaCommandCenterCommandSet")
    new_cs = old_cs.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if new_cs == old_cs:
        fail("CommandSet.ini unchanged")
    if len(new_cs) - len(old_cs) != len(NEW_BLOCK) - len(OLD_BLOCK):
        fail("size delta mismatch")
    old_slots = slots(OLD_BLOCK)
    new_slots = slots(NEW_BLOCK)
    if old_slots.get(6):
        fail("slot 6 was already occupied")
    if new_slots.get(6) != "Command_ConstructUSAPAC3":
        fail("slot 6 not USAPAC3")
    for k, v in old_slots.items():
        if new_slots.get(k) != v:
            fail(f"slot {k} mutated {v} -> {new_slots.get(k)}")
    # no other CommandSet mutated: only this blob changes, and only this block
    other = new_cs.replace(NEW_BLOCK, b"", 1)
    other_old = old_cs.replace(OLD_BLOCK, b"", 1)
    if other != other_old:
        fail("CommandSet.ini changed outside AmericaCommandCenterCommandSet")

    file_map[cs_name] = new_cs
    for name, blob in file_map.items():
        if name == cs_name:
            continue
        orig = None
        for n2, off, size in entries:
            if n2 == name:
                orig = raw[off : off + size]
                break
        if orig != blob:
            fail(f"non-CommandSet path mutated: {name}")

    # protected object files still present and unedited
    found_prot = {k: 0 for k in PROTECTED_OBJECTS}
    for name, blob in file_map.items():
        for key in PROTECTED_OBJECTS:
            found_prot[key] += blob.count(key)
    for key, count in found_prot.items():
        print(f"protected {key.decode()} count={count}")

    out_data = build_big(file_map)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    out_cs = OUT_DIR / "CommandSet.ini"
    out_big.write_bytes(out_data)
    out_cs.write_bytes(new_cs)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(
        f"{sha256(out_data)}  _SPEC_DATA_ONE.big\n", encoding="ascii"
    )
    (OUT_DIR / "CommandSet.ini.sha256").write_text(
        f"{sha256(new_cs)}  CommandSet.ini\n", encoding="ascii"
    )

    # re-read and confirm
    raw2, entries2 = read_big(out_big)
    amap = {n.replace("/", "\\").lower(): raw2[off : off + size] for n, off, size in entries2}
    packed_cs = amap[CS_PATH.lower()]
    if packed_cs != new_cs:
        fail("roundtrip CommandSet.ini mismatch")
    if b"  6  = Command_ConstructUSAPAC3" not in packed_cs:
        fail("slot 6 missing after pack")
    if packed_cs.count(b"CommandSet AmericaCommandCenterCommandSet\r\n") != 1:
        fail("duplicate CC CommandSet after pack")

    lines = [
        f"DATA bytes={len(out_data)} sha256={sha256(out_data)} entries={len(file_map)}",
        f"CommandSet.ini bytes={len(new_cs)} sha256={sha256(new_cs)}",
        "AmericaCommandCenterCommandSet slot 6 = Command_ConstructUSAPAC3",
        f"other CC slots unchanged: {sorted(old_slots.items())}",
        "THAAD/Patriot/NASAMS object files not modified",
        "STATIC_OK",
    ]
    text = "\n".join(lines) + "\n"
    (OUT_DIR / "SLOT6_PATCH_REPORT.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
