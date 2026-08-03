#!/usr/bin/env python3
"""Patch AmericaDozerCommandSet in CommandSet.ini: Strategy Center -> Advanced Airfield."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

NEW_LINES = [
    "CommandSet AmericaDozerCommandSet",
    "  1  = Command_ConstructAmericaPowerPlant",
    "  2  = Command_ConstructAmerica_AdvancedAirBase",
    "  3  = Command_ConstructAmericaBarracks",
    "  4  = Command_ConstructAmericaPatriotPAC3MSE",
    "  5  = Command_ConstructAmericaSupplyCenter",
    "  6  = Command_ConstructAmericaRadarStation",
    "  7  = Command_ConstructAmericaPatriotBattery",
    "  8  = Command_ConstructAmericaCommandCenter",
    "  9  = Command_ConstructAmericaFireBase",
    " 10  = Command_ConstructAmerica_MIM104F",
    " 11  = Command_ConstructAmericaWarFactory_T",
    " 12  = Command_ConstructAmericaLgm30",
    " 13  = Command_ConstructAmericaAirfield_T",
    " 14  = Command_DisarmMinesAtPosition",
    " 15  = Command_ConstructAmerica_AdvancedAirBase",
    " 16  = Command_ConstructAmericaVehicleTHAAD_AI",
    " 17  = Command_ConstructAmericaWarFactory",
    " 18  = Command_ConstructAmericaAirfield",
    "End",
    "",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("commandset_ini", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    text = args.commandset_ini.read_bytes().decode("utf-8")
    m = re.search(r"^CommandSet AmericaDozerCommandSet\b.*?(?=^CommandSet |\Z)", text, re.S | re.M)
    if not m:
        raise SystemExit("AmericaDozerCommandSet not found")
    nl = "\r\n" if "\r\n" in text else "\n"
    # real newlines detection
    nl = "
" if "
" in text else "
"
    block = nl.join(NEW_LINES)
    out = text[: m.start()] + block + text[m.end() :]
    dest = args.output or args.commandset_ini
    dest.write_bytes(out.encode("ascii"))
    print("patched", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
