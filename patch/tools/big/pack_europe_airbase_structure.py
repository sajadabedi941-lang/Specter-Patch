#!/usr/bin/env python3
"""Restore European nuclear/atomic dozer slot and put helicopters on existing airbases.

France / Germany / Italy / UK:
  Fighter Airbase = fighters + attack helicopters
  Heavy Airbase   = transports, AWACS, drones, bombers, remaining helicopters
No extra helicopter building. Slot 12 is Command_ConstructAmericaLgm30 again.
Aircraft objects, ART, and weapons are not rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch
import pack_france_airforce as fr

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/europe_airforce_expansion/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/europe_airforce_expansion/_SPEC_ART_ONE.big")

MENUS = {
    "France": {
        "airfield": [
            "Command_ConstructFranceJetRafaleC",
            "Command_ConstructFranceJetRafaleB",
            "Command_ConstructFranceJetRafaleM",
            "Command_ConstructFranceJetMirage2000",
            "Command_ConstructFranceJetMirage2000D",
            "Command_ConstructFranceJetMirageF1CT",
            "Command_ConstructFranceJetMirageIIIE",
            "Command_ConstructFranceJetMirage5",
            "Command_ConstructFranceHelicopterTiger",
        ],
        "heavy": [
            "Command_ConstructFranceJetC130",
            "Command_ConstructFranceAircraftE3",
            "Command_ConstructFranceHelicopterNH90",
            "Command_ConstructFranceHelicopterCaracal",
        ],
        "heli_all": [
            "Command_ConstructFranceHelicopterTiger",
            "Command_ConstructFranceHelicopterNH90",
            "Command_ConstructFranceHelicopterCaracal",
        ],
        "dozer_heli": "Command_ConstructFranceHelicopterBase",
    },
    "Germany": {
        "airfield": [
            "Command_ConstructGermanyJetTyphoonT4",
            "Command_ConstructGermanyJetTyphoonECR",
            "Command_ConstructGermanyJetTornadoIDS",
            "Command_ConstructGermanyJetTornadoECR",
            "Command_ConstructGermanyJetF35A",
            "Command_ConstructGermanyJetMiG29G",
            "Command_ConstructGermanyJetAlphaJet",
            "Command_ConstructGermanyJetF4F",
            "Command_ConstructGermanyJetTornadoADV",
            "Command_ConstructGermanyJetMako",
            "Command_ConstructGermanyHelicopterTigerUHT",
        ],
        "heavy": [
            "Command_ConstructGermanyJetA400M",
            "Command_ConstructGermanyJetC130J",
            "Command_ConstructGermanyAircraftE3",
            "Command_ConstructGermanyDroneHeronTP",
            "Command_ConstructGermanyHelicopterNH90",
            "Command_ConstructGermanyHelicopterCH53",
            "Command_ConstructGermanyHelicopterH145M",
        ],
        "heli_all": [
            "Command_ConstructGermanyHelicopterTigerUHT",
            "Command_ConstructGermanyHelicopterNH90",
            "Command_ConstructGermanyHelicopterCH53",
            "Command_ConstructGermanyHelicopterH145M",
        ],
        "dozer_heli": "Command_ConstructGermany_HelicopterBase",
    },
    "Italy": {
        "airfield": [
            "Command_ConstructItalyJetTyphoon",
            "Command_ConstructItalyJetF35A",
            "Command_ConstructItalyJetF35B",
            "Command_ConstructItalyJetAMX",
            "Command_ConstructItalyJetTornadoIDS",
            "Command_ConstructItalyJetTornadoECR",
            "Command_ConstructItalyJetHarrierII",
            "Command_ConstructItalyJetF16",
            "Command_ConstructItalyJetM346FA",
            "Command_ConstructItalyJetMB339",
            "Command_ConstructItalyHelicopterAW249",
            "Command_ConstructItalyHelicopterA129",
        ],
        "heavy": [
            "Command_ConstructItalyJetC130J",
            "Command_ConstructItalyJetC27J",
            "Command_ConstructItalyAircraftG550CAEW",
            "Command_ConstructItalyDroneMQ9",
            "Command_ConstructItalyHelicopterNH90",
            "Command_ConstructItalyHelicopterAW101",
            "Command_ConstructItalyHelicopterAW139",
        ],
        "heli_all": [
            "Command_ConstructItalyHelicopterAW249",
            "Command_ConstructItalyHelicopterA129",
            "Command_ConstructItalyHelicopterNH90",
            "Command_ConstructItalyHelicopterAW101",
            "Command_ConstructItalyHelicopterAW139",
        ],
        "dozer_heli": "Command_ConstructItaly_HelicopterBase",
    },
    "Britain": {
        "airfield": [
            "Command_ConstructBritainJetF35B",
            "Command_ConstructBritainJetTyphoonFGR4",
            "Command_ConstructBritainJetTyphoonT3",
            "Command_ConstructBritainJetHarrierGR9",
            "Command_ConstructBritainJetTornadoGR4",
            "Command_ConstructBritainJetJaguarGR3",
            "Command_ConstructBritainJetSeaHarrierFA2",
            "Command_ConstructBritainJetPhantomFG1",
            "Command_ConstructBritainJetLightningF6",
            "Command_ConstructBritainJetHawk200",
            "Command_ConstructBritainHelicopterApache",
        ],
        "heavy": [
            "Command_ConstructBritainJetA400M",
            "Command_ConstructBritainJetC17",
            "Command_ConstructBritainAircraftE7",
            "Command_ConstructBritainDroneMQ9",
            "Command_ConstructBritainBomberVulcan",
            "Command_ConstructBritainHelicopterChinook",
            "Command_ConstructBritainHelicopterMerlin",
            "Command_ConstructBritainHelicopterWildcat",
            "Command_ConstructBritainHelicopterPuma",
        ],
        "heli_all": [
            "Command_ConstructBritainHelicopterApache",
            "Command_ConstructBritainHelicopterChinook",
            "Command_ConstructBritainHelicopterMerlin",
            "Command_ConstructBritainHelicopterWildcat",
            "Command_ConstructBritainHelicopterPuma",
        ],
        "dozer_heli": "Command_ConstructBritain_HelicopterBase",
    },
}

PROTECT_SETS = [
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
]

OVERLAY_COMMANDSETS = [
    ("INI/CommandSet_France.ini", r"Data\INI\CommandSet_France.ini"),
    ("INI/CommandSet_Germany.ini", r"Data\INI\CommandSet_Germany.ini"),
    ("INI/CommandSet_Italy.ini", r"Data\INI\CommandSet_Italy.ini"),
    ("INI/CommandSet_Britain.ini", r"Data\INI\CommandSet_Britain.ini"),
]


def cs_block(name: str, buttons: list[str]) -> str:
    lines = [f"CommandSet {name}"]
    for i, btn in enumerate(buttons, 1):
        lines.append(f"  {i}  = {btn}")
    lines.append("  13 = Command_SetRallyPoint")
    lines.append("  14 = Command_Sell")
    lines.append("End")
    return "\n".join(lines) + "\n"


def restore_dozer(cs_text: str, country: str, heli_btn: str) -> str:
    name = f"{country}DozerCommandSet"
    block = ch.grab_block(cs_text, name)
    if "Command_ConstructAmericaLgm30" in block and heli_btn not in block:
        print(f"{name} already has AmericaLgm30")
        return cs_text
    new_block, n = re.subn(
        rf"^( 12\s*=\s*){re.escape(heli_btn)}\s*$",
        r"\1Command_ConstructAmericaLgm30",
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        # already Lgm30 but leftover heli on another slot
        new_block, n2 = re.subn(
            rf"^\s*\d+\s*=\s*{re.escape(heli_btn)}\s*$",
            " 12  = Command_ConstructAmericaLgm30",
            block,
            count=1,
            flags=re.M,
        )
        if n2 != 1 and "Command_ConstructAmericaLgm30" not in block:
            raise SystemExit(f"{name} cannot restore AmericaLgm30 from {heli_btn}\n{block}")
        if n2 == 1:
            new_block = new_block
        else:
            return cs_text
    return fr.replace_block(cs_text, name, new_block)


def strip_heli_dozer_buttons(cb_text: str) -> str:
    for btn in (
        "Command_ConstructFranceHelicopterBase",
        "Command_ConstructGermany_HelicopterBase",
        "Command_ConstructItaly_HelicopterBase",
        "Command_ConstructBritain_HelicopterBase",
    ):
        cb_text, n = re.subn(
            rf"CommandButton {re.escape(btn)}\s*\n.*?^End\s*\n?",
            "",
            cb_text,
            count=1,
            flags=re.M | re.S,
        )
        print(f"Removed {btn} from CommandButton.ini ({n})")
    return cb_text


def validate(cs_text: str, cb_text: str) -> None:
    errors = []
    core = set(re.findall(r"^CommandButton (\S+)\s*$", cb_text, re.M))
    for country, spec in MENUS.items():
        names = (
            f"{country}AirfieldCommandSet",
            f"{country}_LargeAirBaseCommandSet",
            f"{country}_HeavyAirBaseCommandSet",
            f"{country}DozerCommandSet",
        )
        for name in names:
            n = cs_text.count(f"CommandSet {name}")
            if n != 1:
                errors.append(f"{name} count={n}")
                continue
            block = ch.grab_block(cs_text, name)
            idx = cs_text.find(f"CommandSet {name}")
            declared = core | set(re.findall(r"^CommandButton (\S+)\s*$", cs_text[:idx], re.M))
            for line in block.splitlines():
                m = re.match(r"^\s*\d+\s*=\s*(Command_\S+)\s*$", line)
                if not m:
                    continue
                btn = m.group(1)
                if btn not in declared:
                    errors.append(f"{name} refs unknown CommandButton {btn}")
            slots = [int(x) for x in re.findall(r"^\s*(\d+)\s*=", block, re.M)]
            if len(slots) != len(set(slots)):
                errors.append(f"{name} duplicate slots {slots}")
        fighter = ch.grab_block(cs_text, f"{country}AirfieldCommandSet")
        large = ch.grab_block(cs_text, f"{country}_LargeAirBaseCommandSet")
        heavy = ch.grab_block(cs_text, f"{country}_HeavyAirBaseCommandSet")
        dozer = ch.grab_block(cs_text, f"{country}DozerCommandSet")
        for btn in spec["airfield"]:
            if btn not in fighter:
                errors.append(f"{country} airfield missing {btn}")
            if btn not in large:
                errors.append(f"{country} LargeAirBase missing {btn}")
        for btn in spec["heavy"]:
            if btn not in heavy:
                errors.append(f"{country} heavy missing {btn}")
        for btn in spec["heli_all"]:
            if btn not in fighter and btn not in heavy:
                errors.append(f"{country} helicopter {btn} not on any airbase")
        if spec["dozer_heli"] in dozer:
            errors.append(f"{country} dozer still constructs Helicopter Base")
        if "Command_ConstructAmericaLgm30" not in dozer:
            errors.append(f"{country} dozer missing AmericaLgm30")
        if "HelicopterBase" in fighter or "HelicopterBase" in heavy:
            errors.append(f"{country} airbase still references HelicopterBase construct")
    if errors:
        raise SystemExit("PARSER CHECK FAIL\n" + "\n".join(errors))
    print("PARSER CHECK PASS CommandButton refs and airbase structure")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/europe_airbase_structure"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    overlay: dict[str, bytes] = {}
    for rel, dest in OVERLAY_COMMANDSETS:
        overlay[dest] = ch.lf((PATCH / rel).read_bytes())
    fr.parse_check(overlay)

    data_entries, data_raw = ch.read_big(BASE_DATA)
    art_entries, art_raw = ch.read_big(BASE_ART)
    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = ch.norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])
    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = ch.norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    cs_key = "data\\ini\\commandset.ini"
    cb_key = "data\\ini\\commandbutton.ini"
    cs_name, cs_blob = data_map[cs_key]
    cb_name, cb_blob = data_map[cb_key]
    cs_text = cs_blob.decode("latin1")
    cb_text = cb_blob.decode("latin1")

    protect_before = {n: ch.grab_block(cs_text, n) for n in PROTECT_SETS}

    cb_text = strip_heli_dozer_buttons(cb_text)
    data_map[cb_key] = (cb_name, ch.lf(cb_text.encode("latin1")))

    for country, spec in MENUS.items():
        cs_text = fr.replace_block(
            cs_text,
            f"{country}AirfieldCommandSet",
            cs_block(f"{country}AirfieldCommandSet", spec["airfield"]),
        )
        cs_text = fr.replace_block(
            cs_text,
            f"{country}_LargeAirBaseCommandSet",
            cs_block(f"{country}_LargeAirBaseCommandSet", spec["airfield"]),
        )
        cs_text = fr.replace_block(
            cs_text,
            f"{country}_HeavyAirBaseCommandSet",
            cs_block(f"{country}_HeavyAirBaseCommandSet", spec["heavy"]),
        )
        cs_text = restore_dozer(cs_text, country, spec["dozer_heli"])
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    validate(cs_text, cb_text)
    ch.validate_commandset_button_refs(cs_text, cb_text)
    protect_after = {n: ch.grab_block(cs_text, n) for n in PROTECT_SETS}
    for n in PROTECT_SETS:
        if protect_before[n] != protect_after[n]:
            raise SystemExit(f"PROTECTED CommandSet mutated: {n}")
    print("PROTECT CHECK PASS China/Russia CommandSets unchanged")

    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)

    zpath = out / "EUROPE_AIRBASE_STRUCTURE.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.writestr(
            "INSTALL.txt",
            "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
            "Keep EnglishZH.big and AudioZH.big unchanged.\n"
            "France/Germany/Italy/UK: Fighter Airbase + Heavy Airbase only.\n"
            "Nuclear/Atomic building restored on dozer slot 12.\n"
            "Helicopters are built from existing airbases. No extra airfield.\n",
        )
    verify = out / "zip_verify"
    if verify.exists():
        shutil.rmtree(verify)
    verify.mkdir()
    with zipfile.ZipFile(zpath, "r") as zf:
        zf.extractall(verify)
        names = set(zf.namelist())
    if "_SPEC_DATA_ONE.big" not in names or "_SPEC_ART_ONE.big" not in names:
        raise SystemExit(f"ZIP missing BIG files: {sorted(names)}")
    if hashlib.sha256((verify / "_SPEC_DATA_ONE.big").read_bytes()).digest() != hashlib.sha256(data_big).digest():
        raise SystemExit("ZIP DATA hash mismatch")
    if hashlib.sha256((verify / "_SPEC_ART_ONE.big").read_bytes()).digest() != hashlib.sha256(art_big).digest():
        raise SystemExit("ZIP ART hash mismatch")
    print("ZIP extract verify PASS")

    report = out / "PACK_REPORT.txt"
    report.write_text(
        f"DATA sha256 {hashlib.sha256(data_big).hexdigest()}\n"
        f"ART  sha256 {hashlib.sha256(art_big).hexdigest()}\n"
        f"ZIP  sha256 {hashlib.sha256(zpath.read_bytes()).hexdigest()}\n"
        f"DATA bytes {len(data_big)}\n"
        f"ART  bytes {len(art_big)}\n"
        "PARSER CHECK PASS overlay INI\n"
        "PARSER CHECK PASS CommandButton refs\n"
        "PROTECT CHECK PASS China/Russia\n"
        "ZIP extract verify PASS\n"
        "DOZER slot 12 = Command_ConstructAmericaLgm30 (FR/DE/IT/UK)\n"
        "NO Helicopter Base construct building\n"
        "Fighter Airbase = fighters + attack helicopters\n"
        "Heavy Airbase = transports/AWACS/drones/bombers + remaining helicopters\n"
    )
    print(report.read_text())
    print("wrote", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
