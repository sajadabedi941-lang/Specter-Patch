#!/usr/bin/env python3
"""Verify USA Air Force DATA chain after INIZH.big wins CommandSet.ini / CommandButton.ini."""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

INIZH_BUTTONS = {
    "Command_ConstructAmericaJetRaptor",
    "Command_ConstructAmericaVehicleComanche",
    "Command_ConstructAmericaJetAurora",
    "Command_ConstructAmericaJetStealthFighter",
    "Command_UpgradeComancheRocketPods",
    "Command_UpgradeAmericaLaserMissiles",
    "Command_UpgradeAmericaCountermeasures",
    "Command_UpgradeAmericaBunkerBusters",
    "Command_SetRallyPoint",
    "Command_Sell",
    "Command_ConstructAmericaDozer",
    "Command_SpectreGunship",
    "Command_LeafletDrop",
    "Command_A10ThunderboltMissileStrike",
    "Command_Paradrop",
    "Command_SpyDrone",
    "Command_EmergencyRepair",
    "Command_DaisyCutter",
    "Command_SpySatelliteScan",
}

INIZH_AIRFIELD = [
    "Command_ConstructAmericaJetRaptor",
    "Command_ConstructAmericaVehicleComanche",
    "Command_ConstructAmericaJetAurora",
    "Command_ConstructAmericaJetStealthFighter",
    "Command_UpgradeComancheRocketPods",
    "Command_UpgradeAmericaLaserMissiles",
    "Command_UpgradeAmericaCountermeasures",
    "Command_UpgradeAmericaBunkerBusters",
    "Command_SetRallyPoint",
    "Command_Sell",
]

INIZH_CC = [
    "Command_ConstructAmericaDozer",
    "Command_SpectreGunship",
    "Command_LeafletDrop",
    "Command_A10ThunderboltMissileStrike",
    "Command_Paradrop",
    "Command_SpyDrone",
    "Command_EmergencyRepair",
    "Command_DaisyCutter",
    "Command_SpySatelliteScan",
    "Command_SetRallyPoint",
    "Command_Sell",
]

FORBIDDEN_REDEFINE = INIZH_BUTTONS | {
    "AmericaAirfieldCommandSet",
    "AmericaCommandCenterCommandSet",
}

KNOWN_OBJECTS = {
    "AmericaJetRaptor",
    "AmericaVehicleComanche",
    "AmericaJetAurora",
    "AmericaJetStealthFighter",
    "AmericaJetA10C",
    "AmericaJetF-16C_AG",
    "AmericaJetF-15E_AA",
    "AmericaJetF-22A_AA",
    "AmericaJetF35C",
    "AmericaJetF35C_AA",
    "AmericaJetAuterF22",
    "AmericaJetV22Visual",
    "AmericaJetEA18G",
    "AmericaHelicopterUH60",
    "AmericaJetF117Clean",
    "AmericaJetB52H",
    "AmericaJetB1R",
    "AmericaJetB2Spirit",
    "AmericaJetB21Clean",
    "AmericaDozer",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="latin1", errors="replace")


def blocks(text: str, kind: str) -> dict[str, str]:
    out: dict[str, str] = {}
    pat = re.compile(rf"^{kind}\s+(\S+)\s*$", re.M)
    matches = list(pat.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end]
        em = re.search(r"^End\s*$", chunk, re.M)
        out[m.group(1)] = chunk[: em.end()] if em else chunk
    return out


def slot_buttons(block: str) -> list[str]:
    return re.findall(r"^\s*\d+\s*=\s*(\S+)", block, re.M)


def button_object(block: str) -> str | None:
    m = re.search(r"^\s*Object\s*=\s*(\S+)", block, re.M)
    return m.group(1) if m else None


def button_upgrade(block: str) -> str | None:
    m = re.search(r"^\s*Upgrade\s*=\s*(\S+)", block, re.M)
    return m.group(1) if m else None


def big_map(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace").replace("/", "\\")
        pos = end + 1
        out[name.lower()] = data[off : off + size]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch-ini", type=Path, default=Path("patch/Data/INI"))
    ap.add_argument("--data-big", type=Path, default=None)
    args = ap.parse_args()

    errors: list[str] = []
    notes: list[str] = []

    cs = read_text(args.patch_ini / "CommandSet_USA_AirForce.ini")
    cb = read_text(args.patch_ini / "CommandButton_USA_AirForce.ini")
    sets = blocks(cs, "CommandSet")
    buttons = blocks(cb, "CommandButton")

    for name in FORBIDDEN_REDEFINE:
        if name in buttons or name in sets:
            errors.append(f"redefines INIZH name: {name}")

    required_sets = [
        "AmericaAirfieldCommandSet_USAAirForce",
        "AmericaCommandCenterCommandSet_USAAirForce",
        "America_LargeAirBaseCommandSet",
    ]
    for name in required_sets:
        if name not in sets:
            errors.append(f"missing CommandSet {name}")

    air = sets.get("AmericaAirfieldCommandSet_USAAirForce", "")
    cc = sets.get("AmericaCommandCenterCommandSet_USAAirForce", "")
    hangar = sets.get("America_LargeAirBaseCommandSet", "")
    air_btns = slot_buttons(air)
    cc_btns = slot_buttons(cc)
    hangar_btns = slot_buttons(hangar)

    if len(air_btns) < 10:
        errors.append(f"airfield CommandSet empty/too small: {air_btns}")
    if len(cc_btns) < 11:
        errors.append(f"command center CommandSet empty/too small: {cc_btns}")
    if len(hangar_btns) < 14:
        errors.append(f"hangar CommandSet empty/too small: {hangar_btns}")

    for b in INIZH_AIRFIELD:
        if b not in air_btns:
            errors.append(f"airfield missing working INIZH button {b}")
    for b in INIZH_CC:
        if b not in cc_btns:
            errors.append(f"command center missing working INIZH button {b}")

    extras = {
        "Command_ConstructAmericaJetF35C_AA": "airfield",
        "Command_ConstructAmerica_AuterF22": "airfield",
        "Command_ConstructAmericaJetV22Visual": "airfield",
        "Command_ConstructAmerica_B21A": "hangar",
        "Command_UpgradeAmerica_AirForceBombs": "cc",
    }
    for b, where in extras.items():
        pool = {"airfield": air_btns, "hangar": hangar_btns, "cc": cc_btns}[where]
        if b not in pool:
            errors.append(f"{where} missing extra slot {b}")

    if "Command_ConstructAmericaJetF117" not in hangar_btns:
        errors.append("hangar dropped existing heavy Command_ConstructAmericaJetF117")
    if "Command_ConstructAmericaJetEA18" not in hangar_btns:
        errors.append("hangar dropped existing heavy Command_ConstructAmericaJetEA18")

    all_set_buttons = air_btns + cc_btns + hangar_btns
    for b in all_set_buttons:
        if b in INIZH_BUTTONS:
            continue
        if b not in buttons:
            errors.append(f"CommandSet references undefined button {b}")

    for name, block in buttons.items():
        obj = button_object(block)
        upg = button_upgrade(block)
        if obj:
            if obj not in KNOWN_OBJECTS:
                errors.append(f"{name} Object={obj} is not a known existing object")
            notes.append(f"OK button {name} -> {obj}")
        elif upg:
            if upg != "Upgrade_America_AirForceBombs":
                errors.append(f"{name} unexpected Upgrade={upg}")
            notes.append(f"OK button {name} -> upgrade {upg}")
        else:
            errors.append(f"{name} has no Object or Upgrade")

    required_objects = {
        "AmericaJetAuterF22": "Command_ConstructAmerica_AuterF22",
        "AmericaJetF35C_AA": "Command_ConstructAmericaJetF35C_AA",
        "AmericaJetB21Clean": "Command_ConstructAmerica_B21A",
        "AmericaJetV22Visual": "Command_ConstructAmericaJetV22Visual",
    }
    for obj, btn in required_objects.items():
        if btn not in all_set_buttons:
            errors.append(f"object {obj} has no CommandSet slot ({btn})")

    airfield_ini = read_text(
        args.patch_ini
        / "Object/Specter/United States Of America/Buildings/Airfield.ini"
    )
    cc_ini = read_text(
        args.patch_ini
        / "Object/Specter/United States Of America/Buildings/CommandCenter.ini"
    )
    hangar_ini = read_text(
        args.patch_ini
        / "Object/Specter/United States Of America/Buildings/America_LargeAirBase.ini"
    )
    v22_ini = read_text(
        args.patch_ini
        / "Object/Specter/United States Of America/AmericaJetV22Visual.ini"
    )

    if "AmericaAirfieldCommandSet_USAAirForce" not in airfield_ini:
        errors.append("Airfield.ini not pointed at AmericaAirfieldCommandSet_USAAirForce")
    if "AmericaCommandCenterCommandSet_USAAirForce" not in cc_ini:
        errors.append("CommandCenter.ini not pointed at AmericaCommandCenterCommandSet_USAAirForce")
    if re.search(r"CommandSet\s*=\s*America_LargeAirBaseCommandSet\s*$", hangar_ini, re.M) is None:
        errors.append("America_LargeAirBase.ini not pointed at America_LargeAirBaseCommandSet")
    if re.search(r"Buildable\s*=\s*Ignore_Prerequisites", v22_ini):
        errors.append("V22 still has Ignore_Prerequisites lock")
    if not re.search(r"Buildable\s*=\s*Yes", v22_ini):
        errors.append("V22 is not Buildable = Yes")

    if args.data_big:
        files = big_map(args.data_big)
        must = [
            r"data\ini\commandset_usa_airforce.ini",
            r"data\ini\commandbutton_usa_airforce.ini",
            r"data\ini\object\specter\united states of america\buildings\airfield.ini",
            r"data\ini\object\specter\united states of america\buildings\commandcenter.ini",
            r"data\ini\object\specter\united states of america\buildings\america_largeairbase.ini",
        ]
        for key in must:
            if key not in files:
                errors.append(f"DATA big missing {key}")
        packed_cs = files.get(r"data\ini\commandset_usa_airforce.ini", b"").decode("latin1", "replace")
        if "AmericaAirfieldCommandSet_USAAirForce" not in packed_cs:
            errors.append("packed CommandSet_USA_AirForce.ini missing airfield set")
        if "Command_ConstructAmericaJetRaptor" not in packed_cs:
            errors.append("packed airfield set missing working Raptor button")
        if "Command_UpgradeAmerica_AirForceBombs" not in packed_cs:
            errors.append("packed CC set missing bomb upgrade extra slot")
        if "Command_ConstructAmerica_B21A" not in packed_cs:
            errors.append("packed hangar set missing B21A extra slot")
        packed_v22 = files.get(
            r"data\ini\object\specter\united states of america\americajetv22visual.ini",
            b"",
        ).decode("latin1", "replace")
        if "Ignore_Prerequisites" in packed_v22:
            errors.append("packed V22 still locked Ignore_Prerequisites")

    print("USA Air Force DATA verify")
    print(f"  airfield slots: {len(air_btns)} {air_btns}")
    print(f"  command center slots: {len(cc_btns)} {cc_btns}")
    print(f"  hangar slots: {len(hangar_btns)} {hangar_btns}")
    print(f"  unique buttons: {len(buttons)}")
    for n in notes:
        print(f"  {n}")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
