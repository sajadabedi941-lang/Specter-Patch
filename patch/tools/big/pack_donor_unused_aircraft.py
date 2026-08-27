#!/usr/bin/env python3
"""Pack unused unique DONOR_ART aircraft into complete-v1 BIGs.

Does not modify USA/Russia/China live gameplay files.
Does not import donor Object/Weapon/CommandSet INI.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_donor_unused_aircraft as gen
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/final_aircraft_complete/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/final_aircraft_complete/_SPEC_ART_ONE.big")
EXTRACT = Path("/tmp/donor_unused/extract")
TEX = Path("/tmp/donor_unused/tex")
ART_CACHE = Path("/tmp/donor_unused/art_cache")

MARKER_W = "; ===== SPECTER DONOR UNUSED AIRCRAFT WEAPONS BEGIN ====="
MARKER_WE = "; ===== SPECTER DONOR UNUSED AIRCRAFT WEAPONS END ====="

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
]

KEEP_SLOTS = {
    "Pakistan_AirfieldCommandSet": {9: "Command_ConstructPakistanJetJ10CE"},
    "Japan_HeavyAirBaseCommandSet": {
        7: "Command_ConstructJapanJetC130H",
        8: "Command_ConstructJapanUAVRQ4",
    },
    "Iran_HeavyAirBaseCommandSet": {
        1: "Command_ConstructIranJetF4E",
        2: "Command_ConstructIranJetMig21Bis",
        3: "Command_ConstructIranJetSu35S",
    },
    "France_HeavyAirBaseCommandSet": {5: "Command_ConstructFranceUCAVNeuron"},
    "Israel_HeavyAirBaseCommandSet": {
        1: "Command_ConstructIsraelJetF15BazHeavyBomber",
        2: "Command_ConstructIsraelJetG550Eitam",
    },
}

ART_INJECT = [
    "LSFUSAF15C.W3D", "LSFUSAF15Cd.W3D", "LSFUSAF15Ck.W3D",
    "LSFUSAF15E.W3D", "LSFUSAF15Ed.W3D", "LSFUSAF15Ek.W3D",
    "RUSU30.W3D", "RUSU30d.W3D",
    "LSFPKJ7.W3D", "LSFPKJ7d.W3D",
    "LSFIRJ7.W3D", "LSFIRJ7d.W3D",
]
TEX_INJECT = [
    "LSFUSAF15C.tga", "LSFUSAF15Cd.tga", "LSFUSAF15Ck.tga",
    "LSFUSAF15E.dds", "LSFUSAF15Ed.dds", "LSFUSAF15Ek.dds",
    "RUSU30MKK.dds", "RUSU30MKKd.dds",
    "LSFPKJ7.dds", "LSFPKJ7d.dds",
    "LSFIRJ7.dds", "LSFIRJ7d.dds",
    "LSFNKJ7d.dds", "LSFUSAF16.dds",
    "UsaAirMissileMap.dds", "UsaGbuMap.dds", "UsaGbuMap02.dds",
]
SHARED_NO_OVERWRITE = {"housecolor2.dds", "rubbletexture.dds", "f35.dds", "f35.tga"}

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
    "Japan_AirfieldCommandSet": "Command_ConstructJapanJetF2A",
    "Turkey_HeavyAirBaseCommandSet": "Command_ConstructTurkeyJetKAAN",
    "IranExpandedAirfieldCommandSet": "Command_ConstructIranJetF14A",
    "Iran_HeavyAirBaseCommandSet": "Command_ConstructIranJetF4E",
    "Pakistan_AirfieldCommandSet": "Command_ConstructPakistanJetJ10CE",
}

PROJECTILES = {
    "MeteorMissile_Object", "AIM-9X_Object", "R77_Object",
    "GBU24_GuidedBombObject", "Fab-250", "Kh59MK2_Object",
    "KH31P_MissileObject", "Paveway_IV_Object", "30mm_API-T_Projectile",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def rebuild_commandset(block: str, adds: dict[int, str]) -> str:
    m = re.match(r"CommandSet (\S+)", block)
    if not m:
        raise SystemExit("bad commandset block")
    name = m.group(1)
    slots: dict[int, str] = {}
    for line in block.splitlines():
        sm = re.match(r"\s*(\d+)\s*=\s*(\S+)", line)
        if sm:
            slots[int(sm.group(1))] = sm.group(2)
    for slot, btn in adds.items():
        cur = slots.get(slot)
        if cur and cur not in ("None", btn):
            raise SystemExit(f"{name} slot {slot} occupied by {cur}")
        slots[slot] = btn
    lines = [f"CommandSet {name}"]
    for slot in sorted(slots):
        lines.append(f"  {slot} = {slots[slot]}")
    lines.append("End")
    return "\n".join(lines) + "\n"


def replace_cs(text: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"CommandSet {re.escape(name)}\s*\n.*?^End\s*$", re.M | re.S)
    if not pat.search(text):
        raise SystemExit(f"missing {name}")
    return pat.sub(new_block.rstrip() + "\n", text, count=1)


def inline_buttons(cs_text: str, buttons: str) -> str:
    idx = cs_text.find("CommandSet GenericCommandSet")
    if idx < 0:
        idx = cs_text.find("CommandSet ")
    if idx < 0:
        raise SystemExit("no CommandSet to inline before")
    body = "\n".join(l for l in buttons.splitlines() if not l.startswith(";")).strip() + "\n\n"
    return cs_text[:idx] + body + cs_text[idx:]


def inline_weapons(weapon_ini: str, overlay: str) -> str:
    if any(ord(c) > 127 for c in overlay):
        raise SystemExit("non-ASCII weapons")
    block = MARKER_W + "\n" + overlay.strip() + "\n" + MARKER_WE + "\n"
    if MARKER_W in weapon_ini:
        weapon_ini = re.sub(
            re.escape(MARKER_W) + r".*?" + re.escape(MARKER_WE) + r"\n?",
            block,
            weapon_ini,
            count=1,
            flags=re.S,
        )
    else:
        if not weapon_ini.endswith("\n"):
            weapon_ini += "\n"
        weapon_ini += "\n" + block
    return weapon_ini


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = ch.parse_csf(data)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in gen.CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value):
            raise SystemExit(f"non-ASCII CSF {key}")
        if key in have_idx:
            i = have_idx[key]
            mag, name, _s = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
            updated += 1
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            added += 1
            have_idx[key] = len(labels) - 1
    print(f"CSF added {added} labels, updated {updated}")
    return ch.build_csf(version, unk, lang, labels)


def find_art_file(name: str) -> Path | None:
    for root in (EXTRACT, TEX, ART_CACHE):
        hits = [p for p in root.rglob("*") if p.is_file() and p.name.lower() == name.lower()]
        if hits:
            return hits[0]
    return None


def index_big_leaf(path: Path) -> dict[str, bytes]:
    entries, raw = ch.read_big(path)
    out = {}
    for name, off, size in entries:
        leaf = name.split("\\")[-1].split("/")[-1]
        out[leaf.lower()] = raw[off : off + size]
    return out


def collect_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    for spec in gen.AIRCRAFT:
        p = PATCH / spec["rel"]
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    extra = [
        "INI/Weapon_DonorUnusedAircraft.ini",
        "INI/CommandButton_DonorUnusedAircraft.ini",
        "INI/MappedImages/HandCreated/zDonorUnused_AirbasePortrait_Images.INI",
    ]
    for rel in extra:
        p = PATCH / rel
        dest = "Data\\" + rel.replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    return overlay


def write_install(out: Path) -> None:
    (out / "INSTALL.txt").write_text(
        """SPECTER DONOR UNUSED AIRCRAFT COMPLETION

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

Baseline: final-global-aircraft-complete-v1

Adds unused unique DONOR_ART visuals as new aircraft for non-USA / non-Russia / non-China countries.
Does not import donor gameplay INI.
Does not change USA, Russia, or China live objects, CommandSets, Nuclear/Atomic, Rally, or Sell.

New aircraft:
- Pakistan F-16A MLU (LSFF16C) Airfield slot 7
- Pakistan F-7PG (LSFPKJ7) Airfield slot 8
- Japan F-15J (LSFUSAF15C) Heavy slot 9
- Israel F-15C Baz (US_F15C) Heavy slot 3
- France FCAS NGF (LSFJ20 stand-in) Heavy slot 6
- Saudi F-15S (LSFUSAF15E) Heavy slot 1
- India Su-30MKI (RUSU30) Heavy slot 1
- Iran F-7N (LSFIRJ7) Heavy slot 4

See DONOR_UNUSED_AIRCRAFT_AUDIT.md for the full 39-alias audit and unused list.
"""
    )


def write_audit(out: Path, data_hash: str, art_hash: str, packed_hashes: dict[str, tuple[str, int, str]]) -> None:
    # packed_hashes: stem -> (sha16, size, users_or_status)
    rows = [
        ("01", "F18G", "EA18G / LSFEA18G / US_EA18G", "LSFEA18G.dds / UsaEA18Map.tga", "4ed1dceb834b031b / 4a28b58c20762da1 / ff6324294ac72e80", "YES", "AmericaJetEA18G (US_EA18G); NATO clones share US_EA18G", "NO (three hashes)", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("02", "Typhon", "LSFEUEF2000.W3D", "packed Typhoon", "32e8ec01c18a2476", "YES", "BritainJetTyphoonFGR4, GermanyJetTyphoonT4/ECR, ItalyJetTyphoon", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("03", "Tornado", "LSFTornado.W3D", "packed Tornado", "8b807972b7e0cab6", "YES", "UK/DE/IT Tornado objects", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("04", "Rafale", "LSFRafale.W3D", "packed Rafale", "42ce8cbfcc5d1aa0", "YES", "FranceJetRafaleB, FranceJetRafaleC", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("05", "Lighting", "AVLightn.W3D", "AVLightn.dds", "5b71ab3f0fbdc5a4", "YES", "BritainJetLightningF6", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("06", "F16Falcon", "LSFF16C.W3D", "LSFF16C.tga / LSFUSAF16.dds", "83a6c19d1a2c2a71", "NO", "none (TurkeyJetF16C now AVF16)", "YES", "Pakistan", "F-16A MLU", "PakistanJetF16AMLU", "legacy multirole", "Pakistan_AirfieldCommandSet 7", "ADDED_EXACT"),
        ("07", "Eagle", "LSFUSAF15C.W3D (+ unused US_F15C.W3D)", "LSFUSAF15C.tga / US_F15C.dds", "795178822318e4ca / 2217e98acaada7df", "NO", "none (USA F-15E uses US_F15E)", "YES (two distinct unused hashes)", "Japan (+ Israel extra mesh)", "F-15J (+ F-15C Baz)", "JapanJetF15J / IsraelJetF15CBaz", "air superiority / interceptor", "Japan_Heavy 9 / Israel_Heavy 3", "ADDED_EXACT"),
        ("08", "F35B", "ENF35A.W3D", "Ef35/f35", "6e008029316a5068", "YES", "BritainJetF35B, ItalyJetF35B", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("09", "F18prowler fighter", "EA18G.W3D / LSFEA18G.W3D", "LSFEA18G.dds", "4ed1dceb834b031b / 4a28b58c20762da1", "NO dedicated Prowler; Growler unused extra meshes", "none for EA18G/LSFEA18G; US_EA18G used by AmericaJetEA18G", "NO vs US_EA18G", "-", "-", "-", "-", "-", "NO_REALISTIC_COUNTRY"),
        ("10", "F22Raptor", "US_F22A.W3D / LSFF22.W3D", "packed / LSFF22.dds", "48320fb8eace20d4 / e7dbe3d342c220fc", "YES", "AmericaJetF-22A_AA; TurkeyJetKAAN", "YES (two hashes both live)", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("11", "Falcon", "LSFF16C.W3D", "LSFF16C.tga", "83a6c19d1a2c2a71", "NO", "same as 06", "NO", "Pakistan", "F-16A MLU", "PakistanJetF16AMLU", "legacy multirole", "slot 7", "DUPLICATE_ALIAS"),
        ("12", "F18PROWLER", "EA18G / LSFEA18G / US_EA18G", "LSFEA18G.dds", "same as 01/09", "YES identity", "AmericaJetEA18G", "NO extra Prowler mesh", "-", "-", "-", "-", "-", "DUPLICATE_ALIAS"),
        ("13", "F18HORNET", "AmF18A.W3D / F18SEA.W3D", "AmF18MA01.tga / F18SEA_*.tga", "81113b17a306d412 / c96e4c9cf302a5b2", "NO", "none", "YES (two distinct unused Hornet hashes)", "-", "-", "-", "-", "-", "NO_REALISTIC_COUNTRY"),
        ("14", "Lightning", "AVLightn_A1.W3D", "AVLightn.dds", "c83af18f3e075a98", "NO as aircraft", "helper of AVLightn (4035 bytes)", "NO", "-", "-", "-", "-", "-", "DUPLICATE_ALIAS"),
        ("15", "auter f22", "LSFF22.W3D", "LSFF22.dds", "e7dbe3d342c220fc", "YES", "TurkeyJetKAAN", "NO vs 10 LSFF22", "-", "-", "-", "-", "-", "DUPLICATE_ALIAS"),
        ("16", "F15strikeEagle", "US_F15E.W3D used; LSFUSAF15E.W3D unused unique", "LSFUSAF15E.dds", "952a869cd89d8e77 / c5b4347d456a185c", "YES for US_F15E; NO for LSFUSAF15E", "AmericaJetF-15E_AA uses US_F15E", "YES unused extra hash", "Saudi Arabia", "F-15S", "SaudiJetF15S", "strike", "SaudiArabia_HeavyAirBaseCommandSet 1", "ADDED_EXACT"),
        ("17", "F2", "JPF2.W3D", "LSFJPF2.dds", "197f5b0832732cad", "YES", "JapanJetF2A", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("18", "F16fighter", "LSFKF16.W3D", "LSFKF16.dds", "edc889829d2bb892", "YES", "TurkeyJetF16Ozgur", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("19", "Tomcat", "Iran_F14A.W3D used; LSFIRF14A.W3D unused extra", "LSFF14A.dds", "e9cd92e67ef753ab / 11aa6372b8b43b74", "YES for Iran_F14A", "IranJetF14A", "YES unused extra Tomcat hash", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("20", "StrikeEagle", "US_F15EX.W3D", "packed", "9eabd3d7c16eef9c", "YES", "AmericaJetAurora / AmericaJetF15E_GBU72", "related to 16", "-", "-", "-", "-", "-", "DUPLICATE_ALIAS"),
        ("21", "J11FLANKER", "LSFJ11B.W3D", "packed", "8b7947638aabc1c0", "YES", "ChinaJetJ11B", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("22", "auterj31", "LSFJ31.W3D", "packed", "82bfb69417a1a5b1", "YES", "ChinaJetJ31 (Germany FCAS uses NVJ31)", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("23", "J10BRAPTOR", "ChJ10B.W3D", "packed", "68193997ec77aefe", "YES", "ChinaJetJ10B (Pakistan J-10CE uses NVJ-10)", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("24", "Qiang5", "QIANG5.W3D", "chq5m.dds", "d4bc2841c6531ea4", "YES", "ChinaJetQ5", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("25", "S6-30superflahker", "RUS_SU30SM2 used; RUSU30.W3D unused unique", "RUSU30MKK.dds", "a0d751cad05e7702 / a7bcee3bd0bb51bb", "YES for SM2; NO for RUSU30", "RussiaJetSu30SM2", "YES unused extra hash", "India", "Su-30MKI", "IndiaJetSu30MKI", "multirole", "India_HeavyAirBaseCommandSet 1", "ADDED_EXACT"),
        ("26", "F16ingLeapard", "CHJH7A.W3D unused extra; CHI_JH7A2/NVJH-7A used", "chfbc.tga", "ce9d3a8b9a0cb8c0", "YES family / NO exact CHJH7A", "ChinaJetJH7A2 uses NVJH-7A; clones use CHI_JH7A2", "YES unused extra JH-7 hash", "-", "-", "-", "-", "-", "NO_REALISTIC_COUNTRY"),
        ("27", "J15A", "J15JZ.W3D", "packed", "2345cdf7e1df4b22", "YES", "ChinaJetJ15", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("28", "J20C", "NVJ-20 live China; LSFJ20.W3D unused unique", "LSFJ20.dds", "222b75c620cab5f6 / 321abab7aec6b792", "YES China object; NO exact LSFJ20", "ChinaJetJ20C uses NVJ-20", "YES unused extra hash", "France", "FCAS NGF", "FranceJetFCASNGF", "air superiority", "France_HeavyAirBaseCommandSet 6", "ADDED_AS_REALISTIC_STANDIN"),
        ("29", "J7chengdu", "LSFJ7 used China; LSFPKJ7/LSFIRJ7 unused unique skins", "LSFPKJ7.dds / LSFIRJ7.dds", "1c512d3753e82c3a / 557322bab379c87c / dc6d62471406d45d", "YES LSFJ7; NO country skins", "ChinaJetJ7", "YES two unused country hashes", "Pakistan / Iran", "F-7PG / F-7N", "PakistanJetF7PG / IranJetF7N", "legacy fighter", "Pakistan_Airfield 8 / Iran_Heavy 4", "ADDED_EXACT"),
        ("30", "Rafale fighter", "LSFRafaleAS.W3D", "packed", "af9f837cc378743c", "YES", "FranceJetRafaleM", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("31", "Mirage 2000d", "LSFMirage2KD.W3D", "packed", "bd121ff24058722b", "YES", "FranceJetMirage2000D", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("32", "StormFighter", "(none)", "-", "-", "NO", "none; BritainJetTempest uses SPEC_OLD_F35", "NO dedicated Storm/Tempest W3D", "-", "-", "-", "-", "-", "MISSING_W3D"),
        ("33", "AuterF2", "LSF02TJ.W3D", "chZBD92.dds", "4a0874f501caa0b9", "YES", "JapanJetF2Kai", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("34", "Shinshin", "LSFSX2.W3D", "SHAXIN2.dds", "f1410feb44057ea6", "YES", "JapanJetX2Shinshin", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("35", "Eagle Japan", "LSFJPF15J.W3D", "LSFJPF15J.dds", "8cf833961173e2be", "YES", "JapanJetF15JKai", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("36", "F4phantom", "JPF4.W3D", "LSFJPF4.dds", "dc72dc5cc2140848", "YES", "IranJetF4E, JapanJetF4EJKai, TurkeyJetF4ETerm, UK Phantom, Germany F-4F", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("37", "F2fighter", "AGMZJPF2G.W3D", "AGMZJPF2G.tga", "36c871e211a4e969", "YES", "JapanJetF2B", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("38", "Mirage2000fighter", "FraMirage2000.W3D", "Mirage2000m.dds", "729bd016f661983e", "YES", "FranceJetMirage20005F", "YES", "-", "-", "-", "-", "-", "USED_ALREADY"),
        ("39", "Mirage21fighter", "LSFFRF1 / LSFMirage3 / LSFMirage5 / UVMirage", "packed", "5e36de7862f9abe7 / 626b2380517289e3 / 96bda9bbadd84b8a / 59f722831a4ecf71", "YES", "France Mirage F1CT/IIIE/5/F1CR, UK Jaguar, Italy AMX", "family used", "-", "-", "-", "-", "-", "USED_ALREADY"),
    ]
    lines = [
        "# DONOR UNUSED AIRCRAFT AUDIT",
        "",
        "Baseline: `final-global-aircraft-complete-v1`",
        f"DATA sha256 `{data_hash}`",
        f"ART sha256 `{art_hash}`",
        "",
        "DONOR_ART is visual-only. No donor Object/Weapon/CommandSet INI was imported.",
        "USA / Russia / China live gameplay files were hash-protected and left unchanged.",
        "",
        "## Per-alias audit",
        "",
        "| # | Alias | Resolved W3D | Texture set | SHA256/16 | Already used? | Existing objects | Unique visual? | Target country | Final identity | Object | Role | CommandSet/Slot | Result |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    lines += [
        "",
        "## Unused aliases (still unused after this pass)",
        "",
        "These remain unused so they can be assigned manually:",
        "",
        "1. **F18G / F18prowler fighter / F18PROWLER extra meshes** `EA18G.W3D` (sha `4ed1dceb834b031b`) and `LSFEA18G.W3D` (sha `4a28b58c20762da1`). Growler identity already live as `AmericaJetEA18G` (`US_EA18G`). No Australia faction. Do not invent German/French/Italian EA-18G service.",
        "2. **F18HORNET** `AmF18A.W3D` (sha `81113b17a306d412`, 214327 bytes, textures AmF18MA01/02) and `F18SEA.W3D` (sha `c96e4c9cf302a5b2`, 559006 bytes, textures F18SEA_1/2/3). Unique unused Hornets. No Australia/Canada/Finland/Spain/Switzerland faction exists in this build.",
        "3. **StormFighter** — no dedicated Tempest/Storm W3D in DONOR_ART. UK Tempest already uses `SPEC_OLD_F35`.",
        "4. **F16ingLeapard extra** `CHJH7A.W3D` (sha `ce9d3a8b9a0cb8c0`). JH-7 family; China already has `ChinaJetJH7A2` on `NVJH-7A`. No realistic non-China JH-7 operator among playable factions.",
        "5. **Tomcat extra** `LSFIRF14A.W3D` (sha `11aa6372b8b43b74`, 311558 bytes). Iran already operates the live `Iran_F14A` Tomcat. Iran is the only realistic F-14 operator; live object was not overwritten.",
        "6. **Lighting helper** `AVLightn_A1.W3D` (4035 bytes) — duplicate helper, not a second aircraft.",
        "",
        "Helper/duplicate aliases not given slots: Falcon (11), Lightning (14), auter f22 (15), StrikeEagle (20), F18PROWLER (12).",
        "",
        "## New aircraft this pass",
        "",
        "| Object | Country | Identity | Role | W3D | Scale | CommandSet | Slot |",
        "|---|---|---|---|---|---|---|---|",
        "| PakistanJetF16AMLU | Pakistan | F-16A MLU | legacy multirole | LSFF16C | 0.90 | Pakistan_AirfieldCommandSet | 7 |",
        "| PakistanJetF7PG | Pakistan | F-7PG | legacy fighter | LSFPKJ7 | 0.86 | Pakistan_AirfieldCommandSet | 8 |",
        "| JapanJetF15J | Japan | F-15J | air superiority | LSFUSAF15C | 1.02 | Japan_HeavyAirBaseCommandSet | 9 |",
        "| IsraelJetF15CBaz | Israel | F-15C Baz | interceptor | US_F15C | 1.00 | Israel_HeavyAirBaseCommandSet | 3 |",
        "| FranceJetFCASNGF | France | FCAS NGF | air superiority | LSFJ20 | 1.00 | France_HeavyAirBaseCommandSet | 6 |",
        "| SaudiJetF15S | Saudi Arabia | F-15S | strike | LSFUSAF15E | 1.05 | SaudiArabia_HeavyAirBaseCommandSet | 1 |",
        "| IndiaJetSu30MKI | India | Su-30MKI | multirole | RUSU30 | 0.92 | India_HeavyAirBaseCommandSet | 1 |",
        "| IranJetF7N | Iran | F-7N | legacy fighter | LSFIRJ7 | 0.86 | Iran_HeavyAirBaseCommandSet | 4 |",
        "",
        "Existing aircraft visually upgraded: **0** (no live USA/RU/CN/UK/DE/IT object Model= lines were rewritten).",
        "",
        "G. Existing aircraft visually upgraded: 0",
        "H. Added per country: Pakistan 2, Japan 1, Israel 1, France 1, Saudi Arabia 1, India 1, Iran 1",
        "",
    ]
    text = "\n".join(lines) + "\n"
    (out / "DONOR_UNUSED_AIRCRAFT_AUDIT.md").write_text(text)
    (ROOT / "DONOR_UNUSED_AIRCRAFT_AUDIT.md").write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/donor_unused_pack"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    ART_CACHE.mkdir(parents=True, exist_ok=True)

    gen.main()
    overlay = collect_overlay()
    fr.parse_check(overlay)
    print("overlay parser PASS")

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

    # dump packed portraits sources
    packed_art_leaf = {}
    for key, (name, blob) in art_map.items():
        packed_art_leaf[name.split("\\")[-1].lower()] = blob

    protect_hash = {}
    cs_probe = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n in PROTECT_SETS:
        protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        print("protect", n, protect_hash[n][:16])

    usa_ru_cn_file_hash = {}
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        if any(s in key for s in (
            "united states of america",
            "armed forces of russian federation",
            "\\pla\\",
            "\\specter\\pla\\",
        )):
            usa_ru_cn_file_hash[key] = hashlib.sha256(blob).hexdigest()

    # keep-slot occupancy
    for set_name, keep in KEEP_SLOTS.items():
        block = ch.grab_block(cs_probe, set_name)
        for slot, btn in keep.items():
            if f"{slot} = {btn}" not in block and f"{slot}={btn}" not in block:
                # allow whitespace variants
                if not re.search(rf"^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", block, re.M):
                    raise SystemExit(f"keep-slot missing {set_name} {slot} {btn}")

    cs_text = cs_probe
    for set_name, adds in gen.SLOT_ADDS.items():
        old = ch.grab_block(cs_text, set_name)
        new = rebuild_commandset(old, adds)
        # preserve Rally 13 / Sell 14 if present
        old_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", old, re.M)}
        new_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", new, re.M)}
        for k in (13, 14):
            if k in old_slots and new_slots.get(k) != old_slots[k]:
                raise SystemExit(f"{set_name} rally/sell changed")
        if "Command_Upgrade_NuclearTipWarhead2" in old and "Command_Upgrade_NuclearTipWarhead2" not in new:
            raise SystemExit(f"{set_name} lost nuclear")
        cs_text = replace_cs(cs_text, set_name, new)
        print("slot", set_name, adds)

    cs_text = inline_buttons(cs_text, gen.buttons_text())
    data_map["data\\ini\\commandset.ini"] = (
        data_map["data\\ini\\commandset.ini"][0],
        ch.lf(cs_text.encode("latin1")),
    )

    w_key = "data\\ini\\weapon.ini"
    w_name, w_blob = data_map[w_key]
    w_new = inline_weapons(w_blob.decode("latin1"), gen.WEAPONS)
    data_map[w_key] = (w_name, ch.lf(w_new.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(gen.CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    # portraits
    src_files = {}
    for dest_name, src_name in gen.PORTRAIT_SRC.items():
        src = find_art_file(src_name)
        if src is None and src_name.lower() in packed_art_leaf:
            tmp = ART_CACHE / src_name
            tmp.write_bytes(packed_art_leaf[src_name.lower()])
            src = tmp
        if src is None:
            raise SystemExit(f"missing portrait source {src_name}")
        src_files[dest_name] = src
        tga = eu.make_portrait_any(src)
        art_dest = "Art\\Textures\\" + dest_name
        key = ch.norm_key(art_dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (art_dest, tga)
        print("portrait", dest_name, "from", src.name)

    mi_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    mi_name, mi_bytes = data_map[mi_key]
    overlay_portraits = (PATCH / "INI/MappedImages/HandCreated/zDonorUnused_AirbasePortrait_Images.INI").read_text(encoding="ascii")
    mi_text = mi_bytes.decode("latin1")
    if "MappedImage SPEC_PakistanF16AMLU" not in mi_text:
        if not mi_text.endswith("\n"):
            mi_text += "\n"
        mi_text += "\n" + overlay_portraits
    data_map[mi_key] = (mi_name, ch.lf(mi_text.encode("latin1")))

    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    packed_tex_keys = {k.split("\\")[-1].lower() for k in art_map if "textures" in k}
    for name in ART_INJECT:
        src = find_art_file(name)
        if src is None:
            raise SystemExit(f"missing W3D {name}")
        dest = "Art\\W3D\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    for name in TEX_INJECT:
        src = find_art_file(name)
        if src is None:
            if name.lower() in packed_tex_keys:
                print("skip missing donor tex, packed has", name)
                continue
            raise SystemExit(f"missing tex {name}")
        if name.lower() in SHARED_NO_OVERWRITE and name.lower() in packed_tex_keys:
            print("keep packed shared tex", name)
            continue
        dest = "Art\\Textures\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    print("ART injected")

    # validations on overlay objects
    obj_names = [s["obj"] for s in gen.AIRCRAFT]
    if len(obj_names) != len(set(obj_names)):
        raise SystemExit("duplicate new object names")
    new_wpn = re.findall(r"^Weapon (\S+)", gen.WEAPONS, re.M)
    if len(new_wpn) != len(set(new_wpn)):
        raise SystemExit("duplicate new weapons")
    for spec in gen.AIRCRAFT:
        errs = e7.balanced_end((PATCH / spec["rel"]).read_text(encoding="ascii"), spec["obj"])
        if errs:
            raise SystemExit(f"End balance {spec['obj']}: {errs}")
        if re.search(r"Animation\s*=", (PATCH / spec["rel"]).read_text(encoding="ascii")):
            raise SystemExit(f"Animation= on {spec['obj']}")

    # projectile refs
    for wpn_name in new_wpn:
        m = re.search(rf"^Weapon {re.escape(wpn_name)}\s*\n(.*?)(?:^End\s*$)", gen.WEAPONS, re.M | re.S)
        if not m:
            continue
        pm = re.search(r"ProjectileObject = (\S+)", m.group(1))
        if pm and pm.group(1) not in PROJECTILES:
            raise SystemExit(f"bad projectile {wpn_name} -> {pm.group(1)}")
    print("projectile refs PASS")

    # rebuild BIGs
    data_files = {data_map[k][0]: data_map[k][1] for k in data_keys}
    art_files = {art_map[k][0]: art_map[k][1] for k in art_keys}
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(ch.build_big(data_files))
    out_art.write_bytes(ch.build_big(art_files))
    dh = sha256(out_data)
    ah = sha256(out_art)
    print("DATA sha256", dh)
    print("ART sha256", ah)

    # re-extract validation
    v_entries, v_raw = ch.read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[ch.norm_key(name)] = (name, v_raw[off : off + size])
    va_entries, va_raw = ch.read_big(out_art)
    va_w3d = set()
    va_tex = set()
    for name, off, size in va_entries:
        leaf = name.split("\\")[-1].lower()
        if leaf.endswith(".w3d"):
            va_w3d.add(leaf.replace(".w3d", ""))
        if leaf.endswith((".dds", ".tga")):
            va_tex.add(leaf)

    vcs = v_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n, h in protect_hash.items():
        got = hashlib.sha256(ch.grab_block(vcs, n).encode("latin1")).hexdigest()
        if got != h:
            raise SystemExit(f"PROTECTED CommandSet changed {n}")
    print("USA/RU/CN CommandSet hash PASS")

    for key, h in usa_ru_cn_file_hash.items():
        if key not in v_map:
            raise SystemExit(f"protected file missing {key}")
        got = hashlib.sha256(v_map[key][1]).hexdigest()
        if got != h:
            raise SystemExit(f"PROTECTED file changed {key}")
    print("USA/RU/CN object INI hash PASS")

    for set_name, btn in REGRESS.items():
        if btn not in ch.grab_block(vcs, set_name):
            raise SystemExit(f"regression missing {set_name} {btn}")
    print("country regression menus PASS")

    for set_name, adds in gen.SLOT_ADDS.items():
        block = ch.grab_block(vcs, set_name)
        slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M)}
        for slot, btn in adds.items():
            if slots.get(slot) != btn:
                raise SystemExit(f"{set_name} slot {slot} != {btn}")
        if slots.get(13) not in (None, "Command_SetRallyPoint") and "Rally" not in slots.get(13, ""):
            # Israel/Pakistan/France/Japan/India/Saudi/Iran Heavy have Rally at 13
            pass
        if 13 in slots and slots[13] != "Command_SetRallyPoint" and set_name != "IranAirfieldCommandSet":
            # some airfields use Upgrade as 13 historically; our edited sets should keep original
            orig = ch.grab_block(cs_probe, set_name)
            orig_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", orig, re.M)}
            if orig_slots.get(13) != slots.get(13):
                raise SystemExit(f"{set_name} slot 13 changed {orig_slots.get(13)} -> {slots.get(13)}")
        if slots.get(14) != "Command_Sell":
            orig = ch.grab_block(cs_probe, set_name)
            orig_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", orig, re.M)}
            if orig_slots.get(14) != slots.get(14):
                raise SystemExit(f"{set_name} slot 14 changed")
        # unique 1-12
        vis = [slots[i] for i in range(1, 13) if i in slots]
        if len(vis) != len(set(vis)):
            raise SystemExit(f"{set_name} duplicate 1-12")
        print("menu", set_name, "1-12 OK rally/sell preserved")

    # button declaration order
    btn_decl = set(re.findall(r"^CommandButton (\S+)", vcs, re.M))
    for spec in gen.AIRCRAFT:
        btn = f"Command_Construct{spec['obj']}"
        idx_btn = vcs.find(f"CommandButton {btn}")
        for set_name, adds in gen.SLOT_ADDS.items():
            if btn in adds.values():
                idx_set = vcs.find(f"CommandSet {set_name}")
                if idx_btn < 0 or idx_set < 0 or idx_btn > idx_set:
                    raise SystemExit(f"button {btn} not declared before {set_name}")
    print("button declaration order PASS")

    # objects unique + models exist
    obj_pat = re.compile(r"^Object\s+(\S+)", re.M)
    all_objs = []
    for key, (name, blob) in v_map.items():
        if key.endswith(".ini"):
            all_objs.extend(obj_pat.findall(blob.decode("latin1")))
    if len(all_objs) != len(set(all_objs)):
        from collections import Counter
        dups = [k for k, n in Counter(all_objs).items() if n > 1]
        # some packed files already have known dups; only fail on OUR new objects
        ours = [o for o in dups if o in obj_names]
        if ours:
            raise SystemExit(f"duplicate objects {ours}")
    for spec in gen.AIRCRAFT:
        if spec["obj"] not in all_objs:
            raise SystemExit(f"missing packed object {spec['obj']}")
        if spec["model"].lower() not in va_w3d:
            raise SystemExit(f"missing W3D {spec['model']}")
        por = spec["portrait"].lower() + ".tga"
        if por not in va_tex:
            raise SystemExit(f"missing portrait tex {por}")
    print("object/W3D/portrait existence PASS")

    # CommandSet refs to our buttons exist
    for spec in gen.AIRCRAFT:
        btn = f"Command_Construct{spec['obj']}"
        if f"CommandButton {btn}" not in vcs:
            raise SystemExit(f"missing CommandButton {btn}")

    # nuclear / fighter-heavy architecture
    ahb = ch.grab_block(vcs, "America_HeavyAirBaseCommandSet")
    if "Command_Upgrade_NuclearTipWarhead2" not in ahb:
        raise SystemExit("USA Heavy nuclear missing")
    if "Command_ConstructAmericaJetB2" not in ahb:
        raise SystemExit("USA Heavy B2 missing")
    print("Nuclear/airbase architecture PASS")

    # overlay End balance on packed new files
    for spec in gen.AIRCRAFT:
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        text = v_map[ch.norm_key(dest)][1].decode("latin1")
        errs = e7.balanced_end(text, spec["obj"])
        if errs:
            raise SystemExit(errs)
        if "\r" in text:
            raise SystemExit(f"CRLF in {spec['obj']}")
    print("INI parser/End PASS")

    write_audit(out, dh, ah, {})
    write_install(out)
    zpath = out / "DONOR_UNUSED_AIRCRAFT_COMPLETION.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(out / "DONOR_UNUSED_AIRCRAFT_AUDIT.md", "DONOR_UNUSED_AIRCRAFT_AUDIT.md")
        zf.write(out / "INSTALL.txt", "INSTALL.txt")
    print("ZIP", zpath, zpath.stat().st_size)
    (out / "PACK_REPORT.txt").write_text(
        f"DATA sha256 {dh}\nART sha256 {ah}\nZIP sha256 {sha256(zpath)}\n"
        f"new objects {len(gen.AIRCRAFT)}\n"
    )
    (ROOT / "DONOR_UNUSED_AIRCRAFT_AUDIT.md").write_text((out / "DONOR_UNUSED_AIRCRAFT_AUDIT.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
