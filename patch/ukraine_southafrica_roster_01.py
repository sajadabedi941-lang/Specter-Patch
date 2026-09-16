#!/usr/bin/env python3
"""SPECTER1 Ukraine + South Africa roster pass.

Baseline: SPECTER1_Nato_Libya_Roster_01 DATA+ART.
Does not revert prior country work (including NATO/Libya).
Does not modify USA/Iraq donor INIs.
Only Ukraine and South Africa CommandSets, object INIs, and new clone files.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_NATO_LIBYA_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_NATO_LIBYA_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "2bd4506ed9264c04b620cb602e6f743a5c520cacf58965afb991d18e40ce90dc"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_UKRAINE_SOUTHAFRICA_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_UKRAINE_SOUTHAFRICA_ROSTER_01")

P_CMDSET = jf.P_CMDSET
P_CMDBTN = jf.P_CMDBTN
P_WEAPON = jf.P_WEAPON
P_NATIONAL = jf.P_NATIONAL

USA_B1 = r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini"
USA_B2 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"
USA_E3 = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
USA_V22 = r"Data\INI\Object\Specter\United States Of America\AmericaJetV22Visual.ini"
USA_C17 = r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini"
FR_B21 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB21.ini"
FR_B52 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB52H.ini"

IRAQ_RIFLE = r"Data\INI\Object\Specter\Iraq Army\Infantry\Rifleman.ini"
IRAQ_AT = r"Data\INI\Object\Specter\Iraq Army\Infantry\Antitank.ini"
IRAQ_AA = r"Data\INI\Object\Specter\Iraq Army\Infantry\AntiAir.ini"
IRAQ_MORTAR = r"Data\INI\Object\Specter\Iraq Army\Infantry\MortarTeam.ini"
IRAQ_KORNET = r"Data\INI\Object\Specter\Iraq Army\Infantry\KornetTeam.ini"
IRAQ_MG = r"Data\INI\Object\Specter\Iraq Army\Infantry\Machineguner.ini"
IRAQ_ENG = r"Data\INI\Object\Specter\Iraq Army\Infantry\Enginer.ini"
IRAQ_SF = r"Data\INI\Object\Specter\Iraq Army\Infantry\SpecialForces.ini"
IRAQ_SNIPER = r"Data\INI\Object\Specter\Iraq Army\Infantry\HeavySniper.ini"
IRAQ_WORKER = r"Data\INI\Object\Specter\Iraq Army\Infantry\Iraq_Worker.ini"
IRAQ_INFANTRY = [
    IRAQ_RIFLE, IRAQ_AT, IRAQ_AA, IRAQ_MORTAR, IRAQ_KORNET, IRAQ_MG, IRAQ_ENG, IRAQ_SF, IRAQ_SNIPER, IRAQ_WORKER,
]

UA_MIG29 = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig29.ini"
UA_MIG29MU1 = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig29MU1.ini"
UA_SU27 = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27.ini"
UA_SU27UB = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27UB.ini"
UA_F16AM = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetF16AM.ini"
UA_F16D = r"Data\INI\Object\Specter\Ukrainian Armed Forces\FixedWings\F16DBlk52.ini"
UA_M2000 = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMirage2000.ini"
UA_SU24M = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu24M.ini"
UA_SU24MR = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu24MR.ini"
UA_SU25 = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu25.ini"
UA_SU25M1 = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu25M1.ini"
UA_MIG21 = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetMig21.ini"
UA_E3_OLD = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineAircraftE3AWACS.ini"
UA_E3_NEW = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineAircraftE3USA.ini"
UA_B1_NEW = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetB1R.ini"
UA_V22_NEW = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetV22.ini"
UA_B21_NEW = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetB21.ini"

SA_F1BQ = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfrica_MirageF1-Bq.ini"
SA_IIICZ = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetMirageIIICZ.ini"
SA_CHEET_C = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahC.ini"
SA_CHEET_D = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahD.ini"
SA_CHEET_E = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetCheetahE.ini"
SA_GRIP_C = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenC.ini"
SA_GRIP_D = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenD.ini"
SA_GRIP_E = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetGripenE.ini"
SA_HAWK120 = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetHawk120.ini"
SA_HAWK127 = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetHawk127.ini"
SA_IMPALA = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetImpala.ini"
SA_BUCC = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetBuccaneer.ini"
SA_MIG29 = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfrica_Mig-29A.ini"
SA_SU25 = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfrica_Su-25K.ini"
SA_F16 = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfrica_F16Blk52.ini"
SA_IL76 = r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetIL76.ini"
SA_INF = r"Data\INI\Object\Specter\South African National Defence Force\Infantry"

DONOR_PROTECTED = list(jf.DONOR_PROTECTED) + [
    USA_B1, USA_B2, USA_E3, USA_V22, USA_C17, FR_B21, FR_B52,
] + IRAQ_INFANTRY
STD44 = list(jf.STD44)
UA_SA_STD44 = [
    UA_SU27,
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\UH60.ini",
    SA_IL76,
]
BYTE_LOCKED = [p for p in STD44 + DONOR_PROTECTED if jf.norm(p).lower() not in {jf.norm(x).lower() for x in UA_SA_STD44}]

INF_PAIRS = [
    ("Iraq_RepublicanGuard", "SouthAfrica_RepublicanGuard"),
    ("Iraq_SpecialForces", "SouthAfrica_SpecialForces"),
    ("Iraq_Worker", "SouthAfrica_Worker"),
    ("IraqInfantryMortarGuard", "SouthAfricaInfantryMortarGuard"),
]


def replace_models(text: str, pairs: list[tuple[str, str]], label: str) -> str:
    out = text
    for old, new in pairs:
        out2, n = re.subn(rf"(?im)^(\s*Model\s*=\s*){re.escape(old)}\b", rf"\1{new}", out)
        if n < 1:
            raise SystemExit(f"{label}: model {old} not found")
        out = out2
    return out


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

    # --- Ukraine USA aircraft clones ---
    e3 = jf.clone_rename(
        jf.text_of(entries, USA_E3),
        [("AmericaJetE3Visual", "UkraineAircraftE3USA")],
        "America",
        "Ukraine",
        "; SPECTER1 Ukraine USA AWACS. Donor AmericaJetE3Visual (NOT modified).\n",
    )
    e3 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", e3, count=1)
    e3 = jf.insert_before_geometry(e3, jf.E3_USA_MODULES, "ua e3")
    jf.add_file(entries, UA_E3_NEW, e3)

    b1 = jf.clone_rename(
        jf.text_of(entries, USA_B1),
        [("AmericaJetB1R", "UkraineJetB1R")],
        "America",
        "Ukraine",
        "; SPECTER1 Ukraine B-1R clone. Donor AmericaJetB1R (NOT modified).\n",
    )
    b1, _ = jf.promote_player_upgrade_weaponset(b1, "ua b1")
    jf.add_file(entries, UA_B1_NEW, b1)

    v22 = jf.clone_rename(
        jf.text_of(entries, USA_V22),
        [("AmericaJetV22Visual", "UkraineJetV22")],
        "America",
        "Ukraine",
        "; SPECTER1 Ukraine V-22 clone. Donor AmericaJetV22Visual (NOT modified).\n",
    )
    jf.add_file(entries, UA_V22_NEW, v22)

    b21 = jf.clone_rename(
        jf.text_of(entries, FR_B21),
        [("FranceJetB21", "UkraineJetB21")],
        "France",
        "Ukraine",
        "; SPECTER1 Ukraine B-21 clone. Source FranceJetB21 (AmericaJetB21Clean not modified).\n",
    )
    jf.add_file(entries, UA_B21_NEW, b21)

    # --- Ukraine fighter bombs (skip STD44 Su-27) ---
    ua_bombs = [
        (UA_MIG29, "TERTIARY", "UkraineJetMig29_WpnGun", "GBU_31V2_JDAM_F15E"),
        (UA_MIG29MU1, "TERTIARY", "UkraineJetMig29MU1_WpnStrike", "6_MK-82"),
        (UA_SU27UB, "TERTIARY", "UkraineJetSu27UB_WpnStrike", "Gbu-12II_Paveway"),
        (UA_F16AM, "TERTIARY", "UkraineJetF16AM_WpnStrike", "GBU38_JDAM_F16C"),
        (UA_M2000, "TERTIARY", "UkraineJetMirage2000_WpnStrike", "GBU-39_SDB_F22A"),
        (UA_SU24M, "SECONDARY", "UkraineJetSu24M_WpnBomb", "Kab1500_LeaserGuidedBomb"),
        (UA_SU24MR, "SECONDARY", "UkraineJetSu24MR_WpnBomb", "Kab500_LeaserGuidedBomb"),
        (UA_SU25, "TERTIARY", "UkraineJetSu25_WpnBomb", "Paveway_IV_EF2000"),
        (UA_SU25M1, "TERTIARY", "UkraineJetSu25M1_WpnBomb", "Kab2500_LeaserGuidedBomb"),
        (UA_MIG21, "TERTIARY", "Kab500_LeaserGuidedBomb", "AGM-154C_JSOW_F16C"),
    ]
    for path, slot, old, new in ua_bombs:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)

    # --- South Africa Hawk visuals ---
    hawk120 = replace_models(
        jf.text_of(entries, SA_HAWK120),
        [("UVVampire_D", "LSFT50d"), ("UVVampire", "LSFT50")],
        "hawk120 mesh",
    )
    if not hawk120.startswith("; SPECTER1"):
        hawk120 = "; SPECTER1 South Africa Hawk 120 visual: LSFT50 (was UVVampire). Function kept.\n" + hawk120
    jf.set_text(entries, SA_HAWK120, hawk120)
    hawk127 = replace_models(
        jf.text_of(entries, SA_HAWK127),
        [("AVHawk_D", "LSFKoreaF5d"), ("AVHawk", "LSFKoreaF5")],
        "hawk127 mesh",
    )
    if not hawk127.startswith("; SPECTER1"):
        hawk127 = "; SPECTER1 South Africa Hawk 127 visual: LSFKoreaF5 (was AVHawk). Function kept.\n" + hawk127
    jf.set_text(entries, SA_HAWK127, hawk127)

    # --- South Africa fighter bombs ---
    sa_replace = [
        (SA_IIICZ, "TERTIARY", "SouthAfricaJetMirageIIICZ_WpnGun", "6_MK-82"),
        (SA_CHEET_C, "TERTIARY", "SouthAfricaJetCheetahC_WpnGun", "Gbu-12II_Paveway"),
        (SA_CHEET_D, "SECONDARY", "SouthAfricaJetCheetahD_WpnBomb", "GBU38_JDAM_F16C"),
        (SA_CHEET_E, "TERTIARY", "SouthAfricaJetCheetahE_WpnStrike", "GBU-39_SDB_F22A"),
        (SA_GRIP_C, "TERTIARY", "SouthAfricaJetGripenC_WpnStrike", "Kab1500_LeaserGuidedBomb"),
        (SA_GRIP_D, "TERTIARY", "SouthAfricaJetGripenD_WpnStrike", "Paveway_IV_EF2000"),
        (SA_GRIP_E, "TERTIARY", "SouthAfricaJetGripenE_WpnGun", "Kab500_LeaserGuidedBomb"),
        (SA_HAWK120, "TERTIARY", "SouthAfricaJetHawk120_WpnBomb", "Kab2500_LeaserGuidedBomb"),
        (SA_HAWK127, "TERTIARY", "SouthAfricaJetHawk127_WpnBomb", "AGM-154C_JSOW_F16C"),
        (SA_IMPALA, "TERTIARY", "SouthAfricaJetImpala_WpnBomb", "4x_GBU54B_500lb_LGB_EF2000"),
    ]
    for path, slot, old, new in sa_replace:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)
    sa_tertiary = [
        (SA_F1BQ, "GBU_31V2_JDAM_F15E", "sa f1bq bomb"),
        (SA_MIG29, "Specter_Weapon_SU34MF_Bomb6", "sa mig29 bomb"),
        (SA_F16, "GBU_31V2_JDAM_F35C", "sa f16 bomb"),
    ]
    for path, wpn, label in sa_tertiary:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.add_tertiary_weapon(t, wpn, label)
        jf.set_text(entries, path, t)

    # --- SA infantry = Iraqi package ---
    inf_clones = [
        (IRAQ_RIFLE, SA_INF + r"\Rifleman.ini", INF_PAIRS),
        (IRAQ_AT, SA_INF + r"\Antitank.ini", INF_PAIRS),
        (IRAQ_AA, SA_INF + r"\AntiAir.ini", INF_PAIRS),
        (IRAQ_SNIPER, SA_INF + r"\HeavySniper.ini", INF_PAIRS),
        (IRAQ_SF, SA_INF + r"\SpecialForces.ini", INF_PAIRS),
        (IRAQ_WORKER, SA_INF + r"\SouthAfrica_Worker.ini", INF_PAIRS),
        (IRAQ_MORTAR, SA_INF + r"\MortarTeam.ini", INF_PAIRS),
        (IRAQ_KORNET, SA_INF + r"\KornetTeam.ini", INF_PAIRS),
        (IRAQ_MG, SA_INF + r"\Machineguner.ini", INF_PAIRS),
        (IRAQ_ENG, SA_INF + r"\Enginer.ini", INF_PAIRS),
    ]
    existing_inf = {
        (SA_INF + r"\Rifleman.ini").lower(),
        (SA_INF + r"\Antitank.ini").lower(),
        (SA_INF + r"\AntiAir.ini").lower(),
        (SA_INF + r"\HeavySniper.ini").lower(),
        (SA_INF + r"\SpecialForces.ini").lower(),
        (SA_INF + r"\SouthAfrica_Worker.ini").lower(),
    }
    for src, dst, pairs in inf_clones:
        cloned = jf.clone_rename(
            jf.text_of(entries, src),
            pairs,
            "Iraq",
            "SouthAfrica",
            "; SPECTER1 South Africa infantry clone. Donor " + src.split("\\")[-1] + " (NOT modified).\n",
        )
        if jf.norm(dst).lower() in existing_inf:
            jf.set_text(entries, dst, cloned)
        else:
            jf.add_file(entries, dst, cloned)

    # --- Unlock Ukraine + South Africa ---
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
            "Ukrainian Armed" in ln
            or "South African National" in ln
            or ln.endswith("NationalGroundForces.ini")
        )
        if not allow:
            continue
        t = b.decode("latin1", errors="replace")
        t2, stripped = jf.unlock_named_objects(t, ("Ukraine", "SouthAfrica"))
        if t2 != t:
            jf.set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    btn = jf.text_of(entries, P_CMDBTN)
    new_btns = [
        jf.unit_button("Command_ConstructUkraineAircraftE3USA", "UkraineAircraftE3USA", "us_e3g", "\n"),
        jf.unit_button("Command_ConstructUkraineJetB1R", "UkraineJetB1R", "B1", "\n"),
        jf.unit_button("Command_ConstructUkraineJetV22", "UkraineJetV22", "V22", "\n"),
        jf.unit_button("Command_ConstructUkraineJetB21", "UkraineJetB21", "B21_L", "\n"),
        jf.unit_button("Command_ConstructUkraineVehicleM142ATACMS", "UkraineVehicleM142ATACMS", "Nat_m142at", "\n"),
        jf.unit_button("Command_ConstructUkraineJetMig29", "UkraineJetMig29", "SPEC_UkraineJetMig29", "\n"),
        jf.unit_button("Command_ConstructUkraineJetMig29MU1", "UkraineJetMig29MU1", "SPEC_UkraineJetMig29MU1", "\n"),
        jf.unit_button("Command_ConstructUkraineJetSu27", "UkraineJetSu27", "SPEC_UkraineJetSu27", "\n"),
        jf.unit_button("Command_ConstructUkraineJetSu27UB", "UkraineJetSu27UB", "SPEC_UkraineJetSu27UB", "\n"),
        jf.unit_button("Command_ConstructUkraineJetF16AM", "UkraineJetF16AM", "SPEC_UkraineJetF16AM", "\n"),
        jf.unit_button("Command_ConstructUkraineJetMirage2000", "UkraineJetMirage2000", "SPEC_UkraineJetMirage2000", "\n"),
        jf.unit_button("Command_ConstructUkraineJetSu24M", "UkraineJetSu24M", "SPEC_UkraineJetSu24M", "\n"),
        jf.unit_button("Command_ConstructUkraineJetSu24MR", "UkraineJetSu24MR", "SPEC_UkraineJetSu24MR", "\n"),
        jf.unit_button("Command_ConstructUkraineJetSu25", "UkraineJetSu25", "SPEC_UkraineJetSu25", "\n"),
        jf.unit_button("Command_ConstructUkraineJetSu25M1", "UkraineJetSu25M1", "SPEC_UkraineJetSu25M1", "\n"),
        jf.unit_button("Command_ConstructUkraineJetMig21", "UkraineJetMig21", "SPEC_UkraineJetMig21", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetMirageIIICZ", "SouthAfricaJetMirageIIICZ", "SPEC_SouthAfricaJetMirageIIICZ", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetCheetahC", "SouthAfricaJetCheetahC", "SPEC_SouthAfricaJetCheetahC", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetCheetahD", "SouthAfricaJetCheetahD", "SPEC_SouthAfricaJetCheetahD", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetCheetahE", "SouthAfricaJetCheetahE", "SPEC_SouthAfricaJetCheetahE", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetGripenC", "SouthAfricaJetGripenC", "SPEC_SouthAfricaJetGripenC", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetGripenD", "SouthAfricaJetGripenD", "SPEC_SouthAfricaJetGripenD", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetGripenE", "SouthAfricaJetGripenE", "SPEC_SouthAfricaJetGripenE", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetHawk120", "SouthAfricaJetHawk120", "SPEC_SouthAfricaJetHawk120", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetHawk127", "SouthAfricaJetHawk127", "SPEC_SouthAfricaJetHawk127", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetImpala", "SouthAfricaJetImpala", "SPEC_SouthAfricaJetImpala", "\n"),
        jf.unit_button("Command_ConstructSouthAfricaJetBuccaneer", "SouthAfricaJetBuccaneer", "SPEC_SouthAfricaJetBuccaneer", "\n"),
        jf.unit_button("Command_ConstructSouthAfrica_RepublicanGuardMortar", "SouthAfrica_RepublicanGuardMortar", "irq_mortar", "\n"),
        jf.unit_button("Command_ConstructSouthAfrica_RepublicanGuardKornet", "SouthAfrica_RepublicanGuardKornet", "irq_kornet", "\n"),
        jf.unit_button("Command_ConstructSouthAfrica_RepublicanGuard_Pkm", "SouthAfrica_RepublicanGuard_Pkm", "irq_machinegunner", "\n"),
        jf.unit_button("Command_ConstructSouthAfrica_RepublicanGuard_Eng", "SouthAfrica_RepublicanGuard_Eng", "irq_eng", "\n"),
    ]
    btn = jf.append_buttons(btn, new_btns)
    img_fixes = [
        ("Command_ConstructSouthAfricaVehicleRatel", "arb_m2a3", "sa ratel"),
        ("Command_ConstructSouthAfricaVehicleCasspir", "us_m1126S", "sa casspir"),
        ("Command_ConstructSouthAfricaVehicleCactus", "us_mim104e", "sa cactus"),
        ("Command_ConstructSouthAfricaVehicleThutlwa", "us_tpy2", "sa thutlwa"),
        ("Command_ConstructSouthAfrica_RepublicanGuard_AKMS", "irq_rifleman", "sa akms img"),
        ("Command_ConstructSouthAfrica_RepublicanGuard_RPG7", "irq_antitank", "sa rpg img"),
        ("Command_ConstructSouthAfrica_RepublicanGuardIgla", "irq_igla", "sa igla img"),
        ("Command_ConstructSouthAfrica_SpecialForces_Akms", "irq_specialforce", "sa sf img"),
        ("Command_ConstructSouthAfrica_RepublicanGuard_TBK14", "irq_sniper", "sa tbk img"),
        ("Command_ConstructSouthAfrica_Worker", "irq_eng", "sa worker img"),
    ]
    for name, image, label in img_fixes:
        btn = jf.patch_button_image(btn, name, image, label)
    jf.set_text(entries, P_CMDBTN, btn)

    cs = jf.text_of(entries, P_CMDSET)
    ua_wf = [
        "  1  = Command_ConstructUkraineTankLeopard2A7Plus",
        "  2  = Command_ConstructUkraineTankPuma",
        "  3  = Command_ConstructUkraineVehicleCortaleMK3",
        "  4  = Command_ConstructUkraineVehicleVBCI",
        "  5  = Command_ConstructUkraineVehicleM142",
        "  6  = Command_ConstructUkraineVehicleCaesar",
        "  7  = Command_ConstructUkraineVehicleCentauroB2",
        "  8  = Command_ConstructUkraineVehicleIRIST",
        "  9  = Command_ConstructUkraineVehicleTRML4D",
        "  10 = Command_ConstructUkraineVehicleM142ATACMS",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "UkraineWarfactoryCommandSet", ua_wf)
    ua_heavy = [
        "  1 = Command_ConstructUkraineAircraftE3USA",
        "  2 = Command_ConstructUkraineHelicopterCH47F",
        "  3 = Command_ConstructUkraineHelicopterUH60",
        "  4 = Command_ConstructUkraineHelicopterAH64E",
        "  5 = Command_ConstructUkraineJetB1R",
        "  6 = Command_ConstructUkraineJetV22",
        "  7 = Command_ConstructUkraineJetB21",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "Ukraine_HeavyAirBaseCommandSet", ua_heavy)
    sa_wf = [
        "  1  = Command_ConstructSouthAfricaTankOlifant",
        "  2  = Command_ConstructSouthAfricaTankOlifant1B",
        "  3  = Command_ConstructSouthAfricaVehicleRooikat",
        "  4  = Command_ConstructSouthAfricaVehicleRatel",
        "  5  = Command_ConstructSouthAfricaVehicleCasspir",
        "  6  = Command_ConstructSouthAfricaVehicleYstervark",
        "  7  = Command_ConstructSouthAfricaVehicleCactus",
        "  8  = Command_ConstructSouthAfricaVehicleThutlwa",
        "  9  = Command_ConstructSouthAfricaVehicleValkiri",
        "  10 = Command_ConstructSouthAfricaVehicleBateleur",
        "  11 = Command_ConstructSouthAfricaVehicleG6",
        "  12 = Command_ConstructSouthAfricaVehicleZT3",
        "  13 = Command_ConstructSouthAfricaVehicleARV",
        "  14 = Command_Sell",
    ]
    for wf_name in (
        "SouthAfrica_WarFactoryCommandSet",
        "SouthAfrica_WarFactoryCommandSet1",
        "SouthAfrica_WarFactoryCommandSet2",
        "SouthAfrica_WarFactoryCommandSet3",
    ):
        cs = jf.replace_commandset(cs, wf_name, sa_wf)
    sa_barracks = [
        "  1 = Command_ConstructSouthAfrica_RepublicanGuard_AKMS",
        "  2 = Command_ConstructSouthAfrica_RepublicanGuard_RPG7",
        "  3 = Command_ConstructSouthAfrica_RepublicanGuardMortar",
        "  4 = Command_ConstructSouthAfrica_RepublicanGuardKornet",
        "  5 = Command_ConstructSouthAfrica_RepublicanGuard_Pkm",
        "  6 = Command_ConstructSouthAfrica_RepublicanGuard_TBK14",
        "  7 = Command_ConstructSouthAfrica_RepublicanGuard_Eng",
        "  8 = Command_ConstructSouthAfrica_SpecialForces_Akms",
        "  9 = Command_ConstructSouthAfrica_RepublicanGuardIgla",
        "  11 = Command_UpgradeGLARebelCaptureBuilding",
        "  12 = Command_Upgrade_RGD5",
        "  13 = Command_Upgrade_Rpg29",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "SouthAfrica_BarracksCommandSet", sa_barracks)
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

    if "Object AmericaJetE3Visual" not in jf.text_of(entries, USA_E3):
        raise SystemExit("USA E3 damaged")
    if "Object AmericaJetB1R" not in jf.text_of(entries, USA_B1):
        raise SystemExit("USA B1 damaged")
    if "Object AmericaJetV22Visual" not in jf.text_of(entries, USA_V22):
        raise SystemExit("USA V22 damaged")
    if "Object FranceJetB21" not in jf.text_of(entries, FR_B21):
        raise SystemExit("France B21 damaged")
    if "Object Iraq_RepublicanGuard_AKMS" not in jf.text_of(entries, IRAQ_RIFLE):
        raise SystemExit("Iraq rifle damaged")
    if "Object UkraineJetSu27" not in jf.text_of(entries, UA_SU27):
        raise SystemExit("STD44 Ukraine Su27 missing object")
    if "Object SouthAfricaJetIL76" not in jf.text_of(entries, SA_IL76):
        raise SystemExit("STD44 SA IL76 damaged")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, UA_E3_NEW):
        raise SystemExit("Ukraine E3 missing USA radar")
    if not re.search(r"(?im)^\s*Side\s*=\s*Ukraine\b", jf.text_of(entries, UA_E3_NEW)):
        raise SystemExit("Ukraine E3 side not Ukraine")
    hawk120_chk = jf.text_of(entries, SA_HAWK120)
    if not re.search(r"(?im)^\s*Model\s*=\s*LSFT50\b", hawk120_chk):
        raise SystemExit("Hawk120 mesh not replaced")
    if re.search(r"(?im)^\s*Model\s*=\s*UVVampire", hawk120_chk):
        raise SystemExit("Hawk120 still UVVampire")
    hawk127_chk = jf.text_of(entries, SA_HAWK127)
    if not re.search(r"(?im)^\s*Model\s*=\s*LSFKoreaF5\b", hawk127_chk):
        raise SystemExit("Hawk127 mesh not replaced")
    if re.search(r"(?im)^\s*Model\s*=\s*AVHawk", hawk127_chk):
        raise SystemExit("Hawk127 still AVHawk")

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
        "UkraineAircraftE3USA", "UkraineJetB1R", "UkraineJetV22", "UkraineJetB21",
        "SouthAfrica_RepublicanGuard_AKMS", "SouthAfrica_RepublicanGuardMortar",
        "SouthAfrica_RepublicanGuardKornet", "SouthAfrica_RepublicanGuard_Pkm",
        "SouthAfrica_RepublicanGuard_Eng",
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
    locked_counts = {"ua_wf": 0, "ua_air": 0, "sa_wf": 0, "sa_air": 0, "sa_bar": 0}

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

    ua_wf_btns = audit_cs("UkraineWarfactoryCommandSet", "ua_wf")
    ua_air = audit_cs("UkraineAirfieldCommandSet", "ua_air")
    ua_heavy = audit_cs("Ukraine_HeavyAirBaseCommandSet", "ua_air")
    sa_wf_btns = audit_cs("SouthAfrica_WarFactoryCommandSet", "sa_wf")
    sa_air = audit_cs("SouthAfrica_AirfieldCommandSet", "sa_air")
    sa_bar = audit_cs("SouthAfrica_BarracksCommandSet", "sa_bar")

    for w in [
        "GBU_31V2_JDAM_F15E", "6_MK-82", "Gbu-12II_Paveway", "GBU38_JDAM_F16C", "GBU-39_SDB_F22A",
        "Kab1500_LeaserGuidedBomb", "Kab500_LeaserGuidedBomb", "Paveway_IV_EF2000",
        "Kab2500_LeaserGuidedBomb", "AGM-154C_JSOW_F16C", "4x_GBU54B_500lb_LGB_EF2000",
        "4x_Fab500_SU34", "2x_AGM88G_AARGM-ER_F16CJ", "Fab-250", "Specter_Weapon_SU34MF_Bomb6",
        "GBU_31V2_JDAM_F35C", "AN_APY2_Radar_Power", "AWACS_BaseMonaitoring",
    ]:
        if w not in weapons:
            missing_wpn.append(w)

    model_checks = ["LSFT50", "LSFT50d", "LSFKoreaF5", "LSFKoreaF5d", "E3", "US_B1R", "AVOsprey", "AVB21_A"]
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
    if any("Nato" in c for c in ua_wf_btns):
        raise SystemExit("Ukraine WF still Nato")
    if any("Iraq" in c for c in sa_wf_btns):
        raise SystemExit("South Africa WF still Iraq")
    if "Command_ConstructUkraineAircraftE3USA" not in ua_heavy:
        raise SystemExit("USA AWACS missing")
    if "Command_ConstructUkraineAircraftE3AWACS" in ua_heavy:
        raise SystemExit("old Ukraine AWACS still produced")
    if "Command_ConstructUkraineJetB1R" not in ua_heavy:
        raise SystemExit("Ukraine B-1 missing")
    if "Command_ConstructUkraineJetV22" not in ua_heavy:
        raise SystemExit("Ukraine V-22 missing")
    if "Command_ConstructUkraineJetB21" not in ua_heavy:
        raise SystemExit("Ukraine B-21 missing")
    if "Command_ConstructUkraineJetMig29" not in ua_air:
        raise SystemExit("Ukraine Mig29 button missing")
    if "Command_ConstructSouthAfricaJetHawk120" not in sa_air:
        raise SystemExit("SA Hawk120 button missing")
    if "Command_ConstructSouthAfrica_RepublicanGuardMortar" not in sa_bar:
        raise SystemExit("SA Iraqi mortar missing")
    if "Command_ConstructSouthAfrica_EliteSSG" in sa_bar:
        raise SystemExit("EliteSSG still in SA barracks")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    ua_bomb_map = {
        "UkraineJetMig29": jf.slot_weapon(jf.text_of(entries, UA_MIG29), "TERTIARY"),
        "UkraineJetMig29MU1": jf.slot_weapon(jf.text_of(entries, UA_MIG29MU1), "TERTIARY"),
        "UkraineJetSu27": jf.slot_weapon(jf.text_of(entries, UA_SU27), "SECONDARY"),
        "UkraineJetSu27UB": jf.slot_weapon(jf.text_of(entries, UA_SU27UB), "TERTIARY"),
        "UkraineJetF16AM": jf.slot_weapon(jf.text_of(entries, UA_F16AM), "TERTIARY"),
        "UkraineJetF16DBlk52": jf.slot_weapon(jf.text_of(entries, UA_F16D), "PRIMARY"),
        "UkraineJetMirage2000": jf.slot_weapon(jf.text_of(entries, UA_M2000), "TERTIARY"),
        "UkraineJetSu24M": jf.slot_weapon(jf.text_of(entries, UA_SU24M), "SECONDARY"),
        "UkraineJetSu24MR": jf.slot_weapon(jf.text_of(entries, UA_SU24MR), "SECONDARY"),
        "UkraineJetSu25": jf.slot_weapon(jf.text_of(entries, UA_SU25), "TERTIARY"),
        "UkraineJetSu25M1": jf.slot_weapon(jf.text_of(entries, UA_SU25M1), "TERTIARY"),
        "UkraineJetMig21": jf.slot_weapon(jf.text_of(entries, UA_MIG21), "TERTIARY"),
    }
    sa_bomb_map = {
        "SouthAfrica_MirageF1_Bq": jf.slot_weapon(jf.text_of(entries, SA_F1BQ), "TERTIARY"),
        "SouthAfricaJetMirageIIICZ": jf.slot_weapon(jf.text_of(entries, SA_IIICZ), "TERTIARY"),
        "SouthAfricaJetCheetahC": jf.slot_weapon(jf.text_of(entries, SA_CHEET_C), "TERTIARY"),
        "SouthAfricaJetCheetahD": jf.slot_weapon(jf.text_of(entries, SA_CHEET_D), "SECONDARY"),
        "SouthAfricaJetCheetahE": jf.slot_weapon(jf.text_of(entries, SA_CHEET_E), "TERTIARY"),
        "SouthAfricaJetGripenC": jf.slot_weapon(jf.text_of(entries, SA_GRIP_C), "TERTIARY"),
        "SouthAfricaJetGripenD": jf.slot_weapon(jf.text_of(entries, SA_GRIP_D), "TERTIARY"),
        "SouthAfricaJetGripenE": jf.slot_weapon(jf.text_of(entries, SA_GRIP_E), "TERTIARY"),
        "SouthAfricaJetHawk120": jf.slot_weapon(jf.text_of(entries, SA_HAWK120), "TERTIARY"),
        "SouthAfricaJetHawk127": jf.slot_weapon(jf.text_of(entries, SA_HAWK127), "TERTIARY"),
        "SouthAfricaJetImpala": jf.slot_weapon(jf.text_of(entries, SA_IMPALA), "TERTIARY"),
        "SouthAfricaJetBuccaneer": jf.slot_weapon(jf.text_of(entries, SA_BUCC), "SECONDARY"),
        "SouthAfrica_Mig-29A": jf.slot_weapon(jf.text_of(entries, SA_MIG29), "TERTIARY"),
        "SouthAfrica_Su-25K": jf.slot_weapon(jf.text_of(entries, SA_SU25), "PRIMARY"),
        "SouthAfrica_F16Blk52": jf.slot_weapon(jf.text_of(entries, SA_F16), "TERTIARY"),
    }
    for label, mp in (("UA", ua_bomb_map), ("SA", sa_bomb_map)):
        vals = list(mp.values())
        if "NONE" in vals:
            raise SystemExit(f"{label} missing bomb {mp}")
        if len(set(vals)) != len(vals):
            raise SystemExit(f"{label} bomb collision {mp}")

    e3_txt = jf.text_of(entries, UA_E3_NEW)
    if "StealthDetectorUpdate" not in e3_txt:
        raise SystemExit("Ukraine E3 missing StealthDetectorUpdate")
    v22_txt = jf.text_of(entries, UA_V22_NEW)
    if "AVOsprey" not in v22_txt or "CAN_ATTACK" not in v22_txt:
        raise SystemExit("Ukraine V22 donor data lost")

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
            or "Ukrainian Armed" in ln
            or "South African National" in ln
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
    p("SPECTER1 UKRAINE + SOUTH AFRICA ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy; Hawk 120/127 use existing LSFT50/LSFKoreaF5)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("PRIOR_COUNTRIES_UNCHANGED = YES")
    p("NATO_LIBYA_IN_BASELINE = YES")
    p("")
    p("=== UKRAINE ===")
    p("WARFACTORY_FIXED = YES (Nato Side mismatch -> Ukraine-side Leopard/Puma/M142 native copies)")
    p("AWACS_REPLACED_WITH_USA = YES (UkraineAircraftE3USA clone of AmericaJetE3Visual)")
    p("B1_ADDED = YES")
    p("V22_ADDED = YES")
    p("B21_ADDED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("UA WARFACTORY =")
    for c in ua_wf_btns:
        p("  " + c)
    p("UA HEAVY =")
    for c in ua_heavy:
        p("  " + c)
    p("UA BOMBS =")
    for obj, wpn in ua_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("")
    p("=== SOUTH AFRICA ===")
    p("INFANTRY_REPLACED_WITH_IRAQ = YES (cloned Side=SouthAfrica; Iraq donors unchanged)")
    p("HAWK120_VISUAL_CHANGED = YES (LSFT50; was UVVampire)")
    p("HAWK127_VISUAL_CHANGED = YES (LSFKoreaF5; was AVHawk)")
    p("WARFACTORY_FIXED = YES (Iraq Side mismatch -> Olifant/Rooikat/Ratel native)")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("SA WARFACTORY =")
    for c in sa_wf_btns:
        p("  " + c)
    p("SA BARRACKS =")
    for c in sa_bar:
        p("  " + c)
    p("SA BOMBS =")
    for obj, wpn in sa_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("")
    p("=== SAFETY ===")
    p("USA_E3_DONOR_UNCHANGED = YES")
    p("USA_B1_DONOR_UNCHANGED = YES")
    p("USA_V22_DONOR_UNCHANGED = YES")
    p("FRANCE_B21_DONOR_UNCHANGED = YES")
    p("IRAQ_INFANTRY_DONORS_UNCHANGED = YES")
    p("NATO_LIBYA_SWEDEN_UAE_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("UKRAINE:")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("WARFACTORY_FIXED = YES")
    p("B1_ADDED = YES")
    p("V22_ADDED = YES")
    p("B21_ADDED = YES")
    p("AWACS_USA_FUNCTIONALITY = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("SOUTH AFRICA:")
    p("INFANTRY_REPLACED_WITH_IRAQ = YES")
    p("HAWK120_VISUAL_CHANGED = YES")
    p("HAWK127_VISUAL_CHANGED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Ukraine + South Africa Roster 01

Continues from SPECTER1_Nato_Libya_Roster_01. Does not revert prior country work.
USA/Iraq donor INIs untouched. NATO/Libya remain as packed in the baseline.

Ukraine:
- War factory retargeted from Nato Side-mismatch units to Ukraine-side Leopard/Puma/M142 copies.
- AWACS replaced with AmericaJetE3Visual clone. B-1R, V-22, B-21 added.
- Missing fighter construct buttons added. Distinct fighter bombs. Upgrade locks stripped.

South Africa:
- Barracks uses cloned Iraqi Republican Guard package (Side=SouthAfrica). EliteSSG removed.
- Hawk 120 visual LSFT50 (was UVVampire). Hawk 127 visual LSFKoreaF5 (was AVHawk).
- War factory retargeted from Iraq to Olifant/Rooikat/Ratel native roster.
- Distinct fighter bombs. Upgrade locks stripped.

ART packed unchanged (existing W3D stems). INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    zpath = WS_OUT / "SPECTER1_Ukraine_SouthAfrica_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Ukraine_SouthAfrica_Roster_01.zip").write_bytes(zpath.read_bytes())
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
