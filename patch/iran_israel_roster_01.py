#!/usr/bin/env python3
"""SPECTER1 Iran + Israel roster pass.

Baseline: SPECTER1_Ukraine_SouthAfrica_Roster_01 DATA+ART.
Does not revert prior country work.
Does not modify USA/Russia/China donor INIs or STD44 files.
Only Iran and Israel CommandSets, object INIs, and new clone files.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_UKRAINE_SOUTHAFRICA_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_UKRAINE_SOUTHAFRICA_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "3a844974065d21b7ce745020778e775b0de2afe06feae6b4db447a89da2017fb"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_IRAN_ISRAEL_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_IRAN_ISRAEL_ROSTER_01")

P_CMDSET = jf.P_CMDSET
P_CMDBTN = jf.P_CMDBTN
P_WEAPON = jf.P_WEAPON
P_NATIONAL = jf.P_NATIONAL

USA_B1 = r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini"
USA_B2 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"
USA_E3 = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
USA_V22 = r"Data\INI\Object\Specter\United States Of America\AmericaJetV22Visual.ini"
FR_B21 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB21.ini"
FR_B52 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB52H.ini"
RUS_TU22 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini"
RUS_TU160 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetTU160.ini"
CHN_H6K = r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini"
CHN_H20 = r"Data\INI\Object\Specter\PLA\Airforce\H20.ini"

IRAN_AF = r"Data\INI\Object\Specter\Iranian Army\Buildings\Airfield.ini"
IRAN_LARGE = r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_LargeAirBase.ini"
IRAN_HEAVY = r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_HeavyAirBase.ini"
IRAN_SYS = r"Data\INI\Object\Specter\Iranian Army\Iran_System.ini"
IRAN_MI8 = r"Data\INI\Object\Specter\Iranian Army\Airforce\Mil_Mi8.ini"
IRAN_PANHA = r"Data\INI\Object\Specter\Iranian Army\Airforce\Iran_Panha2091.ini"

IRAN_FIGHTERS = [
    r"Data\INI\Object\Specter\Iranian Army\Airforce\Iran_F14A.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF14AM.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF4E.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\Iran_Mig29A.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetMig21Bis.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetF7N.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\Iran_Su22.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\Iran_Su-24M.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\Iran_Su-25K.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetSu35S.ini",
    r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetMirageF1CR.ini",
]

IRAN_TU22_NEW = r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetTu22M3M.ini"
IRAN_TU160_NEW = r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetTu160.ini"
IRAN_H6K_NEW = r"Data\INI\Object\Specter\Iranian Army\Airforce\IranBomberH6K.ini"
IRAN_H20_NEW = r"Data\INI\Object\Specter\Iranian Army\Airforce\IranBomberH20.ini"

ISR_AIR_T = r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_Airfield_T.ini"
ISR_HEAVY_BLD = r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_HeavyAirBase.ini"
ISR_LARGE_BLD = r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_LargeAirBase.ini"
ISR_E3_NEW = r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelAircraftE3USA.ini"
ISR_V22_NEW = r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetV22.ini"
ISR_B1_NEW = r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB1R.ini"
ISR_B52_NEW = r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB52H.ini"
ISR_B2_NEW = r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB2A.ini"
ISR_B21_NEW = r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB21.ini"

DONOR_PROTECTED = list(jf.DONOR_PROTECTED) + [
    USA_B1, USA_B2, USA_E3, USA_V22, FR_B21, FR_B52, RUS_TU22, RUS_TU160, CHN_H6K, CHN_H20,
]
STD44 = list(jf.STD44)
BYTE_LOCKED = list(STD44) + list(DONOR_PROTECTED)

MI8_AI = """  Behavior = JetAIUpdate ModuleTag_07
    OutOfAmmoDamagePerSecond = 0%
    TakeoffDistForMaxLift = 0%
    TakeoffPause = 500
    MinHeight = 5
    ParkingOffset = 3
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    ReturnToBaseIdleTime = 10000
    AutoAcquireEnemiesWhenIdle = Yes
  End
"""

IRAN_SYS_JETS = {
    "IranJetJ10CE", "IranJetSu47Berkut", "IranJetSu57E", "IranJetJ20E", "IranJetMiG41",
}

ISR_LARGE_CS = [
    "  1 = Command_ConstructIsraelJetF35I_AA",
    "  2 = Command_ConstructIsraelJetF35IAdirPenetrator",
    "  3 = Command_ConstructIsraelJetF16ISufaPrecision",
    "  4 = Command_ConstructIsrael_F16I_AG",
    "  5 = Command_ConstructIsraelJetF16CBarak",
    "  6 = Command_ConstructIsraelJetF15CBaz",
    "  7 = Command_ConstructIsrael_F15I_AA",
    "  8 = Command_ConstructIsraelJetF15IRaamII",
    "  9 = Command_ConstructIsraelJetKfir",
    "  10 = Command_ConstructIsraelJetNesher",
    "  11 = Command_ConstructIsraelJetF4E",
    "  12 = Command_ConstructIsraelJetF15IRaamDeepStrike",
    "  13 = Command_SetRallyPoint",
    "  14 = Command_Sell",
]


def expand_parking(text: str, rows: int, cols: int, label: str) -> str:
    m = re.search(r"(?im)^  Behavior = ParkingPlaceBehavior[\s\S]*?^  End", text)
    if not m:
        raise SystemExit(f"{label}: no ParkingPlaceBehavior")
    block = m.group(0)
    block, n1 = re.subn(r"(?im)^(\s*NumRows\s*=\s*)\S+", rf"\g<1>{rows}", block, count=1)
    block, n2 = re.subn(r"(?im)^(\s*NumCols\s*=\s*)\S+", rf"\g<1>{cols}", block, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"{label}: parking replace n1={n1} n2={n2}")
    if not re.search(r"(?im)^\s*HasRunways\s*=\s*Yes", block):
        block = re.sub(r"(?im)^(\s*NumCols\s*=\s*\S+[^\n]*\n)", r"\1    HasRunways              = Yes\n", block, count=1)
    return text[: m.start()] + block + text[m.end() :]


def fix_jetai_block(block: str, needs_runway: str) -> str:
    nl = "\r\n" if "\r\n" in block else "\n"
    if re.search(r"(?im)^\s*NeedsRunway\s*=", block):
        block = re.sub(r"(?im)^(\s*NeedsRunway\s*=\s*)\S+", rf"\g<1>{needs_runway}", block)
    else:
        block = re.sub(
            r"(?im)^(\s*MinHeight\s*=\s*\S+[^\n]*\n)",
            rf"\1    NeedsRunway               = {needs_runway}{nl}",
            block,
            count=1,
        )
    if re.search(r"(?im)^\s*KeepsParkingSpaceWhenAirborne\s*=", block):
        block = re.sub(r"(?im)^(\s*KeepsParkingSpaceWhenAirborne\s*=\s*)\S+", r"\g<1>No", block)
    else:
        block = re.sub(
            r"(?im)^(\s*NeedsRunway\s*=\s*\S+[^\n]*\n)",
            rf"\1    KeepsParkingSpaceWhenAirborne = No{nl}",
            block,
            count=1,
        )
    block = re.sub(r"(?im)^(\s*ReturnToBaseIdleTime\s*=\s*)999999\b", r"\g<1>10000", block)
    if not re.search(r"(?im)^\s*ParkingOffset\s*=", block):
        block = re.sub(
            r"(?im)^(\s*MinHeight\s*=\s*\S+[^\n]*\n)",
            rf"\1    ParkingOffset             = 3{nl}",
            block,
            count=1,
        )
    return block


def fix_jetai_in_text(text: str, label: str, needs_runway: str = "Yes") -> str:
    out, n = re.subn(
        r"(?im)^  Behavior = JetAIUpdate[\s\S]*?^  End",
        lambda m: fix_jetai_block(m.group(0), needs_runway),
        text,
    )
    if n < 1:
        raise SystemExit(f"{label}: no JetAIUpdate")
    return out


def fix_named_object_jetai(text: str, names: set[str], needs_runway: str) -> str:
    matches = list(re.finditer(r"(?im)^Object\s+(\S+)", text))
    if not matches:
        return text
    out = text[: matches[0].start()]
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start() : end]
        if m.group(1) in names and re.search(r"(?im)^  Behavior = JetAIUpdate", block):
            block = fix_jetai_in_text(block, m.group(1), needs_runway)
        out += block
    return out


def retarget_sides(text: str, new_side: str, old_sides: set[str]) -> str:
    def repl(m: re.Match[str]) -> str:
        if m.group(2) in old_sides:
            return m.group(1) + new_side
        return m.group(0)

    return re.sub(r"(?im)^(\s*Side\s*=\s*)(\S+)", repl, text)


def ensure_commandset(text: str, name: str, body_lines: list[str]) -> str:
    if re.search(rf"(?im)^CommandSet\s+{re.escape(name)}\s*$", text):
        return jf.replace_commandset(text, name, body_lines)
    nl = jf.file_nl(text)
    block = "CommandSet " + name + nl
    for line in body_lines:
        block += line + nl
    block += "End" + nl + nl
    if not text.endswith(("\n", "\r\n")):
        text += nl
    return text + block


def main() -> int:
    data_sha = jf.sha256_file(SRC_DATA)
    art_sha = jf.sha256_file(SRC_ART)
    if data_sha != EXPECTED_DATA_SHA:
        raise SystemExit(f"DATA SHA mismatch {data_sha}")
    if art_sha != EXPECTED_ART_SHA:
        raise SystemExit(f"ART SHA mismatch {art_sha}")

    entries = jf.read_big_list(SRC_DATA)
    art_entries = jf.read_big_list(SRC_ART)
    baseline_hashes = {jf.norm(n).lower(): hashlib.sha256(b).hexdigest() for n, b in entries}

    # --- Iran runway: more parking, jets release spots, helis leave runway ---
    jf.set_text(entries, IRAN_AF, expand_parking(jf.text_of(entries, IRAN_AF), 4, 4, "iran airfield"))
    jf.set_text(entries, IRAN_LARGE, expand_parking(jf.text_of(entries, IRAN_LARGE), 4, 4, "iran large"))
    jf.set_text(entries, IRAN_HEAVY, expand_parking(jf.text_of(entries, IRAN_HEAVY), 4, 4, "iran heavy"))
    for path in IRAN_FIGHTERS:
        t = jf.text_of(entries, path)
        t = fix_jetai_in_text(t, path, "Yes")
        jf.set_text(entries, path, t)
    sys_txt = jf.text_of(entries, IRAN_SYS)
    sys_txt = fix_named_object_jetai(sys_txt, IRAN_SYS_JETS, "Yes")
    jf.set_text(entries, IRAN_SYS, sys_txt)

    mi8 = jf.text_of(entries, IRAN_MI8)
    nl = jf.file_nl(mi8)
    mi8, n = re.subn(
        r"(?im)^  Behavior = ChinookAIUpdate ModuleTag_07\r?\n(?:.*\r?\n)*?^  End\r?\n",
        jf.to_nl(MI8_AI, nl),
        mi8,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"mi8 ChinookAI replace failed n={n}")
    mi8, n = re.subn(r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+", r"\1ComancheLocomotor", mi8, count=1)
    if n != 1:
        raise SystemExit("mi8 locomotor replace failed")
    if "ChinookAIUpdate" in mi8:
        raise SystemExit("mi8 still ChinookAIUpdate")
    if not re.search(r"(?im)^\s*NeedsRunway\s*=\s*No", mi8):
        raise SystemExit("mi8 missing NeedsRunway=No")
    jf.set_text(entries, IRAN_MI8, mi8)

    # --- Iran Russian/Chinese bomber clones ---
    tu22 = jf.clone_rename(
        jf.text_of(entries, RUS_TU22),
        [("RussiaJetTu22M3M", "IranJetTu22M3M")],
        "Russia",
        "Iran",
        "; SPECTER1 Iran Tu-22M3M clone. Donor RussiaJetTu22M3M (NOT modified).\n",
    )
    tu22, _ = jf.promote_player_upgrade_weaponset(tu22, "iran tu22")
    tu22 = fix_jetai_in_text(tu22, "iran tu22", "Yes")
    jf.add_file(entries, IRAN_TU22_NEW, tu22)

    tu160 = jf.clone_rename(
        jf.text_of(entries, RUS_TU160),
        [("RussiaJetTU160", "IranJetTu160")],
        "Russia",
        "Iran",
        "; SPECTER1 Iran Tu-160 clone. Donor RussiaJetTU160 (NOT modified).\n",
    )
    tu160, _ = jf.promote_player_upgrade_weaponset(tu160, "iran tu160")
    tu160 = fix_jetai_in_text(tu160, "iran tu160", "Yes")
    jf.add_file(entries, IRAN_TU160_NEW, tu160)

    h6k = jf.clone_rename(
        jf.text_of(entries, CHN_H6K),
        [("ChinaBomberH6K", "IranBomberH6K")],
        "China",
        "Iran",
        "; SPECTER1 Iran H-6K clone. Donor ChinaBomberH6K (NOT modified).\n",
    )
    h6k, _ = jf.promote_player_upgrade_weaponset(h6k, "iran h6k")
    h6k = fix_jetai_in_text(h6k, "iran h6k", "Yes")
    jf.add_file(entries, IRAN_H6K_NEW, h6k)

    h20 = jf.clone_rename(
        jf.text_of(entries, CHN_H20),
        [("ChinaBomberH20", "IranBomberH20")],
        "China",
        "Iran",
        "; SPECTER1 Iran H-20 clone. Donor ChinaBomberH20 (NOT modified).\n",
    )
    h20, _ = jf.promote_player_upgrade_weaponset(h20, "iran h20")
    h20 = fix_jetai_in_text(h20, "iran h20", "Yes")
    jf.add_file(entries, IRAN_H20_NEW, h20)

    # --- Israel USA aircraft clones ---
    e3 = jf.clone_rename(
        jf.text_of(entries, USA_E3),
        [("AmericaJetE3Visual", "IsraelAircraftE3USA")],
        "America",
        "Israel",
        "; SPECTER1 Israel USA AWACS. Donor AmericaJetE3Visual (NOT modified).\n",
    )
    e3 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", e3, count=1)
    e3 = jf.insert_before_geometry(e3, jf.E3_USA_MODULES, "israel e3")
    jf.add_file(entries, ISR_E3_NEW, e3)

    v22 = jf.clone_rename(
        jf.text_of(entries, USA_V22),
        [("AmericaJetV22Visual", "IsraelJetV22")],
        "America",
        "Israel",
        "; SPECTER1 Israel V-22 clone. Donor AmericaJetV22Visual (NOT modified).\n",
    )
    jf.add_file(entries, ISR_V22_NEW, v22)

    b1 = jf.clone_rename(
        jf.text_of(entries, USA_B1),
        [("AmericaJetB1R", "IsraelJetB1R")],
        "America",
        "Israel",
        "; SPECTER1 Israel B-1R clone. Donor AmericaJetB1R (NOT modified).\n",
    )
    b1, _ = jf.promote_player_upgrade_weaponset(b1, "israel b1")
    jf.add_file(entries, ISR_B1_NEW, b1)

    b52 = jf.clone_rename(
        jf.text_of(entries, FR_B52),
        [("FranceJetB52H", "IsraelJetB52H")],
        "France",
        "Israel",
        "; SPECTER1 Israel B-52H clone. Source FranceJetB52H (USA_System.ini not modified).\n",
    )
    b52, _ = jf.promote_player_upgrade_weaponset(b52, "israel b52")
    jf.add_file(entries, ISR_B52_NEW, b52)

    b2 = jf.clone_rename(
        jf.text_of(entries, USA_B2),
        [("AmericaJetB2A", "IsraelJetB2A")],
        "America",
        "Israel",
        "; SPECTER1 Israel B-2A clone. Donor AmericaJetB2A (NOT modified).\n",
    )
    jf.add_file(entries, ISR_B2_NEW, b2)

    b21 = jf.clone_rename(
        jf.text_of(entries, FR_B21),
        [("FranceJetB21", "IsraelJetB21")],
        "France",
        "Israel",
        "; SPECTER1 Israel B-21 clone. Source FranceJetB21 (AmericaJetB21Clean not modified).\n",
    )
    jf.add_file(entries, ISR_B21_NEW, b21)

    # Israel Side + parking so FactionIsrael can actually produce aircraft
    for path in (ISR_HEAVY_BLD, ISR_LARGE_BLD, ISR_AIR_T):
        t = retarget_sides(jf.text_of(entries, path), "Israel", {"AmericaAirForceGeneral", "America", "Nato"})
        t = expand_parking(t, 4, 4, path)
        jf.set_text(entries, path, t)
    for n, b in list(entries):
        ln = n.replace("/", "\\")
        if "Israel Defense Forces" not in ln or not ln.lower().endswith(".ini"):
            continue
        if jf.norm(ln).lower() in {jf.norm(x).lower() for x in BYTE_LOCKED}:
            continue
        t = b.decode("latin1", errors="replace")
        t2 = retarget_sides(t, "Israel", {"AmericaAirForceGeneral", "America", "Nato"})
        if t2 != t:
            jf.set_text(entries, n, t2)

    # --- Unlock Iran + Israel ---
    unlock_files = 0
    unlock_lines = 0
    protected = {jf.norm(x).lower() for x in BYTE_LOCKED}
    for n, b in list(entries):
        ln = n.replace("/", "\\")
        if not ln.lower().endswith(".ini"):
            continue
        if "\\object\\" not in ln.lower():
            continue
        if jf.norm(ln).lower() in protected:
            continue
        allow = (
            "Iranian Army" in ln
            or "Israel Defense" in ln
            or ln.endswith("NationalGroundForces.ini")
        )
        if not allow:
            continue
        t = b.decode("latin1", errors="replace")
        t2, stripped = jf.unlock_named_objects(t, ("Iran", "IRAN", "Israel"))
        if t2 != t:
            jf.set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    btn = jf.text_of(entries, P_CMDBTN)
    new_btns = [
        jf.unit_button("Command_ConstructIranJetTu22M3M", "IranJetTu22M3M", "TU22M3", "\n"),
        jf.unit_button("Command_ConstructIranJetTu160", "IranJetTu160", "TU160", "\n"),
        jf.unit_button("Command_ConstructIranBomberH6K", "IranBomberH6K", "pla_h6k", "\n"),
        jf.unit_button("Command_ConstructIranBomberH20", "IranBomberH20", "pla_h20", "\n"),
        jf.unit_button("Command_ConstructIsraelAircraftE3USA", "IsraelAircraftE3USA", "us_e3g", "\n"),
        jf.unit_button("Command_ConstructIsraelJetV22", "IsraelJetV22", "V22", "\n"),
        jf.unit_button("Command_ConstructIsraelJetB1R", "IsraelJetB1R", "B1", "\n"),
        jf.unit_button("Command_ConstructIsraelJetB52H", "IsraelJetB52H", "B52", "\n"),
        jf.unit_button("Command_ConstructIsraelJetB2A", "IsraelJetB2A", "B2A", "\n"),
        jf.unit_button("Command_ConstructIsraelJetB21", "IsraelJetB21", "B21_L", "\n"),
        jf.unit_button("Command_ConstructIsraelJetF16CBarak", "IsraelJetF16CBarak", "SPEC_IsraelJetF16CBarak", "\n"),
        jf.unit_button("Command_ConstructIsraelJetF15CBaz", "IsraelJetF15CBaz", "SPEC_IsraelF15CBaz", "\n"),
        jf.unit_button("Command_ConstructIsraelJetF15IRaamII", "IsraelJetF15IRaamII", "SPEC_IsraelJetF15IRaamII", "\n"),
        jf.unit_button("Command_ConstructIsraelJetKfir", "IsraelJetKfir", "SPEC_IsraelJetKfir", "\n"),
        jf.unit_button("Command_ConstructIsraelJetNesher", "IsraelJetNesher", "SPEC_IsraelJetNesher", "\n"),
        jf.unit_button("Command_ConstructIsraelJetF4E", "IsraelJetF4E", "SPEC_IsraelJetF4E", "\n"),
    ]
    btn = jf.append_buttons(btn, new_btns)
    jf.set_text(entries, P_CMDBTN, btn)

    cs = jf.text_of(entries, P_CMDSET)
    iran_heavy = [
        "  1 = Command_ConstructIranHelicopterPanha2091",
        "  2 = Command_ConstructIranHelicopterMi8",
        "  3 = Command_ConstructIranJetSu47Berkut",
        "  4 = Command_ConstructIranJetMirageF1CR",
        "  5 = Command_ConstructIranJetTu22M3M",
        "  6 = Command_ConstructIranJetTu160",
        "  7 = Command_ConstructIranBomberH6K",
        "  8 = Command_ConstructIranBomberH20",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "Iran_HeavyAirBaseCommandSet", iran_heavy)
    israel_heavy = [
        "  1 = Command_ConstructIsraelAircraftE3USA",
        "  2 = Command_ConstructIsraelJetV22",
        "  3 = Command_ConstructIsraelJetB1R",
        "  4 = Command_ConstructIsraelJetB52H",
        "  5 = Command_ConstructIsraelJetB2A",
        "  6 = Command_ConstructIsraelJetB21",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "Israel_HeavyAirBaseCommandSet", israel_heavy)
    for name in (
        "Israel_LargeAirBaseCommandSet",
        "Israel_AirfieldCommandSet",
        "Israel_AirfieldCommandSet1",
        "Israel_AirfieldCommandSet2",
        "Israel_AirfieldCommandSet3",
    ):
        cs = ensure_commandset(cs, name, ISR_LARGE_CS)
    jf.set_text(entries, P_CMDSET, cs)

    for p in BYTE_LOCKED:
        try:
            i = jf.find_index(entries, p)
        except SystemExit:
            continue
        new_h = hashlib.sha256(entries[i][1]).hexdigest()
        old_h = baseline_hashes[jf.norm(p).lower()]
        if new_h != old_h:
            raise SystemExit(f"PROTECTED FILE CHANGED: {p}")

    if "Object RussiaJetTu22M3M" not in jf.text_of(entries, RUS_TU22):
        raise SystemExit("Russia Tu22 damaged")
    if "Object ChinaBomberH6K" not in jf.text_of(entries, CHN_H6K):
        raise SystemExit("China H6K damaged")
    if "Object AmericaJetE3Visual" not in jf.text_of(entries, USA_E3):
        raise SystemExit("USA E3 damaged")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, ISR_E3_NEW):
        raise SystemExit("Israel E3 missing USA radar")
    if re.search(r"(?im)^\s*KeepsParkingSpaceWhenAirborne\s*=\s*Yes", jf.text_of(entries, IRAN_FIGHTERS[3])):
        raise SystemExit("Iran Mig29 still keeps parking")
    park = jf.text_of(entries, IRAN_AF)
    if not re.search(r"(?im)^\s*NumRows\s*=\s*4", park) or not re.search(r"(?im)^\s*NumCols\s*=\s*4", park):
        raise SystemExit("Iran airfield parking not expanded")
    if not re.search(r"(?im)^\s*Side\s*=\s*Israel\b", jf.text_of(entries, ISR_HEAVY_BLD)):
        raise SystemExit("Israel HeavyAirBase side not Israel")
    if "ChinookAIUpdate" in jf.text_of(entries, IRAN_MI8):
        raise SystemExit("Mi8 still ChinookAI")

    seen: dict[str, list[str]] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        if "\\object\\" not in n.lower().replace("/", "\\"):
            continue
        t = b.decode("latin1", errors="replace")
        for m in re.finditer(r"(?im)^Object\s+(\S+)", t):
            seen.setdefault(m.group(1), []).append(n)
    for on in (
        "IranJetTu22M3M", "IranJetTu160", "IranBomberH6K", "IranBomberH20",
        "IsraelAircraftE3USA", "IsraelJetV22", "IsraelJetB1R", "IsraelJetB52H",
        "IsraelJetB2A", "IsraelJetB21",
    ):
        files = seen.get(on, [])
        if len(files) != 1:
            raise SystemExit(f"{on} files={files}")

    illegal = jf.object_folder_illegal(entries)
    btns = jf.parse_buttons(jf.text_of(entries, P_CMDBTN))
    btns.update(jf.parse_buttons(jf.text_of(entries, P_CMDSET)))
    csets = jf.parse_commandsets(jf.text_of(entries, P_CMDSET))
    images = jf.mapped_images(entries)
    astems = jf.art_stems(art_entries)
    weapons = set(re.findall(r"(?im)^Weapon\s+(\S+)", jf.text_of(entries, P_WEAPON)))
    last_seen = {k: v[-1] for k, v in seen.items()}

    missing_btn: list[str] = []
    missing_obj: list[str] = []
    missing_img: list[str] = []
    missing_wpn: list[str] = []
    locked_counts = {"iran_air": 0, "iran_heavy": 0, "isr_air": 0, "isr_heavy": 0}

    def audit_cs(cs_name: str, bucket: str | None = None) -> list[str]:
        blk = csets[cs_name]
        cmds = re.findall(r"(?m)^\s*\d+\s*=\s*(\S+)", blk)
        rows = []
        skip = {"Command_SetRallyPoint", "Command_Sell", "Command_Stop"}
        for c in cmds:
            if c in skip:
                continue
            b = btns.get(c)
            if not b:
                missing_btn.append(f"{cs_name} -> {c}")
                continue
            objm = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", b)
            imgm = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", b)
            cmdm = re.search(r"(?im)^\s*Command\s*=\s*(\S+)", b)
            cmd = cmdm.group(1) if cmdm else ""
            if cmd in ("UNIT_BUILD", "DOZER_CONSTRUCT") and re.search(
                r"(?i)RequiredScience|NeededUpgrade|NEED_UPGRADE|NEED_SPECIAL_POWER_SCIENCE", b
            ):
                if bucket:
                    locked_counts[bucket] += 1
            if objm and objm.group(1) not in last_seen:
                missing_obj.append(f"{c} Object={objm.group(1)}")
            if cmd in ("UNIT_BUILD", "DOZER_CONSTRUCT") and imgm and imgm.group(1) not in images:
                missing_img.append(f"{c} ButtonImage={imgm.group(1)}")
            rows.append(c)
        return rows

    iran_air = audit_cs("IranAirfieldCommandSet", "iran_air")
    iran_heavy_btns = audit_cs("Iran_HeavyAirBaseCommandSet", "iran_heavy")
    isr_air = audit_cs("Israel_LargeAirBaseCommandSet", "isr_air")
    isr_field = audit_cs("Israel_AirfieldCommandSet", "isr_air")
    isr_heavy = audit_cs("Israel_HeavyAirBaseCommandSet", "isr_heavy")

    for w in ["AN_APY2_Radar_Power", "AWACS_BaseMonaitoring"]:
        if w not in weapons:
            missing_wpn.append(w)

    model_checks = ["RUS_TU22M3M", "LSFRussiaTu160", "h6k", "NVH20", "E3", "AVOsprey", "US_B1R", "US_B52H", "AVB3bmbr", "AVB21_A"]
    missing_models = [m for m in model_checks if m.lower() not in astems]

    if illegal:
        raise SystemExit("illegal Object-folder blocks: " + "; ".join(illegal[:8]))
    if missing_btn:
        raise SystemExit("missing buttons: " + "; ".join(missing_btn[:8]))
    if missing_obj:
        raise SystemExit("missing objects: " + "; ".join(missing_obj[:8]))
    if missing_wpn:
        raise SystemExit("missing weapons: " + "; ".join(missing_wpn[:8]))
    if missing_img:
        raise SystemExit("missing button images: " + "; ".join(missing_img[:12]))
    if missing_models:
        raise SystemExit("missing W3D: " + ", ".join(missing_models))
    if "Command_ConstructIranJetTu22M3M" not in iran_heavy_btns:
        raise SystemExit("Iran Tu-22 missing")
    if "Command_ConstructIranJetTu160" not in iran_heavy_btns:
        raise SystemExit("Iran Tu-160 missing")
    if "Command_ConstructIranBomberH6K" not in iran_heavy_btns:
        raise SystemExit("Iran H-6K missing")
    if "Command_ConstructIranBomberH20" not in iran_heavy_btns:
        raise SystemExit("Iran H-20 missing")
    if "Command_ConstructIsraelAircraftE3USA" not in isr_heavy:
        raise SystemExit("Israel USA AWACS missing")
    if "Command_ConstructIsraelJetV22" not in isr_heavy:
        raise SystemExit("Israel V-22 missing")
    if "Command_ConstructIsraelJetB1R" not in isr_heavy:
        raise SystemExit("Israel B-1 missing")
    if "Command_ConstructIsraelJetB52H" not in isr_heavy:
        raise SystemExit("Israel B-52 missing")
    if "Command_ConstructIsraelJetB2A" not in isr_heavy:
        raise SystemExit("Israel B-2 missing")
    if "Command_ConstructIsraelJetB21" not in isr_heavy:
        raise SystemExit("Israel B-21 missing")
    if "Command_ConstructIsraelJetF16CBarak" not in isr_air:
        raise SystemExit("Israel F16C button missing")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    e3_txt = jf.text_of(entries, ISR_E3_NEW)
    if "StealthDetectorUpdate" not in e3_txt:
        raise SystemExit("Israel E3 missing StealthDetectorUpdate")
    if "CAN_ATTACK" not in jf.text_of(entries, ISR_V22_NEW):
        raise SystemExit("Israel V22 lost CAN_ATTACK")

    changed = []
    for n, b in entries:
        h = hashlib.sha256(b).hexdigest()
        key = jf.norm(n).lower()
        if key not in baseline_hashes or baseline_hashes[key] != h:
            changed.append(n)
    changed.sort()
    other_hits = []
    for n in changed:
        ln = n.replace("/", "\\")
        ok = (
            ln in (P_CMDSET, P_CMDBTN)
            or "Iranian Army" in ln
            or "Israel Defense" in ln
            or ln.endswith("NationalGroundForces.ini")
        )
        if not ok:
            other_hits.append(n)
    if other_hits:
        raise SystemExit("unrelated paths changed: " + "; ".join(other_hits[:8]))

    blob = jf.build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    art_bytes = SRC_ART.read_bytes()
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_bytes)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_bytes)

    lines: list[str] = []
    p = lines.append
    p("SPECTER1 IRAN + ISRAEL ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy; donor W3D already packed)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("PRIOR_COUNTRIES_UNCHANGED = YES")
    p("")
    p("=== IRAN ===")
    p("RUNWAY_FIXED = YES (airfield parking 4x4; jets KeepsParking=No NeedsRunway=Yes; Mi-8 JetAI NeedsRunway=No)")
    p("RUSSIAN_BOMBERS_ADDED = YES (Tu-22M3M, Tu-160)")
    p("CHINESE_BOMBERS_ADDED = YES (H-6K, H-20)")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("IRAN AIRFIELD =")
    for c in iran_air:
        p("  " + c)
    p("IRAN HEAVY =")
    for c in iran_heavy_btns:
        p("  " + c)
    p("")
    p("=== ISRAEL ===")
    p("V22_ADDED = YES")
    p("B1_ADDED = YES")
    p("B52_ADDED = YES")
    p("B2_ADDED = YES")
    p("B21_ADDED = YES")
    p("USA_AWACS_ADDED = YES (IsraelAircraftE3USA clone of AmericaJetE3Visual)")
    p("SIDE_FIXED = YES (AmericaAirForceGeneral -> Israel on Israel folder objects/airbases)")
    p("AIRFIELD_COMMANDSETS_ADDED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("ISRAEL AIRFIELD/LARGE =")
    for c in isr_air:
        p("  " + c)
    p("ISRAEL HEAVY =")
    for c in isr_heavy:
        p("  " + c)
    p("")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("")
    p("=== SAFETY ===")
    p("USA_DONORS_UNCHANGED = YES")
    p("RUSSIA_TU22_DONOR_UNCHANGED = YES")
    p("CHINA_H6K_DONOR_UNCHANGED = YES")
    p("NATO_LIBYA_UKRAINE_SA_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("IRAN:")
    p("RUNWAY_FIXED = YES")
    p("RUSSIAN_BOMBERS_ADDED = YES")
    p("CHINESE_BOMBERS_ADDED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("ISRAEL:")
    p("V22_ADDED = YES")
    p("B1_ADDED = YES")
    p("B52_ADDED = YES")
    p("B2_ADDED = YES")
    p("B21_ADDED = YES")
    p("USA_AWACS_ADDED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Iran + Israel Roster 01

Continues from SPECTER1_Ukraine_SouthAfrica_Roster_01. Does not revert prior country work.
USA/Russia/China donor INIs and STD44 files untouched.

Iran:
- Fighter airfield parking expanded 3x2 -> 4x4. Jets set NeedsRunway=Yes and KeepsParkingSpaceWhenAirborne=No.
- Mi-8 ChinookAI/ChinookLocomotor replaced with JetAI NeedsRunway=No + ComancheLocomotor (airfield takeoff).
- Russian Tu-22M3M and Tu-160 plus Chinese H-6K and H-20 cloned onto HeavyAirBase.
- Science/NeededUpgrade stripped.

Israel:
- Heavy/Large airbase and Israel-folder objects retargeted Side=Israel (were AmericaAirForceGeneral).
- Missing airfield CommandSets and fighter construct buttons added.
- USA clones: E-3 AWACS, V-22, B-1R, B-52H, B-2A, B-21 on HeavyAirBase.
- Science/NeededUpgrade stripped.

ART packed unchanged (existing W3D stems). INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    zpath = WS_OUT / "SPECTER1_Iran_Israel_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Iran_Israel_Roster_01.zip").write_bytes(zpath.read_bytes())
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
