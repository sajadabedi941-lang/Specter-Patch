#!/usr/bin/env python3
"""Final global aircraft completion packer.

Baseline: new-folder-aircraft-source-fix BIGs.
Visual-only TEOD swaps for unused New folder meshes. No CommandSet slot changes.
Does not import TEOD Object/Weapon/CommandSet gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_final_aircraft_complete as gen
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/new_folder_source_fix/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/new_folder_source_fix/_SPEC_ART_ONE.big")
TEOD_W3D = Path("/tmp/teod/!TEOD_W3D.big")
TEOD_TEX = Path("/tmp/teod/!TEOD_Textures.big")
ART_CACHE = Path("/tmp/teod_final_art")

KEEP_SLOTS = {
    "Germany_HeavyAirBaseCommandSet": {
        8: "Command_ConstructGermanyUAVEuroMALE",
        9: "Command_ConstructGermanyJetFCASNGF",
    },
    "France_HeavyAirBaseCommandSet": {5: "Command_ConstructFranceUCAVNeuron"},
    "FranceAirfieldCommandSet": {
        11: "Command_ConstructFranceJetMirageF1CR",
        12: "Command_ConstructFranceJetRafaleF4",
    },
    "France_LargeAirBaseCommandSet": {
        11: "Command_ConstructFranceJetMirageF1CR",
        12: "Command_ConstructFranceJetRafaleF4",
    },
    "Britain_HeavyAirBaseCommandSet": {12: "Command_ConstructBritainAircraftTornadoECR"},
    "Japan_HeavyAirBaseCommandSet": {
        7: "Command_ConstructJapanJetC130H",
        8: "Command_ConstructJapanUAVRQ4",
    },
    "China_HeavyAirBaseCommandSet": {12: "Command_ConstructChinaJetJ35A"},
    "Iran_HeavyAirBaseCommandSet": {
        2: "Command_ConstructIranJetMig21Bis",
        3: "Command_ConstructIranJetSu35S",
    },
    "Turkey_HeavyAirBaseCommandSet": {6: "Command_ConstructTurkeyJetF4ETerm"},
    "Italy_HeavyAirBaseCommandSet": {8: "Command_ConstructItalyJetGCAP"},
    "Pakistan_AirfieldCommandSet": {9: "Command_ConstructPakistanJetJ10CE"},
}

PROTECT_SETS = [
    "AmericaAirfieldCommandSet",
    "America_LargeAirBaseCommandSet",
    "America_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
    "ItalyAirfieldCommandSet",
    "Italy_LargeAirBaseCommandSet",
    "Italy_HeavyAirBaseCommandSet",
    "BritainAirfieldCommandSet",
    "Britain_LargeAirBaseCommandSet",
    "Britain_HeavyAirBaseCommandSet",
    "GermanyAirfieldCommandSet",
    "Germany_LargeAirBaseCommandSet",
    "Germany_HeavyAirBaseCommandSet",
    "TurkeyAirfieldCommandSet",
    "Turkey_LargeAirBaseCommandSet",
    "Turkey_HeavyAirBaseCommandSet",
    "IranAirfieldCommandSet",
    "IranExpandedAirfieldCommandSet",
    "Iran_HeavyAirBaseCommandSet",
    "Japan_AirfieldCommandSet",
    "Japan_HeavyAirBaseCommandSet",
    "FranceAirfieldCommandSet",
    "France_LargeAirBaseCommandSet",
    "France_HeavyAirBaseCommandSet",
    "Pakistan_AirfieldCommandSet",
]

NUCLEAR_KEEP = {
    "America_HeavyAirBaseCommandSet": (6, "Command_Upgrade_NuclearTipWarhead2"),
}

PACKED_VISUALS = [
    {
        "key": r"data\ini\object\specter\pla\airforce\j20b.ini",
        "old": {"CHI_J20B", "CHI_J20B_D", "CHI_J20B_R"},
        "models": ("NVJ-20", "NVJ-20D", "NVJ-20D1"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\pla\airforce\j20b_aa.ini",
        "old": {"CHI_J20B", "CHI_J20B_D", "CHI_J20B_R"},
        "models": ("NVJ-20", "NVJ-20D", "NVJ-20D1"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\pla\airforce\j16d.ini",
        "old": {"Chi_J16D"},
        "models": ("NVJ16", "NVJ16_D", "NVJ16_E"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\pla\airforce\jh7a2.ini",
        "old": {"CHI_JH7A2", "CHI_JH7A2D", "CHI_JH7A2R"},
        "models": ("NVJH-7A", "NVJH-7AD", "NVJH-7AD1"),
        "strip_anim": True,
    },
    {
        "key": r"data\ini\object\specter\united states of america\airforce\f35c.ini",
        "old": {"US_F35A"},
        "models": ("AVF-35", "AVF-35_D", "AVF-35_E"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\united states of america\airforce\f35c_aa.ini",
        "old": {"US_F35A"},
        "models": ("AVF-35", "AVF-35_D", "AVF-35_E"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\united states of america\airforce\fa18e.ini",
        "old": {"US_FA18E"},
        "models": ("AVF-18", "AVF-18_D", "AVF-18_E"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\armed forces of russian federation\airforce\mig31k.ini",
        "old": {"RUS_MIG31K"},
        "models": ("RU-Mig31", "RU-Mig31_D", "RU-Mig31_E"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\armed forces of russian federation\airforce\mig35.ini",
        "old": {"RUS_Mig35"},
        "models": ("RUMIG_35", "RUMIG_35D", "RUMIG_35E"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\armed forces of russian federation\airforce\su34m.ini",
        "old": {"RUS_SU34"},
        "models": ("RUSU-34", "RUSU-34_D", "RUSU-34_E1"),
        "strip_anim": False,
    },
    {
        "key": r"data\ini\object\specter\armed forces of russian federation\airforce\su25t_su39.ini",
        "old": {"RUS_SU25T"},
        "models": ("RUSU-25", "RUSU-25_D", "RUSU-25_E"),
        "strip_anim": False,
    },
]

W3D_INJECT = [
    "NVJ-20.W3D", "NVJ-20D.W3D", "NVJ-20D1.W3D",
    "NVJ16.W3D", "NVJ16_D.W3D", "NVJ16_E.W3D",
    "NVJH-7A.W3D", "NVJH-7AD.W3D", "NVJH-7AD1.W3D",
    "AVF-35.W3D", "AVF-35_D.W3D", "AVF-35_E.W3D",
    "AVF-18.W3D", "AVF-18_D.W3D", "AVF-18_E.W3D",
    "RU-Mig31.W3D", "RU-Mig31_D.W3D", "RU-Mig31_E.W3D",
    "RUMIG_35.W3D", "RUMIG_35D.W3D", "RUMIG_35E.W3D",
    "RUSU-34.W3D", "RUSU-34_D.W3D", "RUSU-34_E1.W3D",
    "RUSU-25.W3D", "RUSU-25_D.W3D", "RUSU-25_E.W3D",
]

TEX_INJECT = [
    "J-20.dds", "J-20_D.dds", "J-20_E.dds", "PGZ-04.dds",
    "J16.dds", "J16_D.dds", "J16_E.dds",
    "JH-7A.dds", "JH-7A_D.dds", "JH-7A_E.dds",
    "F-35.dds", "F-35_D.dds", "F-35_E.dds",
    "F-18.dds", "F-18_D.dds", "F-18_E.dds",
    "USA Missiles.dds", "USA Missiles_D.dds",
    "Mig-31.dds", "Mig-31_D.dds", "Mig-31_E.dds",
    "Mig-35.dds", "Mig-35_D.dds", "Mig-35_E.dds",
    "SU-34.dds", "SU-34_D.dds", "SU-34_E.dds", "R-33.dds",
    "SU-25.dds", "SU-25_D.dds", "SU-25_E.dds",
    "Chinese_Missiles.dds", "Chinese_Missiles_D.dds",
    "Russian Missiles.dds", "Russian Missiles_D.dds",
    "housecolor2.dds",
]

SHARED_NO_OVERWRITE = {"housecolor2.dds", "rubbletexture.dds"}

PORTRAIT_SRC = {
    "SPEC_ChinaJ20C.tga": "J-20.dds",
    "SPEC_ItalyF35A.tga": "F-35.dds",
}

PRESERVED_MODELS = {
    "GermanyUAVEuroMALE": "Nat_Heron",
    "FranceUCAVNeuron": "CHI_GJ11L",
    "FranceJetRafaleF4": "LSFIDRafale",
    "BritainAircraftTornadoECR": "LSFTornado",
    "JapanUAVRQ4": "US_RQ-4",
    "TurkeyJetF4ETerm": "JPF4",
    "FranceJetMirageF1CR": "UVMirage",
    "GermanyJetFCASNGF": "NVJ31",
    "ChinaJetJ35A": "NVJ31",
    "IranJetMig21Bis": "UVMig-21",
    "IranJetSu35S": "SU-37",
    "TurkeyJetF16C": "AVF16",
    "ItalyJetGCAP": "PAK-FA",
    "PakistanJetJ10CE": "NVJ-10",
    "JapanJetC130H": "AVCargoPln",
    "ChinaJetJ31": "LSFJ31",
    "BritainJetF35B": "ENF35A",
    "ItalyJetF35B": "ENF35A",
    "GermanyJetF35A": "LSFUSAF35A",
    "AmericaDroneRQ180": "AV_RQ180",
    "BritainJetVampireFB5": "UV_Turbo",
    "BritainJetVampireFB9": "UVVampire",
}

EXPECT_NEW = {
    "ChinaJetJ20C": "NVJ-20",
    "ChinaJetJ20B_AG": "NVJ-20",
    "ChinaJetJ20B_AA": "NVJ-20",
    "ChinaJetJ16D": "NVJ16",
    "ChinaJetJH7A2": "NVJH-7A",
    "AmericaJetF35C": "AVF-35",
    "AmericaJetF35C_AA": "AVF-35",
    "AmericaJetFA18E": "AVF-18",
    "ItalyJetF35A": "AVF-35",
    "RussiaJetMig31K": "RU-Mig31",
    "RussiaJetMig35": "RUMIG_35",
    "RussiaJetSu34": "RUSU-34",
    "RussiaJetSU25T": "RUSU-25",
}

REGRESS = {
    "America_LargeAirBaseCommandSet": "Command_ConstructAmericaJetRaptor",
    "America_HeavyAirBaseCommandSet": "Command_ConstructAmericaJetB2",
    "Russia_LargeAirBaseCommandSet": "Command_ConstructRussiaJetSu35S",
    "PLAAirfieldCommandSet": "Command_ConstructChinaJetJ11B",
    "China_HeavyAirBaseCommandSet": "Command_ConstructChinaJetJ20C",
    "France_LargeAirBaseCommandSet": "Command_ConstructFranceJetRafaleC",
    "FranceAirfieldCommandSet": "Command_ConstructFranceJetMirage20005F",
    "Germany_LargeAirBaseCommandSet": "Command_ConstructGermanyJetTyphoonT4",
    "Italy_LargeAirBaseCommandSet": "Command_ConstructItalyJetTyphoon",
    "Britain_LargeAirBaseCommandSet": "Command_ConstructBritainJetF35B",
    "Britain_HeavyAirBaseCommandSet": "Command_ConstructBritainJetTempest",
    "BritainAirfieldCommandSet": "Command_ConstructBritainJetPhantomFG1",
    "Japan_AirfieldCommandSet": "Command_ConstructJapanJetF2A",
    "Turkey_HeavyAirBaseCommandSet": "Command_ConstructTurkeyJetKAAN",
    "IranExpandedAirfieldCommandSet": "Command_ConstructIranJetF14A",
    "Iran_HeavyAirBaseCommandSet": "Command_ConstructIranJetF4E",
    "Pakistan_AirfieldCommandSet": "Command_ConstructPakistanJetJ10CE",
}

COUNTRY_SETS = {
    "USA": ["AmericaAirfieldCommandSet", "America_LargeAirBaseCommandSet", "America_HeavyAirBaseCommandSet"],
    "Russia": ["RussiaAirfieldCommandSet", "Russia_LargeAirBaseCommandSet", "Russia_HeavyAirBaseCommandSet"],
    "China": ["PLAAirfieldCommandSet", "China_LargeAirBaseCommandSet", "China_HeavyAirBaseCommandSet"],
    "France": ["FranceAirfieldCommandSet", "France_LargeAirBaseCommandSet", "France_HeavyAirBaseCommandSet"],
    "Germany": ["GermanyAirfieldCommandSet", "Germany_LargeAirBaseCommandSet", "Germany_HeavyAirBaseCommandSet"],
    "Italy": ["ItalyAirfieldCommandSet", "Italy_LargeAirBaseCommandSet", "Italy_HeavyAirBaseCommandSet"],
    "United Kingdom": ["BritainAirfieldCommandSet", "Britain_LargeAirBaseCommandSet", "Britain_HeavyAirBaseCommandSet"],
    "Turkey": ["TurkeyAirfieldCommandSet", "Turkey_LargeAirBaseCommandSet", "Turkey_HeavyAirBaseCommandSet"],
    "Iran": ["IranAirfieldCommandSet", "IranExpandedAirfieldCommandSet", "Iran_HeavyAirBaseCommandSet"],
    "Japan": ["Japan_AirfieldCommandSet", "Japan_LargeAirBaseCommandSet", "Japan_HeavyAirBaseCommandSet"],
    "Pakistan": ["Pakistan_AirfieldCommandSet"],
}

SOURCE_HINTS = [
    (tuple(x.lower() for x in (
        "NVJ-20", "NVJ16", "NVJH-7A", "AVF-35", "AVF-18", "RU-Mig31", "RUMIG_35",
        "RUSU-34", "RUSU-25", "NVJ31", "UVMirage", "AVCargoPln", "UVMig-21",
        "SU-37", "AVF16", "PAK-FA", "NVJ-10", "RU_Orion", "AV_RQ180", "UV_Turbo", "UVVampire",
    )), "New folder"),
    (tuple(x.lower() for x in (
        "LSF", "ENF35A", "LSFUSAF35A", "CHI_GJ11L", "Nat_Heron", "JPF4", "qsnt50",
        "LSFJ31", "LSFIDRafale", "LSFTornado",
    )), "DONOR_ART"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def visual_source(model: str) -> str:
    low = model.lower()
    for names, src in SOURCE_HINTS:
        if any(low == n or low.startswith(n) for n in names):
            return src
    return "existing Specter"


def apply_state_models(text: str, old: set[str], model: str, model_d: str, model_k: str, strip_anim: bool = False) -> str:
    out = []
    state = "default"
    for line in text.splitlines(True):
        s = line.strip()
        if s.startswith("DefaultConditionState"):
            state = "default"
        elif s.startswith("ConditionState") and "RUBBLE" in s:
            state = "rubble"
        elif s.startswith("ConditionState") and "REALLYDAMAGED" in s:
            state = "damaged"
        elif s.startswith("ConditionState"):
            state = "other"
        if strip_anim and re.match(r"\s*Animation(Mode)?\s*=", line):
            continue
        m = re.match(r"(\s*Model\s+=\s+)(\S+)(\s*)$", line)
        if m and m.group(2) in old:
            tgt = model if state in ("default", "other") else (model_k if state == "rubble" else model_d)
            nl = "\n" if line.endswith("\n") else ""
            line = m.group(1) + tgt + nl
        out.append(line)
    return "".join(out)


def index_big(path: Path) -> dict[str, tuple[str, bytes]]:
    entries, raw = ch.read_big(path)
    out: dict[str, tuple[str, bytes]] = {}
    for name, off, size in entries:
        leaf = name.split("\\")[-1].split("/")[-1]
        out[leaf.lower()] = (name, raw[off : off + size])
    return out


def extract_teod() -> dict[str, Path]:
    ART_CACHE.mkdir(parents=True, exist_ok=True)
    w3d = index_big(TEOD_W3D)
    tex = index_big(TEOD_TEX)
    written: dict[str, Path] = {}
    missing = []
    for name in W3D_INJECT + TEX_INJECT:
        srcmap = w3d if name.lower().endswith(".w3d") else tex
        hit = srcmap.get(name.lower())
        if not hit:
            missing.append(name)
            continue
        dest = ART_CACHE / name
        dest.write_bytes(hit[1])
        written[name.lower()] = dest
    if missing:
        print("TEOD extract missing:", missing)
    print("extracted", len(written), "TEOD art files")
    return written


def classify_role(block: str) -> str:
    ws = re.search(r"WeaponSet\s*\n.*?^  End", block, re.M | re.S)
    if not ws:
        if "StealthDetector" in block or "ShroudClearingRange" in block:
            kind = block
            if "CAN_ATTACK" not in re.search(r"KindOf\s+=.*", block).group(0) if re.search(r"KindOf\s+=.*", block) else "":
                return "recon/support"
        return "unarmed/support"
    body = ws.group(0)
    air = "AIRCRAFT" in body or "AntiAirborneVehicle = Yes" in block
    gnd = "VEHICLE STRUCTURE" in body or "STRUCTURE" in body
    kindof = re.search(r"KindOf\s+=\s+(.*)", block)
    k = kindof.group(1) if kindof else ""
    if "CAN_ATTACK" not in k:
        return "recon/support"
    if air and not gnd:
        return "A2A"
    if gnd and not air:
        return "strike/CAS"
    return "multirole"


def ammo_from_weapons(block: str, wpn_text: str) -> str:
    names = re.findall(r"Weapon\s+=\s+\S+\s+(\S+)", block)
    bits = []
    for n in names[:6]:
        m = re.search(rf"^Weapon {re.escape(n)}\s*\n(.*?)(?:^End\s*$)", wpn_text, re.M | re.S)
        clip = "?"
        if m:
            cm = re.search(r"ClipSize\s+=\s+(\S+)", m.group(1))
            if cm:
                clip = cm.group(1)
        bits.append(f"{n} x{clip}")
    return "; ".join(bits) if bits else "none"


def load_objects(data_map: dict[str, tuple[str, bytes]]) -> dict[str, tuple[str, str]]:
    obj_pat = re.compile(r"^Object\s+(\S+)", re.M)
    out: dict[str, tuple[str, str]] = {}
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for m in obj_pat.finditer(text):
            obj = m.group(1)
            start = m.start()
            nxt = obj_pat.search(text, m.end())
            end = nxt.start() if nxt else len(text)
            out[obj] = (name, text[start:end])
    return out


def write_reports(out: Path, data_map: dict[str, tuple[str, bytes]], art_w3d: set[str], dh: str, ah: str) -> dict:
    cs_text = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    wpn_text = data_map["data\\ini\\weapon.ini"][1].decode("latin1")
    objs = load_objects(data_map)
    rows = []
    unresolved = []
    stats = {"audited": 0, "changed": 0, "newfolder": 0, "donor": 0, "a2a": 0, "multi": 0, "strike": 0, "created": 3}

    changed_objs = set(EXPECT_NEW) | {
        "FranceJetMirageF1CR", "GermanyJetFCASNGF", "ChinaJetJ35A", "IranJetMig21Bis",
        "IranJetSu35S", "TurkeyJetF16C", "ItalyJetGCAP", "PakistanJetJ10CE",
        "JapanJetC130H", "RussiaDronesOrion2",
    }

    for country, sets in COUNTRY_SETS.items():
        for set_name in sets:
            try:
                block = ch.grab_block(cs_text, set_name)
            except SystemExit:
                continue
            loc = "Fighter"
            if "Heavy" in set_name:
                loc = "Heavy"
            elif "Large" in set_name:
                loc = "Large"
            for line in block.splitlines():
                sm = re.match(r"\s*(\d+)\s*=\s*(\S+)", line)
                if not sm:
                    continue
                slot, btn = int(sm.group(1)), sm.group(2)
                if slot > 12:
                    continue
                if not btn.startswith("Command_Construct"):
                    continue
                obj = btn[len("Command_Construct"):]
                if obj not in objs:
                    unresolved.append(f"{country} {set_name} slot {slot} {btn} missing Object")
                    continue
                _fname, oblock = objs[obj]
                models = re.findall(r"Model\s+=\s+(\S+)", oblock)
                model = models[0] if models else "?"
                scale_m = re.search(r"^Scale\s+=\s+(\S+)", oblock, re.M)
                scale = scale_m.group(1) if scale_m else "1.00"
                portrait = re.search(r"SelectPortrait\s+=\s+(\S+)", oblock)
                por = portrait.group(1) if portrait else "?"
                display = re.search(r"DisplayName\s+=\s+(\S+)", oblock)
                disp = display.group(1) if display else f"OBJECT:{obj}"
                role = classify_role(oblock)
                src = visual_source(model)
                ammo = ammo_from_weapons(oblock, wpn_text)
                w3d_ok = model.lower() in art_w3d or model == "?"
                rows.append({
                    "country": country, "obj": obj, "disp": disp, "role": role,
                    "model": model, "src": src, "loc": loc, "set": set_name,
                    "slot": slot, "ammo": ammo, "scale": scale, "por": por,
                    "buildable": "YES" if slot <= 12 else "NO",
                    "w3d": "PASS" if w3d_ok else "FAIL",
                })
                stats["audited"] += 1
                if obj in changed_objs:
                    stats["changed"] += 1
                if src == "New folder":
                    stats["newfolder"] += 1
                elif src == "DONOR_ART":
                    stats["donor"] += 1
                if role == "A2A":
                    stats["a2a"] += 1
                elif role == "multirole":
                    stats["multi"] += 1
                elif role == "strike/CAS":
                    stats["strike"] += 1

    # packed-but-unslotted
    for obj, note in [
        ("AmericaDroneRQ180", "OBJECT_READY_NO_SAFE_SLOT"),
        ("BritainJetVampireFB5", "OBJECT_READY_NO_SAFE_SLOT"),
        ("BritainJetVampireFB9", "OBJECT_READY_NO_SAFE_SLOT"),
    ]:
        if obj in objs:
            _f, oblock = objs[obj]
            models = re.findall(r"Model\s+=\s+(\S+)", oblock)
            model = models[0] if models else "?"
            unresolved.append(f"{obj} visual {model} {note}")

    lines = [
        "# FINAL AIRCRAFT COMPLETION REPORT",
        "",
        f"Baseline: new-folder-aircraft-source-fix-v1",
        f"DATA sha256 `{dh}`",
        f"ART sha256 `{ah}`",
        "",
        "## A–N. Aircraft by country (visible CommandSet slots 1–12)",
        "",
        "| Country | Object | DisplayName | Role | W3D | Source | Airbase | CommandSet | Slot | Loadout/ammo | Scale | Button | Buildable | W3D |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['country']} | `{r['obj']}` | {r['disp']} | {r['role']} | `{r['model']}` | {r['src']} | {r['loc']} | `{r['set']}` | {r['slot']} | {r['ammo'].replace('|','/')} | {r['scale']} | `{r['por']}` | {r['buildable']} | {r['w3d']} |"
        )
    lines += [
        "",
        "## O. Parser validation",
        "See pack log: CommandSet hashes unchanged, CommandButton refs, object uniqueness of new overlays, projectile refs, re-extract PASS.",
        "",
        "## P. Unused valid New folder aircraft W3Ds (intentionally not applied)",
        "- NVJ-20R, NVJH-7B/C, AVF-35_NFZ, AVF-18 extra debris, RUSU-25S, RUIL76, RUSU-47: not mapped to a live unique slot this pass, or would duplicate an existing unique aircraft.",
        "- AVF-35 applied to USA F-35C and Italy F-35A. UK/Italy F-35B keep dedicated donor ENF35A. Germany F-35A keeps dedicated donor LSFUSAF35A.",
        "",
        "## Q. Missing/broken donor assets",
        "- Eurodrone / nEUROn / Rafale F4 / Vulcan / Tornado airframe: no valid New folder W3D (UVTornado_M is T-55 ammo).",
        "- CWCusAC130.tga still missing from TEOD; C-130 uses AC130.dds.",
        "",
        "## R. Regression",
        "Raptor, Su-35, J-11B, J-20C, Rafale C, Mirage 2000-5F, Typhoon, F-35B, Tempest, Phantom, F-2A, KAAN, F-14, F-4E, J-10CE, J-35A, Eurodrone, nEUROn, GCAP preserved on menus.",
        "",
        "## Unresolved",
        *[f"- {u}" for u in unresolved],
        "",
        f"Audited visible construct slots: {stats['audited']}",
    ]
    (out / "FINAL_AIRCRAFT_COMPLETION_REPORT.md").write_text("\n".join(lines) + "\n")
    (ROOT / "FINAL_AIRCRAFT_COMPLETION_REPORT.md").write_text("\n".join(lines) + "\n")

    mlines = [
        "# FINAL VISUAL DONOR MATRIX",
        "",
        "| Country | Aircraft | Identity | W3D | Source | Exact/stand-in |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        kind = "exact" if r["src"] == "New folder" else ("stand-in" if r["src"] == "DONOR_ART" else "existing Specter")
        # refine
        if r["obj"] in EXPECT_NEW:
            kind = "New folder exact/close"
        if r["obj"] in ("GermanyUAVEuroMALE", "FranceUCAVNeuron", "FranceJetRafaleF4", "BritainAircraftTornadoECR", "JapanUAVRQ4", "TurkeyJetF4ETerm"):
            kind = "CURRENT_STANDIN_PRESERVED"
        mlines.append(f"| {r['country']} | `{r['obj']}` | {r['disp']} | `{r['model']}` | {r['src']} | {kind} |")
    (out / "FINAL_VISUAL_DONOR_MATRIX.md").write_text("\n".join(mlines) + "\n")
    (ROOT / "FINAL_VISUAL_DONOR_MATRIX.md").write_text("\n".join(mlines) + "\n")
    stats["unresolved"] = unresolved
    return stats


def write_install(out: Path) -> None:
    (out / "INSTALL.txt").write_text(
        """SPECTER FINAL GLOBAL AIRCRAFT COMPLETE

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

Visual-only New folder / TEOD meshes applied to live USA/Russia/China/NATO
aircraft. Gameplay, CommandSets, Rally/Sell, and Nuclear/Atomic slots unchanged.

See FINAL_AIRCRAFT_COMPLETION_REPORT.md and FINAL_VISUAL_DONOR_MATRIX.md.
"""
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/final_aircraft_complete"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    gen.main()
    overlay: dict[str, bytes] = {}
    for spec in gen.OVERLAY:
        p = PATCH / spec["rel"]
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    fr.parse_check(overlay)
    print("overlay parser PASS")

    teod_files = extract_teod()
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

    cs_probe = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    protect_hash = {}
    for n in PROTECT_SETS:
        try:
            protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        except Exception:
            print("protect skip missing", n)

    for spec in PACKED_VISUALS:
        key = spec["key"]
        if key not in data_map:
            raise SystemExit(f"missing packed {key}")
        name, blob = data_map[key]
        text = blob.decode("latin1")
        m, md, mk = spec["models"]
        new = apply_state_models(text, spec["old"], m, md, mk, spec["strip_anim"])
        if spec["strip_anim"] and re.search(r"Animation\s*=", new):
            # leftover animation on other objects in file is OK only if not old model anim
            pass
        if spec["strip_anim"]:
            new = re.sub(r"^[ \t]*Animation(Mode)?[ \t]*=.*\n", "", new, flags=re.M)
        if m not in new:
            raise SystemExit(f"{key} failed to apply {m}")
        data_map[key] = (name, ch.lf(new.encode("latin1")))
        print("packed visual", name, "->", m)

    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    packed_tex_keys = {k.split("\\")[-1].lower() for k in art_map if "\\textures\\" in k}
    for name in W3D_INJECT:
        src = teod_files.get(name.lower())
        if src is None:
            raise SystemExit(f"missing extracted W3D {name}")
        dest = "Art\\W3D\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    for name in TEX_INJECT:
        src = teod_files.get(name.lower())
        if src is None:
            if name.lower() in packed_tex_keys:
                print("skip missing TEOD tex, packed has", name)
                continue
            print("WARN missing tex", name)
            continue
        if name.lower() in SHARED_NO_OVERWRITE and name.lower() in packed_tex_keys:
            print("keep packed shared tex", name)
            continue
        dest = "Art\\Textures\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    print("ART injected")

    packed_tex = {k.split("\\")[-1].lower(): art_map[k][1] for k in art_map if "\\textures\\" in k}
    for dest_name, src_name in PORTRAIT_SRC.items():
        src = teod_files.get(src_name.lower())
        if src is None:
            leaf = src_name.lower()
            tmp = Path("/tmp") / ("portrait_src_" + leaf.replace(" ", "_"))
            tmp.write_bytes(packed_tex[leaf])
            src = tmp
        tga = eu.make_portrait_any(src)
        dest = f"Art\\Textures\\{dest_name}"
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, tga)
        print("portrait", dest_name, len(tga))

    # keep US_F35A packed
    if "art\\w3d\\us_f35a.w3d" not in art_map and "art\\w3d\\us_f35a.w3d" not in {ch.norm_key(art_map[k][0]) for k in art_map}:
        print("WARN US_F35A missing")
    else:
        print("US_F35A reserved packed PASS")

    cs_final = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    cb_text = data_map["data\\ini\\commandbutton.ini"][1].decode("latin1")
    ch.validate_commandset_button_refs(cs_final, cb_text)
    print("CommandButton refs PASS")

    for n, oldh in protect_hash.items():
        h = hashlib.sha256(ch.grab_block(cs_final, n).encode("latin1")).hexdigest()
        if h != oldh:
            raise SystemExit(f"protected CommandSet changed: {n}")
    print("protected CommandSets unchanged PASS")

    for set_name, adds in KEEP_SLOTS.items():
        block = ch.grab_block(cs_final, set_name)
        for slot, btn in adds.items():
            if not re.search(rf"^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", block, re.M):
                raise SystemExit(f"{set_name} missing {slot}={btn}")
        if "Command_SetRallyPoint" not in block and "Command_Sell" not in block:
            print("WARN", set_name, "no Rally/Sell")
    print("kept slots PASS")

    for set_name, (slot, btn) in NUCLEAR_KEEP.items():
        block = ch.grab_block(cs_final, set_name)
        if not re.search(rf"^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", block, re.M):
            raise SystemExit(f"nuclear slot lost {set_name} {slot}")
    print("Nuclear/Atomic preservation PASS")

    for set_name, btn in REGRESS.items():
        if btn not in ch.grab_block(cs_final, set_name):
            raise SystemExit(f"regression {set_name} lost {btn}")
    print("country regression PASS")

    for obj, model in PRESERVED_MODELS.items():
        hits = []
        for key, (name, blob) in data_map.items():
            if key.endswith(".ini") and re.search(rf"^Object {re.escape(obj)}\b", blob.decode("latin1"), re.M):
                hits.append(blob.decode("latin1"))
        if len(hits) != 1:
            raise SystemExit(f"preserved {obj} hits={len(hits)}")
        if not re.search(rf"Model\s+=\s+{re.escape(model)}\b", hits[0]):
            raise SystemExit(f"{obj} lost model {model}")
    print("prior visual preserve PASS")

    for obj, model in EXPECT_NEW.items():
        found = False
        for key, (name, blob) in data_map.items():
            if not key.endswith(".ini"):
                continue
            text = blob.decode("latin1")
            if re.search(rf"^Object {re.escape(obj)}\b", text, re.M):
                found = True
                if not re.search(rf"Model\s+=\s+{re.escape(model)}\b", text):
                    raise SystemExit(f"{obj} missing {model}")
                if obj == "ChinaJetJH7A2" and re.search(r"Animation\s*=", text):
                    raise SystemExit("JH7A2 still has Animation")
        if not found:
            raise SystemExit(f"missing object {obj}")
    print("new visual apply PASS")

    # JH7A2 animation specifically
    jh = data_map[r"data\ini\object\specter\pla\airforce\jh7a2.ini"][1].decode("latin1")
    if re.search(r"Animation\s*=", jh):
        raise SystemExit("JH7A2 Animation remains")
    print("JH7A2 animation stripped PASS")

    # SU25 UCAS untouched
    su = data_map[r"data\ini\object\specter\armed forces of russian federation\airforce\su25t_su39.ini"][1].decode("latin1")
    if "RUS_SU25TU" not in su:
        raise SystemExit("SU25T_UCAS visual lost")
    if "RUSU-25" not in su:
        raise SystemExit("SU25T visual not applied")
    print("Su-25 T vs UCAS split PASS")

    art_w3d = {k.split("\\")[-1].lower().replace(".w3d", "") for k in art_map if k.endswith(".w3d")}
    for m in ("nvj-20", "nvj16", "nvjh-7a", "avf-35", "avf-18", "ru-mig31", "rumig_35", "rusu-34", "rusu-25", "us_f35a", "enf35a", "nvj31", "uvmirage"):
        if m not in art_w3d:
            raise SystemExit(f"missing W3D {m}")
    print("ART/W3D PASS")

    for rel in gen.OVERLAY:
        key = ch.norm_key("Data\\" + rel["rel"].replace("/", "\\"))
        text = data_map[key][1].decode("latin1")
        errs = e7.balanced_end(text, rel["rel"])
        if errs:
            raise SystemExit("End balance FAIL\n" + "\n".join(errs))
    print("overlay End balance PASS")

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)
    dh = sha256(out_data)
    ah = sha256(out_art)
    print("DATA sha256", dh)
    print("ART sha256", ah)

    v_entries, v_raw = ch.read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[ch.norm_key(name)] = (name, v_raw[off : off + size])
    va_entries, va_raw = ch.read_big(out_art)
    va_w3d = set()
    for name, off, size in va_entries:
        if name.lower().endswith(".w3d"):
            va_w3d.add(name.split("\\")[-1].lower().replace(".w3d", ""))
    checks = {
        r"data\ini\object\specter\pla\airforce\chinajetj20c.ini": "NVJ-20",
        r"data\ini\object\specter\pla\airforce\j16d.ini": "NVJ16",
        r"data\ini\object\specter\pla\airforce\jh7a2.ini": "NVJH-7A",
        r"data\ini\object\specter\united states of america\airforce\f35c.ini": "AVF-35",
        r"data\ini\object\specter\united states of america\airforce\fa18e.ini": "AVF-18",
        r"data\ini\object\specter\armed forces of russian federation\airforce\mig31k.ini": "RU-Mig31",
        r"data\ini\object\specter\armed forces of russian federation\airforce\mig35.ini": "RUMIG_35",
        r"data\ini\object\specter\armed forces of russian federation\airforce\su34m.ini": "RUSU-34",
        r"data\ini\object\specter\armed forces of russian federation\airforce\su25t_su39.ini": "RUSU-25",
        r"data\ini\object\specter\pla\airforce\chinajetj35a.ini": "NVJ31",
        r"data\ini\object\specter\french armed forces\airforce\francejetmiragef1cr.ini": "UVMirage",
    }
    for key, model in checks.items():
        if model not in v_map[key][1].decode("latin1"):
            raise SystemExit(f"re-extract {key} missing {model}")
    jh = v_map[r"data\ini\object\specter\pla\airforce\jh7a2.ini"][1].decode("latin1")
    if re.search(r"Animation\s*=", jh):
        raise SystemExit("re-extract JH7A2 Animation")
    for m in ("nvj-20", "nvj16", "nvjh-7a", "avf-35", "avf-18", "ru-mig31", "us_f35a"):
        if m not in va_w3d:
            raise SystemExit(f"re-extract ART missing {m}")
    vcs = v_map["data\\ini\\commandset.ini"][1].decode("latin1")
    if "Command_ConstructAmericaDroneRQ180" in ch.grab_block(vcs, "America_HeavyAirBaseCommandSet"):
        raise SystemExit("RQ-180 incorrectly slotted")
    print("re-extract FINAL content PASS")

    write_install(out)
    stats = write_reports(out, v_map, va_w3d, dh, ah)
    zh = sha256(out_data)  # placeholder
    zpath = out / "FINAL_GLOBAL_AIRCRAFT_COMPLETE.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(out / "FINAL_AIRCRAFT_COMPLETION_REPORT.md", "FINAL_AIRCRAFT_COMPLETION_REPORT.md")
        zf.write(out / "FINAL_VISUAL_DONOR_MATRIX.md", "FINAL_VISUAL_DONOR_MATRIX.md")
        zf.write(out / "INSTALL.txt", "INSTALL.txt")
    print("ZIP", zpath, zpath.stat().st_size)
    print("STATS", {k: stats[k] for k in stats if k != "unresolved"})
    for u in stats["unresolved"]:
        print("UNRESOLVED", u)
    (out / "PACK_REPORT.txt").write_text(
        f"DATA sha256 {dh}\nART sha256 {ah}\nZIP bytes {zpath.stat().st_size}\n"
        f"audited {stats['audited']} changed {stats['changed']} newfolder {stats['newfolder']} donor {stats['donor']}\n"
        f"a2a {stats['a2a']} multi {stats['multi']} strike {stats['strike']}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
