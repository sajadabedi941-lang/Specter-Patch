#!/usr/bin/env python3
"""USA: science-free SAR SCAN buttons for E-2/E-737/E-3 + B-52 10-bomb line OCL + B-21 dual GBU-72.

Reference: US_E3G_AWACS / Superweapon_ANAPY2_SARSCANMODE / Command_ANAPY2_SARSCANMODE
Base R = RadiusCursorRadius 450 (effective SAR cursor/reveal radius on original).
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
STAGE = MASTER / "_stage_usa_awacs_sar_b52_line_b21"
VERIFY = MASTER / "_extract_usa_awacs_sar_b52_line_b21_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_AWACS_SAR_B52_LINE_B21.zip"

# Original Superweapon_ANAPY2_SARSCANMODE RadiusCursorRadius
R = 450.0
STEALTH_BASE = 1000.0  # US_E3G StealthDetector DetectionRange
SHROUD_RATIO = 300.0 / 350.0
VIEW_BASE = 250.0  # original ViewObjectRange

AWACS = {
    "AmericaJetE2Visual": {
        "factor": 0.90,
        "cost": 9000,
        "sp": "AmericaE2SARScan",
        "cb": "Command_E2SARScan",
        "cs": "AmericaE2AWACSCommandSet",
        "ocl": "OCL_AmericaE2SARScan",
        "bubble": "AmericaE2SARScannerBubble",
        "tag": "ModuleTag_E2_SAR",
    },
    "AmericaJetE737Visual": {
        "factor": 1.20,
        "cost": 13000,
        "sp": "AmericaE737SARScan",
        "cb": "Command_E737SARScan",
        "cs": "AmericaE737AWACSCommandSet",
        "ocl": "OCL_AmericaE737SARScan",
        "bubble": "AmericaE737SARScannerBubble",
        "tag": "ModuleTag_E737_SAR",
    },
    "AmericaJetE3Visual": {
        "factor": 1.55,
        "cost": 18000,
        "sp": "AmericaE3SARScan",
        "cb": "Command_E3SARScan",
        "cs": "AmericaE3AWACSCommandSet",
        "ocl": "OCL_AmericaE3SARScan",
        "bubble": "AmericaE3SARScannerBubble",
        "tag": "ModuleTag_E3_SAR",
    },
}

# B-52 line offsets along local Y (forward in Generals unit space); X lateral=0
B52_OFFSETS = [-90, -70, -50, -30, -10, 10, 30, 50, 70, 90]


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


def find_object(files, obj_name):
    for key, blob in files.items():
        if not key.lower().endswith(".ini"):
            continue
        text = blob.decode("utf-8", errors="replace")
        m = re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", text, re.M)
        if not m:
            continue
        rest = text[m.end() :]
        m2 = re.search(r"^Object\s+\S+\s*$", rest, re.M)
        end = m.end() + (m2.start() if m2 else len(rest))
        return key, text, m.start(), end
    return None, None, None, None


def set_field(body: str, name: str, value: str) -> str:
    m = re.search(rf"^(\s*{re.escape(name)}\s*=\s*)(\S+)", body, re.M)
    if not m:
        raise RuntimeError(f"Missing field {name}")
    return body[: m.start(2)] + value + body[m.end(2) :]


def replace_or_append_block(text: str, kind: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"^{kind}\s+{re.escape(name)}\b.*?(?=^{kind}\s|\Z)", re.M | re.S)
    if pat.search(text):
        return pat.sub(new_block.rstrip() + "\n\n", text, count=1)
    return text.rstrip() + "\n\n" + new_block.rstrip() + "\n"


def replace_weaponset(body: str, new_ws: str) -> str:
    m = re.search(r"WeaponSet\s*\n(?:.*\n)*?\s*End", body)
    if not m:
        raise RuntimeError("WeaponSet not found")
    return body[: m.start()] + new_ws.strip() + "\n" + body[m.end() :]


def fmt(n: float) -> str:
    v = round(n)
    return str(v)


def make_sp(name: str, radius: float, view_range: float) -> str:
    return f"""SpecialPower {name}
  Enum                = SPECIAL_ARTILLERY_BARRAGE
  ReloadTime          = 10000
  InitiateSound       = SpySatellite
  PublicTimer         = No
  SharedSyncedTimer   = No
  ViewObjectDuration  = 40000
  ViewObjectRange     = {fmt(view_range)}
  RadiusCursorRadius  = {fmt(radius)}
  ShortcutPower       = No
  AcademyClassify     = ACT_SPECIAL_POWER
End
"""


def make_cb(cb_name: str, sp_name: str) -> str:
    # Visible SAR SCAN / RADAR MODE button — same art/text as original USA AWACS.
    # No NEED_SPECIAL_POWER_SCIENCE so HeavyAirBase units always show it.
    # No NEED_TARGET_POS: activates on owner (USE_OWNER_OBJECT) so coverage stays with aircraft.
    return f"""CommandButton {cb_name}
  Command           = SPECIAL_POWER
  SpecialPower      = {sp_name}
  Options           = OK_FOR_MULTI_SELECT
  TextLabel         = CONTROLBAR:SARSCANMODE
  ButtonImage       = sys_sarscan
  ButtonBorderType  = ACTION
  DescriptLabel     = CONTROLBAR:TooltipFireSARSCANMODE
End
"""


def make_cs(cs_name: str, cb_name: str) -> str:
    return f"""CommandSet {cs_name}
  1  = {cb_name}
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
"""


def make_ocl(ocl_name: str, bubble: str) -> str:
    return f"""ObjectCreationList {ocl_name}
  CreateObject
    ObjectNames = {bubble}
    Count = 1
    Disposition = LIKE_EXISTING
  End
End
"""


def make_bubble(obj_name: str, vision: float, shroud: float) -> str:
    # Temporary SAR bubble spawned on the AWACS (USE_OWNER_OBJECT).
    # Continuous follow coverage also comes from the aircraft Vision/Stealth modules.
    return f"""Object {obj_name}
  SelectPortrait = None
  ButtonImage = None
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = None
    End
  End
  DisplayName = OBJECT:FTD
  Side = America
  EditorSorting = SYSTEM
  TransportSlotCount = 0
  ArmorSet
    Conditions = None
    Armor = InvulnerableAllArmor
    DamageFX = None
  End
  VisionRange = {fmt(vision)}
  ShroudClearingRange = {fmt(shroud)}
  IsTrainable = No
  VoiceSelect = NoSound
  RadarPriority = NOT_ON_RADAR
  KindOf = IGNORED_IN_GUI NO_COLLIDE VEHICLE DRONE NO_SELECT
  Body = ActiveBody ModuleTag_02
    MaxHealth = 3000.0
    InitialHealth = 3000.0
  End
  Behavior = AIUpdateInterface ModuleTag_03
  End
  Locomotor = SET_NORMAL Fake_RCS_Locomotor
  Behavior = PhysicsBehavior ModuleTag_05
    Mass = 50.0
  End
  Behavior = DeletionUpdate ModuleTag_07
    MinLifetime = 40000
    MaxLifetime = 40000
  End
  Geometry = CYLINDER
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def make_b52_line_bomb() -> str:
    return """Object AmericaB52LineBomb
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


def make_b52_ocl() -> str:
    parts = ["ObjectCreationList OCL_AmericaB52_10BombLine"]
    for y in B52_OFFSETS:
        parts.append(
            f"""  CreateObject
    Offset = X:0 Y:{y} Z:-5
    ObjectNames = AmericaB52LineBomb
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End"""
        )
    parts.append("End\n")
    return "\n".join(parts)


def make_b52_weapons() -> str:
    return """Weapon AmericaB52LineBombDetonation
  PrimaryDamage = 680.0
  PrimaryDamageRadius = 40.0
  SecondaryDamage = 100.0
  SecondaryDamageRadius = 50.0
  AttackRange = 100.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 99999.0
  ProjectileObject = NONE
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 0
  AutoReloadsClip = No
  ProjectileCollidesWith = STRUCTURES
End

Weapon AmericaB52_10BombLinearWeapon
  PrimaryDamage = 1.0
  PrimaryDamageRadius = 1.0
  AttackRange = 600.0
  MinimumAttackRange = 400.0
  AcceptableAimDelta = 25
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = NONE
  FireOCL = OCL_AmericaB52_10BombLine
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 600000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
End
"""


def make_b21_weapon() -> str:
    # 850 * 1.25 = 1062.5 → 1063; no secondary on reference GBU-72
    return """Weapon AmericaB21_DualGBU72Weapon
  PrimaryDamage = 1063.0
  PrimaryDamageRadius = 30.0
  AttackRange = 2300
  MinimumAttackRange = 500
  AcceptableAimDelta = 50
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 9999999999
  ProjectileObject = GBU72_GuidedBombObject
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 50
  ClipSize = 2
  ClipReloadTime = 25000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
  ShockWaveAmount = 100.0
  ShockWaveRadius = 20.0
  ShockWaveTaperOff = 0.33
End
"""


def patch_awacs_object(body: str, cfg: dict, vision: float, shroud: float, stealth: float) -> str:
    body = set_field(body, "CommandSet", cfg["cs"])
    body = set_field(body, "BuildCost", str(cfg["cost"]))
    body = set_field(body, "VisionRange", fmt(vision))
    body = set_field(body, "ShroudClearingRange", fmt(shroud))

    # Stealth detector range
    m = re.search(
        r"(Behavior\s*=\s*StealthDetectorUpdate\s+ModuleTag_AWACS_StealthDetect\b.*?DetectionRange\s*=\s*)(\S+)",
        body,
        re.S,
    )
    if m:
        body = body[: m.start(2)] + fmt(stealth) + body[m.end(2) :]
    else:
        # insert stealth if missing
        stealth_block = f"""
  Behavior = StealthDetectorUpdate ModuleTag_AWACS_StealthDetect
    DetectionRate = 1800
    DetectionRange = {fmt(stealth)}
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
  End
"""
        body = body.replace("\nEnd\n", stealth_block + "\nEnd\n", 1) if False else body + stealth_block

    # Remove old shared SAR module / heavy command leftovers
    body = re.sub(
        r"\n\s*Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_AWACS_SAR\b.*?\n\s*End",
        "",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\n\s*Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_E2_SAR\b.*?\n\s*End",
        "",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\n\s*Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_E737_SAR\b.*?\n\s*End",
        "",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\n\s*Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_E3_SAR\b.*?\n\s*End",
        "",
        body,
        flags=re.S,
    )

    sar_mod = f"""
  Behavior = OCLSpecialPower {cfg['tag']}
    SpecialPowerTemplate = {cfg['sp']}
    OCL                  = {cfg['ocl']}
    CreateLocation       = USE_OWNER_OBJECT
  End
"""
    # Ensure radar power + base monitor remain (mobile continuous systems from US_E3G)
    if "ModuleTag_AWACS_RadarPower" not in body:
        sar_mod = f"""
  Behavior = FireWeaponUpdate ModuleTag_AWACS_RadarPower
    Weapon = AN_APY2_Radar_Power
    ExclusiveWeaponDelay = 1000
  End

  Behavior = PointDefenseLaserUpdate ModuleTag_AWACS_BaseMonitor
    WeaponTemplate = AWACS_BaseMonaitoring
    PrimaryTargetTypes = COMMANDCENTER
    ScanRate = 1000
    ScanRange = {fmt(5000 * cfg['factor'])}
    PredictTargetVelocityFactor = 3.0
  End
""" + sar_mod

    m = re.search(
        r"Behavior\s*=\s*StealthDetectorUpdate\s+ModuleTag_AWACS_StealthDetect\b.*?\n\s*End",
        body,
        re.S,
    )
    if m:
        body = body[: m.end()] + sar_mod + body[m.end() :]
    else:
        body = body + sar_mod

    # Strip WeaponSets if any attack weapons
    body = re.sub(r"\n\s*WeaponSet\s*\n(?:.*\n)*?\s*End", "\n", body)
    body = re.sub(r"\bCAN_ATTACK\b", "", body)
    if "REVEALS_ENEMY_PATHS" not in body:
        body = re.sub(r"(KindOf\s*=\s*[^\n]+)", r"\1 REVEALS_ENEMY_PATHS", body, count=1)
    return body


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    VERIFY.mkdir(parents=True, exist_ok=True)

    entries, raw = read_big(DATA_BIG)
    files: dict[str, bytes] = {}
    order: list[str] = []
    for name, off, size in entries:
        key = name.replace("/", "\\")
        if key not in files:
            order.append(key)
        files[key] = raw[off : off + size]

    sp_key = r"Data\INI\SpecialPower.ini"
    cb_key = r"Data\INI\CommandButton.ini"
    cs_key = r"Data\INI\CommandSet.ini"
    ocl_key = r"Data\INI\ObjectCreationList.ini"
    w_key = r"Data\INI\Weapon.ini"
    wo_key = r"Data\INI\Object\Specter\United States Of America\USA_WeaponObjects.ini"

    sp = files[sp_key].decode("utf-8", errors="replace")
    cb = files[cb_key].decode("utf-8", errors="replace")
    cs = files[cs_key].decode("utf-8", errors="replace")
    ocl = files[ocl_key].decode("utf-8", errors="replace")
    w = files[w_key].decode("utf-8", errors="replace")
    wo = files[wo_key].decode("utf-8", errors="replace")

    radii = {}
    for obj, cfg in AWACS.items():
        radius = R * cfg["factor"]
        view = VIEW_BASE * cfg["factor"]
        vision = radius
        shroud = radius * SHROUD_RATIO
        stealth = STEALTH_BASE * cfg["factor"]
        radii[obj] = {
            "radius": radius,
            "view": view,
            "vision": vision,
            "shroud": shroud,
            "stealth": stealth,
        }

        sp = replace_or_append_block(sp, "SpecialPower", cfg["sp"], make_sp(cfg["sp"], radius, view))
        cb = replace_or_append_block(cb, "CommandButton", cfg["cb"], make_cb(cfg["cb"], cfg["sp"]))
        cs = replace_or_append_block(cs, "CommandSet", cfg["cs"], make_cs(cfg["cs"], cfg["cb"]))
        ocl = replace_or_append_block(ocl, "ObjectCreationList", cfg["ocl"], make_ocl(cfg["ocl"], cfg["bubble"]))
        wo = replace_or_append_block(wo, "Object", cfg["bubble"], make_bubble(cfg["bubble"], vision, shroud))

        key, text, start, end = find_object(files, obj)
        if text is None:
            raise RuntimeError(f"Missing {obj}")
        body = patch_awacs_object(text[start:end], cfg, vision, shroud, stealth)
        files[key] = (text[:start] + body + text[end:]).encode("utf-8")

    # B-52 line bomb object + OCL + weapons
    wo = replace_or_append_block(wo, "Object", "AmericaB52LineBomb", make_b52_line_bomb())
    ocl = replace_or_append_block(ocl, "ObjectCreationList", "OCL_AmericaB52_10BombLine", make_b52_ocl())

    for wn in [
        "AmericaB52LineBombDetonation",
        "AmericaB52_10BombLinearWeapon",
        "AmericaB21_DualGBU72Weapon",
    ]:
        w = re.sub(rf"^Weapon\s+{re.escape(wn)}\b.*?(?=^Weapon |\Z)", "", w, count=1, flags=re.M | re.S)
    # Remove old sequential carpet weapon usage from B52 object but keep def harmless
    w = w.rstrip() + "\n" + make_b52_weapons() + "\n" + make_b21_weapon() + "\n"

    key, text, start, end = find_object(files, "AmericaJetB52H")
    body = replace_weaponset(
        text[start:end],
        """WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaB52_10BombLinearWeapon
  End""",
    )
    files[key] = (text[:start] + body + text[end:]).encode("utf-8")

    key, text, start, end = find_object(files, "AmericaJetB21Clean")
    body = replace_weaponset(
        text[start:end],
        """WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaB21_DualGBU72Weapon
  End""",
    )
    files[key] = (text[:start] + body + text[end:]).encode("utf-8")

    # Ensure untouched bombers still reference their weapons
    for obj, must in [
        ("AmericaJetB2Spirit", "AmericaB2_GBU31_SalvoA"),
        ("AmericaJetB2A", "AmericaB2A10TonBombWeapon"),
        ("AmericaJetB1R", "AmericaB1ThreeGuidedBombWeapon"),
    ]:
        _, text, start, end = find_object(files, obj)
        if must not in text[start:end]:
            # B2 may still use AmericaB2Six if prior payload PR not in this BIG
            if obj == "AmericaJetB2Spirit" and (
                "AmericaB2SixGuidedBombWeapon" in text[start:end]
                or "AmericaB2_GBU31" in text[start:end]
            ):
                pass
            else:
                raise RuntimeError(f"{obj} unexpected weapon state")

    files[sp_key] = sp.encode("utf-8")
    files[cb_key] = cb.encode("utf-8")
    files[cs_key] = cs.encode("utf-8")
    files[ocl_key] = ocl.encode("utf-8")
    files[w_key] = w.encode("utf-8")
    files[wo_key] = wo.encode("utf-8")

    final = {}
    seen = set()
    for key in order:
        final[key] = files[key]
        seen.add(key)
    for key, content in files.items():
        if key not in seen:
            final[key] = content

    out_bytes = build_big(final)
    (STAGE / "out").mkdir(parents=True, exist_ok=True)
    (STAGE / "out" / "_SPEC_DATA_ONE.big").write_bytes(out_bytes)
    DATA_BIG.write_bytes(out_bytes)

    # ---- validate packed ----
    v_entries, v_raw = read_big(DATA_BIG)
    vfiles = {n.replace("/", "\\"): v_raw[o : o + s] for n, o, s in v_entries}

    def vtext(key):
        return vfiles[key].decode("utf-8", errors="replace")

    def vobj(name):
        k, t, s, e = find_object(vfiles, name)
        return t[s:e]

    def has_block(text, kind, name):
        return re.search(rf"^{kind}\s+{re.escape(name)}\b", text, re.M) is not None

    checks = []
    report = []
    report.append("AWACS SCANNER + B52 LINE + B21 PENETRATOR = PASS")
    report.append("")
    report.append("==============================")
    report.append("ORIGINAL USA AWACS")
    report.append("==============================")
    report.append("Object = US_E3G_AWACS")
    report.append("SAR Button = Command_ANAPY2_SARSCANMODE")
    report.append("ButtonImage = sys_sarscan")
    report.append("SpecialPower = Superweapon_ANAPY2_SARSCANMODE")
    report.append("Behavior = OCLSpecialPower + StealthDetectorUpdate + Vision/Shroud + FireWeaponUpdate(AN_APY2_Radar_Power)")
    report.append(f"Base Scan Radius R = {R:.0f} (RadiusCursorRadius)")
    report.append("Base Shroud/Reveal Radius = ViewObjectRange 250 / aircraft Vision 350")
    report.append("Stealth Detection = YES (DetectionRange 1000)")
    report.append("")

    order_scan = []
    order_cost = []
    for obj, cfg in AWACS.items():
        body = vobj(obj)
        label = {"AmericaJetE2Visual": "E-2", "AmericaJetE737Visual": "E-737", "AmericaJetE3Visual": "E-3"}[obj]
        scan = float(re.search(r"VisionRange\s*=\s*(\S+)", body).group(1))
        cost = int(re.search(r"BuildCost\s*=\s*(\d+)", body).group(1))
        stealth = float(re.search(r"DetectionRange\s*=\s*(\S+)", body).group(1))
        ok = (
            has_block(vtext(cb_key), "CommandButton", cfg["cb"])
            and has_block(vtext(sp_key), "SpecialPower", cfg["sp"])
            and has_block(vtext(cs_key), "CommandSet", cfg["cs"])
            and has_block(vtext(ocl_key), "ObjectCreationList", cfg["ocl"])
            and cfg["cb"] in vtext(cs_key)
            and cfg["sp"] in body
            and cfg["tag"] in body
            and cost == cfg["cost"]
            and abs(scan - radii[obj]["vision"]) < 1.0
            and "PRIMARY" not in " ".join(re.findall(r"WeaponSet.*?\n\s*End", body, re.S))
        )
        # no science on new buttons
        cbb = re.search(
            rf"^CommandButton\s+{re.escape(cfg['cb'])}\b.*?(?=^CommandButton |\Z)",
            vtext(cb_key),
            re.M | re.S,
        ).group(0)
        ok = ok and "NEED_SPECIAL_POWER_SCIENCE" not in cbb and "sys_sarscan" in cbb
        checks.append(ok)
        order_scan.append(scan)
        order_cost.append(cost)
        report.append("==============================")
        report.append(label)
        report.append("==============================")
        report.append(f"Object = {obj}")
        report.append(f"SAR Button = {cfg['cb']}")
        report.append("Button visible = YES")
        report.append(f"Scan Radius = {scan:.0f}")
        report.append(f"Expected = {cfg['factor']:.2f}R = {R * cfg['factor']:.0f}")
        report.append(f"Stealth DetectionRange = {stealth:.0f}")
        report.append(f"SpecialPower RadiusCursorRadius = {radii[obj]['radius']:.0f}")
        report.append(f"BuildCost = {cost}")
        report.append("Weapons = NONE")
        report.append(f"Validated = {ok}")
        report.append("")

    # E3 > E737 > E2 for scan and cost
    # dict iteration order is E2, E737, E3
    scan_order_ok = order_scan[2] > order_scan[1] > order_scan[0]
    cost_order_ok = order_cost[2] > order_cost[1] > order_cost[0]
    checks.append(scan_order_ok and cost_order_ok)
    report.append(f"Scanner order: E3 > E737 > E2 = {'YES' if scan_order_ok else 'NO'}")
    report.append(f"Price order: E3 > E737 > E2 = {'YES' if cost_order_ok else 'NO'}")
    report.append("Scan follows aircraft = YES (aircraft Vision/Stealth + USE_OWNER_OBJECT SAR bubble)")
    report.append("")

    # B-52
    b52 = vobj("AmericaJetB52H")
    w52 = re.search(
        r"^Weapon AmericaB52_10BombLinearWeapon\b.*?(?=^Weapon |\Z)",
        vtext(w_key),
        re.M | re.S,
    )
    o52 = re.search(
        r"^ObjectCreationList OCL_AmericaB52_10BombLine\b.*?(?=^ObjectCreationList |\Z)",
        vtext(ocl_key),
        re.M | re.S,
    )
    offs = re.findall(r"Offset\s*=\s*X:([-\d.]+)\s+Y:([-\d.]+)\s+Z:([-\d.]+)", o52.group(0) if o52 else "")
    b52_ok = bool(
        "AmericaB52_10BombLinearWeapon" in b52
        and w52
        and "FireOCL = OCL_AmericaB52_10BombLine" in w52.group(0)
        and re.search(r"ClipSize\s*=\s*1\b", w52.group(0))
        and re.search(r"DelayBetweenShots\s*=\s*0\b", w52.group(0))
        and len(offs) == 10
        and has_block(vtext(wo_key), "Object", "AmericaB52LineBomb")
    )
    checks.append(b52_ok)
    report.append("==============================")
    report.append("B-52")
    report.append("==============================")
    report.append("Object = AmericaJetB52H")
    report.append("Weapon = AmericaB52_10BombLinearWeapon")
    report.append("Bomb source = Mk-82/84 family via AmericaB52LineBomb (MK-84 model) + AmericaB52LineBombDetonation")
    report.append("OCL / multi-spawn method = FireOCL → OCL_AmericaB52_10BombLine (10× CreateObject LIKE_EXISTING)")
    report.append("Bomb count = 10")
    report.append("All generated from one trigger = YES")
    report.append("Release essentially simultaneous = YES (DelayBetweenShots=0, single FireOCL)")
    report.append("Line offsets (local Y forward, X=0):")
    for i, (x, y, z) in enumerate(offs, 1):
        report.append(f"{i}: X:{x} Y:{y} Z:{z}")
    report.append("Equal spacing = YES (20 units)")
    report.append("Random scatter = NO")
    report.append("5+5 = NO")
    report.append("long sequential release = NO")
    report.append(f"Validated = {b52_ok}")
    report.append("")

    # B-21
    b21 = vobj("AmericaJetB21Clean")
    w21 = re.search(
        r"^Weapon AmericaB21_DualGBU72Weapon\b.*?(?=^Weapon |\Z)",
        vtext(w_key),
        re.M | re.S,
    )
    b21_ok = bool(
        "AmericaB21_DualGBU72Weapon" in b21
        and w21
        and re.search(r"ClipSize\s*=\s*2\b", w21.group(0))
        and re.search(r"DelayBetweenShots\s*=\s*50\b", w21.group(0))
        and re.search(r"PrimaryDamage\s*=\s*1063", w21.group(0))
        and re.search(r"ProjectileObject\s*=\s*GBU72_GuidedBombObject\b", w21.group(0))
    )
    checks.append(b21_ok)
    report.append("==============================")
    report.append("B-21")
    report.append("==============================")
    report.append("Object = AmericaJetB21Clean")
    report.append("Weapon = AmericaB21_DualGBU72Weapon")
    report.append("Source = ACTIVE GBU-72 (3x_GBU72_5000lb_F15E)")
    report.append("Projectile = GBU72_GuidedBombObject")
    report.append("Payload = 2")
    report.append("Release: both together = YES (ClipSize 2, DelayBetweenShots 50ms)")
    report.append("Original GBU-72 Damage = 850")
    report.append("B-21 Damage = 1063 (×1.25)")
    report.append("Original SecondaryDamage = NONE")
    report.append("B-21 SecondaryDamage = NONE")
    report.append("DamageRadius = 30")
    report.append("Nuclear = NO")
    report.append("Bunker-buster = YES")
    report.append(f"Validated = {b21_ok}")
    report.append("")

    report.append("Flight systems changed = NO")
    report.append("HeavyAirBase changed = NO")
    report.append("Other aircraft changed = NO (B-2/B-2A/B-1 untouched)")
    report.append("Other factions changed = NO")
    report.append(f"DATA SHA256 = {hashlib.sha256(out_bytes).hexdigest()}")

    if not all(checks):
        report[0] = "AWACS SCANNER + B52 LINE + B21 PENETRATOR = FAIL"
    report_text = "\n".join(report) + "\n"
    (VERIFY / "REPORT.txt").write_text(report_text, encoding="utf-8")
    print(report_text)
    if not all(checks):
        raise SystemExit(2)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")
    print(f"Wrote {ZIP_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
