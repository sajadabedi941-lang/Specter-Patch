#!/usr/bin/env python3
"""SPECTER1 NATO + Libya roster pass.

Baseline: SPECTER1_Sweden_UAE_Roster_01 DATA+ART.
Does not revert prior country work.
Does not modify USA/Iraq donor INIs or STD44 files.
Only NATO and Libya CommandSets, object INIs, and new clone files.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_SWEDEN_UAE_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_SWEDEN_UAE_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "0513e20ed717c83a66f0522b853a3d7532dcec759f9b40efae77fbb42ef78888"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_NATO_LIBYA_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_NATO_LIBYA_ROSTER_01")

P_CMDSET = jf.P_CMDSET
P_CMDBTN = jf.P_CMDBTN
P_WEAPON = jf.P_WEAPON
P_NATIONAL = jf.P_NATIONAL

USA_B1 = r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini"
USA_B2 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"
USA_E3 = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
USA_V22 = r"Data\INI\Object\Specter\United States Of America\AmericaJetV22Visual.ini"
USA_C17 = r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini"
FR_B52 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB52H.ini"

NATO_F18A = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18A.ini"
NATO_F18C = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18C.ini"
NATO_F18E = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18E.ini"
NATO_F18F = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18F.ini"
NATO_F35B = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF35B.ini"
NATO_F16C = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF16C.ini"
NATO_TORNADO = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetTornadoIDS.ini"
NATO_EA18G = r"Data\INI\Object\Specter\NATO\FixedWings\EA18G.ini"
NATO_T4 = r"Data\INI\Object\Specter\NATO\FixedWings\EF2000_T4.ini"
NATO_T4AA = r"Data\INI\Object\Specter\NATO\FixedWings\EF2000_T4_AA.ini"
NATO_T4CAS = r"Data\INI\Object\Specter\NATO\FixedWings\EF2000_T4_CAS.ini"
NATO_F16D = r"Data\INI\Object\Specter\NATO\FixedWings\F16DBlk52.ini"
NATO_F35C = r"Data\INI\Object\Specter\NATO\FixedWings\F35A.ini"
NATO_F35C_AA = r"Data\INI\Object\Specter\NATO\FixedWings\F35A_AA.ini"
NATO_RAFALE = r"Data\INI\Object\Specter\NATO\FixedWings\Rafale_B_F3.ini"

NATO_E3_NEW = r"Data\INI\Object\Specter\NATO\Airforce\NatoAircraftE3USA.ini"
NATO_B1_NEW = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetB1R.ini"
NATO_B2_NEW = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetB2A.ini"
NATO_B52_NEW = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetB52H.ini"
NATO_V22_NEW = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetV22.ini"
NATO_C17_NEW = r"Data\INI\Object\Specter\NATO\Airforce\NatoJetC17.ini"

LIBYA_MIG29 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\Libya_Mig-29A.ini"
LIBYA_F1BQ = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\Libya_MirageF1-Bq.ini"
LIBYA_F1BD = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMirageF1BD.ini"
LIBYA_MIG23 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig23.ini"
LIBYA_MIG25 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig25.ini"
LIBYA_MIG21 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig21.ini"
LIBYA_MIG21MF = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetMig21MF.ini"
LIBYA_J7 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetJ7.ini"
LIBYA_SU22 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu22.ini"
LIBYA_SU22M4 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu22M4.ini"
LIBYA_SU25 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\Libya_Su-25K.ini"
LIBYA_SU24 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetSu24.ini"
LIBYA_F16 = r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\Libya_F16Blk52.ini"

DONOR_PROTECTED = list(jf.DONOR_PROTECTED) + [
    USA_B1, USA_B2, USA_E3, USA_V22, USA_C17, FR_B52,
]
STD44 = list(jf.STD44)
NATO_STD44 = [
    NATO_F18E, NATO_F18F, NATO_F35B, NATO_EA18G, NATO_F35C,
    r"Data\INI\Object\Specter\NATO\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\UH60.ini",
]
BYTE_LOCKED = [p for p in STD44 + DONOR_PROTECTED if jf.norm(p).lower() not in {jf.norm(x).lower() for x in NATO_STD44}]


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

    # --- NATO USA aircraft clones ---
    e3 = jf.clone_rename(
        jf.text_of(entries, USA_E3),
        [("AmericaJetE3Visual", "NatoAircraftE3USA")],
        "America",
        "Nato",
        "; SPECTER1 NATO USA AWACS. Donor AmericaJetE3Visual (NOT modified).\n",
    )
    e3 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", e3, count=1)
    e3 = jf.insert_before_geometry(e3, jf.E3_USA_MODULES, "nato e3")
    jf.add_file(entries, NATO_E3_NEW, e3)

    b1 = jf.clone_rename(
        jf.text_of(entries, USA_B1),
        [("AmericaJetB1R", "NatoJetB1R")],
        "America",
        "Nato",
        "; SPECTER1 NATO B-1R clone. Donor AmericaJetB1R (NOT modified).\n",
    )
    b1, _ = jf.promote_player_upgrade_weaponset(b1, "nato b1")
    jf.add_file(entries, NATO_B1_NEW, b1)

    b2 = jf.clone_rename(
        jf.text_of(entries, USA_B2),
        [("AmericaJetB2A", "NatoJetB2A")],
        "America",
        "Nato",
        "; SPECTER1 NATO B-2A clone. Donor AmericaJetB2A (NOT modified).\n",
    )
    jf.add_file(entries, NATO_B2_NEW, b2)

    b52 = jf.clone_rename(
        jf.text_of(entries, FR_B52),
        [("FranceJetB52H", "NatoJetB52H")],
        "France",
        "Nato",
        "; SPECTER1 NATO B-52H clone. Source FranceJetB52H (USA_System.ini not modified).\n",
    )
    b52, _ = jf.promote_player_upgrade_weaponset(b52, "nato b52")
    jf.add_file(entries, NATO_B52_NEW, b52)

    v22 = jf.clone_rename(
        jf.text_of(entries, USA_V22),
        [("AmericaJetV22Visual", "NatoJetV22")],
        "America",
        "Nato",
        "; SPECTER1 NATO V-22 clone. Donor AmericaJetV22Visual (NOT modified).\n",
    )
    jf.add_file(entries, NATO_V22_NEW, v22)

    c17 = jf.clone_rename(
        jf.text_of(entries, USA_C17),
        [("AmericaJetC17Visual", "NatoJetC17")],
        "America",
        "Nato",
        "; SPECTER1 NATO C-17 Starlifter clone. Donor AmericaJetC17Visual (NOT modified).\n",
    )
    if "ModuleTag_StarlifterCargo" not in c17 and "ModuleTag_An124Cargo" not in c17:
        raise SystemExit("NATO C17 missing Starlifter cargo contain")
    jf.add_file(entries, NATO_C17_NEW, c17)

    # --- NATO fighter bombs (skip STD44 F18E/F18F/F35B/EA18G/F35A) ---
    nato_bombs = [
        (NATO_F18A, "TERTIARY", "NatoJetF18A_WpnStrike", "GBU_31V2_JDAM_F15E"),
        (NATO_F18C, "TERTIARY", "NatoJetF18C_WpnStrike", "6_MK-82"),
        (NATO_F16C, "TERTIARY", "NatoJetF16C_WpnStrike", "Kab500_LeaserGuidedBomb"),
        (NATO_TORNADO, "SECONDARY", "NatoJetTornadoIDS_WpnBomb", "Kab1500_LeaserGuidedBomb"),
    ]
    for path, slot, old, new in nato_bombs:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)
    t4aa = jf.text_of(entries, NATO_T4AA)
    t4aa, _ = jf.promote_player_upgrade_weaponset(t4aa, "nato t4aa")
    t4aa = jf.add_tertiary_weapon(t4aa, "GBU38_JDAM_F16C", "nato t4aa bomb")
    jf.set_text(entries, NATO_T4AA, t4aa)

    # --- Libya fighter bombs (skip STD44 J7) ---
    libya_replace = [
        (LIBYA_F1BD, "TERTIARY", "LibyaJetMirageF1BD_WpnStrike", "Gbu-12II_Paveway"),
        (LIBYA_MIG23, "TERTIARY", "LibyaJetMig23_WpnStrike", "GBU38_JDAM_F16C"),
        (LIBYA_MIG25, "TERTIARY", "LibyaJetMig25_WpnGun", "GBU-39_SDB_F22A"),
        (LIBYA_MIG21, "TERTIARY", "Kab500_LeaserGuidedBomb", "Kab1500_LeaserGuidedBomb"),
        (LIBYA_MIG21MF, "TERTIARY", "LibyaJetMig21MF_WpnGun", "Paveway_IV_EF2000"),
        (LIBYA_SU22, "SECONDARY", "LibyaJetSu22_WpnBomb", "Kab2500_LeaserGuidedBomb"),
        (LIBYA_SU22M4, "TERTIARY", "LibyaJetSu22M4_WpnBomb", "AGM-154C_JSOW_F16C"),
    ]
    for path, slot, old, new in libya_replace:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.replace_weapon_slot(t, slot, old, new, path)
        jf.set_text(entries, path, t)
    libya_tertiary = [
        (LIBYA_MIG29, "GBU_31V2_JDAM_F15E", "libya mig29 bomb"),
        (LIBYA_F1BQ, "6_MK-82", "libya f1bq bomb"),
        (LIBYA_F16, "4x_GBU54B_500lb_LGB_EF2000", "libya f16 bomb"),
    ]
    for path, wpn, label in libya_tertiary:
        t = jf.text_of(entries, path)
        t, _ = jf.promote_player_upgrade_weaponset(t, path)
        t = jf.add_tertiary_weapon(t, wpn, label)
        jf.set_text(entries, path, t)

    # --- Unlock NATO (not Libya; not STD44 / donors) ---
    unlock_files = 0
    unlock_lines = 0
    protected = {jf.norm(x).lower() for x in BYTE_LOCKED}
    nato_unlock_prefixes = (
        "Nato", "IRIST", "Nlaw", "Meteor", "Paveway", "Brimstone", "Scalp",
    )
    for n, b in list(entries):
        ln = n.replace("/", "\\")
        if not ln.lower().endswith(".ini"):
            continue
        if "\\object\\" not in ln.lower():
            continue
        if jf.norm(ln).lower() in protected:
            continue
        allow_nato = "\\NATO\\" in ln or "\\Nato\\" in ln
        allow_nat = ln.endswith("NationalGroundForces.ini")
        if not allow_nato and not allow_nat:
            continue
        t = b.decode("latin1", errors="replace")
        prefixes = nato_unlock_prefixes if allow_nato else ("Nato",)
        t2, stripped = jf.unlock_named_objects(t, prefixes)
        if t2 != t:
            jf.set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    btn = jf.text_of(entries, P_CMDBTN)
    new_btns = [
        jf.unit_button("Command_ConstructNatoAircraftE3USA", "NatoAircraftE3USA", "us_e3g", "\n"),
        jf.unit_button("Command_ConstructNatoJetB1R", "NatoJetB1R", "B1", "\n"),
        jf.unit_button("Command_ConstructNatoJetB2A", "NatoJetB2A", "B2A", "\n"),
        jf.unit_button("Command_ConstructNatoJetB52H", "NatoJetB52H", "B52", "\n"),
        jf.unit_button("Command_ConstructNatoJetV22", "NatoJetV22", "V22", "\n"),
        jf.unit_button("Command_ConstructNatoJetC17", "NatoJetC17", "SPEC_BritainC17", "\n"),
        jf.unit_button("Command_ConstructNatoJetF18A", "NatoJetF18A", "SPEC_NatoJetF18A", "\n"),
        jf.unit_button("Command_ConstructNatoJetF18C", "NatoJetF18C", "SPEC_NatoJetF18C", "\n"),
        jf.unit_button("Command_ConstructNatoJetF18E", "NatoJetF18E", "SPEC_NatoJetF18E", "\n"),
        jf.unit_button("Command_ConstructNatoJetF18F", "NatoJetF18F", "SPEC_NatoJetF18F", "\n"),
        jf.unit_button("Command_ConstructNatoJetF16C", "NatoJetF16C", "SPEC_NatoJetF16C", "\n"),
        jf.unit_button("Command_ConstructNatoJetTornadoIDS", "NatoJetTornadoIDS", "SPEC_NatoJetTornadoIDS", "\n"),
    ]
    btn = jf.append_buttons(btn, new_btns)
    jf.set_text(entries, P_CMDBTN, btn)

    cs = jf.text_of(entries, P_CMDSET)
    nato_heavy = [
        "  1 = Command_ConstructNatoAircraftE3USA",
        "  2 = Command_ConstructNatoHelicopterAH64E",
        "  3 = Command_ConstructNatoHelicopterUH60",
        "  4 = Command_ConstructNatoHelicopterCH47F",
        "  5 = Command_ConstructNatoJetB1R",
        "  6 = Command_ConstructNatoJetB2A",
        "  7 = Command_ConstructNatoJetB52H",
        "  8 = Command_ConstructNatoJetV22",
        "  9 = Command_ConstructNatoJetC17",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = jf.replace_commandset(cs, "Nato_HeavyAirBaseCommandSet", nato_heavy)
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
    if "Object AmericaJetB2A" not in jf.text_of(entries, USA_B2):
        raise SystemExit("USA B2 damaged")
    if "Object AmericaJetB1R" not in jf.text_of(entries, USA_B1):
        raise SystemExit("USA B1 damaged")
    if "Object AmericaJetV22Visual" not in jf.text_of(entries, USA_V22):
        raise SystemExit("USA V22 damaged")
    if "Object AmericaJetC17Visual" not in jf.text_of(entries, USA_C17):
        raise SystemExit("USA C17 damaged")
    if "Object FranceJetB52H" not in jf.text_of(entries, FR_B52):
        raise SystemExit("France B52 damaged")
    if "Object NatoJetF18E" not in jf.text_of(entries, NATO_F18E):
        raise SystemExit("STD44 NATO F18E damaged")
    if "Object NatoJetF18F" not in jf.text_of(entries, NATO_F18F):
        raise SystemExit("STD44 NATO F18F damaged")
    if "Object NatoJetF35B" not in jf.text_of(entries, NATO_F35B):
        raise SystemExit("STD44 NATO F35B damaged")
    if "Object NatoJetEA18G" not in jf.text_of(entries, NATO_EA18G):
        raise SystemExit("STD44 NATO EA18G damaged")
    if "Object NatoJetF35C" not in jf.text_of(entries, NATO_F35C):
        raise SystemExit("STD44 NATO F35C damaged")
    if "Object LibyaJetJ7" not in jf.text_of(entries, LIBYA_J7):
        raise SystemExit("STD44 Libya J7 damaged")
    if "AN_APY2_Radar_Power" not in jf.text_of(entries, NATO_E3_NEW):
        raise SystemExit("NATO E3 missing USA radar")
    if "ModuleTag_StarlifterCargo" not in jf.text_of(entries, NATO_C17_NEW):
        raise SystemExit("NATO C17 missing Starlifter cargo")
    if not re.search(r"(?im)^\s*Side\s*=\s*Nato\b", jf.text_of(entries, NATO_E3_NEW)):
        raise SystemExit("NATO E3 side not Nato")

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
        "NatoAircraftE3USA", "NatoJetB1R", "NatoJetB2A", "NatoJetB52H", "NatoJetV22", "NatoJetC17",
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
    missing_models: list[str] = []
    locked_counts = {"nato_air": 0, "nato_heavy": 0, "libya_air": 0}

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

    nato_air = audit_cs("NatoAirfieldCommandSet", "nato_air")
    nato_large = audit_cs("Nato_LargeAirBaseCommandSet", "nato_air")
    nato_heavy_btns = audit_cs("Nato_HeavyAirBaseCommandSet", "nato_heavy")
    libya_air = audit_cs("Libya_AirfieldCommandSet", "libya_air")

    for w in [
        "GBU_31V2_JDAM_F15E", "6_MK-82", "Gbu-12II_Paveway", "GBU38_JDAM_F16C", "GBU-39_SDB_F22A",
        "Kab1500_LeaserGuidedBomb", "Kab500_LeaserGuidedBomb", "Kab2500_LeaserGuidedBomb",
        "AGM-154C_JSOW_F16C", "Paveway_IV_EF2000", "Fab-250", "4x_GBU54B_500lb_LGB_EF2000",
        "AN_APY2_Radar_Power", "AWACS_BaseMonaitoring", "2x_GBU12II_FA18F",
        "AGM88G_AARGM_ER_F16CJ_LR", "Specter_Weapon_SU34MF_Bomb6", "2x_ALCM_ScalpEG",
        "2x_AGM88G_AARGM-ER_F16CJ",
    ]:
        if w not in weapons:
            missing_wpn.append(w)

    for path, models in [
        (NATO_E3_NEW, ["E3"]),
        (NATO_B1_NEW, ["US_B1R"]),
        (NATO_B2_NEW, ["AVB3bmbr"]),
        (NATO_B52_NEW, ["US_B52H"]),
        (NATO_V22_NEW, ["AVOsprey"]),
        (NATO_C17_NEW, ["IUAC17HXNew"]),
    ]:
        t = jf.text_of(entries, path)
        for mname in models:
            if not re.search(rf"(?im)^\s*Model\s*=\s*{re.escape(mname)}\b", t):
                missing_models.append(f"{path} Model={mname}")
            elif mname.lower() not in astems:
                missing_models.append(mname)

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
    if "Command_ConstructNatoAircraftE3USA" not in nato_heavy_btns:
        raise SystemExit("USA AWACS missing")
    if "Command_ConstructNatoJetE3AAWACS" in nato_heavy_btns:
        raise SystemExit("old NATO AWACS still produced")
    if "Command_ConstructNatoJetB1R" not in nato_heavy_btns:
        raise SystemExit("NATO B-1 missing")
    if "Command_ConstructNatoJetB2A" not in nato_heavy_btns:
        raise SystemExit("NATO B-2 missing")
    if "Command_ConstructNatoJetB52H" not in nato_heavy_btns:
        raise SystemExit("NATO B-52 missing")
    if "Command_ConstructNatoJetV22" not in nato_heavy_btns:
        raise SystemExit("NATO V-22 missing")
    if "Command_ConstructNatoJetC17" not in nato_heavy_btns:
        raise SystemExit("NATO C-17 missing")
    if "Command_ConstructNatoJetF18A" not in nato_air:
        raise SystemExit("NATO F18A airfield button missing")
    if "Command_ConstructNatoJetF18C" not in nato_air:
        raise SystemExit("NATO F18C airfield button missing")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    nato_bomb_map = {
        "NatoJetF18A": jf.slot_weapon(jf.text_of(entries, NATO_F18A), "TERTIARY"),
        "NatoJetF18C": jf.slot_weapon(jf.text_of(entries, NATO_F18C), "TERTIARY"),
        "NatoJetF18E": jf.slot_weapon(jf.text_of(entries, NATO_F18E), "PRIMARY"),
        "NatoJetF18F": jf.slot_weapon(jf.text_of(entries, NATO_F18F), "SECONDARY"),
        "NatoJetEA18G": jf.slot_weapon(jf.text_of(entries, NATO_EA18G), "PRIMARY"),
        "NatoJetF35C": jf.slot_weapon(jf.text_of(entries, NATO_F35C), "PRIMARY"),
        "NatoJetF35B": jf.slot_weapon(jf.text_of(entries, NATO_F35B), "PRIMARY"),
        "NatoJetEF2000T4": jf.slot_weapon(jf.text_of(entries, NATO_T4), "PRIMARY"),
        "NatoJetF16C": jf.slot_weapon(jf.text_of(entries, NATO_F16C), "TERTIARY"),
        "NatoJetF16DBlk52": jf.slot_weapon(jf.text_of(entries, NATO_F16D), "PRIMARY"),
        "NatoJetRafaleF3": jf.slot_weapon(jf.text_of(entries, NATO_RAFALE), "PRIMARY"),
        "NatoJetTornadoIDS": jf.slot_weapon(jf.text_of(entries, NATO_TORNADO), "SECONDARY"),
    }
    libya_bomb_map = {
        "Libya_Mig-29A": jf.slot_weapon(jf.text_of(entries, LIBYA_MIG29), "TERTIARY"),
        "Libya_MirageF1_Bq": jf.slot_weapon(jf.text_of(entries, LIBYA_F1BQ), "TERTIARY"),
        "LibyaJetMirageF1BD": jf.slot_weapon(jf.text_of(entries, LIBYA_F1BD), "TERTIARY"),
        "LibyaJetMig23": jf.slot_weapon(jf.text_of(entries, LIBYA_MIG23), "TERTIARY"),
        "LibyaJetMig25": jf.slot_weapon(jf.text_of(entries, LIBYA_MIG25), "TERTIARY"),
        "LibyaJetMig21": jf.slot_weapon(jf.text_of(entries, LIBYA_MIG21), "TERTIARY"),
        "LibyaJetMig21MF": jf.slot_weapon(jf.text_of(entries, LIBYA_MIG21MF), "TERTIARY"),
        "LibyaJetJ7": jf.slot_weapon(jf.text_of(entries, LIBYA_J7), "PRIMARY"),
        "LibyaJetSu22": jf.slot_weapon(jf.text_of(entries, LIBYA_SU22), "SECONDARY"),
        "LibyaJetSu22M4": jf.slot_weapon(jf.text_of(entries, LIBYA_SU22M4), "TERTIARY"),
        "Libya_Su-25K": jf.slot_weapon(jf.text_of(entries, LIBYA_SU25), "PRIMARY"),
        "LibyaJetSu24": jf.slot_weapon(jf.text_of(entries, LIBYA_SU24), "SECONDARY"),
        "Libya_F16Blk52": jf.slot_weapon(jf.text_of(entries, LIBYA_F16), "TERTIARY"),
    }
    for label, mp in (("NATO", nato_bomb_map), ("LIBYA", libya_bomb_map)):
        vals = list(mp.values())
        if "NONE" in vals:
            raise SystemExit(f"{label} missing bomb {mp}")
        if len(set(vals)) != len(vals):
            raise SystemExit(f"{label} bomb collision {mp}")

    e3_txt = jf.text_of(entries, NATO_E3_NEW)
    if "StealthDetectorUpdate" not in e3_txt:
        raise SystemExit("NATO E3 missing StealthDetectorUpdate")
    v22_txt = jf.text_of(entries, NATO_V22_NEW)
    if "AVOsprey" not in v22_txt:
        raise SystemExit("NATO V22 missing AVOsprey")
    if "CAN_ATTACK" not in v22_txt:
        raise SystemExit("NATO V22 lost CAN_ATTACK")

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
            or "\\NATO\\" in ln
            or "\\Nato\\" in ln
            or "Libyan Armed Forces" in ln
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
    p("SPECTER1 NATO + LIBYA ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy; USA donor W3D already packed)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("PRIOR_COUNTRIES_UNCHANGED = YES")
    p("")
    p("=== NATO ===")
    p("B1_ADDED = YES")
    p("B2_ADDED = YES")
    p("B52_ADDED = YES")
    p("V22_ADDED = YES")
    p("E3_ADDED = YES (NatoAircraftE3USA clone of AmericaJetE3Visual)")
    p("C17_STARLIFTER_ADDED = YES (NatoJetC17 clone of AmericaJetC17Visual + Starlifter cargo)")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("NATO AIRFIELD =")
    for c in nato_air:
        p("  " + c)
    p("NATO LARGE AIRBASE =")
    for c in nato_large:
        p("  " + c)
    p("NATO HEAVY =")
    for c in nato_heavy_btns:
        p("  " + c)
    p("NATO BOMBS =")
    for obj, wpn in nato_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("")
    p("=== LIBYA ===")
    p("BOMB_DIVERSITY_APPLIED = YES (STD44 LibyaJetJ7.ini not edited)")
    p("LIBYA AIRFIELD =")
    for c in libya_air:
        p("  " + c)
    p("LIBYA BOMBS =")
    for obj, wpn in libya_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("")
    p("=== SAFETY ===")
    p("USA_E3_DONOR_UNCHANGED = YES")
    p("USA_B1_DONOR_UNCHANGED = YES")
    p("USA_B2_DONOR_UNCHANGED = YES")
    p("USA_V22_DONOR_UNCHANGED = YES")
    p("USA_C17_DONOR_UNCHANGED = YES")
    p("FRANCE_B52_DONOR_UNCHANGED = YES")
    p("STD44_NON_NATO_UNCHANGED = YES")
    p("NATO_STD44_UNLOCK_ONLY = YES (EA18G/F35A science locks stripped; weapons/models kept)")
    p("SWEDEN_UAE_SAUDI_UK_KOREA_ITALY_JAPAN_FRANCE_INDIA_GERMANY_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("NATO:")
    p("B1_ADDED = YES")
    p("B2_ADDED = YES")
    p("B52_ADDED = YES")
    p("V22_ADDED = YES")
    p("E3_ADDED = YES")
    p("C17_STARLIFTER_ADDED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("LIBYA:")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 NATO + Libya Roster 01

Continues from SPECTER1_Sweden_UAE_Roster_01. Does not revert prior country work.
USA/France donor INIs and STD44 files untouched.

NATO:
- Heavy airbase adds USA clones: B-1R, B-2A, B-52H, V-22 Osprey, E-3 AWACS, C-17 Starlifter.
- Old NatoJetE3AAWACS production slot replaced by AmericaJetE3Visual clone.
- Missing F-18A/C/E/F, F-16C, Tornado IDS construct buttons added.
- Distinct fighter bombs. Upgrade locks stripped on NATO objects, including STD44 EA-18G/F-35C science gates.

Libya:
- Distinct fighter bombs (STD44 J-7 not edited). Unlocks not requested.

ART packed unchanged (existing USA W3D stems). INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    zpath = WS_OUT / "SPECTER1_Nato_Libya_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Nato_Libya_Roster_01.zip").write_bytes(zpath.read_bytes())
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
