#!/usr/bin/env python3
"""Patch live SPE DATA for Shahed-136 Fire + Khormshar launcher/FX.

Source: PR #709 / Release iran-commandset-ini-fire _SPEC_DATA_ONE.big
(SHA 46aab7d5c9433471a545935e2f922949d85130de287e44da3d13772a18c604cc).

Does not rewrite CommandSet.ini (PR #710 loose overlay stays the live panel).
Does not pack ART: ART ONE Irn_Khormsh already has MISSILE01 (identical to ART TWO).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/IRAN_COMMANDSET_INI_FIRE/_SPEC_DATA_ONE.big"
SRC_SHA = "46aab7d5c9433471a545935e2f922949d85130de287e44da3d13772a18c604cc"
OUT_DIR = ROOT / "Release/IRAN_SHAHED_KHORMSHAR_FIRE"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_SHA = OUT_DIR / "_SPEC_DATA_ONE.big.sha256"

K_SHAHED_OBJ = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
K_SHAHED_PROJ = r"Data\INI\Object\Specter\Iranian Army\Iran_Shahed136_FireProjectile.ini"
K_SHAHED_WPN_EXTRA = r"Data\INI\Weapon_ZZZZ_IranShahed136Launcher.ini"
K_KHOR_OBJ = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Khormshar.ini"
K_KHOR_OVERLAY = r"Data\INI\Object_ZZZZ_ZzGlobalStoreFivePrereq.ini"
K_WEAPON_OBJECTS = r"Data\INI\Object\Specter\Iranian Army\Iran_WeaponObjects.ini"
K_WEAPON = r"Data\INI\Weapon.ini"
K_COMMANDSET = r"Data\INI\CommandSet.ini"

SHAHED_WEAPON_BLOCK = """\
; Iran Shahed-136 Mobile Launcher PRIMARY. Live Object
; IranVehicleShahedLauncher points here. Previously this name existed only in
; Data\\INI\\Weapon_ZZZZ_IranShahed136Launcher.ini, which WeaponStore does not
; load (initSubsystem file is Data\\INI\\Weapon.ini). Fateh 2x_SRBM_Fateh313_HE
; is in this file; Shahed must be too or FIRE_WEAPON stays inert.
Weapon Weapon_Iran_Shahed136Launcher
  PrimaryDamage               = 1800
  PrimaryDamageRadius         = 10.0
  SecondaryDamage             = 10.0
  SecondaryDamageRadius       = 10.0
  AttackRange                 = 3000
  MinimumAttackRange          = 200.0
  DamageType                  = EXPLOSION
  DeathType                   = EXPLODED
  FireFX                      = FX_IskanderFiringEffects
  ProjectileObject            = Iran_Shahed136_FireProjectile
  ProjectileDetonationFX      = FX_LoiteringDroneDetonation
  RadiusDamageAffects         = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound                   = Iskander_Firing
  WeaponSpeed                 = 180
  AcceptableAimDelta          = 360
  DelayBetweenShots           = 2000
  ClipSize                    = 5
  ClipReloadTime              = 140000
  AntiGround                  = Yes
End
""".replace("\n", "\r\n")


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def dec(blob: bytes) -> str:
    return blob.decode("latin1")


def enc(text: str) -> bytes:
    return text.encode("latin1")


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def replace_object_block(text: str, obj_name: str, transform) -> str:
    nl = nl_of(text)
    pat = re.compile(
        rf"(^Object {re.escape(obj_name)}\s*{re.escape(nl)})(.*?)(?=^Object |\Z)",
        re.M | re.S,
    )
    m = pat.search(text)
    if not m:
        raise RuntimeError(f"Object {obj_name} not found")
    new_body = transform(m.group(1) + m.group(2))
    return text[: m.start()] + new_body + text[m.end() :]


def patch_khormshar_vehicle(block: str) -> str:
    """Show MISSILE01 on the live TEL; bind FireMainWeapon (PRIMARY) to that bone."""
    nl = nl_of(block)
    lines = block.splitlines()
    out: list[str] = []
    in_main = False
    cond = ""
    state_lines: list[str] = []
    injected_feedback = False

    def flush_state(buf: list[str], cond_flags: str) -> list[str]:
        if not buf:
            return buf
        flags = cond_flags.upper()
        is_rider1 = "RIDER1" in flags
        is_rubble = ("RUBBLE" in flags) and ("RIDER" not in flags)
        joined = nl.join(buf)
        has_hide = bool(re.search(r"HideSubObject\s*=\s*MISSILE01\b", joined, re.I))
        has_show = bool(re.search(r"ShowSubObject\s*=\s*MISSILE01\b", joined, re.I))
        has_primary = bool(
            re.search(r"WeaponLaunchBone\s*=\s*PRIMARY\s+MISSILE01\b", joined, re.I)
        )
        result: list[str] = []
        for line in buf:
            if re.search(r"HideSubObject\s*=\s*MISSILE01\b", line, re.I):
                if is_rider1 or is_rubble:
                    result.append(line)
                else:
                    result.append(re.sub(r"HideSubObject", "ShowSubObject", line, count=1))
            elif re.search(r"WeaponLaunchBone\s*=\s*SECONDARY\s+MISSILE01\b", line, re.I):
                indent = line[: len(line) - len(line.lstrip())]
                if not has_primary:
                    result.append(f"{indent}WeaponLaunchBone  = PRIMARY   MISSILE01")
                    result.append(f"{indent}WeaponFireFXBone  = PRIMARY   WEAPONFX")
                    has_primary = True
                result.append(line)
            else:
                result.append(line)
        if not is_rider1 and not is_rubble:
            # MOVING / Default / DEPLOYED must show the TEL missile.
            if not has_show and not any(
                re.search(r"ShowSubObject\s*=\s*MISSILE01\b", ln, re.I) for ln in result
            ):
                indent = "      "
                # insert before End
                result.insert(-1, f"{indent}ShowSubObject     = MISSILE01")
            fire_state = (
                "DEFAULTCONDITIONSTATE" in flags
                or "DEPLOYED" in flags
                or "RIDER2" in flags
            )
            if fire_state and not has_primary:
                indent = "      "
                result.insert(-1, f"{indent}WeaponLaunchBone  = PRIMARY   MISSILE01")
                result.insert(-1, f"{indent}WeaponFireFXBone  = PRIMARY   WEAPONFX")
        return result

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.search(r"Draw\s*=\s*W3DTruckDraw\s+ModuleTag_01\b", line):
            in_main = True
            out.append(line)
            i += 1
            continue
        if in_main and (not injected_feedback) and "OkToChangeModelColor" in line:
            out.append(line)
            out.append("    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY")
            injected_feedback = True
            i += 1
            continue
        if in_main and re.match(r"\s*TrackMarks\s*=", line):
            if state_lines:
                out.extend(flush_state(state_lines, cond))
                state_lines = []
            in_main = False
            out.append(line)
            i += 1
            continue
        if in_main:
            if re.match(r"\s*DefaultConditionState\b", line) or re.match(
                r"\s*ConditionState\b", line
            ):
                if state_lines:
                    out.extend(flush_state(state_lines, cond))
                    state_lines = []
                cond = line.split(";", 1)[0]
                state_lines = [line]
                i += 1
                continue
            if state_lines:
                state_lines.append(line)
                if re.match(r"\s*End\s*$", line.split(";", 1)[0]):
                    out.extend(flush_state(state_lines, cond))
                    state_lines = []
                    cond = ""
                i += 1
                continue
        out.append(line)
        i += 1
    if state_lines:
        out.extend(flush_state(state_lines, cond))
    text = nl.join(out)
    if not text.endswith(nl):
        text += nl
    if "ProjectileBoneFeedbackEnabledSlots" not in text:
        raise RuntimeError("failed to inject ProjectileBoneFeedbackEnabledSlots")
    if not re.search(
        r"ShowSubObject\s*=\s*MISSILE01", text
    ) or "DefaultConditionState" not in text:
        raise RuntimeError("failed to show MISSILE01 on default state")
    return text


def patch_shahed_projectile(text: str) -> str:
    nl = nl_of(text)
    text = text.replace(
        "ParticleSysBone = ENGINE01 CruiseMissileExhaust_Ending_VLS",
        "ParticleSysBone = ENGINE CruiseMissileExhaust_Ending_VLS",
    )
    if "ParticleSysBone = ENGINE " not in text:
        raise RuntimeError("Shahed projectile ENGINE bone not patched")
    return text


def patch_weapon_ini(text: str) -> str:
    nl = nl_of(text)
    if re.search(r"^Weapon Weapon_Iran_Shahed136Launcher\s*$", text, re.M):
        raise RuntimeError("Shahed launcher weapon already in Weapon.ini")
    icbm = re.search(
        r"(^Weapon Khormshar1_ICBM\s*"
        + re.escape(nl)
        + r".*?ProjectileObject\s*=\s*Khormshar1_Object\s*"
        + re.escape(nl)
        + r")",
        text,
        re.M | re.S,
    )
    if not icbm:
        raise RuntimeError("Khormshar1_ICBM block not found")
    insert = (
        icbm.group(1)
        + "  ProjectileDetonationFX      = FX_HeavyWarheadCruiseMissileExplosion"
        + nl
        + "  AntiGround                  = Yes"
        + nl
    )
    # Do not match ICBM_AI: the captured block must not contain _AI.
    if "Khormshar1_ICBM_AI" in icbm.group(1):
        raise RuntimeError("ICBM patch captured the AI weapon")
    text = text[: icbm.start()] + insert + text[icbm.end() :]
    if not text.endswith(nl):
        text += nl
    text = text + nl + SHAHED_WEAPON_BLOCK.replace("\r\n", nl)
    if not text.endswith(nl):
        text += nl
    return text


def patch_khormshar_projectile(block: str) -> str:
    nl = nl_of(block)
    old = (
        "; ---- begin Projectile death behaviors"
        + nl
        + "  Behavior = InstantDeathBehavior DeathModuleTag_01"
        + nl
        + "    DeathTypes = ALL"
        + nl
        + "  End"
        + nl
        + "; ---- end Projectile death behaviors"
    )
    new = (
        "; ---- begin Projectile death behaviors"
        + nl
        + "  Behavior = InstantDeathBehavior DeathModuleTag_01"
        + nl
        + "    DeathTypes = NONE +DETONATED +NORMAL"
        + nl
        + "  End"
        + nl
        + "  Behavior = InstantDeathBehavior DeathModuleTag_02"
        + nl
        + "    DeathTypes = ALL -DETONATED -NORMAL"
        + nl
        + "    FX = FX_GenericMissileDisintegrate"
        + nl
        + "    OCL = OCL_GenericMissileDisintegrate"
        + nl
        + "  End"
        + nl
        + "  Behavior = InstantDeathBehavior DeathModuleTag_03"
        + nl
        + "    DeathTypes = ALL -LASERED -DETONATED"
        + nl
        + "    FX = FX_GenericMissileDeath"
        + nl
        + "  End"
        + nl
        + "  Behavior = FireWeaponWhenDeadBehavior ModuleTag_KhorImpact"
        + nl
        + "    DeathTypes   = NONE +NORMAL +DETONATED"
        + nl
        + "    DeathWeapon  = Khormshar1WarheadReentryGlideVehicleDamage"
        + nl
        + "    StartsActive = Yes"
        + nl
        + "  End"
        + nl
        + "; ---- end Projectile death behaviors"
    )
    if old not in block:
        raise RuntimeError("Khormshar1_Object InstantDeath ALL block not found")
    return block.replace(old, new, 1)


def patch_extra_shahed_weapon(text: str) -> str:
    """Keep extra file identical to Weapon.ini definition (backup if extras load)."""
    nl = nl_of(text)
    return (
        "; Mirror of Weapon.ini Weapon_Iran_Shahed136Launcher."
        + nl
        + "; WeaponStore loads Data\\INI\\Weapon.ini; this extra path is not that table."
        + nl
        + "; Kept in sync so a patched exe that does load extras cannot last-win a"
        + nl
        + "; different AttackRange / AntiGround."
        + nl
        + nl
        + SHAHED_WEAPON_BLOCK.replace("\r\n", nl)
    )


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> list[str]:
    notes: list[str] = []
    require(set(orig) == set(new), "entry names changed")
    changed = [k for k in orig if orig[k] != new[k]]
    notes.append("changed_entries=" + str(len(changed)))
    expected = {
        K_SHAHED_PROJ,
        K_SHAHED_WPN_EXTRA,
        K_KHOR_OBJ,
        K_KHOR_OVERLAY,
        K_WEAPON_OBJECTS,
        K_WEAPON,
    }
    require(set(changed) == expected, f"unexpected changed set {changed}")
    require(orig[K_COMMANDSET] == new[K_COMMANDSET], "CommandSet.ini must stay byte-identical")
    require(orig[K_SHAHED_OBJ] == new[K_SHAHED_OBJ], "Shahed Object file should stay byte-identical")

    w = dec(new[K_WEAPON])
    require(
        bool(re.search(r"^Weapon Weapon_Iran_Shahed136Launcher\s*$", w, re.M)),
        "Shahed weapon missing from Weapon.ini",
    )
    m = re.search(
        r"^Weapon Weapon_Iran_Shahed136Launcher\s*\r?\n(.*?)^End\s*$",
        w,
        re.M | re.S,
    )
    require(m is not None, "Shahed weapon block unreadable")
    body = m.group(1)
    require("AttackRange                 = 3000" in body, "Shahed AttackRange 3000 missing")
    require("MinimumAttackRange          = 200.0" in body, "Shahed MinRange missing")
    require("AntiGround                  = Yes" in body, "Shahed AntiGround missing")
    require("ProjectileObject            = Iran_Shahed136_FireProjectile" in body, "Shahed projectile missing")
    require("ClipSize                    = 5" in body, "Shahed ClipSize 5 missing")

    icbm = re.search(
        r"^Weapon Khormshar1_ICBM\s*\r?\n(.*?)^End\s*$", w, re.M | re.S
    )
    require(icbm is not None, "Khormshar1_ICBM missing")
    ib = icbm.group(1)
    require("PrimaryDamage               = 1" in ib, "ICBM damage changed")
    require("PrimaryDamageRadius         = 0" in ib, "ICBM radius changed")
    require("AttackRange                 = 2000" in ib, "ICBM range changed")
    require("MinimumAttackRange          = 1000" in ib, "ICBM min range changed")
    require("ProjectileDetonationFX      = FX_HeavyWarheadCruiseMissileExplosion" in ib, "ICBM detonation FX missing")
    require("FireOCL                     = OCL_HussienMissileDisarm" in ib, "ICBM FireOCL lost")
    require("Khormshar1_ICBM_AI" not in ib, "ICBM block ate AI weapon")

    # Do not retouch other countries' launcher weapons.
    for name in (
        "2x_SRBM_Fateh313_HE",
        "5x_Shahed136DroneSwarm",
        "Khormshar1_ICBM_AI",
        "Khormshar1WarheadReentryWeapon",
        "Khormshar1WarheadReentryGlideVehicleDamage",
        "Khormshar1HighExplosiveExplosion",
    ):
        o = re.search(rf"^Weapon {name}\s*\r?\n(.*?)^End\s*$", dec(orig[K_WEAPON]), re.M | re.S)
        n = re.search(rf"^Weapon {name}\s*\r?\n(.*?)^End\s*$", w, re.M | re.S)
        require(o is not None and n is not None, f"lost weapon {name}")
        if name != "Khormshar1_ICBM":
            require(o.group(0) == n.group(0), f"weapon {name} body changed")

    sh = dec(new[K_SHAHED_OBJ])
    require("Weapon = PRIMARY   Weapon_Iran_Shahed136Launcher" in sh, "Shahed PRIMARY lost")
    require("CommandSet    = IranShahed136FireCommandSet" in sh, "Shahed CommandSet lost")
    require("VisionRange     = 3000" in sh, "Shahed VisionRange lost")
    require("BuildCost       = 1500" in sh, "Shahed cost changed")

    proj = dec(new[K_SHAHED_PROJ])
    require("ParticleSysBone = ENGINE CruiseMissileExhaust_Ending_VLS" in proj, "ENGINE bone missing")
    require("ENGINE01" not in proj, "ENGINE01 still present")
    require("DumbProjectileBehavior" in proj, "Shahed projectile behavior lost")

    kh = dec(new[K_KHOR_OBJ])
    require("CommandSet             = IranKhorramshahrFireCommandSet" in kh, "Khormshar CS lost")
    require("BuildTime       = 10.0" in kh, "Khormshar BuildTime lost")
    require("BuildCost       = 2500" in kh, "Khormshar cost changed")
    require(re.search(r"Prerequisites\s*\r?\n\s*End", kh) is not None, "Khormshar prereq changed")
    require("ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY" in kh, "feedback slots missing")
    require("WeaponLaunchBone  = PRIMARY   MISSILE01" in kh, "PRIMARY MISSILE01 missing")
    # Default state must SHOW, RIDER1 must still HIDE.
    def_m = re.search(
        r"DefaultConditionState\r?\n(.*?)(?:\r?\n)\s*End", kh, re.S
    )
    require(def_m is not None, "default state missing")
    require("ShowSubObject     = MISSILE01" in def_m.group(1), "default still hiding missile")
    require("HideSubObject     = MISSILE01" not in def_m.group(1), "default hide remains")
    rider1 = re.search(
        r"ConditionState\s+=\s+RIDER1\s*\r?\n(.*?)(?:\r?\n)\s*End", kh, re.S
    )
    require(rider1 is not None, "RIDER1 state missing")
    require("HideSubObject     = MISSILE01" in rider1.group(1), "RIDER1 hide lost")

    ov = dec(new[K_KHOR_OVERLAY])
    ov_block = re.search(
        r"^Object IranVehicleKhormshar\s*\r?\n(.*?)(?=^Object )", ov, re.M | re.S
    )
    require(ov_block is not None, "overlay Khormshar missing")
    ob = ov_block.group(0)
    require("ShowSubObject     = MISSILE01" in ob, "overlay default not showing")
    require("WeaponLaunchBone  = PRIMARY   MISSILE01" in ob, "overlay PRIMARY bone missing")
    require("BuildTime       = 10.0" in ob, "overlay BuildTime lost")
    require("BuildCost       = 2500" in ob, "overlay cost changed")

    wo = dec(new[K_WEAPON_OBJECTS])
    kobj = re.search(
        r"^Object Khormshar1_Object\s*\r?\n(.*?)(?=^Object )", wo, re.M | re.S
    )
    require(kobj is not None, "Khormshar1_Object missing")
    kb = kobj.group(0)
    require("FireWeaponWhenDeadBehavior ModuleTag_KhorImpact" in kb, "impact death weapon missing")
    require("DeathWeapon  = Khormshar1WarheadReentryGlideVehicleDamage" in kb, "glide damage missing")
    inst = re.search(
        r"InstantDeathBehavior DeathModuleTag_01\s*\r?\n(.*?)(?:\r?\n)\s*End",
        kb,
        re.S,
    )
    require(inst is not None, "booster InstantDeath 01 missing")
    require("DETONATED" in inst.group(1), "booster InstantDeath 01 not DETONATED")
    require(not re.search(r"DeathTypes\s*=\s*ALL\s*$", inst.group(1), re.M), "booster InstantDeath 01 still ALL")
    # AI object must keep InstantDeath ALL (untouched).
    kai = re.search(
        r"^Object Khormshar1_AI_Object\s*\r?\n(.*?)(?=^Object )", wo, re.M | re.S
    )
    require(kai is not None, "AI object missing")
    require("DeathTypes = ALL" in kai.group(1), "AI InstantDeath ALL lost")

    cs = dec(new[K_COMMANDSET])
    for name in (
        "IranShahed136FireCommandSet",
        "IranKhorramshahrFireCommandSet",
        "IranMissileFireCommandSet",
        "IranWarfactoryCommandSet",
    ):
        require(f"CommandSet {name}" in cs, f"CommandSet {name} missing")

    notes.append("shahed_weapon_in_Weapon.ini=yes")
    notes.append("khormshar_show_MISSILE01=yes")
    notes.append("commandset_unchanged=yes")
    return notes


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    src_sha = hashlib.sha256(SRC_BIG.read_bytes()).hexdigest()
    if src_sha != SRC_SHA:
        raise SystemExit(f"source BIG sha mismatch: {src_sha} != {SRC_SHA}")
    orig = read_big(SRC_BIG)
    new = dict(orig)

    new[K_SHAHED_PROJ] = enc(patch_shahed_projectile(dec(orig[K_SHAHED_PROJ])))
    new[K_SHAHED_WPN_EXTRA] = enc(patch_extra_shahed_weapon(dec(orig[K_SHAHED_WPN_EXTRA])))
    new[K_KHOR_OBJ] = enc(
        replace_object_block(dec(orig[K_KHOR_OBJ]), "IranVehicleKhormshar", patch_khormshar_vehicle)
    )
    new[K_KHOR_OVERLAY] = enc(
        replace_object_block(
            dec(orig[K_KHOR_OVERLAY]), "IranVehicleKhormshar", patch_khormshar_vehicle
        )
    )
    new[K_WEAPON_OBJECTS] = enc(
        replace_object_block(
            dec(orig[K_WEAPON_OBJECTS]), "Khormshar1_Object", patch_khormshar_projectile
        )
    )
    new[K_WEAPON] = enc(patch_weapon_ini(dec(orig[K_WEAPON])))

    notes = validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blob = build_big(new)
    OUT_BIG.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    OUT_SHA.write_text(digest + "\n", encoding="ascii")
    print("wrote", OUT_BIG, "bytes", len(blob), "sha256", digest, "entries", len(new))
    for n in notes:
        print(" ", n)


if __name__ == "__main__":
    main()
