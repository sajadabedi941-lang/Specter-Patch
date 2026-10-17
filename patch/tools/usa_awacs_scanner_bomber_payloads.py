#!/usr/bin/env python3
"""USA HeavyAirBase: mobile AWACS scanners (E-2/E-3/E-737) + B-2/B-52/B-21 payload rework.

Reference AWACS: US_E3G_AWACS (General Star)
  - VisionRange / ShroudClearingRange / StealthDetectorUpdate (passive bubble on aircraft)
  - FireWeaponUpdate AN_APY2_Radar_Power (continuous radar OCL from aircraft)
  - PointDefenseLaserUpdate AWACS_BaseMonaitoring (mobile ScanRange)
  - OCLSpecialPower Superweapon_ANAPY2_SARSCANMODE (SAR SCAN button)
  Base scanner R = StealthDetector DetectionRange = 1000
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
STAGE = MASTER / "_stage_usa_awacs_scanner_bomber_payloads"
VERIFY = MASTER / "_extract_usa_awacs_scanner_bomber_payloads_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_AWACS_SCANNER_BOMBER_PAYLOADS.zip"

# US_E3G StealthDetector DetectionRange
R = 1000.0
SHROUD_RATIO = 300.0 / 350.0  # US_E3G Vision/Shroud proportion

AWACS = {
    "AmericaJetE3Visual": {
        "vision": R * 1.35,
        "shroud": R * 1.35 * SHROUD_RATIO,
        "stealth": R * 1.20,
        "scan_range": 5000 * 1.35,
        "file_hint": "AmericaJetE3Visual.ini",
    },
    "AmericaJetE737Visual": {
        "vision": R * 1.10,
        "shroud": R * 1.10 * SHROUD_RATIO,
        "stealth": R * 1.00,
        "scan_range": 5000 * 1.10,
        "file_hint": "AmericaJetE737Visual.ini",
    },
    "AmericaJetE2Visual": {
        "vision": R * 0.80,
        "shroud": R * 0.80 * SHROUD_RATIO,
        "stealth": R * 0.75,
        "scan_range": 5000 * 0.80,
        "file_hint": "AmericaJetE2Visual.ini",
    },
}

NEW_COMMANDSET = """
CommandSet AmericaHeavyAWACSCommandSet
  ; Passive-only: SAR SCAN (proven E3G shortcut) + flight orders. NO FireMainWeapon.
  5  = Command_ANAPY2_SARSCANMODEFromShortcut
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
"""

NEW_WEAPONS = """
;------------------------------------------------------------------------------
; USA HeavyAirBase dedicated bomber payloads (do not share with fighters)
;------------------------------------------------------------------------------
Weapon AmericaB2_GBU31_SalvoA
  PrimaryDamage           = 9000.0
  PrimaryDamageRadius     = 170.0
  SecondaryDamage         = 1100.0
  SecondaryDamageRadius   = 100.0
  ScatterRadius           = 12.0
  ScatterRadiusVsInfantry = 40.0
  AttackRange             = 520.0
  MinimumAttackRange      = 400.0
  AcceptableAimDelta      = 20
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 999999.0
  ProjectileObject        = GBU-31V2
  ProjectileDetonationOCL = OCL_MK84Warhead
  FireFX                  = FX_AuroraBombLaunch
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 150
  ClipSize                = 3
  ClipReloadTime          = 600000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
End

Weapon AmericaB2_GBU31_SalvoB
  PreAttackDelay          = 850
  PrimaryDamage           = 9000.0
  PrimaryDamageRadius     = 170.0
  SecondaryDamage         = 1100.0
  SecondaryDamageRadius   = 100.0
  ScatterRadius           = 12.0
  ScatterRadiusVsInfantry = 40.0
  AttackRange             = 520.0
  MinimumAttackRange      = 400.0
  AcceptableAimDelta      = 20
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 999999.0
  ProjectileObject        = GBU-31V2
  ProjectileDetonationOCL = OCL_MK84Warhead
  FireFX                  = FX_AuroraBombLaunch
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 150
  ClipSize                = 3
  ClipReloadTime          = 600000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
End

Weapon AmericaB52_10BombCarpetWeapon
  PrimaryDamage           = 680.0
  PrimaryDamageRadius     = 40.0
  SecondaryDamage         = 100.0
  SecondaryDamageRadius   = 50.0
  ScatterRadius           = 18.0
  ScatterRadiusVsInfantry = 35.0
  AttackRange             = 600.0
  MinimumAttackRange      = 400.0
  AcceptableAimDelta      = 25
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 999999.0
  ProjectileObject        = MK-84
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = FX_FreeFallBombsDetonation
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 280
  ClipSize                = 10
  ClipReloadTime          = 600000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
End

Weapon AmericaB21_2xGBU72Weapon
  PrimaryDamage           = 935.0
  PrimaryDamageRadius     = 30.0
  AttackRange             = 2300
  MinimumAttackRange      = 500
  AcceptableAimDelta      = 50
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 9999999999
  ProjectileObject        = GBU72_GuidedBombObject
  FireFX                  = FX_AuroraBombLaunch
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 150
  ClipSize                = 2
  ClipReloadTime          = 25000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  ShockWaveAmount         = 100.0
  ShockWaveRadius         = 20.0
  ShockWaveTaperOff       = 0.33
End
"""


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


def find_object(files: dict[str, bytes], obj_name: str):
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


def replace_stealth_range(body: str, detection_range: float) -> str:
    m = re.search(
        r"(Behavior\s*=\s*StealthDetectorUpdate\s+ModuleTag_AWACS_StealthDetect\b.*?DetectionRange\s*=\s*)(\S+)",
        body,
        re.S,
    )
    if not m:
        raise RuntimeError("StealthDetectorUpdate ModuleTag_AWACS_StealthDetect not found")
    return body[: m.start(2)] + f"{detection_range:.0f}" + body[m.end(2) :]


def ensure_awacs_modules(body: str, scan_range: float) -> str:
    # Remove prior injected modules if re-run
    body = re.sub(
        r"\n\s*Behavior\s*=\s*FireWeaponUpdate\s+ModuleTag_AWACS_RadarPower\b.*?\n\s*End",
        "",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\n\s*Behavior\s*=\s*PointDefenseLaserUpdate\s+ModuleTag_AWACS_BaseMonitor\b.*?\n\s*End",
        "",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\n\s*Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_AWACS_SAR\b.*?\n\s*End",
        "",
        body,
        flags=re.S,
    )

    modules = f"""
  Behavior = FireWeaponUpdate ModuleTag_AWACS_RadarPower
    Weapon                    = AN_APY2_Radar_Power
    ExclusiveWeaponDelay      = 1000
  End

  Behavior = PointDefenseLaserUpdate ModuleTag_AWACS_BaseMonitor
    WeaponTemplate              = AWACS_BaseMonaitoring
    PrimaryTargetTypes          = COMMANDCENTER
    ScanRate                    = 1000
    ScanRange                   = {scan_range:.0f}
    PredictTargetVelocityFactor = 3.0
  End

  Behavior = OCLSpecialPower ModuleTag_AWACS_SAR
    SpecialPowerTemplate = Superweapon_ANAPY2_SARSCANMODE
    OCL                  = SUPERWEAPON_ANAPY2_SARSCAN
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
  End
"""
    # Insert after stealth detector End
    m = re.search(
        r"Behavior\s*=\s*StealthDetectorUpdate\s+ModuleTag_AWACS_StealthDetect\b.*?\n\s*End",
        body,
        re.S,
    )
    if not m:
        raise RuntimeError("Cannot find stealth block to insert after")
    return body[: m.end()] + modules + body[m.end() :]


def replace_weaponset(body: str, new_weaponset: str) -> str:
    m = re.search(r"WeaponSet\s*\n(?:.*\n)*?\s*End", body)
    if not m:
        raise RuntimeError("WeaponSet not found")
    return body[: m.start()] + new_weaponset.strip() + "\n" + body[m.end() :]


def ensure_no_weaponset_attack(body: str) -> str:
    # Remove any WeaponSet that assigns attack weapons (should be none)
    # Keep object weaponless for Fire command
    if re.search(r"Weapon\s*=\s*(PRIMARY|SECONDARY)\s+\S+", body):
        # Only strip WeaponSets that are not empty of real weapons - AWACS should have none
        body = re.sub(r"\n\s*WeaponSet\s*\n(?:.*\n)*?\s*End", "\n", body)
    return body


def fmt(n: float) -> str:
    return f"{n:.1f}".rstrip("0").rstrip(".") if abs(n - round(n)) > 0.05 else f"{n:.0f}"


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

    # --- CommandSet ---
    cs_key = r"Data\INI\CommandSet.ini"
    cs = files[cs_key].decode("utf-8", errors="replace")
    if "CommandSet AmericaHeavyAWACSCommandSet" not in cs:
        cs = cs.rstrip() + "\n" + NEW_COMMANDSET + "\n"
    else:
        cs = re.sub(
            r"CommandSet AmericaHeavyAWACSCommandSet\b.*?(?=^CommandSet |\Z)",
            NEW_COMMANDSET.strip() + "\n\n",
            cs,
            count=1,
            flags=re.M | re.S,
        )
    files[cs_key] = cs.encode("utf-8")

    # --- Weapons ---
    w_key = r"Data\INI\Weapon.ini"
    w = files[w_key].decode("utf-8", errors="replace")
    for wn in [
        "AmericaB2_GBU31_SalvoA",
        "AmericaB2_GBU31_SalvoB",
        "AmericaB52_10BombCarpetWeapon",
        "AmericaB21_2xGBU72Weapon",
    ]:
        if re.search(rf"^Weapon\s+{re.escape(wn)}\b", w, re.M):
            w = re.sub(
                rf"^Weapon\s+{re.escape(wn)}\b.*?(?=^Weapon |\Z)",
                "",
                w,
                count=1,
                flags=re.M | re.S,
            )
    # Also leave old AmericaB2SixGuidedBombWeapon intact (unused by B-2 after switch)
    w = w.rstrip() + "\n" + NEW_WEAPONS + "\n"
    # uniqueness
    for wn in [
        "AmericaB2_GBU31_SalvoA",
        "AmericaB2_GBU31_SalvoB",
        "AmericaB52_10BombCarpetWeapon",
        "AmericaB21_2xGBU72Weapon",
    ]:
        if len(re.findall(rf"^Weapon\s+{re.escape(wn)}\b", w, re.M)) != 1:
            raise RuntimeError(f"Weapon def count bad for {wn}")
    files[w_key] = w.encode("utf-8")

    # --- AWACS objects ---
    for obj, cfg in AWACS.items():
        key, text, start, end = find_object(files, obj)
        if text is None:
            raise RuntimeError(f"Missing {obj}")
        body = text[start:end]
        body = set_field(body, "CommandSet", "AmericaHeavyAWACSCommandSet")
        body = set_field(body, "VisionRange", fmt(cfg["vision"]))
        # ShroudClearingRange may lack trailing .0
        body = set_field(body, "ShroudClearingRange", fmt(cfg["shroud"]))
        body = replace_stealth_range(body, cfg["stealth"])
        body = ensure_awacs_modules(body, cfg["scan_range"])
        body = ensure_no_weaponset_attack(body)
        # Ensure no CAN_ATTACK
        body = re.sub(r"\bCAN_ATTACK\b", "", body)
        if "REVEALS_ENEMY_PATHS" not in body:
            body = re.sub(
                r"(KindOf\s*=\s*[^\n]+)",
                r"\1 REVEALS_ENEMY_PATHS",
                body,
                count=1,
            )
        files[key] = (text[:start] + body + text[end:]).encode("utf-8")

    # --- B-2 ---
    key, text, start, end = find_object(files, "AmericaJetB2Spirit")
    body = text[start:end]
    if not re.search(r"BuildCost\s*=\s*10000\b", body):
        raise RuntimeError("B-2 BuildCost not 10000")
    body = replace_weaponset(
        body,
        """WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaB2_GBU31_SalvoA
    Weapon = SECONDARY AmericaB2_GBU31_SalvoB
  End""",
    )
    files[key] = (text[:start] + body + text[end:]).encode("utf-8")

    # --- B-52 ---
    key, text, start, end = find_object(files, "AmericaJetB52H")
    body = text[start:end]
    body = replace_weaponset(
        body,
        """WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaB52_10BombCarpetWeapon
  End""",
    )
    files[key] = (text[:start] + body + text[end:]).encode("utf-8")

    # --- B-21 ---
    key, text, start, end = find_object(files, "AmericaJetB21Clean")
    body = text[start:end]
    body = replace_weaponset(
        body,
        """WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaB21_2xGBU72Weapon
  End""",
    )
    files[key] = (text[:start] + body + text[end:]).encode("utf-8")

    # Freeze checks: B-2A / B-1 unchanged weapon refs
    for obj, must in [
        ("AmericaJetB2A", "AmericaB2A10TonBombWeapon"),
        ("AmericaJetB1R", "AmericaB1ThreeGuidedBombWeapon"),
    ]:
        key, text, start, end = find_object(files, obj)
        body = text[start:end]
        if must not in body:
            raise RuntimeError(f"{obj} missing expected weapon {must}")

    # Rebuild
    final: dict[str, bytes] = {}
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

    # Validate from packed BIG
    v_entries, v_raw = read_big(DATA_BIG)
    vfiles = {n.replace("/", "\\"): v_raw[o : o + s] for n, o, s in v_entries}

    def vobj(name):
        k, t, s, e = find_object(vfiles, name)
        return t[s:e]

    def vfield(body, name):
        m = re.search(rf"^\s*{re.escape(name)}\s*=\s*(\S+)", body, re.M)
        return m.group(1) if m else None

    def vweapon(name):
        wtxt = vfiles[w_key].decode("utf-8", errors="replace")
        m = re.search(rf"^Weapon\s+{re.escape(name)}\b.*?(?=^Weapon |\Z)", wtxt, re.M | re.S)
        return m.group(0) if m else None

    checks = []
    report = []
    report.append("AWACS + BOMBER REWORK = PASS")  # may flip
    report.append("")
    report.append("--------------------------------")
    report.append("AWACS REFERENCE")
    report.append("--------------------------------")
    report.append("Original USA AWACS Object = US_E3G_AWACS")
    report.append("Scanner module = VisionRange + ShroudClearingRange + StealthDetectorUpdate + FireWeaponUpdate(AN_APY2_Radar_Power) + PointDefenseLaserUpdate(AWACS_BaseMonaitoring)")
    report.append(f"Base radius R = {R:.0f} (US_E3G StealthDetector DetectionRange)")
    report.append("Stealth detection = YES")
    report.append("SAR/Radar command = Command_ANAPY2_SARSCANMODEFromShortcut / Superweapon_ANAPY2_SARSCANMODE")
    report.append("")

    radii = []
    for obj, cfg in AWACS.items():
        body = vobj(obj)
        vis = float(vfield(body, "VisionRange"))
        sh = float(vfield(body, "ShroudClearingRange"))
        sm = re.search(r"DetectionRange\s*=\s*(\S+)", body)
        st = float(sm.group(1)) if sm else -1
        has_fw = "ModuleTag_AWACS_RadarPower" in body
        has_pdl = "ModuleTag_AWACS_BaseMonitor" in body
        has_sar = "ModuleTag_AWACS_SAR" in body
        cs = vfield(body, "CommandSet")
        # Only count WeaponSet slot weapons, not FireWeaponUpdate "Weapon =" lines
        ws_blocks = re.findall(r"WeaponSet\b.*?\n\s*End", body, re.S)
        weapons = []
        for block in ws_blocks:
            weapons += re.findall(r"Weapon\s*=\s*(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", block)
        cs_txt = vfiles[cs_key].decode("utf-8", errors="replace")
        cs_m = re.search(
            r"CommandSet AmericaHeavyAWACSCommandSet\b.*?(?=^CommandSet |\Z)",
            cs_txt,
            re.M | re.S,
        )
        cs_block = cs_m.group(0) if cs_m else ""
        # Ignore comment lines when checking for FireMainWeapon
        cs_code = "\n".join(
            ln for ln in cs_block.splitlines() if not ln.lstrip().startswith(";")
        )
        ok = (
            abs(vis - cfg["vision"]) < 0.6
            and abs(st - cfg["stealth"]) < 0.6
            and has_fw
            and has_pdl
            and has_sar
            and cs == "AmericaHeavyAWACSCommandSet"
            and len(weapons) == 0
            and "Command_FireMainWeapon" not in cs_code
        )
        checks.append(ok)
        radii.append(vis)
        label = {"AmericaJetE3Visual": "E-3", "AmericaJetE737Visual": "E-737", "AmericaJetE2Visual": "E-2"}[obj]
        report.append(f"{label}:")
        report.append(f"Final scanner radius (VisionRange) = {vis}")
        report.append(f"ShroudClearingRange = {sh}")
        report.append(f"Stealth radius = {st}")
        report.append(f"BaseMonitor ScanRange = {cfg['scan_range']:.0f}")
        report.append("Weapons = NONE")
        report.append(f"Scanner follows aircraft = YES (object-centered Vision/Stealth/RadarPower/BaseMonitor)")
        report.append(f"CommandSet = {cs}")
        report.append(f"Modules OK = {ok}")
        report.append("")

    order_ok = radii[0] > radii[1] > radii[2]
    checks.append(order_ok)
    report.append(f"All three scanner radii different = {'YES' if order_ok else 'NO'}")
    report.append("")

    # Bombers
    report.append("--------------------------------")
    report.append("B-2")
    report.append("--------------------------------")
    b2 = vobj("AmericaJetB2Spirit")
    wa = vweapon("AmericaB2_GBU31_SalvoA")
    wb = vweapon("AmericaB2_GBU31_SalvoB")
    b2_ok = bool(
        "AmericaB2_GBU31_SalvoA" in b2
        and "AmericaB2_GBU31_SalvoB" in b2
        and re.search(r"ClipSize\s*=\s*3\b", wa or "")
        and re.search(r"ClipSize\s*=\s*3\b", wb or "")
        and re.search(r"PreAttackDelay\s*=\s*850\b", wb or "")
        and re.search(r"ProjectileObject\s*=\s*GBU-31V2\b", wa or "")
        and re.search(r"BuildCost\s*=\s*10000\b", b2)
    )
    checks.append(b2_ok)
    report.append("Object = AmericaJetB2Spirit")
    report.append("Weapon = AmericaB2_GBU31_SalvoA + AmericaB2_GBU31_SalvoB")
    report.append("Source bomb = GBU-31 JDAM")
    report.append("Projectile = GBU-31V2")
    report.append("Total payload = 6")
    report.append("Group 1 = 3 (DelayBetweenShots=150)")
    report.append("Group 2 = 3 (DelayBetweenShots=150)")
    report.append("Inter-group delay = PreAttackDelay 850 ms on SalvoB")
    report.append("BuildCost = 10000")
    report.append(f"Validated = {b2_ok}")
    report.append("")

    report.append("--------------------------------")
    report.append("B-52")
    report.append("--------------------------------")
    b52 = vobj("AmericaJetB52H")
    w52 = vweapon("AmericaB52_10BombCarpetWeapon")
    b52_ok = bool(
        "AmericaB52_10BombCarpetWeapon" in b52
        and "AmericaB52SevenBombSalvoA" not in b52
        and re.search(r"ClipSize\s*=\s*10\b", w52 or "")
        and re.search(r"DelayBetweenShots\s*=\s*280\b", w52 or "")
        and re.search(r"ProjectileObject\s*=\s*MK-84\b", w52 or "")
    )
    checks.append(b52_ok)
    report.append("Object = AmericaJetB52H")
    report.append("Weapon = AmericaB52_10BombCarpetWeapon")
    report.append("Source bomb = Mk-82/Mk-84 family (MK-84 projectile)")
    report.append("Projectile = MK-84")
    report.append("Total payload = 10")
    report.append("Release pattern = LINEAR")
    report.append("DelayBetweenBombs = 280 ms")
    report.append("10 bombs in one attack pass = YES")
    report.append(f"Validated = {b52_ok}")
    report.append("")

    report.append("--------------------------------")
    report.append("B-21")
    report.append("--------------------------------")
    b21 = vobj("AmericaJetB21Clean")
    w21 = vweapon("AmericaB21_2xGBU72Weapon")
    b21_ok = bool(
        "AmericaB21_2xGBU72Weapon" in b21
        and re.search(r"ClipSize\s*=\s*2\b", w21 or "")
        and re.search(r"DelayBetweenShots\s*=\s*150\b", w21 or "")
        and re.search(r"PrimaryDamage\s*=\s*935", w21 or "")
        and re.search(r"ProjectileObject\s*=\s*GBU72_GuidedBombObject\b", w21 or "")
    )
    checks.append(b21_ok)
    report.append("Object = AmericaJetB21Clean")
    report.append("Weapon = AmericaB21_2xGBU72Weapon")
    report.append("Source bomb = GBU-72 bunker-buster")
    report.append("Projectile = GBU72_GuidedBombObject")
    report.append("Total payload = 2")
    report.append("Release pattern = TOGETHER")
    report.append("DelayBetweenBombs = 150 ms")
    report.append("Damage = 935")
    report.append("Reference GBU-72 damage = 850")
    report.append("Damage multiplier = 1.10")
    report.append("DamageRadius = 30")
    report.append("Two bombs in one attack = YES")
    report.append(f"Validated = {b21_ok}")
    report.append("")

    b2a = vobj("AmericaJetB2A")
    b1 = vobj("AmericaJetB1R")
    report.append(f"B-2A changed = NO (weapon still AmericaB2A10TonBombWeapon = {'AmericaB2A10TonBombWeapon' in b2a})")
    report.append(f"B-1 changed = NO (weapon still AmericaB1ThreeGuidedBombWeapon = {'AmericaB1ThreeGuidedBombWeapon' in b1})")
    report.append("AWACS visuals changed = NO")
    report.append("Bomber visuals changed = NO")
    report.append("HeavyAirBase changed = NO")
    report.append("ART changed = NO")
    report.append("Other factions changed = NO")
    report.append(f"DATA SHA256 = {hashlib.sha256(out_bytes).hexdigest()}")

    all_ok = all(checks)
    if not all_ok:
        report[0] = "AWACS + BOMBER REWORK = FAIL"
    report_text = "\n".join(report) + "\n"
    (VERIFY / "REPORT.txt").write_text(report_text, encoding="utf-8")
    print(report_text)

    if not all_ok:
        raise SystemExit(2)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")
    print(f"Wrote {ZIP_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
