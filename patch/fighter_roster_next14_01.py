#!/usr/bin/env python3
"""FIGHTER_ROSTER_NEXT14 — implement the approved 14-country 2/2/6 plan.

Writes last-win CommandButton/CommandSet and the analyzed WeaponSet-only
rebinds. Does NOT write a BIG. Does NOT modify Weapon.ini or completed
SA/UAE/Syria/India/Pakistan overlays.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

BIG = Path("/workspace/patch/Release/FIGHTER_ROSTER_SA_UAE_SYRIA_INDIA_PAKISTAN/_SPEC_DATA_ONE.big")
ROOT = Path("/workspace/patch")
INI = ROOT / "Data" / "INI"
BTN_OUT = INI / "CommandButton_ZZZZ_FighterRoster_Next14.ini"
CS_OUT = INI / "CommandSet_ZZZZ_FighterRoster_Next14.ini"

WS_F15C_AA = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY   6x_MRAAM_AIM120C_F15C
    Weapon            = SECONDARY AN/APG63V3_AESA_Radar_AAMode
    Weapon            = TERTIARY  2x_AIM-9X
  End
"""

WS_AGM65_AT = """  WeaponSet
    Conditions = None
    Weapon              = PRIMARY    2x_AGM65F_F16CMB50
    PreferredAgainst    = PRIMARY    VEHICLE
    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""

WS_KH29_AT = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY     2x_KH29L_AGM_F1EQ
    PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE
    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""

WS_MIG29_AA = """  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY     4x_R27_MRBVR_Mig29A
  End
"""

WS_SU24 = """  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY     2x_TVG_Kab1500Kr_Su24M2
    Weapon            = SECONDARY   SVP-24_AMTS_SU24M2
  End
"""

WS_F35_AA = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY   AmericaF35C_AA_AIM120
    Weapon            = SECONDARY AIM9X_HOBS_SRAAM_F35C
  End
"""

WS_UA_MIG29MU1_AA = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY   UkraineJetMig29MU1_WpnRadar
    Weapon            = SECONDARY UkraineJetMig29MU1_WpnIR
  End
"""

# Analyzed WeaponSet-only rebinds (transferred / mixed country Objects).
REBINDS: dict[str, str] = {
    "JapanJetF15J": WS_F15C_AA,
    "Libya_Mig-29A": WS_MIG29_AA,
    "Libya_MirageF1_Bq": WS_KH29_AT,
    "LibyaJetSu24": WS_SU24,
    "LibyaJetMig23": WS_KH29_AT,
    "SouthAfrica_MirageF1_Bq": WS_KH29_AT,
    "SouthKoreaJetF35A": WS_F35_AA,
    "SouthKoreaJetF5E": WS_AGM65_AT,
    "SouthKoreaJetF4E": WS_AGM65_AT,
    "UkraineJetSu24M": WS_SU24,
    "UkraineJetMig29": WS_MIG29_AA,
    "UkraineJetMig29MU1": WS_UA_MIG29MU1_AA,
    "TurkeyJetF16C": WS_AGM65_AT,
}

KEEP_OBJECTS = {
    "TurkeyJetF16DBlk52",
    "UkraineJetF16DBlk52",
    "BritainJetF16DBlk52",
    "FranceJetF16DBlk52",
    "GermanyJetF16DBlk52",
    "ItalyJetF16DBlk52",
    "SwedenJetF16DBlk52",
    "LibyaJetJ7",
    "Egypt_Su-25K",
    "Libya_Su-25K",
    "Egypt_Mig-29A",
    "Egypt_MirageF1_Bq",
    "SouthAfricaJetF15E",
    "SouthAfricaJetJ10C",
}

# National 12: (button, object) per analysis slot order.
AIRFIELD: dict[str, list[tuple[str, str]]] = {
    "Turkey": [
        ("Command_ConstructTurkeyJetKAAN", "TurkeyJetKAAN"),
        ("Command_ConstructTurkeyJetKAANBlk2", "TurkeyJetKAANBlk2"),
        ("Command_ConstructTurkeyJetF16C", "TurkeyJetF16C"),
        ("Command_ConstructTurkeyJetF4ETerm", "TurkeyJetF4ETerm"),
        ("Command_ConstructTurkeyJetF16DBlk52", "TurkeyJetF16DBlk52"),
        ("Command_ConstructTurkeyJetF16Blk30", "TurkeyJetF16Blk30"),
        ("Command_ConstructTurkeyJetF4E", "TurkeyJetF4E"),
        ("Command_ConstructTurkeyJetRF4E", "TurkeyJetRF4E"),
        ("Command_ConstructTurkeyJetF35A", "TurkeyJetF35A"),
        ("Command_ConstructTurkeyJetF16Ozgur", "TurkeyJetF16Ozgur"),
        ("Command_ConstructTurkeyJetHurjet", "TurkeyJetHurjet"),
        ("Command_ConstructTurkeyJetNF5", "TurkeyJetNF5"),
    ],
    "Ukraine": [
        ("Command_ConstructUkraineJetMig29", "UkraineJetMig29"),
        ("Command_ConstructUkraineJetMig29MU1", "UkraineJetMig29MU1"),
        ("Command_ConstructUkraineJetSu27", "UkraineJetSu27"),
        ("Command_ConstructUkraineJetSu25", "UkraineJetSu25"),
        ("Command_ConstructUkraineJetF16AM", "UkraineJetF16AM"),
        ("Command_ConstructUkraineJetF16DBlk52", "UkraineJetF16DBlk52"),
        ("Command_ConstructUkraineJetMirage2000", "UkraineJetMirage2000"),
        ("Command_ConstructUkraineJetSu24M", "UkraineJetSu24M"),
        ("Command_ConstructUkraineJetSu24MR", "UkraineJetSu24MR"),
        ("Command_ConstructUkraineJetSu25M1", "UkraineJetSu25M1"),
        ("Command_ConstructUkraineJetSu27UB", "UkraineJetSu27UB"),
        ("Command_ConstructUkraineJetMig21", "UkraineJetMig21"),
    ],
    "Japan": [
        ("Command_ConstructJapanJetF35B", "JapanJetF35B"),
        ("Command_ConstructJapanJetF15J", "JapanJetF15J"),
        ("Command_ConstructJapanJetF4EJKai", "JapanJetF4EJKai"),
        ("Command_ConstructJapanJetF2A", "JapanJetF2A"),
        ("Command_ConstructJapanJetF35A", "JapanJetF35A"),
        ("Command_ConstructJapanJetF15DJ", "JapanJetF15DJ"),
        ("Command_ConstructJapanJetF2B", "JapanJetF2B"),
        ("Command_ConstructJapanJetF2Kai", "JapanJetF2Kai"),
        ("Command_ConstructJapanJetX2Shinshin", "JapanJetX2Shinshin"),
        ("Command_ConstructJapanJetF16", "JapanJetF16"),
        ("Command_ConstructJapanJetF18G", "JapanJetF18G"),
        ("Command_ConstructJapanJetEA6BUSA", "JapanJetEA6BUSA"),
    ],
    "Britain": [
        ("Command_ConstructBritainJetF35B", "BritainJetF35B"),
        ("Command_ConstructBritainJetTyphoonFGR4", "BritainJetTyphoonFGR4"),
        ("Command_ConstructBritainJetHarrierGR9", "BritainJetHarrierGR9"),
        ("Command_ConstructBritainJetTornadoGR4", "BritainJetTornadoGR4"),
        ("Command_ConstructBritainJetTyphoonT3", "BritainJetTyphoonT3"),
        ("Command_ConstructBritainJetTempest", "BritainJetTempest"),
        ("Command_ConstructBritainJetTornadoF3", "BritainJetTornadoF3"),
        ("Command_ConstructBritainJetSeaHarrierFA2", "BritainJetSeaHarrierFA2"),
        ("Command_ConstructBritainJetPhantomFG1", "BritainJetPhantomFG1"),
        ("Command_ConstructBritainJetJaguarGR3", "BritainJetJaguarGR3"),
        ("Command_ConstructBritainJetLightningF6", "BritainJetLightningF6"),
        ("Command_ConstructBritainJetHawk200", "BritainJetHawk200"),
    ],
    "Egypt": [
        ("Command_ConstructEgypt_Mig-29A", "Egypt_Mig-29A"),
        ("Command_ConstructEgyptJetRafaleDM_AA", "EgyptJetRafaleDM_AA"),
        ("Command_ConstructEgypt_MirageF1_Bq", "Egypt_MirageF1_Bq"),
        ("Command_ConstructEgypt_Su-25K", "Egypt_Su-25K"),
        ("Command_ConstructEgypt_Rafale", "Egypt_Rafale"),
        ("Command_ConstructEgypt_F16C", "Egypt_F16C"),
        ("Command_ConstructEgyptJetF16C", "EgyptJetF16C"),
        ("Command_ConstructEgyptJetRafaleDM", "EgyptJetRafaleDM"),
        ("Command_ConstructEgyptJetMig29M2", "EgyptJetMig29M2"),
        ("Command_ConstructEgyptJetSU35BM", "EgyptJetSU35BM"),
        ("Command_ConstructEgypt_Mi-8T", "Egypt_Mi-8T"),
        ("Command_ConstructEgypt_IL-76", "SpecterPlayableIL76"),
    ],
    "France": [
        ("Command_ConstructFranceJetRafaleC", "FranceJetRafaleC"),
        ("Command_ConstructFranceJetMirage20005F", "FranceJetMirage20005F"),
        ("Command_ConstructFranceJetMirage2000D", "FranceJetMirage2000D"),
        ("Command_ConstructFranceJetMirageF1CT", "FranceJetMirageF1CT"),
        ("Command_ConstructFranceJetRafaleB", "FranceJetRafaleB"),
        ("Command_ConstructFranceJetRafaleM", "FranceJetRafaleM"),
        ("Command_ConstructFranceJetRafaleF4", "FranceJetRafaleF4"),
        ("Command_ConstructFranceJetRafaleF3", "FranceJetRafaleF3"),
        ("Command_ConstructFranceJetMirage2000", "FranceJetMirage2000"),
        ("Command_ConstructFranceJetMirageIIIE", "FranceJetMirageIIIE"),
        ("Command_ConstructFranceJetMirage5", "FranceJetMirage5"),
        ("Command_ConstructFranceJetFCASNGF", "FranceJetFCASNGF"),
    ],
    "Germany": [
        ("Command_ConstructGermanyJetTyphoonT4", "GermanyJetTyphoonT4"),
        ("Command_ConstructGermanyJetTyphoonT1", "GermanyJetTyphoonT1"),
        ("Command_ConstructGermanyJetTornadoECR", "GermanyJetTornadoECR"),
        ("Command_ConstructGermanyJetTornadoIDS", "GermanyJetTornadoIDS"),
        ("Command_ConstructGermanyJetF35A", "GermanyJetF35A"),
        ("Command_ConstructGermanyJetMiG29G", "GermanyJetMiG29G"),
        ("Command_ConstructGermanyJetTyphoonECR", "GermanyJetTyphoonECR"),
        ("Command_ConstructGermanyJetTornadoADV", "GermanyJetTornadoADV"),
        ("Command_ConstructGermanyJetF4F", "GermanyJetF4F"),
        ("Command_ConstructGermanyJetAlphaJet", "GermanyJetAlphaJet"),
        ("Command_ConstructGermanyJetMako", "GermanyJetMako"),
        ("Command_ConstructGermanyJetFCASNGF", "GermanyJetFCASNGF"),
    ],
    "Israel": [
        ("Command_ConstructIsraelJetF35I_AA", "IsraelJetF35I_AA"),
        ("Command_ConstructIsrael_F15I_AA", "Israel_F15I_AA"),
        ("Command_ConstructIsrael_F16I_AG", "Israel_F16I_AG"),
        ("Command_ConstructIsraelJetF16ISufaPrecision", "IsraelJetF16ISufaPrecision"),
        ("Command_ConstructIsraelJetF35IAdirPenetrator", "IsraelJetF35IAdirPenetrator"),
        ("Command_ConstructIsraelJetF16CBarak", "IsraelJetF16CBarak"),
        ("Command_ConstructIsraelJetF15CBaz", "IsraelJetF15CBaz"),
        ("Command_ConstructIsraelJetF15IRaamII", "IsraelJetF15IRaamII"),
        ("Command_ConstructIsraelJetKfir", "IsraelJetKfir"),
        ("Command_ConstructIsraelJetNesher", "IsraelJetNesher"),
        ("Command_ConstructIsraelJetF4E", "IsraelJetF4E"),
        ("Command_ConstructIsraelJetF15IRaamDeepStrike", "IsraelJetF15IRaamDeepStrike"),
    ],
    "Italy": [
        ("Command_ConstructItalyJetTyphoon", "ItalyJetTyphoon"),
        ("Command_ConstructItalyJetF35B", "ItalyJetF35B"),
        ("Command_ConstructItalyJetTornadoECR", "ItalyJetTornadoECR"),
        ("Command_ConstructItalyJetAMX", "ItalyJetAMX"),
        ("Command_ConstructItalyJetF35A", "ItalyJetF35A"),
        ("Command_ConstructItalyJetTornadoIDS", "ItalyJetTornadoIDS"),
        ("Command_ConstructItalyJetEF2000T4", "ItalyJetEF2000T4"),
        ("Command_ConstructItalyJetHarrierII", "ItalyJetHarrierII"),
        ("Command_ConstructItalyJetF16", "ItalyJetF16"),
        ("Command_ConstructItalyJetM346FA", "ItalyJetM346FA"),
        ("Command_ConstructItalyJetMB339", "ItalyJetMB339"),
        ("Command_ConstructItalyJetGCAP", "ItalyJetGCAP"),
    ],
    "Libya": [
        ("Command_ConstructLibya_Mig-29A", "Libya_Mig-29A"),
        ("Command_ConstructLibyaJetMig25", "LibyaJetMig25"),
        ("Command_ConstructLibya_MirageF1_Bq", "Libya_MirageF1_Bq"),
        ("Command_ConstructLibyaJetMig23", "LibyaJetMig23"),
        ("Command_ConstructLibyaJetJ7", "LibyaJetJ7"),
        ("Command_ConstructLibyaJetSu22", "LibyaJetSu22"),
        ("Command_ConstructLibyaJetSu22M4", "LibyaJetSu22M4"),
        ("Command_ConstructLibya_Su-25K", "Libya_Su-25K"),
        ("Command_ConstructLibyaJetSu24", "LibyaJetSu24"),
        ("Command_ConstructLibyaJetMirageF1BD", "LibyaJetMirageF1BD"),
        ("Command_ConstructLibyaJetMig21", "LibyaJetMig21"),
        ("Command_ConstructLibyaJetMig21MF", "LibyaJetMig21MF"),
    ],
    "SouthAfrica": [
        ("Command_ConstructSouthAfricaJetCheetahC", "SouthAfricaJetCheetahC"),
        ("Command_ConstructSouthAfricaJetGripenC", "SouthAfricaJetGripenC"),
        ("Command_ConstructSouthAfrica_MirageF1_Bq", "SouthAfrica_MirageF1_Bq"),
        ("Command_ConstructSouthAfricaJetCheetahD", "SouthAfricaJetCheetahD"),
        ("Command_ConstructSouthAfricaJetCheetahE", "SouthAfricaJetCheetahE"),
        ("Command_ConstructSouthAfricaJetGripenD", "SouthAfricaJetGripenD"),
        ("Command_ConstructSouthAfricaJetGripenE", "SouthAfricaJetGripenE"),
        ("Command_ConstructSouthAfricaJetMirageIIICZ", "SouthAfricaJetMirageIIICZ"),
        ("Command_ConstructSouthAfricaJetHawk120", "SouthAfricaJetHawk120"),
        ("Command_ConstructSouthAfricaJetHawk127", "SouthAfricaJetHawk127"),
        ("Command_ConstructSouthAfricaJetImpala", "SouthAfricaJetImpala"),
        ("Command_ConstructSouthAfricaJetBuccaneer", "SouthAfricaJetBuccaneer"),
    ],
    "SouthKorea": [
        ("Command_ConstructSouthKoreaJetF35B", "SouthKoreaJetF35B"),
        ("Command_ConstructSouthKoreaJetF35A", "SouthKoreaJetF35A"),
        ("Command_ConstructSouthKoreaJetF5E", "SouthKoreaJetF5E"),
        ("Command_ConstructSouthKoreaJetF4E", "SouthKoreaJetF4E"),
        ("Command_ConstructSouthKoreaJetKF21", "SouthKoreaJetKF21"),
        ("Command_ConstructSouthKoreaJetF15KSlam", "SouthKoreaJetF15KSlam"),
        ("Command_ConstructSouthKoreaJetF16C", "SouthKoreaJetF16C"),
        ("Command_ConstructSouthKoreaJetF16D", "SouthKoreaJetF16D"),
        ("Command_ConstructSouthKoreaJetFA50", "SouthKoreaJetFA50"),
        ("Command_ConstructSouthKoreaJetFA50Blk20", "SouthKoreaJetFA50Blk20"),
        ("Command_ConstructSouthKoreaJetT50", "SouthKoreaJetT50"),
        ("Command_ConstructSouthKoreaJetKF21Blk2", "SouthKoreaJetKF21Blk2"),
    ],
    "Sweden": [
        ("Command_ConstructSwedenJetGripenA", "SwedenJetGripenA"),
        ("Command_ConstructSwedenJetGripenE", "SwedenJetGripenE"),
        ("Command_ConstructSwedenJetEF2000T4_CAS", "SwedenJetEF2000T4_CAS"),
        ("Command_ConstructSwedenJetViggenAJS37", "SwedenJetViggenAJS37"),
        ("Command_ConstructSwedenJetEF2000T4", "SwedenJetEF2000T4"),
        ("Command_ConstructSwedenJetEF2000T4_AA", "SwedenJetEF2000T4_AA"),
        ("Command_ConstructSwedenJetViggenJA37", "SwedenJetViggenJA37"),
        ("Command_ConstructSwedenJetViggenSH", "SwedenJetViggenSH"),
        ("Command_ConstructSwedenJetDrakenJ35", "SwedenJetDrakenJ35"),
        ("Command_ConstructSwedenJetLansenJ32", "SwedenJetLansenJ32"),
        ("Command_ConstructSwedenJetSK60", "SwedenJetSK60"),
        ("Command_ConstructSwedenJetSK60B", "SwedenJetSK60B"),
    ],
    "Vietnam": [
        ("Command_ConstructVietnamJetMig29S", "VietnamJetMig29S"),
        ("Command_ConstructVietnamJetMig21", "VietnamJetMig21"),
        ("Command_ConstructVietnamJetSu27", "VietnamJetSu27"),
        ("Command_ConstructVietnamJetSu22", "VietnamJetSu22"),
        ("Command_ConstructVietnamJetSu30", "VietnamJetSu30"),
        ("Command_ConstructVietnamJetYak130", "VietnamJetYak130"),
        ("Command_ConstructVietnamJetF5E", "VietnamJetF5E"),
        ("Command_ConstructVietnamJetMig21bis", "VietnamJetMig21bis"),
        ("Command_ConstructVietnamJetSu22M4", "VietnamJetSu22M4"),
        ("Command_ConstructVietnamJetSu30MK2", "VietnamJetSu30MK2"),
        ("Command_ConstructVietnamJetSu27UB", "VietnamJetSu27UB"),
        ("Command_ConstructVietnamJetL39", "VietnamJetL39"),
    ],
}

# Dual names: object-bound XAirfieldCommandSet + country-INI X_AirfieldCommandSet.
CS_NAMES: dict[str, list[str]] = {
    "Turkey": ["TurkeyAirfieldCommandSet"],
    "Ukraine": ["UkraineAirfieldCommandSet"],
    "Japan": ["Japan_AirfieldCommandSet"],
    "Britain": ["BritainAirfieldCommandSet", "Britain_AirfieldCommandSet"],
    "Egypt": ["Egypt_AirfieldCommandSet"] + [f"Egypt_AirfieldCommandSet{i}" for i in (1, 2, 3)],
    "France": ["FranceAirfieldCommandSet", "France_AirfieldCommandSet"],
    "Germany": ["GermanyAirfieldCommandSet", "Germany_AirfieldCommandSet"],
    "Israel": ["Israel_AirfieldCommandSet"] + [f"Israel_AirfieldCommandSet{i}" for i in (1, 2, 3)],
    "Italy": ["ItalyAirfieldCommandSet", "Italy_AirfieldCommandSet"],
    "Libya": ["Libya_AirfieldCommandSet"] + [f"Libya_AirfieldCommandSet{i}" for i in (1, 2, 3)],
    "SouthAfrica": ["SouthAfrica_AirfieldCommandSet"] + [f"SouthAfrica_AirfieldCommandSet{i}" for i in (1, 2, 3)],
    "SouthKorea": ["SouthKorea_AirfieldCommandSet"],
    "Sweden": ["SwedenAirfieldCommandSet"],
    "Vietnam": ["Vietnam_AirfieldCommandSet"],
}

NEW_BUTTON_OBJECTS = {
    "TurkeyJetKAAN", "TurkeyJetKAANBlk2", "TurkeyJetF16C", "TurkeyJetF16Ozgur",
    "TurkeyJetF16Blk30", "TurkeyJetF4ETerm", "TurkeyJetF4E", "TurkeyJetRF4E",
    "TurkeyJetHurjet", "TurkeyJetNF5",
    "SwedenJetGripenA", "SwedenJetGripenE", "SwedenJetViggenJA37",
    "SwedenJetViggenAJS37", "SwedenJetViggenSH", "SwedenJetDrakenJ35",
    "SwedenJetLansenJ32", "SwedenJetSK60", "SwedenJetSK60B",
    "LibyaJetMirageF1BD", "LibyaJetMig23", "LibyaJetMig25", "LibyaJetMig21",
    "LibyaJetMig21MF", "LibyaJetJ7", "LibyaJetSu22", "LibyaJetSu22M4", "LibyaJetSu24",
    "VietnamJetMig21bis", "VietnamJetSu22M4", "VietnamJetSu30MK2",
    "VietnamJetSu27UB", "VietnamJetL39",
    "FranceJetRafaleF4", "FranceJetMirage20005F", "FranceJetFCASNGF",
    "GermanyJetTyphoonT1", "GermanyJetFCASNGF",
    "BritainJetTempest",
    "ItalyJetGCAP",
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
        entries.append((name, data[off:off + size]))
    return entries


def first_val(body: str, key: str):
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", body)
    return m.group(1) if m else None


def replace_weaponsets(body: str, new_ws: str) -> str:
    m = re.search(r"(?im)^\s*WeaponSet\b", body)
    if not m:
        raise SystemExit("WeaponSet missing")
    rest = body[m.start():]
    armor = re.search(r"(?im)^\s*ArmorSet\b", rest)
    if not armor:
        raise SystemExit("ArmorSet missing after WeaponSet")
    return body[: m.start()] + new_ws.rstrip() + "\n\n" + rest[armor.start():]


def big_path_to_ws(packed: str) -> Path:
    rel = packed.replace("\\", "/")
    if rel.lower().startswith("data/"):
        rel = rel[5:]
    return INI / rel[len("INI/"):] if rel.startswith("INI/") else ROOT / rel


def main() -> int:
    if len(NEW_BUTTON_OBJECTS) != 40:
        raise SystemExit(f"NEW_BUTTON_OBJECTS {len(NEW_BUTTON_OBJECTS)} != 40")
    for obj in KEEP_OBJECTS:
        if obj in REBINDS:
            raise SystemExit(f"KEEP object scheduled for rebind: {obj}")

    entries = read_big(BIG)
    file_by_name = {n.replace("/", "\\"): b for n, b in entries}

    OBJ_RE = re.compile(r"(?m)^Object\s+(\S+)\s*\n(.*?)(?=^Object\s|\Z)", re.S)
    WPN_RE = re.compile(r"(?m)^Weapon\s+(\S+)\s*$")
    BTN_RE = re.compile(r"(?m)^CommandButton\s+(\S+)\s*$")

    obj_src: dict[str, str] = {}
    obj_body: dict[str, str] = {}
    weapons: set[str] = set()
    live_buttons: set[str] = set()

    for n, b in entries:
        t = b.decode("latin1", errors="replace").replace("\r\n", "\n")
        if n.lower().endswith(".ini") and "commandbutton" in n.lower():
            live_buttons.update(BTN_RE.findall(t))
        if n.lower().endswith(".ini"):
            weapons.update(WPN_RE.findall(t))
            if "Object " in t:
                for m in OBJ_RE.finditer(t):
                    obj_src[m.group(1)] = n.replace("/", "\\")
                    obj_body[m.group(1)] = m.group(2)

    needed = set()
    for ws in REBINDS.values():
        needed.update(re.findall(r"Weapon\s*=\s*(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", ws))
    missing_w = sorted(w for w in needed if w not in weapons)
    if missing_w:
        raise SystemExit(f"missing weapons in live BIG: {missing_w}")

    written: list[str] = []

    for obj, ws in REBINDS.items():
        if obj not in obj_src:
            raise SystemExit(f"rebind object missing from BIG: {obj}")
        packed = obj_src[obj]
        raw = file_by_name[packed].decode("latin1").replace("\r\n", "\n")
        om = re.search(rf"(?m)^Object {re.escape(obj)}\b\n(.*?)(?=^Object |\Z)", raw, re.S)
        if not om:
            raise SystemExit(f"cannot isolate {obj} in {packed}")
        new_body = replace_weaponsets(om.group(1), ws)
        new_raw = raw[: om.start()] + f"Object {obj}\n" + new_body
        dest = big_path_to_ws(packed)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(new_raw.replace("\n", "\r\n"), encoding="latin1", newline="")
        written.append(str(dest.relative_to(ROOT)))

    btn_lines = [
        "; FIGHTER_ROSTER_NEXT14 missing UNIT_BUILD buttons\n",
        "; Last-win append. Does not rewrite CommandButton.ini\n\n",
    ]
    new_btn_count = 0
    for country, slots in AIRFIELD.items():
        for btn, obj in slots:
            if obj not in NEW_BUTTON_OBJECTS:
                continue
            if btn in live_buttons:
                raise SystemExit(f"button already live, not a missing-40: {btn}")
            if obj not in obj_body:
                raise SystemExit(f"button object missing: {obj}")
            image = first_val(obj_body[obj], "ButtonImage") or first_val(obj_body[obj], "SelectPortrait") or "us_airfield"
            btn_lines.append(
                f"CommandButton {btn}\n"
                f"  Command          = UNIT_BUILD\n"
                f"  Object           = {obj}\n"
                f"  TextLabel        = CONTROLBAR:Construct{obj}\n"
                f"  ButtonImage      = {image}\n"
                f"  ButtonBorderType = BUILD\n"
                f"  DescriptLabel    = CONTROLBAR:ToolTipConstruct{obj}\n"
                f"End\n\n"
            )
            new_btn_count += 1
    if new_btn_count != 40:
        raise SystemExit(f"wrote {new_btn_count} new buttons, expected 40")
    BTN_OUT.write_text("".join(btn_lines).replace("\n", "\r\n"), encoding="latin1", newline="")
    written.append(str(BTN_OUT.relative_to(ROOT)))

    cs_lines = [
        "; FIGHTER_ROSTER_NEXT14 last-win airfield CommandSets\n",
        "; 2 A2A / 2 AT / 6 strike + 2 overflow. Heavy CommandSets are NOT touched.\n\n",
    ]
    for country, slots in AIRFIELD.items():
        for cs_name in CS_NAMES[country]:
            cs_lines.append(f"CommandSet {cs_name}\n")
            for i, (btn, _obj) in enumerate(slots, start=1):
                cs_lines.append(f"  {i} = {btn}\n")
            cs_lines.append("  13 = Command_SetRallyPoint\n")
            cs_lines.append("  14 = Command_Sell\n")
            cs_lines.append("End\n\n")
    CS_OUT.write_text("".join(cs_lines).replace("\n", "\r\n"), encoding="latin1", newline="")
    written.append(str(CS_OUT.relative_to(ROOT)))

    print("WROTE", len(written), "files")
    for p in written:
        print(" ", p)
    print("NEW_BUTTONS", new_btn_count)
    print("REBIND_OBJECTS", len(REBINDS))
    print("KEEP_OBJECTS", len(KEEP_OBJECTS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
