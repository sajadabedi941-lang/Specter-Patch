#!/usr/bin/env python3
"""Restore in-building Supply Centre buy buttons (Israel pattern).

Israel's working building is AirF_AmericaSupplyCenter:
  CommandSet = AirF_AmericaSupplyCenterCommandSet   (defined in CommandSet.ini)
  slot 1 = AirF_Command_ConstructAFGChinook         (UNIT_BUILD in CommandButton.ini)
  slot 13 = Rally, slot 14 = Sell
  AFG Chinook Prerequisites are commented.

America / China / Russia last-win buildings pointed at *_CountryIncome
CommandSets that do not exist in CommandSet.ini. France's CommandSet.ini
definition is sell-only. AmericaSupplyChinook_USA also had an active
Prerequisites { Object = AmericaSupplyCenter } that Israel's working
Chinook does not.

This rebuild:
  * points the four buildings at core CommandSet.ini names
  * last-wins those names (and _CountryIncome aliases) to Israel slots
    1 = country UNIT_BUILD, 13 = Rally, 14 = Sell
  * comments AmericaSupplyChinook_USA Prerequisites
  * overwrites Russia slot 2 so Mi-8 cannot remain via CommandSet merge
  * does not edit Israel, Iraq radar grant, or other countries
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
CS_SUPPLY = r"Data\INI\CommandSet_ZZZZ_ZZZZSupplyCentreBuy.ini"
CS_SUPPLY_LATER = r"Data\INI\CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini"
BTN_SUPPLY = r"Data\INI\CommandButton_ZZZZ_ZZZZSupplyCentreBuy.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_DIR = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"

SPY_BUTTONS = (
    "Command_SpySatelliteScan",
    "Command_SpecterSpySatelliteFee",
    "Command_IraqiRadarSearch",
)

CORE_COMMANDSETS = {
    "AmericaSupplyCenter": "AmericaSupplyCenterCommandSet",
    "ChinaSupplyCenter": "ChinaSupplyCenterCommandSet",
    "RussiaSupplyCenter": "RussiaSupplyCenterCommandSet",
    "FranceSupplyCenter": "FranceSupplyCenterCommandSet",
}

BUY_BUTTONS = {
    "America": ("Command_ConstructAmericaSupplyChinook_USA", "AmericaSupplyChinook_USA"),
    "China": ("Command_ConstructChinaVehicleSupplyTruck", "ChinaVehicleSupplyTruck"),
    "Russia": ("Command_ConstructRussiaSupplyTruck_CountryIncome", "RussiaSupplyTruck_CountryIncome"),
    "France": ("Command_ConstructFranceHelicopterCH47F", "FranceHelicopterCH47F"),
}


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


def crlf(body: str) -> bytes:
    return body.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def slots(body: str | None) -> dict[str, str]:
    if not body:
        return {}
    return dict(re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", body))


def merged_slots(file_map: dict[str, bytes], name: str) -> dict[str, str]:
    pat = re.compile(
        rf"(?m)^CommandSet\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower)\s|\Z)",
        re.S,
    )
    merged: dict[str, str] = {}
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin1")
        for m in pat.finditer(text):
            merged.update(slots(m.group(0)))
    return merged


COMMANDSET_IRAQ = """\
; SPECTER last-win. SAGE CommandSet parse merges slots into the existing
; CommandSet, so slots 1 and 2 MUST be rewritten or Spy Satellite remains
; from CommandSet_ZZZZ_SpySatelliteRadar.ini. Command_IraqiRadarSearch is
; also last-won away from SPECIAL_SPY_SATELLITE so a leftover slot cannot
; still fire Spy Sat.

CommandSet Iraq_RadarStationCommandSet
  1 = Command_IraqiCamoflage
  2 = Command_Upgrade_MTS
  3 = Command_ConstructIraq_Sarab3
  4 = Command_ConstructIraq_Ababil200
  5 = Command_ConstructIraq_Lamiaa
  6 = Command_ConstructIraqDroneQuds5_AI
  7 = Command_ConstructSpecterRadarHeron
  9 = Command_ConstructSpecterRadarMQ4
  10 = Command_ConstructSpecterRadarOrlan10
  11 = Command_ConstructSpecterRadarShahedLauncher
  14 = Command_Sell
  15 = Command_ConstructIraqDroneQuds5_AI
End

CommandButton Command_IraqiRadarSearch
  Command           = STOP
  TextLabel         = CONTROLBAR:Stop
  ButtonImage       = SSStop
  ButtonBorderType  = ACTION
  DescriptLabel     = CONTROLBAR:TooltipStop
End
"""

COMMANDSET_SUPPLY = """\
; SPECTER last-win. In-building buy lists for France / America / China / Russia.
; Pattern matches Israel AirF_AmericaSupplyCenterCommandSet:
;   1 = country UNIT_BUILD, 13 = Rally, 14 = Sell
; Both core CommandSet.ini names and overlay *_CountryIncome aliases are
; last-won so either building assignment still shows the buy button.
; Russia slot 2 is overwritten (CommandSet merge would otherwise keep Mi-8).

CommandSet FranceSupplyCenterCommandSet
  1 = Command_ConstructFranceHelicopterCH47F
 13 = Command_SetRallyPoint
 14 = Command_Sell
End

CommandSet AmericaSupplyCenterCommandSet
  1 = Command_ConstructAmericaSupplyChinook_USA
 13 = Command_SetRallyPoint
 14 = Command_Sell
 16 = Command_ConstructAmericaVehicleM-ATV_AI
End

CommandSet AmericaSupplyCenterCommandSet_CountryIncome
  1 = Command_ConstructAmericaSupplyChinook_USA
 13 = Command_SetRallyPoint
 14 = Command_Sell
 16 = Command_ConstructAmericaVehicleM-ATV_AI
End

CommandSet ChinaSupplyCenterCommandSet
  1 = Command_ConstructChinaVehicleSupplyTruck
 13 = Command_SetRallyPoint
 14 = Command_Sell
End

CommandSet ChinaSupplyCenterCommandSet_CountryIncome
  1 = Command_ConstructChinaVehicleSupplyTruck
 13 = Command_SetRallyPoint
 14 = Command_Sell
End

CommandSet RussiaSupplyCenterCommandSet
  1 = Command_ConstructRussiaSupplyTruck_CountryIncome
  2 = Command_SetRallyPoint
 13 = Command_SetRallyPoint
 14 = Command_Sell
End

CommandSet RussiaSupplyCenterCommandSet_CountryIncome
  1 = Command_ConstructRussiaSupplyTruck_CountryIncome
  2 = Command_SetRallyPoint
 13 = Command_SetRallyPoint
 14 = Command_Sell
End
"""

COMMANDBUTTON_SUPPLY = """\
; SPECTER last-win. USA Chinook + Russia truck UNIT_BUILD buttons.
; Core CommandButton.ini already has France CH47F and China truck.

CommandButton Command_ConstructAmericaSupplyChinook_USA
  Command       = UNIT_BUILD
  Object        = AmericaSupplyChinook_USA
  TextLabel     = CONTROLBAR:ConstructAmericaVehicleChinook
  ButtonImage   = SAChinook
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipUSABUildChinook
End

CommandButton Command_ConstructRussiaSupplyTruck_CountryIncome
  Command       = UNIT_BUILD
  Object        = RussiaSupplyTruck_CountryIncome
  TextLabel     = CONTROLBAR:ConstructChinaVehicleSupplyTruck
  ButtonImage   = SNSupplyTruck
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipChinaBuildSupplyTruck
End
"""


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def validate(file_map: dict[str, bytes]) -> None:
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _req(cs_src == CS_IRAQ, f"Iraq CS last-win moved to {cs_src}")
    sl = slots(cs)
    for btn in SPY_BUTTONS:
        _req(btn not in sl.values(), f"Iraq CS slot still {btn}: {sl}")
    _req(sl.get("1") != "Command_SpySatelliteScan", "slot 1 still Spy Sat")
    _req(sl.get("2") != "Command_SpecterSpySatelliteFee", "slot 2 still Spy Sat fee")
    _req("Command_Sell" in sl.values(), "Iraq CS lost Sell")

    btn_src, btn = last_win_block(file_map, "CommandButton", "Command_IraqiRadarSearch")
    _req(bool(btn) and "SpecialPowerIraqiRadarSearch" not in btn, f"Command_IraqiRadarSearch still Spy Sat ({btn_src})")
    _req("SSSpySat" not in (btn or ""), "Command_IraqiRadarSearch still uses SSSpySat")

    obj_src, obj = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(obj_src == OBJ_IRAQ, f"Iraq object last-win moved to {obj_src}")
    ru = re.search(r"Behavior\s*=\s*RadarUpgrade.*?End", obj or "", re.S)
    _req(bool(ru) and "TriggeredBy" in ru.group(0) and "Upgrade_AmericaRadar" in ru.group(0), "Iraq RadarUpgrade TriggeredBy lost")
    _req("DisableProof" in (ru.group(0) if ru else ""), "Iraq RadarUpgrade DisableProof lost")
    guc = re.search(r"Behavior\s*=\s*GrantUpgradeCreate.*?End", obj or "", re.S)
    _req(bool(guc) and "Upgrade_AmericaRadar" in guc.group(0) and "UNDER_CONSTRUCTION" in guc.group(0), "Iraq GrantUpgradeCreate lost")

    spy_src, spy = last_win_block(file_map, "CommandButton", "Command_SpySatelliteScan")
    _req(bool(spy) and "SpecialPowerSpySatellite" in spy, "Command_SpySatelliteScan broken for other countries")
    for other in (
        "AmericaRadarStationCommandSet",
        "ChinaRadarStationCommandSet",
        "RussiaRadarStationCommandSet",
        "Japan_RadarStationCommandSet",
    ):
        _, body = last_win_block(file_map, "CommandSet", other)
        _req(bool(body) and "Command_SpySatelliteScan" in body, f"{other} lost Spy Sat")

    # Israel reference must stay untouched.
    isr_src, isr = last_win_block(file_map, "Object", "AirF_AmericaSupplyCenter")
    _req(isr_src and "Israel Defense Forces" in (isr_src or ""), f"Israel AirF Supply last-win moved to {isr_src}")
    _req("AirF_AmericaSupplyCenterCommandSet" in (isr or ""), "Israel AirF lost its CommandSet")
    _, isr_cs = last_win_block(file_map, "CommandSet", "AirF_AmericaSupplyCenterCommandSet")
    isr_sl = slots(isr_cs)
    _req(isr_sl.get("1") == "AirF_Command_ConstructAFGChinook", f"Israel AirF slot 1 changed: {isr_sl}")
    _req(isr_sl.get("13") == "Command_SetRallyPoint", "Israel AirF lost Rally")
    _req(isr_sl.get("14") == "Command_Sell", "Israel AirF lost Sell")

    expected_unit = {
        "FranceHelicopterCH47F": ("France", "ChinookAIUpdate"),
        "AmericaSupplyChinook_USA": ("America", "ChinookAIUpdate"),
        "ChinaVehicleSupplyTruck": ("China", "SupplyTruckAIUpdate"),
        "RussiaSupplyTruck_CountryIncome": ("Russia", "SupplyTruckAIUpdate"),
    }
    for bldg, csname in CORE_COMMANDSETS.items():
        src, body = last_win_block(file_map, "Object", bldg)
        _req(bool(body), f"missing {bldg}")
        _req("zzzzz_SpecterSupplyCentreBuy" in (src or ""), f"{bldg} last-win not zzzzz ({src})")
        _req(f"CommandSet       = {csname}" in body or f"CommandSet = {csname}" in body, f"{bldg} CommandSet is not {csname}")
        _req("SupplyCenterDockUpdate" in body, f"{bldg} lost dock")
        _req("SupplyCenterProductionExitUpdate" in body, f"{bldg} lost exit")
        _req("ProductionUpdate" in body, f"{bldg} lost ProductionUpdate")

    for unit, (side, ai) in expected_unit.items():
        src, body = last_win_block(file_map, "Object", unit)
        _req(bool(body), f"missing Object {unit}")
        side_m = re.search(r"(?im)^\s*Side\s*=\s*(\S+)", body)
        _req(bool(side_m) and side_m.group(1) == side, f"{unit} Side not {side} ({src})")
        _req(ai in body, f"{unit} lost {ai}")
        _req("HARVESTER" in body, f"{unit} lost HARVESTER")

    usa_src, usa = last_win_block(file_map, "Object", "AmericaSupplyChinook_USA")
    _req("zzzzz_SpecterSupplyCentreBuy" in (usa_src or ""), f"USA Chinook last-win moved to {usa_src}")
    prereq = re.search(r"(?is)^\s*Prerequisites\s*(.*?)^\s*End", usa or "", re.M)
    _req(bool(prereq), "USA Chinook lost Prerequisites block")
    _req(re.search(r"(?m)^\s*Object\s*=\s*AmericaSupplyCenter\s*$", prereq.group(1)) is None, "USA Chinook still has active Supply Centre prerequisite")

    country_cs = {
        "AmericaSupplyCenterCommandSet": "Command_ConstructAmericaSupplyChinook_USA",
        "AmericaSupplyCenterCommandSet_CountryIncome": "Command_ConstructAmericaSupplyChinook_USA",
        "ChinaSupplyCenterCommandSet": "Command_ConstructChinaVehicleSupplyTruck",
        "ChinaSupplyCenterCommandSet_CountryIncome": "Command_ConstructChinaVehicleSupplyTruck",
        "RussiaSupplyCenterCommandSet": "Command_ConstructRussiaSupplyTruck_CountryIncome",
        "RussiaSupplyCenterCommandSet_CountryIncome": "Command_ConstructRussiaSupplyTruck_CountryIncome",
        "FranceSupplyCenterCommandSet": "Command_ConstructFranceHelicopterCH47F",
    }
    for csname, buy in country_cs.items():
        src, body = last_win_block(file_map, "CommandSet", csname)
        _req(src in {CS_SUPPLY, CS_SUPPLY_LATER}, f"{csname} last-win moved to {src}")
        slc = merged_slots(file_map, csname)
        _req(slc.get("1") == buy, f"{csname} slot 1 is {slc.get('1')} not {buy}")
        _req(slc.get("13") == "Command_SetRallyPoint", f"{csname} missing Rally")
        _req(slc.get("14") == "Command_Sell", f"{csname} missing Sell")
        if "Russia" in csname:
            _req(slc.get("2") != "Command_ConstructRussiaHelicopterMi8AMTSh", "Russia slot 2 still Mi-8")
            _req("Command_ConstructRussiaHelicopterMi8AMTSh" not in slc.values(), "Russia CS still sells Mi-8")

    for country, (btn_name, obj_name) in BUY_BUTTONS.items():
        bsrc, bbody = last_win_block(file_map, "CommandButton", btn_name)
        _req(bool(bbody), f"missing button {btn_name}")
        _req("UNIT_BUILD" in bbody, f"{btn_name} is not UNIT_BUILD")
        _req(f"Object        = {obj_name}" in bbody or f"Object = {obj_name}" in bbody, f"{btn_name} Object is not {obj_name}")
        _req("SCRIPT_ONLY" not in bbody, f"{btn_name} is SCRIPT_ONLY")
        _req("OK_FOR_AI_ONLY" not in bbody, f"{btn_name} is AI-only")

    # Prior accepted last-wins
    _, dl = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(bool(dl) and "DamageDealtAtSelfPosition = Yes" in dl, "92N6E last-win lost")
    _, s400abm = last_win_block(file_map, "Weapon", "3x_LRSAM_40N6KMissile_ABM")
    _req(bool(s400abm) and "CRUSH" in s400abm, "S-400 ABM changed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--objects",
        type=Path,
        default=Path("patch/Data/INI/Object/zzzzz_SpecterSupplyCentreBuy"),
    )
    args = ap.parse_args()

    fm = read_big(args.src_big)
    extras: dict[str, bytes] = {
        CS_IRAQ: crlf(COMMANDSET_IRAQ),
        CS_SUPPLY: crlf(COMMANDSET_SUPPLY),
        CS_SUPPLY_LATER: crlf(COMMANDSET_SUPPLY),
        BTN_SUPPLY: crlf(COMMANDBUTTON_SUPPLY),
    }
    for ini in sorted(args.objects.glob("*.ini")):
        extras[rf"{OBJ_DIR}\{ini.name}"] = crlf(ini.read_text(encoding="latin1"))

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
