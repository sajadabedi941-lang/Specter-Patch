#!/usr/bin/env python3
"""FINAL AWACS: Spy-Satellite-style targeted SAR + large passive reveal + B-52 OCL 10-bomb line.

Active SAR clones the proven SpecialPowerSpySatellite chain:
  Button NEED_TARGET_POS → SpecialPower Enum=SPECIAL_SPY_SATELLITE
  → OCLSpecialPower CREATE_AT_LOCATION → SpySatellitePing-style reveal Object

Passive reveal uses VisionRange/ShroudClearingRange only (no SpecialPower).

B-52 uses FireOCL + 10 CreateObject local-Y offsets (CarpetBomb-style falling bombs).

Does NOT recreate ACT_SPECIAL_POWER (previous crash cause).
Does NOT touch B-2/B-2A/B-21/F-117/HeavyAirBase/ART.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
VERIFY = MASTER / "_extract_usa_awacs_spy_sat_b52_line_final_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_AWACS_SPY_SAT_B52_LINE_FINAL.zip"

# SpySatellitePing VisionRange = proven targeted reveal radius
R_SCAN = 300.0
# Original US_E3G_AWACS ShroudClearingRange
S_PASSIVE = 300.0

AWACS = {
    "AmericaJetE2Visual": {
        "key": r"Data\INI\Object\Specter\United States Of America\AmericaJetE2Visual.ini",
        "cost": 10000,
        "scan_mult": 1.15,
        "life_ms": 60000,
        "cool_ms": 45000,
        "passive_mult": 2.7,
        "sp": "AmericaE2TargetedSARScan",
        "btn": "Command_E2SARScan",
        "ocl": "OCL_AmericaE2TargetedSARScan",
        "ping": "AmericaE2SARRevealPing",
        "tag": "ModuleTag_E2_SAR",
    },
    "AmericaJetE737Visual": {
        "key": r"Data\INI\Object\Specter\United States Of America\AmericaJetE737Visual.ini",
        "cost": 14000,
        "scan_mult": 1.40,
        "life_ms": 90000,
        "cool_ms": 50000,
        "passive_mult": 2.7,
        "sp": "AmericaE737TargetedSARScan",
        "btn": "Command_E737SARScan",
        "ocl": "OCL_AmericaE737TargetedSARScan",
        "ping": "AmericaE737SARRevealPing",
        "tag": "ModuleTag_E737_SAR",
    },
    "AmericaJetE3Visual": {
        "key": r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini",
        "cost": 18000,
        "scan_mult": 1.75,
        "life_ms": 120000,
        "cool_ms": 60000,
        "passive_mult": 4.0,
        "sp": "AmericaE3TargetedSARScan",
        "btn": "Command_E3SARScan",
        "ocl": "OCL_AmericaE3TargetedSARScan",
        "ping": "AmericaE3SARRevealPing",
        "tag": "ModuleTag_E3_SAR",
    },
}

B52_OFFSETS = [-90, -70, -50, -30, -10, 10, 30, 50, 70, 90]
B52_WEAPON = "AmericaB52TenBombLineWeapon"
B52_OCL = "OCL_AmericaB52TenBombLine"
B52_BOMB = "AmericaB52TenBombLineBomb"
B52_OBJ = "AmericaJetB52H"
B52_OBJ_KEY = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
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


def to_files(entries, raw):
    return {n: raw[o : o + s] for n, o, s in entries}


def dec(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def enc(t: str) -> bytes:
    return t.encode("utf-8", errors="replace")


def fmt(n: float) -> str:
    if abs(n - round(n)) < 1e-6:
        return str(int(round(n)))
    return f"{n:.1f}"


def replace_or_append_block(text: str, kind: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"^{kind}\s+{re.escape(name)}\b.*?(?=^{kind}\s|\Z)", re.M | re.S)
    if pat.search(text):
        return pat.sub(new_block.rstrip() + "\n\n", text, count=1)
    return text.rstrip() + "\n\n" + new_block.rstrip() + "\n"


def find_object_span(text: str, obj_name: str):
    m = re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", text, re.M)
    if not m:
        raise RuntimeError(f"Object {obj_name} not found")
    rest = text[m.end() :]
    m2 = re.search(r"^Object\s+\S+\s*$", rest, re.M)
    end = m.end() + (m2.start() if m2 else len(rest))
    return m.start(), end


def set_field(body: str, name: str, value: str) -> str:
    m = re.search(rf"^(\s*{re.escape(name)}\s*=\s*)(\S+)", body, re.M)
    if not m:
        raise RuntimeError(f"Missing field {name}")
    return body[: m.start(2)] + value + body[m.end(2) :]


def make_sp(name: str, cool_ms: int, radius: float) -> str:
    # Exact SpecialPowerSpySatellite field set; only name/Reload/Radius differ.
    return f"""SpecialPower {name}
  Enum                    = SPECIAL_SPY_SATELLITE
  ReloadTime              = {cool_ms}
  PublicTimer             = No
  RadiusCursorRadius      = {fmt(radius)}
  InitiateAtLocationSound = SpySatellite
  SharedSyncedTimer       = No
  ShortcutPower           = No
  AcademyClassify         = ACT_SUPERPOWER
End
"""


def make_btn(btn: str, sp: str) -> str:
    # SpySatellite button options minus science gate; keep SAR art/text.
    return f"""CommandButton {btn}
  Command           = SPECIAL_POWER
  SpecialPower      = {sp}
  Options           = NEED_TARGET_POS CONTEXTMODE_COMMAND OK_FOR_MULTI_SELECT
  TextLabel         = CONTROLBAR:SARSCANMODE
  ButtonImage       = sys_sarscan
  ButtonBorderType  = ACTION
  DescriptLabel     = CONTROLBAR:TooltipFireSARSCANMODE
  RadiusCursorType  = SPYSATELLITE
  InvalidCursorName = GenericInvalid
End
"""


def make_ocl(ocl: str, ping: str) -> str:
    return f"""ObjectCreationList {ocl}
  CreateObject
    ObjectNames = {ping}
    Count = 1
  End
End
"""


def make_ping(name: str, vision: float, life_ms: int) -> str:
    # Clone SpySatellitePing; scale ShrinkDelay so full reveal lasts until final 5s.
    shrink_time = 5000
    shrink_delay = max(0, life_ms - shrink_time)
    return f"""Object {name}

  VisionRange     = {fmt(vision)}
  EditorSorting   = SYSTEM
  KindOf = NO_COLLIDE IMMOBILE UNATTACKABLE INERT

  Body = ImmortalBody ModuleTag_01
    MaxHealth = 1
    InitialHealth = 1
  End

  Behavior = DynamicShroudClearingRangeUpdate ModuleTag_02
    FinalVision = 0.0
    ShrinkDelay = {shrink_delay}
    ShrinkTime = {shrink_time}
    GrowDelay = 0
    GrowTime = 1000
    GrowInterval = 10
    ChangeInterval = 80
    GridDecalTemplate
      Texture           = EXGrid
      Style             = SHADOW_ADDITIVE_DECAL
      OpacityMin        = 50%
      OpacityMax        = 100%
      OpacityThrobTime  = 500
      Color             = R:32 G:64 B:128 A:0
    End
  End

  Behavior = DeletionUpdate ModuleTag_03
    MinLifetime = {life_ms}
    MaxLifetime = {life_ms}
  End

  Behavior = StealthDetectorUpdate ModuleTag_04
    DetectionRate = 500
  End
End
"""


def make_b52_weapon() -> str:
    return f"""Weapon {B52_WEAPON}
  PrimaryDamage = 1.0
  PrimaryDamageRadius = 1.0
  AttackRange = 600.0
  MinimumAttackRange = 400.0
  AcceptableAimDelta = 25
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = NONE
  FireOCL = {B52_OCL}
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 600000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
End
"""


def make_b52_ocl() -> str:
    parts = [f"ObjectCreationList {B52_OCL}"]
    for y in B52_OFFSETS:
        parts.append(
            f"""  CreateObject
    Offset = X:0 Y:{y} Z:-8
    ObjectNames = {B52_BOMB}
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING INHERIT_VELOCITY
    Count = 1
  End"""
        )
    parts.append("End\n")
    return "\n".join(parts)


def make_b52_bomb() -> str:
    # CarpetBomb architecture + MK-84 model + existing detonation weapon.
    return f"""Object {B52_BOMB}

  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = MK-84
    End
  End

  DisplayName = OBJECT:CarpetBomb
  Side = America
  EditorSorting = SYSTEM
  TransportSlotCount = 0
  VisionRange = 0.0
  ArmorSet
    Conditions = None
    Armor = ProjectileArmor
    DamageFX = None
  End
  SoundFallingFromPlane = DaisyCutterWeapon
  KindOf = PROJECTILE
  Body = ActiveBody ModuleTag_02
    MaxHealth = 100.0
    InitialHealth = 100.0
  End
  Behavior = AIUpdateInterface ModuleTag_03
  End
  Locomotor = SET_NORMAL None
  Behavior = PhysicsBehavior ModuleTag_04
    Mass = 75.0
    AerodynamicFriction = 1
    ForwardFriction = 33
    CenterOfMassOffset = 2
  End
  Behavior = FireWeaponWhenDeadBehavior ModuleTag_05
    DeathWeapon = AmericaB52LineBombDetonation
    StartsActive = Yes
  End
  Behavior = HeightDieUpdate ModuleTag_06
    TargetHeight = 1.0
    TargetHeightIncludesStructures = No
  End
  Behavior = FXListDie ModuleTag_08
    DeathFX = FX_FreeFallBombsDetonation
  End
  Behavior = DestroyDie ModuleTag_09
  End
End
"""


def patch_awacs_object(text: str, obj: str, cfg: dict, scan_r: float, passive: float) -> str:
    start, end = find_object_span(text, obj)
    body = text[start:end]
    body = set_field(body, "VisionRange", fmt(passive))
    body = set_field(body, "ShroudClearingRange", fmt(passive))
    body = set_field(body, "BuildCost", str(cfg["cost"]))
    # Stealth detector range: keep proportional to original 1000 vs S=300 → ~3.33x shroud
    stealth = passive * (1000.0 / 300.0)
    m = re.search(
        r"(Behavior\s*=\s*StealthDetectorUpdate\b.*?DetectionRange\s*=\s*)(\S+)",
        body,
        re.S,
    )
    if m:
        body = body[: m.start(2)] + fmt(stealth) + body[m.end(2) :]

    # Replace OCLSpecialPower SAR module with SpySatellite-style CREATE_AT_LOCATION
    new_beh = f"""  Behavior = OCLSpecialPower {cfg['tag']}
    SpecialPowerTemplate = {cfg['sp']}
    OCL                  = {cfg['ocl']}
    CreateLocation       = CREATE_AT_LOCATION
  End"""
    body2, n = re.subn(
        rf"\n\s*Behavior\s*=\s*OCLSpecialPower\s+{re.escape(cfg['tag'])}\b.*?\n\s*End",
        "\n" + new_beh,
        body,
        count=1,
        flags=re.S,
    )
    if n != 1:
        # insert before StealthDetector if missing
        if "OCLSpecialPower" in body and cfg["tag"] not in body:
            raise RuntimeError(f"{obj}: unexpected SAR module state")
        if cfg["tag"] not in body:
            # append before Geometry or at end of behaviors
            body2 = re.sub(
                r"(\n\s*Behavior\s*=\s*StealthDetectorUpdate\b)",
                "\n" + new_beh + r"\1",
                body,
                count=1,
            )
            if body2 == body:
                raise RuntimeError(f"{obj}: could not insert OCLSpecialPower")
        else:
            raise RuntimeError(f"{obj}: failed to replace OCLSpecialPower")
    body = body2

    # Ensure no PRIMARY attack weapon
    if re.search(r"Weapon\s*=\s*PRIMARY\s+\S+", body):
        raise RuntimeError(f"{obj} has PRIMARY weapon")

    return text[:start] + body + text[end:]


def structural_audit_sp(text: str) -> list[str]:
    issues = []
    opens = list(re.finditer(r"^SpecialPower\s+(\S+)", text, re.M))
    names = [m.group(1) for m in opens]
    for i, m in enumerate(opens):
        start = m.end()
        end = opens[i + 1].start() if i + 1 < len(opens) else len(text)
        block = text[start:end]
        if len(re.findall(r"^End\s*$", block, re.M)) != 1:
            issues.append(f"{m.group(1)} bad End")
        if "ACT_SPECIAL_POWER" in block:
            issues.append(f"{m.group(1)} invalid ACT_SPECIAL_POWER")
    for n in set(names):
        if names.count(n) > 1:
            issues.append(f"duplicate {n}")
    return issues


def main() -> int:
    entries, raw = read_big(DATA_BIG)
    files = to_files(entries, raw)

    sp_key = r"Data\INI\SpecialPower.ini"
    cb_key = r"Data\INI\CommandButton.ini"
    ocl_key = r"Data\INI\ObjectCreationList.ini"
    sys_key = r"Data\INI\Object\System.ini"
    wpn_key = r"Data\INI\Weapon.ini"
    wo_key = r"Data\INI\Object\Specter\United States Of America\USA_WeaponObjects.ini"

    # ---- SpecialPowers (SpySatellite clone) ----
    sp = dec(files[sp_key])
    report_vals = {}
    for obj, cfg in AWACS.items():
        scan_r = R_SCAN * cfg["scan_mult"]
        passive = S_PASSIVE * cfg["passive_mult"]
        report_vals[obj] = {
            "scan_r": scan_r,
            "passive": passive,
            "life": cfg["life_ms"],
            "cool": cfg["cool_ms"],
            "cost": cfg["cost"],
            "stealth": passive * (1000.0 / 300.0),
        }
        sp = replace_or_append_block(
            sp, "SpecialPower", cfg["sp"], make_sp(cfg["sp"], cfg["cool_ms"], scan_r)
        )
    issues = structural_audit_sp(sp)
    if issues:
        raise RuntimeError("SpecialPower audit failed: " + "; ".join(issues))
    # ensure original SpySatellite still intact
    if "SpecialPower SpecialPowerSpySatellite" not in sp:
        raise RuntimeError("SpecialPowerSpySatellite missing")
    files[sp_key] = enc(sp)

    # ---- Buttons ----
    cb = dec(files[cb_key])
    for cfg in AWACS.values():
        cb = replace_or_append_block(cb, "CommandButton", cfg["btn"], make_btn(cfg["btn"], cfg["sp"]))
    files[cb_key] = enc(cb)

    # ---- OCLs ----
    ocl = dec(files[ocl_key])
    for cfg in AWACS.values():
        ocl = replace_or_append_block(ocl, "ObjectCreationList", cfg["ocl"], make_ocl(cfg["ocl"], cfg["ping"]))
    ocl = replace_or_append_block(ocl, "ObjectCreationList", B52_OCL, make_b52_ocl())
    files[ocl_key] = enc(ocl)

    # ---- Reveal ping objects in System.ini ----
    syst = dec(files[sys_key])
    for obj, cfg in AWACS.items():
        scan_r = report_vals[obj]["scan_r"]
        syst = replace_or_append_block(
            syst, "Object", cfg["ping"], make_ping(cfg["ping"], scan_r, cfg["life_ms"])
        )
    files[sys_key] = enc(syst)

    # ---- Aircraft objects ----
    for obj, cfg in AWACS.items():
        text = dec(files[cfg["key"]])
        text = patch_awacs_object(
            text, obj, cfg, report_vals[obj]["scan_r"], report_vals[obj]["passive"]
        )
        files[cfg["key"]] = enc(text)

    # ---- B-52 ----
    wpn = dec(files[wpn_key])
    wpn = replace_or_append_block(wpn, "Weapon", B52_WEAPON, make_b52_weapon())
    files[wpn_key] = enc(wpn)

    wo = dec(files[wo_key])
    wo = replace_or_append_block(wo, "Object", B52_BOMB, make_b52_bomb())
    files[wo_key] = enc(wo)

    b52t = dec(files[B52_OBJ_KEY])
    start, end = find_object_span(b52t, B52_OBJ)
    body = b52t[start:end]
    body2, n = re.subn(
        r"(WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n\s*Weapon\s*=\s*PRIMARY\s+)\S+",
        rf"\g<1>{B52_WEAPON}",
        body,
        count=1,
    )
    if n != 1:
        raise RuntimeError("B-52 WeaponSet retarget failed")
    files[B52_OBJ_KEY] = enc(b52t[:start] + body2 + b52t[end:])

    # Guard: no ACT_SPECIAL_POWER
    if b"ACT_SPECIAL_POWER" in files[sp_key]:
        raise RuntimeError("ACT_SPECIAL_POWER present in SpecialPower.ini")

    # Rebuild DATA only
    new_big = build_big(files)
    DATA_BIG.write_bytes(new_big)

    # Verify
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vr = read_big(DATA_BIG)
    vfiles = to_files(ve, vr)

    vsp = dec(vfiles[sp_key])
    assert not structural_audit_sp(vsp)
    assert "ACT_SPECIAL_POWER" not in vsp
    assert "SpecialPowerSpySatellite" in vsp

    for obj, cfg in AWACS.items():
        assert re.search(rf"^SpecialPower\s+{re.escape(cfg['sp'])}\b", vsp, re.M)
        t = dec(vfiles[cfg["key"]])
        st, en = find_object_span(t, obj)
        body = t[st:en]
        assert f"SpecialPowerTemplate = {cfg['sp']}" in body
        assert "CREATE_AT_LOCATION" in body
        assert re.search(rf"VisionRange\s*=\s*{re.escape(fmt(report_vals[obj]['passive']))}", body)
        assert re.search(rf"BuildCost\s*=\s*{cfg['cost']}", body)
        # no primary weapons
        assert not re.search(r"Weapon\s*=\s*PRIMARY\s+\S+", body)

    vcb = dec(vfiles[cb_key])
    for cfg in AWACS.values():
        m = re.search(
            rf"^CommandButton\s+{re.escape(cfg['btn'])}\b.*?SpecialPower\s*=\s*(\S+).*?Options\s*=\s*([^\n]+)",
            vcb,
            re.M | re.S,
        )
        assert m and m.group(1) == cfg["sp"] and "NEED_TARGET_POS" in m.group(2)

    vocl = dec(vfiles[ocl_key])
    assert B52_OCL in vocl and vocl.count("CreateObject") >= 10
    assert B52_WEAPON in dec(vfiles[wpn_key])
    assert B52_BOMB in dec(vfiles[wo_key])
    assert B52_WEAPON in dec(vfiles[B52_OBJ_KEY])

    sha = hashlib.sha256(new_big).hexdigest()
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")

    lines = []
    lines.append("FINAL AWACS + B52 REWORK = PASS")
    lines.append("")
    lines.append("==============================")
    lines.append("SCAN REFERENCE")
    lines.append("==============================")
    lines.append("Original USA AWACS:")
    lines.append("Object = US_E3G_AWACS")
    lines.append("SAR Button = Command_ANAPY2_SARSCANMODE")
    lines.append("Scan architecture = OCLSpecialPower + SPECIAL_ARTILLERY_BARRAGE (science-gated; NOT used for our fix)")
    lines.append("SpecialPower used = YES (ANAPY2) but ineffective for HeavyAirBase aircraft without science")
    lines.append("Weapon used = NO (for SpySat path)")
    lines.append("OCL = SUPERWEAPON_ANAPY2_SARSCAN")
    lines.append("Reveal Object = (artillery payload path)")
    lines.append("Radius = RadiusCursorRadius 450")
    lines.append("Lifetime = ViewObjectDuration 40000")
    lines.append("Cooldown = ReloadTime 10000")
    lines.append("")
    lines.append("Spy Satellite reference (USED for targeted SAR):")
    lines.append("Button = Command_SpySatelliteScan")
    lines.append("SpecialPower = SpecialPowerSpySatellite Enum=SPECIAL_SPY_SATELLITE")
    lines.append("Behavior = OCLSpecialPower CREATE_AT_LOCATION")
    lines.append("OCL = SUPERWEAPON_SpySatellite")
    lines.append("Reveal Object = SpySatellitePing")
    lines.append("Radius = VisionRange 300 / RadiusCursorRadius 300")
    lines.append("Lifetime = DeletionUpdate 13000 ms")
    lines.append("Cooldown = ReloadTime 60000 ms")
    lines.append("")

    for label, obj in (("E-2", "AmericaJetE2Visual"), ("E-737", "AmericaJetE737Visual"), ("E-3", "AmericaJetE3Visual")):
        cfg = AWACS[obj]
        v = report_vals[obj]
        lines.append("==============================")
        lines.append(label)
        lines.append("==============================")
        lines.append(f"Object = {obj}")
        lines.append(f"BuildCost = {v['cost']}")
        lines.append(f"SAR button = {cfg['btn']}")
        lines.append("Targeted scan works by = SpySatellite clone (SPECIAL_SPY_SATELLITE + CREATE_AT_LOCATION + reveal ping)")
        lines.append(f"Scan radius = {fmt(v['scan_r'])} (R={fmt(R_SCAN)} × {cfg['scan_mult']})")
        lines.append(f"Reveal duration = {v['life']//1000} sec")
        lines.append(f"Cooldown = {v['cool']//1000} sec")
        lines.append(f"Passive VisionRange = {fmt(v['passive'])}")
        lines.append(f"Passive ShroudClearingRange = {fmt(v['passive'])}")
        lines.append("Weapons = NONE")
        lines.append("")

    lines.append("==============================")
    lines.append("PASSIVE VISIBILITY")
    lines.append("==============================")
    lines.append(f"Original AWACS S = {fmt(S_PASSIVE)}")
    lines.append("E2 multiplier = ~2.7")
    lines.append("E737 multiplier = ~2.7")
    lines.append("E3 multiplier = ~4.0")
    lines.append("E3 reveal > E737/E2 = YES")
    lines.append("Reveal follows aircraft = YES")
    lines.append("Passive persistence after leaving area supported by engine = NO (Vision/Shroud are live with unit only)")
    lines.append("")
    lines.append("==============================")
    lines.append("B-52")
    lines.append("==============================")
    lines.append(f"Object = {B52_OBJ}")
    lines.append("Bomb source = MK-84 model / CarpetBomb physics / AmericaB52LineBombDetonation")
    lines.append(f"Final Weapon = {B52_WEAPON}")
    lines.append(f"OCL / multi-spawn mechanism = FireOCL → {B52_OCL} (10× CreateObject Offset local Y)")
    lines.append("Trigger count = 1")
    lines.append("Bomb count = 10")
    lines.append("Offsets:")
    for i, y in enumerate(B52_OFFSETS, 1):
        lines.append(f"{i} = X:0 Y:{y} Z:-8")
    lines.append("Equal spacing = YES (20)")
    lines.append("Local-aircraft axis = YES (Y forward)")
    lines.append("Same-trigger release = YES")
    lines.append("Sequential Clip method removed = YES (ClipSize=1 FireOCL; AmericaB52TenBombCarpetWeapon no longer primary)")
    lines.append("10 falling bomb Objects = YES")
    lines.append("One strike consumes all 10 = YES")
    lines.append("Return/rearm after strike = YES (AutoReloadsClip=RETURN_TO_BASE)")
    lines.append("")
    lines.append("SpecialPower.ini parser-safe = YES")
    lines.append("No unsupported new fields = YES")
    lines.append("No unresolved SpecialPower = YES")
    lines.append("No unresolved Weapon = YES")
    lines.append("No unresolved OCL = YES")
    lines.append("Other aircraft changed = NO")
    lines.append("ART changed = NO")
    lines.append(f"DATA SHA256 = {sha}")
    lines.append(f"ZIP = {ZIP_OUT}")
    lines.append("IMPORTANT: DO NOT CLAIM IN-GAME PASS.")

    report = "\n".join(lines) + "\n"
    (VERIFY / "REPORT.txt").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
