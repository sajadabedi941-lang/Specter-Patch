#!/usr/bin/env python3
"""OIL-CAPTURE infantry fix — implement the approved audit only.

Class 1: add Unpause TriggeredBy on seven packed NATO G36 country clones.
Class 2: last-win RepublicanGuard CommandSets for SA/UAE/Libya/SouthAfrica.

Does not rewrite CommandSet.ini / CommandButton.ini / Weapon.ini.
Does not touch Japan / South Korea / Vietnam, USA ranger, or oil objects.
Does not pack a BIG.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

BIG = Path("/workspace/patch/Release/FIGHTER_ROSTER_NEXT14/_SPEC_DATA_ONE.big")
INI = Path("/workspace/patch/Data/INI")

CLASS1 = [
    r"Data\INI\Object\Specter\Swedish Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Infantry\Rifleman_G36.ini",
]

# Exact USA ranger Unpause architecture (donor not modified).
OLD_UNPAUSE = (
    "  Behavior = UnpauseSpecialPowerUpgrade ModuleTag_20\r\n"
    "    SpecialPowerTemplate = SpecialAbilityRangerCaptureBuilding\r\n"
    "  End"
)
NEW_UNPAUSE = (
    "  Behavior = UnpauseSpecialPowerUpgrade ModuleTag_20\r\n"
    "    SpecialPowerTemplate = SpecialAbilityRangerCaptureBuilding\r\n"
    "    TriggeredBy = Upgrade_InfantryCaptureBuilding\r\n"
    "  End"
)

# Iraq / Vietnam last-win rifle CommandSet layout.
CLASS2_SETS = [
    "SaudiArabia_RepublicanGuardCommandSet",
    "UAE_RepublicanGuardCommandSet",
    "Libya_RepublicanGuardCommandSet",
    "SouthAfrica_RepublicanGuardCommandSet",
]
CS_OUT = INI / "CommandSet_ZZZZ_OilCapture_Class2.ini"

FORBIDDEN_PATHS = {
    "japan",
    "southkorea",
    "vietnam",
}


def read_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def ws_path(packed: str) -> Path:
    rel = packed.replace("\\", "/")
    if not rel.lower().startswith("data/ini/"):
        raise SystemExit(f"unexpected path {packed}")
    return INI / rel[len("Data/INI/") :]


def patch_unpause(raw: bytes) -> bytes:
    if NEW_UNPAUSE.encode("latin1") in raw:
        raise SystemExit("TriggeredBy already present")
    if raw.count(OLD_UNPAUSE.encode("latin1")) != 1:
        raise SystemExit("expected exactly one packed Unpause block")
    return raw.replace(OLD_UNPAUSE.encode("latin1"), NEW_UNPAUSE.encode("latin1"), 1)


def main() -> int:
    file_by = {n.replace("/", "\\").lower(): (n, b) for n, b in read_big(BIG)}
    written = []
    for packed in CLASS1:
        low = packed.lower()
        if any(f in low for f in FORBIDDEN_PATHS):
            raise SystemExit(f"refused forbidden path {packed}")
        if low not in file_by:
            raise SystemExit(f"missing from live BIG: {packed}")
        _name, raw = file_by[low]
        new = patch_unpause(raw)
        dest = ws_path(packed)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(new)
        written.append(str(dest))
        print("WROTE", dest)

    lines = [
        "; OIL_CAPTURE Class 2 last-win RepublicanGuard CommandSets\n",
        "; Slot 1 = existing Command_GLAInfantryRebelCaptureBuilding.\n",
        "; Does not rewrite CommandSet.ini. Japan/SK/Vietnam not listed.\n\n",
    ]
    for name in CLASS2_SETS:
        lines.append(f"CommandSet {name}\n")
        lines.append("  1 = Command_GLAInfantryRebelCaptureBuilding\n")
        lines.append("  12 = Command_AttackMove\n")
        lines.append("  13 = Command_Guard\n")
        lines.append("  14 = Command_Stop\n")
        lines.append("End\n\n")
    CS_OUT.write_text("".join(lines).replace("\n", "\r\n"), encoding="latin1", newline="")
    print("WROTE", CS_OUT)
    print("CLASS1", len(CLASS1), "CLASS2", len(CLASS2_SETS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
