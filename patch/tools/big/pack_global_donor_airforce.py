#!/usr/bin/env python3
"""Pack global donor air-force expansion from the UK E-7-fixed BIGs.

ART from DONOR_ART only. Specter gameplay stays native.
Fills unused visible CommandSet slots. Does not rewrite mature USA/RU/CN/UK/FR/DE/IT menus
except adding empty-slot units and safe visual-only mesh swaps.
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
import generate_global_donor_airforce as gen
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
DONOR = Path("/tmp/donor_global")
BASE_DATA = Path("/tmp/uk_e7_boot_crash_fix/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/uk_e7_boot_crash_fix/_SPEC_ART_ONE.big")

MARKER_W = "; ===== SPECTER GLOBAL DONOR AIRFORCE WEAPONS BEGIN ====="
MARKER_WE = "; ===== SPECTER GLOBAL DONOR AIRFORCE WEAPONS END ====="

NEW_OBJECTS = [s["obj"] for s in gen.AIRCRAFT]
NEW_BTNS = [f"Command_Construct{o}" for o in NEW_OBJECTS]
NEW_WEAPONS = re.findall(r"^Weapon (\S+)", gen.WEAPONS, re.M)

PROTECT_SETS = [
    "AmericaAirfieldCommandSet",
    "America_LargeAirBaseCommandSet",
    "America_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "ItalyAirfieldCommandSet",
    "Italy_LargeAirBaseCommandSet",
    "Italy_HeavyAirBaseCommandSet",
    "BritainAirfieldCommandSet",
    "Britain_LargeAirBaseCommandSet",
    "GermanyAirfieldCommandSet",
    "Germany_LargeAirBaseCommandSet",
    "Germany_HeavyAirBaseCommandSet",
    "TurkeyAirfieldCommandSet",
    "Turkey_LargeAirBaseCommandSet",
    "IranAirfieldCommandSet",
    "IranExpandedAirfieldCommandSet",
    "France_HeavyAirBaseCommandSet",
]

SLOT_ADDS = {
    "Iran_HeavyAirBaseCommandSet": {1: "Command_ConstructIranJetF4E"},
    "Turkey_HeavyAirBaseCommandSet": {
        3: "Command_ConstructTurkeyJetKAAN",
        4: "Command_ConstructTurkeyJetF16C",
        5: "Command_ConstructTurkeyJetF16Ozgur",
    },
    "Japan_AirfieldCommandSet": {
        9: "Command_ConstructJapanJetF2A",
        10: "Command_ConstructJapanJetF15JKai",
        11: "Command_ConstructJapanJetX2Shinshin",
    },
    "Japan_HeavyAirBaseCommandSet": {
        4: "Command_ConstructJapanJetF2B",
        5: "Command_ConstructJapanJetF2Kai",
        6: "Command_ConstructJapanJetF4EJKai",
    },
    "China_HeavyAirBaseCommandSet": {
        9: "Command_ConstructChinaJetJ10B",
        10: "Command_ConstructChinaJetQ5",
        11: "Command_ConstructChinaJetJ20C",
    },
    "FranceAirfieldCommandSet": {10: "Command_ConstructFranceJetMirage20005F"},
    "France_LargeAirBaseCommandSet": {10: "Command_ConstructFranceJetMirage20005F"},
}

ART_NAMES = {
    "AVLightn.W3D", "AVLightn_D.W3D",
    "LSFF16C.W3D", "LSFF16Cd.W3D", "LSFF16Ck.W3D",
    "LSFKF16.W3D", "LSFKF16d.W3D",
    "LSFF22.W3D", "LSFF22d.W3D", "LSFF22k.W3D",
    "JPF2.W3D", "JPF2D.W3D", "JPF2K.W3D",
    "LSF02TJ.W3D", "LSF02TJd.W3D", "LSF02TJk.W3D",
    "AGMZJPF2G.W3D",
    "LSFJPF15J.W3D", "LSFJPF15Jd.W3D", "LSFJPF15Jk.W3D",
    "LSFSX2.W3D", "LSFSX2d.W3D", "LSFSX2k.W3D",
    "QIANG5.W3D", "QIANG5d.W3D", "QIANG5k.W3D",
    "LSFJ20.W3D",
    "FraMirage2000.W3D",
    "AVLightn.dds", "AVLightn_D.dds",
    "LSFF16C.tga", "LSFF16Cd.tga", "LSFF16Ck.tga",
    "LSFUSAF16.dds", "LSFUSAF16d.dds", "LSFUSAF16k.dds",
    "LSFKF16.dds", "LSFKF16d.dds",
    "LSFF22.dds", "LSFF22d.dds", "LSFF22k.dds",
    "LSFJPF2.dds", "LSFJPF2d.dds", "LSFJPF2k.dds",
    "chZBD92.dds", "chZBD92d.dds", "chZBD92k.dds",
    "AGMZJPF2G.tga", "J11B.tga", "J11A.tga", "AMAIM120_M.tga", "JapF2FIM.dds",
    "LSFJPF15J.dds", "LSFJPF15Jd.dds", "LSFJPF15Jk.dds",
    "SHAXIN2.dds", "SHAXIN2d.dds", "SHAXIN2k.dds", "LSFSX2M.tga",
    "chq5m.dds", "QIANG5D.dds", "QIANG5k.dds",
    "LSFJ20.dds",
    "CHJ10A.dds", "Mirage2000m.dds", "chinagrmis.tga",
}

PORTRAIT_SRC = {
    "SPEC_IranF4E.tga": "LSFJPF4.dds",
    "SPEC_TurkeyKAAN.tga": "LSFF22.dds",
    "SPEC_TurkeyF16C.tga": "LSFF16C.tga",
    "SPEC_TurkeyF16Ozgur.tga": "LSFKF16.dds",
    "SPEC_JapanF2A.tga": "LSFJPF2.dds",
    "SPEC_JapanF15JKai.tga": "LSFJPF15J.dds",
    "SPEC_JapanX2Shinshin.tga": "SHAXIN2.dds",
    "SPEC_JapanF2B.tga": "AGMZJPF2G.tga",
    "SPEC_JapanF2Kai.tga": "chZBD92.dds",
    "SPEC_JapanF4EJKai.tga": "LSFJPF4.dds",
    "SPEC_ChinaQ5.tga": "chq5m.dds",
    "SPEC_ChinaJ20C.tga": "LSFJ20.dds",
    "SPEC_FranceMirage20005F.tga": "Mirage2000m.dds",
    "SPEC_BritainLightningF6.tga": "AVLightn.dds",
}

PROJECTILES = {
    "MeteorMissile_Object", "AIM-9X_Object", "R77_Object", "AIM-54_MissileObject",
    "GBU24_GuidedBombObject", "Fab-250", "Kh59MK2_Object", "AGM65C_MissileObject",
    "KH31P_MissileObject", "Paveway_IV_Object", "GenericUnguidedRockets",
    "30mm_API-T_Projectile",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def find_donor(name: str) -> Path | None:
    hits = [p for p in DONOR.rglob("*") if p.is_file() and p.name.lower() == name.lower()]
    return hits[0] if hits else None


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
        if slot in slots and slots[slot] != btn:
            raise SystemExit(f"{name} slot {slot} occupied by {slots[slot]}")
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


def apply_visual_overlays() -> None:
    lightning = PATCH / "INI/Object/Specter/British Armed Forces/Airforce/BritainJetLightningF6.ini"
    t = lightning.read_text(encoding="ascii")
    t = t.replace("Donor ART LSFMirage3.W3D", "Donor ART AVLightn.W3D")
    t = t.replace("Model               = LSFMirage3d", "Model               = AVLightn_D")
    t = t.replace("Model               = LSFMirage3k", "Model               = AVLightn")
    t = t.replace("Model               = LSFMirage3", "Model               = AVLightn")
    lightning.write_bytes(t.replace("\r\n", "\n").encode("ascii"))

    italy = PATCH / "INI/Object/Specter/Italian Armed Forces/Airforce/ItalyJetF35B.ini"
    t = italy.read_text(encoding="ascii")
    t = t.replace("Donor ART US_F35A.W3D", "Donor ART ENF35A.W3D")
    t = t.replace("Model               = US_F35A", "Model               = ENF35A")
    italy.write_bytes(t.replace("\r\n", "\n").encode("ascii"))

    ger = PATCH / "INI/Object/Specter/German Armed Forces/Airforce/GermanyJetF35A.ini"
    t = ger.read_text(encoding="ascii")
    t = t.replace("Donor ART US_F35A.W3D", "Donor ART LSFUSAF35A.W3D")
    t = t.replace(
        "    ConditionState        = REALLYDAMAGED\n      Model               = US_F35A",
        "    ConditionState        = REALLYDAMAGED\n      Model               = LSFUSAF35Ad",
    )
    t = t.replace(
        "    ConditionState        = REALLYDAMAGED JETEXHAUST\n      Model               = US_F35A",
        "    ConditionState        = REALLYDAMAGED JETEXHAUST\n      Model               = LSFUSAF35Ad",
    )
    t = t.replace(
        "    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER\n      Model               = US_F35A",
        "    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER\n      Model               = LSFUSAF35Ad",
    )
    t = t.replace(
        "    ConditionState        = RUBBLE\n      Model               = US_F35A",
        "    ConditionState        = RUBBLE\n      Model               = LSFUSAF35Ak",
    )
    t = t.replace(
        "    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER\n      Model               = US_F35A",
        "    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER\n      Model               = LSFUSAF35Ak",
    )
    t = t.replace("Model               = US_F35A", "Model               = LSFUSAF35A")
    ger.write_bytes(t.replace("\r\n", "\n").encode("ascii"))


def collect_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    for spec in gen.AIRCRAFT:
        p = PATCH / spec["rel"]
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    extra = [
        "INI/Object/Specter/British Armed Forces/Airforce/BritainJetLightningF6.ini",
        "INI/Object/Specter/Italian Armed Forces/Airforce/ItalyJetF35B.ini",
        "INI/Object/Specter/German Armed Forces/Airforce/GermanyJetF35A.ini",
        "INI/Weapon_GlobalDonorAirforce.ini",
        "INI/CommandButton_GlobalDonorAirforce.ini",
        "INI/MappedImages/HandCreated/zGlobalDonor_AirbasePortrait_Images.INI",
    ]
    for rel in extra:
        p = PATCH / rel
        dest = "Data\\" + rel.replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    return overlay


def write_reports(out: Path, data_hash: str, art_hash: str) -> None:
    manifest = """# DONOR_AIRCRAFT_MASTER_MANIFEST

Requested alias | Actual W3D | Textures | Source archive | Visual family | Assigned Specter aircraft | Assigned country | Scale | Role
--- | --- | --- | --- | --- | --- | --- | --- | ---
01 F18G | EA18G.W3D / LSFEA18G.W3D | LSFEA18G.dds | DONOR_ART | Growler / Super Hornet EW | AmericaJetEA18G (existing US_EA18G) | USA | 0.90 | EW / SEAD existing
02 Typhon | LSFEUEF2000.W3D | packed Typhoon textures | DONOR_ART + packed ART | Eurofighter | GermanyJetTyphoonT4 / ItalyJetTyphoon / BritainJetTyphoonFGR4 (existing) | DE/IT/UK | 0.95 | air superiority existing
03 Tornado | LSFTornado.W3D | packed | DONOR_ART + packed ART | Tornado IDS | Germany/Italy/UK Tornado objects (existing) | DE/IT/UK | ~1.0 | strike existing
04 Rafale | LSFRafale.W3D | packed | DONOR_ART + packed ART | Rafale C | FranceJetRafaleC (existing) | France | 0.95 | multirole existing
05 Lighting | AVLightn.W3D | AVLightn.dds | DONOR_ART | English Electric Lightning | BritainJetLightningF6 (visual upgrade) | UK | 1.02 | interceptor
06 F16Falcon | LSFF16C.W3D | LSFF16C.tga | DONOR_ART | F-16C | TurkeyJetF16C | Turkey | 0.90 | light multirole
07 Eagle | LSFUSAF15C.W3D / US_F15C.W3D | packed | DONOR_ART + packed ART | F-15C | AmericaJetF-15E_AA was F-15C mesh; F-15C family existing | USA | - | air superiority existing
08 F35B | ENF35A.W3D | Ef35.dds / f35.dds | DONOR_ART + packed ART | F-35 STOVL | BritainJetF35B (existing) + ItalyJetF35B (visual upgrade) | UK/Italy | 0.92-0.95 | stealth multirole
09 F18Prowler Fighter | NOT FOUND dedicated Prowler mesh | - | DONOR_ART | - | Super Hornet AmericaJetFA18E/F exist, not on menu | USA | - | no safe slot
10 F22Raptor | US_F22A.W3D / LSFF22.W3D | packed / LSFF22.dds | DONOR_ART + packed ART | F-22 family | AmericaJetF-22A_AA existing; LSFF22 used by Turkish KAAN | USA/Turkey | 0.90-1.00 | stealth A2A
11 Falcon | LSFF16C.W3D | LSFF16C.tga | DONOR_ART | F-16 | TurkeyJetF16C | Turkey | 0.90 | light multirole
12 F18PROWLER | NOT FOUND dedicated; EA-18G family used | LSFEA18G.dds | DONOR_ART | Growler | AmericaJetEA18G existing | USA | 0.90 | EW existing
13 F18HORNET | AmF18A.W3D / F18SEA.W3D | AmF18MA*.dds | DONOR_ART | classic Hornet | none (USA fighter/heavy menus full) | USA | - | found, no safe slot
14 Lightning | AVLightn_A1.W3D | AVLightn.dds | DONOR_ART | Lightning helper (4035 bytes) | DUPLICATE helper of AVLightn, no extra unit | UK | - | duplicate helper
15 Auter F22 | LSFF22.W3D | LSFF22.dds | DONOR_ART | F-22-like stealth | TurkeyJetKAAN (UI never says F-22) | Turkey | 1.00 | next-gen A2A
16 F15 Strike Eagle | US_F15E.W3D / LSFUSAF15E.W3D | packed | packed ART / DONOR_ART | F-15E | AmericaJetF-15E_AA visual upgrade US_F15C -> US_F15E | USA | - | heavy strike
17 F2 | JPF2.W3D | LSFJPF2.dds | DONOR_ART | Mitsubishi F-2 | JapanJetF2A | Japan | 0.98 | naval/antiship multirole
18 F16 Fighter | LSFKF16.W3D | LSFKF16.dds | DONOR_ART | F-16 (distinct from LSFF16C) | TurkeyJetF16Ozgur | Turkey | 0.92 | modernized multirole
19 Tomcat | Iran_F14A.W3D / LSFIRF14A.W3D | packed / LSFF14A.dds | packed ART / DONOR_ART | F-14 | IranJetF14A existing | Iran | - | interceptor existing
20 Strike Eagle | US_F15EX.W3D | packed | packed ART | F-15EX | packed mesh exists; object/menu already mature, not duplicated | USA | - | existing EX mesh
21 J11 Flanker | LSFJ11B.W3D | packed | DONOR_ART + packed ART | J-11B | ChinaJetJ11B existing | China | - | A2A/multirole existing
22 Auter J31 | LSFJ31.W3D | packed | DONOR_ART + packed ART | FC-31 | ChinaJetJ31 existing | China | 1.15 | stealth existing
23 J10B Raptor | ChJ10B.W3D | packed | DONOR_ART + packed ART | J-10B | ChinaJetJ10B existing, wired to Heavy slot 9 | China | 1.18 | multirole existing
24 Qiang 5 | QIANG5.W3D | chq5m.dds | DONOR_ART | Q-5 | ChinaJetQ5 | China | 0.88 | legacy CAS
25 S6-30 Super Flanker | RUSU30.W3D / RUS_SU30SM2.W3D | RUSU30MKK.dds | DONOR_ART + packed ART | Su-30 | RussiaJetSu30SM2 existing (not replaced) | Russia | 0.90 | multirole existing
26 F16ing Leopard | CHJH7A.W3D / CHI_JH7A2.W3D | packed | DONOR_ART + packed ART | JH-7A | ChinaJetJH7A2 existing (not replaced) | China | - | strike existing
27 J15A | J15JZ.W3D | packed | DONOR_ART + packed ART | J-15 | ChinaJetJ15 existing | China | - | naval existing
28 J20C | LSFJ20.W3D | LSFJ20.dds | DONOR_ART | J-20 (distinct hash from CHI_J20B) | ChinaJetJ20C | China | 1.10 | stealth A2A
29 J7 Chengdu | LSFJ7.W3D | packed | DONOR_ART + packed ART | J-7 | ChinaJetJ7 existing | China | 1.22 | legacy interceptor existing
30 Rafale Fighter | LSFRafaleAS.W3D | packed | DONOR_ART + packed ART | Rafale M | FranceJetRafaleM existing | France | - | naval existing
31 Mirage 2000D | LSFMirage2KD.W3D | packed | DONOR_ART + packed ART | Mirage 2000D | FranceJetMirage2000D existing | France | 0.90 | strike existing
32 Storm Fighter | NOT FOUND dedicated Tempest/Storm W3D | - | DONOR_ART | - | BritainJetTempest already uses SPEC_OLD_F35 | UK | 1.00 | existing Tempest
33 Auter F2 | LSF02TJ.W3D | chZBD92.dds | DONOR_ART | F-2 experimental | JapanJetF2Kai | Japan | 1.00 | modernized multirole
34 Shinshin | LSFSX2.W3D | SHAXIN2.dds / LSFSX2M.tga | DONOR_ART | X-2 | JapanJetX2Shinshin | Japan | 0.92 | experimental stealth
35 Eagle Japan | LSFJPF15J.W3D | LSFJPF15J.dds | DONOR_ART | F-15J | JapanJetF15JKai | Japan | 1.08 | air superiority
36 F4 Phantom | JPF4.W3D | LSFJPF4.dds | packed ART | Phantom | IranJetF4E + JapanJetF4EJKai (independent objects) | Iran/Japan | 1.00 | legacy multirole
37 F2 Fighter | AGMZJPF2G.W3D | AGMZJPF2G.tga | DONOR_ART | F-2B | JapanJetF2B | Japan | 0.94 | light multirole
38 Mirage 2000 Fighter | FraMirage2000.W3D | Mirage2000m.dds | DONOR_ART | Mirage 2000-5 | FranceJetMirage20005F | France | 0.90 | A2A specialist
39 Mirage 21 Fighter | LSFFRF1 / LSFMirage3 / LSFMirage5 | packed | DONOR_ART + packed ART | Mirage F1 / III / 5 | FranceJetMirageF1CT / IIIE / Mirage5 existing | France | 0.85 | legacy existing
"""
    usage = """# DONOR_USAGE_FINAL

Every requested alias status.

| Alias | Status | Notes |
| --- | --- | --- |
| 01 F18G | USED | Existing AmericaJetEA18G (US_EA18G). Donor EA18G/LSFEA18G inspected, working Growler not replaced. |
| 02 Typhon | USED | Existing DE/IT/UK Typhoon objects (LSFEUEF2000). EVTyphoon missing SU-25MU texture, not swapped onto ECR. |
| 03 Tornado | USED | Existing DE/IT/UK Tornado objects (LSFTornado). |
| 04 Rafale | USED | Existing FranceJetRafaleC (LSFRafale). |
| 05 Lighting | USED | BritainJetLightningF6 visual AVLightn (was wrongly LSFMirage3). |
| 06 F16Falcon | USED | TurkeyJetF16C = LSFF16C. |
| 07 Eagle | USED | USA F-15 family existing; F-15E_AA visual corrected to US_F15E. |
| 08 F35B | USED | UK F-35B ENF35A existing; Italy F-35B upgraded US_F35A -> ENF35A. Germany F-35A -> LSFUSAF35A. |
| 09 F18Prowler Fighter | NOT FOUND | No dedicated EA-6B/Prowler mesh. Super Hornet US_FA18E/F packed but menus full. |
| 10 F22Raptor | USED | Existing AmericaJetF-22A_AA (US_F22A). LSFF22 reserved for Turkish KAAN. |
| 11 Falcon | DUPLICATE OF 06 F16Falcon | Same F-16C family; LSFF16C assigned to Turkey F-16C. |
| 12 F18PROWLER | DUPLICATE OF 01 F18G | No dedicated second Prowler mesh. Growler remains AmericaJetEA18G. |
| 13 F18HORNET | FOUND / NO SLOT | AmF18A.W3D and F18SEA.W3D extracted. USA fighter and heavy menus are full. Not created. |
| 14 Lightning | DUPLICATE OF 05 Lighting | AVLightn_A1.W3D is a 4035-byte helper, not a second aircraft. No extra slot used. |
| 15 Auter F22 | USED | TurkeyJetKAAN = LSFF22. UI strings are KAAN only. |
| 16 F15 Strike Eagle | USED | AmericaJetF-15E_AA Model US_F15C -> US_F15E. |
| 17 F2 | USED | JapanJetF2A = JPF2. |
| 18 F16 Fighter | USED | TurkeyJetF16Ozgur = LSFKF16 (distinct from LSFF16C). |
| 19 Tomcat | USED | Existing IranJetF14A (Iran_F14A). LSFIRF14A inspected, working Tomcat not replaced. |
| 20 Strike Eagle | DUPLICATE OF 16 / existing EX | US_F15EX already packed. No extra USA slot. |
| 21 J11 Flanker | USED | Existing ChinaJetJ11B (LSFJ11B). |
| 22 Auter J31 | USED | Existing ChinaJetJ31 (LSFJ31). |
| 23 J10B Raptor | USED | Existing ChinaJetJ10B (ChJ10B) wired to China Heavy slot 9 (was off-screen slot 15 only). |
| 24 Qiang 5 | USED | ChinaJetQ5 = QIANG5. |
| 25 S6-30 Super Flanker | USED | Existing RussiaJetSu30SM2 (RUS_SU30SM2). Donor RUSU30 not swapped. |
| 26 F16ing Leopard | USED | Existing ChinaJetJH7A2 (CHI_JH7A2). Donor CHJH7A not swapped. |
| 27 J15A | USED | Existing ChinaJetJ15 (J15JZ). |
| 28 J20C | USED | ChinaJetJ20C = LSFJ20 (hash differs from CHI_J20B). |
| 29 J7 Chengdu | USED | Existing ChinaJetJ7 (LSFJ7). |
| 30 Rafale Fighter | USED | Existing FranceJetRafaleM (LSFRafaleAS). |
| 31 Mirage 2000D | USED | Existing FranceJetMirage2000D (LSFMirage2KD). |
| 32 Storm Fighter | NOT FOUND | No dedicated Tempest/Storm W3D. BritainJetTempest already uses SPEC_OLD_F35. |
| 33 Auter F2 | USED | JapanJetF2Kai = LSF02TJ. |
| 34 Shinshin | USED | JapanJetX2Shinshin = LSFSX2. |
| 35 Eagle Japan | USED | JapanJetF15JKai = LSFJPF15J. |
| 36 F4 Phantom | USED | IranJetF4E and JapanJetF4EJKai independent objects on JPF4. |
| 37 F2 Fighter | USED | JapanJetF2B = AGMZJPF2G. |
| 38 Mirage 2000 Fighter | USED | FranceJetMirage20005F = FraMirage2000. |
| 39 Mirage 21 Fighter | USED | Inspected as Mirage F1 / III / 5. Existing FranceJetMirageF1CT, FranceJetMirageIIIE, FranceJetMirage5. |

Summary: 39 aliases inspected. Unique W3Ds newly packed for new/upgraded units listed in GLOBAL_AIRCRAFT_GAMEPLAY_MATRIX.md.
"""
    matrix = f"""# GLOBAL_AIRCRAFT_GAMEPLAY_MATRIX

Country | Aircraft | Role | Visual donor | A2A weapon | A2G weapon | Special weapon | Ammo | Scale | Price | Build time | Airbase | CommandSet slot
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Iran | IranJetF4E | legacy strike | JPF4 | Sparrow-style Meteor wrap x4 | Fab-250 x6 | Sidewinder x2 | 4/2/6 | 1.00 | 1400 | 12 | Heavy | 1
Turkey | TurkeyJetKAAN | stealth air superiority | LSFF22 | Gokhan/R-77 x6 | HGK x2 | Bozdogan/AIM-9X x2 | 6/2/2 | 1.00 | 2800 | 18 | Heavy | 3
Turkey | TurkeyJetF16C | light multirole | LSFF16C | AIM-120 style x4 | HGK x4 | SOM x2 | 4/4/2 | 0.90 | 1600 | 13 | Heavy | 4
Turkey | TurkeyJetF16Ozgur | modernized multirole | LSFKF16 | Goktug/R-77 x6 | SOM x4 | IR x2 | 6/2/4 | 0.92 | 1800 | 14 | Heavy | 5
Japan | JapanJetF2A | naval/antiship multirole | JPF2 | AAM-4B x4 | GBU x4 | ASM-2/KH-31 x2 | 4/2/4 | 0.98 | 2000 | 15 | Fighter | 9
Japan | JapanJetF15JKai | air superiority | LSFJPF15J | AAM-4B x8 | cannon | AAM-5 x4 | 8/4/40 | 1.08 | 2400 | 16 | Fighter | 10
Japan | JapanJetX2Shinshin | experimental stealth interceptor | LSFSX2 | AAM-4 x4 | cannon | AAM-5 x2 | 4/2/24 | 0.92 | 2200 | 16 | Fighter | 11
Japan | JapanJetF2B | light multirole | AGMZJPF2G | AAM-4B x2 | GBU x2 | AAM-5 x2 | 2/2/2 | 0.94 | 1700 | 13 | Heavy | 4
Japan | JapanJetF2Kai | modernized multirole | LSF02TJ | AAM-4B x6 | Paveway x4 | AAM-5 x2 | 6/2/4 | 1.00 | 2100 | 15 | Heavy | 5
Japan | JapanJetF4EJKai | legacy multirole | JPF4 | Sparrow-style x2 | Fab-250 x4 | Sidewinder x2 | 2/2/4 | 1.00 | 1300 | 12 | Heavy | 6
China | ChinaJetJ10B | multirole (existing) | ChJ10B | existing LT3/KD88/MK82 | existing | existing | existing | 1.18 | 1250 | 14 | Heavy | 9
China | ChinaJetQ5 | legacy CAS | QIANG5 | cannon | Fab-250 x8 | rockets x8 | 8/8/24 | 0.88 | 800 | 8 | Heavy | 10
China | ChinaJetJ20C | stealth A2A | LSFJ20 | PL-15/R-77 x6 | LS-6 x2 | PL-10 x2 | 6/2/2 | 1.10 | 3000 | 18 | Heavy | 11
France | FranceJetMirage20005F | air superiority | FraMirage2000 | Meteor x6 | cannon | MICA x4 | 6/4/28 | 0.90 | 1900 | 14 | Fighter | 10
UK | BritainJetLightningF6 | interceptor (visual) | AVLightn | existing Meteor/ASRAAM/cannon | none | existing | existing | 1.02 | 1300 | 11 | Fighter | 9 (unchanged)
Italy | ItalyJetF35B | stealth (visual) | ENF35A | existing | existing | existing | existing | 0.92 | existing | existing | Fighter | 3 (unchanged)
Germany | GermanyJetF35A | stealth (visual) | LSFUSAF35A | existing | existing | existing | existing | 0.92 | existing | existing | Fighter | 5 (unchanged)
USA | AmericaJetF-15E_AA | strike (visual) | US_F15E | existing | existing | existing | existing | existing | existing | existing | Fighter | existing

DATA sha256: {data_hash}
ART sha256: {art_hash}
"""
    (out / "DONOR_AIRCRAFT_MASTER_MANIFEST.md").write_text(manifest)
    (out / "DONOR_USAGE_FINAL.md").write_text(usage)
    (out / "GLOBAL_AIRCRAFT_GAMEPLAY_MATRIX.md").write_text(matrix)
    (ROOT / "DONOR_AIRCRAFT_MASTER_MANIFEST.md").write_text(manifest)
    (ROOT / "DONOR_USAGE_FINAL.md").write_text(usage)
    (ROOT / "GLOBAL_AIRCRAFT_GAMEPLAY_MATRIX.md").write_text(matrix)


def write_install(out: Path) -> None:
    text = """SPECTER GLOBAL DONOR AIR FORCE EXPANSION

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This pack is ART-only from DONOR_ART plus native Specter gameplay wrappers.
It does not import donor Object/Weapon/CommandSet INI.

Adds/upgrades:
- Iran F-4E Phantom II (Heavy Airbase)
- Turkey KAAN, F-16C Block 50+, F-16 OZGUR (Heavy Airbase)
- Japan F-2A, F-15J Kai, X-2 Shinshin (Fighter Airbase unused slots)
- Japan F-2B, F-2 Kai, F-4EJ Kai (Heavy Airbase unused slots)
- China Q-5, J-20C, and visible J-10B (Heavy Airbase unused slots)
- France Mirage 2000-5F (Fighter Airbase unused slot)
- UK Lightning F6 true Lightning mesh
- Italy F-35B ENF35A mesh
- Germany F-35A LSFUSAF35A mesh
- USA F-15E Strike Eagle mesh on the existing F-15E_AA object

Does not rewrite USA/Russia/China/UK/France/Germany/Italy working fighter menus
except France slot 10 (was empty) and the visual-only swaps above.
"""
    (out / "INSTALL.txt").write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/global_donor_airforce"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    gen.main()
    apply_visual_overlays()
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

    protect_hash = {n: hashlib.sha256(ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), n).encode("latin1")).hexdigest() for n in PROTECT_SETS}

    # USA F-15E visual
    f15_key = None
    for k in data_map:
        if k.endswith("\\f15c.ini") and "united states" in k:
            f15_key = k
            break
    if not f15_key:
        raise SystemExit("packed F15C.ini missing")
    f15_name, f15_blob = data_map[f15_key]
    f15_text = f15_blob.decode("latin1")
    if "Object AmericaJetF-15E_AA" not in f15_text:
        raise SystemExit("AmericaJetF-15E_AA missing")
    f15_new = f15_text.replace("Model               = US_F15C", "Model               = US_F15E")
    if f15_new == f15_text:
        raise SystemExit("F-15E visual patch did not apply")
    data_map[f15_key] = (f15_name, ch.lf(f15_new.encode("latin1")))
    print("patched AmericaJetF-15E_AA US_F15C -> US_F15E")

    cs_key = "data\\ini\\commandset.ini"
    cs_name, cs_blob = data_map[cs_key]
    cs_text = cs_blob.decode("latin1")
    btn_overlay = overlay[r"Data\INI\CommandButton_GlobalDonorAirforce.ini"].decode("ascii")
    cs_text = inline_buttons(cs_text, btn_overlay)
    for set_name, adds in SLOT_ADDS.items():
        old = ch.grab_block(cs_text, set_name)
        new = rebuild_commandset(old, adds)
        cs_text = replace_cs(cs_text, set_name, new)
        print("updated", set_name, sorted(adds))
    cb_key = "data\\ini\\commandbutton.ini"
    cb_text = data_map[cb_key][1].decode("latin1")
    ch.validate_commandset_button_refs(cs_text, cb_text)
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    wpn_text = wpn_blob.decode("latin1")
    for proj in PROJECTILES:
        if f" {proj}" not in wpn_text and proj not in data_map.get("data\\ini\\weapon.ini", ("", b""))[1].decode("latin1"):
            pass
    # projectile objects live in object INI, not Weapon.ini. Verify later against all DATA.
    wpn_overlay = overlay[r"Data\INI\Weapon_GlobalDonorAirforce.ini"].decode("ascii")
    for wname in NEW_WEAPONS:
        if f"Weapon {wname}" in wpn_text:
            raise SystemExit(f"Weapon {wname} already in Weapon.ini")
    wpn_text = inline_weapons(wpn_text, wpn_overlay)
    for wname in NEW_WEAPONS:
        if wpn_text.count(f"Weapon {wname}") != 1:
            raise SystemExit(f"Weapon {wname} count {wpn_text.count('Weapon '+wname)}")
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_text.encode("latin1")))
    print("inlined", len(NEW_WEAPONS), "weapons")

    hc_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    if hc_key not in data_map:
        # find
        for k in data_map:
            if k.endswith("handcreatedmappedimages.ini"):
                hc_key = k
                break
    hc_name, hc_blob = data_map[hc_key]
    hc_text = hc_blob.decode("latin1")
    por_ini = overlay[r"Data\INI\MappedImages\HandCreated\zGlobalDonor_AirbasePortrait_Images.INI"].decode("ascii")
    if not hc_text.endswith("\n"):
        hc_text += "\n"
    hc_text += "\n" + por_ini.strip() + "\n"
    data_map[hc_key] = (hc_name, ch.lf(hc_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(gen.CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    skip = {
        "data\\ini\\commandbutton_globaldonorairforce.ini",
        "data\\ini\\weapon_globaldonorairforce.ini",
    }
    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key in skip:
            continue
        if key.endswith("zglobaldonor_airbaseportrait_images.ini"):
            if key not in data_map:
                data_keys.append(key)
            data_map[key] = (dest, content)
            continue
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    # ART
    missing_art = []
    for name in sorted(ART_NAMES):
        src = find_donor(name)
        if src is None:
            # packed already?
            packed = None
            for k, (pn, blob) in art_map.items():
                if pn.split("\\")[-1].lower() == name.lower():
                    packed = True
                    break
            if packed:
                continue
            missing_art.append(name)
            continue
        dest = ("Art\\W3D\\" if name.lower().endswith(".w3d") else "Art\\Textures\\") + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    if missing_art:
        raise SystemExit("missing ART\n" + "\n".join(missing_art))
    print("ART injected from donor")

    packed_tex = {k.split("\\")[-1].lower(): art_map[k][1] for k in art_map if "\\textures\\" in k}
    for dest_name, src_name in PORTRAIT_SRC.items():
        src = find_donor(src_name)
        if src is None:
            leaf = src_name.lower()
            if leaf not in packed_tex:
                raise SystemExit(f"missing portrait source {src_name}")
            tmp = Path("/tmp") / leaf
            tmp.write_bytes(packed_tex[leaf])
            src = tmp
        tga = eu.make_portrait_any(src)
        dest = f"Art\\Textures\\{dest_name}"
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, tga)
        print("portrait", dest_name, len(tga))

    # uniqueness of new objects
    obj_hits: dict[str, list[str]] = {o: [] for o in NEW_OBJECTS}
    for key in list(data_map):
        name, blob = data_map[key]
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for obj in NEW_OBJECTS:
            if re.search(rf"^Object {re.escape(obj)}\b", text, re.M):
                obj_hits[obj].append(name)
        if key in {ch.norm_key(r"Data\\" + s["rel"].replace("/", "\\")) for s in gen.AIRCRAFT}:
            errs = e7.balanced_end(text, name)
            if errs:
                raise SystemExit("End balance FAIL\n" + "\n".join(errs))
    for obj, hits in obj_hits.items():
        if hits != [next("Data\\" + s["rel"].replace("/", "\\") for s in gen.AIRCRAFT if s["obj"] == obj)]:
            # allow only the overlay path
            expect = [s for s in gen.AIRCRAFT if s["obj"] == obj][0]
            expect_name = "Data\\" + expect["rel"].replace("/", "\\")
            if hits != [expect_name] and [h.lower() for h in hits] != [expect_name.lower()]:
                raise SystemExit(f"Object {obj} hits={hits}")
    print("new Object unique PASS")

    # models exist in ART
    art_w3d = {k.split("\\")[-1].lower().replace(".w3d", "") for k in art_map if k.endswith(".w3d")}
    for spec in gen.AIRCRAFT:
        for m in (spec["model"], spec["model_d"], spec["model_k"]):
            if m.lower() not in art_w3d:
                raise SystemExit(f"missing W3D for {spec['obj']} model {m}")
    if "avlightn" not in art_w3d:
        raise SystemExit("AVLightn not packed")
    if "enf35a" not in art_w3d:
        raise SystemExit("ENF35A not packed")
    if "lsfusaf35a" not in art_w3d:
        raise SystemExit("LSFUSAF35A not packed")
    if "us_f15e" not in art_w3d:
        raise SystemExit("US_F15E not packed")
    print("ART/W3D PASS")

    # projectiles exist as Object
    found_proj = set()
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for p in PROJECTILES:
            if re.search(rf"^Object {re.escape(p)}\b", text, re.M):
                found_proj.add(p)
    missing_proj = PROJECTILES - found_proj
    if missing_proj:
        raise SystemExit("missing projectile objects: " + ", ".join(sorted(missing_proj)))
    print("Projectile references PASS")

    cs_final = data_map[cs_key][1].decode("latin1")
    for n in PROTECT_SETS:
        h = hashlib.sha256(ch.grab_block(cs_final, n).encode("latin1")).hexdigest()
        if h != protect_hash[n]:
            raise SystemExit(f"protected CommandSet changed: {n}")
    print("protected CommandSets unchanged PASS")

    # slot verification
    for set_name, adds in SLOT_ADDS.items():
        block = ch.grab_block(cs_final, set_name)
        for slot, btn in adds.items():
            if not re.search(rf"^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", block, re.M):
                raise SystemExit(f"{set_name} missing {slot}={btn}")
        if "Command_SetRallyPoint" not in block and set_name != "IranAirfieldCommandSet":
            # Iran fighter historically has no rally; heavy does
            if "13" in {int(x) for x in re.findall(r"^\s*(\d+)\s*=", block, re.M)}:
                if "Command_Sell" not in block:
                    raise SystemExit(f"{set_name} lost Sell")
        if "Command_Sell" not in block:
            raise SystemExit(f"{set_name} lost Sell")
        slots = [int(x) for x in re.findall(r"^\s*(\d+)\s*=", block, re.M)]
        if len(slots) != len(set(slots)):
            raise SystemExit(f"{set_name} duplicate slots {slots}")
        if any(s > 14 and s not in slots for s in []):
            pass
        # visible bar 1-12: our adds must be <= 12
        for slot in adds:
            if slot > 12:
                raise SystemExit(f"{set_name} used off-screen slot {slot}")
    print("slot fill PASS")

    # regression existing country buttons
    regress = {
        "America_LargeAirBaseCommandSet": "Command_ConstructAmericaJetRaptor",
        "Russia_LargeAirBaseCommandSet": "Command_ConstructRussiaJetSu35S",
        "PLAAirfieldCommandSet": "Command_ConstructChinaJetJ11B",
        "France_LargeAirBaseCommandSet": "Command_ConstructFranceJetRafaleC",
        "Germany_LargeAirBaseCommandSet": "Command_ConstructGermanyJetTyphoonT4",
        "Italy_LargeAirBaseCommandSet": "Command_ConstructItalyJetTyphoon",
        "Britain_LargeAirBaseCommandSet": "Command_ConstructBritainJetF35B",
        "Britain_HeavyAirBaseCommandSet": "Command_ConstructBritainJetTempest",
        "Japan_AirfieldCommandSet": "Command_ConstructJapanAir_WZ10ME",
        "Turkey_LargeAirBaseCommandSet": "Command_ConstructTurkeyJetRafaleF3",
        "IranExpandedAirfieldCommandSet": "Command_ConstructIranJetF14A",
    }
    for set_name, btn in regress.items():
        if btn not in ch.grab_block(cs_final, set_name):
            raise SystemExit(f"regression {set_name} lost {btn}")
    print("country regression PASS")

    # CSF no F-22 on KAAN
    _v, _u, _l, labels = ch.parse_csf(csf_new)
    for _m, name, strings in labels:
        if "KAAN" in name or (strings and "KAAN" in strings[0][1]):
            val = strings[0][1] if strings else ""
            if re.search(r"F-?22", val, re.I) or re.search(r"F-?22", name, re.I):
                raise SystemExit(f"KAAN CSF mentions F-22: {name}={val}")
    print("KAAN CSF identity PASS")

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

    # re-extract validate
    v_entries, v_raw = ch.read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[ch.norm_key(name)] = (name, v_raw[off : off + size])
    va_entries, va_raw = ch.read_big(out_art)
    va_w3d = set()
    for name, off, size in va_entries:
        if name.lower().endswith(".w3d"):
            va_w3d.add(name.split("\\")[-1].lower())
    vcs = v_map["data\\ini\\commandset.ini"][1].decode("latin1")
    vwpn = v_map["data\\ini\\weapon.ini"][1].decode("latin1")
    for obj in NEW_OBJECTS:
        hits = []
        for name, blob in v_map.values():
            if name.lower().endswith(".ini") and re.search(rf"^Object {re.escape(obj)}\b", blob.decode("latin1"), re.M):
                hits.append(name)
        if len(hits) != 1:
            raise SystemExit(f"re-extract Object {obj} hits={hits}")
        if f"Command_Construct{obj}" not in vcs:
            raise SystemExit(f"re-extract missing button {obj}")
    for wname in NEW_WEAPONS:
        if f"Weapon {wname}" not in vwpn:
            raise SystemExit(f"re-extract missing weapon {wname}")
    for need in ("avlightn.w3d", "lsff16c.w3d", "lsff22.w3d", "jpf2.w3d", "qiang5.w3d", "lsfj20.w3d", "framirage2000.w3d", "lsfsx2.w3d"):
        if need not in va_w3d:
            raise SystemExit(f"re-extract ART missing {need}")
    if "Object AmericaJetF-15E_AA" not in v_map[f15_key][1].decode("latin1"):
        raise SystemExit("re-extract lost F-15E_AA")
    if "US_F15E" not in v_map[f15_key][1].decode("latin1"):
        raise SystemExit("re-extract F-15E visual lost")
    if "AVLightn" not in v_map[ch.norm_key(r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetLightningF6.ini")][1].decode("latin1"):
        raise SystemExit("re-extract Lightning visual lost")
    print("re-extract FINAL content PASS")

    write_reports(out, dh, ah)
    write_install(out)
    zpath = out / "GLOBAL_DONOR_AIRFORCE_EXPANSION.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(out / "INSTALL.txt", "INSTALL.txt")
        zf.write(out / "DONOR_USAGE_FINAL.md", "DONOR_USAGE_FINAL.md")
        zf.write(out / "GLOBAL_AIRCRAFT_GAMEPLAY_MATRIX.md", "GLOBAL_AIRCRAFT_GAMEPLAY_MATRIX.md")
    print("ZIP", zpath, zpath.stat().st_size)
    (out / "PACK_REPORT.txt").write_text(
        f"DATA sha256 {dh}\nART  sha256 {ah}\nDATA bytes {out_data.stat().st_size}\nART  bytes {out_art.stat().st_size}\n"
        f"new aircraft {len(NEW_OBJECTS)}\nnew weapons {len(NEW_WEAPONS)}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
