#!/usr/bin/env python3
"""Fix ZH parse crash at CommandSet GermanyAirfieldCommandSet.

CommandSet.ini references Command_ConstructGermanyJet* buttons that were
never defined. Objects already exist. This only repairs CommandSet syntax
and CommandButton references. No Object/Weapon/Armor/Locomotor/ART/CSF/cost
changes.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_national_ground_forces import build_big_ordered, construct_button, last_named, norm, parse_big
from national_ground_roster import LOCKED_BIG_PATHS

SRC_DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_commandbar/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_commandbar")

GERMANY_AIRFIELD_BUTTONS = (
    ("Command_ConstructGermanyJetTyphoonT4", "GermanyJetTyphoonT4", "SPEC_GermanyTyphoonT4"),
    ("Command_ConstructGermanyJetTyphoonECR", "GermanyJetTyphoonECR", "SPEC_GermanyTyphoonECR"),
    ("Command_ConstructGermanyJetTornadoADV", "GermanyJetTornadoADV", "SPEC_GermanyTornadoADV"),
    ("Command_ConstructGermanyJetF35A", "GermanyJetF35A", "SPEC_GermanyF35A"),
    ("Command_ConstructGermanyJetMiG29G", "GermanyJetMiG29G", "SPEC_GermanyMiG29G"),
    ("Command_ConstructGermanyJetTornadoIDS", "GermanyJetTornadoIDS", "SPEC_GermanyTornadoIDS"),
    ("Command_ConstructGermanyJetF4F", "GermanyJetF4F", "SPEC_GermanyF4F"),
    ("Command_ConstructGermanyJetAlphaJet", "GermanyJetAlphaJet", "SPEC_GermanyAlphaJet"),
    ("Command_ConstructGermanyJetMako", "GermanyJetMako", "SPEC_GermanyMako"),
    # Same missing-ref class on later Germany air bars in CommandSet.ini
    ("Command_ConstructGermanyJetA400M", "GermanyJetA400M", "SPEC_GermanyA400M"),
    ("Command_ConstructGermanyJetC130J", "GermanyJetC130J", "SPEC_GermanyC130J"),
    ("Command_ConstructGermanyAircraftE3", "GermanyAircraftE3", "SPEC_GermanyE3"),
    ("Command_ConstructGermanyDroneHeronTP", "GermanyDroneHeronTP", "SPEC_GermanyHeronTP"),
    ("Command_ConstructGermanyHelicopterTigerUHT", "GermanyHelicopterTigerUHT", "SPEC_GermanyTigerUHT"),
    ("Command_ConstructGermanyHelicopterNH90", "GermanyHelicopterNH90", "SPEC_GermanyNH90"),
    ("Command_ConstructGermanyHelicopterCH53", "GermanyHelicopterCH53", "SPEC_GermanyCH53"),
    ("Command_ConstructGermanyHelicopterH145M", "GermanyHelicopterH145M", "SPEC_GermanyH145M"),
)


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def index_named(entries, kind: str) -> set[str]:
    found = set()
    for n, blob in entries:
        if not n.lower().endswith(".ini"):
            continue
        found.update(re.findall(rf"(?m)^{kind}\s+(\S+)\s*$", blob.decode("latin1")))
    return found


def repair_commandset_ini(text: str) -> str:
    # Separate the CRLF War Factory End from the LF Airfield header.
    old = "End\r\nCommandSet GermanyAirfieldCommandSet"
    new = "End\r\n\r\nCommandSet GermanyAirfieldCommandSet"
    if old in text:
        text = text.replace(old, new, 1)
        print("inserted blank line before GermanyAirfieldCommandSet")
    elif "CommandSet GermanyAirfieldCommandSet" not in text:
        raise SystemExit("GermanyAirfieldCommandSet missing from CommandSet.ini")
    else:
        print("GermanyAirfieldCommandSet header already separated")
    return text


def append_missing_buttons(text: str, existing_buttons: set[str], existing_objects: set[str]) -> str:
    chunks = []
    for btn, obj, image in GERMANY_AIRFIELD_BUTTONS:
        if btn in existing_buttons:
            print("button exists", btn)
            continue
        if obj not in existing_objects:
            raise SystemExit(f"refusing to create button {btn}: object {obj} missing")
        chunks.append(
            construct_button(
                btn,
                obj,
                f"CONTROLBAR:Construct{obj}",
                f"CONTROLBAR:ToolTip{obj}",
                image,
            )
        )
        existing_buttons.add(btn)
        print("add button", btn, "->", obj, image)
    if not chunks:
        return text
    if not text.endswith("\n"):
        text += "\r\n"
    return text + "\r\n" + "\r\n".join(chunks)


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing CommandBar packed BIG", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    src_names = [n for n, _ in data_entries]
    data_index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    src_map = {norm(n): b for n, b in data_entries}

    existing_buttons = index_named(data_entries, "CommandButton")
    existing_objects = index_named(data_entries, "Object")

    cs_key = norm(r"Data\INI\CommandSet.ini")
    i = data_index[cs_key]
    old = data_entries[i][1].decode("latin1")
    new = repair_commandset_ini(old)
    if new != old:
        data_entries[i] = (data_entries[i][0], new.encode("latin1"))
        print("patched CommandSet.ini delta", len(new) - len(old))

    cb_key = norm(r"Data\INI\CommandButton.ini")
    i = data_index[cb_key]
    old = data_entries[i][1].decode("latin1")
    new = append_missing_buttons(old, existing_buttons, existing_objects)
    if new != old:
        data_entries[i] = (data_entries[i][0], new.encode("latin1"))
        print("patched CommandButton.ini delta", len(new) - len(old))

    locked = {norm(p) for p in LOCKED_BIG_PATHS}
    for n, b in data_entries:
        if norm(n) in locked and src_map.get(norm(n)) != b:
            raise SystemExit(f"locked file changed {n}")
        if n.lower().endswith(".ini") and "\\object\\" in n.replace("/", "\\").lower():
            if b != src_map.get(norm(n)):
                raise SystemExit(f"object INI changed {n}")
    if [n for n, _ in data_entries] != src_names:
        raise SystemExit("DATA entry names/order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    if Path(SRC_ART).resolve() != (OUT_DIR / "_SPEC_ART_ONE.big").resolve():
        shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256((OUT_DIR / "_SPEC_ART_ONE.big").read_bytes()).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
