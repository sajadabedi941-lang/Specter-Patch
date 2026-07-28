#!/usr/bin/env python3
"""Full Turkey faction reset — no new weapon objects.

1) Rebuild key aircraft from validated USA/China/Russia Specter donors
2) Retarget every Turkey_* weapon reference to existing stock weapons
3) Remove broken Turkey custom weapon/projectile Objects
4) Keep Turkey names / Side=Turkey
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # patch/
DATA = ROOT / "Data" / "INI"
TURKEY = DATA / "Object" / "Specter" / "Turkey Armed Forces"
REPORT = ROOT / "Release" / "TURKEY_FACTION_FULL_RESET" / "RESET_REPORT.txt"

# Valid existing weapons only (Weapon.ini / Weapon_FactionExpansion.ini)
WMAP = {
    "Turkey_Weapon_AIM120D_F16Block70": "AIM120D_BVR_MRAAM_F22A",
    "Turkey_Weapon_AIM120C_F16V": "America_Weapon_AIM120C_F16V",
    "Turkey_Weapon_AAM_Medium": "America_Weapon_AIM120C_F16V",
    "Turkey_Weapon_AAM_Short": "AIM-9X_F16C",
    "Turkey_Weapon_Goktug_KAAN": "America_Weapon_AIM120C_F16V",
    "Turkey_Weapon_ATGM": "4x_AGM114N_Mq9",
    "Turkey_Weapon_Altay_ATGM": "9M113_Konkurs",
    "Turkey_Weapon_Cruise": "America_Weapon_JASSM_F15E",
    "Turkey_Weapon_BallisticStrike": "America_Weapon_Tomahawk_Strategic",
    "Turkey_Weapon_Tayfun": "America_Weapon_Tomahawk_Strategic",
    "Turkey_Weapon_Fab250": "GBU_31V1_JDAM_F16C",
    "Turkey_Weapon_KH25ML": "Russia_Weapon_Kh32_Tu22M3",
    "Turkey_Weapon_S8Rocket": "6X_80mm_S8_Rockets_MI28N",
    "Turkey_Weapon_SAM": "Russia_Weapon_S400",
    "Turkey_Weapon_SHORAD": "Russia_Weapon_Buk",
    "Turkey_Weapon_MD": "America_Weapon_THAAD",
    "Turkey_Weapon_ADSAM": "America_Weapon_Patriot",
    "Turkey_Weapon_AntiDrone": "America_Weapon_AntiDrone",
    "Turkey_Weapon_TankAP": "9M113_Konkurs",
    "Turkey_Weapon_MLRS_Semi": "America_Weapon_PrSM",
    "Turkey_Weapon_MLRS_Salvo": "America_Weapon_PrSM",
    "Turkey_Weapon_MLRS_Warhead": "America_Weapon_PrSM",
    "Turkey_Weapon_TRG230_Salvo": "America_Weapon_PrSM",
    "Turkey_Weapon_TRG230_HE": "America_Weapon_PrSM",
    "Turkey_Weapon_AbbasMissile": "America_Weapon_Tomahawk_Strategic",
    "Turkey_Weapon_AbbasICBM_AI": "America_Weapon_Tomahawk_Strategic",
    "Turkey_AlAbidMissileWeapon": "America_Weapon_Tomahawk_Strategic",
    "Turkey_HussieanMissileWeapon": "America_Weapon_Tomahawk_Strategic",
    "Turkey_HussieanMissileWeapon_AI": "America_Weapon_Tomahawk_Strategic",
    "4x_Turkey_Fab-100_CenterRack_Mig23BN": "5x_Fab500_SU22M3_CenterRack",
    "2A18_Turkey_122mm_ClusterShell_BD": "America_Weapon_PrSM",
}

# Safety: Turkey weapons still defined but point at validated FactionExpansion projectiles
PROJ_RETARGET = {
    "Turkey_Goktug_Projectile": "America_Projectile_AIM120C_F16V",
    "Turkey_Projectile_ADSAM": "America_Projectile_Patriot",
    "Turkey_SOM_Cruise_Projectile": "America_Projectile_JASSM_F15E",
    "Turkey_Projectile_Tank": "America_Projectile_AntiDrone",
    "Turkey_Projectile_MLRSShort": "America_Projectile_Tomahawk_Strategic",
    "Turkey_SOM_Projectile": "America_Projectile_Tomahawk_Strategic",
    "Turkey_Projectile_ATGM": "America_Projectile_AntiDrone",
    "Turkey_Projectile_SHORAD": "Russia_Projectile_Buk",
    "Turkey_Projectile_SAM": "Russia_Projectile_S400",
    "Turkey_Projectile_MD": "America_Projectile_THAAD",
    "Turkey_Projectile_Goktug_KAAN": "America_Projectile_AIM120C_F16V",
    "Turkey_Projectile_AIM120C_F16V": "America_Projectile_AIM120C_F16V",
    "Turkey_Tayfun_Projectile": "America_Projectile_Tomahawk_Strategic",
    "Turkey_Projectile_AntiDrone": "America_Projectile_AntiDrone",
    "Turkey_Projectile_F16Blk70_AIM120": "America_Projectile_AIM120C_F16V",
    "Turkey_Projectile_Altay_ATGM": "America_Projectile_AntiDrone",
    "Turkey_Fab-250": "America_Projectile_JASSM_F15E",
    "Turkey_Fab-100": "America_Projectile_JASSM_F15E",
    "Turkey_Abbas_Missile": "America_Projectile_Tomahawk_Strategic",
    "Turkey_KH-25ML_MissileObject": "Russia_Projectile_Kh32_Tu22M3",
    "Turkey_Turkey_122mm_m21OF_Grad_Missile_Short": "America_Projectile_Tomahawk_Strategic",
    "Turkey_255mmShell": "America_Projectile_Tomahawk_Strategic",
}


def clone_identity(text: str, *, old_object: str, new_object: str, old_side: str, new_side: str,
                   display: str | None = None, prereq_from: str | None = None,
                   prereq_to: str | None = None, upgrade_from: str | None = None,
                   upgrade_to: str | None = None) -> str:
    out = text
    out = re.sub(rf"^Object\s+{re.escape(old_object)}\s*$", f"Object {new_object}", out, count=1, flags=re.M)
    out = re.sub(rf"(DisplayName\s*=\s*)OBJECT:{re.escape(old_object)}", rf"\1OBJECT:{new_object}", out)
    if display:
        out = re.sub(r"(DisplayName\s*=\s*)\S+", rf"\1{display}", out, count=1)
    out = re.sub(rf"(Side\s*=\s*){re.escape(old_side)}", rf"\1{new_side}", out)
    if prereq_from and prereq_to:
        out = out.replace(prereq_from, prereq_to)
    if upgrade_from and upgrade_to:
        out = out.replace(upgrade_from, upgrade_to)
    # Strip foreign BuildVariations that would pull missing objects
    out = re.sub(r"^\s*BuildVariations\s*=\s*.*$", "", out, flags=re.M)
    header = (
        f"; SPECTER TURKEY FACTION FULL RESET\n"
        f"; Donor clone → {new_object} (Side={new_side})\n"
        f"; Weapons: existing USA/China/Russia only — no new weapon objects\n"
    )
    if not out.lstrip().startswith("; SPECTER TURKEY FACTION FULL RESET"):
        out = header + out
    return out


def set_weaponset_f16(text: str) -> str:
    """Force USA F-16 weapon system."""
    ws = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F22A
    Weapon = SECONDARY AGM-154C_JSOW_F16C
    Weapon = TERTIARY AN/AAQ33_SniperXR_ATP_F16C
  End"""
    if re.search(r"^\s*WeaponSet\b", text, re.M):
        text = re.sub(
            r"^\s*WeaponSet\b.*?^\s*End\s*$",
            ws,
            text,
            count=1,
            flags=re.M | re.S,
        )
    else:
        text = re.sub(r"(^\s*Side\s*=\s*.*$)", rf"\1\n{ws}", text, count=1, flags=re.M)
    return text


def set_weaponset_mq9(text: str) -> str:
    ws = """  WeaponSet
    Conditions            = None
    Weapon                = PRIMARY     4x_AGM114N_Mq9
    PreferredAgainst      = PRIMARY     VEHICLE STRUCTURE
    AutoChooseSources     = PRIMARY     FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon                = SECONDARY   2x_GBU12II_Mq9
    PreferredAgainst      = SECONDARY   STRUCTURE
    AutoChooseSources     = SECONDARY   FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""
    text = re.sub(r"^\s*WeaponSet\b.*?^\s*End\s*$", ws, text, count=1, flags=re.M | re.S)
    return text


def set_weaponset_tu22(text: str) -> str:
    ws = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY Russia_Weapon_Kh32_Tu22M3
  End"""
    if re.search(r"^\s*WeaponSet\b", text, re.M):
        text = re.sub(r"^\s*WeaponSet\b.*?^\s*End\s*$", ws, text, count=1, flags=re.M | re.S)
    else:
        text = re.sub(r"(^\s*Side\s*=\s*.*$)", rf"\1\n{ws}", text, count=1, flags=re.M)
    return text


def retarget_weapons_in_text(text: str) -> tuple[str, int]:
    n = 0
    for old, new in sorted(WMAP.items(), key=lambda kv: -len(kv[0])):
        # Weapon = SLOT NAME
        pattern = rf"(^\s*Weapon\s*=\s*\S+\s+){re.escape(old)}\b"
        text2, c = re.subn(pattern, rf"\g<1>{new}", text, flags=re.M)
        # bare token occurrences in weapon files ProjectileObject etc. handled separately
        if c:
            text = text2
            n += c
        # also replace standalone weapon name assignments without slot (rare)
        pattern2 = rf"(^\s*Weapon\s*=\s*){re.escape(old)}\b"
        text2, c2 = re.subn(pattern2, rf"\g<1>{new}", text, flags=re.M)
        if c2:
            text = text2
            n += c2
    return text, n


def retarget_projectiles_in_text(text: str) -> tuple[str, int]:
    n = 0
    for old, new in PROJ_RETARGET.items():
        text2, c = re.subn(
            rf"(^\s*ProjectileObject\s*=\s*){re.escape(old)}\b",
            rf"\g<1>{new}",
            text,
            flags=re.M,
        )
        if c:
            text = text2
            n += c
    return text, n


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def rebuild_aircraft(log: list[str]) -> None:
    britain = (DATA / "Object/Specter/British Armed Forces/Airforce/Britain_F16DBlk52.ini").read_text(
        encoding="utf-8", errors="replace"
    )
    japan = (DATA / "Object/Specter/Japan Self-Defense Forces/Airforce/Japan_MQ9.ini").read_text(
        encoding="utf-8", errors="replace"
    )
    aab = (DATA / "Object/Specter/PatchSystems/AdvancedAirBase/Aircraft_AAB_Global.ini").read_text(
        encoding="utf-8", errors="replace"
    )

    def extract_aab(name: str) -> str:
        m = re.search(rf"^Object\s+{re.escape(name)}\s*$", aab, re.M)
        if not m:
            raise SystemExit(f"missing AAB donor {name}")
        m2 = re.search(r"^Object\s+\S+", aab[m.end() :], re.M)
        end = m.end() + m2.start() if m2 else len(aab)
        return aab[m.start() : end].rstrip() + "\n"

    britain_obj = re.search(r"^Object\s+(\S+)", britain, re.M).group(1)
    # --- F-16 Block70 from Britain USA F-16D donor + USA F-16 weapons ---
    f16 = clone_identity(
        britain,
        old_object=britain_obj,
        new_object="Turkey_F16Block70",
        old_side="Britain",
        new_side="Turkey",
        display="OBJECT:Turkey_F16Block70",
        prereq_from="Britain_AdvancedAirBase",
        prereq_to="Turkey_AdvancedAirBase",
        upgrade_from="Upgrade_Britain",
        upgrade_to="Upgrade_Turkey",
    )
    f16 = f16.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
    f16 = f16.replace("Upgrade_AIM-9X", "Upgrade_Turkey_PrecisionMunitions")
    f16 = set_weaponset_f16(f16)
    # Fix DisplayName leftovers
    f16 = re.sub(r"DisplayName\s*=\s*\S+", "DisplayName             = OBJECT:Turkey_F16Block70", f16, count=1)
    write(TURKEY / "Airforce" / "Turkey_F16Block70.ini", f16)
    log.append("Rebuilt Turkey_F16Block70 from Britain_F16DBlk52 + USA F-16 weapons")

    # --- F16V + variants ---
    variants = [
        ("Turkey_F16V", "America_Weapon_AIM120C_F16V"),
        ("Turkey_F16V_Mixed", "America_Weapon_AIM120C_F16V"),
        ("Turkey_F16V_AGM", "AGM-154C_JSOW_F16C"),
        ("Turkey_F16V_GBU24", "GBU_31V1_JDAM_F16C"),
    ]
    parts = [
        "; SPECTER TURKEY FACTION FULL RESET - Turkey_F16V family\n"
        "; Donor: Britain_F16DBlk52 (USA F-16D art) / USA F-16 weapon system\n"
        "; BuildVariations preserved as separate Objects with stock weapons only\n\n"
    ]
    for i, (obj, primary) in enumerate(variants):
        block = clone_identity(
            britain,
            old_object=britain_obj,
            new_object=obj,
            old_side="Britain",
            new_side="Turkey",
            display=f"OBJECT:{obj}",
            prereq_from="Britain_AdvancedAirBase",
            prereq_to="Turkey_AdvancedAirBase",
        )
        block = block.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
        block = re.sub(r"DisplayName\s*=\s*\S+", f"DisplayName             = OBJECT:{obj}", block, count=1)
        if obj == "Turkey_F16V":
            ws = f"""  WeaponSet
    Conditions = None
    Weapon = PRIMARY {primary}
    Weapon = SECONDARY AGM-154C_JSOW_F16C
    Weapon = TERTIARY AN/AAQ33_SniperXR_ATP_F16C
  End"""
        else:
            ws = f"""  WeaponSet
    Conditions = None
    Weapon = PRIMARY {primary}
    Weapon = SECONDARY AGM-154C_JSOW_F16C
  End"""
        block = re.sub(r"^\s*WeaponSet\b.*?^\s*End\s*$", ws, block, count=1, flags=re.M | re.S)
        if obj == "Turkey_F16V":
            # re-insert BuildVariations after Side
            block = re.sub(
                r"(^\s*Side\s*=\s*Turkey\s*$)",
                r"\1\n  BuildVariations         = Turkey_F16V Turkey_F16V_Mixed Turkey_F16V_AGM Turkey_F16V_GBU24",
                block,
                count=1,
                flags=re.M,
            )
        parts.append(block if block.endswith("\n") else block + "\n")
        parts.append("\n")
    write(TURKEY / "Airforce" / "Turkey_F16V.ini", "".join(parts))
    log.append("Rebuilt Turkey_F16V family from Britain_F16DBlk52 + USA F-16 weapons")

    # --- TB2 / Akinci / Kizilelma from Japan_MQ9 (China CH5 art + USA MQ-9 weapons) ---
    for obj, path in [
        ("Turkey_TB2", TURKEY / "Airforce" / "Turkey_TB2.ini"),
        ("Turkey_Akinci", TURKEY / "Airforce" / "Turkey_Akinci.ini"),
        ("Turkey_Kizilelma", TURKEY / "Drones" / "Turkey_Kizilelma.ini"),
    ]:
        block = clone_identity(
            japan,
            old_object="Japan_MQ9",
            new_object=obj,
            old_side="Japan",
            new_side="Turkey",
            display=f"OBJECT:{obj}",
            prereq_from="Japan_AdvancedAirBase",
            prereq_to="Turkey_AdvancedAirBase",
        )
        block = block.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
        block = re.sub(r"DisplayName\s*=\s*\S+", f"DisplayName             = OBJECT:{obj}", block, count=1)
        block = set_weaponset_mq9(block)
        # Kizilelma may use SCIENCE_Rank3 — keep
        write(path, block)
        log.append(f"Rebuilt {obj} from Japan_MQ9 (CHI_CH5 + USA MQ-9 weapons)")

    # --- Tu-22M3 from Patch_Russia_Tu22M3 ---
    ru = extract_aab("Patch_Russia_Tu22M3")
    for obj, path in [
        ("Turkey_Tu-22M3", TURKEY / "Airforce" / "Turkey_Tu-22M3.ini"),
        ("Turkey_Tu-22M3_AI", TURKEY / "Airforce" / "Turkey_Tu-22M3_AI.ini"),
    ]:
        block = clone_identity(
            ru,
            old_object="Patch_Russia_Tu22M3",
            new_object=obj,
            old_side="Russia",
            new_side="Turkey",
            display=f"OBJECT:{obj}",
        )
        block = re.sub(r"DisplayName\s*=\s*\S+", f"DisplayName = OBJECT:{obj}", block, count=1)
        block = set_weaponset_tu22(block)
        # Ensure Turkey airbase prereq if present pattern
        if "Prerequisites" not in block:
            block = re.sub(
                r"(^\s*Side\s*=\s*Turkey\s*$)",
                r"\1\n  Prerequisites\n    Object = Turkey_AdvancedAirBase\n  End",
                block,
                count=1,
                flags=re.M,
            )
        write(path, block)
        log.append(f"Rebuilt {obj} from Patch_Russia_Tu22M3 + Russia_Weapon_Kh32_Tu22M3")


def strip_custom_weapon_objects(log: list[str]) -> None:
    # Empty WeaponObjects — do not create new Objects
    write(
        TURKEY / "Turkey_WeaponObjects.ini",
        "; SPECTER TURKEY FACTION FULL RESET\n"
        "; All broken Turkey custom weapon Objects removed.\n"
        "; Units now reference existing USA/China/Russia weapons only.\n"
        "; Do not add new weapon Objects here.\n",
    )
    log.append("Cleared Turkey_WeaponObjects.ini (removed all custom Objects)")

    # Clear Projectiles
    proj_dir = TURKEY / "Projectiles"
    if proj_dir.is_dir():
        for p in sorted(proj_dir.glob("*.ini")):
            write(
                p,
                f"; SPECTER TURKEY FACTION FULL RESET\n"
                f"; Removed broken custom projectile Object formerly in {p.name}\n"
                f"; Use existing America_/Russia_/China_ Projectile_* Objects instead.\n",
            )
            log.append(f"Cleared projectile file {p.name}")

    # Keep Turkey_Shells minimal stub without custom if present
    shells = TURKEY / "Turkey_Shells.ini"
    if shells.exists():
        write(
            shells,
            "; SPECTER TURKEY FACTION FULL RESET\n"
            "; Custom Turkey shells removed — use stock USA/Russia munitions.\n",
        )
        log.append("Cleared Turkey_Shells.ini")


def keep_systems_non_weapon(log: list[str]) -> None:
    """Keep only non-weapon system Objects still required by buildings/OCL/command."""
    systems = TURKEY / "Turkey_Systems.ini"
    if not systems.exists():
        return
    text = systems.read_text(encoding="utf-8", errors="replace")
    keep = {
        "TurkeySystemSpecialPowerShortcut",
        "Turkey_GenericFakeRider1_Default_Rank",
        "Turkey_GenericFakeRider2_Default_Rank",
        "Turkey_HussienResearchObject",
        "Turkey_AbbasResearchObject",
        "Turkey_92N6EResearchObject",
        "Turkey_Mig25RB_Radar",
        "Turkey_255mmAl-FawCannon",
    }
    # Extract Object blocks with nested End matching by scanning lines
    lines = text.splitlines(keepends=True)
    blocks: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^Object\s+(\S+)\s*$", lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        start = i
        depth = 0
        i += 1
        # Count End vs module starts roughly: every line that is exactly 'End' or '  End'
        # Generals INI: Object ... End closes object; nested modules also End.
        # Use depth: +1 for lines matching ^\s*(Draw|Behavior|Body|ArmorSet|WeaponSet|LocomotorSet|ConditionState|DefaultConditionState|Prerequisites|UnitSpecificSounds|AttackContactPoint|ClientUpdate|FireWeaponWhenDamagedBehavior)\b
        # Simpler approach: find matching End by tracking indent-less structure — use stack of 'openers'
        openers = re.compile(
            r"^\s*(Draw|Behavior|Body|ArmorSet|WeaponSet|Prerequisites|UnitSpecificSounds|"
            r"ConditionState|DefaultConditionState|ClientUpdate|Geometry\w*|Turret|"
            r"ProductionUpdate|FireWeaponWhenDamagedBehavior)\b"
        )
        # Actually simplest: read until we see an End at column 0
        while i < len(lines):
            if re.match(r"^End\s*$", lines[i]):
                i += 1
                break
            i += 1
        block = "".join(lines[start:i])
        blocks.append((name, block))

    kept = [b for n, b in blocks if n in keep]
    removed = [n for n, _ in blocks if n not in keep]
    out = (
        "; SPECTER TURKEY FACTION FULL RESET — Turkey_Systems\n"
        "; Kept only non-weapon system Objects still referenced by buildings/OCL/commands.\n"
        "; Removed weapon-like / unused system Objects.\n\n"
    )
    out += "\n".join(kept)
    if not out.endswith("\n"):
        out += "\n"
    write(systems, out)
    log.append(f"Turkey_Systems.ini kept {len(kept)} objects, removed {len(removed)}")


def retarget_all_ini(log: list[str]) -> None:
    total_w = total_p = 0
    # Unit files under Turkey
    for p in sorted(TURKEY.rglob("*.ini")):
        if p.name in {"Turkey_WeaponObjects.ini", "Turkey_Shells.ini"}:
            continue
        if p.parent.name == "Projectiles":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        text2, nw = retarget_weapons_in_text(text)
        if nw:
            write(p, text2)
            total_w += nw
            log.append(f"Retargeted {nw} weapon refs in {p.relative_to(TURKEY)}")

    # Weapon definition files
    for name in [
        "Weapon_Turkey.ini",
        "Weapon_Turkey_Phase4.ini",
        "Weapon_PhaseI_TurkeyFixes.ini",
        "Weapon_VerificationFixes.ini",
    ]:
        p = DATA / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        text2, np_ = retarget_projectiles_in_text(text)
        # Also rewrite Weapon names used elsewhere? keep names but fix projectiles
        if np_:
            write(p, text2)
            total_p += np_
            log.append(f"Retargeted {np_} ProjectileObject refs in {name}")

    # OCL Turkey — retarget object names that pointed at removed shells
    ocl = DATA / "ObjectCreationList_Turkey.ini"
    if ocl.exists():
        text = ocl.read_text(encoding="utf-8", errors="replace")
        text2 = text
        for old, new in [
            ("Turkey_255mmShell", "America_Projectile_Tomahawk_Strategic"),
            ("Turkey_Fab-250", "America_Projectile_JASSM_F15E"),
            ("Turkey_Fab-100", "America_Projectile_JASSM_F15E"),
        ]:
            text2 = text2.replace(old, new)
        if text2 != text:
            write(ocl, text2)
            log.append("Retargeted ObjectCreationList_Turkey.ini custom shell refs")

    log.append(f"TOTAL unit weapon retargets: {total_w}")
    log.append(f"TOTAL projectile retargets: {total_p}")


def stub_turkey_weapon_ini(log: list[str]) -> None:
    """Replace Turkey weapon INI files with stubs that only alias to stock weapons.

    Do not create new weapon Objects. Keep Weapon *names* that other INIs may still
    reference, but each Weapon body only uses existing ProjectileObjects / FX.
    """
    # After unit retargets, most Turkey_Weapon_* should be unused. Still provide
    # safe aliases so any missed reference cannot NULL-crash.
    aliases = [
        ("Turkey_Weapon_AIM120D_F16Block70", "AIM120D_BVR_MRAAM_F22A", "America_Projectile_AIM120C_F16V"),
        ("Turkey_Weapon_AIM120C_F16V", "America_Weapon_AIM120C_F16V", "America_Projectile_AIM120C_F16V"),
        ("Turkey_Weapon_AAM_Medium", "America_Weapon_AIM120C_F16V", "America_Projectile_AIM120C_F16V"),
        ("Turkey_Weapon_AAM_Short", "AIM-9X_F16C", "America_Projectile_AIM9X_F35"),
        ("Turkey_Weapon_Goktug_KAAN", "America_Weapon_AIM120C_F16V", "America_Projectile_AIM120C_F16V"),
        ("Turkey_Weapon_ATGM", "4x_AGM114N_Mq9", "America_Projectile_AntiDrone"),
        ("Turkey_Weapon_Altay_ATGM", "9M113_Konkurs", "America_Projectile_AntiDrone"),
        ("Turkey_Weapon_Cruise", "America_Weapon_JASSM_F15E", "America_Projectile_JASSM_F15E"),
        ("Turkey_Weapon_BallisticStrike", "America_Weapon_Tomahawk_Strategic", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_Tayfun", "America_Weapon_Tomahawk_Strategic", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_Fab250", "GBU_31V1_JDAM_F16C", "America_Projectile_JASSM_F15E"),
        ("Turkey_Weapon_KH25ML", "Russia_Weapon_Kh32_Tu22M3", "Russia_Projectile_Kh32_Tu22M3"),
        ("Turkey_Weapon_S8Rocket", "6X_80mm_S8_Rockets_MI28N", "Russia_Projectile_R77_Su35"),
        ("Turkey_Weapon_SAM", "Russia_Weapon_S400", "Russia_Projectile_S400"),
        ("Turkey_Weapon_SHORAD", "Russia_Weapon_Buk", "Russia_Projectile_Buk"),
        ("Turkey_Weapon_MD", "America_Weapon_THAAD", "America_Projectile_THAAD"),
        ("Turkey_Weapon_ADSAM", "America_Weapon_Patriot", "America_Projectile_Patriot"),
        ("Turkey_Weapon_AntiDrone", "America_Weapon_AntiDrone", "America_Projectile_AntiDrone"),
        ("Turkey_Weapon_TankAP", "9M113_Konkurs", "America_Projectile_AntiDrone"),
        ("Turkey_Weapon_MLRS_Semi", "America_Weapon_PrSM", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_MLRS_Salvo", "America_Weapon_PrSM", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_MLRS_Warhead", "America_Weapon_PrSM", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_TRG230_Salvo", "America_Weapon_PrSM", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_TRG230_HE", "America_Weapon_PrSM", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_AbbasMissile", "America_Weapon_Tomahawk_Strategic", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_Weapon_AbbasICBM_AI", "America_Weapon_Tomahawk_Strategic", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_AlAbidMissileWeapon", "America_Weapon_Tomahawk_Strategic", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_HussieanMissileWeapon", "America_Weapon_Tomahawk_Strategic", "America_Projectile_Tomahawk_Strategic"),
        ("Turkey_HussieanMissileWeapon_AI", "America_Weapon_Tomahawk_Strategic", "America_Projectile_Tomahawk_Strategic"),
    ]

    def make_weapon(name: str, proj: str) -> str:
        # Minimal Weapon body cloned from FactionExpansion pattern
        return (
            f"Weapon {name}\n"
            f"  ; FULL RESET alias — ProjectileObject is existing stock/FactionExpansion\n"
            f"  PrimaryDamage = 50.0\n"
            f"  PrimaryDamageRadius = 5.0\n"
            f"  AttackRange = 250.0\n"
            f"  WeaponSpeed = 99999.0\n"
            f"  ProjectileObject = {proj}\n"
            f"  FireFX = None\n"
            f"  ProjectileDetonationFX = FX_LightAAMImpact\n"
            f"  FireSound = RaptorJetMissileWeapon\n"
            f"  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS\n"
            f"  DelayBetweenShots = 1000\n"
            f"  ClipSize = 0\n"
            f"  ClipReloadTime = 0\n"
            f"End\n\n"
        )

    body = (
        "; SPECTER TURKEY FACTION FULL RESET — Weapon_Turkey.ini\n"
        "; Alias-only weapons. ProjectileObjects are existing USA/China/Russia defs.\n"
        "; No new weapon Objects created.\n\n"
    )
    for name, _stock, proj in aliases:
        body += make_weapon(name, proj)
    write(DATA / "Weapon_Turkey.ini", body)
    log.append(f"Rewrote Weapon_Turkey.ini as {len(aliases)} safe aliases")

    # PhaseI / Phase4 → thin aliases too
    # Avoid duplicate Weapon names — PhaseI/Phase4 content folded into Weapon_Turkey.ini
    write(
        DATA / "Weapon_PhaseI_TurkeyFixes.ini",
        "; SPECTER TURKEY FACTION FULL RESET — PhaseI Turkey weapon fixes\n"
        "; Content folded into Weapon_Turkey.ini aliases (no duplicate Weapon names).\n",
    )
    log.append("Stubbed Weapon_PhaseI_TurkeyFixes.ini (no duplicate weapons)")

    write(
        DATA / "Weapon_Turkey_Phase4.ini",
        "; SPECTER TURKEY FACTION FULL RESET — Phase4 Turkey weapons\n"
        "; Content folded into Weapon_Turkey.ini aliases (no duplicate Weapon names).\n",
    )
    log.append("Stubbed Weapon_Turkey_Phase4.ini (no duplicate weapons)")

    # Fix VerificationFixes Turkey Fab-100 weapon projectile
    vf = DATA / "Weapon_VerificationFixes.ini"
    if vf.exists():
        text = vf.read_text(encoding="utf-8", errors="replace")
        text2, n = re.subn(
            r"(Weapon\s+4x_Turkey_Fab-100_CenterRack_Mig23BN\b.*?ProjectileObject\s*=\s*)\S+",
            r"\1America_Projectile_JASSM_F15E",
            text,
            count=1,
            flags=re.S,
        )
        if n:
            write(vf, text2)
            log.append("Retargeted 4x_Turkey_Fab-100_CenterRack_Mig23BN projectile")


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    log.append("TURKEY FACTION FULL RESET")
    log.append(f"Turkey root: {TURKEY}")

    rebuild_aircraft(log)
    retarget_all_ini(log)
    stub_turkey_weapon_ini(log)
    strip_custom_weapon_objects(log)
    keep_systems_non_weapon(log)

    REPORT.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")
    for line in log:
        print(" -", line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
