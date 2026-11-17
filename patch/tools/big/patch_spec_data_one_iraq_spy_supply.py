#!/usr/bin/env python3
"""Phase follow-up: clear Iraq radar Spy Sat slots + restore Supply Centre spawn.

Iraq Spy Sat still visible after the previous DATA rebuild because SAGE
CommandSet parse MERGES slots into the existing CommandSet object. The
last-win file omitted slots 1 and 2, so CommandSet_ZZZZ_SpySatelliteRadar.ini
kept Command_SpySatelliteScan + Command_SpecterSpySatelliteFee. RadarUpgrade
TriggeredBy is left untouched.

Supply Centre: PR #694 last-won buy buttons only. SPEC same-path
SupplyCenter.ini still SpawnBehavior-spawns AmericaVehicleChinook (France)
and ChinaVehicleSupplyTruck (Russia) — wrong Side — so the unit that
actually leaves the building cannot serve that player. Overlay
0_SPECTER_CountrySupplyIncome already has the designed spawn templates.
This packs those building last-wins on a later unique path and removes
Russia Mi-8 (not a HARVESTER) from the buy list by overwriting slot 2.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
CS_SUPPLY = r"Data\INI\CommandSet_ZZZZ_ZZZZSupplyCentreBuy.ini"
BTN_SUPPLY = r"Data\INI\CommandButton_ZZZZ_ZZZZSupplyCentreBuy.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_DIR = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"

SPY_BUTTONS = (
    "Command_SpySatelliteScan",
    "Command_SpecterSpySatelliteFee",
    "Command_IraqiRadarSearch",
)


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
; SPECTER last-win. Buy lists for France / America / China / Russia.
; Russia slot 2 overwritten (was Mi-8, not a HARVESTER).

CommandSet FranceSupplyCenterCommandSet
  1 = Command_ConstructFranceHelicopterCH47F
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
    for tok in (
        "SpecialPowerSpySatellite",
        "SUPERWEAPON_SpySatellite",
        "SpecialPowerIraqiRadarSearch",
        "SUPERWEAPON_IraqiRadarScan",
        "P30_Radar_Deploy_St",
    ):
        _req(tok not in (obj or ""), f"Iraq object regained {tok}")

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

    expected_spawn = {
        "FranceSupplyCenter": ("FranceHelicopterCH47F", "FranceSupplyCenterCommandSet"),
        "AmericaSupplyCenter": ("AmericaSupplyChinook_USA", None),
        "ChinaSupplyCenter": ("ChinaVehicleSupplyTruck", None),
        "RussiaSupplyCenter": ("RussiaSupplyTruck_CountryIncome", None),
    }
    expected_unit = {
        "FranceHelicopterCH47F": ("France", "ChinookAIUpdate"),
        "AmericaSupplyChinook_USA": ("America", "ChinookAIUpdate"),
        "ChinaVehicleSupplyTruck": ("China", "SupplyTruckAIUpdate"),
        "RussiaSupplyTruck_CountryIncome": ("Russia", "SupplyTruckAIUpdate"),
    }
    for bldg, (spawn, csname) in expected_spawn.items():
        src, body = last_win_block(file_map, "Object", bldg)
        _req(bool(body), f"missing {bldg}")
        _req(OBJ_DIR.replace("\\", "").lower() in (src or "").replace("\\", "").lower() or "zzzzz_SpecterSupplyCentreBuy" in (src or ""), f"{bldg} last-win not zzzzz ({src})")
        _req(f"SpawnTemplateName = {spawn}" in body, f"{bldg} spawn is not {spawn}")
        _req("SupplyCenterDockUpdate" in body, f"{bldg} lost dock")
        _req("SupplyCenterProductionExitUpdate" in body, f"{bldg} lost exit")
        _req("ProductionUpdate" in body, f"{bldg} lost ProductionUpdate")
        if csname:
            _req(csname in body, f"{bldg} lost CommandSet {csname}")

    for unit, (side, ai) in expected_unit.items():
        src, body = last_win_block(file_map, "Object", unit)
        _req(bool(body), f"missing Object {unit}")
        side_m = re.search(r"(?im)^\s*Side\s*=\s*(\S+)", body)
        _req(bool(side_m) and side_m.group(1) == side, f"{unit} Side not {side} ({src})")
        _req(ai in body, f"{unit} lost {ai}")
        _req("HARVESTER" in body, f"{unit} lost HARVESTER")

    rus_src, rus = last_win_block(file_map, "CommandSet", "RussiaSupplyCenterCommandSet")
    _req("Command_ConstructRussiaHelicopterMi8AMTSh" not in (rus or ""), "Russia CS still sells Mi-8")
    _req("Command_ConstructRussiaSupplyTruck_CountryIncome" in (rus or ""), "Russia CS lost truck")
    slr = slots(rus)
    _req(slr.get("2") != "Command_ConstructRussiaHelicopterMi8AMTSh", "Russia slot 2 still Mi-8")

    _, fr = last_win_block(file_map, "CommandSet", "FranceSupplyCenterCommandSet")
    _req("Command_ConstructFranceHelicopterCH47F" in (fr or ""), "France CS lost CH47F")

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
    }
    for ini in sorted(args.objects.glob("*.ini")):
        extras[rf"{OBJ_DIR}\{ini.name}"] = crlf(ini.read_text(encoding="latin1"))

    changed = []
    for name, body in extras.items():
        prev = fm.get(name)
        fm[name] = body
        changed.append(("update" if prev is not None else "add", name))

    # Keep existing packed harvester objects (already in src BIG).
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
