#!/usr/bin/env python3
"""Remove Sarab7 / 9P117 / AlAbbas War Factory buy options for 7 countries.

Packed CommandSet.ini last-wins Saudi/UAE/Syria/SouthAfrica/Libya War
Factory CommandSets to the Iraq roster, including:
  slot 9  = Command_ConstructIraq_Sarab7
  slot 13 = Command_ConstructIraq_R11ScudB   (ButtonImage irq_9p117)

India last-wins a USA roster; Pakistan last-wins a Russia roster.
Neither currently lists those three UNIT_BUILD buttons. Their WF
CommandSets are still last-won here so CommandSet slot-merge cannot
reintroduce the leftover Iraq buttons.

Shared CommandSet.ini is not edited. Object / Weapon / CommandButton
definitions are not edited. Dedicated MissileFactory and Abbas
CommandSets are not redefined. Iraq / Turkey War Factory sets are
not redefined.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
CS_SUPPLY = r"Data\INI\CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini"
CS_WF = r"Data\INI\CommandSet_ZZZZ_ZZZZZWfRemoveSarab.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_RADAR = r"Data\INI\Object\zzzzz_SpecterRadarTpy2Cue"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"

IRAQ_CLONE_COUNTRIES = (
    "SaudiArabia",
    "UAE",
    "Syria",
    "SouthAfrica",
    "Libya",
)
LOCK_COUNTRIES = ("India", "Pakistan")
ALL_COUNTRIES = IRAQ_CLONE_COUNTRIES + LOCK_COUNTRIES
WF_SUFFIXES = ("", "1", "2", "3")

BANNED = (
    "Command_ConstructIraq_Sarab7",
    "Command_ConstructIraq_R11ScudB",
    "Command_ConstructTurkey_Sarab7",
    "Command_ConstructTurkey_R11ScudB",
    "Command_ConstructWFUnlock_Iraq_Sarab7",
    "Command_ConstructWFUnlock_Iraq_R11ScudB",
    "CB_MISSILE_D",
    "CB_MISSILE_E",
    "CB_MISSILE_G",
    "Command_ConstructIraq_AlAbbas",
)

BANNED_RE = re.compile(
    r"(?i)(Sarab7|R11ScudB|AlAbbas|9P117|CB_MISSILE_[DEG])"
)

IRAQ_CLONE_KEEP = {
    1: "Command_ConstructIraq_T-72",
    2: "Command_ConstructIraq_BMP-1",
    3: "Command_ConstructIraq_BMP-2",
    4: "Command_ConstructIraq_BTR-90",
    5: "Command_ConstructIraq_2S1",
    6: "Command_ConstructIraq_Sam8",
    7: "Command_ConstructIraq_AssadBabel-2",
    8: "Command_ConstructIraq_SA-6",
    10: "Command_ConstructIraq_Alhussaien",
    11: "Command_ConstructIraqVehicleRoland3K",
    12: "Command_ConstructIraq_BM-21",
    14: "Command_Sell",
}

INDIA_KEEP = {
    1: "Command_ConstructAmericaTankCrusader",
    2: "Command_ConstructAmericaVehicleM1128",
    3: "Command_ConstructAmericaVehicleM1296",
    4: "Command_ConstructAmericaVehicleSentryDrone",
    5: "Command_ConstructAmericaVehicleTomahawk",
    6: "Command_ConstructAmericaTankM109A7",
    7: "Command_ConstructAmericaVehicleAvenger",
    8: "Command_ConstructAmericaVehicleMicrowave",
    9: "Command_ConstructAmericaVehicleAN_TPY2",
    10: "Command_ConstructAmericaVehicleTHAAD",
    11: "Command_ConstructAmericaVehicleM142",
    12: "Command_ConstructAmericaVehicleM1075I",
    13: "Command_ConstructAmericaVehicleM1075T",
    14: "Command_Sell",
}

PAKISTAN_KEEP = {
    1: "Command_ConstructRussiaTankT90A",
    2: "Command_ConstructRussiaTankT72B3M",
    3: "Command_ConstructRussiaVehicleBm30",
    4: "Command_ConstructRussiaVehicleKrasukha4",
    5: "Command_ConstructRussiaArtillery2S19M2",
    6: "Command_ConstructRussiaTankBMP3",
    7: "Command_ConstructRussiaTankTorM2M",
    8: "Command_ConstructRussiaVehiclePantsirS1M",
    9: "Command_ConstructRussiaVehicle92N6R",
    10: "Command_ConstructRussiaVehicleS400",
    11: "Command_ConstructRussiaTankTos1A",
    12: "Command_ConstructRussiaVehicle9K720",
    13: "Command_ConstructRussiaVehicleRS24",
    14: "Command_Sell",
}

CS_PAT = re.compile(
    r"(?m)^CommandSet\s+(\S+)\s*(.*?)(?=^CommandSet\s|\Z)",
    re.S,
)
SLOT_PAT = re.compile(r"(?m)^\s*(\d+)\s*=\s*(\S+)")


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


def merged_slots(file_map: dict[str, bytes], name: str) -> tuple[dict[int, str], list[str]]:
    slots: dict[int, str] = {}
    sources: list[str] = []
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin1")
        for m in CS_PAT.finditer(text):
            if m.group(1) != name:
                continue
            sources.append(path)
            for a, b in SLOT_PAT.findall(m.group(2)):
                slots[int(a)] = b
    return slots, sources


def wf_names(country: str) -> list[str]:
    return [f"{country}_WarFactoryCommandSet{sfx}" for sfx in WF_SUFFIXES]


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
    for country in ALL_COUNTRIES:
        for csname in wf_names(country):
            src, last = last_win_block(file_map, "CommandSet", csname)
            _req(src == CS_WF, f"{csname} last-win is {src}, expected {CS_WF}")
            slots, sources = merged_slots(file_map, csname)
            _req(bool(slots), f"{csname} missing merged slots")
            _req(CS_WF in sources, f"{csname} not defined in later file")
            for btn in BANNED:
                _req(btn not in slots.values(), f"{csname} still has {btn}: {slots}")
            for slot, btn in slots.items():
                _req(
                    not BANNED_RE.search(btn),
                    f"{csname} slot {slot} still {btn}",
                )
            _req("Command_Sell" in slots.values(), f"{csname} lost Sell")

            if country in IRAQ_CLONE_COUNTRIES:
                for slot, btn in IRAQ_CLONE_KEEP.items():
                    _req(slots.get(slot) == btn, f"{csname} slot {slot} became {slots.get(slot)}, expected {btn}")
                _req(slots.get(9) != "Command_ConstructIraq_Sarab7", f"{csname} slot 9 still Sarab7")
                _req(slots.get(13) != "Command_ConstructIraq_R11ScudB", f"{csname} slot 13 still 9P117")
            elif country == "India":
                _req(slots == INDIA_KEEP, f"{csname} India roster changed: {slots}")
            elif country == "Pakistan":
                _req(slots == PAKISTAN_KEEP, f"{csname} Pakistan roster changed: {slots}")

    # Shared CommandSet.ini still has the original Iraq-clone leftover (first-win path).
    packed_cs = file_map.get(r"Data\INI\CommandSet.ini", b"").decode("latin1")
    _req("CommandSet SaudiArabia_WarFactoryCommandSet" in packed_cs, "packed CommandSet.ini lost Saudi WF")
    _req("Command_ConstructIraq_Sarab7" in packed_cs, "packed CommandSet.ini unexpectedly lost Sarab7 (Iraq/shared)")

    # Iraq / Turkey / dedicated missile buildings unchanged.
    irq_src, irq = last_win_block(file_map, "CommandSet", "Iraq_WarFactoryCommandSet_T3")
    _req(irq_src == r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini", f"Iraq WF T3 last-win moved to {irq_src}")
    _req("Command_ConstructIraq_Sarab7" not in (irq or ""), "Iraq WF T3 unexpectedly gained Sarab7")

    _, irq_base = last_win_block(file_map, "CommandSet", "Iraq_WarFactoryCommandSet")
    _req(bool(irq_base), "Iraq_WarFactoryCommandSet missing")

    _, al_fahd = last_win_block(file_map, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    _req("CB_MISSILE_D" in (al_fahd or ""), "AlAbbas UNIT_BUILD lost from Iraq missile factory")
    _req("CB_MISSILE_E" in (al_fahd or ""), "Sarab7 UNIT_BUILD lost from Iraq missile factory")
    _req("CB_MISSILE_G" in (al_fahd or ""), "9P117 UNIT_BUILD lost from Iraq missile factory")

    for country in ALL_COUNTRIES:
        src, body = last_win_block(file_map, "CommandSet", f"{country}_MissileFactoryCommandSet")
        _req(bool(body), f"{country} MissileFactory CommandSet missing")
        _req(src != CS_WF, f"{country} MissileFactory was rewritten by WF last-win ({src})")
        _req("Command_Sell" in (body or ""), f"{country} MissileFactory lost Sell")

    for obj in ("Iraq_Sarab7", "Iraq_R11ScudB", "Iraq_AlAbbas"):
        src, body = last_win_block(file_map, "Object", obj)
        _req(bool(body), f"Object {obj} missing")
        _req("zzzzz" not in (src or "").lower() or "WfRemove" not in (src or ""), f"{obj} last-win moved to {src}")

    _, btn = last_win_block(file_map, "CommandButton", "Command_ConstructIraq_Sarab7")
    _req("Object        = Iraq_Sarab7" in (btn or ""), "Sarab7 construct button changed")
    _, btn = last_win_block(file_map, "CommandButton", "Command_ConstructIraq_R11ScudB")
    _req("Object        = Iraq_R11ScudB" in (btn or ""), "9P117 construct button changed")
    _req("irq_9p117" in (btn or ""), "9P117 ButtonImage changed")
    _, btn = last_win_block(file_map, "CommandButton", "CB_MISSILE_D")
    _req("Iraq_AlAbbas" in (btn or ""), "CB_MISSILE_D no longer builds AlAbbas")

    # Prior accepted last-wins.
    obj_src, obj = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(obj_src == OBJ_IRAQ, f"Iraq radar object last-win moved to {obj_src}")
    ru = re.search(r"Behavior\s*=\s*RadarUpgrade.*?End", obj or "", re.S)
    _req(bool(ru) and "TriggeredBy" in ru.group(0) and "Upgrade_AmericaRadar" in ru.group(0), "Iraq RadarUpgrade TriggeredBy lost")
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _req(cs_src == CS_IRAQ, f"Iraq radar CS last-win moved to {cs_src}")
    _req("Command_SpySatelliteScan" not in (cs or ""), "Iraq CS regained Spy Sat")

    am_src, am = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(OBJ_SUPPLY.replace("\\", "") in (am_src or "").replace("\\", ""), f"America Supply Centre last-win lost ({am_src})")
    _req("AmericaSupplyCenterCommandSet" in (am or ""), "America Supply Centre CommandSet lost")
    sc_src, sc = last_win_block(file_map, "CommandSet", "AmericaSupplyCenterCommandSet")
    _req(sc_src == CS_SUPPLY, f"America Supply CS last-win moved to {sc_src}")
    _req("Command_ConstructAmericaSupplyChinook_USA" in (sc or ""), "America Supply buy button lost")

    tpy_src, tpy = last_win_block(file_map, "Object", "US_AN_TPY2_CombatMode")
    _req(tpy_src and "US_AN_TPY2.ini" in (tpy_src or ""), f"TPY-2 CombatMode last-win moved to {tpy_src}")
    _req("FireControlRadarDataLink" in fcrl_block(tpy), "TPY-2 lost FireControlRadarDataLink")
    for obj_name in ("ChinaVehicleHT233_CombatMode", "Russia_92N6R_CombatMode"):
        src, body = last_win_block(file_map, "Object", obj_name)
        _req(OBJ_RADAR.replace("\\", "") in (src or "").replace("\\", ""), f"{obj_name} last-win not TPY-2 cue ({src})")
        _req("FireControlRadarDataLink" in fcrl_block(body), f"{obj_name} FCRL not TPY-2 DataLink")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"92N6R DataLink last-win moved to {wsrc}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--ini",
        type=Path,
        default=Path("patch/Data/INI/CommandSet_ZZZZ_ZZZZZWfRemoveSarab.ini"),
    )
    args = ap.parse_args()

    fm = read_big(args.src_big)
    body = crlf(args.ini.read_text(encoding="latin1"))
    prev = fm.get(CS_WF)
    fm[CS_WF] = body
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
    print(f"  {'update' if prev is not None else 'add'} {CS_WF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
