#!/usr/bin/env python3
"""Retarget 7 country War Factories onto unique CommandSets without missiles.

Why the previous extra CommandSet_*.ini last-win failed in-game:
  CommandSet.ini (INIZH first-wins that path, or the first parsed
  CommandSet.ini) already defines SaudiArabia_WarFactoryCommandSet etc.
  with slot 9 = Sarab7 and slot 13 = R11ScudB/9P117. Redefining those
  SAME names in a later CommandSet_ZZZZ_*.ini does not replace the
  in-game bar. The building still reads the first-loaded name.

This rebuild last-wins the War Factory OBJECTS (Object/ is parsed) and
points them at NEW CommandSet names defined only in the Object folder.
No merge leftovers. Object / Weapon / button definitions are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
CS_SUPPLY = r"Data\INI\CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_RADAR = r"Data\INI\Object\zzzzz_SpecterRadarTpy2Cue"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
OBJ_WF = r"Data\INI\Object\zzzzz_SpecterWfRemoveSarab"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"

COUNTRIES = (
    "SaudiArabia",
    "UAE",
    "Syria",
    "India",
    "Pakistan",
    "SouthAfrica",
    "Libya",
)
IRAQ_CLONE = ("SaudiArabia", "UAE", "Syria", "SouthAfrica", "Libya")
BANNED_RE = re.compile(
    r"(?i)(Sarab7|R11ScudB|AlAbbas|9P117|CB_MISSILE_[DEG]|ConstructIraq_Abbas)"
)
CS_PAT = re.compile(r"(?m)^CommandSet\s+(\S+)\s*(.*?)(?=^CommandSet\s|\Z)", re.S)
SLOT_PAT = re.compile(r"(?m)^\s*(\d+)\s*=\s*(\S+)")
OBJ_CS = re.compile(r"(?im)^\s*CommandSet\s*=\s*(\S+)")


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    fm: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        fm[name] = data[off : off + size]
    return fm


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
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
    return bytes(out)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def crlf(body: str) -> bytes:
    return body.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def last_win_block(file_map: dict[str, bytes], kind: str, name: str) -> tuple[str | None, str | None]:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower)\s|\Z)",
        re.S,
    )
    last = None
    src = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin1")
        for m in pat.finditer(text):
            last = m.group(0)
            src = path
    return src, last


def merged_slots(file_map: dict[str, bytes], name: str) -> dict[int, str]:
    slots: dict[int, str] = {}
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        for m in CS_PAT.finditer(raw.decode("latin1")):
            if m.group(1) != name:
                continue
            for a, b in SLOT_PAT.findall(m.group(2)):
                slots[int(a)] = b
    return slots


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def fcrl_block(body: str | None) -> str:
    m = re.search(
        r"Behavior\s*=\s*FireWeaponUpdate\s+ModuleTag_FCRL\s*.*?End",
        body or "",
        re.S,
    )
    return m.group(0) if m else ""


def validate(file_map: dict[str, bytes]) -> None:
    for country in COUNTRIES:
        obj = f"{country}_WarFactory_T"
        src, body = last_win_block(file_map, "Object", obj)
        _req(OBJ_WF.replace("\\", "") in (src or "").replace("\\", ""), f"{obj} last-win not {OBJ_WF} ({src})")
        css = OBJ_CS.findall(body or "")
        unique = f"{country}_WarFactoryCommandSet_NoSarab"
        _req(unique in css, f"{obj} CommandSet is {css}, expected {unique}")
        _req(f"{country}_WarFactoryCommandSet" not in css, f"{obj} still points at the old shared CommandSet {css}")
        _req("ProductionUpdate" in (body or ""), f"{obj} lost ProductionUpdate")
        _req("RepairDockUpdate" in (body or ""), f"{obj} lost RepairDock")
        _req(f"Side             = {country}" in (body or "") or f"Side             = {country}\r" in (body or ""), f"{obj} Side changed")

        cs_src, cs_body = last_win_block(file_map, "CommandSet", unique)
        _req(OBJ_WF.replace("\\", "") in (cs_src or "").replace("\\", ""), f"{unique} last-win not Object folder ({cs_src})")
        slots = merged_slots(file_map, unique)
        _req(bool(slots), f"{unique} has no slots")
        for slot, btn in slots.items():
            _req(not BANNED_RE.search(btn), f"{unique} slot {slot} still {btn}")
        _req("Command_Sell" in slots.values(), f"{unique} lost Sell")
        if country in IRAQ_CLONE:
            _req(slots.get(1) == "Command_ConstructIraq_T-72", f"{unique} lost T-72")
            _req(slots.get(9) == f"Command_Construct{country}_AlKhalid", f"{unique} slot 9 not country AlKhalid")
            _req(slots.get(13) == f"Command_Construct{country}_CombatDrone", f"{unique} slot 13 not country CombatDrone")
            _req(slots.get(10) == "Command_ConstructIraq_Alhussaien", f"{unique} lost Alhussaien")
            _req(len({slots[i] for i in (9, 10, 11, 12, 13)}) == 5, f"{unique} has duplicate production buttons in 9-13")
        else:
            _req(slots.get(1) == "Command_ConstructAmericaTankCrusader", f"{unique} India/Pakistan roster changed")

        # CommandSet.ini still carries the leftover Iraq buttons on the OLD
        # shared names. Buildings must not read those names anymore.
        packed_cs = file_map.get(r"Data\INI\CommandSet.ini", b"").decode("latin1")
        if country in IRAQ_CLONE:
            _req(
                f"CommandSet {country}_WarFactoryCommandSet" in packed_cs
                and "Command_ConstructIraq_Sarab7" in packed_cs,
                f"CommandSet.ini lost the leftover {country} / Sarab7 definition we detach from",
            )

    # No last-win WF object for these countries may still assign a banned button.
    for country in COUNTRIES:
        src, body = last_win_block(file_map, "Object", f"{country}_WarFactory_T")
        assigned = OBJ_CS.findall(body or "")
        for csname in assigned:
            slots = merged_slots(file_map, csname)
            for slot, btn in slots.items():
                _req(not BANNED_RE.search(btn), f"{country} active CS {csname} slot {slot}={btn}")

    _, al_fahd = last_win_block(file_map, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    _req("CB_MISSILE_D" in (al_fahd or ""), "AlAbbas lost from Iraq missile factory")
    _req("CB_MISSILE_E" in (al_fahd or ""), "Sarab7 lost from Iraq missile factory")
    _req("CB_MISSILE_G" in (al_fahd or ""), "9P117 lost from Iraq missile factory")

    for country in COUNTRIES:
        src, body = last_win_block(file_map, "CommandSet", f"{country}_MissileFactoryCommandSet")
        _req(bool(body), f"{country} MissileFactory missing")
        _req(OBJ_WF.replace("\\", "") not in (src or "").replace("\\", ""), f"{country} MissileFactory rewritten")

    for obj in ("Iraq_Sarab7", "Iraq_R11ScudB", "Iraq_AlAbbas"):
        src, body = last_win_block(file_map, "Object", obj)
        _req(bool(body), f"Object {obj} missing")
        _req(OBJ_WF.replace("\\", "") not in (src or "").replace("\\", ""), f"{obj} last-win moved to {src}")

    _, btn = last_win_block(file_map, "CommandButton", "Command_ConstructIraq_Sarab7")
    _req("Iraq_Sarab7" in (btn or ""), "Sarab7 construct button changed")
    _, btn = last_win_block(file_map, "CommandButton", "Command_ConstructIraq_R11ScudB")
    _req("irq_9p117" in (btn or ""), "9P117 ButtonImage changed")
    _, btn = last_win_block(file_map, "CommandButton", "CB_MISSILE_D")
    _req("Iraq_AlAbbas" in (btn or ""), "CB_MISSILE_D no longer builds AlAbbas")

    irq_src, _ = last_win_block(file_map, "CommandSet", "Iraq_WarFactoryCommandSet_T3")
    _req(irq_src == r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini", f"Iraq WF T3 last-win moved to {irq_src}")

    obj_src, obj = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(obj_src == OBJ_IRAQ, f"Iraq radar object last-win moved to {obj_src}")
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _req(cs_src == CS_IRAQ, f"Iraq radar CS last-win moved to {cs_src}")
    _req("Command_SpySatelliteScan" not in (cs or ""), "Iraq CS regained Spy Sat")

    am_src, am = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(OBJ_SUPPLY.replace("\\", "") in (am_src or "").replace("\\", ""), f"America Supply last-win lost ({am_src})")
    sc_src, sc = last_win_block(file_map, "CommandSet", "AmericaSupplyCenterCommandSet")
    _req(sc_src == CS_SUPPLY, f"America Supply CS last-win moved to {sc_src}")

    tpy_src, tpy = last_win_block(file_map, "Object", "US_AN_TPY2_CombatMode")
    _req(tpy_src and "US_AN_TPY2.ini" in (tpy_src or ""), f"TPY-2 moved to {tpy_src}")
    _req("FireControlRadarDataLink" in fcrl_block(tpy), "TPY-2 lost DataLink")
    for obj_name in ("ChinaVehicleHT233_CombatMode", "Russia_92N6R_CombatMode"):
        src, body = last_win_block(file_map, "Object", obj_name)
        _req(OBJ_RADAR.replace("\\", "") in (src or "").replace("\\", ""), f"{obj_name} last-win not TPY-2 cue ({src})")
        _req("FireControlRadarDataLink" in fcrl_block(body), f"{obj_name} FCRL not TPY-2")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"92N6R DataLink last-win moved to {wsrc}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--objects",
        type=Path,
        default=Path("patch/Data/INI/Object/zzzzz_SpecterWfRemoveSarab"),
    )
    args = ap.parse_args()

    fm = read_big(args.src_big)
    extras: dict[str, bytes] = {}
    for ini in sorted(args.objects.glob("*.ini")):
        extras[rf"{OBJ_WF}\{ini.name}"] = crlf(ini.read_text(encoding="latin1"))

    changed = []
    for name, body in extras.items():
        prev = fm.get(name)
        fm[name] = body
        changed.append(("update" if prev is not None else "add", name))

    validate(fm)

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    blob = build_big(fm)
    args.out_big.write_bytes(blob)
    hdr = struct.unpack(">I", blob[4:8])[0]
    if hdr != len(blob):
        raise SystemExit(f"BIG size field {hdr} != file {len(blob)}")
    digest = sha256(args.out_big)
    Path(str(args.out_big) + ".sha256").write_text(digest + "\n")
    print(f"SRC  size={args.src_big.stat().st_size} sha256={sha256(args.src_big)}")
    print(f"OUT  size={args.out_big.stat().st_size} sha256={digest} entries={len(fm)}")
    for op, name in changed:
        print(f"  {op} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
