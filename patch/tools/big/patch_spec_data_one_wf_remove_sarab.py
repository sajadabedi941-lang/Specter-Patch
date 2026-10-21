#!/usr/bin/env python3
"""Restore seven War Factory CommandSets to names that CommandSet.ini actually binds.

Empty-bar cause (wf-fix-commandset-crash):
  Objects last-won onto *_WarFactoryCommandSet_NoSarab. Those names exist
  only in Data\\INI\\CommandSet_ZZZZ_ZZZZZWfDetach.ini. SPECTER's live
  command bar binds CommandSet.ini (INIZH first-wins that path; extra
  CommandSet_ZZZZ_*.ini files do not attach new names). A missing
  CommandSet name yields an empty production bar. The same failure mode
  as Supply Centre *_CountryIncome names.

  Object\\ CommandSet BLOCKS crash ZH. Extra CommandSet_*.ini last-wins
  of already-defined names do not change the in-game bar. Unique names
  that are not in CommandSet.ini do not appear either.

This rebuild strips the WF overlay files from the installable DATA BIG
so each *_WarFactory_T again uses its packed CommandSet.ini name.
Trusted content matches HT233_92N6E_TPY2_CUE (last DATA before the
empty-bar overlays). No CommandSet blocks are placed in Object\\.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
CS_SUPPLY = r"Data\INI\CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini"
CS_DETACH = r"Data\INI\CommandSet_ZZZZ_ZZZZZWfDetach.ini"
CS_REMOVE = r"Data\INI\CommandSet_ZZZZ_ZZZZZWfRemoveSarab.ini"
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
CS_PAT = re.compile(r"(?m)^CommandSet\s+(\S+)\s*(.*?)(?=^CommandSet\s|\Z)", re.S)
SLOT_PAT = re.compile(r"(?m)^\s*(\d+)\s*=\s*(\S+)")
OBJ_CS = re.compile(r"(?im)^\s*CommandSet\s*=\s*(\S+)")
BTN_PAT = re.compile(r"(?m)^CommandButton\s+(\S+)")
CS_BLOCK = re.compile(r"(?m)^CommandSet\s+([A-Za-z_][A-Za-z0-9_]*)")


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


def first_cs_in_commandset_ini(file_map: dict[str, bytes], name: str) -> dict[int, str]:
    raw = file_map.get(r"Data\INI\CommandSet.ini", b"").decode("latin1")
    for m in CS_PAT.finditer(raw):
        if m.group(1) == name:
            return {int(a): b for a, b in SLOT_PAT.findall(m.group(2))}
    return {}


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _norm(path: str | None) -> str:
    return (path or "").replace("\\", "").replace("/", "").lower()


def fcrl_block(body: str | None) -> str:
    m = re.search(
        r"Behavior\s*=\s*FireWeaponUpdate\s+ModuleTag_FCRL\s*.*?End",
        body or "",
        re.S,
    )
    return m.group(0) if m else ""


def command_buttons(file_map: dict[str, bytes]) -> set[str]:
    names: set[str] = set()
    for path, raw in file_map.items():
        if "commandbutton" in path.lower() and path.lower().endswith(".ini"):
            names.update(BTN_PAT.findall(raw.decode("latin1")))
    return names


def drop_wf_overlays(file_map: dict[str, bytes]) -> list[str]:
    removed = []
    for name in list(file_map):
        low = name.lower().replace("/", "\\")
        if "zzzzz_specterwfremovesarab" in low or low.endswith("commandset_zzzz_zzzzzwfdetach.ini") or low.endswith("commandset_zzzz_zzzzzwfremovesarab.ini"):
            del file_map[name]
            removed.append(name)
    return removed


def validate(file_map: dict[str, bytes]) -> dict[str, dict[int, str]]:
    for path in file_map:
        low = path.lower().replace("/", "\\")
        _req("zzzzz_specterwfremovesarab" not in low, f"WF overlay still packed: {path}")
        _req("commandset_zzzz_zzzzzwfdetach.ini" not in low, f"Detach extra CS still packed: {path}")
        _req("commandset_zzzz_zzzzzwfremovesarab.ini" not in low, f"Remove extra CS still packed: {path}")
        if _norm(OBJ_WF) in _norm(path) and path.lower().endswith(".ini"):
            blocks = CS_BLOCK.findall(file_map[path].decode("latin1"))
            _req(not blocks, f"Object folder still has CommandSet blocks in {path}: {blocks}")

    buttons = command_buttons(file_map)
    restored: dict[str, dict[int, str]] = {}
    for country in COUNTRIES:
        obj = f"{country}_WarFactory_T"
        src, body = last_win_block(file_map, "Object", obj)
        _req(bool(body), f"{obj} missing")
        _req(_norm(OBJ_WF) not in _norm(src), f"{obj} still last-wins from overlay {src}")
        css = OBJ_CS.findall(body or "")
        live = f"{country}_WarFactoryCommandSet"
        _req(live in css, f"{obj} CommandSet is {css}, expected {live}")
        _req(not any(name.endswith("_NoSarab") for name in css), f"{obj} still points at unique empty name {css}")
        _req("ProductionUpdate" in (body or ""), f"{obj} lost ProductionUpdate")
        _req("RepairDockUpdate" in (body or ""), f"{obj} lost RepairDock")

        slots = first_cs_in_commandset_ini(file_map, live)
        _req(bool(slots), f"{live} missing from packed CommandSet.ini")
        _req("Command_Sell" in slots.values(), f"{live} lost Sell")
        vehicle = [btn for slot, btn in sorted(slots.items()) if btn != "Command_Sell"]
        _req(len(vehicle) >= 12, f"{live} has only {len(vehicle)} production buttons")
        missing = [btn for btn in slots.values() if btn not in buttons]
        _req(not missing, f"{live} buttons missing from CommandButton.ini: {missing}")
        if country in IRAQ_CLONE:
            _req(slots.get(1) == "Command_ConstructIraq_T-72", f"{live} lost T-72")
        else:
            _req(slots.get(1) == "Command_ConstructAmericaTankCrusader", f"{live} lost Crusader")
        restored[country] = slots

        unique = f"{country}_WarFactoryCommandSet_NoSarab"
        usrc, _ = last_win_block(file_map, "CommandSet", unique)
        _req(usrc is None, f"{unique} still defined in {usrc}")

    _, al_fahd = last_win_block(file_map, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    _req("CB_MISSILE_D" in (al_fahd or ""), "AlAbbas lost from Iraq missile factory")
    _req("CB_MISSILE_E" in (al_fahd or ""), "Sarab7 lost from Iraq missile factory")
    _req("CB_MISSILE_G" in (al_fahd or ""), "9P117 lost from Iraq missile factory")

    irq_src, _ = last_win_block(file_map, "CommandSet", "Iraq_WarFactoryCommandSet_T3")
    _req(irq_src == r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini", f"Iraq WF T3 last-win moved to {irq_src}")

    obj_src, obj = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(obj_src == OBJ_IRAQ, f"Iraq radar object last-win moved to {obj_src}")
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _req(cs_src == CS_IRAQ, f"Iraq radar CS last-win moved to {cs_src}")
    _req("Command_SpySatelliteScan" not in (cs or ""), "Iraq CS regained Spy Sat")

    am_src, am = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(_norm(OBJ_SUPPLY) in _norm(am_src), f"America Supply last-win lost ({am_src})")
    sc_src, sc = last_win_block(file_map, "CommandSet", "AmericaSupplyCenterCommandSet")
    _req(sc_src == CS_SUPPLY, f"America Supply CS last-win moved to {sc_src}")

    tpy_src, tpy = last_win_block(file_map, "Object", "US_AN_TPY2_CombatMode")
    _req(tpy_src and "US_AN_TPY2.ini" in (tpy_src or ""), f"TPY-2 moved to {tpy_src}")
    _req("FireControlRadarDataLink" in fcrl_block(tpy), "TPY-2 lost DataLink")
    for obj_name in ("ChinaVehicleHT233_CombatMode", "Russia_92N6R_CombatMode"):
        src, body = last_win_block(file_map, "Object", obj_name)
        _req(_norm(OBJ_RADAR) in _norm(src), f"{obj_name} last-win not TPY-2 cue ({src})")
        _req("FireControlRadarDataLink" in fcrl_block(body), f"{obj_name} FCRL not TPY-2")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"92N6R DataLink last-win moved to {wsrc}")
    return restored


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument("--trusted-ref", type=Path, default=None)
    args = ap.parse_args()

    fm = read_big(args.src_big)
    removed = drop_wf_overlays(fm)

    if args.trusted_ref:
        trusted = read_big(args.trusted_ref)
        _req(set(fm) == set(trusted), f"restored entry set != trusted ref (+{sorted(set(fm)-set(trusted))} -{sorted(set(trusted)-set(fm))})")
        for name in fm:
            _req(fm[name] == trusted[name], f"content mismatch vs trusted ref: {name}")

    restored = validate(fm)

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
    for name in removed:
        print(f"  remove {name}")
    for country, slots in restored.items():
        print(f"  {country} {country}_WarFactoryCommandSet buttons={len(slots)}")
        for slot, btn in sorted(slots.items()):
            print(f"    {slot:2d} = {btn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
