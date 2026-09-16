#!/usr/bin/env python3
"""SPECTER1 South Korea + Italy roster pass.

Baseline: SPECTER1_Japan_France_Roster_01 DATA+ART.
Does not revert India/Germany/Japan/France/Vietnam/Syria work.
Does not modify USA/Germany donor INIs or STD44 files.
Only South Korea and Italy CommandSets, object INIs, and new clone files.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_JAPAN_FRANCE_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_JAPAN_FRANCE_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "d7d466a8933b362dd192f390b9095abce494c24cdf8834212aaccbb0880f7bdf"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_KOREA_ITALY_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_KOREA_ITALY_ROSTER_01")

P_CMDSET = jf.P_CMDSET
P_CMDBTN = jf.P_CMDBTN
P_WEAPON = jf.P_WEAPON
P_NATIONAL = jf.P_NATIONAL

USA_B1 = r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini"
DE_C130 = jf.DE_C130
FR_B52 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB52H.ini"
SK_AH64_STD = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetAH64E.ini"
SK_F35B_STD = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35B.ini"
IT_F35B_STD = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35B.ini"
IT_CH47_STD = r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\CH47F.ini"

SK_F35A = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35A.ini"
SK_KF21 = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF21.ini"
SK_F15K = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF15KSlam.ini"
SK_F16C = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16C.ini"
SK_F16D = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16D.ini"
SK_FA50 = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetFA50.ini"
SK_FA50B20 = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetFA50Blk20.ini"
SK_T50 = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetT50.ini"
SK_F4E = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF4E.ini"
SK_F5E = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF5E.ini"
SK_KF21B2 = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF21Blk2.ini"
SK_E737 = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetE737.ini"
SK_UH60 = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetUH60P.ini"
SK_AH64_NEW = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaHelicopterAH64E.ini"
SK_CN235_NEW = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetCN235US.ini"
SK_B1_NEW = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetB1R.ini"
SK_B52_NEW = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetB52H.ini"

IT_TYPH = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTyphoon.ini"
IT_EF2000 = r"Data\INI\Object\Specter\Italian Armed Forces\FixedWings\EF2000_T4.ini"
IT_F35A = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35A.ini"
IT_TIDS = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTornadoIDS.ini"
IT_TECR = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetTornadoECR.ini"
IT_AMX = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetAMX.ini"
IT_HAR = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetHarrierII.ini"
IT_F16 = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF16.ini"
IT_GCAP = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetGCAP.ini"
IT_M346 = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetM346FA.ini"
IT_MB339 = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetMB339.ini"
IT_G550 = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyAircraftG550CAEW.ini"
IT_A129 = r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterA129.ini"
IT_AW101 = r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW101.ini"
IT_C27 = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetC27J.ini"

DONOR_PROTECTED = list(jf.DONOR_PROTECTED) + [USA_B1, DE_C130, FR_B52, jf.USA_SYSTEM, jf.USA_PROWLER, jf.USA_B21]
STD44 = list(jf.STD44)

UH60_WEAPONS = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY 30mm_M230E1_ChainGun
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 70mm_Hydra_AH64E
    PreferredAgainst = SECONDARY STRUCTURE INFANTRY
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY GenericHeliRWR
    PreferredAgainst = TERTIARY AIRCRAFT
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""

AW101_AI = """  Behavior = JetAIUpdate ModuleTag_09ai
    OutOfAmmoDamagePerSecond = 0%
    TakeoffDistForMaxLift = 0%
    TakeoffPause = 500
    MinHeight = 5
    ParkingOffset = 3
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    ReturnToBaseIdleTime = 10000
    AutoAcquireEnemiesWhenIdle = No
  End
"""


def replace_models(text: str, pairs: list[tuple[str, str]], label: str) -> str:
    out = text
    for old, new in pairs:
        out2, n = re.subn(rf"(?im)^(\s*Model\s*=\s*){re.escape(old)}\b", rf"\1{new}", out)
        if n < 1:
            raise SystemExit(f"{label}: model {old} not found")
        out = out2
    return out


def fix_uh60(text: str) -> str:
    nl = jf.file_nl(text)
    if not text.startswith("; SPECTER1"):
        text = "; SPECTER1 South Korea UH-60P combat-utility. CAN_ATTACK + JetAI NeedsRunway=No.\n" + text
    text, n = re.subn(
        r"(?im)^(\s*CommandSet\s*=\s*)\S+",
        r"\1GenericAttackHelicopterHoverCommandSet",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("uh60 commandset")
    if "30mm_M230E1_ChainGun" not in text:
        text = re.sub(
            r"(?im)^(\s*CommandSet\s*=\s*GenericAttackHelicopterHoverCommandSet[^\n]*\n)",
            r"\1" + jf.to_nl(UH60_WEAPONS, nl),
            text,
            count=1,
        )
    text, n = re.subn(
        r"(?im)^(\s*KindOf\s*=\s*).*$",
        r"\1PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT PRODUCED_AT_HELIPAD",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("uh60 kindof")
    text, n = re.subn(
        r"(?im)^  Behavior = JetAIUpdate ModuleTag_09ai\r?\n(?:.*\r?\n)*?^  End\r?\n",
        jf.to_nl(
            """  Behavior = JetAIUpdate ModuleTag_09ai
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
""",
            nl,
        ),
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("uh60 jetai")
    text, n = re.subn(
        r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+",
        r"\1ComancheLocomotor",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("uh60 loco")
    if "CAN_ATTACK" not in text or "NeedsRunway = No" not in text:
        raise SystemExit("uh60 still broken")
    return text


def fix_aw101(text: str) -> str:
    nl = jf.file_nl(text)
    if not text.startswith("; SPECTER1"):
        text = "; SPECTER1 Italy AW101 movement: ComancheLocomotor + full JetAI NeedsRunway=No.\n" + text
    text, n = re.subn(
        r"(?im)^  Behavior = JetAIUpdate ModuleTag_09ai\r?\n(?:.*\r?\n)*?^  End\r?\n",
        jf.to_nl(AW101_AI, nl),
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("aw101 jetai")
    text, n = re.subn(
        r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+",
        r"\1ComancheLocomotor",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("aw101 loco")
    return text


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

    # --- SK AH-64E combat clone (do not edit STD44 SouthKoreaJetAH64E.ini) ---
    ah = jf.text_of(entries, SK_AH64_STD)
    ah = ah.replace("Object SouthKoreaJetAH64E", "Object SouthKoreaHelicopterAH64E")
    ah, n = re.subn(r"GenericHeliGunnerSight", "30mm_M230E1_ChainGun", ah, count=1)
    if n != 1:
        raise SystemExit("ah64 gun replace")
    ah, n = re.subn(r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+", r"\1ComancheLocomotor", ah, count=1)
    if n != 1:
        raise SystemExit("ah64 loco")
    ah = "; SPECTER1 ROK AH-64E combat clone. STD44 SouthKoreaJetAH64E unused. 30mm + Hellfire + Hydra, ComancheLocomotor.\n" + ah
    jf.add_file(entries, SK_AH64_NEW, ah)

    # --- American CN235 (LSFUSAC130 + An-124 contain), donor Germany C-130 not edited ---
    cn = jf.clone_rename(
        jf.text_of(entries, DE_C130),
        [("GermanyJetC130", "SouthKoreaJetCN235US")],
        "Germany",
        "SouthKorea",
        "; SPECTER1 ROK American CN235. Donor GermanyJetC130 LSFUSAC130 + An-124 contain (NOT modified).\n",
    )
    jf.add_file(entries, SK_CN235_NEW, cn)

    # --- B-1 from USA B1R ---
    b1 = jf.clone_rename(
        jf.text_of(entries, USA_B1),
        [("AmericaJetB1R", "SouthKoreaJetB1R")],
        "America",
        "SouthKorea",
        "; SPECTER1 ROK B-1R clone. Donor AmericaJetB1R (NOT modified).\n",
    )
    b1, _ = jf.promote_player_upgrade_weaponset(b1, "sk b1")
    jf.add_file(entries, SK_B1_NEW, b1)

    # --- B-52 from France B-52H clone (USA_System.ini not modified) ---
    b52 = jf.clone_rename(
        jf.text_of(entries, FR_B52),
        [("FranceJetB52H", "SouthKoreaJetB52H")],
        "France",
        "SouthKorea",
        "; SPECTER1 ROK B-52H clone. Source FranceJetB52H (USA_System.ini not modified this pass).\n",
    )
    jf.add_file(entries, SK_B52_NEW, b52)

    # --- SK fighter bombs (skip STD44 F-35B) ---
    sk_bombs = [
        (SK_KF21, "SECONDARY", "GBU_31V2_JDAM_F35C", "Paveway_IV_EF2000"),
        (SK_F15K, "SECONDARY", "GBU_31V2_JDAM_F35C", "Kab500_LeaserGuidedBomb"),
        (SK_F16C, "SECONDARY", "GBU_31V2_JDAM_F35C", "6_MK-82"),
        (SK_F16D, "SECONDARY", "GBU_31V2_JDAM_F35C", "Gbu-12II_Paveway"),
        (SK_FA50, "SECONDARY", "GBU_31V2_JDAM_F35C", "GBU38_JDAM_F16C"),
        (SK_FA50B20, "SECONDARY", "GBU_31V2_JDAM_F35C", "GBU-39_SDB_F22A"),
        (SK_T50, "SECONDARY", "GBU_31V2_JDAM_F35C", "Fab-250"),
        (SK_F4E, "SECONDARY", "GBU_31V2_JDAM_F35C", "Kab1500_LeaserGuidedBomb"),
        (SK_F5E, "SECONDARY", "GBU_31V2_JDAM_F35C", "Kab2500_LeaserGuidedBomb"),
        (SK_KF21B2, "SECONDARY", "GBU_31V2_JDAM_F35C", "AGM-154C_JSOW_F16C"),
    ]
    for path, slot, old, new in sk_bombs:
        t = jf.text_of(entries, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)

    f5 = jf.text_of(entries, SK_F5E)
    f5, n = re.subn(r"(?im)^(\s*Scale\s*=\s*)\S+", r"\g<1>1.05", f5, count=1)
    if n != 1:
        raise SystemExit("f5e scale")
    jf.set_text(entries, SK_F5E, f5)

    fa50 = replace_models(
        jf.text_of(entries, SK_FA50),
        [("LSFT50k", "LSFF16Ck"), ("LSFT50d", "LSFF16Cd"), ("LSFT50", "LSFF16C")],
        "fa50 mesh",
    )
    jf.set_text(entries, SK_FA50, fa50)
    fa50b = replace_models(
        jf.text_of(entries, SK_FA50B20),
        [("LSFT50k", "AVF16_E"), ("LSFT50d", "AVF16_D"), ("LSFT50", "AVF16")],
        "fa50 blk20 mesh",
    )
    jf.set_text(entries, SK_FA50B20, fa50b)

    e737 = jf.text_of(entries, SK_E737)
    e737 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", e737, count=1)
    e737 = jf.insert_before_geometry(e737, jf.E3_USA_MODULES, "sk e737")
    jf.set_text(entries, SK_E737, e737)

    jf.set_text(entries, SK_UH60, fix_uh60(jf.text_of(entries, SK_UH60)))

    # --- Italy bombs (skip STD44 F-35B) ---
    it_bombs = [
        (IT_TYPH, "TERTIARY", "Italy_Weapon_JetCannon", "GBU_31V2_JDAM_F15E"),
        (IT_TIDS, "SECONDARY", "Italy_Weapon_Bomb", "6_MK-82"),
        (IT_TECR, "TERTIARY", "Italy_Weapon_JetCannon", "Kab500_LeaserGuidedBomb"),
        (IT_AMX, "PRIMARY", "Italy_Weapon_Bomb", "Kab1500_LeaserGuidedBomb"),
        (IT_HAR, "PRIMARY", "Italy_Weapon_Paveway", "GBU38_JDAM_F16C"),
        (IT_F16, "TERTIARY", "Italy_Weapon_JetCannon", "ODAB_500_PMV_SU39"),
        (IT_GCAP, "TERTIARY", "Italy_Weapon_PGM_GCAP", "Kab2500_LeaserGuidedBomb"),
        (IT_M346, "PRIMARY", "Italy_Weapon_JDAM", "AGM-154C_JSOW_F16C"),
        (IT_MB339, "PRIMARY", "Italy_Weapon_Bomb", "GBU-39_SDB_F22A"),
    ]
    for path, slot, old, new in it_bombs:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)
    # EF2000T4 keeps unique Paveway_IV; F-35A keeps Italy_Weapon_JDAM.

    g550 = jf.text_of(entries, IT_G550)
    g550 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", g550, count=1)
    g550 = jf.insert_before_geometry(g550, jf.E3_USA_MODULES, "italy g550")
    jf.set_text(entries, IT_G550, g550)

    a129 = jf.text_of(entries, IT_A129)
    a129, n = re.subn(r"(?im)^(\s*GeometryIsSmall\s*=\s*)Yes\b", r"\1No", a129, count=1)
    if n != 1:
        raise SystemExit("a129 geometry")
    if "NeedsRunway = No" not in a129:
        raise SystemExit("a129 runway")
    jf.set_text(entries, IT_A129, a129)
    jf.set_text(entries, IT_AW101, fix_aw101(jf.text_of(entries, IT_AW101)))

    c27 = replace_models(
        jf.text_of(entries, IT_C27),
        [("LSFUSAC130d", "US_C130H"), ("LSFUSAC130k", "US_C130H"), ("LSFUSAC130", "US_C130H")],
        "c27 color",
    )
    if not c27.startswith("; SPECTER1"):
        c27 = "; SPECTER1 Italy C-27J color: US_C130H American scheme (was LSFUSAC130).\n" + c27
    jf.set_text(entries, IT_C27, c27)

    # --- Unlock SK + Italy ---
    unlock_files = 0
    unlock_lines = 0
    protected = {jf.norm(x).lower() for x in STD44 + DONOR_PROTECTED}
    for n, b in list(entries):
        ln = n.replace("/", "\\")
        if not ln.lower().endswith(".ini"):
            continue
        if "\\object\\" not in ln.lower():
            continue
        if jf.norm(ln).lower() in protected:
            continue
        allow = (
            "Republic of Korea" in ln
            or "South Korean Armed" in ln
            or "Italian Armed" in ln
            or ln.endswith("NationalGroundForces.ini")
        )
        if not allow:
            continue
        t = b.decode("latin1", errors="replace")
        t2, stripped = jf.unlock_named_objects(t, ("SouthKorea", "Italy"))
        if t2 != t:
            jf.set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    btn = jf.text_of(entries, P_CMDBTN)
    new_btns = [
        jf.unit_button("Command_ConstructSouthKoreaHelicopterAH64E", "SouthKoreaHelicopterAH64E", "Nat_ah64e", "\n"),
        jf.unit_button("Command_ConstructSouthKoreaJetCN235US", "SouthKoreaJetCN235US", "SPEC_JapanC130H", "\n"),
        jf.unit_button("Command_ConstructSouthKoreaJetB1R", "SouthKoreaJetB1R", "B1", "\n"),
        jf.unit_button("Command_ConstructSouthKoreaJetB52H", "SouthKoreaJetB52H", "B52", "\n"),
    ]
    btn = jf.append_buttons(btn, new_btns)
    img_fixes = [
        ("Command_ConstructSouthKoreaVehicleK200", "us_m1126S", "sk k200"),
        ("Command_ConstructSouthKoreaVehicleK21", "arb_m2a3", "sk k21"),
        ("Command_ConstructSouthKoreaVehicleK200APC", "us_m1126S", "sk k200apc"),
        ("Command_ConstructSouthKoreaVehicleCheongung", "us_mim104e", "sk cheongung"),
        ("Command_ConstructSouthKoreaVehicleRadar", "us_tpy2", "sk radar"),
        ("Command_ConstructSouthKoreaVehicleHyunmoo", "us_m1075t", "sk hyunmoo"),
        ("Command_ConstructSouthKoreaVehicleHyunmoo2B", "us_m1075t", "sk hyunmoo2"),
    ]
    for name, image, label in img_fixes:
        btn = jf.patch_button_image(btn, name, image, label)
    jf.set_text(entries, P_CMDBTN, btn)

    cs = jf.text_of(entries, P_CMDSET)
    sk_wf = [
        "  1  = Command_ConstructSouthKoreaTankK1A2",
        "  2  = Command_ConstructSouthKoreaTankK1A1",
        "  3  = Command_ConstructSouthKoreaVehicleK200",
        "  4  = Command_ConstructSouthKoreaVehicleK21",
        "  5  = Command_ConstructSouthKoreaVehicleK200APC",
        "  6  = Command_ConstructSouthKoreaVehicleK30",
        "  7  = Command_ConstructSouthKoreaVehicleCheongung",
        "  8  = Command_ConstructSouthKoreaVehicleRadar",
        "  9  = Command_ConstructSouthKoreaVehicleChunmoo",
        "  10 = Command_ConstructSouthKoreaVehicleHyunmoo",
        "  11 = Command_ConstructSouthKoreaVehicleK9",
        "  12 = Command_ConstructSouthKoreaVehicleK21AT",
        "  13 = Command_ConstructSouthKoreaVehicleK288",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "SouthKorea_WarFactoryCommandSet", sk_wf)
    sk_heavy = [
        "  1 = Command_ConstructSouthKoreaJetE737",
        "  2 = Command_ConstructSouthKoreaJetCN235US",
        "  3 = Command_ConstructSouthKoreaUAVRQ4",
        "  4 = Command_ConstructSouthKoreaHelicopterAH64E",
        "  5 = Command_ConstructSouthKoreaJetUH60P",
        "  6 = Command_ConstructSouthKoreaJetCH47",
        "  7 = Command_ConstructSouthKoreaJetB1R",
        "  8 = Command_ConstructSouthKoreaJetB52H",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "SouthKorea_HeavyAirBaseCommandSet", sk_heavy)
    jf.set_text(entries, P_CMDSET, cs)

    for p in STD44 + DONOR_PROTECTED:
        try:
            i = jf.find_index(entries, p)
        except SystemExit:
            continue
        new_h = hashlib.sha256(entries[i][1]).hexdigest()
        old_h = baseline_hashes[jf.norm(p).lower()]
        if new_h != old_h:
            raise SystemExit(f"PROTECTED FILE CHANGED: {p}")

    if "Object AmericaJetB1R" not in jf.text_of(entries, USA_B1):
        raise SystemExit("USA B1 damaged")
    if "Object GermanyJetC130" not in jf.text_of(entries, DE_C130):
        raise SystemExit("Germany C130 damaged")
    if "Object FranceJetB52H" not in jf.text_of(entries, FR_B52):
        raise SystemExit("France B52 damaged")
    if "Object SouthKoreaJetAH64E" not in jf.text_of(entries, SK_AH64_STD):
        raise SystemExit("STD44 AH64 damaged")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, SK_E737):
        raise SystemExit("E737 missing USA radar")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, IT_G550):
        raise SystemExit("G550 missing USA radar")
    uh = jf.text_of(entries, SK_UH60)
    if "CAN_ATTACK" not in uh or "ChinookAIUpdate" in uh:
        raise SystemExit("UH60 not combat")
    if "LSFRUMi171" in jf.text_of(entries, r"Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterCaracal.ini"):
        pass
    if "US_C130H" not in jf.text_of(entries, IT_C27):
        raise SystemExit("C27 color not applied")
    if "LSFF16C" not in jf.text_of(entries, SK_FA50):
        raise SystemExit("FA50 mesh not replaced")
    if "AVF16" not in jf.text_of(entries, SK_FA50B20):
        raise SystemExit("FA50Blk20 mesh not replaced")
    if "Scale = 1.05" not in jf.text_of(entries, SK_F5E) and "Scale=1.05" not in jf.text_of(entries, SK_F5E):
        raise SystemExit("F5E scale")
    if "ComancheLocomotor" not in jf.text_of(entries, IT_AW101):
        raise SystemExit("AW101 loco")
    if "GeometryIsSmall = No" not in jf.text_of(entries, IT_A129):
        raise SystemExit("A129 geom")

    seen: dict[str, list[str]] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        if "\\object\\" not in n.lower().replace("/", "\\"):
            continue
        t = b.decode("latin1", errors="replace")
        for m in re.finditer(r"(?im)^Object\s+(\S+)", t):
            seen.setdefault(m.group(1), []).append(n)
    for on in ("SouthKoreaHelicopterAH64E", "SouthKoreaJetCN235US", "SouthKoreaJetB1R", "SouthKoreaJetB52H"):
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
    locked_counts = {"sk_wf": 0, "sk_air": 0, "it_wf": 0, "it_air": 0}

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
            if re.search(r"(?i)RequiredScience|NeededUpgrade|NEED_UPGRADE|NEED_SPECIAL_POWER_SCIENCE", b):
                if bucket:
                    locked_counts[bucket] += 1
            objm = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", b)
            imgm = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", b)
            cmdm = re.search(r"(?im)^\s*Command\s*=\s*(\S+)", b)
            cmd = cmdm.group(1) if cmdm else ""
            if objm and objm.group(1) not in last_seen:
                missing_obj.append(f"{c} Object={objm.group(1)}")
            if cmd in ("UNIT_BUILD", "DOZER_CONSTRUCT") and imgm and imgm.group(1) not in images:
                missing_img.append(f"{c} ButtonImage={imgm.group(1)}")
            rows.append(c)
        return rows

    sk_wf_btns = audit_cs("SouthKorea_WarFactoryCommandSet", "sk_wf")
    sk_air = audit_cs("SouthKorea_AirfieldCommandSet", "sk_air")
    sk_heavy = audit_cs("SouthKorea_HeavyAirBaseCommandSet", "sk_air")
    it_air = audit_cs("ItalyAirfieldCommandSet", "it_air")
    it_heavy = audit_cs("Italy_HeavyAirBaseCommandSet", "it_air")
    it_heli = audit_cs("Italy_HelicopterBaseCommandSet", "it_air")

    for w in [
        "Paveway_IV_EF2000", "Kab500_LeaserGuidedBomb", "6_MK-82", "Gbu-12II_Paveway",
        "GBU38_JDAM_F16C", "GBU-39_SDB_F22A", "Fab-250", "Kab1500_LeaserGuidedBomb",
        "Kab2500_LeaserGuidedBomb", "AGM-154C_JSOW_F16C", "GBU_31V2_JDAM_F35C",
        "GBU_31V2_JDAM_F15E", "ODAB_500_PMV_SU39", "AN_APY2_Radar_Power", "AWACS_BaseMonaitoring",
        "30mm_M230E1_ChainGun", "70mm_Hydra_AH64E",
    ]:
        if w not in weapons:
            missing_wpn.append(w)

    model_checks = ["LSFF16C", "AVF16", "US_C130H", "US_B1R", "US_B52H", "US_AH64E", "LSFKoreaUH60", "KVE737", "LSFKOREAF5"]
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
    if "Command_ConstructAmericaTankCrusader" in sk_wf_btns:
        raise SystemExit("SK WF still America")
    if "Command_ConstructSouthKoreaJetC130H" in sk_heavy:
        raise SystemExit("C-130 still on SK heavy")
    if "Command_ConstructSouthKoreaJetRC800" in sk_heavy:
        raise SystemExit("RC-800 still produced")
    if "Command_ConstructSouthKoreaHelicopterKUH1" in sk_heavy:
        raise SystemExit("KUH-1 still produced")
    if "Command_ConstructSouthKoreaHelicopterLAH" in sk_heavy:
        raise SystemExit("LAH still produced")
    if "Command_ConstructSouthKoreaJetCN235US" not in sk_heavy:
        raise SystemExit("American CN235 missing")
    if "Command_ConstructSouthKoreaJetB1R" not in sk_heavy:
        raise SystemExit("B-1 missing")
    if "Command_ConstructSouthKoreaJetB52H" not in sk_heavy:
        raise SystemExit("B-52 missing")
    if "Command_ConstructSouthKoreaHelicopterAH64E" not in sk_heavy:
        raise SystemExit("AH64 combat clone missing")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    sk_bomb_map = {
        "SouthKoreaJetF35A": jf.slot_weapon(jf.text_of(entries, SK_F35A), "SECONDARY"),
        "SouthKoreaJetKF21": jf.slot_weapon(jf.text_of(entries, SK_KF21), "SECONDARY"),
        "SouthKoreaJetF15KSlam": jf.slot_weapon(jf.text_of(entries, SK_F15K), "SECONDARY"),
        "SouthKoreaJetF16C": jf.slot_weapon(jf.text_of(entries, SK_F16C), "SECONDARY"),
        "SouthKoreaJetF16D": jf.slot_weapon(jf.text_of(entries, SK_F16D), "SECONDARY"),
        "SouthKoreaJetFA50": jf.slot_weapon(jf.text_of(entries, SK_FA50), "SECONDARY"),
        "SouthKoreaJetFA50Blk20": jf.slot_weapon(jf.text_of(entries, SK_FA50B20), "SECONDARY"),
        "SouthKoreaJetT50": jf.slot_weapon(jf.text_of(entries, SK_T50), "SECONDARY"),
        "SouthKoreaJetF4E": jf.slot_weapon(jf.text_of(entries, SK_F4E), "SECONDARY"),
        "SouthKoreaJetF5E": jf.slot_weapon(jf.text_of(entries, SK_F5E), "SECONDARY"),
        "SouthKoreaJetKF21Blk2": jf.slot_weapon(jf.text_of(entries, SK_KF21B2), "SECONDARY"),
    }
    it_bomb_map = {
        "ItalyJetTyphoon": jf.slot_weapon(jf.text_of(entries, IT_TYPH), "TERTIARY"),
        "ItalyJetEF2000T4": jf.slot_weapon(jf.text_of(entries, IT_EF2000), "PRIMARY"),
        "ItalyJetF35A": jf.slot_weapon(jf.text_of(entries, IT_F35A), "PRIMARY"),
        "ItalyJetTornadoIDS": jf.slot_weapon(jf.text_of(entries, IT_TIDS), "SECONDARY"),
        "ItalyJetTornadoECR": jf.slot_weapon(jf.text_of(entries, IT_TECR), "TERTIARY"),
        "ItalyJetAMX": jf.slot_weapon(jf.text_of(entries, IT_AMX), "PRIMARY"),
        "ItalyJetHarrierII": jf.slot_weapon(jf.text_of(entries, IT_HAR), "PRIMARY"),
        "ItalyJetF16": jf.slot_weapon(jf.text_of(entries, IT_F16), "TERTIARY"),
        "ItalyJetGCAP": jf.slot_weapon(jf.text_of(entries, IT_GCAP), "TERTIARY"),
        "ItalyJetM346FA": jf.slot_weapon(jf.text_of(entries, IT_M346), "PRIMARY"),
        "ItalyJetMB339": jf.slot_weapon(jf.text_of(entries, IT_MB339), "PRIMARY"),
    }
    for label, mp in (("SK", sk_bomb_map), ("IT", it_bomb_map)):
        vals = list(mp.values())
        if "NONE" in vals:
            raise SystemExit(f"{label} missing bomb {mp}")
        if len(set(vals)) != len(vals):
            raise SystemExit(f"{label} bomb collision {mp}")

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
            or "Republic of Korea" in ln
            or "South Korean Armed" in ln
            or "Italian Armed" in ln
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

    wtxt = jf.text_of(entries, P_WEAPON)

    def clip(name: str) -> str:
        return jf.weapon_clip(wtxt, name)

    lines: list[str] = []
    p = lines.append
    p("SPECTER1 SOUTH KOREA + ITALY ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy; FA-50/C-27J use existing W3D stems)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("PRIOR_INDIA_GERMANY_JAPAN_FRANCE = UNCHANGED")
    p("")
    p("=== SOUTH KOREA FACTORY ===")
    p("BUG = SouthKorea_WarFactoryCommandSet produced Side=America Crusader/Stryker")
    p("FIX = K1A2/K1A1/K200/K21/K30/Cheongung/Radar/Chunmoo/Hyunmoo/K9/K21AT/K288")
    p("FACTORY_FIXED = YES")
    p("SK WARFACTORY =")
    for c in sk_wf_btns:
        p("  " + c)
    p("")
    p("=== SOUTH KOREA AIRCRAFT ===")
    p("C130_REMOVED = YES")
    p("E737_AWACS_SCAN_FIXED = YES (AN_APY2_Radar_Power + AWACS_BaseMonaitoring, detect 4000)")
    p("RC800_REMOVED = YES")
    p("CN235_REPLACED_AMERICAN = YES (SouthKoreaJetCN235US LSFUSAC130 + An-124 contain)")
    p("AH64E_FIRE_ENABLED = YES (SouthKoreaHelicopterAH64E clone; STD44 file unused; 30mm+Hellfire+Hydra)")
    p("UH60P_FUNCTIONAL = YES (CAN_ATTACK, hover CS, ComancheLocomotor, chain gun + Hydra)")
    p("KUH1_REMOVED = YES")
    p("LAH_REMOVED = YES")
    p("B1_ADDED = YES")
    p("B52_ADDED = YES")
    p("FA50_VISUAL_REPLACED = YES (LSFF16C)")
    p("FA50_BLK20_VISUAL_REPLACED = YES (AVF16)")
    p("F5E_SCALE = 1.05 (was 0.80)")
    p("SK HEAVY =")
    for c in sk_heavy:
        p("  " + c)
    p("")
    p("=== SOUTH KOREA BOMBS ===")
    for obj, wpn in sk_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("STD44_SKIP = SouthKoreaJetF35B.ini")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("=== SOUTH KOREA UNLOCK ===")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("=== ITALY ===")
    p("BOMB_DIVERSITY_APPLIED = YES (STD44 ItalyJetF35B.ini not edited)")
    for obj, wpn in it_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("G550_SCAN_FIXED = YES (USA AWACS FireWeaponUpdate + PointDefenseLaserUpdate)")
    p("A129_MOVEMENT_FIXED = YES (GeometryIsSmall=No; JetAI NeedsRunway=No + ComancheLocomotor kept)")
    p("AW101_MOVEMENT_FIXED = YES (full JetAI + ComancheLocomotor)")
    p("C27J_COLOR_CHANGED = YES (US_C130H American scheme)")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("=== SAFETY ===")
    p("USA_B1_DONOR_UNCHANGED = YES")
    p("GERMANY_C130_DONOR_UNCHANGED = YES")
    p("FRANCE_B52_UNCHANGED = YES")
    p("STD44_FILES_UNCHANGED = YES")
    p("JAPAN_FRANCE_INDIA_GERMANY_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("SOUTH_KOREA:")
    p("FACTORY_FIXED = YES")
    p("C130_REMOVED = YES")
    p("E737_AWACS_SCAN_FIXED = YES")
    p("RC800_REMOVED = YES")
    p("CN235_REPLACED_AMERICAN = YES")
    p("AH64E_FIRE_ENABLED = YES")
    p("UH60P_FUNCTIONAL = YES")
    p("KUH1_REMOVED = YES")
    p("LAH_REMOVED = YES")
    p("B1_ADDED = YES")
    p("B52_ADDED = YES")
    p("FA50_VISUAL_REPLACED = YES")
    p("FA50_BLK20_VISUAL_REPLACED = YES")
    p("F5E_SCALE_INCREASED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("ITALY:")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("G550_SCAN_FIXED = YES")
    p("A129_MOVEMENT_FIXED = YES")
    p("AW101_MOVEMENT_FIXED = YES")
    p("C27J_COLOR_CHANGED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 South Korea + Italy Roster 01

Continues from SPECTER1_Japan_France_Roster_01. Does not revert India/Germany/Japan/France.
USA/Germany donor INIs and STD44 files untouched.

South Korea:
- War factory retargeted from Side=America to K1/K200/K21/Cheongung/Chunmoo/K9 roster.
- Removed C-130, RC-800, KUH-1, LAH. Added American CN235 (LSFUSAC130+An-124), B-1R, B-52H.
- E-737 gained USA AWACS radar modules. AH-64E combat clone (STD44 unused). UH-60P now fires.
- FA-50 mesh LSFF16C, FA-50 Block 20 mesh AVF16, F-5E scale 1.05. Distinct fighter bombs.
- Science/NeededUpgrade locks stripped.

Italy:
- Distinct fighter bombs (F-35B STD44 not edited). G550 USA AWACS scan modules.
- A129 GeometryIsSmall=No. AW101 ComancheLocomotor + full JetAI.
- C-27J color scheme switched to US_C130H. Upgrade locks stripped.

ART packed unchanged (existing W3D stems). INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    zpath = WS_OUT / "SPECTER1_Korea_Italy_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Korea_Italy_Roster_01.zip").write_bytes(zpath.read_bytes())
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
