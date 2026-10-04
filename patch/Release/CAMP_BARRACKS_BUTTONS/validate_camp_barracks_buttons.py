#!/usr/bin/env python3
"""Static validation: merge live DATA BIG with the Camp/Barracks cameo overlay."""
from __future__ import annotations

import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIG = ROOT / "Release/EUROPEAN_BUILDING_FLAGS_FINAL/_SPEC_DATA_ONE.big"
OVERLAY = Path(__file__).resolve().parent / "payload/Data/INI/CommandButton_ZZZZZ_CampBarracksConstructCameo.ini"
SOURCE = ROOT / "Data/INI/CommandButton_ZZZZZ_CampBarracksConstructCameo.ini"

INI_BLOCK = re.compile(
    r"^(CommandSet|CommandButton|Object|MappedImage|PlayerTemplate)\s+(\S+)\s*$",
    re.I | re.M,
)
KV = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*$", re.M)

COUNTRIES = {
    "South Africa": {
        "builder": "SouthAfrica_Dozer",
        "cs": "SouthAfricaDozerCommandSet",
        "btn": "Command_ConstructSouthAfrica_Barracks",
        "obj": "SouthAfrica_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "Libya": {
        "builder": "Libya_Dozer",
        "cs": "LibyaDozerCommandSet",
        "btn": "Command_ConstructLibya_Barracks",
        "obj": "Libya_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "Syria": {
        "builder": "Syria_Dozer",
        "cs": "SyriaDozerCommandSet",
        "btn": "Command_ConstructSyria_Barracks",
        "obj": "Syria_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "UAE": {
        "builder": "UAE_Dozer",
        "cs": "UAEDozerCommandSet",
        "btn": "Command_ConstructUAE_Barracks",
        "obj": "UAE_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "Saudi Arabia": {
        "builder": "SaudiArabia_Dozer",
        "cs": "SaudiArabiaDozerCommandSet",
        "btn": "Command_ConstructSaudiArabia_Barracks",
        "obj": "SaudiArabia_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "Japan": {
        "builder": "Japan_VT72B",
        "cs": "Japan_VT72BCommandSet",
        "btn": "Command_ConstructJapan_Barracks_SAFE",
        "obj": "Japan_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "Vietnam": {
        "builder": "Vietnam_VT72B",
        "cs": "Vietnam_VT72BCommandSet",
        "btn": "Command_ConstructVietnam_Barracks_SAFE",
        "obj": "Vietnam_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "South Korea": {
        "builder": "SouthKorea_VT72B",
        "cs": "SouthKorea_VT72BCommandSet",
        "btn": "Command_ConstructSouthKorea_Barracks_SAFE",
        "obj": "SouthKorea_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "India": {
        "builder": "India_Dozer",
        "cs": "IndiaDozerCommandSet",
        "btn": "Command_ConstructIndia_Barracks",
        "obj": "India_Barracks",
        "image": "irq_barracks",
        "kind": "Barracks",
    },
    "Pakistan": {
        "builder": "Pakistan_Dozer",
        "cs": "PakistanDozerCommandSet",
        "btn": "Command_ConstructPakistan_Barracks",
        "obj": "Pakistan_Barracks",
        "image": "us_camp",
        "kind": "Barracks",
        "skip_overlay": True,
    },
    "Turkey": {
        "builder": "TurkeyVehicleDozer",
        "cs": "TurkeyDozerCommandSet",
        "btn": "Command_ConstructTurkeyBootCamp",
        "obj": "TurkeyBootCamp",
        "image": "us_camp",
        "kind": "Camp",
    },
    "Ukraine": {
        "builder": "UkraineVehicleDozer",
        "cs": "UkraineDozerCommandSet",
        "btn": "Command_ConstructUkraineBootCamp",
        "obj": "UkraineBootCamp",
        "image": "us_camp",
        "kind": "Camp",
    },
    "Britain": {
        "builder": "BritainVehicleDozer",
        "cs": "BritainDozerCommandSet",
        "btn": "Command_ConstructBritainBootCamp",
        "obj": "BritainBootCamp",
        "image": "us_camp",
        "kind": "Camp",
    },
    "Germany": {
        "builder": "GermanyVehicleDozer",
        "cs": "GermanyDozerCommandSet",
        "btn": "Command_ConstructGermanyBootCamp",
        "obj": "GermanyBootCamp",
        "image": "us_camp",
        "kind": "Camp",
    },
    "France": {
        "builder": "FranceVehicleDozer",
        "cs": "FranceDozerCommandSet",
        "btn": "Command_ConstructFranceBootCamp",
        "obj": "FranceBootCamp",
        "image": "us_camp",
        "kind": "Camp",
    },
    "Italy": {
        "builder": "ItalyVehicleDozer",
        "cs": "ItalyDozerCommandSet",
        "btn": "Command_ConstructItalyBootCamp",
        "obj": "ItalyBootCamp",
        "image": "us_camp",
        "kind": "Camp",
    },
    "Sweden": {
        "builder": "SwedenVehicleDozer",
        "cs": "SwedenDozerCommandSet",
        "btn": "Command_ConstructSwedenBootCamp",
        "obj": "SwedenBootCamp",
        "image": "us_camp",
        "kind": "Camp",
    },
}

FROZEN_CS = [
    "CommandSet_ZZZZ_OilCapture_SoldierCommand",
    "CommandSet_ZZZZ_OilCapture_BarracksAndRifles",
    "CommandSet_ZZZZ_FighterRoster_Next14",
    "CommandSet_ZZZZ_FighterRoster_SAUAESYINPK",
    "CommandSet_ZZZZ_JapanSKVietnam_Capture",
    "CommandSet_ZZZZ_AfricaPakistanSyria_AirExp",
]


def read_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def parse_blocks(text: str, src: str):
    blocks = []
    matches = list(INI_BLOCK.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        end_m = re.search(r"^\s*End\s*$", body, re.M | re.I)
        if end_m:
            body = body[: end_m.start()]
        fields = {}
        slots = {}
        for km in KV.finditer(body):
            k, v = km.group(1), km.group(2).strip()
            if k.isdigit():
                slots[int(k)] = v
            else:
                fields[k] = v
        blocks.append({"kind": m.group(1), "name": m.group(2), "fields": fields, "slots": slots, "src": src})
    return blocks


def main() -> int:
    errors = []
    if not BIG.exists():
        print(f"FAIL missing live DATA BIG: {BIG}")
        return 1
    if not OVERLAY.exists() or not SOURCE.exists():
        print("FAIL overlay source/payload missing")
        return 1
    src_txt = SOURCE.read_text(encoding="latin1")
    ov_txt = OVERLAY.read_text(encoding="latin1")
    if src_txt != ov_txt:
        errors.append("payload overlay differs from patch/Data/INI source")

    entries, raw = read_big(BIG)
    ini_entries = [(n, o, s) for n, o, s in entries if n.lower().endswith(".ini")]
    by_path = sorted(ini_entries, key=lambda e: e[0].replace("\\", "/").lower())

    kinds = defaultdict(dict)
    overlay_names = set()
    for name, off, size in by_path:
        text = raw[off : off + size].decode("latin1", errors="replace")
        for b in parse_blocks(text, name):
            kinds[b["kind"]][b["name"]] = b

    # merge overlay as last-win (name sorts after CommandButton_ZZZZ_*)
    for b in parse_blocks(ov_txt, str(OVERLAY)):
        overlay_names.add(b["name"])
        kinds[b["kind"]][b["name"]] = b

    cs, cb, obj, mi = kinds["CommandSet"], kinds["CommandButton"], kinds["Object"], kinds["MappedImage"]

    # overlay must only redefine existing buttons
    for n in overlay_names:
        if not n.startswith("Command_Construct"):
            errors.append(f"overlay introduced non-construct button {n}")

    new_names = [n for n in overlay_names if n not in {
        "Command_ConstructSouthAfrica_Barracks",
        "Command_ConstructLibya_Barracks",
        "Command_ConstructSyria_Barracks",
        "Command_ConstructUAE_Barracks",
        "Command_ConstructSaudiArabia_Barracks",
        "Command_ConstructIndia_Barracks",
        "Command_ConstructJapan_Barracks_SAFE",
        "Command_ConstructVietnam_Barracks_SAFE",
        "Command_ConstructSouthKorea_Barracks_SAFE",
        "Command_ConstructTurkeyBootCamp",
        "Command_ConstructUkraineBootCamp",
        "Command_ConstructBritainBootCamp",
        "Command_ConstructGermanyBootCamp",
        "Command_ConstructFranceBootCamp",
        "Command_ConstructItalyBootCamp",
        "Command_ConstructSwedenBootCamp",
    }]
    if new_names:
        errors.append(f"overlay introduced unexpected names: {new_names}")

    print("Country|Kind|Builder CS slot|Button|Object|Image|OK")
    for country, spec in COUNTRIES.items():
        btn = spec["btn"]
        objn = spec["obj"]
        csn = spec["cs"]
        img = spec["image"]
        ok = True
        notes = []
        if csn not in cs:
            ok = False
            notes.append("missing CS")
        else:
            slots = cs[csn]["slots"]
            slot = next((s for s, v in slots.items() if v == btn), None)
            if slot is None:
                ok = False
                notes.append("CS lacks button")
            # collision: same slot used twice
            used = defaultdict(list)
            for s, v in slots.items():
                used[s].append(v)
            for s, vs in used.items():
                if len(vs) > 1:
                    ok = False
                    notes.append(f"slot {s} collision {vs}")
        if btn not in cb:
            ok = False
            notes.append("missing button")
        else:
            fields = cb[btn]["fields"]
            if fields.get("Command") != "DOZER_CONSTRUCT":
                ok = False
                notes.append(f"Command={fields.get('Command')}")
            if fields.get("Object") != objn:
                ok = False
                notes.append(f"Object={fields.get('Object')}")
            if fields.get("ButtonImage") != img:
                ok = False
                notes.append(f"Image={fields.get('ButtonImage')}")
            if fields.get("ButtonImage") not in mi:
                ok = False
                notes.append("MappedImage missing")
        if objn not in obj:
            ok = False
            notes.append("object missing")
        slot = next((s for s, v in cs.get(csn, {}).get("slots", {}).items() if v == btn), "?")
        status = "PASS" if ok else "FAIL"
        if not ok:
            errors.append(f"{country}: {notes}")
        print(f"{country}|{spec['kind']}|{csn}[{slot}]|{btn}|{objn}|{img}|{status}")

    # frozen overlays still present in live BIG
    live_names = {n.replace("\\", "/").lower() for n, _, _ in entries}
    for frozen in FROZEN_CS:
        path = f"data/ini/{frozen.lower()}.ini"
        if path not in live_names:
            errors.append(f"frozen overlay missing from live BIG: {frozen}")

    # overlay must not mention frozen systems
    banned = ("OilCapture", "FighterRoster", "Flag_Hs", "Weapon", "Science")
    for word in banned:
        if word.lower() in ov_txt.lower() and word != "Science":
            # comments may mention nothing of these
            if re.search(rf"\b{word}\b", ov_txt):
                errors.append(f"overlay mentions out-of-scope token {word}")

    print()
    if errors:
        print("STATIC VALIDATION: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("STATIC VALIDATION: PASS")
    print(f"Overlay buttons: {len(overlay_names)}")
    print("Pakistan left on existing us_camp last-win (CommandButton_Pakistan.ini)")
    print("No CommandSet edits. No ART edits. No BIG packed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
