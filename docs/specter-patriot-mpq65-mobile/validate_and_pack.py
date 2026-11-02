#!/usr/bin/env python3
"""Validate PR #743 correction and pack overlay BIG."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
PACKED = Path("/tmp/spec-audit/_SPEC_DATA_ONE.big")
OUT_DIR = ROOT / "docs/specter-patriot-mpq65-mobile"
OUT_BIG = OUT_DIR / "_SPECTER_PATRIOT_MPQ65_VEHICLE.big"
VEHICLE = ROOT / (
    "patch/Data/INI/Object/Specter/PatchSystems/AirDefense/"
    "AmericaVehiclePatriotMPQ65.ini"
)
BUTTON = ROOT / "patch/Data/INI/CommandButton_AmericaVehiclePatriotMPQ65.ini"
CMDSET = ROOT / "patch/Data/INI/CommandSet_ZZZZ_AmericaVehiclePatriotMPQ65.ini"
OLD_OVERLAY = ROOT / (
    "patch/Data/INI/Object/Specter/United States Of America/"
    "AirDefense Installation/AN_MPQ65.ini"
)
PACK_FILES = [
    VEHICLE,
    BUTTON,
    CMDSET,
    ROOT / "patch/Data/English/FactionExpansion_AmericaVehiclePatriotMPQ65_Strings.txt",
    ROOT / "patch/Data/English/generals.csf",
]


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def list_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        offset, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1").replace("\\", "/")
        pos = end + 1
        entries.append((name, offset, size))
    return data, entries


def pack_big(file_map: dict[str, bytes]) -> bytes:
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


def overlay_mentions_static() -> list[str]:
    hits = []
    root = ROOT / "patch/Data"
    for p in root.rglob("*.ini"):
        text = p.read_text(encoding="latin-1", errors="replace")
        if re.search(r"(?m)^Object\s+AmericaRadarAN/MPQ65\s*$", text):
            hits.append(str(p.relative_to(ROOT)))
    return hits


def last_wins_cmdset() -> str:
    files = sorted((ROOT / "patch/Data/INI").glob("CommandSet*.ini"), key=lambda p: p.name.lower())
    last = None
    for p in files:
        text = p.read_text(encoding="latin-1", errors="replace")
        if re.search(r"(?m)^CommandSet\s+America_MilitaryHQCommandSet\s*$", text):
            last = p.name
    return last or ""


def main() -> int:
    if OLD_OVERLAY.exists():
        fail(f"static overlay rewrite still present: {OLD_OVERLAY}")
    hits = overlay_mentions_static()
    if hits:
        fail(f"overlay still redefines AmericaRadarAN/MPQ65 in {hits}")
    print("OK   overlay does not redefine AmericaRadarAN/MPQ65")

    packed, entries = list_big(PACKED)
    static_blob = None
    for name, off, sz in entries:
        if name.endswith("AirDefense Installation/AN_MPQ65.ini"):
            static_blob = packed[off : off + sz].decode("latin-1", "replace")
            break
    if not static_blob:
        fail("packed AN_MPQ65.ini missing")
    if "KindOf = SELECTABLE CAN_CAST_REFLECTIONS PRELOAD VEHICLE IMMOBILE" not in static_blob:
        fail("packed static radar KindOf changed")
    if "Locomotor" in static_blob.split("Object AmericaRadarAN/MPQ65", 1)[1].split("Object AmericaMPQ65Damaged", 1)[0]:
        fail("packed static radar unexpectedly has Locomotor")
    print("OK   packed AmericaRadarAN/MPQ65 still IMMOBILE with no Locomotor")

    veh = VEHICLE.read_text(encoding="latin-1")
    checks = {
        "new_object": "Object AmericaVehiclePatriotMPQ65" in veh,
        "model": "Model               = US_AN_MPQ65" in veh,
        "anim": "US_AN_MPQ65.US_AN_MPQ65" in veh,
        "side": "Side                = America" in veh,
        "loco": "Locomotor = SET_NORMAL Generic8x8Locomotor" in veh,
        "ai": "AIUpdateInterface" in veh,
        "no_immobile": "IMMOBILE" not in veh,
        "fcr": "AN_MPQ65_WaveEmitter" in veh,
        "detect": "DetectionRange            = 970" in veh,
        "cost": "BuildCost            = 2600" in veh,
        "time": "BuildTime            = 15.0" in veh,
        "cmd": "GenericCommandSet" in veh,
        "no_static_name": "Object AmericaRadarAN/MPQ65" not in veh,
        "no_deploy": "DeployStyleAIUpdate" not in veh,
    }
    for name, ok in checks.items():
        print(("OK  " if ok else "FAIL"), name)
        if not ok:
            fail(name)

    btn = BUTTON.read_text(encoding="latin-1")
    if "Object             = AmericaVehiclePatriotMPQ65" not in btn:
        fail("construct button Object mismatch")
    if "Command_ConstructAmericaVehiclePatriotMPQ65" not in btn:
        fail("construct button name missing")
    print("OK   construct button")

    cs = CMDSET.read_text(encoding="latin-1")
    if "12 = Command_ConstructAmericaVehiclePatriotMPQ65" not in cs:
        fail("HQ slot 12 missing")
    for slot in range(1, 12):
        if not re.search(rf"(?m)^\s*{slot} = Command_ConstructAmerica_", cs):
            fail(f"HQ slot {slot} dropped")
    if last_wins_cmdset() != CMDSET.name:
        fail(f"last-wins America_MilitaryHQCommandSet is {last_wins_cmdset()} not {CMDSET.name}")
    print("OK   America_MilitaryHQCommandSet last-wins slot 12")
    print("OK   last-wins file", last_wins_cmdset())

    file_map = {}
    for path in PACK_FILES:
        if not path.exists():
            fail(f"missing {path}")
        rel = path.relative_to(ROOT / "patch").as_posix().replace("/", "\\")
        file_map[rel] = path.read_bytes()
    if any("AN_MPQ65.ini" in k for k in file_map):
        fail("BIG still contains static AN_MPQ65.ini overlay")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    big = pack_big(file_map)
    OUT_BIG.write_bytes(big)
    digest = hashlib.sha256(big).hexdigest()
    (OUT_DIR / (OUT_BIG.name + ".sha256")).write_text(
        f"{digest}  {OUT_BIG.name}\n", encoding="ascii"
    )
    print(f"PACKED {OUT_BIG} bytes={len(big)} entries={len(file_map)} sha256={digest}")
    print("STATIC_OK")
    print("HQ_BUILD_STATIC: America_MilitaryHQCommandSet slot 12 = Command_ConstructAmericaVehiclePatriotMPQ65")
    print("INGAME_ZH: not executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
