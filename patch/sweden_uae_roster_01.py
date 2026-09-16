#!/usr/bin/env python3
"""SPECTER1 Sweden + UAE roster pass.

Baseline: SPECTER1_Saudi_UK_Roster_01 DATA+ART.
Does not revert prior country work.
Does not modify USA/Iraq donor INIs or STD44 files.
Only Sweden and UAE CommandSets, object INIs, and new clone files.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_SAUDI_UK_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_SAUDI_UK_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "62dd689b387ffbe1b28d7bfd210abd46fada2a960dd31c789ac7deff08a51999"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_SWEDEN_UAE_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_SWEDEN_UAE_ROSTER_01")

P_CMDSET = jf.P_CMDSET
P_CMDBTN = jf.P_CMDBTN
P_WEAPON = jf.P_WEAPON
P_NATIONAL = jf.P_NATIONAL

USA_B1 = r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini"
USA_B2 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"
USA_E3 = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
FR_B21 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB21.ini"
FR_E3 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceAircraftE3.ini"

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

SE_GRIP_A = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetGripenA.ini"
SE_GRIP_E = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetGripenE.ini"
SE_JA37 = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenJA37.ini"
SE_AJS37 = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenAJS37.ini"
SE_SH = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetViggenSH.ini"
SE_DRAKEN = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetDrakenJ35.ini"
SE_LANSEN = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetLansenJ32.ini"
SE_SK60 = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetSK60.ini"
SE_SK60B = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetSK60B.ini"
SE_T4 = r"Data\INI\Object\Specter\Swedish Armed Forces\FixedWings\EF2000_T4.ini"
SE_T4AA = r"Data\INI\Object\Specter\Swedish Armed Forces\FixedWings\EF2000_T4_AA.ini"
SE_T4CAS = r"Data\INI\Object\Specter\Swedish Armed Forces\FixedWings\EF2000_T4_CAS.ini"
SE_E3_NEW = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenAircraftE3USA.ini"
SE_B1_NEW = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetB1R.ini"
SE_B2_NEW = r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetB2A.ini"

UAE_F16E = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16E.ini"
UAE_F16CEGY = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16ECegy.ini"
UAE_F16BLK_STD = r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Airforce\UAE_F16Blk52.ini"
UAE_F16F = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16F.ini"
UAE_M2000_9 = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009.ini"
UAE_M2000_9E = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009E.ini"
UAE_M2000_DAD = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage2000DAD.ini"
UAE_F15EA = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15EA.ini"
UAE_F15E_STD = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15E.ini"
UAE_F15SA = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15SA.ini"
UAE_HAWK = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetHawk102.ini"
UAE_M2000_5 = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20005.ini"
UAE_INF = r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Infantry"
UAE_B21_NEW = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetB21.ini"
UAE_B2_NEW = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetB2A.ini"
UAE_B1_NEW = r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetB1R.ini"

DONOR_PROTECTED = list(jf.DONOR_PROTECTED) + [
    USA_B1, USA_B2, USA_E3, FR_B21, FR_E3,
] + IRAQ_INFANTRY
STD44 = list(jf.STD44)

INF_PAIRS = [
    ("Iraq_RepublicanGuard", "UAE_RepublicanGuard"),
    ("Iraq_SpecialForces", "UAE_SpecialForces"),
    ("Iraq_Worker", "UAE_Worker"),
    ("IraqInfantryMortarGuard", "UAEInfantryMortarGuard"),
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

    # --- Sweden USA AWACS clone (Nato_Systems SwedenJetE3AAWACS unused) ---
    e3 = jf.clone_rename(
        jf.text_of(entries, USA_E3),
        [("AmericaJetE3Visual", "SwedenAircraftE3USA")],
        "America",
        "Sweden",
        "; SPECTER1 Sweden USA AWACS. Donor AmericaJetE3Visual (NOT modified).\n",
    )
    e3 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", e3, count=1)
    e3 = jf.insert_before_geometry(e3, jf.E3_USA_MODULES, "se e3")
    jf.add_file(entries, SE_E3_NEW, e3)

    b1 = jf.clone_rename(
        jf.text_of(entries, USA_B1),
        [("AmericaJetB1R", "SwedenJetB1R")],
        "America",
        "Sweden",
        "; SPECTER1 Sweden B-1R clone. Donor AmericaJetB1R (NOT modified).\n",
    )
    b1, _ = jf.promote_player_upgrade_weaponset(b1, "se b1")
    jf.add_file(entries, SE_B1_NEW, b1)
    b2 = jf.clone_rename(
        jf.text_of(entries, USA_B2),
        [("AmericaJetB2A", "SwedenJetB2A")],
        "America",
        "Sweden",
        "; SPECTER1 Sweden B-2A clone. Donor AmericaJetB2A (NOT modified).\n",
    )
    jf.add_file(entries, SE_B2_NEW, b2)

    # --- Sk60B visual ---
    sk60b = replace_models(
        jf.text_of(entries, SE_SK60B),
        [("AVHawk_D1", "LSFT50")],
        "sk60b mesh",
    )
    if not sk60b.startswith("; SPECTER1"):
        sk60b = "; SPECTER1 Sweden SK60B visual: LSFT50 trainer mesh (was broken Hawk damage mesh). Function kept.\n" + sk60b
    jf.set_text(entries, SE_SK60B, sk60b)

    # --- Sweden fighter bombs ---
    se_bombs = [
        (SE_GRIP_A, "TERTIARY", "SwedenJetGripenA_WpnGun", "GBU_31V2_JDAM_F15E"),
        (SE_GRIP_E, "TERTIARY", "SwedenJetGripenE_WpnGun", "6_MK-82"),
        (SE_JA37, "TERTIARY", "SwedenJetViggenJA37_WpnGun", "Gbu-12II_Paveway"),
        (SE_AJS37, "SECONDARY", "SwedenJetViggenAJS37_WpnBomb", "GBU38_JDAM_F16C"),
        (SE_SH, "SECONDARY", "SwedenJetViggenSH_WpnBomb", "GBU-39_SDB_F22A"),
        (SE_DRAKEN, "TERTIARY", "SwedenJetDrakenJ35_WpnGun", "Kab1500_LeaserGuidedBomb"),
        (SE_LANSEN, "SECONDARY", "SwedenJetLansenJ32_WpnBomb", "Fab-250"),
        (SE_SK60, "TERTIARY", "SwedenJetSK60_WpnBomb", "Kab2500_LeaserGuidedBomb"),
        (SE_SK60B, "TERTIARY", "SwedenJetSK60B_WpnBomb", "AGM-154C_JSOW_F16C"),
    ]
    for path, slot, old, new in se_bombs:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)
    t4aa = jf.text_of(entries, SE_T4AA)
    t4aa, _ = jf.promote_player_upgrade_weaponset(t4aa, "t4aa")
    t4aa = jf.add_tertiary_weapon(t4aa, "Kab500_LeaserGuidedBomb", "t4aa bomb")
    jf.set_text(entries, SE_T4AA, t4aa)
    # EF2000T4 keeps Paveway_IV_EF2000; T4_CAS keeps 4x_GBU54B_500lb_LGB_EF2000.

    # --- UAE American bombers ---
    uae_b21 = jf.clone_rename(
        jf.text_of(entries, FR_B21),
        [("FranceJetB21", "UAEJetB21")],
        "France",
        "UAE",
        "; SPECTER1 UAE B-21 clone. Source FranceJetB21 (AmericaJetB21Clean not modified this pass).\n",
    )
    jf.add_file(entries, UAE_B21_NEW, uae_b21)
    uae_b2 = jf.clone_rename(
        jf.text_of(entries, USA_B2),
        [("AmericaJetB2A", "UAEJetB2A")],
        "America",
        "UAE",
        "; SPECTER1 UAE B-2A clone. Donor AmericaJetB2A (NOT modified).\n",
    )
    jf.add_file(entries, UAE_B2_NEW, uae_b2)
    uae_b1 = jf.clone_rename(
        jf.text_of(entries, USA_B1),
        [("AmericaJetB1R", "UAEJetB1R")],
        "America",
        "UAE",
        "; SPECTER1 UAE B-1R clone. Donor AmericaJetB1R (NOT modified).\n",
    )
    uae_b1, _ = jf.promote_player_upgrade_weaponset(uae_b1, "uae b1")
    jf.add_file(entries, UAE_B1_NEW, uae_b1)

    # --- UAE fighter bombs (skip STD44 F-16 Blk52 and F-15E) ---
    uae_bombs = [
        (UAE_F16E, "TERTIARY", "UAEJetF16E_WpnStrike", "Paveway_IV_EF2000"),
        (UAE_F16CEGY, "SECONDARY", "UAEJetF16ECegy_WpnBomb", "6_MK-82"),
        (UAE_F16F, "TERTIARY", "UAEJetF16F_WpnStrike", "Kab500_LeaserGuidedBomb"),
        (UAE_M2000_9, "TERTIARY", "UAEJetMirage20009_WpnGun", "Gbu-12II_Paveway"),
        (UAE_M2000_9E, "TERTIARY", "UAEJetMirage20009E_WpnStrike", "GBU38_JDAM_F16C"),
        (UAE_M2000_DAD, "SECONDARY", "UAEJetMirage2000DAD_WpnBomb", "GBU-39_SDB_F22A"),
        (UAE_F15EA, "SECONDARY", "UAEJetF15EA_WpnBomb", "Kab1500_LeaserGuidedBomb"),
        (UAE_F15SA, "TERTIARY", "UAEJetF15SA_WpnGun", "Fab-250"),
        (UAE_HAWK, "TERTIARY", "UAEJetHawk102_WpnBomb", "Kab2500_LeaserGuidedBomb"),
        (UAE_M2000_5, "TERTIARY", "UAEJetMirage20005_WpnStrike", "AGM-154C_JSOW_F16C"),
    ]
    for path, slot, old, new in uae_bombs:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)

    # --- UAE infantry = Iraqi package ---
    inf_clones = [
        (IRAQ_RIFLE, UAE_INF + r"\Rifleman.ini", INF_PAIRS),
        (IRAQ_AT, UAE_INF + r"\Antitank.ini", INF_PAIRS),
        (IRAQ_AA, UAE_INF + r"\AntiAir.ini", INF_PAIRS),
        (IRAQ_SNIPER, UAE_INF + r"\HeavySniper.ini", INF_PAIRS),
        (IRAQ_SF, UAE_INF + r"\SpecialForces.ini", INF_PAIRS),
        (IRAQ_WORKER, UAE_INF + r"\UAE_Worker.ini", INF_PAIRS),
        (IRAQ_MORTAR, UAE_INF + r"\MortarTeam.ini", INF_PAIRS),
        (IRAQ_KORNET, UAE_INF + r"\KornetTeam.ini", INF_PAIRS),
        (IRAQ_MG, UAE_INF + r"\Machineguner.ini", INF_PAIRS),
        (IRAQ_ENG, UAE_INF + r"\Enginer.ini", INF_PAIRS),
    ]
    existing_inf = {
        (UAE_INF + r"\Rifleman.ini").lower(),
        (UAE_INF + r"\Antitank.ini").lower(),
        (UAE_INF + r"\AntiAir.ini").lower(),
        (UAE_INF + r"\HeavySniper.ini").lower(),
        (UAE_INF + r"\SpecialForces.ini").lower(),
        (UAE_INF + r"\UAE_Worker.ini").lower(),
    }
    for src, dst, pairs in inf_clones:
        cloned = jf.clone_rename(
            jf.text_of(entries, src),
            pairs,
            "Iraq",
            "UAE",
            "; SPECTER1 UAE infantry clone. Donor " + src.split("\\")[-1] + " (NOT modified).\n",
        )
        if jf.norm(dst).lower() in existing_inf:
            jf.set_text(entries, dst, cloned)
        else:
            jf.add_file(entries, dst, cloned)

    # --- Unlock Sweden + UAE ---
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
            "Swedish Armed" in ln
            or "United Arab Emirates" in ln
            or ln.endswith("NationalGroundForces.ini")
        )
        if not allow:
            continue
        t = b.decode("latin1", errors="replace")
        t2, stripped = jf.unlock_named_objects(t, ("Sweden", "UAE"))
        if t2 != t:
            jf.set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    btn = jf.text_of(entries, P_CMDBTN)
    new_btns = [
        jf.unit_button("Command_ConstructSwedenAircraftE3USA", "SwedenAircraftE3USA", "us_e3g", "\n"),
        jf.unit_button("Command_ConstructSwedenJetB1R", "SwedenJetB1R", "B1", "\n"),
        jf.unit_button("Command_ConstructSwedenJetB2A", "SwedenJetB2A", "B2A", "\n"),
        jf.unit_button("Command_ConstructUAEJetB21", "UAEJetB21", "B21_L", "\n"),
        jf.unit_button("Command_ConstructUAEJetB2A", "UAEJetB2A", "B2A", "\n"),
        jf.unit_button("Command_ConstructUAEJetB1R", "UAEJetB1R", "B1", "\n"),
        jf.unit_button("Command_ConstructUAE_RepublicanGuardMortar", "UAE_RepublicanGuardMortar", "irq_mortar", "\n"),
        jf.unit_button("Command_ConstructUAE_RepublicanGuardKornet", "UAE_RepublicanGuardKornet", "irq_kornet", "\n"),
        jf.unit_button("Command_ConstructUAE_RepublicanGuard_Pkm", "UAE_RepublicanGuard_Pkm", "irq_machinegunner", "\n"),
        jf.unit_button("Command_ConstructUAE_RepublicanGuard_Eng", "UAE_RepublicanGuard_Eng", "irq_eng", "\n"),
    ]
    btn = jf.append_buttons(btn, new_btns)
    img_fixes = [
        ("Command_ConstructSwedenVehicleCV90R", "us_m1126S", "se cv90r"),
        ("Command_ConstructSwedenVehicleCV90", "arb_m2a3", "se cv90"),
        ("Command_ConstructSwedenVehiclePatgb203", "us_m1126S", "se patgb"),
        ("Command_ConstructSwedenVehicleGiraffe", "us_tpy2", "se giraffe"),
        ("Command_ConstructSwedenVehicleRBS15", "us_m1075t", "se rbs15"),
        ("Command_ConstructUAEVehicleBMP3", "arb_m2a3", "uae bmp3"),
        ("Command_ConstructUAEVehicleNimr", "us_m1126S", "uae nimr"),
        ("Command_ConstructUAEVehicleRabdan", "arb_m2a3", "uae rabdan"),
        ("Command_ConstructUAEVehiclePatria", "us_m1126S", "uae patria"),
        ("Command_ConstructUAEVehiclePatriot", "us_mim104e", "uae patriot"),
        ("Command_ConstructUAEVehicleRadar", "us_tpy2", "uae radar"),
        ("Command_ConstructUAEVehicleThunder", "us_m1075t", "uae thunder"),
        ("Command_ConstructUAE_RepublicanGuard_AKMS", "irq_rifleman", "uae akms img"),
        ("Command_ConstructUAE_RepublicanGuard_RPG7", "irq_antitank", "uae rpg img"),
        ("Command_ConstructUAE_RepublicanGuardIgla", "irq_igla", "uae igla img"),
        ("Command_ConstructUAE_SpecialForces_Akms", "irq_specialforce", "uae sf img"),
        ("Command_ConstructUAE_RepublicanGuard_TBK14", "irq_sniper", "uae tbk img"),
        ("Command_ConstructUAE_Worker", "irq_eng", "uae worker img"),
    ]
    for name, image, label in img_fixes:
        btn = jf.patch_button_image(btn, name, image, label)
    jf.set_text(entries, P_CMDBTN, btn)

    cs = jf.text_of(entries, P_CMDSET)
    se_wf = [
        "  1  = Command_ConstructSwedenTankStrv122",
        "  2  = Command_ConstructSwedenTankStrv121",
        "  3  = Command_ConstructSwedenVehicleCV90R",
        "  4  = Command_ConstructSwedenVehicleCV90",
        "  5  = Command_ConstructSwedenVehiclePatgb203",
        "  6  = Command_ConstructSwedenVehicleLvkv90",
        "  7  = Command_ConstructSwedenVehicleGiraffe",
        "  8  = Command_ConstructSwedenVehiclePULS",
        "  9  = Command_ConstructSwedenVehicleRBS15",
        "  10 = Command_ConstructSwedenVehicleArcher",
        "  11 = Command_ConstructSwedenVehicleCV90AT",
        "  12 = Command_ConstructSwedenVehicleBgbv120",
        "  13 = Command_ConstructSwedenTankStrv122B",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "SwedenWarfactoryCommandSet", se_wf)
    se_heavy = [
        "  1 = Command_ConstructSwedenAircraftE3USA",
        "  2 = Command_ConstructSwedenHelicopterCH47F",
        "  3 = Command_ConstructSwedenHelicopterUH60",
        "  4 = Command_ConstructSwedenHelicopterAH64E",
        "  5 = Command_ConstructSwedenJetB1R",
        "  6 = Command_ConstructSwedenJetB2A",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "Sweden_HeavyAirBaseCommandSet", se_heavy)
    uae_wf = [
        "  1  = Command_ConstructUAETankLeclerc",
        "  2  = Command_ConstructUAEVehicleBMP3",
        "  3  = Command_ConstructUAEVehicleNimr",
        "  4  = Command_ConstructUAEVehicleRabdan",
        "  5  = Command_ConstructUAEVehiclePatria",
        "  6  = Command_ConstructUAEVehiclePantsir",
        "  7  = Command_ConstructUAEVehiclePatriot",
        "  8  = Command_ConstructUAEVehicleRadar",
        "  9  = Command_ConstructUAEVehicleHIMARS",
        "  10 = Command_ConstructUAEVehicleThunder",
        "  11 = Command_ConstructUAEVehicleG6",
        "  12 = Command_ConstructUAEVehicleBMP3AT",
        "  13 = Command_ConstructUAEVehicleLeclercARV",
        "  14 = Command_Sell",
    ]
    for wf_name in (
        "UAE_WarFactoryCommandSet",
        "UAE_WarFactoryCommandSet1",
        "UAE_WarFactoryCommandSet2",
        "UAE_WarFactoryCommandSet3",
    ):
        cs = jf.replace_commandset(cs, wf_name, uae_wf)
    uae_heavy = [
        "  1 = Command_ConstructUAE_IL-76",
        "  2 = Command_ConstructUAE_Mi-8T",
        "  3 = Command_ConstructUAEJetB21",
        "  4 = Command_ConstructUAEJetB2A",
        "  5 = Command_ConstructUAEJetB1R",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "UAE_HeavyAirBaseCommandSet", uae_heavy)
    uae_barracks = [
        "  1 = Command_ConstructUAE_RepublicanGuard_AKMS",
        "  2 = Command_ConstructUAE_RepublicanGuard_RPG7",
        "  3 = Command_ConstructUAE_RepublicanGuardMortar",
        "  4 = Command_ConstructUAE_RepublicanGuardKornet",
        "  5 = Command_ConstructUAE_RepublicanGuard_Pkm",
        "  6 = Command_ConstructUAE_RepublicanGuard_TBK14",
        "  7 = Command_ConstructUAE_RepublicanGuard_Eng",
        "  8 = Command_ConstructUAE_SpecialForces_Akms",
        "  9 = Command_ConstructUAE_RepublicanGuardIgla",
        "  11 = Command_UpgradeGLARebelCaptureBuilding",
        "  12 = Command_Upgrade_RGD5",
        "  13 = Command_Upgrade_Rpg29",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "UAE_BarracksCommandSet", uae_barracks)
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

    if "Object AmericaJetE3Visual" not in jf.text_of(entries, USA_E3):
        raise SystemExit("USA E3 damaged")
    if "Object AmericaJetB2A" not in jf.text_of(entries, USA_B2):
        raise SystemExit("USA B2 damaged")
    if "Object AmericaJetB1R" not in jf.text_of(entries, USA_B1):
        raise SystemExit("USA B1 damaged")
    if "Object Iraq_RepublicanGuard_AKMS" not in jf.text_of(entries, IRAQ_RIFLE):
        raise SystemExit("Iraq rifle damaged")
    if "Object UAE_F16Blk52" not in jf.text_of(entries, UAE_F16BLK_STD):
        raise SystemExit("STD44 UAE F16 damaged")
    if "Object UAEJetF15E" not in jf.text_of(entries, UAE_F15E_STD):
        raise SystemExit("STD44 UAE F15E damaged")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, SE_E3_NEW):
        raise SystemExit("Sweden E3 missing USA radar")
    sk60b_chk = jf.text_of(entries, SE_SK60B)
    if not re.search(r"(?im)^\s*Model\s*=\s*LSFT50\b", sk60b_chk):
        raise SystemExit("SK60B mesh not replaced")
    if re.search(r"(?im)^\s*Model\s*=\s*AVHawk", sk60b_chk):
        raise SystemExit("SK60B still AVHawk model")

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
        "SwedenAircraftE3USA", "SwedenJetB1R", "SwedenJetB2A",
        "UAEJetB21", "UAEJetB2A", "UAEJetB1R",
        "UAE_RepublicanGuard_AKMS", "UAE_RepublicanGuardMortar",
        "UAE_RepublicanGuardKornet", "UAE_RepublicanGuard_Pkm", "UAE_RepublicanGuard_Eng",
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
    locked_counts = {"se_wf": 0, "se_air": 0, "uae_wf": 0, "uae_air": 0, "uae_bar": 0}

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

    se_wf_btns = audit_cs("SwedenWarfactoryCommandSet", "se_wf")
    se_air = audit_cs("SwedenAirfieldCommandSet", "se_air")
    se_heavy = audit_cs("Sweden_HeavyAirBaseCommandSet", "se_air")
    uae_wf_btns = audit_cs("UAE_WarFactoryCommandSet", "uae_wf")
    uae_air = audit_cs("UAE_AirfieldCommandSet", "uae_air")
    uae_heavy = audit_cs("UAE_HeavyAirBaseCommandSet", "uae_air")
    uae_bar = audit_cs("UAE_BarracksCommandSet", "uae_bar")

    for w in [
        "GBU_31V2_JDAM_F15E", "6_MK-82", "Gbu-12II_Paveway", "GBU38_JDAM_F16C", "GBU-39_SDB_F22A",
        "Kab1500_LeaserGuidedBomb", "Fab-250", "Kab2500_LeaserGuidedBomb", "AGM-154C_JSOW_F16C",
        "Paveway_IV_EF2000", "Kab500_LeaserGuidedBomb", "4x_GBU54B_500lb_LGB_EF2000",
        "2x_AGM88G_AARGM-ER_F16CJ", "AN_APY2_Radar_Power", "AWACS_BaseMonaitoring",
    ]:
        if w not in weapons:
            missing_wpn.append(w)

    model_checks = ["LSFT50", "E3", "US_E3G", "AVB3bmbr", "US_B1R", "AVB21_A", "AGMZRT501"]
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
    if any("Nato" in c for c in se_wf_btns):
        raise SystemExit("Sweden WF still Nato")
    if any("Egypt" in c or "GLA" in c or "Arb_" in c or "Arab_" in c for c in uae_wf_btns):
        raise SystemExit("UAE WF still Egypt/GLA")
    if "Command_ConstructSwedenAircraftE3USA" not in se_heavy:
        raise SystemExit("USA AWACS missing")
    if "Command_ConstructSwedenJetE3AAWACS" in se_heavy:
        raise SystemExit("old Sweden AWACS still produced")
    if "Command_ConstructSwedenJetB1R" not in se_heavy:
        raise SystemExit("Sweden B-1 missing")
    if "Command_ConstructSwedenJetB2A" not in se_heavy:
        raise SystemExit("Sweden B-2 missing")
    if "Command_ConstructUAEJetB21" not in uae_heavy:
        raise SystemExit("UAE B-21 missing")
    if "Command_ConstructUAEJetB2A" not in uae_heavy:
        raise SystemExit("UAE B-2 missing")
    if "Command_ConstructUAEJetB1R" not in uae_heavy:
        raise SystemExit("UAE B-1 missing")
    if "Command_ConstructUAE_RepublicanGuardMortar" not in uae_bar:
        raise SystemExit("UAE Iraqi mortar missing")
    if "Command_ConstructUAE_EliteSSG" in uae_bar:
        raise SystemExit("EliteSSG still in UAE barracks")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    se_bomb_map = {
        "SwedenJetGripenA": jf.slot_weapon(jf.text_of(entries, SE_GRIP_A), "TERTIARY"),
        "SwedenJetEF2000T4": jf.slot_weapon(jf.text_of(entries, SE_T4), "PRIMARY"),
        "SwedenJetEF2000T4_AA": jf.slot_weapon(jf.text_of(entries, SE_T4AA), "TERTIARY"),
        "SwedenJetGripenE": jf.slot_weapon(jf.text_of(entries, SE_GRIP_E), "TERTIARY"),
        "SwedenJetEF2000T4_CAS": jf.slot_weapon(jf.text_of(entries, SE_T4CAS), "SECONDARY"),
        "SwedenJetViggenJA37": jf.slot_weapon(jf.text_of(entries, SE_JA37), "TERTIARY"),
        "SwedenJetViggenAJS37": jf.slot_weapon(jf.text_of(entries, SE_AJS37), "SECONDARY"),
        "SwedenJetViggenSH": jf.slot_weapon(jf.text_of(entries, SE_SH), "SECONDARY"),
        "SwedenJetDrakenJ35": jf.slot_weapon(jf.text_of(entries, SE_DRAKEN), "TERTIARY"),
        "SwedenJetLansenJ32": jf.slot_weapon(jf.text_of(entries, SE_LANSEN), "SECONDARY"),
        "SwedenJetSK60": jf.slot_weapon(jf.text_of(entries, SE_SK60), "TERTIARY"),
        "SwedenJetSK60B": jf.slot_weapon(jf.text_of(entries, SE_SK60B), "TERTIARY"),
    }
    uae_bomb_map = {
        "UAEJetF16E": jf.slot_weapon(jf.text_of(entries, UAE_F16E), "TERTIARY"),
        "UAEJetF16ECegy": jf.slot_weapon(jf.text_of(entries, UAE_F16CEGY), "SECONDARY"),
        "UAE_F16Blk52": jf.slot_weapon(jf.text_of(entries, UAE_F16BLK_STD), "PRIMARY"),
        "UAEJetF16F": jf.slot_weapon(jf.text_of(entries, UAE_F16F), "TERTIARY"),
        "UAEJetMirage20009": jf.slot_weapon(jf.text_of(entries, UAE_M2000_9), "TERTIARY"),
        "UAEJetMirage20009E": jf.slot_weapon(jf.text_of(entries, UAE_M2000_9E), "TERTIARY"),
        "UAEJetMirage2000DAD": jf.slot_weapon(jf.text_of(entries, UAE_M2000_DAD), "SECONDARY"),
        "UAEJetF15EA": jf.slot_weapon(jf.text_of(entries, UAE_F15EA), "SECONDARY"),
        "UAEJetF15E": jf.slot_weapon(jf.text_of(entries, UAE_F15E_STD), "PRIMARY"),
        "UAEJetF15SA": jf.slot_weapon(jf.text_of(entries, UAE_F15SA), "TERTIARY"),
        "UAEJetHawk102": jf.slot_weapon(jf.text_of(entries, UAE_HAWK), "TERTIARY"),
        "UAEJetMirage20005": jf.slot_weapon(jf.text_of(entries, UAE_M2000_5), "TERTIARY"),
    }
    for label, mp in (("SE", se_bomb_map), ("UAE", uae_bomb_map)):
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
            or "Swedish Armed" in ln
            or "United Arab Emirates" in ln
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
    p("SPECTER1 SWEDEN + UAE ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy; SK60B uses existing LSFT50)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("PRIOR_COUNTRIES_UNCHANGED = YES")
    p("")
    p("=== SWEDEN ===")
    p("AWACS_REPLACED_WITH_USA = YES (SwedenAircraftE3USA clone of AmericaJetE3Visual)")
    p("B1_ADDED = YES")
    p("B2_ADDED = YES")
    p("SK60B_VISUAL_CHANGED = YES (LSFT50; was AVHawk_D1)")
    p("WARFACTORY_FIXED = YES (Nato Side mismatch -> Strv122/CV90/Archer native)")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("SE WARFACTORY =")
    for c in se_wf_btns:
        p("  " + c)
    p("SE HEAVY =")
    for c in se_heavy:
        p("  " + c)
    p("SE BOMBS =")
    for obj, wpn in se_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("")
    p("=== UAE ===")
    p("INFANTRY_REPLACED_WITH_IRAQ = YES (cloned Side=UAE; Iraq donors unchanged)")
    p("B21_ADDED = YES")
    p("B2_ADDED = YES")
    p("B1_ADDED = YES")
    p("WARFACTORY_FIXED = YES (Egypt/GLA -> Leclerc/BMP3/Nimr/Patriot/HIMARS native)")
    p("BOMB_DIVERSITY_APPLIED = YES (STD44 UAE_F16Blk52.ini and UAEJetF15E.ini not edited)")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("UAE WARFACTORY =")
    for c in uae_wf_btns:
        p("  " + c)
    p("UAE HEAVY =")
    for c in uae_heavy:
        p("  " + c)
    p("UAE BARRACKS =")
    for c in uae_bar:
        p("  " + c)
    p("UAE BOMBS =")
    for obj, wpn in uae_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("")
    p("=== SAFETY ===")
    p("USA_E3_DONOR_UNCHANGED = YES")
    p("USA_B1_DONOR_UNCHANGED = YES")
    p("USA_B2_DONOR_UNCHANGED = YES")
    p("IRAQ_INFANTRY_DONORS_UNCHANGED = YES")
    p("STD44_FILES_UNCHANGED = YES")
    p("SAUDI_UK_KOREA_ITALY_JAPAN_FRANCE_INDIA_GERMANY_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("SWEDEN:")
    p("AWACS_REPLACED_WITH_USA = YES")
    p("B1_ADDED = YES")
    p("B2_ADDED = YES")
    p("SK60B_VISUAL_CHANGED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("WARFACTORY_FIXED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("UAE:")
    p("INFANTRY_REPLACED_WITH_IRAQ = YES")
    p("B21_ADDED = YES")
    p("B2_ADDED = YES")
    p("B1_ADDED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("WARFACTORY_FIXED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Sweden + UAE Roster 01

Continues from SPECTER1_Saudi_UK_Roster_01. Does not revert prior country work.
USA/Iraq donor INIs and STD44 files untouched.

Sweden:
- War factory retargeted from Nato Side-mismatch units to Strv122/CV90/Archer native roster.
- Swedish AWACS replaced with AmericaJetE3Visual clone (USA scan modules). B-1R and B-2A added.
- SK60B visual LSFT50 (was AVHawk_D1). Distinct fighter bombs. Upgrade locks stripped.

UAE:
- War factory retargeted from Egypt/GLA to Leclerc/BMP3/Nimr/Patriot/HIMARS native roster.
- Barracks uses cloned Iraqi Republican Guard package (Side=UAE).
- B-21, B-2A, B-1R added. Distinct fighter bombs (STD44 F-16 Blk52 / F-15E not edited).
- Upgrade locks stripped.

ART packed unchanged (existing W3D stems). INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    zpath = WS_OUT / "SPECTER1_Sweden_UAE_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Sweden_UAE_Roster_01.zip").write_bytes(zpath.read_bytes())
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
