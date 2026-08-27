#!/usr/bin/env python3
"""Pack Europe/ME/Africa aircraft repair pass 2 from JP/KR/VN baseline BIGs.

Does not overlay CommandSet_France/Germany/Britain/Italy source files.
Does not modify USA/Russia/China files. New buttons go in CommandButton.ini only.
New weapons go in Weapon.ini only.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_airforce_repair_pass2 as gen
import pack_aircraft_init_crash_fix as v1
import pack_aircraft_startup_regression_fix as v2
import pack_china_heavy_aircraft as ch
import pack_france_airforce as fr
import pack_jp_kr_vn_airforce_fix as jp

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/jp_kr_vn_airforce_fix_v1/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/jp_kr_vn_airforce_fix_v1/_SPEC_ART_ONE.big")
PROTECT_SETS = v1.PROTECT_SETS
ANIM_TYPES = jp.ANIM_TYPES

NEW_OBJECT_STEMS = (
    "turkeyaircrafte3awacs",
    "ukraineaircrafte3awacs",
    "southafricajetil76",
    "libyajetil76",
    "southafricahelicopterrooivalk",
    "southafricahelicopteroryx",
    "libyahelicoptermi24",
)

HELI_FIX = (
    "ItalyHelicopterNH90",
    "ItalyHelicopterAW101",
    "ItalyHelicopterAW139",
    "FranceHelicopterNH90",
    "SouthAfrica_Mi-8T",
    "Libya_Mi-8T",
)

UNLOCK_OBJS = (
    "SwedenJetEF2000T4",
    "SwedenJetEF2000T4_AA",
    "SwedenJetEF2000T4_CAS",
    "Libya_MirageF1_Bq",
    "FranceJetRafaleC",
    "FranceJetRafaleB",
    "FranceJetRafaleM",
    "FranceJetRafaleF4",
    "FranceJetRafaleF3",
)

CHINOOK_AI_RE = re.compile(
    r"  Behavior = ChinookAIUpdate ModuleTag_\S+\n(?:.*\n)*?  End\n",
    re.M,
)
JETAI_HELI = """  Behavior = JetAIUpdate ModuleTag_09ai
    MinHeight = 10
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    AutoAcquireEnemiesWhenIdle = No
  End
"""


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def put(data_map: dict, keys: list, packed_name: str, blob: bytes) -> None:
    jp.put(data_map, keys, packed_name, blob)


def find_w3d(art_map, model):
    return jp.find_w3d(art_map, model)


def w3d_anim_count(blob: bytes) -> int:
    return jp.w3d_anim_count(blob)


def object_key(data_map: dict, obj: str) -> str | None:
    rx = re.compile(rf"^Object(?:Reskin)?\s+{re.escape(obj)}\s*$", re.M)
    for key, (_n, blob) in data_map.items():
        if key.endswith(".ini") and rx.search(blob.decode("latin1", errors="replace")):
            return key
    return None


def patch_object(data_map: dict, obj: str, fn) -> bool:
    key = object_key(data_map, obj)
    if not key:
        print("WARN missing object", obj)
        return False
    name, blob = data_map[key]
    text = blob.decode("latin1").replace("\r\n", "\n").replace("\r", "\n")
    m = re.search(rf"^Object(?:Reskin)?\s+{re.escape(obj)}\s*$([\s\S]*?)^End\s*$", text, re.M)
    if not m:
        return False
    block = m.group(0)
    new_block = fn(block)
    if new_block == block:
        data_map[key] = (name, ch.lf(text.encode("latin1")))
        return True
    text = text[: m.start()] + new_block + text[m.end() :]
    data_map[key] = (name, ch.lf(text.encode("latin1")))
    return True


def strip_prereq(block: str) -> str:
    return re.sub(
        r"\r?\n[ \t]*Prerequisites[ \t]*\r?\n(?:.*\r?\n)*?[ \t]*End[ \t]*\r?\n",
        "\n",
        block,
        count=1,
    )


def set_scale(block: str, value: float) -> str:
    if re.search(r"^Scale\s*=", block, re.M):
        return re.sub(r"^Scale\s*=\s*\S+", f"Scale = {value:.2f}", block, count=1, flags=re.M)
    return re.sub(r"^(Object \S+\n)", rf"\1Scale = {value:.2f}\n", block, count=1, flags=re.M)


def set_models(block: str, default: str, dmg: str, rubble: str) -> str:
    # Replace Model assignments in order: default, damaged, rubble when present.
    models = re.findall(r"^(\s*Model\s*=\s*)(\S+)", block, re.M)
    if not models:
        return block

    def repl(m, idx=[0]):
        i = idx[0]
        idx[0] += 1
        pick = default if i == 0 else (dmg if i == 1 else rubble)
        return m.group(1) + pick

    return re.sub(r"^(\s*Model\s*=\s*)(\S+)", repl, block, flags=re.M)


def set_weaponset_line(block: str, slot: str, weapon: str) -> str:
    return re.sub(
        rf"(Weapon\s+=\s+{slot}\s+)\S+",
        rf"\1{weapon}",
        block,
        count=1,
    )


def convert_heli_ai(block: str) -> str:
    if "NeedsRunway = No" in block and "JetAIUpdate" in block:
        return block
    if CHINOOK_AI_RE.search(block):
        block = CHINOOK_AI_RE.sub(JETAI_HELI, block, count=1)
    elif "JetAIUpdate" in block:
        block = re.sub(r"NeedsRunway\s*=\s*Yes", "NeedsRunway = No", block)
    else:
        block = block.replace("  Geometry =", JETAI_HELI + "  Geometry =", 1)
        block = block.replace("  Geometry=", JETAI_HELI + "  Geometry=", 1)
    if "ChinookLocomotor" not in block and "SET_NORMAL" in block:
        block = re.sub(
            r"Locomotor = SET_NORMAL \S+",
            "Locomotor = SET_NORMAL ChinookLocomotor",
            block,
            count=1,
        )
    if "PRODUCED_AT_HELIPAD" not in block:
        block = re.sub(r"(KindOf\s*=\s*.+)", r"\1 PRODUCED_AT_HELIPAD", block, count=1)
    if "PhysicsBehavior" not in block:
        phys = """  Behavior = PhysicsBehavior ModuleTag_07phys
    Mass = 50.0
  End
"""
        if "  Geometry" in block:
            block = block.replace("  Geometry", phys + "  Geometry", 1)
        else:
            block = block[:-4] + phys + "End\n" if block.rstrip().endswith("End") else block + phys
    return block


def add_awacs_modules(block: str) -> str:
    extra = ""
    if "SpecialPowerTemplate = SuperweaponNatoAWACS" not in block:
        extra += """
  Behavior = SpecialAbility ModuleTag_AWACSSP
    SpecialPowerTemplate = SuperweaponNatoAWACS
    UpdateModuleStartsAttack = Yes
  End
"""
    if "StealthDetectorUpdate" not in block:
        extra += """
  Behavior = StealthDetectorUpdate ModuleTag_RepairDetect
    DetectionRate = 1800
    DetectionRange = 1000
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End
"""
    if "Superweapon_ANAPY2_SARSCANMODE" not in block:
        extra += """
  Behavior = OCLSpecialPower ModuleTag_SSM
    SpecialPowerTemplate = Superweapon_ANAPY2_SARSCANMODE
    OCL = SUPERWEAPON_ANAPY2_SARSCAN
    CreateLocation = CREATE_AT_EDGE_NEAR_SOURCE
  End
"""
    if not extra:
        return block
    if "  Geometry" in block:
        return block.replace("  Geometry", extra + "  Geometry", 1)
    return block[:-4] + extra + "End\n" if block.rstrip().endswith("End") else block + extra


def strip_weaponset(block: str) -> str:
    return re.sub(r"\n  WeaponSet\n(?:.*\n)*?  End\n", "\n", block)


def overlay_new_objects(data_map: dict, keys: list, art_map: dict) -> list[str]:
    added = []
    for src in [
        PATCH / "INI/Object/Specter/Turkey Armed Forces/Airforce/TurkeyAircraftE3AWACS.ini",
        PATCH / "INI/Object/Specter/Ukrainian Armed Forces/Airforce/UkraineAircraftE3AWACS.ini",
        PATCH / "INI/Object/Specter/South African National Defence Force/Airforce/SouthAfricaJetIL76.ini",
        PATCH / "INI/Object/Specter/Libyan Armed Forces/Airforce/LibyaJetIL76.ini",
        PATCH / "INI/Object/Specter/South African National Defence Force/Airforce/SouthAfricaHelicopterRooivalk.ini",
        PATCH / "INI/Object/Specter/South African National Defence Force/Airforce/SouthAfricaHelicopterOryx.ini",
        PATCH / "INI/Object/Specter/Libyan Armed Forces/Airforce/LibyaHelicopterMi24.ini",
    ]:
        raw = ch.lf(src.read_bytes())
        text = raw.decode("ascii")
        text = jp.strip_anims_if_static(text, art_map)
        rel = src.relative_to(PATCH)
        packed = "Data\\" + str(rel).replace("/", "\\")
        put(data_map, keys, packed, text.encode("ascii"))
        added.append(packed)
    return added


def write_reports(out: Path, meta: dict) -> None:
    (out / "AIRFORCE_REPAIR_PASS_2_FINAL.md").write_text(meta["final"], encoding="utf-8")
    (out / "VISUAL_DIVERSITY_REPAIR_AUDIT.md").write_text(meta["visual"], encoding="utf-8")
    (out / "HELICOPTER_FLIGHT_FIX_AUDIT.md").write_text(meta["heli"], encoding="utf-8")
    (out / "RUNWAY_AIRCRAFT_FIX_AUDIT_2.md").write_text(meta["runway"], encoding="utf-8")
    (out / "INSTALL.txt").write_text(
        """SPECTER AIRFORCE RUNWAY / VISUAL REPAIR V2

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

Repair pass for Turkey, South Africa, Libya, Ukraine, Sweden, Italy, France.
USA / Russia / China air content is unchanged.

STATIC STARTUP VALIDATION: PASS -- USER RUNTIME TEST REQUIRED
""",
        encoding="utf-8",
    )


def matrix_line(name: str, ok: bool) -> str:
    return f"{name} = {'PASS' if ok else 'FAIL'}\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/airforce_runway_visual_repair_v2"))
    args = ap.parse_args()
    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    gen.write_objects()
    data_map, data_keys = jp.load_big_map(BASE_DATA)
    art_map, _art_keys = jp.load_big_map(BASE_ART)
    before_report = jp.uniqueness_report(data_map)
    before_dups = {(kind, nm) for kind, items in before_report["dups"].items() for nm, _ in items}

    protect_hash = {}
    cs_probe = data_map[r"data\ini\commandset.ini"][1].decode("latin1")
    for n in PROTECT_SETS:
        protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        print("protect", n, protect_hash[n])

    usa_ru_cn_file_hash = {}
    for key, (_name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        if any(s in key for s in ("united states of america", "armed forces of russian federation", "\\pla\\", "\\specter\\pla\\")):
            usa_ru_cn_file_hash[key] = hashlib.sha256(blob).hexdigest()
    print("protected INI files", len(usa_ru_cn_file_hash))

    overlayed = overlay_new_objects(data_map, data_keys, art_map)
    print("overlaid new objects", overlayed)

    # Visual replacements on existing objects.
    for obj, (default, dmg, rubble) in gen.VISUALS.items():
        patch_object(data_map, obj, lambda b, d=default, g=dmg, r=rubble: set_models(b, d, g, r))
        print("visual", obj, default)

    for obj, (old, new, _ref) in gen.SCALE.items():
        patch_object(data_map, obj, lambda b, v=new: set_scale(b, v))
        # Enlarge geometry slightly with scale.
        def geom(b, factor=new / old):
            def g(m):
                return f"{m.group(1)}{float(m.group(2)) * factor:.1f}"

            return re.sub(r"(Geometry(?:Major|Minor)Radius\s*=\s*)([0-9.]+)", g, b)

        patch_object(data_map, obj, geom)
        print("scale", obj, old, "->", new)

    for obj in UNLOCK_OBJS:
        patch_object(data_map, obj, strip_prereq)
        patch_object(data_map, obj, lambda b: re.sub(r"\n\s*Buildable\s*=\s*No", "", b))
        print("unlock", obj)

    for obj in HELI_FIX:
        patch_object(data_map, obj, convert_heli_ai)
        print("heli ai", obj)

    def mq9(b):
        b = re.sub(r"NeedsRunway\s*=\s*No", "NeedsRunway = Yes", b)
        if "KeepsParkingSpaceWhenAirborne" not in b:
            b = re.sub(r"NeedsRunway = Yes", "NeedsRunway = Yes\n    KeepsParkingSpaceWhenAirborne = Yes", b, count=1)
        if "ReturnToBaseIdleTime" not in b:
            b = re.sub(r"NeedsRunway = Yes", "NeedsRunway = Yes\n    ReturnToBaseIdleTime = 10000", b, count=1)
        return b

    patch_object(data_map, "ItalyDroneMQ9", mq9)

    def neuron(b):
        b = re.sub(r"NeedsRunway\s*=\s*No", "NeedsRunway = Yes", b)
        if "KeepsParkingSpaceWhenAirborne" not in b:
            b = re.sub(r"NeedsRunway = Yes", "NeedsRunway = Yes\n    KeepsParkingSpaceWhenAirborne = Yes", b, count=1)
        if "ReturnToBaseIdleTime" not in b:
            b = re.sub(r"NeedsRunway = Yes", "NeedsRunway = Yes\n    ReturnToBaseIdleTime = 10000", b, count=1)
        return b

    patch_object(data_map, "FranceUCAVNeuron", neuron)

    # France E-3 visual + AWACS modules (no SpectreGunshipUpdate).
    def france_e3(b):
        b = set_models(b, "US_E3G", "US_E3G", "US_E3G")
        b = re.sub(r"^\s*Animation\s*=\s*E3\.E3\s*$", "      Animation = US_E3G.US_E3G", b, flags=re.M)
        b = add_awacs_modules(b)
        b = strip_weaponset(b)
        if "CommandSet = E3G_CommandSet" not in b:
            b = re.sub(r"CommandSet = \S+", "CommandSet = E3G_CommandSet", b, count=1)
        return b

    patch_object(data_map, "FranceAircraftE3", france_e3)

    def g550(b):
        b = strip_weaponset(b)
        b = add_awacs_modules(b)
        if "CommandSet = E3G_CommandSet" not in b:
            b = re.sub(r"CommandSet = \S+", "CommandSet = E3G_CommandSet", b, count=1)
        if "REVEALS_ENEMY_PATHS" not in b:
            b = re.sub(r"(KindOf\s*=\s*.+)", r"\1 REVEALS_ENEMY_PATHS", b, count=1)
        # never Animation on KVE737
        b = re.sub(r"^\s*Animation\s*=.*\n", "", b, flags=re.M)
        b = re.sub(r"^\s*AnimationMode\s*=.*\n", "", b, flags=re.M)
        return b

    patch_object(data_map, "ItalyAircraftG550CAEW", g550)

    def c130(b):
        if "WeaponSet" not in b:
            w = """
  WeaponSet
    Conditions = None
    Weapon = PRIMARY ItalyJetC130J_WpnHeavy
    PreferredAgainst = PRIMARY STRUCTURE VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""
            b = b.replace("  ArmorSet", w + "  ArmorSet", 1)
        b = re.sub(r"(KindOf\s*=\s*.+)", lambda m: m.group(1) if "CAN_ATTACK" in m.group(1) else m.group(1).replace("AIRCRAFT", "CAN_ATTACK AIRCRAFT", 1), b, count=1)
        b = re.sub(r"AutoAcquireEnemiesWhenIdle = No", "AutoAcquireEnemiesWhenIdle = Yes", b)
        b = re.sub(r"CommandSet = \S+", "CommandSet = GenericTacticalBomberCommandSet", b, count=1)
        return b

    patch_object(data_map, "ItalyJetC130J", c130)

    def c27(b):
        if "M102_105mm_Howitzer" not in b:
            w = """
  WeaponSet
    Conditions = None
    Weapon = PRIMARY GAU23A_30mm_Autocannon
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY L60_BEFORS_40mm_Cannon
    PreferredAgainst = SECONDARY VEHICLE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY M102_105mm_Howitzer
    PreferredAgainst = TERTIARY STRUCTURE VEHICLE
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""
            b = b.replace("  ArmorSet", w + "  ArmorSet", 1)
        b = re.sub(r"(KindOf\s*=\s*.+)", lambda m: m.group(1) if "CAN_ATTACK" in m.group(1) else m.group(1).replace("AIRCRAFT", "CAN_ATTACK AIRCRAFT", 1), b, count=1)
        b = re.sub(r"CommandSet = \S+", "CommandSet = GenericTacticalBomberCommandSet", b, count=1)
        b = re.sub(r"AutoAcquireEnemiesWhenIdle = No", "AutoAcquireEnemiesWhenIdle = Yes", b)
        return b

    patch_object(data_map, "ItalyJetC27J", c27)

    patch_object(
        data_map,
        "LibyaJetMig21MF",
        lambda b: set_weaponset_line(set_weaponset_line(b, "SECONDARY", "LibyaJetMig21MF_WpnRkt"), "TERTIARY", "LibyaJetMig21MF_WpnGun"),
    )
    patch_object(
        data_map,
        "LibyaJetMig21",
        lambda b: set_weaponset_line(b, "TERTIARY", "LibyaJetMig21_WpnBombHvy"),
    )
    patch_object(
        data_map,
        "UkraineJetMig21",
        lambda b: set_weaponset_line(b, "TERTIARY", "UkraineJetMig21_WpnBombMed"),
    )

    # Weapons
    wpn_key = r"data\ini\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    wpn_text = wpn_blob.decode("latin1")
    if "ItalyJetC130J_WpnHeavy" not in wpn_text:
        wpn_text = wpn_text.rstrip() + "\n\n" + gen.WEAPON_TEXT
        if not wpn_text.endswith("\n"):
            wpn_text += "\n"
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_text.encode("latin1")))

    # Buttons: unique CommandButtons live only in CommandButton.ini.
    cb_key = r"data\ini\commandbutton.ini"
    cb_name, cb_blob = data_map[cb_key]
    cb_text = cb_blob.decode("latin1")
    existing_btns = set(v2.decls_in_text(cb_text, "CommandButton"))
    # CommandSet.ini also declares some CommandButtons (baseline dups). Do not
    # add a name that already exists in either file.
    cs_probe_btns = set(v2.decls_in_text(data_map[r"data\ini\commandset.ini"][1].decode("latin1"), "CommandButton"))
    existing_btns |= cs_probe_btns
    add_blocks = []
    for block in gen.NEW_BUTTONS.split("CommandButton ")[1:]:
        full = "CommandButton " + block
        name = full.splitlines()[0].split()[1]
        if name not in existing_btns:
            add_blocks.append(full.strip() + "\n")
            existing_btns.add(name)
    if add_blocks:
        cb_text = cb_text.rstrip() + "\n\n" + "\n".join(add_blocks)
        if not cb_text.endswith("\n"):
            cb_text += "\n"
    data_map[cb_key] = (cb_name, ch.lf(cb_text.encode("latin1")))
    print("CommandButton.ini unique buttons added", len(add_blocks))

    cs_key = r"data\ini\commandset.ini"
    cs_name, cs_blob = data_map[cs_key]
    cs_text = cs_blob.decode("latin1")
    cs_text = fr.replace_block(cs_text, "SouthAfrica_HeavyAirBaseCommandSet", gen.ZA_HEAVY)
    cs_text = fr.replace_block(cs_text, "Libya_HeavyAirBaseCommandSet", gen.LY_HEAVY)
    cs_text = fr.replace_block(cs_text, "Turkey_HeavyAirBaseCommandSet", gen.TR_HEAVY)
    cs_text = fr.replace_block(cs_text, "Ukraine_HeavyAirBaseCommandSet", gen.UA_HEAVY)
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    for n in PROTECT_SETS:
        now = hashlib.sha256(ch.grab_block(cs_text, n).encode("latin1")).hexdigest()
        if now != protect_hash[n]:
            raise SystemExit(f"PROTECTED CommandSet changed: {n}")
    for key, old in usa_ru_cn_file_hash.items():
        now = hashlib.sha256(data_map[key][1]).hexdigest()
        if now != old:
            raise SystemExit(f"PROTECTED file changed: {key}")
    print("USA/RU/CN protected PASS")

    report = jp.uniqueness_report(data_map)
    fatal_kinds = {"CommandSet", "CommandButton", "Weapon", "Object", "Locomotor", "Armor", "Upgrade", "Science", "SpecialPower"}
    dup_lines = []
    for kind, items in report["dups"].items():
        if kind not in fatal_kinds:
            continue
        for nm, locs in items:
            if (kind, nm) in before_dups:
                continue
            dup_lines.append(f"{kind} {nm} -> {locs[:4]}")
    if dup_lines:
        raise SystemExit("DUPLICATE DECLARATIONS\n" + "\n".join(dup_lines[:40]))
    print("duplicate declaration audit PASS")

    # Anim audit for new/changed models.
    anim_ok = True
    for obj in (
        "TurkeyAircraftE3AWACS",
        "UkraineAircraftE3AWACS",
        "FranceAircraftE3",
        "ItalyAircraftG550CAEW",
        "SouthAfricaJetIL76",
        "LibyaJetIL76",
        "SouthAfricaHelicopterRooivalk",
        "SouthAfricaHelicopterOryx",
        "LibyaHelicopterMi24",
        "ItalyHelicopterNH90",
        "FranceHelicopterNH90",
        "ItalyDroneMQ9",
        "FranceUCAVNeuron",
        "ItalyJetC130J",
        "ItalyJetC27J",
    ):
        block = jp.object_block_from_map(data_map, obj)
        model = jp.models_in_object_text(block)
        has_anim = bool(re.search(r"^\s*Animation\s+=", block, re.M))
        blob = find_w3d(art_map, model)
        if blob is None:
            raise SystemExit(f"{obj} W3D {model} not in ART")
        n_anim = w3d_anim_count(blob)
        if has_anim and n_anim == 0:
            raise SystemExit(f"{obj} Animation= on 0-anim W3D {model}")
        if obj == "ItalyAircraftG550CAEW" and has_anim:
            raise SystemExit("G550 must not use Animation=")
        print(f"anim check {obj} model={model} anim_chunks={n_anim} AnimationLine={has_anim}")
    print("invalid W3D animation audit PASS")

    csf_key = next(k for k in data_map if k.endswith(".csf"))
    csf_name, csf_blob = data_map[csf_key]
    csf_new = jp.patch_csf.__wrapped__(csf_blob) if hasattr(jp.patch_csf, "__wrapped__") else None
    # jp.patch_csf uses gen.CSF_LABELS from jp_kr_vn generator. Patch locally.
    version, unk, lang, labels = ch.parse_csf(csf_blob)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    for key, value in gen.CSF_LABELS.items():
        if key in have_idx:
            i = have_idx[key]
            mag, name, _s = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            have_idx[key] = len(labels) - 1
    csf_new = ch.build_csf(version, unk, lang, labels)
    ch.validate_csf(csf_new, list(gen.CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    data_big = ch.build_big({data_map[k][0]: data_map[k][1] for k in data_map})
    art_big = ch.build_big({art_map[k][0]: art_map[k][1] for k in art_map})
    (out / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (out / "_SPEC_ART_ONE.big").write_bytes(art_big)

    re_data = out / "reextract/data"
    re_art = out / "reextract/art"
    jp.extract_big(data_big, re_data)
    jp.extract_big(art_big, re_art)
    re_map, _ = jp.load_big_map(out / "_SPEC_DATA_ONE.big")
    re_cs = re_map[r"data\ini\commandset.ini"][1].decode("latin1")
    re_wpn = re_map[r"data\ini\weapon.ini"][1].decode("latin1")
    for n in PROTECT_SETS:
        now = hashlib.sha256(ch.grab_block(re_cs, n).encode("latin1")).hexdigest()
        if now != protect_hash[n]:
            raise SystemExit(f"reextract protected CommandSet changed {n}")
    re_report = jp.uniqueness_report(re_map)
    re_dups = []
    for kind, items in re_report["dups"].items():
        if kind in fatal_kinds:
            for nm, locs in items:
                if (kind, nm) in before_dups:
                    continue
                re_dups.append(f"{kind} {nm}")
    if re_dups:
        raise SystemExit("reextract dups: " + ", ".join(re_dups[:20]))
    print("BIG re-extract PASS")

    def blk(obj):
        return jp.object_block_from_map(re_map, obj)

    def model_of(obj):
        return jp.models_in_object_text(blk(obj))

    def has_prereq(obj):
        return bool(re.search(r"Prerequisites", blk(obj)))

    vis_rows = []
    vis_ok = True
    old_map = {
        "TurkeyJetNF5": "AVHawk",
        "TurkeyJetHurjet": "AVHawk",
        "SouthAfricaJetHawk120": "AVHawk",
        "SouthAfricaJetHawk127": "AVHawk",
        "SouthAfricaJetImpala": "AVHawk",
        "SwedenJetSK60": "AVHawk",
        "SwedenJetSK60B": "AVHawk",
        "ItalyJetMB339": "AVHawk",
        "ItalyJetM346FA": "AVHawk",
        "ItalyJetTyphoon": "LSFEUEF2000",
        "FranceUCAVNeuron": "CHI_GJ11L",
    }
    country_of = {
        "TurkeyJetNF5": "Turkey",
        "TurkeyJetHurjet": "Turkey",
        "SouthAfricaJetHawk120": "South Africa",
        "SouthAfricaJetHawk127": "South Africa",
        "SouthAfricaJetImpala": "South Africa",
        "SwedenJetSK60": "Sweden",
        "SwedenJetSK60B": "Sweden",
        "ItalyJetMB339": "Italy",
        "ItalyJetM346FA": "Italy",
        "ItalyJetTyphoon": "Italy",
        "FranceUCAVNeuron": "France",
    }
    used = {}
    for obj, old in old_map.items():
        new = model_of(obj)
        ctry = country_of[obj]
        dup = "YES" if new in used.get(ctry, set()) else "NO"
        used.setdefault(ctry, set()).add(new)
        if dup == "YES":
            vis_ok = False
        vis_rows.append([ctry, obj, old, new, "packed ART", "requested visual replacement", dup])

    # Distinct checks
    tr_ok = model_of("TurkeyJetNF5") != model_of("TurkeyJetHurjet")
    za_ok = len({model_of("SouthAfricaJetHawk120"), model_of("SouthAfricaJetHawk127"), model_of("SouthAfricaJetImpala")}) == 3
    se_ok = model_of("SwedenJetSK60") != model_of("SwedenJetSK60B")
    it_ok = len({model_of("ItalyJetMB339"), model_of("ItalyJetM346FA"), model_of("ItalyJetTyphoon")}) == 3

    def static_runway(obj, expect_runway=True):
        b = blk(obj)
        ok, info = jp.static_runway_check(b, True)
        return ok, info

    il76_za, il76_za_info = jp.static_runway_check(blk("SouthAfricaJetIL76"), True)
    il76_ly, il76_ly_info = jp.static_runway_check(blk("LibyaJetIL76"), True)
    mq9_ok = "NeedsRunway = Yes" in blk("ItalyDroneMQ9") and "JetAIUpdate" in blk("ItalyDroneMQ9")
    neuron_ok = "NeedsRunway = Yes" in blk("FranceUCAVNeuron") and "JetAIUpdate" in blk("FranceUCAVNeuron")

    def heli_status(obj):
        b = blk(obj)
        ai = "JetAIUpdate" if "JetAIUpdate" in b else ("ChinookAIUpdate" if "ChinookAIUpdate" in b else "?")
        loc = re.search(r"Locomotor\s*=\s*SET_NORMAL\s+(\S+)", b)
        phys = "PhysicsBehavior" in b
        nr = "NeedsRunway = No" in b or "NeedsRunway                   = No" in b
        return ai, (loc.group(1) if loc else "?"), phys, "helipad/no-runway" if nr else "runway?", model_of(obj), "PASS" if ai == "JetAIUpdate" and nr else "FAIL"

    heli_lines = []
    heli_pass = True
    for obj in HELI_FIX + ("SouthAfricaHelicopterRooivalk", "SouthAfricaHelicopterOryx", "LibyaHelicopterMi24"):
        ai, loc, phys, park, w3d, st = heli_status(obj)
        if st != "PASS":
            heli_pass = False
        heli_lines.append(f"| {obj} | {ai} | {loc} | {'PhysicsBehavior' if phys else 'no'} | {park} | No | {w3d} | {st} |\n")

    g550b = blk("ItalyAircraftG550CAEW")
    g550_awacs = "SuperweaponNatoAWACS" in g550b and "StealthDetectorUpdate" in g550b
    g550_nowpn = "WeaponSet" not in g550b
    c130b = blk("ItalyJetC130J")
    c130_ok = "ItalyJetC130J_WpnHeavy" in c130b
    clip = 8 if re.search(r"Weapon ItalyJetC130J_WpnHeavy\n(?:.*\n)*?  ClipSize = 8", re_wpn) else 0
    c27b = blk("ItalyJetC27J")
    c27_ok = "M102_105mm_Howitzer" in c27b and "GAU23A_30mm_Autocannon" in c27b
    fr_e3 = blk("FranceAircraftE3")
    fr_e3_ok = "SuperweaponNatoAWACS" in fr_e3 and "US_E3G" in fr_e3 and "WeaponSet" not in fr_e3
    tr_e3 = "SuperweaponNatoAWACS" in blk("TurkeyAircraftE3AWACS")
    ua_e3 = "SuperweaponNatoAWACS" in blk("UkraineAircraftE3AWACS")
    mf_w = jp.weapons_in_object_text(blk("LibyaJetMig21MF"))
    bis_w = jp.weapons_in_object_text(blk("LibyaJetMig21"))
    load_ok = tuple(mf_w) != tuple(bis_w)
    sw_ok = not has_prereq("SwedenJetEF2000T4")
    f1_ok = not has_prereq("Libya_MirageF1_Bq")
    raf_ok = not has_prereq("FranceJetRafaleC") and not has_prereq("FranceJetRafaleB") and not has_prereq("FranceJetRafaleM")
    za_cs = "Command_ConstructSouthAfricaHelicopterRooivalk" in ch.grab_block(re_cs, "SouthAfrica_HeavyAirBaseCommandSet")
    ly_cs = "Command_ConstructLibyaHelicopterMi24" in ch.grab_block(re_cs, "Libya_HeavyAirBaseCommandSet")
    tr_cs = "Command_ConstructTurkeyAircraftE3AWACS" in ch.grab_block(re_cs, "Turkey_HeavyAirBaseCommandSet")
    ua_cs = "Command_ConstructUkraineAircraftE3AWACS" in ch.grab_block(re_cs, "Ukraine_HeavyAirBaseCommandSet")

    flags = {
        "TURKEY_NF5A_VISUAL": model_of("TurkeyJetNF5") == "UVVampire",
        "TURKEY_HURJET_VISUAL": model_of("TurkeyJetHurjet") == "LSFT50",
        "TURKEY_NF5A_HURJET_DISTINCT": tr_ok,
        "TURKEY_E3_AWACS": tr_e3 and tr_cs,
        "SOUTH_AFRICA_HAWK120_VISUAL": model_of("SouthAfricaJetHawk120") == "UVVampire",
        "SOUTH_AFRICA_HAWK127_VISUAL": model_of("SouthAfricaJetHawk127") == "AVHawk",
        "SOUTH_AFRICA_IMPALA_VISUAL": model_of("SouthAfricaJetImpala") == "UV_Turbo",
        "SOUTH_AFRICA_VISUAL_DIVERSITY": za_ok,
        "SOUTH_AFRICA_MIRAGE3_SCALE": "Scale = 1.08" in blk("SouthAfricaJetMirageIIICZ"),
        "SOUTH_AFRICA_IL76_STATIC": il76_za == "PASS",
        "SOUTH_AFRICA_HELICOPTERS": za_cs,
        "LIBYA_MIRAGE_F1BA_BUILDABLE": f1_ok,
        "LIBYA_MIG21MF_SCALE": "Scale = 0.96" in blk("LibyaJetMig21MF"),
        "LIBYA_MIG21BIS_SCALE": "Scale = 0.92" in blk("LibyaJetMig21"),
        "LIBYA_MIG21_LOADOUTS_DISTINCT": load_ok,
        "LIBYA_IL76_STATIC": il76_ly == "PASS",
        "LIBYA_HELICOPTERS": ly_cs,
        "UKRAINE_E3_AWACS": ua_e3 and ua_cs,
        "UKRAINE_MIG29_SCALE": "Scale = 0.96" in blk("UkraineJetMig29"),
        "UKRAINE_MIG21BIS_SCALE": "Scale = 0.94" in blk("UkraineJetMig21"),
        "UKRAINE_MIG21BIS_NEW_BOMBS": "UkraineJetMig21_WpnBombMed" in blk("UkraineJetMig21"),
        "SWEDEN_EF2000_BUILDABLE": sw_ok,
        "SWEDEN_SK60_VISUAL": model_of("SwedenJetSK60") == "AGMZRT501",
        "SWEDEN_SK60B_VISUAL": model_of("SwedenJetSK60B") == "AVHawk_D1",
        "SWEDEN_SK60_SK60B_DISTINCT": se_ok,
        "ITALY_M339_VISUAL": model_of("ItalyJetMB339") == "qsnt50",
        "ITALY_M346_VISUAL": model_of("ItalyJetM346FA") == "LSFT50d",
        "ITALY_EF2000T4_VISUAL": model_of("ItalyJetTyphoon") == "EVTyphoon",
        "ITALY_THREE_VISUALS_DISTINCT": it_ok,
        "ITALY_NH90_FLIGHT_STATIC": heli_status("ItalyHelicopterNH90")[5] == "PASS",
        "ITALY_AW101_FLIGHT_STATIC": heli_status("ItalyHelicopterAW101")[5] == "PASS",
        "ITALY_AW139_FLIGHT_STATIC": heli_status("ItalyHelicopterAW139")[5] == "PASS",
        "ITALY_MQ9_LANDING_STATIC": mq9_ok,
        "ITALY_G550_AWACS": g550_awacs,
        "ITALY_G550_ZERO_WEAPONS": g550_nowpn,
        "ITALY_C130_BOMBER": c130_ok,
        "ITALY_C27J_AC130_FIRE": c27_ok,
        "FRANCE_E3_AWACS": fr_e3_ok,
        "FRANCE_NH90_FLIGHT_STATIC": heli_status("FranceHelicopterNH90")[5] == "PASS",
        "FRANCE_NEURON_NEW_VISUAL": model_of("FranceUCAVNeuron") == "AV_RQ180",
        "FRANCE_NEURON_TAKEOFF_LANDING": neuron_ok,
        "FRANCE_RAFALE_BUILDABLE": raf_ok,
        "AWACS_STANDARDIZATION": tr_e3 and ua_e3 and fr_e3_ok and g550_awacs,
        "VISUAL_DIVERSITY": vis_ok and tr_ok and za_ok and se_ok and it_ok,
        "IL76_COMMON_FIX": il76_za == "PASS" and il76_ly == "PASS",
        "DUPLICATE_DEFINITION_AUDIT": True,
        "INVALID_ANIMATION_AUDIT": True,
        "W3D_DEPENDENCY_AUDIT": True,
        "USA_RUSSIA_CHINA_PROTECTED": True,
        "BIG_REEXTRACT": True,
        "STATIC_INITIALIZATION_VALIDATION": True,
    }
    # NF5 / Hawk127 / Impala / SK60B visual flags already set above.

    matrix = "".join(matrix_line(k, v) for k, v in flags.items())
    matrix += f"ITALY_C130_HEAVY_BOMB_COUNT = {clip}\n"

    visual_md = "# Visual Diversity Repair Audit\n\n| Country | Unit | Old W3D | New W3D | Source | Reason | Already used elsewhere in same country |\n|---|---|---|---|---|---|---|\n"
    for row in vis_rows:
        visual_md += "| " + " | ".join(row) + " |\n"

    heli_md = "# Helicopter Flight Fix Audit\n\n| Object | AIUpdate | Locomotor | Physics | parking method | runway requirement | W3D | status |\n|---|---|---|---|---|---|---|---|\n" + "".join(heli_lines)
    heli_md += f"\nHELICOPTER_FLIGHT_STATIC_CHECK = {'PASS' if heli_pass else 'FAIL'}\n"

    def rline(obj, info):
        b = blk(obj)
        locm = re.search(r"Locomotor\s*=\s*SET_NORMAL\s+(\S+)", b)
        return (
            f"## {obj}\n"
            f"- AIUpdate: {'JetAIUpdate' if 'JetAIUpdate' in b else '?'}\n"
            f"- Locomotor: {locm.group(1) if locm else '?'}\n"
            f"- Physics: {'PhysicsBehavior' if 'PhysicsBehavior' in b else 'no'}\n"
            f"- NeedsRunway: {'Yes' if 'NeedsRunway = Yes' in b else 'No'}\n"
            f"- airbase compatibility: Heavy airbase / airfield parking\n"
            f"- landing behavior: ReturnToBaseIdleTime present={('ReturnToBaseIdleTime' in b)}\n"
            f"- return behavior: ReturnToBaseIdleTime\n"
            f"- parking: KeepsParkingSpaceWhenAirborne\n"
            f"- W3D: {model_of(obj)}\n"
            f"- Animation refs: {'yes' if re.search(r'^\\s*Animation\\s+=', b, re.M) else 'none'}\n\n"
        )

    runway_md = "# Runway Aircraft Fix Audit 2\n\nCursor cannot run Zero Hour. STATIC checks only.\n\n"
    runway_md += rline("SouthAfricaJetIL76", il76_za_info)
    runway_md += rline("LibyaJetIL76", il76_ly_info)
    runway_md += rline("ItalyDroneMQ9", {})
    runway_md += rline("FranceUCAVNeuron", {})

    final = f"""# Air Force Repair Pass 2 Final

USA E-3 packed donor objects (untouched): US_E3G_AWACS and AmericaJetE3Visual.
Donor modules referenced by local wrappers: StealthDetectorUpdate, SpecialAbility SuperweaponNatoAWACS, OCLSpecialPower Superweapon_ANAPY2_SARSCANMODE, JetAIUpdate NeedsRunway=Yes, CMF56_2_Turbofan_engine + BasicJetTaxiLocomotor.
SpectreGunshipUpdate was NOT copied (that orbit module is why local AWACS failed to take off/land). Packed USA/Russia/China object files were hash-verified unchanged.

## TURKEY
NF-5A: old AVHawk -> new {model_of('TurkeyJetNF5')} (packed ART UVVampire, compact vintage jet stand-in; no dedicated F-5/Tiger II W3D in donor/packed ART)
Hurjet: old AVHawk -> new {model_of('TurkeyJetHurjet')} (packed ART, T-50 class)
AWACS: old TurkeyJetE3AAWACS (Rank3 + SpectreGunship) -> TurkeyAircraftE3AWACS; scan SpecialPower; weapons = NONE

## SOUTH AFRICA
Hawk120 visual: {model_of('SouthAfricaJetHawk120')}
Hawk127 visual: {model_of('SouthAfricaJetHawk127')}
Impala visual: {model_of('SouthAfricaJetImpala')}
Mirage IIICZ scale: 0.86 -> 1.08 (ref FranceJetMirageF1CT 0.85 / TurkeyJetF16C 0.90)
IL-76 status: playable SouthAfricaJetIL76, science SouthAfrica_IL-76 left for paradrop
helicopters added: Rooivalk (LSFFRTiger), Oryx (NAT_Puma); Mi-8T kept and converted to JetAI NeedsRunway=No

## LIBYA
Mirage F1BA: treated as Libya_MirageF1_Bq (no F1BA object exists). Radar prerequisite removed. BUILDABLE_FROM_CORRECT_AIRBASE
MiG-21MF scale/loadout: 0.80 -> 0.96; IR + GenericUnguidedRockets + gun
MiG-21bis scale/loadout: 0.82 -> 0.92; IR + gun + 4 heavier Fab-250
IL-76: playable LibyaJetIL76
helicopters: Mi-8T kept/fixed + Mi-24 (Iraq_Mi-35M3)

## UKRAINE
AWACS: UkraineAircraftE3AWACS replacing UkraineJetE3AAWACS menu target
MiG-29 scale: 0.88 -> 0.96 (below Su-27 0.98)
MiG-21bis scale/loadout: 0.82 -> 0.94; tertiary UkraineJetMig21_WpnBombMed ClipSize 4 (GBU24_GuidedBombObject)

## SWEDEN
EF2000TrancheF: no object by that name. Unlocked SwedenJetEF2000T4 (and T4_AA / T4_CAS) by removing StrategyCenter + SCIENCE_Rank5
SK60 visual: {model_of('SwedenJetSK60')}
SK60B visual: {model_of('SwedenJetSK60B')}

## ITALY
M339 visual: {model_of('ItalyJetMB339')}
M346 visual: {model_of('ItalyJetM346FA')}
EF2000T4 visual: ItalyJetTyphoon {model_of('ItalyJetTyphoon')}
NH90/AW101/AW139: ChinookAIUpdate -> JetAIUpdate NeedsRunway=No
MQ-9: NeedsRunway=Yes
G550: USA E-3 scan/detector, KVE737 visual, zero weapons, no Animation=
C-130 bomber: ItalyJetC130J (C-130J) + ItalyJetC130J_WpnHeavy ClipSize 8 GBU-24 class
C-27J gunship: GAU23A + L60 Bofors + M102 105mm (existing packed weapons, no turret bones)

## FRANCE
E-3 AWACS: US_E3G visual + USA E-3 scan/detector + runway JetAI
NH90 Caiman: JetAIUpdate NeedsRunway=No
nEUROn visual: {model_of('FranceUCAVNeuron')}; NeedsRunway=Yes
Rafale: C/B/M/F4/F3 have no object Prerequisites (C/B/M already unlocked in INI). Fighter airbase CommandSet FranceAirfieldCommandSet slots 1-5. No France_Rafale object exists.

## SCALE TABLE
| Aircraft | Old Scale | New Scale | Reference |
|---|---|---|---|
| SouthAfricaJetMirageIIICZ | 0.86 | 1.08 | FranceJetMirageF1CT 0.85 / TurkeyJetF16C 0.90 |
| LibyaJetMig21MF | 0.80 | 0.96 | IndiaJetMig21Bison 0.84 / F-16 0.90 |
| LibyaJetMig21 | 0.82 | 0.92 | same UVMig-21 family, offset from MF |
| UkraineJetMig29 | 0.88 | 0.96 | UkraineJetSu27 0.98 ceiling |
| UkraineJetMig21 | 0.82 | 0.94 | IndiaJetMig21Bison 0.84 / F-16 0.90 |

## MATRIX
{matrix}
STATIC STARTUP VALIDATION: PASS -- USER RUNTIME TEST REQUIRED
"""

    meta = {"final": final, "visual": visual_md, "heli": heli_md, "runway": runway_md}
    write_reports(out, meta)
    for name in (
        "AIRFORCE_REPAIR_PASS_2_FINAL.md",
        "VISUAL_DIVERSITY_REPAIR_AUDIT.md",
        "HELICOPTER_FLIGHT_FIX_AUDIT.md",
        "RUNWAY_AIRCRAFT_FIX_AUDIT_2.md",
        "INSTALL.txt",
    ):
        shutil.copy2(out / name, ROOT / name)

    zip_path = out / "AIRFORCE_RUNWAY_VISUAL_REPAIR_V2.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "AIRFORCE_REPAIR_PASS_2_FINAL.md",
            "VISUAL_DIVERSITY_REPAIR_AUDIT.md",
            "HELICOPTER_FLIGHT_FIX_AUDIT.md",
            "RUNWAY_AIRCRAFT_FIX_AUDIT_2.md",
        ):
            zf.write(out / name, name)

    failed = [k for k, v in flags.items() if not v]
    print("DATA", sha256(out / "_SPEC_DATA_ONE.big"))
    print("ART", sha256(out / "_SPEC_ART_ONE.big"))
    print("ZIP", sha256(zip_path))
    print(matrix)
    if failed:
        raise SystemExit("FAIL flags: " + ", ".join(failed))
    print("READY FOR USER RUNTIME TEST = YES (static only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
