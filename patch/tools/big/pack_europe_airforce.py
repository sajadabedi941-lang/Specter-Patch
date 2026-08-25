#!/usr/bin/env python3
"""Pack Germany/Italy/UK air forces into _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Builds on the France helicopter-force pack. Does not rewrite Russia/China/France menus.
Donor meshes are appearance-only; gameplay names are the real aircraft.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch
import pack_france_airforce as fr

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
DONORS = [
    Path("/tmp/donor_europe_air"),
    Path("/tmp/donor_europe_extra"),
    Path("/tmp/donor_france_air"),
]
BASE_DATA = Path("/tmp/france_helicopter_force/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/france_helicopter_force/_SPEC_ART_ONE.big")
META = json.loads((ROOT / "patch/tools/big/europe_airforce_meta.json").read_text(encoding="ascii"))

CSF_LABELS = dict(META["csf"])
# Richer control-bar tooltips (ASCII). Display names stay the real aircraft.
CSF_LABELS.update(
    {
        "CONTROLBAR:ToolTipGermanyJetTyphoonT4": "German Typhoon Tranche 4. Meteor and IRIS-T.",
        "CONTROLBAR:ToolTipGermanyJetTyphoonECR": "German Typhoon ECR. Taurus and IRIS-T.",
        "CONTROLBAR:ToolTipGermanyJetTornadoIDS": "German Tornado IDS. Bombs and Paveway.",
        "CONTROLBAR:ToolTipGermanyJetTornadoECR": "German Tornado ECR. Taurus and AIM-9.",
        "CONTROLBAR:ToolTipGermanyJetF35A": "German F-35A. JDAM and AMRAAM.",
        "CONTROLBAR:ToolTipGermanyJetMiG29G": "German MiG-29G. AMRAAM and AIM-9.",
        "CONTROLBAR:ToolTipGermanyJetAlphaJet": "German Alpha Jet. Light strike.",
        "CONTROLBAR:ToolTipGermanyJetF4F": "German F-4F Phantom. AMRAAM and AIM-9.",
        "CONTROLBAR:ToolTipGermanyJetTornadoADV": "German Tornado ADV. Meteor and AIM-9.",
        "CONTROLBAR:ToolTipGermanyJetMako": "German Mako light fighter. JDAM and IRIS-T.",
        "CONTROLBAR:ToolTipGermanyJetA400M": "German A400M Atlas transport.",
        "CONTROLBAR:ToolTipGermanyJetC130J": "German C-130J transport.",
        "CONTROLBAR:ToolTipGermanyAircraftE3": "German E-3 AWACS.",
        "CONTROLBAR:ToolTipGermanyDroneHeronTP": "German Heron TP. Brimstone.",
        "CONTROLBAR:ToolTipGermanyHelicopterTigerUHT": "German Tiger UHT. Cannon, missiles, rockets.",
        "CONTROLBAR:ToolTipGermanyHelicopterNH90": "German NH90 transport helicopter.",
        "CONTROLBAR:ToolTipGermanyHelicopterCH53": "German CH-53 heavy transport helicopter.",
        "CONTROLBAR:ToolTipGermanyHelicopterH145M": "German H145M utility helicopter.",
        "CONTROLBAR:ToolTipItalyJetTyphoon": "Italian Eurofighter Typhoon. Meteor and IRIS-T.",
        "CONTROLBAR:ToolTipItalyJetF35A": "Italian F-35A. JDAM and AMRAAM.",
        "CONTROLBAR:ToolTipItalyJetF35B": "Italian F-35B. JDAM and AIM-9.",
        "CONTROLBAR:ToolTipItalyJetAMX": "Italian AMX. Bombs and Paveway.",
        "CONTROLBAR:ToolTipItalyJetTornadoIDS": "Italian Tornado IDS. Storm Shadow.",
        "CONTROLBAR:ToolTipItalyJetTornadoECR": "Italian Tornado ECR. Storm Shadow and AIM-9.",
        "CONTROLBAR:ToolTipItalyJetHarrierII": "Italian Harrier II. Paveway and AIM-9.",
        "CONTROLBAR:ToolTipItalyJetF16": "Italian F-16. AMRAAM and AIM-9.",
        "CONTROLBAR:ToolTipItalyJetM346FA": "Italian M-346FA. JDAM and IRIS-T.",
        "CONTROLBAR:ToolTipItalyJetMB339": "Italian MB-339. Light strike.",
        "CONTROLBAR:ToolTipItalyJetC130J": "Italian C-130J transport.",
        "CONTROLBAR:ToolTipItalyJetC27J": "Italian C-27J Spartan transport.",
        "CONTROLBAR:ToolTipItalyAircraftG550CAEW": "Italian G550 CAEW AWACS.",
        "CONTROLBAR:ToolTipItalyDroneMQ9": "Italian MQ-9. Brimstone.",
        "CONTROLBAR:ToolTipItalyHelicopterAW249": "Italian AW249. Cannon, missiles, rockets.",
        "CONTROLBAR:ToolTipItalyHelicopterA129": "Italian A129 Mangusta. Cannon, missiles, rockets.",
        "CONTROLBAR:ToolTipItalyHelicopterNH90": "Italian NH90 transport helicopter.",
        "CONTROLBAR:ToolTipItalyHelicopterAW101": "Italian AW101 transport helicopter.",
        "CONTROLBAR:ToolTipItalyHelicopterAW139": "Italian AW139 utility helicopter.",
        "CONTROLBAR:ToolTipBritainJetF35B": "British F-35B. Paveway and AMRAAM.",
        "CONTROLBAR:ToolTipBritainJetTyphoonFGR4": "British Typhoon FGR4. Meteor and Brimstone.",
        "CONTROLBAR:ToolTipBritainJetTyphoonT3": "British Typhoon Tranche 3. Meteor and ASRAAM.",
        "CONTROLBAR:ToolTipBritainJetHarrierGR9": "British Harrier GR9. Paveway and Brimstone.",
        "CONTROLBAR:ToolTipBritainJetTornadoGR4": "British Tornado GR4. Storm Shadow and Paveway.",
        "CONTROLBAR:ToolTipBritainJetJaguarGR3": "British Jaguar GR3. Bombs and Paveway.",
        "CONTROLBAR:ToolTipBritainJetSeaHarrierFA2": "British Sea Harrier FA2. AMRAAM and ASRAAM.",
        "CONTROLBAR:ToolTipBritainJetPhantomFG1": "British Phantom FG1. AMRAAM and ASRAAM.",
        "CONTROLBAR:ToolTipBritainJetLightningF6": "British Lightning F6. AMRAAM and ASRAAM.",
        "CONTROLBAR:ToolTipBritainJetHawk200": "British Hawk 200. Light strike.",
        "CONTROLBAR:ToolTipBritainJetA400M": "British A400M transport.",
        "CONTROLBAR:ToolTipBritainJetC17": "British C-17 transport.",
        "CONTROLBAR:ToolTipBritainAircraftE7": "British E-7 Wedgetail AWACS.",
        "CONTROLBAR:ToolTipBritainDroneMQ9": "British MQ-9 Reaper. Brimstone.",
        "CONTROLBAR:ToolTipBritainBomberVulcan": "British Vulcan. Carpet bombing and Storm Shadow.",
        "CONTROLBAR:ToolTipBritainHelicopterApache": "British Apache AH-64E. Cannon, Hellfire, rockets.",
        "CONTROLBAR:ToolTipBritainHelicopterChinook": "British Chinook transport helicopter.",
        "CONTROLBAR:ToolTipBritainHelicopterMerlin": "British Merlin transport helicopter.",
        "CONTROLBAR:ToolTipBritainHelicopterWildcat": "British Wildcat utility helicopter.",
        "CONTROLBAR:ToolTipBritainHelicopterPuma": "British Puma transport helicopter.",
    }
)

COUNTRIES = ("Germany", "Italy", "Britain")

NATO_REMOVED = []
for c in COUNTRIES:
    NATO_REMOVED.extend(
        [
            f"Command_Construct{c}JetRafaleF3",
            f"Command_Construct{c}JetF35C",
            f"Command_Construct{c}JetEF2000T4",
            f"Command_Construct{c}JetEA18G",
            f"Command_Construct{c}JetF16DBlk52",
            f"Command_Construct{c}JetF35C_AA",
            f"Command_Construct{c}JetEF2000T4_AA",
            f"Command_Construct{c}JetEF2000T4_CAS",
            f"Command_Construct{c}HelicopterAH64E",
            f"Command_Construct{c}JetE3AAWACS",
            f"Command_Construct{c}HelicopterUH60",
            f"Command_Construct{c}HelicopterCH47F",
        ]
    )
# Old NATO Tornado ECR button name equals the new German/Italian Tornado ECR button.
# Do not treat those two as NATO leftovers.

PROTECT_SETS = [
    "FranceAirfieldCommandSet",
    "France_LargeAirBaseCommandSet",
    "France_HeavyAirBaseCommandSet",
    "France_HelicopterBaseCommandSet",
    "FranceDozerCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
]

PORTRAIT_SRC = {
    "SPEC_GermanyTyphoonT4.tga": "Art/Textures/TyphoonStrike1.tga",
    "SPEC_GermanyTyphoonECR.tga": "Art/Textures/LSFEUEF2000.tga",
    "SPEC_GermanyTornadoIDS.tga": "Art/Textures/TornadoStrike.tga",
    "SPEC_GermanyTornadoECR.tga": "Art/Textures/LSFTornado.dds",
    "SPEC_GermanyF35A.tga": "Art/Textures/F35tb.tga",
    "SPEC_GermanyMiG29G.tga": "Art/Textures/Mig29AlgeriaTB.tga",
    "SPEC_GermanyAlphaJet.tga": "Art/Textures/AvHawk.dds",
    "SPEC_GermanyF4F.tga": "Art/Textures/LSFJPF4TB.tga",
    "SPEC_GermanyTornadoADV.tga": "Art/Textures/LSFEF2000.tga",
    "SPEC_GermanyMako.tga": "Art/Textures/F16TB.tga",
    "SPEC_GermanyA400M.tga": "Art/Textures/C17GlobalMasterTB.tga",
    "SPEC_GermanyC130J.tga": "Art/Textures/LSFUSAC130.tga",
    "SPEC_GermanyE3.tga": "Art/Textures/E3USA.tga",
    "SPEC_GermanyHeronTP.tga": "Art/Textures/AVReaper.dds",
    "SPEC_GermanyTigerUHT.tga": "Art/Textures/LSFGETiger.dds",
    "SPEC_GermanyNH90.tga": "Art/Textures/EUNH90TB.tga",
    "SPEC_GermanyCH53.tga": "Art/Textures/CH53tb.tga",
    "SPEC_GermanyH145M.tga": "Art/Textures/FenneckTb.tga",
    "SPEC_GermanyHelicopterBase.tga": "Art/Textures/CH53tb.tga",
    "SPEC_ItalyTyphoon.tga": "Art/Textures/LSFEUEF2000.tga",
    "SPEC_ItalyF35A.tga": "Art/Textures/F35tb.tga",
    "SPEC_ItalyF35B.tga": "Art/Textures/F35BTB.tga",
    "SPEC_ItalyAMX.tga": "Art/Textures/LSFMirage5.dds",
    "SPEC_ItalyTornadoIDS.tga": "Art/Textures/TornadoStrike.tga",
    "SPEC_ItalyTornadoECR.tga": "Art/Textures/LSFTornado.dds",
    "SPEC_ItalyHarrierII.tga": "Art/Textures/LSFAV8B.dds",
    "SPEC_ItalyF16.tga": "Art/Textures/F16TB.tga",
    "SPEC_ItalyM346FA.tga": "Art/Textures/AvHawk.dds",
    "SPEC_ItalyMB339.tga": "Art/Textures/LSFF16C.tga",
    "SPEC_ItalyC130J.tga": "Art/Textures/LSFUSAC130.tga",
    "SPEC_ItalyC27J.tga": "Art/Textures/Avionac130TB.tga",
    "SPEC_ItalyG550CAEW.tga": "Art/Textures/avionE737TB.tga",
    "SPEC_ItalyMQ9.tga": "Art/Textures/AVReaper.dds",
    "SPEC_ItalyAW249.tga": "Art/Textures/LSFAH64D.dds",
    "SPEC_ItalyA129.tga": "Art/Textures/AH1WTB.tga",
    "SPEC_ItalyNH90.tga": "Art/Textures/EUNH90TB.tga",
    "SPEC_ItalyAW101.tga": "Art/Textures/EUNH90TB.tga",
    "SPEC_ItalyAW139.tga": "Art/Textures/LSFRUMi171.dds",
    "SPEC_ItalyHelicopterBase.tga": "Art/Textures/AH1WTB.tga",
    "SPEC_BritainF35B.tga": "Art/Textures/AmericaF35BJSFTB.tga",
    "SPEC_BritainTyphoonFGR4.tga": "Art/Textures/TyphoonStrike1.tga",
    "SPEC_BritainTyphoonT3.tga": "Art/Textures/LSFEUEF2000.tga",
    "SPEC_BritainHarrierGR9.tga": "Art/Textures/HarriermMain.dds",
    "SPEC_BritainTornadoGR4.tga": "Art/Textures/TornadoStrike.tga",
    "SPEC_BritainJaguarGR3.tga": "Art/Textures/JaguarStrike.tga",
    "SPEC_BritainSeaHarrierFA2.tga": "Art/Textures/LSFAV8B.dds",
    "SPEC_BritainPhantomFG1.tga": "Art/Textures/LSFJPF4TB.tga",
    "SPEC_BritainLightningF6.tga": "Art/Textures/LSFMirage5.dds",
    "SPEC_BritainHawk200.tga": "Art/Textures/AvHawk.dds",
    "SPEC_BritainA400M.tga": "Art/Textures/C17GlobalMasterTB.tga",
    "SPEC_BritainC17.tga": "Art/Textures/IUCC17THXNew.dds",
    "SPEC_BritainE7.tga": "Art/Textures/avionE737TB.tga",
    "SPEC_BritainMQ9.tga": "Art/Textures/AVReaper.dds",
    "SPEC_BritainVulcan.tga": "Art/Textures/B52TB.tga",
    "SPEC_BritainApache.tga": "Art/Textures/AH64ArabieSTB.tga",
    "SPEC_BritainChinook.tga": "Art/Textures/CH47TB.tga",
    "SPEC_BritainMerlin.tga": "Art/Textures/EUNH90TB.tga",
    "SPEC_BritainWildcat.tga": "Art/Textures/AH7TB.tga",
    "SPEC_BritainPuma.tga": "Art/Textures/AH6AmTB.tga",
    "SPEC_BritainHelicopterBase.tga": "Art/Textures/CH47TB.tga",
}

ART_FILES = [
    # Typhoon
    "Art/w3d/LSFEUEF2000.W3D",
    "Art/w3d/LSFEUEF2000d.W3D",
    "Art/w3d/LSFEUEF2000k.W3D",
    "Art/Textures/LSFEUEF2000.tga",
    "Art/Textures/LSFEUEF2000d.tga",
    "Art/Textures/LSFEF2000.tga",
    # Tornado / Jaguar
    "Art/w3d/LSFTornado.W3D",
    "Art/w3d/LSFTornadod.W3D",
    "Art/w3d/LSFTornadok.W3D",
    "Art/Textures/LSFTornado.dds",
    "Art/Textures/EuropeAirWmap.tga",
    # MiG-29G
    "Art/w3d/LSFruMiG29.W3D",
    "Art/w3d/LSFruMiG29d.W3D",
    "Art/w3d/LSFruMiG29k.W3D",
    "Art/Textures/LSFRUMIG29.dds",
    "Art/Textures/LSFHK29_m.tga",
    # F-16 / Mako
    "Art/w3d/LSFF16.W3D",
    "Art/w3d/LSFF16d.W3D",
    "Art/w3d/LSFF16k.W3D",
    "Art/Textures/LSFUSAF16.dds",
    "Art/Textures/LSFUSAF16d.dds",
    "Art/Textures/LSFUSAF16k.dds",
    # Phantom
    "Art/w3d/JPF4.W3D",
    "Art/w3d/JPF4D.W3D",
    "Art/w3d/JPF4K.W3D",
    "Art/Textures/LSFJPF4.dds",
    "Art/Textures/LSFJPF4d.dds",
    "Art/Textures/LSFJPF4k.dds",
    # Harrier
    "Art/w3d/LSFAV8B.W3D",
    "Art/w3d/LSFAV8Bd.W3D",
    "Art/w3d/LSFAV8Bk.W3D",
    "Art/Textures/LSFAV8B.dds",
    "Art/Textures/HarriermMain.dds",
    # Vulcan / B-52 donor
    "Art/w3d/LSFUSAB52.W3D",
    "Art/w3d/LSFUSAB52d.W3D",
    "Art/w3d/LSFUSAB52k.W3D",
    "Art/Textures/LSFUSAB52.dds",
    "Art/Textures/LSFUSAB52d.dds",
    "Art/Textures/LSFUSAB52k.dds",
    # Tiger / NH90 / H145 / Apache / Lynx
    "Art/w3d/LSFGETiger.W3D",
    "Art/w3d/LSFGETigerd.W3D",
    "Art/w3d/LSFGETigerk.W3D",
    "Art/Textures/LSFGETiger.dds",
    "Art/w3d/LSFGENH90.W3D",
    "Art/w3d/LSFFenneck.W3D",
    "Art/w3d/LSFFenneckd.W3D",
    "Art/w3d/LSFFenneckk.W3D",
    "Art/Textures/LSFFenneck.dds",
    "Art/w3d/LSFAH64D.W3D",
    "Art/w3d/LSFAH64Dd.W3D",
    "Art/Textures/LSFAH64D.dds",
    "Art/w3d/LSFLynxAHMK.W3D",
    "Art/w3d/KVE737.W3D",
    "Art/Textures/KVE737.dds",
    "Art/w3d/IUAC17HXNew.W3D",
    "Art/Textures/IUCC17THXNew.dds",
    "Art/w3d/AVHawk.W3D",
    "Art/w3d/AVHawk_D.W3D",
    "Art/Textures/AvHawk.dds",
    "Art/w3d/AVReaper.W3D",
    "Art/w3d/AVReaper_D.W3D",
    "Art/Textures/AVReaper.dds",
]

WPN_MARKER = b"\n; ===== SPECTER EUROPE AIRFORCE WEAPONS =====\n"

OBJECT_GLOBS = [
    PATCH / "INI/Object/Specter/German Armed Forces/Airforce",
    PATCH / "INI/Object/Specter/German Armed Forces/Rotary",
    PATCH / "INI/Object/Specter/Italian Armed Forces/Airforce",
    PATCH / "INI/Object/Specter/Italian Armed Forces/Rotary",
    PATCH / "INI/Object/Specter/British Armed Forces/Airforce",
    PATCH / "INI/Object/Specter/British Armed Forces/Rotary",
]


def tga_uncompressed(data: bytes) -> bytes:
    """Convert TGA type 10 (RLE truecolor) to type 2 so make_portrait can read it."""
    img_type = data[2]
    if img_type == 2:
        return data
    if img_type != 10:
        raise SystemExit(f"unsupported TGA type={img_type}")
    idlen = data[0]
    width, height = struct.unpack_from("<HH", data, 12)
    bpp = data[16]
    if bpp not in (24, 32):
        raise SystemExit(f"unsupported TGA bpp={bpp}")
    depth = bpp // 8
    payload = data[18 + idlen :]
    out = bytearray()
    i = 0
    need = width * height
    while len(out) // depth < need:
        packet = payload[i]
        i += 1
        count = (packet & 0x7F) + 1
        if packet & 0x80:
            pix = payload[i : i + depth]
            i += depth
            out.extend(pix * count)
        else:
            n = count * depth
            out.extend(payload[i : i + n])
            i += n
    header = bytearray(data[: 18 + idlen])
    header[2] = 2
    return bytes(header) + bytes(out)


def make_portrait_any(src: Path) -> bytes:
    if src.suffix.lower() == ".tga":
        raw = tga_uncompressed(src.read_bytes())
        tmp = Path("/tmp") / f"portrait_{src.name}"
        tmp.write_bytes(raw)
        return fr.make_portrait(tmp)
    return fr.make_portrait(src)


def find_src(rel: str) -> Path:
    rel_n = rel.replace("\\", "/")
    for root in DONORS:
        p = root / rel_n
        if p.exists():
            return p
        # case variants for w3d folder
        alt = root / rel_n.replace("Art/w3d/", "Art/W3D/").replace("Art/textures/", "Art/Textures/")
        if alt.exists():
            return alt
    raise FileNotFoundError(rel)


def fighter_block(name: str, buttons: list[str]) -> str:
    lines = [f"CommandSet {name}"]
    for i, btn in enumerate(buttons, 1):
        lines.append(f"  {i}  = {btn}")
    lines.append("  13 = Command_SetRallyPoint")
    lines.append("  14 = Command_Sell")
    lines.append("End")
    return "\n".join(lines) + "\n"


def heavy_block(name: str, buttons: list[str]) -> str:
    return fighter_block(name, buttons)


def collect_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    keep_re = re.compile(
        r"^(Germany|Italy|Britain)(Jet|Aircraft|Drone|Bomber|Helicopter)"
    )
    for folder in OBJECT_GLOBS:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.ini")):
            if not keep_re.match(path.stem):
                continue
            dest = "Data\\INI\\" + path.relative_to(PATCH / "INI").as_posix().replace("/", "\\")
            overlay[dest] = ch.lf(path.read_bytes())
    for side, folder in (
        ("Germany", "German Armed Forces"),
        ("Italy", "Italian Armed Forces"),
        ("Britain", "British Armed Forces"),
    ):
        p = PATCH / "INI/Object/Specter" / folder / "Buildings" / f"{side}_HelicopterBase.ini"
        dest = rf"Data\INI\Object\Specter\{folder}\Buildings\{side}_HelicopterBase.ini"
        overlay[dest] = ch.lf(p.read_bytes())
    named = [
        ("INI/Weapon_EuropeAirforce.ini", r"Data\INI\Weapon_EuropeAirforce.ini"),
        ("INI/CommandButton_EuropeAirforce.ini", r"Data\INI\CommandButton_EuropeAirforce.ini"),
        ("INI/MappedImages/HandCreated/zEurope_AirbasePortrait_Images.INI", r"Data\INI\MappedImages\HandCreated\zEurope_AirbasePortrait_Images.INI"),
        ("INI/CommandSet_Germany.ini", r"Data\INI\CommandSet_Germany.ini"),
        ("INI/CommandSet_Italy.ini", r"Data\INI\CommandSet_Italy.ini"),
        ("INI/CommandSet_Britain.ini", r"Data\INI\CommandSet_Britain.ini"),
    ]
    for rel, dest in named:
        overlay[dest] = ch.lf((PATCH / rel).read_bytes())
    return overlay


def split_buttons(text: str) -> tuple[str, dict[str, str]]:
    """Return UNIT_BUILD body and DOZER_CONSTRUCT blocks keyed by country."""
    unit_parts = []
    dozer = {}
    for m in re.finditer(r"CommandButton (\S+)\s*\n.*?^End\s*$", text, re.M | re.S):
        block = m.group(0).rstrip() + "\n"
        name = m.group(1)
        if "DOZER_CONSTRUCT" in block:
            dozer[name] = block
        else:
            unit_parts.append(block)
    return "\n".join(unit_parts).strip() + "\n", dozer


def inline_unit_buttons(cs_text: str, buttons: str) -> str:
    needle = "CommandSet GermanyAirfieldCommandSet"
    idx = cs_text.find(needle)
    if idx < 0:
        raise SystemExit("GermanyAirfieldCommandSet not found")
    for m in re.finditer(r"CommandButton (\S+)\s*\n.*?^End\s*$", buttons, re.M | re.S):
        btn = m.group(1)
        cs_text, n = re.subn(
            rf"CommandButton {re.escape(btn)}\s*\n.*?^End\s*\n?",
            "",
            cs_text,
            count=1,
            flags=re.M | re.S,
        )
        if n:
            print(f"Relocated {btn}")
    idx = cs_text.find(needle)
    cs_text = cs_text[:idx] + buttons.rstrip() + "\n\n" + cs_text[idx:]
    print("Inlined Europe UNIT_BUILD buttons before GermanyAirfieldCommandSet")
    return cs_text


def insert_dozer_buttons(cb_text: str, dozer: dict[str, str]) -> str:
    for country in COUNTRIES:
        btn_name = f"Command_Construct{country}_HelicopterBase"
        block = dozer[btn_name]
        cb_text = re.sub(
            rf"CommandButton {re.escape(btn_name)}\s*\n.*?^End\s*\n?",
            "",
            cb_text,
            count=1,
            flags=re.M | re.S,
        )
        needle = f"CommandButton Command_Construct{country}_HeavyAirBase"
        m = re.search(
            rf"CommandButton Command_Construct{country}_HeavyAirBase\s*\n.*?^End\s*$",
            cb_text,
            re.M | re.S,
        )
        if not m:
            raise SystemExit(f"{needle} not in CommandButton.ini")
        insert_at = m.end()
        cb_text = cb_text[:insert_at] + "\n\n" + block.rstrip() + "\n" + cb_text[insert_at:]
        print(f"Inserted {btn_name} into CommandButton.ini")
    return cb_text


def patch_dozer(cs_text: str, country: str) -> str:
    name = f"{country}DozerCommandSet"
    block = ch.grab_block(cs_text, name)
    heli_btn = f"Command_Construct{country}_HelicopterBase"
    if heli_btn in block:
        print(f"{name} already has Helicopter Base")
        return cs_text
    new_block, n = re.subn(
        r"^( 12\s*=\s*)Command_ConstructAmericaLgm30\s*$",
        rf"\1{heli_btn}",
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit(f"{name} slot 12 is not Command_ConstructAmericaLgm30")
    return fr.replace_block(cs_text, name, new_block)


def insert_heli_commandset(cs_text: str, country: str, heli_btns: list[str]) -> str:
    name = f"{country}_HelicopterBaseCommandSet"
    block = heavy_block(name, heli_btns)
    if f"CommandSet {name}" in cs_text:
        return fr.replace_block(cs_text, name, block)
    heavy_name = f"{country}_HeavyAirBaseCommandSet"
    pat = re.compile(rf"(CommandSet {re.escape(heavy_name)}\s*\n.*?^End\s*$)", re.M | re.S)
    if not pat.search(cs_text):
        raise SystemExit(f"{heavy_name} missing; cannot insert {name}")
    return pat.sub(r"\1\n\n" + block.rstrip() + "\n", cs_text, count=1)


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = ch.parse_csf(data)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value):
            raise SystemExit(f"non-ASCII CSF {key!r}")
        if key in have_idx:
            i = have_idx[key]
            mag, name, _strings = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
            updated += 1
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            added += 1
            have_idx[key] = len(labels) - 1
    print(f"CSF added {added} labels, updated {updated}")
    return ch.build_csf(version, unk, lang, labels)


def rename_nato_collisions(data_map: dict[str, tuple[str, bytes]]) -> None:
    pairs = [
        (r"data\ini\object\specter\german armed forces\nato_systems.ini", "GermanyJetTornadoECR"),
        (r"data\ini\object\specter\italian armed forces\nato_systems.ini", "ItalyJetTornadoECR"),
    ]
    for key, obj in pairs:
        if key not in data_map:
            raise SystemExit(f"missing {key}")
        name, blob = data_map[key]
        text = blob.decode("latin1")
        new, n = re.subn(
            rf"^Object {re.escape(obj)}\s*$",
            f"Object {obj}_NATO",
            text,
            count=1,
            flags=re.M,
        )
        if n != 1:
            raise SystemExit(f"failed to rename {obj} in {name}")
        data_map[key] = (name, ch.lf(new.encode("latin1")))
        print(f"Renamed leftover NATO object {obj} -> {obj}_NATO")


def validate_europe_menus(cs_text: str, cb_text: str) -> None:
    errors = []
    core = set(re.findall(r"^CommandButton (\S+)\s*$", cb_text, re.M))
    want = {
        "Germany": (META["germany_fighters"], META["germany_heavy"], META["germany_heli"]),
        "Italy": (META["italy_fighters"], META["italy_heavy"], META["italy_heli"]),
        "Britain": (META["britain_fighters"], META["britain_heavy"], META["britain_heli"]),
    }
    for country, (fighters, heavy, heli) in want.items():
        names = (
            f"{country}AirfieldCommandSet",
            f"{country}_LargeAirBaseCommandSet",
            f"{country}_HeavyAirBaseCommandSet",
            f"{country}_HelicopterBaseCommandSet",
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
                if btn in NATO_REMOVED:
                    errors.append(f"{name} still has NATO button {btn}")
            slots = [int(x) for x in re.findall(r"^\s*(\d+)\s*=", block, re.M)]
            if len(slots) != len(set(slots)):
                errors.append(f"{name} duplicate slots {slots}")
        fighter = ch.grab_block(cs_text, f"{country}_LargeAirBaseCommandSet")
        airfield = ch.grab_block(cs_text, f"{country}AirfieldCommandSet")
        for btn in fighters:
            if btn not in fighter:
                errors.append(f"{country} fighter menu missing {btn}")
            if btn not in airfield:
                errors.append(f"{country} airfield menu missing {btn}")
        heavy_block_txt = ch.grab_block(cs_text, f"{country}_HeavyAirBaseCommandSet")
        for btn in heavy:
            if btn not in heavy_block_txt:
                errors.append(f"{country} heavy menu missing {btn}")
        for btn in heli:
            if btn in heavy_block_txt:
                errors.append(f"{country} heavy menu still has heli {btn}")
            if btn in fighter:
                errors.append(f"{country} fighter menu still has heli {btn}")
        heli_block = ch.grab_block(cs_text, f"{country}_HelicopterBaseCommandSet")
        for btn in heli:
            if btn not in heli_block:
                errors.append(f"{country} heli menu missing {btn}")
        dozer = ch.grab_block(cs_text, f"{country}DozerCommandSet")
        if f"Command_Construct{country}_HelicopterBase" not in dozer:
            errors.append(f"{country} dozer missing Helicopter Base")
        if "Command_ConstructAmericaLgm30" in dozer:
            errors.append(f"{country} dozer still has AmericaLgm30")
    if errors:
        raise SystemExit("PARSER CHECK FAIL CommandButton refs\n" + "\n".join(errors))
    print("PARSER CHECK PASS CommandButton refs")


def validate_art_models(overlay: dict[str, bytes], art_map: dict[str, tuple[str, bytes]]) -> None:
    errors = []
    w3d = {k.split("\\")[-1].lower() for k in art_map}
    for dest, content in overlay.items():
        if not dest.lower().endswith(".ini"):
            continue
        if "\\object\\" not in dest.lower():
            continue
        text = content.decode("ascii")
        for model in re.findall(r"^\s*Model\s*=\s*(\S+)\s*$", text, re.M):
            key = f"{model}.w3d".lower()
            if key not in w3d:
                errors.append(f"{dest} model {model} missing W3D")
    if errors:
        raise SystemExit("ART CHECK FAIL\n" + "\n".join(errors[:40]))
    print("ART CHECK PASS model W3D refs")


def validate_no_donor_names(csf: bytes) -> None:
    banned = [
        "LSFEUEF2000",
        "LSFTornado",
        "LSFruMiG29",
        "LSFF16",
        "JPF4",
        "LSFAV8B",
        "IUAC17HXNew",
        "LSFUSAC130",
        "LSFUSAB52",
        "LSFGETiger",
        "LSFGENH90",
        "LSFRUMi171",
        "LSFFenneck",
        "LSFAH64D",
        "LSFLynxAHMK",
        "LSFMirage3",
        "LSFMirage5",
        "AVHawk",
        "US_F35A",
        "US_CH47F",
        "KVE737",
        "AVReaper",
    ]
    version, unk, lang, labels = ch.parse_csf(csf)
    errors = []
    for _mag, name, strings in labels:
        if not name.startswith(("CONTROLBAR:", "OBJECT:")):
            continue
        if not any(x in name for x in ("Germany", "Italy", "Britain")):
            continue
        for _sm, value, _ex in strings:
            for b in banned:
                if b.lower() in value.lower():
                    errors.append(f"{name} contains donor {b}: {value!r}")
    if errors:
        raise SystemExit("CSF donor-name FAIL\n" + "\n".join(errors[:20]))
    print("CSF CHECK PASS no donor names on DE/IT/UK labels")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/europe_airforce_expansion"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    overlay = collect_overlay()
    fr.parse_check(overlay)

    buttons = overlay[r"Data\INI\CommandButton_EuropeAirforce.ini"].decode("ascii")
    unit_body, dozer = split_buttons(buttons)

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

    protect_before = {n: ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), n) for n in PROTECT_SETS}

    rename_nato_collisions(data_map)

    cs_key = "data\\ini\\commandset.ini"
    cb_key = "data\\ini\\commandbutton.ini"
    cs_name, cs_blob = data_map[cs_key]
    cb_name, cb_blob = data_map[cb_key]
    cs_text = cs_blob.decode("latin1")
    cb_text = cb_blob.decode("latin1")

    cb_text = insert_dozer_buttons(cb_text, dozer)
    data_map[cb_key] = (cb_name, ch.lf(cb_text.encode("latin1")))

    cs_text = inline_unit_buttons(cs_text, unit_body)
    for country, fkey, hkey, rkey in (
        ("Germany", "germany_fighters", "germany_heavy", "germany_heli"),
        ("Italy", "italy_fighters", "italy_heavy", "italy_heli"),
        ("Britain", "britain_fighters", "britain_heavy", "britain_heli"),
    ):
        fighters = META[fkey]
        heavy = META[hkey]
        heli = META[rkey]
        cs_text = fr.replace_block(cs_text, f"{country}AirfieldCommandSet", fighter_block(f"{country}AirfieldCommandSet", fighters))
        cs_text = fr.replace_block(cs_text, f"{country}_LargeAirBaseCommandSet", fighter_block(f"{country}_LargeAirBaseCommandSet", fighters))
        cs_text = fr.replace_block(cs_text, f"{country}_HeavyAirBaseCommandSet", heavy_block(f"{country}_HeavyAirBaseCommandSet", heavy))
        cs_text = insert_heli_commandset(cs_text, country, heli)
        cs_text = patch_dozer(cs_text, country)
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    validate_europe_menus(cs_text, cb_text)
    ch.validate_commandset_button_refs(cs_text, cb_text)

    protect_after = {n: ch.grab_block(cs_text, n) for n in PROTECT_SETS}
    for n in PROTECT_SETS:
        if protect_before[n] != protect_after[n]:
            raise SystemExit(f"PROTECTED CommandSet mutated: {n}")
    print("PROTECT CHECK PASS France/China/Russia CommandSets unchanged")

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    extra_wpn = overlay[r"Data\INI\Weapon_EuropeAirforce.ini"]
    idx = wpn_blob.find(WPN_MARKER)
    if idx >= 0:
        wpn_blob = wpn_blob[:idx].rstrip() + WPN_MARKER + extra_wpn
    else:
        wpn_blob = wpn_blob.rstrip() + WPN_MARKER + extra_wpn
    data_map[wpn_key] = (wpn_name, wpn_blob)
    if b"Germany_Weapon_Meteor" not in data_map[wpn_key][1]:
        raise SystemExit("Europe weapons missing after Weapon.ini patch")
    if b"Britain_Weapon_CarpetBomb" not in data_map[wpn_key][1]:
        raise SystemExit("Vulcan carpet bomb missing after Weapon.ini patch")
    print("Appended Europe weapons block in Weapon.ini")

    hc_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    hc_name, hc_blob = data_map[hc_key]
    portraits_ini = overlay[r"Data\INI\MappedImages\HandCreated\zEurope_AirbasePortrait_Images.INI"].decode("ascii")
    hc_text = hc_blob.decode("latin1")
    for m in re.finditer(r"^MappedImage (SPEC_(?:Germany|Italy|Britain)\S+)\s*$", portraits_ini, re.M):
        name = m.group(1)
        hc_text = re.sub(
            rf"^MappedImage {re.escape(name)}\s*\n.*?^End\s*$\n?",
            "",
            hc_text,
            count=1,
            flags=re.M | re.S,
        )
    if not hc_text.endswith("\n"):
        hc_text += "\n"
    hc_text += "\n" + portraits_ini.strip() + "\n"
    data_map[hc_key] = (hc_name, ch.lf(hc_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(CSF_LABELS))
    validate_no_donor_names(csf_new)
    data_map[csf_key] = (csf_name, csf_new)

    skip_inject = {"data\\ini\\commandbutton_europeairforce.ini"}
    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key in skip_inject:
            continue
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    missing_art = []
    for rel in ART_FILES:
        try:
            src = find_src(rel)
        except FileNotFoundError:
            missing_art.append(rel)
            continue
        dest = rel.replace("/", "\\")
        parts = dest.split("\\")
        if parts[1].lower() == "w3d":
            dest = "Art\\W3D\\" + parts[2]
        elif parts[1].lower() == "textures":
            dest = "Art\\Textures\\" + parts[2]
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    if missing_art:
        raise SystemExit("missing donor ART\n" + "\n".join(missing_art))
    print(f"ART injected {len(ART_FILES)} donor files")

    packed_tex = {k.split("\\")[-1].lower(): art_map[k][1] for k in art_map if "\\textures\\" in k}
    for dest_name, src_rel in PORTRAIT_SRC.items():
        try:
            src = find_src(src_rel)
            tga = make_portrait_any(src)
        except FileNotFoundError:
            leaf = Path(src_rel).name.lower()
            if leaf not in packed_tex:
                raise SystemExit(f"missing portrait source {src_rel}")
            tmp = Path("/tmp") / leaf
            tmp.write_bytes(packed_tex[leaf])
            tga = make_portrait_any(tmp)
        dest = f"Art\\Textures\\{dest_name}"
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, tga)
        print("portrait", dest_name, len(tga))

    validate_art_models(overlay, art_map)

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)

    zpath = out / "EUROPE_AIRFORCE_EXPANSION.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.writestr(
            "INSTALL.txt",
            "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
            "Keep EnglishZH.big and AudioZH.big unchanged.\n"
            "Germany / Italy / United Kingdom air forces. Does not change Russia, China, or France.\n",
        )

    verify = out / "zip_verify"
    if verify.exists():
        import shutil

        shutil.rmtree(verify)
    verify.mkdir()
    with zipfile.ZipFile(zpath, "r") as zf:
        zf.extractall(verify)
        names = set(zf.namelist())
    if "_SPEC_DATA_ONE.big" not in names or "_SPEC_ART_ONE.big" not in names:
        raise SystemExit(f"ZIP missing BIG files: {sorted(names)}")
    vdata = (verify / "_SPEC_DATA_ONE.big").read_bytes()
    vart = (verify / "_SPEC_ART_ONE.big").read_bytes()
    if hashlib.sha256(vdata).digest() != hashlib.sha256(data_big).digest():
        raise SystemExit("ZIP DATA hash mismatch after extract")
    if hashlib.sha256(vart).digest() != hashlib.sha256(art_big).digest():
        raise SystemExit("ZIP ART hash mismatch after extract")
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
        "CSF CHECK PASS\n"
        "ART CHECK PASS model W3D refs\n"
        "PROTECT CHECK PASS France/China/Russia\n"
        "ZIP extract verify PASS\n"
        "PACKAGING=DATA+ART _SPEC_DATA_ONE.big _SPEC_ART_ONE.big\n"
        "GERMANY fighters 10 / heavy 4 / heli 4\n"
        "ITALY fighters 10 / heavy 4 / heli 5\n"
        "UK fighters 10 / heavy 5 (incl Vulcan) / heli 5\n"
    )
    print(report.read_text())
    print("wrote", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
