#!/usr/bin/env python3
"""SPECTER1 Saudi Arabia + United Kingdom roster pass.

Baseline: SPECTER1_Korea_Italy_Roster_01 DATA+ART.
Does not revert India/Germany/Japan/France/Korea/Italy work.
Does not modify USA/Iraq/Russia donor INIs or STD44 files.
Only Saudi and UK CommandSets, object INIs, and new clone files.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_KOREA_ITALY_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_KOREA_ITALY_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "10fc0f05365c93eb724f60354d832a9d1c01b431c2c03c9606d08b255ae035e9"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_SAUDI_UK_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_SAUDI_UK_ROSTER_01")

P_CMDSET = jf.P_CMDSET
P_CMDBTN = jf.P_CMDBTN
P_WEAPON = jf.P_WEAPON
P_NATIONAL = jf.P_NATIONAL

USA_B1 = r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini"
USA_UH60 = r"Data\INI\Object\Specter\United States Of America\Airforce\UH60.ini"
USA_CH47 = r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini"
USA_AH64E = r"Data\INI\Object\Specter\United States Of America\Airforce\AH64E.ini"
USA_RQ180 = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaDroneRQ180.ini"
USA_MQ4 = r"Data\INI\Object\Specter\United States Of America\Drones\Mq4.ini"
FR_B52 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB52H.ini"
FR_B21 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB21.ini"
SK_AH64_NEW = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaHelicopterAH64E.ini"
RUS_SU34 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\SU34M.ini"
RUS_MIG31K = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\MIG31K.ini"

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

SA_HAWK = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetHawk65.ini"
SA_F15S = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15S.ini"
SA_F15SA = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15SA.ini"
SA_F15C = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15C.ini"
SA_F15EX = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15EX.ini"
SA_TYPH = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoon.ini"
SA_TYPH3 = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoonT3.ini"
SA_TIDS = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoIDS.ini"
SA_TADV = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoADV.ini"
SA_TECR = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoECR.ini"
SA_LIGHT = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetLightning.ini"
SA_F5E = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF5E.ini"
SA_WF = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_WarFactory.ini"

SA_INF = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Infantry"
SA_B52_NEW = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetB52H.ini"
SA_B1_NEW = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetB1R.ini"
SA_B21_NEW = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetB21.ini"
SA_AH64_NEW = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiHelicopterAH64E.ini"
SA_UH60_NEW = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiHelicopterUH60.ini"
SA_RQ180_NEW = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Drones\SaudiArabiaDroneRQ180.ini"
SA_MQ4_NEW = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Drones\SaudiArabiaDroneMQ4.ini"

UK_F35B_STD = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetF35B.ini"
UK_CH47_STD = r"Data\INI\Object\Specter\British Armed Forces\Rotary\CH47F.ini"
UK_AH64E = r"Data\INI\Object\Specter\British Armed Forces\Rotary\AH64E.ini"
UK_MERLIN = r"Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterMerlin.ini"
UK_CHINOOK = r"Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterChinook.ini"
UK_E7 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftE7.ini"
UK_A400 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetA400M.ini"
UK_C17 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetC17.ini"
UK_TECR = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftTornadoECR.ini"
UK_FGR2 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetPhantomFGR2.ini"
UK_FGR4 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTyphoonFGR4.ini"
UK_T3 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTyphoonT3.ini"
UK_TEMPEST = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTempest.ini"
UK_TF3 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTornadoF3.ini"
UK_TGR4 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTornadoGR4.ini"
UK_HAR = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetHarrierGR9.ini"
UK_SEA = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetSeaHarrierFA2.ini"
UK_FG1 = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetPhantomFG1.ini"
UK_JAG = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetJaguarGR3.ini"
UK_LIGHT = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetLightningF6.ini"
UK_HAWK = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetHawk200.ini"

IRAQ_INFANTRY = [
    IRAQ_RIFLE, IRAQ_AT, IRAQ_AA, IRAQ_MORTAR, IRAQ_KORNET, IRAQ_MG, IRAQ_ENG, IRAQ_SF, IRAQ_SNIPER, IRAQ_WORKER,
]

DONOR_PROTECTED = list(jf.DONOR_PROTECTED) + [
    USA_B1, USA_UH60, USA_CH47, USA_AH64E, USA_RQ180, USA_MQ4,
    FR_B52, FR_B21, SK_AH64_NEW, RUS_SU34, RUS_MIG31K,
] + IRAQ_INFANTRY
STD44 = list(jf.STD44)

AN124_CONTAIN = """  Behavior = TransportContain ModuleTag_An124Cargo
    Slots                 = 64
    DamagePercentToUnits  = 100%
    AllowInsideKindOf     = INFANTRY VEHICLE
    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE
    ExitDelay             = 100
    NumberOfExitPaths     = 1
  End
"""

JETAI_HELI = """  Behavior = JetAIUpdate ModuleTag_09ai
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

INF_PAIRS = [
    ("Iraq_RepublicanGuard", "SaudiArabia_RepublicanGuard"),
    ("Iraq_SpecialForces", "SaudiArabia_SpecialForces"),
    ("Iraq_Worker", "SaudiArabia_Worker"),
    ("IraqInfantryMortarGuard", "SaudiArabiaInfantryMortarGuard"),
]


def replace_models(text: str, pairs: list[tuple[str, str]], label: str) -> str:
    out = text
    for old, new in pairs:
        out2, n = re.subn(rf"(?im)^(\s*Model\s*=\s*){re.escape(old)}\b", rf"\1{new}", out)
        if n < 1:
            raise SystemExit(f"{label}: model {old} not found")
        out = out2
    return out


def replace_ai_block(text: str, new_block: str, label: str) -> str:
    nl = jf.file_nl(text)
    text2, n = re.subn(
        r"(?im)^  Behavior = (?:ChinookAIUpdate|JetAIUpdate) \S+\r?\n(?:.*\r?\n)*?^  End\r?\n",
        jf.to_nl(new_block, nl),
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{label}: AI block replace n={n}")
    return text2


def set_normal_loco(text: str, loco: str, label: str) -> str:
    text2, n = re.subn(r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+", rf"\1{loco}", text, count=1)
    if n != 1:
        raise SystemExit(f"{label}: locomotor n={n}")
    return text2


def fix_ah64e(text: str) -> str:
    nl = jf.file_nl(text)
    if not text.startswith("; SPECTER1"):
        text = "; SPECTER1 UK AH-64E movement: ComancheLocomotor + JetAI takeoff fields. 30mm chain gun.\n" + text
    text, n = re.subn(r"GenericHeliGunnerSight", "30mm_M230E1_ChainGun", text, count=1)
    if n != 1:
        raise SystemExit("uk ah64e gun")
    text = set_normal_loco(text, "ComancheLocomotor", "uk ah64e")
    if "TakeoffPause" not in text:
        text, n = re.subn(
            r"(?im)^(  Behavior = JetAIUpdate \S+\r?\n)",
            r"\1    OutOfAmmoDamagePerSecond = 0%" + nl
            + "    TakeoffDistForMaxLift = 0%" + nl
            + "    TakeoffPause = 500" + nl
            + "    ParkingOffset = 3" + nl
            + "    ReturnToBaseIdleTime = 10000" + nl,
            text,
            count=1,
        )
        if n != 1:
            raise SystemExit("uk ah64e jetai fields")
    return text


def fix_merlin(text: str) -> str:
    if not text.startswith("; SPECTER1"):
        text = "; SPECTER1 UK Merlin movement: GeometryIsSmall=No (was Yes).\n" + text
    text, n = re.subn(r"(?im)^(\s*GeometryIsSmall\s*=\s*)Yes\b", r"\1No", text, count=1)
    if n != 1:
        raise SystemExit("uk merlin geometry")
    if "ComancheLocomotor" not in text or "NeedsRunway = No" not in text:
        raise SystemExit("uk merlin still broken")
    return text


def fix_chinook_us(text: str) -> str:
    nl = jf.file_nl(text)
    if not text.startswith("; SPECTER1"):
        text = "; SPECTER1 UK American Chinook. Donor AmericaVehicleChinook (NOT modified). JetAI NeedsRunway=No + ComancheLocomotor, TransportContain kept.\n" + text
    text = replace_ai_block(text, JETAI_HELI.replace("AutoAcquireEnemiesWhenIdle = Yes", "AutoAcquireEnemiesWhenIdle = No"), "uk chinook")
    text = set_normal_loco(text, "ComancheLocomotor", "uk chinook")
    if "TransportContain" not in text:
        raise SystemExit("uk chinook lost cargo")
    if "NeedsRunway = No" not in text:
        raise SystemExit("uk chinook runway")
    return text


def combatize_uh60(text: str) -> str:
    nl = jf.file_nl(text)
    if not text.startswith("; SPECTER1"):
        text = "; SPECTER1 Saudi UH-60 combat clone. Donor AmericaHelicopterUH60 (NOT modified).\n" + text
    text, n = re.subn(r"(?im)^(\s*CommandSet\s*=\s*)\S+", r"\1GenericAttackHelicopterHoverCommandSet", text, count=1)
    if n != 1:
        raise SystemExit("sa uh60 commandset")
    text, n = re.subn(
        r"(?im)^(\s*KindOf\s*=\s*).*$",
        r"\1PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT PRODUCED_AT_HELIPAD",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("sa uh60 kindof")
    if "30mm_M230E1_ChainGun" not in text:
        text2, n = re.subn(
            r"(?im)^(\s*CommandSet\s*=\s*GenericAttackHelicopterHoverCommandSet[^\n]*\n)",
            r"\1" + jf.to_nl(UH60_WEAPONS, nl),
            text,
            count=1,
        )
        if n != 1:
            raise SystemExit("sa uh60 weapons")
        text = text2
    text = replace_ai_block(text, JETAI_HELI, "sa uh60")
    text = set_normal_loco(text, "ComancheLocomotor", "sa uh60")
    if "CAN_ATTACK" not in text or "NeedsRunway = No" not in text:
        raise SystemExit("sa uh60 still broken")
    return text


def patch_recon_drone(text: str, label: str) -> str:
    text, _ = jf.strip_unit_science_locks(text)
    text, n = re.subn(
        r"(?im)^(\s*KindOf\s*=\s*).*$",
        r"\1PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT DRONE",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{label} kindof")
    text, n = re.subn(
        r"(?im)^(\s*CommandSet\s*=\s*)C17GlobalMasterCommandSet\b",
        r"\1GenericTacticalBomberCommandSet",
        text,
        count=1,
    )
    text = re.sub(r"(?im)^(\s*NeedsRunway\s*=\s*)Yes\b", r"\1No", text, count=1)
    text = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", text, count=1)
    text = jf.insert_before_geometry(text, jf.E3_USA_MODULES, label)
    if "AN_APY2_Radar_Power" not in text:
        raise SystemExit(f"{label} missing scan")
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

    # --- Saudi Hawk 65 visual (keep function/weapons) ---
    hawk = replace_models(
        jf.text_of(entries, SA_HAWK),
        [("AVHawk_D", "LSFKoreaF5d"), ("AVHawk", "LSFKoreaF5")],
        "hawk65 mesh",
    )
    if not hawk.startswith("; SPECTER1"):
        hawk = "; SPECTER1 Saudi Hawk 65 visual: LSFKoreaF5 (was AVHawk). Weapons/function unchanged.\n" + hawk
    jf.set_text(entries, SA_HAWK, hawk)

    # --- Saudi fighter bomb diversity ---
    sa_bombs = [
        (SA_F15SA, "SECONDARY", "SaudiJetF15SA_WpnBomb", "GBU_31V2_JDAM_F15E"),
        (SA_F15C, "TERTIARY", "SaudiJetF15C_WpnGun", "Gbu-12II_Paveway"),
        (SA_F15EX, "TERTIARY", "SaudiJetF15EX_WpnStrike", "Kab500_LeaserGuidedBomb"),
        (SA_TYPH, "TERTIARY", "SaudiJetTyphoon_WpnGun", "6_MK-82"),
        (SA_TYPH3, "TERTIARY", "SaudiJetTyphoonT3_WpnStrike", "Paveway_IV_EF2000"),
        (SA_TIDS, "SECONDARY", "SaudiJetTornadoIDS_WpnBomb", "GBU38_JDAM_F16C"),
        (SA_TADV, "TERTIARY", "SaudiJetTornadoADV_WpnGun", "GBU-39_SDB_F22A"),
        (SA_TECR, "SECONDARY", "SaudiJetTornadoECR_WpnBomb", "Kab1500_LeaserGuidedBomb"),
        (SA_HAWK, "TERTIARY", "SaudiJetHawk65_WpnBomb", "Fab-250"),
        (SA_LIGHT, "TERTIARY", "SaudiJetLightning_WpnGun", "Kab2500_LeaserGuidedBomb"),
        (SA_F5E, "TERTIARY", "SaudiJetF5E_WpnBomb", "AGM-154C_JSOW_F16C"),
    ]
    for path, slot, old, new in sa_bombs:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)
    # F-15S keeps Saudi_Weapon_GBU_F15S as its unique GBU.

    # --- Saudi American bombers ---
    b52 = jf.clone_rename(
        jf.text_of(entries, FR_B52),
        [("FranceJetB52H", "SaudiJetB52H")],
        "France",
        "SaudiArabia",
        "; SPECTER1 Saudi B-52H clone. Source FranceJetB52H (USA_System.ini not modified this pass).\n",
    )
    jf.add_file(entries, SA_B52_NEW, b52)
    b1 = jf.clone_rename(
        jf.text_of(entries, USA_B1),
        [("AmericaJetB1R", "SaudiJetB1R")],
        "America",
        "SaudiArabia",
        "; SPECTER1 Saudi B-1R clone. Donor AmericaJetB1R (NOT modified).\n",
    )
    b1, _ = jf.promote_player_upgrade_weaponset(b1, "sa b1")
    jf.add_file(entries, SA_B1_NEW, b1)
    b21 = jf.clone_rename(
        jf.text_of(entries, FR_B21),
        [("FranceJetB21", "SaudiJetB21")],
        "France",
        "SaudiArabia",
        "; SPECTER1 Saudi B-21 clone. Source FranceJetB21 (AmericaJetB21Clean not modified this pass).\n",
    )
    jf.add_file(entries, SA_B21_NEW, b21)

    # --- Saudi American combat helis ---
    ah = jf.clone_rename(
        jf.text_of(entries, SK_AH64_NEW),
        [("SouthKoreaHelicopterAH64E", "SaudiHelicopterAH64E")],
        "SouthKorea",
        "SaudiArabia",
        "; SPECTER1 Saudi AH-64E combat clone. Source SouthKoreaHelicopterAH64E (STD44 unused; USA AH64E.ini not modified).\n",
    )
    jf.add_file(entries, SA_AH64_NEW, ah)
    uh = combatize_uh60(
        jf.clone_rename(
            jf.text_of(entries, USA_UH60),
            [("AmericaHelicopterUH60", "SaudiHelicopterUH60")],
            "America",
            "SaudiArabia",
            "",
        )
    )
    jf.add_file(entries, SA_UH60_NEW, uh)

    # --- Saudi American recon UAVs on radar ---
    rq = patch_recon_drone(
        jf.clone_rename(
            jf.text_of(entries, USA_RQ180),
            [("AmericaDroneRQ180", "SaudiArabiaDroneRQ180")],
            "America",
            "SaudiArabia",
            "; SPECTER1 Saudi RQ-180 recon drone. Donor AmericaDroneRQ180 (NOT modified). USA AWACS scan modules.\n",
        ),
        "sa rq180",
    )
    jf.add_file(entries, SA_RQ180_NEW, rq)
    mq = patch_recon_drone(
        jf.clone_rename(
            jf.text_of(entries, USA_MQ4),
            [("AmericaDroneMQ4", "SaudiArabiaDroneMQ4")],
            "America",
            "SaudiArabia",
            "; SPECTER1 Saudi MQ-4 recon drone. Donor AmericaDroneMQ4 (NOT modified). USA AWACS scan modules.\n",
        ),
        "sa mq4",
    )
    jf.add_file(entries, SA_MQ4_NEW, mq)

    # --- Saudi infantry = Iraqi package (donors not edited) ---
    inf_clones = [
        (IRAQ_RIFLE, SA_INF + r"\Rifleman.ini", INF_PAIRS),
        (IRAQ_AT, SA_INF + r"\Antitank.ini", INF_PAIRS),
        (IRAQ_AA, SA_INF + r"\AntiAir.ini", INF_PAIRS),
        (IRAQ_SNIPER, SA_INF + r"\HeavySniper.ini", INF_PAIRS),
        (IRAQ_SF, SA_INF + r"\SpecialForces.ini", INF_PAIRS),
        (IRAQ_WORKER, SA_INF + r"\SaudiArabia_Worker.ini", INF_PAIRS),
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
        (SA_INF + r"\SaudiArabia_Worker.ini").lower(),
    }
    for src, dst, pairs in inf_clones:
        cloned = jf.clone_rename(
            jf.text_of(entries, src),
            pairs,
            "Iraq",
            "SaudiArabia",
            "; SPECTER1 Saudi infantry clone. Donor " + src.split("\\")[-1] + " (NOT modified).\n",
        )
        if jf.norm(dst).lower() in existing_inf:
            jf.set_text(entries, dst, cloned)
        else:
            jf.add_file(entries, dst, cloned)

    # --- UK AH-64E / Merlin / American Chinook ---
    jf.set_text(entries, UK_AH64E, fix_ah64e(jf.text_of(entries, UK_AH64E)))
    jf.set_text(entries, UK_MERLIN, fix_merlin(jf.text_of(entries, UK_MERLIN)))
    chin = jf.clone_rename(
        jf.text_of(entries, USA_CH47),
        [("AmericaVehicleChinook", "BritainHelicopterChinook")],
        "America",
        "Britain",
        "",
    )
    jf.set_text(entries, UK_CHINOOK, fix_chinook_us(chin))

    # --- UK E-7 AWACS scan ---
    e7 = jf.text_of(entries, UK_E7)
    e7 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", e7, count=1)
    e7 = jf.insert_before_geometry(e7, jf.E3_USA_MODULES, "uk e7")
    if not e7.startswith("; SPECTER1"):
        e7 = "; SPECTER1 UK E-7 AWACS scan: AN_APY2_Radar_Power + AWACS_BaseMonaitoring.\n" + e7
    jf.set_text(entries, UK_E7, e7)

    # --- UK C-17 / A400M An-124 cargo ---
    c17 = jf.insert_before_geometry(jf.text_of(entries, UK_C17), AN124_CONTAIN, "uk c17")
    if not c17.startswith("; SPECTER1"):
        c17 = "; SPECTER1 UK C-17 An-124 TransportContain Slots=64 INFANTRY VEHICLE.\n" + c17
    jf.set_text(entries, UK_C17, c17)
    a400 = jf.insert_before_geometry(jf.text_of(entries, UK_A400), AN124_CONTAIN, "uk a400")
    if not a400.startswith("; SPECTER1"):
        a400 = "; SPECTER1 UK A400M An-124 TransportContain Slots=64 INFANTRY VEHICLE.\n" + a400
    jf.set_text(entries, UK_A400, a400)

    # --- UK fighter bombs (skip STD44 F-35B) ---
    uk_bombs = [
        (UK_FGR4, "TERTIARY", "Britain_Weapon_Brimstone", "GBU_31V2_JDAM_F15E"),
        (UK_T3, "TERTIARY", "Britain_Weapon_JetCannon", "Paveway_IV_EF2000"),
        (UK_TEMPEST, "TERTIARY", "Britain_Weapon_TempestPGM", "Kab500_LeaserGuidedBomb"),
        (UK_TF3, "TERTIARY", "Britain_Weapon_ASRAAM", "6_MK-82"),
        (UK_TGR4, "SECONDARY", "Britain_Weapon_Paveway_Heavy", "Gbu-12II_Paveway"),
        (UK_HAR, "PRIMARY", "Britain_Weapon_Paveway", "GBU38_JDAM_F16C"),
        (UK_SEA, "TERTIARY", "Britain_Weapon_JetCannon", "GBU-39_SDB_F22A"),
        (UK_FG1, "TERTIARY", "Britain_Weapon_JetCannon", "Kab1500_LeaserGuidedBomb"),
        (UK_JAG, "SECONDARY", "Britain_Weapon_Bomb", "Fab-250"),
        (UK_LIGHT, "TERTIARY", "Britain_Weapon_JetCannon", "Kab2500_LeaserGuidedBomb"),
        (UK_HAWK, "SECONDARY", "Britain_Weapon_HawkBomb", "AGM-154C_JSOW_F16C"),
        (UK_TECR, "TERTIARY", "Britain_Weapon_TornadoECR_PGM", "Specter_Weapon_SU34MF_Bomb6"),
        (UK_FGR2, "TERTIARY", "Britain_Weapon_JetCannon", "KH-47M2_ALBM_NKTWH"),
    ]
    for path, slot, old, new in uk_bombs:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)

    # --- Unlock Saudi + Britain ---
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
            "Saudi Arabia" in ln
            or "British Armed" in ln
            or ln.endswith("NationalGroundForces.ini")
        )
        if not allow:
            continue
        t = b.decode("latin1", errors="replace")
        t2, stripped = jf.unlock_named_objects(t, ("SaudiArabia", "SaudiJet", "SaudiHelicopter", "Britain"))
        if t2 != t:
            jf.set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    btn = jf.text_of(entries, P_CMDBTN)
    new_btns = [
        jf.unit_button("Command_ConstructSaudiJetB52H", "SaudiJetB52H", "B52", "\n"),
        jf.unit_button("Command_ConstructSaudiJetB1R", "SaudiJetB1R", "B1", "\n"),
        jf.unit_button("Command_ConstructSaudiJetB21", "SaudiJetB21", "B21_L", "\n"),
        jf.unit_button("Command_ConstructSaudiHelicopterAH64E", "SaudiHelicopterAH64E", "Nat_ah64e", "\n"),
        jf.unit_button("Command_ConstructSaudiHelicopterUH60", "SaudiHelicopterUH60", "us_uh60", "\n"),
        jf.unit_button("Command_ConstructSaudiArabiaDroneRQ180", "SaudiArabiaDroneRQ180", "SPEC_AmericaRQ180", "\n"),
        jf.unit_button("Command_ConstructSaudiArabiaDroneMQ4", "SaudiArabiaDroneMQ4", "us_mq4", "\n"),
        jf.unit_button("Command_ConstructSaudiArabia_RepublicanGuardMortar", "SaudiArabia_RepublicanGuardMortar", "irq_mortar", "\n"),
        jf.unit_button("Command_ConstructSaudiArabia_RepublicanGuardKornet", "SaudiArabia_RepublicanGuardKornet", "irq_kornet", "\n"),
        jf.unit_button("Command_ConstructSaudiArabia_RepublicanGuard_Pkm", "SaudiArabia_RepublicanGuard_Pkm", "irq_machinegunner", "\n"),
        jf.unit_button("Command_ConstructSaudiArabia_RepublicanGuard_Eng", "SaudiArabia_RepublicanGuard_Eng", "irq_eng", "\n"),
    ]
    btn = jf.append_buttons(btn, new_btns)
    img_fixes = [
        ("Command_ConstructSaudiArabiaTankM1A2", "us_m1a2", "sa m1a2"),
        ("Command_ConstructSaudiArabiaVehicleLAV25", "us_m1126S", "sa lav25"),
        ("Command_ConstructSaudiArabiaVehicleM2", "arb_m2a3", "sa m2"),
        ("Command_ConstructSaudiArabiaVehicleLAV", "us_m1126S", "sa lav"),
        ("Command_ConstructSaudiArabiaVehiclePatriot", "us_mim104e", "sa patriot"),
        ("Command_ConstructSaudiArabiaVehicleMPQ53", "us_tpy2", "sa mpq"),
        ("Command_ConstructSaudiArabiaVehicleATACMS", "us_m1075t", "sa atacms"),
        ("Command_ConstructSaudiArabiaVehiclePatriotBtry", "us_mim104e", "sa patriotb"),
        ("Command_ConstructSaudiArabia_RepublicanGuard_AKMS", "irq_rifleman", "sa akms img"),
        ("Command_ConstructSaudiArabia_RepublicanGuard_RPG7", "irq_antitank", "sa rpg img"),
        ("Command_ConstructSaudiArabia_RepublicanGuardIgla", "irq_igla", "sa igla img"),
        ("Command_ConstructSaudiArabia_SpecialForces_Akms", "irq_specialforce", "sa sf img"),
        ("Command_ConstructSaudiArabia_RepublicanGuard_TBK14", "irq_sniper", "sa tbk img"),
        ("Command_ConstructSaudiArabia_Worker", "irq_eng", "sa worker img"),
    ]
    for name, image, label in img_fixes:
        btn = jf.patch_button_image(btn, name, image, label)
    jf.set_text(entries, P_CMDBTN, btn)

    cs = jf.text_of(entries, P_CMDSET)
    sa_wf = [
        "  1  = Command_ConstructSaudiArabiaTankM1A2",
        "  2  = Command_ConstructSaudiArabiaTankM1A2S",
        "  3  = Command_ConstructSaudiArabiaVehicleLAV25",
        "  4  = Command_ConstructSaudiArabiaVehicleM2",
        "  5  = Command_ConstructSaudiArabiaVehicleLAV",
        "  6  = Command_ConstructSaudiArabiaVehicleAvenger",
        "  7  = Command_ConstructSaudiArabiaVehiclePatriot",
        "  8  = Command_ConstructSaudiArabiaVehicleMPQ53",
        "  9  = Command_ConstructSaudiArabiaVehicleASTROS",
        "  10 = Command_ConstructSaudiArabiaVehicleATACMS",
        "  11 = Command_ConstructSaudiArabiaVehicleM109",
        "  12 = Command_ConstructSaudiArabiaVehicleLAVAT",
        "  13 = Command_ConstructSaudiArabiaVehicleM88",
        "  14 = Command_Sell",
    ]
    for wf_name in (
        "SaudiArabia_WarFactoryCommandSet",
        "SaudiArabia_WarFactoryCommandSet1",
        "SaudiArabia_WarFactoryCommandSet2",
        "SaudiArabia_WarFactoryCommandSet3",
    ):
        cs = jf.replace_commandset(cs, wf_name, sa_wf)
    sa_heavy = [
        "  1 = Command_ConstructSaudiArabia_Mi-8T",
        "  2 = Command_ConstructSaudiArabia_IL-76",
        "  3 = Command_ConstructSaudiJetB52H",
        "  4 = Command_ConstructSaudiJetB1R",
        "  5 = Command_ConstructSaudiJetB21",
        "  6 = Command_ConstructSaudiHelicopterAH64E",
        "  7 = Command_ConstructSaudiHelicopterUH60",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "SaudiArabia_HeavyAirBaseCommandSet", sa_heavy)
    sa_radar = [
        "  1 = Command_ConstructSaudiArabiaDroneRQ180",
        "  2 = Command_ConstructSaudiArabiaDroneMQ4",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "SaudiArabia_RadarCommandSet", sa_radar)
    sa_barracks = [
        "  1 = Command_ConstructSaudiArabia_RepublicanGuard_AKMS",
        "  2 = Command_ConstructSaudiArabia_RepublicanGuard_RPG7",
        "  3 = Command_ConstructSaudiArabia_RepublicanGuardMortar",
        "  4 = Command_ConstructSaudiArabia_RepublicanGuardKornet",
        "  5 = Command_ConstructSaudiArabia_RepublicanGuard_Pkm",
        "  6 = Command_ConstructSaudiArabia_RepublicanGuard_TBK14",
        "  7 = Command_ConstructSaudiArabia_RepublicanGuard_Eng",
        "  8 = Command_ConstructSaudiArabia_SpecialForces_Akms",
        "  9 = Command_ConstructSaudiArabia_RepublicanGuardIgla",
        "  11 = Command_UpgradeGLARebelCaptureBuilding",
        "  12 = Command_Upgrade_RGD5",
        "  13 = Command_Upgrade_Rpg29",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "SaudiArabia_BarracksCommandSet", sa_barracks)
    uk_heavy = [
        "  1 = Command_ConstructBritainJetA400M",
        "  2 = Command_ConstructBritainJetC17",
        "  3 = Command_ConstructBritainAircraftE7",
        "  4 = Command_ConstructBritainDroneMQ9",
        "  5 = Command_ConstructBritainBomberVulcan",
        "  6 = Command_ConstructBritainHelicopterAH64E",
        "  7 = Command_ConstructBritainHelicopterChinook",
        "  8 = Command_ConstructBritainHelicopterMerlin",
        "  9 = Command_ConstructBritainHelicopterWildcat",
        "  10 = Command_ConstructBritainHelicopterPuma",
        "  11 = Command_ConstructBritainJetPhantomFGR2",
        "  12 = Command_ConstructBritainAircraftTornadoECR",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "Britain_HeavyAirBaseCommandSet", uk_heavy)
    uk_heli = [
        "  1  = Command_ConstructBritainHelicopterAH64E",
        "  2  = Command_ConstructBritainHelicopterChinook",
        "  3  = Command_ConstructBritainHelicopterMerlin",
        "  4  = Command_ConstructBritainHelicopterWildcat",
        "  5  = Command_ConstructBritainHelicopterPuma",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "Britain_HelicopterBaseCommandSet", uk_heli)
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
    if "Object FranceJetB52H" not in jf.text_of(entries, FR_B52):
        raise SystemExit("France B52 damaged")
    if "Object Iraq_RepublicanGuard_AKMS" not in jf.text_of(entries, IRAQ_RIFLE):
        raise SystemExit("Iraq rifle damaged")
    if "Object BritainJetF35B" not in jf.text_of(entries, UK_F35B_STD):
        raise SystemExit("STD44 F35B damaged")
    if "Object BritainHelicopterCH47F" not in jf.text_of(entries, UK_CH47_STD):
        raise SystemExit("STD44 CH47 damaged")
    if "LSFKoreaF5" not in jf.text_of(entries, SA_HAWK):
        raise SystemExit("Hawk65 mesh not replaced")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, UK_E7):
        raise SystemExit("E7 missing USA radar")
    if "ModuleTag_An124Cargo" not in jf.text_of(entries, UK_C17):
        raise SystemExit("C17 missing An-124 cargo")
    if "ModuleTag_An124Cargo" not in jf.text_of(entries, UK_A400):
        raise SystemExit("A400M missing An-124 cargo")
    if "Specter_Weapon_SU34MF_Bomb6" not in jf.text_of(entries, UK_TECR):
        raise SystemExit("Tornado ECR missing Su-34MF bomb")
    if "KH-47M2_ALBM_NKTWH" not in jf.text_of(entries, UK_FGR2):
        raise SystemExit("Phantom FGR.2 missing MiG-31K bomb")
    if "ComancheLocomotor" not in jf.text_of(entries, UK_AH64E):
        raise SystemExit("AH64E loco")
    if "GeometryIsSmall = No" not in jf.text_of(entries, UK_MERLIN):
        raise SystemExit("Merlin geom")
    if "ChinookAIUpdate" in jf.text_of(entries, UK_CHINOOK):
        raise SystemExit("Chinook still ChinookAI")
    if "NeedsRunway = No" not in jf.text_of(entries, UK_CHINOOK):
        raise SystemExit("Chinook runway")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, SA_RQ180_NEW):
        raise SystemExit("RQ180 missing scan")
    if not re.search(r"(?im)^\s*NeedsRunway\s*=\s*No\b", jf.text_of(entries, SA_RQ180_NEW)):
        raise SystemExit("RQ180 still needs runway")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, SA_MQ4_NEW):
        raise SystemExit("MQ4 missing scan")

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
        "SaudiJetB52H", "SaudiJetB1R", "SaudiJetB21", "SaudiHelicopterAH64E", "SaudiHelicopterUH60",
        "SaudiArabiaDroneRQ180", "SaudiArabiaDroneMQ4", "SaudiArabia_RepublicanGuardMortar",
        "SaudiArabia_RepublicanGuardKornet", "SaudiArabia_RepublicanGuard_Pkm", "SaudiArabia_RepublicanGuard_Eng",
        "SaudiArabia_RepublicanGuard_AKMS",
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
    locked_counts = {"sa_wf": 0, "sa_air": 0, "sa_bar": 0, "uk_air": 0}

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

    sa_wf_btns = audit_cs("SaudiArabia_WarFactoryCommandSet", "sa_wf")
    sa_air = audit_cs("SaudiArabia_AirfieldCommandSet", "sa_air")
    sa_heavy = audit_cs("SaudiArabia_HeavyAirBaseCommandSet", "sa_air")
    sa_radar = audit_cs("SaudiArabia_RadarCommandSet", "sa_air")
    sa_bar = audit_cs("SaudiArabia_BarracksCommandSet", "sa_bar")
    uk_air = audit_cs("BritainAirfieldCommandSet", "uk_air")
    uk_heavy = audit_cs("Britain_HeavyAirBaseCommandSet", "uk_air")
    uk_heli = audit_cs("Britain_HelicopterBaseCommandSet", "uk_air")

    for w in [
        "Saudi_Weapon_GBU_F15S", "GBU_31V2_JDAM_F15E", "Gbu-12II_Paveway", "Kab500_LeaserGuidedBomb",
        "6_MK-82", "Paveway_IV_EF2000", "GBU38_JDAM_F16C", "GBU-39_SDB_F22A", "Kab1500_LeaserGuidedBomb",
        "Fab-250", "Kab2500_LeaserGuidedBomb", "AGM-154C_JSOW_F16C", "Specter_Weapon_SU34MF_Bomb6",
        "KH-47M2_ALBM_NKTWH", "AN_APY2_Radar_Power", "AWACS_BaseMonaitoring", "30mm_M230E1_ChainGun",
        "70mm_Hydra_AH64E",
    ]:
        if w not in weapons:
            missing_wpn.append(w)

    model_checks = [
        "LSFKoreaF5", "US_AH64E", "US_UH60", "US_CH47F", "US_B52H", "US_B1R", "AVB21_A",
        "AVHawk", "LSFTornado",
    ]
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
    if any("Egypt" in c or "GLA" in c or "Arb_" in c or "Arab_" in c for c in sa_wf_btns):
        raise SystemExit("Saudi WF still Egypt/GLA")
    if "Command_ConstructSaudiJetB52H" not in sa_heavy:
        raise SystemExit("B-52 missing")
    if "Command_ConstructSaudiJetB1R" not in sa_heavy:
        raise SystemExit("B-1 missing")
    if "Command_ConstructSaudiJetB21" not in sa_heavy:
        raise SystemExit("B-21 missing")
    if "Command_ConstructSaudiHelicopterAH64E" not in sa_heavy:
        raise SystemExit("Saudi AH64 missing")
    if "Command_ConstructSaudiArabiaDroneRQ180" not in sa_radar:
        raise SystemExit("RQ180 missing radar")
    if "Command_ConstructSaudiArabia_RepublicanGuardMortar" not in sa_bar:
        raise SystemExit("Iraqi mortar missing barracks")
    if "Command_ConstructSaudiArabia_EliteSSG" in sa_bar:
        raise SystemExit("EliteSSG still in barracks")
    if "Command_ConstructBritainHelicopterAH64E" not in uk_heavy:
        raise SystemExit("UK AH64E not on heavy")
    if "Command_ConstructBritainHelicopterApache" in uk_heavy:
        raise SystemExit("UK Apache still on heavy")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    sa_bomb_map = {
        "SaudiJetF15S": jf.slot_weapon(jf.text_of(entries, SA_F15S), "TERTIARY"),
        "SaudiJetF15SA": jf.slot_weapon(jf.text_of(entries, SA_F15SA), "SECONDARY"),
        "SaudiJetF15C": jf.slot_weapon(jf.text_of(entries, SA_F15C), "TERTIARY"),
        "SaudiJetF15EX": jf.slot_weapon(jf.text_of(entries, SA_F15EX), "TERTIARY"),
        "SaudiJetTyphoon": jf.slot_weapon(jf.text_of(entries, SA_TYPH), "TERTIARY"),
        "SaudiJetTyphoonT3": jf.slot_weapon(jf.text_of(entries, SA_TYPH3), "TERTIARY"),
        "SaudiJetTornadoIDS": jf.slot_weapon(jf.text_of(entries, SA_TIDS), "SECONDARY"),
        "SaudiJetTornadoADV": jf.slot_weapon(jf.text_of(entries, SA_TADV), "TERTIARY"),
        "SaudiJetTornadoECR": jf.slot_weapon(jf.text_of(entries, SA_TECR), "SECONDARY"),
        "SaudiJetHawk65": jf.slot_weapon(jf.text_of(entries, SA_HAWK), "TERTIARY"),
        "SaudiJetLightning": jf.slot_weapon(jf.text_of(entries, SA_LIGHT), "TERTIARY"),
        "SaudiJetF5E": jf.slot_weapon(jf.text_of(entries, SA_F5E), "TERTIARY"),
    }
    uk_bomb_map = {
        "BritainJetTyphoonFGR4": jf.slot_weapon(jf.text_of(entries, UK_FGR4), "TERTIARY"),
        "BritainJetTyphoonT3": jf.slot_weapon(jf.text_of(entries, UK_T3), "TERTIARY"),
        "BritainJetTempest": jf.slot_weapon(jf.text_of(entries, UK_TEMPEST), "TERTIARY"),
        "BritainJetTornadoF3": jf.slot_weapon(jf.text_of(entries, UK_TF3), "TERTIARY"),
        "BritainJetTornadoGR4": jf.slot_weapon(jf.text_of(entries, UK_TGR4), "SECONDARY"),
        "BritainJetHarrierGR9": jf.slot_weapon(jf.text_of(entries, UK_HAR), "PRIMARY"),
        "BritainJetSeaHarrierFA2": jf.slot_weapon(jf.text_of(entries, UK_SEA), "TERTIARY"),
        "BritainJetPhantomFG1": jf.slot_weapon(jf.text_of(entries, UK_FG1), "TERTIARY"),
        "BritainJetJaguarGR3": jf.slot_weapon(jf.text_of(entries, UK_JAG), "SECONDARY"),
        "BritainJetLightningF6": jf.slot_weapon(jf.text_of(entries, UK_LIGHT), "TERTIARY"),
        "BritainJetHawk200": jf.slot_weapon(jf.text_of(entries, UK_HAWK), "SECONDARY"),
        "BritainAircraftTornadoECR": jf.slot_weapon(jf.text_of(entries, UK_TECR), "TERTIARY"),
        "BritainJetPhantomFGR2": jf.slot_weapon(jf.text_of(entries, UK_FGR2), "TERTIARY"),
    }
    for label, mp in (("SA", sa_bomb_map), ("UK", uk_bomb_map)):
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
            or "Saudi Arabia" in ln
            or "British Armed" in ln
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
    p("SPECTER1 SAUDI ARABIA + UNITED KINGDOM ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy; Hawk 65 uses existing LSFKoreaF5)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("PRIOR_INDIA_GERMANY_JAPAN_FRANCE_KOREA_ITALY = UNCHANGED")
    p("")
    p("=== SAUDI ARABIA FACTORY ===")
    p("BUG = SaudiArabia_WarFactoryCommandSet produced Side=Egypt/GLA/Arab units")
    p("FIX = M1A2/M1A2S/LAV25/M2/LAV/Avenger/Patriot/MPQ53/ASTROS/ATACMS/M109/LAVAT/M88")
    p("FACTORY_FIXED = YES")
    p("SA WARFACTORY =")
    for c in sa_wf_btns:
        p("  " + c)
    p("")
    p("=== SAUDI ARABIA AIRCRAFT ===")
    p("HAWK65_VISUAL_REPLACED = YES (LSFKoreaF5; weapons kept)")
    p("B52_ADDED = YES")
    p("B1_ADDED = YES")
    p("B21_ADDED = YES")
    p("AH64E_COMBAT_ADDED = YES")
    p("UH60_COMBAT_ADDED = YES")
    p("RQ180_RADAR_SCAN = YES (AN_APY2_Radar_Power + AWACS_BaseMonaitoring)")
    p("MQ4_RADAR_SCAN = YES (AN_APY2_Radar_Power + AWACS_BaseMonaitoring)")
    p("INFANTRY_IRAQ_PACKAGE = YES (cloned Side=SaudiArabia; Iraq donors unchanged)")
    p("SA HEAVY =")
    for c in sa_heavy:
        p("  " + c)
    p("SA RADAR =")
    for c in sa_radar:
        p("  " + c)
    p("SA BARRACKS =")
    for c in sa_bar:
        p("  " + c)
    p("")
    p("=== SAUDI ARABIA BOMBS ===")
    for obj, wpn in sa_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("=== SAUDI ARABIA UNLOCK ===")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("=== UNITED KINGDOM ===")
    p("AH64E_MOVEMENT_FIXED = YES (ComancheLocomotor + JetAI takeoff; 30mm)")
    p("MERLIN_MOVEMENT_FIXED = YES (GeometryIsSmall=No)")
    p("CHINOOK_AMERICAN = YES (AmericaVehicleChinook clone, JetAI NeedsRunway=No, TransportContain)")
    p("E7_AWACS_SCAN_FIXED = YES")
    p("C17_AN124_CARGO = YES")
    p("A400M_AN124_CARGO = YES")
    p("TORNADO_ECR_SU34MF_BOMB6 = YES ClipSize=6")
    p("PHANTOM_FGR2_MIG31K_BOMB = YES KH-47M2_ALBM_NKTWH")
    p("STD44_SKIP = BritainJetF35B.ini Rotary\\CH47F.ini")
    p("BOMB_DIVERSITY_APPLIED = YES")
    for obj, wpn in uk_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("UK HEAVY =")
    for c in uk_heavy:
        p("  " + c)
    p("")
    p("=== SAFETY ===")
    p("USA_B1_DONOR_UNCHANGED = YES")
    p("USA_UH60_DONOR_UNCHANGED = YES")
    p("USA_CH47_DONOR_UNCHANGED = YES")
    p("IRAQ_INFANTRY_DONORS_UNCHANGED = YES")
    p("FRANCE_B52_UNCHANGED = YES")
    p("STD44_FILES_UNCHANGED = YES")
    p("KOREA_ITALY_JAPAN_FRANCE_INDIA_GERMANY_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("SAUDI_ARABIA:")
    p("FACTORY_FIXED = YES")
    p("HAWK65_VISUAL_REPLACED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("B52_ADDED = YES")
    p("B1_ADDED = YES")
    p("B21_ADDED = YES")
    p("US_COMBAT_HELIS_ADDED = YES")
    p("IRAQ_INFANTRY_PACKAGE = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("US_RECON_UAVS_RADAR = YES")
    p("")
    p("UNITED_KINGDOM:")
    p("AH64E_MOVEMENT_FIXED = YES")
    p("MERLIN_MOVEMENT_FIXED = YES")
    p("CHINOOK_AMERICAN = YES")
    p("E7_AWACS_SCAN_FIXED = YES")
    p("C17_A400M_AN124_CARGO = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("TORNADO_ECR_SU34MF_BOMB6 = YES")
    p("PHANTOM_FGR2_MIG31K_BOMB = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Saudi Arabia + United Kingdom Roster 01

Continues from SPECTER1_Korea_Italy_Roster_01. Does not revert prior country work.
USA/Iraq donor INIs and STD44 files untouched.

Saudi Arabia:
- War factory retargeted from Egypt/GLA to native M1A2/LAV/M2/Patriot/ASTROS/M109 roster.
- Hawk 65 visual LSFKoreaF5. Distinct fighter bombs. B-52/B-1/B-21 plus AH-64E and UH-60 combat helis.
- Barracks uses cloned Iraqi Republican Guard package (Side=SaudiArabia). Radar RQ-180 + MQ-4 with USA AWACS scan.
- Science/NeededUpgrade locks stripped.

United Kingdom:
- AH-64E ComancheLocomotor + JetAI takeoff fields. Merlin GeometryIsSmall=No.
- Chinook replaced with American CH-47 clone, JetAI NeedsRunway=No, TransportContain kept.
- E-7 USA AWACS scan. C-17 and A400M An-124 cargo (Slots=64 INFANTRY VEHICLE).
- Distinct fighter bombs. Tornado ECR Specter_Weapon_SU34MF_Bomb6 (ClipSize=6). Phantom FGR.2 KH-47M2 (MiG-31K).
- F-35B STD44 not edited. Upgrade locks stripped.

ART packed unchanged (existing W3D stems). INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    zpath = WS_OUT / "SPECTER1_Saudi_UK_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Saudi_UK_Roster_01.zip").write_bytes(zpath.read_bytes())
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
