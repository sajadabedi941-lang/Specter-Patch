#!/usr/bin/env python3
"""Ship loose CommandButton.ini so factory slot M is on the live ControlBar path.

Cause (PR #713 crash):
  Dialog: Data/INI/CommandSet.ini / CommandSet Iraq_AlFahdMissileFactoryCommandSet
  #713 CommandSet.ini (loose, first-win) sets Iraq slot 13 = CB_FACTORY_SLOT_M.
  That button exists only at EOF of DATA BIG CommandButton.ini.
  ControlBar::init opens Data\\INI\\CommandButton.ini with archive first-win
  (INIZH.big sorts before _SPEC_DATA_ONE.big). The DATA copy is never opened.
  parseCommandSetDefinition looks up each slot button; missing name throws
  INI_INVALID_DATA and the dialog names the CommandSet being parsed.
  Iraq_AlFahdMissileFactoryCommandSet is the first factory set in the file
  that references CB_FACTORY_SLOT_M, so it is the name on the crash.

#712 Iraq slot 13 was still CB_MISSILE_M (already in the live/INIZH table).
#713 replaced that known button with CB_FACTORY_SLOT_M.

Fix: same overlay as #710 CommandSet.ini — write the live Specter
CommandButton.ini (the #713 DATA copy, including K/L/M/N) as loose
Data\\INI\\CommandButton.ini. LocalFileSystem beats every BIG.
DATA BIG and CommandSet.ini are unchanged from #713.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/MISSILE_FACTORY_M_RS24/_SPEC_DATA_ONE.big"
SRC_SHA = "d5a8ed982e7ff37de1fa9923f1ee96abe16312f481f563891d95e1b4dffb26c8"
OUT_DIR = ROOT / "Release/IRAQ_FACTORY_CS_CRASH"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"

FACTORY_SETS = [
    "America_MissileFactoryCommandSet",
    "Britain_MissileFactoryCommandSet",
    "China_MissileFactoryCommandSet",
    "France_MissileFactoryCommandSet",
    "Germany_MissileFactoryCommandSet",
    "India_MissileFactoryCommandSet",
    "Iran_MissileFactoryCommandSet",
    "Israel_MissileFactoryCommandSet",
    "Italy_MissileFactoryCommandSet",
    "Japan_MissileFactoryCommandSet",
    "Libya_MissileFactoryCommandSet",
    "NorthKorea_MissileFactoryCommandSet",
    "Pakistan_MissileFactoryCommandSet",
    "Russia_MissileFactoryCommandSet",
    "SaudiArabia_MissileFactoryCommandSet",
    "SouthAfrica_MissileFactoryCommandSet",
    "SouthKorea_MissileFactoryCommandSet",
    "Spain_MissileFactoryCommandSet",
    "Sweden_MissileFactoryCommandSet",
    "Syria_MissileFactoryCommandSet",
    "Turkey_MissileFactoryCommandSet",
    "UAE_MissileFactoryCommandSet",
    "Ukraine_MissileFactoryCommandSet",
    "Vietnam_MissileFactoryCommandSet",
    "Iraq_AlFahdMissileFactoryCommandSet",
]


def slots_of(cs_text: str, name: str) -> dict[int, str]:
    m = re.search(
        rf"^CommandSet {re.escape(name)}\s*\r?\n(.*?)(?=^CommandSet |\Z)",
        cs_text,
        re.M | re.S,
    )
    if not m:
        raise SystemExit(f"VALIDATE FAIL: missing CS {name}")
    return {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(1), re.M)}


def button_names(cb_text: str) -> set[str]:
    return set(re.findall(r"^CommandButton (\S+)", cb_text, re.M))


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def validate(entries: dict[str, bytes]) -> list[str]:
    cs = entries[K_CS].decode("latin1")
    cb = entries[K_CB].decode("latin1")
    names = button_names(cb)
    notes: list[str] = []
    require("CommandButton CB_FACTORY_SLOT_M" in cb, "M button missing from CommandButton.ini")
    require("Object        = Factory_RS24YarsOnce" in cb, "M button object wrong")
    require("CommandButton CB_FACTORY_SLOT_K" in cb, "K button missing")
    require("CommandButton CB_FACTORY_SLOT_L" in cb, "L button missing")
    require("CommandButton CB_FACTORY_SLOT_N" in cb, "N button missing")
    require("CommandSet IranKhorramshahrFireCommandSet" in cs, "lost #710 Khormshar fire")
    require("CommandSet IranShahed136FireCommandSet" in cs, "lost #710 Shahed fire")
    require("CommandSet FactoryOnceFireCommandSet" in cs, "lost factory fire CS")
    iraq = slots_of(cs, "Iraq_AlFahdMissileFactoryCommandSet")
    require(iraq[11] == "CB_MISSILE_K", "Iraq K")
    require(iraq[12] == "CB_FACTORY_SLOT_L", "Iraq L")
    require(iraq[13] == "CB_FACTORY_SLOT_M", "Iraq M")
    require(iraq[14] == "CB_FACTORY_SLOT_N", "Iraq N")
    for i in range(1, 11):
        require(iraq[i] == f"CB_MISSILE_{chr(ord('A') + i - 1)}", f"Iraq A-J slot {i}")
        require(iraq[i] in names, f"Iraq button {iraq[i]} not in CommandButton.ini")
    missing: list[str] = []
    for set_name in FACTORY_SETS:
        sl = slots_of(cs, set_name)
        if set_name != "Iraq_AlFahdMissileFactoryCommandSet":
            require(sl[11] == "CB_FACTORY_SLOT_K", f"{set_name} K")
            require(not sl[1].startswith("CB_MISSILE_"), f"{set_name} imported Iraq A")
        require(sl[13] == "CB_FACTORY_SLOT_M", f"{set_name} M")
        for btn in sl.values():
            if btn not in names:
                missing.append(f"{set_name}:{btn}")
    require(not missing, "buttons missing from CommandButton.ini: " + ", ".join(missing[:8]))
    notes.append(f"factory_sets={len(FACTORY_SETS)}")
    notes.append("iraq_A_J_preserved=yes")
    notes.append("slot_m=CB_FACTORY_SLOT_M")
    notes.append("loose_commandbutton=yes")
    return notes


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != SRC_SHA:
        raise SystemExit(f"source BIG sha mismatch: {digest}")
    entries = read_big(SRC_BIG)
    notes = validate(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIG.write_bytes(blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    cs = entries[K_CS]
    cb = entries[K_CB]
    (OUT_DIR / "CommandSet.ini").write_bytes(cs)
    (OUT_DIR / "CommandSet.ini.sha256").write_text(
        hashlib.sha256(cs).hexdigest() + "\n", encoding="ascii"
    )
    (OUT_DIR / "CommandButton.ini").write_bytes(cb)
    (OUT_DIR / "CommandButton.ini.sha256").write_text(
        hashlib.sha256(cb).hexdigest() + "\n", encoding="ascii"
    )
    print("copied BIG", len(blob), digest)
    print("CommandSet.ini", len(cs), hashlib.sha256(cs).hexdigest())
    print("CommandButton.ini", len(cb), hashlib.sha256(cb).hexdigest())
    for n in notes:
        print(" ", n)


if __name__ == "__main__":
    main()
