#!/usr/bin/env python3
"""Patch SPE _SPEC_DATA_ONE.big for Global Market ABM intercept / radar ID.

Reads the original SPE BIG, replaces inner INI bytes in place, adds ZZZZ
last-win extra files, and writes a new BIGF. Does not touch SPE.rar volumes.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


def read_big(path: Path) -> tuple[list[tuple[str, int, int]], bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def must_replace(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 occurrence of unique block, found {n}")
    return text.replace(old, new)


def decode(raw: bytes) -> tuple[str, str]:
    nl = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("latin1"), nl


def encode(text: str) -> bytes:
    return text.encode("latin1")


OCL_ZZZZ = r"""
; SPECTER last-win inside _SPEC_DATA_ONE.big.
; Sorts after ObjectCreationList.ini and ObjectCreationList_SpecterABMDedicatedRadar.ini.
; Global Market ABM deploy must spawn ABM FCS, not AA FCS.

ObjectCreationList OCL_S500_Deployed_ABM
  CreateObject
    ObjectNames           = S500_FireControlSystem_ABM
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = S400R_FireControlSystem_AUM
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = RussiaVehicleS500CombatMode
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = AirdefenseLinkRestarter
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End

ObjectCreationList OCL_THAAD_Deployed_ABM
  CreateObject
    ObjectNames           = THAAD_FireControlSystem_ABM
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = S400R_FireControlSystem_AUM
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = US_THAAD_CombatMode
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = AirdefenseLinkRestarter
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End

ObjectCreationList OCL_Arrow_Deployed_ABM
  CreateObject
    ObjectNames           = THAAD_FireControlSystem_ABM
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = S400R_FireControlSystem_AUM
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = Israel_Arrow_CombatMode
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = AirdefenseLinkRestarter
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End
""".lstrip()


def patch_weapon_ini(text: str) -> str:
    text = must_replace(
        text,
        "Weapon THAADMissile_ABM\n"
        "  PrimaryDamage              = 2000.0\n"
        "  PrimaryDamageRadius        = 5.0\n"
        "  SecondaryDamage            = 5.0\n"
        "  SecondaryDamageRadius      = 40\n"
        "  AttackRange                = 1700\n"
        "  MinimumAttackRange         = 600\n"
        "  DamageType                 = FALLING\n",
        "Weapon THAADMissile_ABM\n"
        "  PrimaryDamage              = 2000.0\n"
        "  PrimaryDamageRadius        = 5.0\n"
        "  SecondaryDamage            = 5.0\n"
        "  SecondaryDamageRadius      = 40\n"
        "  AttackRange                = 1700\n"
        "  MinimumAttackRange         = 600\n"
        "  DamageType                 = CRUSH\n",
        "THAADMissile_ABM",
    )
    text = must_replace(
        text,
        "Weapon 3x_LRSAM_40N6KMissile_ABM\n"
        "  PrimaryDamage              = 2000\n"
        "  PrimaryDamageRadius        = 0.1\n"
        "  SecondaryDamage            = 0.1\n"
        "  SecondaryDamageRadius      = 0.1\n"
        "  AttackRange                = 1800\n"
        "  MinimumAttackRange         = 450\n"
        "  DamageType                 = FALLING\n",
        "Weapon 3x_LRSAM_40N6KMissile_ABM\n"
        "  PrimaryDamage              = 2000\n"
        "  PrimaryDamageRadius        = 0.1\n"
        "  SecondaryDamage            = 0.1\n"
        "  SecondaryDamageRadius      = 0.1\n"
        "  AttackRange                = 1800\n"
        "  MinimumAttackRange         = 450\n"
        "  DamageType                 = CRUSH\n",
        "3x_LRSAM_40N6KMissile_ABM",
    )
    text = must_replace(
        text,
        "Weapon 77H6Missile_ABM\n"
        "  PrimaryDamage              = 2000\n"
        "  PrimaryDamageRadius        = 0.1\n"
        "  SecondaryDamage            = 0.1\n"
        "  SecondaryDamageRadius      = 0.1\n"
        "  AttackRange                = 2000\n"
        "  MinimumAttackRange         = 450\n"
        "  DamageType                 = FALLING\n",
        "Weapon 77H6Missile_ABM\n"
        "  PrimaryDamage              = 2000\n"
        "  PrimaryDamageRadius        = 0.1\n"
        "  SecondaryDamage            = 0.1\n"
        "  SecondaryDamageRadius      = 0.1\n"
        "  AttackRange                = 2000\n"
        "  MinimumAttackRange         = 450\n"
        "  DamageType                 = CRUSH\n",
        "77H6Missile_ABM",
    )
    return text


def patch_s400(text: str) -> str:
    return must_replace(
        text,
        "Object S400R_FireControlSystem_AUM\n"
        "Scale = 0.9\n"
        "\n"
        "  ; *** ART Parameters ***\n"
        "  Draw = W3DModelDraw ModuleTag_01\n"
        "    ParticlesAttachedToAnimatedBones = Yes\n"
        "    OkToChangeModelColor = Yes\n"
        "    DefaultConditionState\n"
        "      Model                   = S400R_MT\n"
        "      WeaponLaunchBone        = PRIMARY MISSILE\n"
        "      WeaponMuzzleFlash       = PRIMARY MISSILE\n"
        "      WeaponFireFXBone        = PRIMARY MISSILE\n"
        "    End\n"
        "  End\n"
        "  WeaponSet\n"
        "    Conditions        = None\n"
        "    Weapon            = PRIMARY      4x_MRSAM_9M96E2\n"
        "  End\n"
        "  VisionRange         = 900\n",
        "Object S400R_FireControlSystem_AUM\n"
        "Scale = 0.9\n"
        "\n"
        "  ; *** ART Parameters ***\n"
        "  Draw = W3DModelDraw ModuleTag_01\n"
        "    ParticlesAttachedToAnimatedBones = Yes\n"
        "    OkToChangeModelColor = Yes\n"
        "    DefaultConditionState\n"
        "      Model                   = S400R_MT\n"
        "      WeaponLaunchBone        = PRIMARY MISSILE\n"
        "      WeaponMuzzleFlash       = PRIMARY MISSILE\n"
        "      WeaponFireFXBone        = PRIMARY MISSILE\n"
        "    End\n"
        "  End\n"
        "  WeaponSet\n"
        "    Conditions        = None\n"
        "    Weapon            = PRIMARY      4x_MRSAM_9M96E2\n"
        "  End\n"
        "  VisionRange         = 1600\n",
        "S400R_FireControlSystem_AUM VisionRange",
    )


def patch_irist(text: str) -> str:
    return must_replace(
        text,
        "    Weapon            = PRIMARY   THAADMissile_ABM\n"
        "  End\n"
        "  VisionRange         = 1500\n"
        "  ShroudClearingRange = 0\n"
        "  ArmorSet\n"
        "    Conditions        = None\n"
        "    Armor             = Generic_FCS_Armor\n"
        "    DamageFX          = EmptyDamageFX\n"
        "  End\n"
        "  ; ***DESIGN parameters ***\n"
        "  EditorSorting = SYSTEM\n"
        "  KindOf = UNATTACKABLE CAN_ATTACK PRELOAD IMMOBILE NO_SELECT\n",
        "    Weapon            = PRIMARY   THAADMissile_ABM\n"
        "  End\n"
        "  VisionRange         = 1800\n"
        "  ShroudClearingRange = 0\n"
        "  ArmorSet\n"
        "    Conditions        = None\n"
        "    Armor             = Generic_FCS_Armor\n"
        "    DamageFX          = EmptyDamageFX\n"
        "  End\n"
        "  ; ***DESIGN parameters ***\n"
        "  EditorSorting = SYSTEM\n"
        "  KindOf = UNATTACKABLE CAN_ATTACK PRELOAD IMMOBILE NO_SELECT\n",
        "IRIST_FireControlSystem_ABM VisionRange",
    )


def patch_96l6_combat(text: str) -> str:
    return must_replace(
        text,
        "  DisplayName          = OBJECT:96L6\n"
        "  Side                 = Russia\n"
        "  EditorSorting        = VEHICLE\n"
        "  WeaponSet\n"
        "    Conditions         = None \n"
        "    Weapon             = SECONDARY 92N6R_Pack\n"
        "  End\n"
        "  VisionRange         = 200\n",
        "  DisplayName          = OBJECT:96L6\n"
        "  Side                 = Russia\n"
        "  EditorSorting        = VEHICLE\n"
        "  WeaponSet\n"
        "    Conditions         = None \n"
        "    Weapon             = PRIMARY   RadarTrackingBeam\n"
        "    Weapon             = SECONDARY 92N6R_Pack\n"
        "    AutoChooseSources  = SECONDARY None\n"
        "  End\n"
        "  VisionRange         = 900\n",
        "96L6 CombatMode weapons/vision",
    )


def patch_ht233_combat(text: str) -> str:
    text = must_replace(
        text,
        "  DisplayName          = OBJECT:HT233\n"
        "  Side                 = China\n"
        "  EditorSorting        = VEHICLE\n"
        "  WeaponSet\n"
        "    Conditions         = None \n"
        "    Weapon             = SECONDARY 92N6R_Pack\n"
        "  End\n"
        "  VisionRange         = 100\n",
        "  DisplayName          = OBJECT:HT233\n"
        "  Side                 = China\n"
        "  EditorSorting        = VEHICLE\n"
        "  WeaponSet\n"
        "    Conditions         = None \n"
        "    Weapon             = PRIMARY   RadarTrackingBeam\n"
        "    Weapon             = SECONDARY 92N6R_Pack\n"
        "    AutoChooseSources  = SECONDARY None\n"
        "  End\n"
        "  VisionRange         = 900\n",
        "HT233 CombatMode weapons/vision",
    )
    return must_replace(
        text,
        "   Behavior                 = AIUpdateInterface ModuleTag_FT\n"
        "  End\n",
        "  Behavior                     = AIUpdateInterface ModuleTag_FT\n"
        "    Turret\n"
        "      TurretTurnRate           = 50\n"
        "      ControlledWeaponSlots    = PRIMARY\n"
        "    End\n"
        "    AutoAcquireEnemiesWhenIdle = Yes\n"
        "    MoodAttackCheckRate        = 1\n"
        "  End\n",
        "HT233 CombatMode AIUpdate",
    )


def patch_trml_combat(text: str) -> str:
    text = must_replace(
        text,
        "  DisplayName          = OBJECT:trml4d\n"
        "  Side                 = Nato\n"
        "  EditorSorting        = VEHICLE\n"
        "  WeaponSet\n"
        "    Conditions         = None \n"
        "    Weapon             = SECONDARY 92N6R_Pack\n"
        "  End\n"
        "  VisionRange         = 100\n",
        "  DisplayName          = OBJECT:trml4d\n"
        "  Side                 = Nato\n"
        "  EditorSorting        = VEHICLE\n"
        "  WeaponSet\n"
        "    Conditions         = None \n"
        "    Weapon             = PRIMARY   RadarTrackingBeam\n"
        "    Weapon             = SECONDARY 92N6R_Pack\n"
        "    AutoChooseSources  = SECONDARY None\n"
        "  End\n"
        "  VisionRange         = 900\n",
        "TRML4D CombatMode weapons/vision",
    )
    return must_replace(
        text,
        "  Behavior                     = AIUpdateInterface ModuleTag_FT\n"
        "  End\n"
        "  ClientUpdate = AnimatedParticleSysBoneClientUpdate ModuleTag_Client05\n"
        "  End\n"
        "  Behavior  = PhysicsBehavior ModuleTag_06\n"
        "    Mass    = 200\n",
        "  Behavior                     = AIUpdateInterface ModuleTag_FT\n"
        "    Turret\n"
        "      TurretTurnRate           = 50\n"
        "      ControlledWeaponSlots    = PRIMARY\n"
        "    End\n"
        "    AutoAcquireEnemiesWhenIdle = Yes\n"
        "    MoodAttackCheckRate        = 1\n"
        "  End\n"
        "  ClientUpdate = AnimatedParticleSysBoneClientUpdate ModuleTag_Client05\n"
        "  End\n"
        "  Behavior  = PhysicsBehavior ModuleTag_06\n"
        "    Mass    = 200\n",
        "TRML4D CombatMode AIUpdate",
    )


PATCHERS = {
    r"Data\INI\Weapon.ini": patch_weapon_ini,
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\S400.ini": patch_s400,
    r"Data\INI\Object\Specter\NATO\Airdefense\IRIST_SLX.ini": patch_irist,
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\96L6TSP.ini": patch_96l6_combat,
    r"Data\INI\Object\Specter\PLA\AirDefense\HT233.ini": patch_ht233_combat,
    r"Data\INI\Object\Specter\NATO\Airdefense\TRML4D.ini": patch_trml_combat,
}


def normalize_newlines(text: str, nl: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if nl == "\r\n":
        return text.replace("\n", "\r\n")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()

    entries, raw = read_big(args.src_big)
    file_map: dict[str, bytes] = {}
    for name, off, size in entries:
        file_map[name] = raw[off : off + size]

    changed = []
    for inner, fn in PATCHERS.items():
        if inner not in file_map:
            raise SystemExit(f"missing inner file {inner}")
        text, nl = decode(file_map[inner])
        # Unique blocks were authored with \n; match regardless of BIG newlines.
        work = text.replace("\r\n", "\n")
        patched = fn(work)
        patched = normalize_newlines(patched, nl)
        if patched == text:
            raise SystemExit(f"no change applied to {inner}")
        file_map[inner] = encode(patched)
        changed.append(inner)

    ocl_name = r"Data\INI\ObjectCreationList_ZZZZ_ZZGmAdAbm.ini"
    if ocl_name in file_map:
        raise SystemExit(f"already present: {ocl_name}")
    file_map[ocl_name] = encode(OCL_ZZZZ.replace("\n", "\r\n"))
    changed.append(ocl_name + " (added)")

    # Safety: Patriot ABM weapon still CRUSH.
    w = file_map[r"Data\INI\Weapon.ini"].decode("latin1")
    if "Weapon 10x_PAC3_MSE_ABM" not in w or "DamageType                  = CRUSH" not in w:
        raise SystemExit("Patriot 10x_PAC3_MSE_ABM CRUSH missing after patch")
    if "AntiBallisticMissile        = Yes" not in w:
        raise SystemExit("Patriot AntiBallisticMissile flag missing")

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    out = build_big(file_map)
    args.out_big.write_bytes(out)

    src_sha = sha256(args.src_big)
    out_sha = sha256(args.out_big)
    print(f"SRC  size={args.src_big.stat().st_size} sha256={src_sha}")
    print(f"OUT  size={args.out_big.stat().st_size} sha256={out_sha} entries={len(file_map)}")
    print("Changed:")
    for c in changed:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
