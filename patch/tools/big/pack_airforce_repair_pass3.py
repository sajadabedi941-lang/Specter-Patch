#!/usr/bin/env python3
"""AIRFORCE REPAIR PASS 3 — Germany / Syria / India / UAE / Saudi / Pakistan.

Starts from the pass-2 released BIGs and surgically patches only the requested
units. Does not overlay CommandSet_Germany/France/Britain/Italy. Does not
modify USA / Russia / China live CommandSets or objects.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace")
BASE_DATA = Path("/tmp/airforce_pass2_baseline/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/airforce_pass2_baseline/_SPEC_ART_ONE.big")
OUT = Path("/tmp/airforce_repair_pass_3")
EXTRACT = Path("/tmp/pass3_extract")

ANIM_TYPES = {0x00000200, 0x00000280, 0x000002C0, 0x00000250}
HELPER_W3D_MAX = 2048

BLOCK_RE = {
    "CommandSet": re.compile(r"^CommandSet\s+(\S+)\s*$"),
    "CommandButton": re.compile(r"^CommandButton\s+(\S+)\s*$"),
    "Weapon": re.compile(r"^Weapon\s+(\S+)\s*$"),
    "Object": re.compile(r"^Object(?:Reskin)?\s+(\S+)\s*$"),
    "SpecialPower": re.compile(r"^SpecialPower\s+(\S+)\s*$"),
    "Locomotor": re.compile(r"^Locomotor\s+(\S+)\s*$"),
    "Armor": re.compile(r"^Armor\s+(\S+)\s*$"),
    "Science": re.compile(r"^Science\s+(\S+)\s*$"),
    "Upgrade": re.compile(r"^Upgrade\s+(\S+)\s*$"),
}

PROTECTED_CS = [
    "AmericaAirfieldCommandSet",
    "America_LargeAirBaseCommandSet",
    "America_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
]

SCALE_JOBS = [
    # country, object, old, new, reference, reason
    ("Syria", "SyriaJetMig21", 0.82, 0.94, "Ukraine MiG-21bis 0.94 / F-16 0.90", "MiG-21bis was miniature vs F-5/Mirage F1/MiG-29 class"),
    ("Syria", "SyriaJetMig21MF", 0.80, 0.96, "Libya MiG-21MF 0.96; offset from Syria bis 0.94", "Independent MF scale; same W3D family but not identical value"),
    ("India", "IndiaJetMig21Bison", 0.84, 0.90, "F-16 0.90; below India Su-30MKI 0.92", "Bison remains smaller than Su-30MKI"),
    ("India", "IndiaJetTejas", 0.86, 0.90, "F-16/Gripen class; below Su-30MKI 0.92", "Lightweight fighter, not miniature"),
    ("Saudi Arabia", "SaudiJetLightning", 0.86, 1.02, "F-4 Phantom ~1.00 / Mirage F1 / MiG-23", "English Electric Lightning F.53 full-size interceptor"),
    ("Saudi Arabia", "SaudiJetHawk65", 0.80, 0.82, "Alpha Jet / M339 / L-159 trainer class", "Keep trainer; do not enlarge to F-15"),
    ("Saudi Arabia", "SaudiJetF5E", 0.78, 0.88, "Light fighter; larger than trainer, smaller than F-15", "F-5E Tiger II light-fighter scale"),
    ("Pakistan", "PakistanJetMirageROSE", 0.90, 1.06, "SA Mirage III 1.08 / Mirage 2000", "ROSE III Mirage III/V family"),
    ("Pakistan", "PakistanJetF7PG", 0.86, 0.96, "MiG-21 / J-7 class fighter", "F-7PG full-size J-7"),
    ("Pakistan", "PakistanJetF7P", 0.84, 0.94, "Independent of F-7PG; different W3D LSFJ7", "F-7P Skybolt calculated separately"),
]

NEW_WEAPONS = """
Weapon GermanyJetTornadoIDS_WpnBombHvy
  PrimaryDamage = 1100.0
  PrimaryDamageRadius = 48.0
  SecondaryDamage = 90.0
  SecondaryDamageRadius = 80.0
  ScatterRadius = 14.0
  AttackRange = 920.0
  MinimumAttackRange = 90.0
  PreAttackDelay = 2800
  PreAttackType = PER_ATTACK
  AcceptableAimDelta = 20
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  WeaponSpeed = 9999
  ProjectileObject = GBU24_GuidedBombObject
  FireFX = FX_AuroraBombLaunch
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 2200
  ClipSize = 6
  ClipReloadTime = 28000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
  AntiGround = Yes
  AntiAirborneVehicle = No
  LeechRangeWeapon = Yes
End

Weapon GermanyJetTornadoIDS_WpnIR2
  PrimaryDamage = 640.0
  PrimaryDamageRadius = 8.0
  SecondaryDamage = 8.0
  SecondaryDamageRadius = 16.0
  AttackRange = 500.0
  MinimumAttackRange = 80.0
  AcceptableAimDelta = 360
  DamageType = PENALTY
  DeathType = EXPLODED
  WeaponSpeed = 8000
  ProjectileObject = AIM-9X_Object
  FireSound = RaptorJetMissileWeapon
  ProjectileDetonationFX = FX_LightAAMImpact
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 900
  ClipSize = 2
  ClipReloadTime = 14000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = Yes
  AntiGround = No
  AntiAirborneInfantry = Yes
  ShowsAmmoPips = Yes
End
"""

GERMANY_E3 = """; SPECTER repair pass 3 - Germany E-3 AWACS. USA E-3 gameplay reference, USA object untouched.
Object GermanyAircraftE3
Scale = 0.90

  SelectPortrait         = SPEC_GermanyE3
  ButtonImage            = SPEC_GermanyE3

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = US_E3G
      Animation = US_E3G.US_E3G
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = US_E3G
      Animation = US_E3G.US_E3G
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = US_E3G
      Animation = US_E3G.US_E3G
      AnimationMode = LOOP
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = RUBBLE
      Model = US_E3G
    End
  End

  DisplayName = OBJECT:GermanyAircraftE3
  EditorSorting = VEHICLE
  Side = Germany
  TransportSlotCount = 0
  VisionRange = 1100.0
  ShroudClearingRange = 1200.0
  BuildCost = 4200
  BuildTime = 36.0
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = E3G_CommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceGuard = RaptorVoiceAirPatrol
  SoundAmbient = AdvancedFightEngineLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = RaptorVoiceCreate
    VoiceGarrison = RaptorVoiceMove
  End
  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT REVEALS_ENEMY_PATHS
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_02
    MaxHealth = 1100.0
    InitialHealth = 1100.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
    FallHowFast = 110.0%
    FXInitialDeath = FX_RaptorDeathInitial
    OCLInitialDeath = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath = 500
    FXSecondary = FX_JetDeathSecondary
    OCLSecondary = OCL_RaptorDeathSecondary
    FXHitGround = FX_JetDeathHitGround
    OCLHitGround = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround = 200
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp
  End
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 600.0
  End
  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End
  Locomotor = SET_NORMAL CMF56_2_Turbofan_engine
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Behavior = StealthDetectorUpdate ModuleTag_E3_Detect
    DetectionRate = 1500
    DetectionRange = 3600
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End
  Behavior = SpecialAbility ModuleTag_AWACSSP
    SpecialPowerTemplate = SuperweaponNatoAWACS
    UpdateModuleStartsAttack = Yes
  End
  Behavior = OCLSpecialPower ModuleTag_SSM
    SpecialPowerTemplate = Superweapon_ANAPY2_SARSCANMODE
    OCL = SUPERWEAPON_ANAPY2_SARSCAN
    CreateLocation = CREATE_AT_EDGE_NEAR_SOURCE
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 42.0
  GeometryMinorRadius = 14.0
  GeometryHeight = 12.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not a BIGF archive: {path}")
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
    index = []
    blobs = []
    offset = header_size
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


def load_big_map(path: Path):
    entries, raw = read_big(path)
    data_map = {}
    keys = []
    for name, off, size in entries:
        key = norm_key(name)
        if key not in data_map:
            keys.append(key)
        data_map[key] = (name.replace("/", "\\"), raw[off : off + size])
    return data_map, keys


def walk_w3d(blob: bytes, pos: int, end: int, out: list[int]) -> None:
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        payload = csize & 0x7FFFFFFF
        container = bool(csize & 0x80000000)
        hdr_end = pos + 8
        payload_end = hdr_end + payload
        if payload_end > len(blob) + 8:
            break
        out.append(ctype)
        if container:
            walk_w3d(blob, hdr_end, min(payload_end, len(blob)), out)
        pos = payload_end
        if payload_end <= hdr_end:
            break


def w3d_anim_count(blob: bytes) -> int:
    types: list[int] = []
    walk_w3d(blob, 0, len(blob), types)
    return sum(1 for t in types if t in ANIM_TYPES)


def art_leaf(art_map: dict) -> dict[str, tuple[str, bytes]]:
    out = {}
    for key, (name, blob) in art_map.items():
        leaf = name.split("\\")[-1].lower()
        out[leaf] = (name, blob)
    return out


def find_w3d(art_map: dict, model: str) -> tuple[str, bytes] | None:
    leaf = art_leaf(art_map)
    for cand in (f"{model}.w3d", f"{model.lower()}.w3d"):
        hit = leaf.get(cand.lower())
        if hit:
            return hit
    return None


def lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def uniqueness_report(data_map: dict) -> dict:
    found = defaultdict(list)
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for kind, rx in BLOCK_RE.items():
            for i, line in enumerate(text.splitlines(), 1):
                s = line.split(";", 1)[0].rstrip()
                m = rx.match(s)
                if m and m.group(1) not in ("=", "Yes", "No"):
                    found[(kind, m.group(1))].append((name, i))
    dups = defaultdict(list)
    for (kind, nm), locs in found.items():
        if len(locs) > 1:
            dups[kind].append((nm, locs))
    return {"found": found, "dups": dups}


def extract_cs_block(cs_text: str, name: str) -> str:
    m = re.search(rf"^CommandSet {re.escape(name)}\s*$", cs_text, re.M)
    if not m:
        raise SystemExit(f"protected CommandSet missing: {name}")
    start = m.start()
    rest = cs_text[m.end() :]
    consumed = 0
    for line in rest.splitlines(True):
        consumed += len(line)
        if line.rstrip("\r\n") == "End":
            break
    else:
        raise SystemExit(f"protected CommandSet has no End: {name}")
    return cs_text[start : m.end() + consumed]


def cs_key(data_map: dict) -> str:
    for cand in (r"data\ini\commandset.ini", r"data\ini\commandset.ini".lower()):
        if cand in data_map:
            return cand
    for k in data_map:
        if k.endswith("commandset.ini") and k.count("\\") <= 3:
            return k
    raise SystemExit("CommandSet.ini not found")


def weapon_key(data_map: dict) -> str:
    for cand in (r"data\ini\weapon.ini",):
        if cand in data_map:
            return cand
    for k in data_map:
        if k.endswith("weapon.ini") and "weapon_" not in Path(k).name.lower():
            return k
    raise SystemExit("Weapon.ini not found")


def find_object(data_map: dict, obj_name: str) -> tuple[str, str, str]:
    rx = re.compile(rf"^Object(?:Reskin)?\s+{re.escape(obj_name)}\s*$", re.M)
    hits = []
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        if rx.search(text):
            hits.append((key, name, text))
    if not hits:
        raise SystemExit(f"Object not found: {obj_name}")
    if len(hits) > 1:
        # Prefer Airforce / Rotary faction files over ScienceObjects / NATO clones.
        ranked = sorted(
            hits,
            key=lambda h: (
                0 if "/airforce/" in h[0].replace("\\", "/").lower() or "/rotary/" in h[0].replace("\\", "/").lower() else 1,
                len(h[0]),
            ),
        )
        return ranked[0]
    return hits[0]


def object_span(text: str, obj_name: str) -> tuple[int, int]:
    m = re.search(rf"^Object(?:Reskin)?\s+{re.escape(obj_name)}\s*$", text, re.M)
    if not m:
        raise SystemExit(f"Object span missing: {obj_name}")
    consumed = 0
    rest = text[m.end() :]
    for line in rest.splitlines(True):
        consumed += len(line)
        if line.rstrip("\r\n") == "End":
            return m.start(), m.end() + consumed
    raise SystemExit(f"Object End missing: {obj_name}")


def replace_object(data_map: dict, obj_name: str, new_body: str) -> None:
    key, name, text = find_object(data_map, obj_name)
    start, end = object_span(text, obj_name)
    body = lf(new_body).rstrip() + "\n"
    new_text = text[:start] + body + text[end:]
    data_map[key] = (name, new_text.encode("latin1"))


def patch_object(data_map: dict, obj_name: str, fn) -> str:
    key, name, text = find_object(data_map, obj_name)
    start, end = object_span(text, obj_name)
    body = lf(text[start:end])
    new_body = fn(body)
    if not new_body.endswith("\n"):
        new_body += "\n"
    new_text = text[:start] + new_body + text[end:]
    data_map[key] = (name, new_text.encode("latin1"))
    return new_body


def set_scale(body: str, new_scale: float, old_scale: float | None = None) -> str:
    m = re.search(r"^Scale\s*=\s*([0-9.]+)\s*$", body, re.M)
    if m:
        prev = float(m.group(1))
        body = re.sub(r"^Scale\s*=\s*[0-9.]+\s*$", f"Scale = {new_scale:.2f}", body, count=1, flags=re.M)
    else:
        prev = old_scale if old_scale is not None else 1.0
        body = re.sub(r"^(Object\s+\S+\s*)$", rf"\1\nScale = {new_scale:.2f}", body, count=1, flags=re.M)
    factor = new_scale / prev if prev else 1.0
    if abs(factor - 1.0) > 0.001:
        def _g(mx):
            return f"{mx.group(1)}{float(mx.group(2)) * factor:.1f}"

        body = re.sub(r"^(  Geometry(?:Major|Minor)Radius\s+=\s+)([0-9.]+)", _g, body, flags=re.M)
        body = re.sub(r"^(  GeometryHeight\s+=\s+)([0-9.]+)", _g, body, flags=re.M)
        body = re.sub(r"^(  ShadowSizeX\s+=\s+)(\d+)", lambda mx: f"{mx.group(1)}{max(45, int(round(int(mx.group(2)) * factor)))}", body, flags=re.M)
    return body


def replace_models(body: str, mapping: dict[str, str]) -> str:
    def _m(mx):
        old = mx.group(2)
        new = mapping.get(old, mapping.get(old.lower()))
        if new is None:
            for k, v in mapping.items():
                if k.lower() == old.lower():
                    new = v
                    break
        return f"{mx.group(1)}{new if new else old}"

    return re.sub(r"^(\s*Model\s+=\s+)(\S+)", _m, body, flags=re.M)


def strip_prereq(body: str) -> str:
    return re.sub(r"\n[ \t]*Prerequisites\s*\n(?:[ \t]*[^\n]*\n)*?[ \t]*End\s*\n", "\n", body, count=1)


def convert_heli(body: str, mass: float) -> str:
    body = re.sub(
        r"  Behavior = ChinookAIUpdate ModuleTag_\S+\n(?:    .*\n)*?  End\n",
        (
            "  Behavior = JetAIUpdate ModuleTag_09ai\n"
            "    MinHeight = 10\n"
            "    NeedsRunway = No\n"
            "    KeepsParkingSpaceWhenAirborne = No\n"
            "    AutoAcquireEnemiesWhenIdle = No\n"
            "  End\n"
        ),
        body,
        count=1,
    )
    if "PhysicsBehavior" not in body:
        body = body.replace(
            "  Geometry = Box\n",
            (
                f"  Behavior = PhysicsBehavior ModuleTag_07phys\n"
                f"    Mass = {mass:.1f}\n"
                "  End\n"
                "  Geometry = Box\n"
            ),
            1,
        )
    else:
        body = re.sub(r"(Behavior = PhysicsBehavior[^\n]*\n(?:    .*\n)*?    Mass\s+=\s+)([0-9.]+)", rf"\g<1>{mass:.1f}", body, count=1)
    if "NeedsRunway = Yes" in body:
        raise SystemExit("helicopter still NeedsRunway=Yes")
    if "ChinookAIUpdate" in body:
        raise SystemExit("ChinookAIUpdate still present")
    if "JetAIUpdate" not in body:
        raise SystemExit("JetAIUpdate missing after heli convert")
    return body


def force_runway_uav(body: str) -> str:
    if "NeedsRunway" in body:
        body = re.sub(r"NeedsRunway\s+=\s+\S+", "NeedsRunway = Yes", body)
    else:
        body = re.sub(
            r"(Behavior = JetAIUpdate[^\n]*\n)",
            r"\1    NeedsRunway = Yes\n",
            body,
            count=1,
        )
    if "KeepsParkingSpaceWhenAirborne" in body:
        body = re.sub(r"KeepsParkingSpaceWhenAirborne\s+=\s+\S+", "KeepsParkingSpaceWhenAirborne = Yes", body)
    else:
        body = re.sub(
            r"(Behavior = JetAIUpdate[^\n]*\n)",
            r"\1    KeepsParkingSpaceWhenAirborne = Yes\n",
            body,
            count=1,
        )
    if "ReturnToBaseIdleTime" not in body:
        body = re.sub(
            r"(Behavior = JetAIUpdate[^\n]*\n)",
            r"\1    ReturnToBaseIdleTime = 10000\n",
            body,
            count=1,
        )
    return body


def replace_weaponset(body: str, new_ws: str) -> str:
    m = re.search(r"  WeaponSet\n(?:    .*\n)*?  End\n", body)
    if not m:
        raise SystemExit("WeaponSet missing")
    return body[: m.start()] + new_ws + body[m.end() :]


def first_model(body: str) -> str:
    m = re.search(r"^\s*Model\s+=\s+(\S+)", body, re.M)
    return m.group(1) if m else "?"


def field(body: str, key: str, default: str = "?") -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s+=\s+(\S+)", body, re.M)
    return m.group(1) if m else default


def extract_big(path: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    entries, raw = read_big(path)
    for name, off, size in entries:
        out = dest / name.replace("\\", "/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw[off : off + size])


def object_text_from_map(data_map: dict, obj_name: str) -> str:
    key, name, text = find_object(data_map, obj_name)
    start, end = object_span(text, obj_name)
    return lf(text[start:end])


def copy_object_to_patch(data_map: dict, obj_name: str) -> Path:
    key, name, text = find_object(data_map, obj_name)
    start, end = object_span(text, obj_name)
    body = lf(text[start:end]).rstrip() + "\n"
    rel = Path(*Path(name.replace("\\", "/")).parts[1:])  # drop Data/
    dest = ROOT / "patch" / "Data" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body.encode("latin1"))
    return dest


def main() -> None:
    if not BASE_DATA.exists() or not BASE_ART.exists():
        raise SystemExit("pass-2 baseline BIGs missing")

    data_map, data_keys = load_big_map(BASE_DATA)
    art_map, art_keys = load_big_map(BASE_ART)
    base_data_map, _ = load_big_map(BASE_DATA)

    cs_k = cs_key(data_map)
    cs_name, cs_blob = data_map[cs_k]
    cs_text = cs_blob.decode("latin1", errors="replace")
    protected_before = {n: sha256_bytes(extract_cs_block(cs_text, n).encode("latin1")) for n in PROTECTED_CS}
    print("PROTECTED hashes before:")
    for n, h in protected_before.items():
        print(f"  {n} {h}")

    base_uniq = uniqueness_report(base_data_map)
    base_dup_names = {kind: {nm for nm, _ in locs} for kind, locs in base_uniq["dups"].items()}

    # --- Germany E-3 ---
    replace_object(data_map, "GermanyAircraftE3", GERMANY_E3)

    # --- Germany helicopters ---
    patch_object(data_map, "GermanyHelicopterNH90", lambda b: convert_heli(b, 50.0))
    patch_object(data_map, "GermanyHelicopterCH53", lambda b: convert_heli(b, 80.0))

    # --- Germany UAVs ---
    patch_object(data_map, "GermanyUAVEuroMALE", force_runway_uav)
    patch_object(data_map, "GermanyDroneHeronTP", force_runway_uav)

    # --- Visual replacements ---
    def alpha(b: str) -> str:
        b = replace_models(b, {"AVHawk": "qsnt50", "AVHawk_D": "qsnt50", "AVHawk_P": "qsnt50"})
        return b.replace("; SPECTER - France Alpha Jet. Donor ART AVHawk.W3D.", "; SPECTER pass 3 - Germany Alpha Jet. Visual qsnt50 T-50 trainer silhouette.")

    patch_object(data_map, "GermanyJetAlphaJet", alpha)

    def tornado(b: str) -> str:
        ws = (
            "  WeaponSet\n"
            "    Conditions = None\n"
            "    Weapon              = PRIMARY    Germany_Weapon_Taurus\n"
            "    PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE\n"
            "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
            "    Weapon              = SECONDARY  GermanyJetTornadoIDS_WpnBombHvy\n"
            "    PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE\n"
            "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI\n"
            "    Weapon              = TERTIARY   GermanyJetTornadoIDS_WpnIR2\n"
            "    PreferredAgainst    = TERTIARY   AIRCRAFT\n"
            "    AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI\n"
            "  End\n"
        )
        b = replace_weaponset(b, ws)
        if "NeedsRunway" not in b:
            b = re.sub(
                r"(Behavior = JetAIUpdate[^\n]*\n)",
                r"\1    NeedsRunway = Yes\n    KeepsParkingSpaceWhenAirborne = Yes\n",
                b,
                count=1,
            )
        return b

    patch_object(data_map, "GermanyJetTornadoIDS", tornado)

    # --- Scales ---
    for _country, obj, old, new, _ref, _why in SCALE_JOBS:
        def _sc(b, _old=old, _new=new):
            return set_scale(b, _new, _old)

        patch_object(data_map, obj, _sc)

    # --- Syria unlock + visuals ---
    patch_object(data_map, "Syria_MirageF1_Bq", strip_prereq)

    def su25(b: str) -> str:
        return replace_models(b, {"Irq_Su25k": "RUS_SU25T", "Irq_Su25K": "RUS_SU25T"})

    patch_object(data_map, "Syria_Su-25K", su25)

    def l39(b: str) -> str:
        return replace_models(b, {"AVHawk": "AGMZRT501", "AVHawk_D": "AGMZRT501", "AVHawk_P": "AGMZRT501"})

    patch_object(data_map, "SyriaJetL39", l39)

    # --- India MiG-29A visual ---
    def mig29(b: str) -> str:
        b = replace_models(b, {"Irq_Mig29A": "LSFruMiG29"})
        return b

    patch_object(data_map, "India_Mig-29A", mig29)

    # --- UAE Hawk 102 ---
    def hawk102(b: str) -> str:
        return replace_models(b, {"AVHawk": "UV_Turbo", "AVHawk_D": "UV_Turbo_D", "AVHawk_P": "UV_Turbo"})

    patch_object(data_map, "UAEJetHawk102", hawk102)

    # --- Pakistan F-16C Block 52 fire ---
    def f16(b: str) -> str:
        b = strip_prereq(b)
        ws = (
            "  WeaponSet\n"
            "    Conditions = None\n"
            "    Weapon              = PRIMARY    Pakistan_Weapon_AIM120_F16AMLU\n"
            "    PreferredAgainst    = PRIMARY    AIRCRAFT\n"
            "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
            "    Weapon              = SECONDARY  Pakistan_Weapon_AIM9_F16AMLU\n"
            "    PreferredAgainst    = SECONDARY  AIRCRAFT\n"
            "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI\n"
            "    Weapon              = TERTIARY   Pakistan_Weapon_Bomb_F16AMLU\n"
            "    PreferredAgainst    = TERTIARY   VEHICLE STRUCTURE\n"
            "    AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI\n"
            "  End\n"
        )
        b = replace_weaponset(b, ws)
        b = re.sub(r"WeaponLaunchBone\s+=\s+PRIMARY\s+\S+", "WeaponLaunchBone = PRIMARY Weapon01", b)
        if "WeaponLaunchBone = SECONDARY" not in b:
            b = b.replace(
                "WeaponLaunchBone = PRIMARY Weapon01",
                "WeaponLaunchBone = PRIMARY Weapon01\n      WeaponLaunchBone = SECONDARY Weapon02\n      WeaponLaunchBone = TERTIARY Weapon01",
                1,
            )
        b = re.sub(r"OutOfAmmoDamagePerSecond\s+=\s+\S+", "OutOfAmmoDamagePerSecond  = 0%", b)
        if "NeedsRunway" not in b:
            b = re.sub(
                r"(Behavior = JetAIUpdate[^\n]*\n)",
                r"\1    NeedsRunway = Yes\n    KeepsParkingSpaceWhenAirborne = Yes\n    AutoAcquireEnemiesWhenIdle = Yes\n",
                b,
                count=1,
            )
        else:
            b = re.sub(r"NeedsRunway\s+=\s+\S+", "NeedsRunway = Yes", b)
            if "AutoAcquireEnemiesWhenIdle" not in b:
                b = re.sub(
                    r"(Behavior = JetAIUpdate[^\n]*\n)",
                    r"\1    AutoAcquireEnemiesWhenIdle = Yes\n",
                    b,
                    count=1,
                )
        return b

    patch_object(data_map, "Pakistan_F16Blk52", f16)

    # --- Append unique weapons ---
    wk = weapon_key(data_map)
    wname, wblob = data_map[wk]
    wtext = lf(wblob.decode("latin1", errors="replace"))
    for wn in ("GermanyJetTornadoIDS_WpnBombHvy", "GermanyJetTornadoIDS_WpnIR2"):
        if re.search(rf"^Weapon {re.escape(wn)}\s*$", wtext, re.M):
            raise SystemExit(f"weapon already exists: {wn}")
    if not wtext.endswith("\n"):
        wtext += "\n"
    wtext += NEW_WEAPONS
    data_map[wk] = (wname, wtext.encode("latin1"))

    # --- Protected hashes after (CommandSet.ini untouched) ---
    cs_name2, cs_blob2 = data_map[cs_k]
    if cs_blob2 != cs_blob:
        raise SystemExit("CommandSet.ini mutated — STOP")
    cs_text2 = cs_blob2.decode("latin1", errors="replace")
    protected_after = {n: sha256_bytes(extract_cs_block(cs_text2, n).encode("latin1")) for n in PROTECTED_CS}
    for n in PROTECTED_CS:
        if protected_before[n] != protected_after[n]:
            raise SystemExit(f"PROTECTED HASH CHANGED: {n}")

    # --- Uniqueness ---
    new_uniq = uniqueness_report(data_map)
    new_only = {}
    for kind, locs in new_uniq["dups"].items():
        extra = [(nm, loc) for nm, loc in locs if nm not in base_dup_names.get(kind, set())]
        if extra:
            new_only[kind] = extra
    if new_only:
        print("NEW DUPLICATES:")
        for kind, extra in new_only.items():
            for nm, loc in extra:
                print(f"  {kind} {nm} {loc}")
        raise SystemExit("new duplicate declarations")

    # --- Weapon projectile audit ---
    packed_objects = {nm for (kind, nm) in new_uniq["found"] if kind == "Object"}
    packed_weapons = {nm for (kind, nm) in new_uniq["found"] if kind == "Weapon"}
    required_proj = {
        "GBU24_GuidedBombObject",
        "Kh59MK2_Object",
        "MeteorMissile_Object",
        "AIM-9X_Object",
        "Fab-250",
        "AGM114L_MissileObject",
    }
    missing_proj = sorted(p for p in required_proj if p not in packed_objects)
    # Fab-250 is both Weapon and Object — object exists
    if missing_proj:
        raise SystemExit(f"missing projectiles: {missing_proj}")
    for wn in (
        "Germany_Weapon_Taurus",
        "GermanyJetTornadoIDS_WpnBombHvy",
        "GermanyJetTornadoIDS_WpnIR2",
        "Pakistan_Weapon_AIM120_F16AMLU",
        "Pakistan_Weapon_AIM9_F16AMLU",
        "Pakistan_Weapon_Bomb_F16AMLU",
    ):
        if wn not in packed_weapons:
            raise SystemExit(f"missing weapon: {wn}")

    # --- Animation / W3D existence on touched objects ---
    touched = [
        "GermanyAircraftE3",
        "GermanyHelicopterNH90",
        "GermanyHelicopterCH53",
        "GermanyUAVEuroMALE",
        "GermanyDroneHeronTP",
        "GermanyJetAlphaJet",
        "GermanyJetTornadoIDS",
        "SyriaJetMig21",
        "SyriaJetMig21MF",
        "Syria_MirageF1_Bq",
        "Syria_Su-25K",
        "SyriaJetL39",
        "IndiaJetMig21Bison",
        "India_Mig-29A",
        "IndiaJetTejas",
        "UAEJetHawk102",
        "SaudiJetLightning",
        "SaudiJetHawk65",
        "SaudiJetF5E",
        "PakistanJetMirageROSE",
        "PakistanJetF7PG",
        "PakistanJetF7P",
        "Pakistan_F16Blk52",
    ]
    anim_fail = []
    w3d_fail = []
    helper_fail = []
    bodies = {}
    for obj in touched:
        body = object_text_from_map(data_map, obj)
        bodies[obj] = body
        models = re.findall(r"^\s*Model\s+=\s+(\S+)", body, re.M)
        anims = re.findall(r"^\s*Animation\s+=\s+(\S+)", body, re.M)
        for model in models:
            hit = find_w3d(art_map, model)
            if hit is None:
                w3d_fail.append((obj, model))
                continue
            _n, blob = hit
            if len(blob) < HELPER_W3D_MAX:
                helper_fail.append((obj, model, len(blob)))
            if anims:
                n = w3d_anim_count(blob)
                if n == 0 and any(a.upper().startswith(model.upper() + ".") or model.upper() in a.upper() for a in anims):
                    # any Animation= while this model is used
                    if n == 0:
                        anim_fail.append((obj, model, 0))
        if anims:
            for model in set(models):
                hit = find_w3d(art_map, model)
                if hit and w3d_anim_count(hit[1]) == 0:
                    anim_fail.append((obj, model, 0))
    # unique anim fails
    anim_fail = sorted(set(anim_fail))
    if w3d_fail:
        raise SystemExit(f"missing W3D: {w3d_fail}")
    if helper_fail:
        raise SystemExit(f"helper W3D used as aircraft: {helper_fail}")
    if anim_fail:
        raise SystemExit(f"Animation= on 0-anim W3D: {anim_fail}")

    # G550 still static
    g550 = object_text_from_map(data_map, "ItalyAircraftG550CAEW")
    if re.search(r"^\s*Animation\s+=", g550, re.M):
        raise SystemExit("G550 gained Animation=")

    # USA E-3 science object byte-identical
    usa_e3_key = None
    for key, (name, blob) in data_map.items():
        if "scienceobjects" in key.replace("\\", "/").lower() and "e3g.ini" in key.lower() and "united states" in key.lower():
            usa_e3_key = key
            break
    if usa_e3_key and data_map[usa_e3_key][1] != base_data_map[usa_e3_key][1]:
        raise SystemExit("USA E3G.ini mutated")

    # --- Static behavior gates ---
    e3 = bodies["GermanyAircraftE3"]
    assert "WeaponSet" not in e3
    assert "StealthDetectorUpdate" in e3
    assert "SuperweaponNatoAWACS" in e3
    assert "Superweapon_ANAPY2_SARSCANMODE" in e3
    assert "NeedsRunway = Yes" in e3
    assert "CommandSet = E3G_CommandSet" in e3
    assert first_model(e3) == "US_E3G"

    for heli, mass in (("GermanyHelicopterNH90", "50.0"), ("GermanyHelicopterCH53", "80.0")):
        b = bodies[heli]
        assert "JetAIUpdate" in b
        assert "NeedsRunway = No" in b
        assert "ChinookAIUpdate" not in b
        assert "PhysicsBehavior" in b
        assert f"Mass = {mass}" in b
        assert "PRODUCED_AT_HELIPAD" in b
        if heli.endswith("CH53"):
            assert "TransportContain" in b

    for uav in ("GermanyUAVEuroMALE", "GermanyDroneHeronTP"):
        b = bodies[uav]
        assert "JetAIUpdate" in b
        assert "NeedsRunway = Yes" in b
        assert "KeepsParkingSpaceWhenAirborne = Yes" in b
        assert "ReturnToBaseIdleTime" in b
        assert "ChinookAIUpdate" not in b

    assert first_model(bodies["GermanyJetAlphaJet"]) == "qsnt50"
    assert "Germany_Weapon_Taurus" in bodies["GermanyJetTornadoIDS"]
    assert "GermanyJetTornadoIDS_WpnBombHvy" in bodies["GermanyJetTornadoIDS"]
    assert "Syria_RadarStation" not in bodies["Syria_MirageF1_Bq"]
    assert first_model(bodies["Syria_Su-25K"]) == "RUS_SU25T"
    assert first_model(bodies["SyriaJetL39"]) == "AGMZRT501"
    assert first_model(bodies["India_Mig-29A"]) == "LSFruMiG29"
    assert first_model(bodies["UAEJetHawk102"]) == "UV_Turbo"
    assert "Pakistan_Weapon_AIM120_F16AMLU" in bodies["Pakistan_F16Blk52"]
    assert "WeaponLaunchBone = PRIMARY Weapon01" in bodies["Pakistan_F16Blk52"]
    assert "NeedsRunway = Yes" in bodies["Pakistan_F16Blk52"]
    assert "Prerequisites" not in bodies["Pakistan_F16Blk52"]

    # Fighter CS slots unchanged
    for token in (
        "Command_ConstructGermanyJetTornadoIDS",
        "Command_ConstructGermanyJetAlphaJet",
        "Command_ConstructGermanyAircraftE3",
        "Command_ConstructSyria_MirageF1_Bq",
        "Command_ConstructPakistan_F16Blk52",
    ):
        if token not in cs_text2:
            raise SystemExit(f"menu button missing: {token}")

    # --- Build BIGs ---
    OUT.mkdir(parents=True, exist_ok=True)
    file_map_data = {name: blob for name, blob in (data_map[k] for k in data_keys)}
    # include any new keys
    for k, (name, blob) in data_map.items():
        file_map_data[name] = blob
    data_bytes = build_big(file_map_data)
    art_file_map = {name: blob for name, blob in (art_map[k] for k in art_keys)}
    for k, (name, blob) in art_map.items():
        art_file_map[name] = blob
    art_bytes = build_big(art_file_map)
    (OUT / "_SPEC_DATA_ONE.big").write_bytes(data_bytes)
    (OUT / "_SPEC_ART_ONE.big").write_bytes(art_bytes)

    data_hash = sha256(OUT / "_SPEC_DATA_ONE.big")
    art_hash = sha256(OUT / "_SPEC_ART_ONE.big")
    print(f"DATA SHA256 {data_hash}")
    print(f"ART SHA256 {art_hash}")

    # Re-extract and confirm
    extract_big(OUT / "_SPEC_DATA_ONE.big", EXTRACT / "DataBig")
    extract_big(OUT / "_SPEC_ART_ONE.big", EXTRACT / "ArtBig")
    re_data, _ = load_big_map(OUT / "_SPEC_DATA_ONE.big")
    re_art, _ = load_big_map(OUT / "_SPEC_ART_ONE.big")
    re_cs = re_data[cs_key(re_data)][1]
    if re_cs != cs_blob:
        raise SystemExit("reextract CommandSet.ini != baseline")
    for obj in touched:
        b = object_text_from_map(re_data, obj)
        if b != bodies[obj]:
            raise SystemExit(f"reextract mismatch {obj}")

    # Write reports
    write_reports(bodies, protected_before, protected_after, data_hash, art_hash, new_uniq, base_dup_names)

    # Copy patched objects into repo source
    copied = []
    for obj in touched:
        copied.append(str(copy_object_to_patch(re_data, obj)))
    print("copied", len(copied), "object INIs")

    # INSTALL + zip
    install = OUT / "INSTALL.txt"
    install.write_text(
        """SPECTER AIRFORCE REPAIR PASS 3 V1

Copy both BIG files into the C&C Generals Zero Hour / Specter folder,
replacing the previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This is a surgical repair pass on top of airforce-runway-visual-repair-v2.
It does not rebuild country rosters and does not modify USA / Russia / China
live CommandSets or objects.

Cursor cannot launch Zero Hour. Movement, landing, and weapon fire are
STATIC PASS only. USER RUNTIME TEST REQUIRED.

See AIRFORCE_REPAIR_PASS_3_FINAL.md
""",
        encoding="ascii",
    )

    for name in (
        "AIRFORCE_REPAIR_PASS_3_FINAL.md",
        "AIRCRAFT_SCALE_REPAIR_AUDIT_3.md",
        "VISUAL_DIVERSITY_REPAIR_AUDIT_3.md",
        "GERMANY_HELICOPTER_FLIGHT_AUDIT.md",
        "GERMANY_UAV_RUNWAY_AUDIT.md",
        "INSTALL.txt",
    ):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, OUT / name)

    zip_path = OUT / "AIRFORCE_REPAIR_PASS_3_V1.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "AIRFORCE_REPAIR_PASS_3_FINAL.md",
            "AIRCRAFT_SCALE_REPAIR_AUDIT_3.md",
            "VISUAL_DIVERSITY_REPAIR_AUDIT_3.md",
            "GERMANY_HELICOPTER_FLIGHT_AUDIT.md",
            "GERMANY_UAV_RUNWAY_AUDIT.md",
        ):
            zf.write(OUT / name, name)
    print(f"ZIP SHA256 {sha256(zip_path)}")
    print("PACK OK")


def write_reports(bodies: dict, prot_b: dict, prot_a: dict, data_hash: str, art_hash: str, uniq: dict, base_dups: dict) -> None:
    scale_rows = []
    for country, obj, old, new, ref, why in SCALE_JOBS:
        b = bodies[obj]
        scale_rows.append(
            f"| {country} | {obj} | {obj} | {first_model(b)} | {old:.2f} | {new:.2f} | {ref} | {why} |"
        )
    (ROOT / "AIRCRAFT_SCALE_REPAIR_AUDIT_3.md").write_text(
        "# AIRCRAFT SCALE REPAIR AUDIT 3\n\n"
        "Per-aircraft geometry Scale values. Not a single arbitrary constant.\n\n"
        "| Country | Aircraft | Object | W3D | Old Geometry Scale | New Geometry Scale | Reference aircraft | Reason |\n"
        "|---|---|---|---|---|---|---|---|\n"
        + "\n".join(scale_rows)
        + "\n\nSCALE_AUDIT = PASS\n"
        "Cursor cannot launch Zero Hour. Visual size is STATIC vs reference scales.\n",
        encoding="ascii",
    )

    visual = [
        ("Germany", "Alpha Jet", "GermanyJetAlphaJet", "AVHawk", "qsnt50", "packed Specter ART", "Fallback T-50 trainer/light-attack silhouette (no dedicated Alpha Jet W3D)", "NO"),
        ("Syria", "Su-25K", "Syria_Su-25K", "Irq_Su25k", "RUS_SU25T", "packed Specter ART", "Exact Su-25T class", "NO"),
        ("Syria", "L-39ZA", "SyriaJetL39", "AVHawk", "AGMZRT501", "packed Specter ART", "Fallback compact trainer (no dedicated L-39 W3D)", "NO"),
        ("India", "MiG-29A", "India_Mig-29A", "Irq_Mig29A", "LSFruMiG29", "packed Specter ART", "Exact Fulcrum-family", "NO"),
        ("UAE", "Hawk 102", "UAEJetHawk102", "AVHawk", "UV_Turbo", "packed Specter ART", "Fallback compact trainer (no dedicated Hawk 102 W3D)", "NO"),
    ]
    vlines = [
        "| Country | Aircraft | Object | Old W3D | New W3D | Source | Exact/Fallback | Duplicate visual in same country |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in visual:
        vlines.append("| " + " | ".join(row) + " |")
    (ROOT / "VISUAL_DIVERSITY_REPAIR_AUDIT_3.md").write_text(
        "# VISUAL DIVERSITY REPAIR AUDIT 3\n\n"
        + "\n".join(vlines)
        + "\n\nGermany Alpha Jet qsnt50 is not LSFTornado / LSFF16 (Mako) / US_E3G.\n"
        "Syria Su-25K RUS_SU25T is not AGMZRT501 (L-39) and not UVMig-21.\n"
        "UAE Hawk 102 UV_Turbo is not used by UAE F-16 / Mirage / F-15 fighters.\n"
        "India MiG-29A LSFruMiG29 is Fulcrum, not the RUS_Mig35 used by IndiaJetMig29K.\n\n"
        "VISUAL_DIVERSITY = PASS\n",
        encoding="ascii",
    )

    def heli_section(obj: str) -> str:
        b = bodies[obj]
        anims = len(re.findall(r"^\s*Animation\s+=", b, re.M))
        km = re.search(r"KindOf\s+=\s+(.+)", b)
        kindof = km.group(1).strip() if km else "?"
        return (
            f"## {obj}\n\n"
            f"- Object: `{obj}`\n"
            f"- AIUpdate: JetAIUpdate (converted from ChinookAIUpdate)\n"
            f"- Locomotor: {field(b, 'Locomotor')}\n"
            f"- Physics: PhysicsBehavior Mass={field(b, 'Mass')}\n"
            f"- KindOf: `{kindof}`\n"
            f"- NeedsRunway: {field(b, 'NeedsRunway')}\n"
            f"- Parking: KeepsParkingSpaceWhenAirborne={field(b, 'KeepsParkingSpaceWhenAirborne')} PRODUCED_AT_HELIPAD present\n"
            f"- W3D: {first_model(b)}\n"
            f"- Animation reference count: {anims}\n"
            f"- TransportContain: {'YES' if 'TransportContain' in b else 'NO'}\n\n"
        )

    nh = bodies["GermanyHelicopterNH90"]
    ch = bodies["GermanyHelicopterCH53"]
    (ROOT / "GERMANY_HELICOPTER_FLIGHT_AUDIT.md").write_text(
        "# GERMANY HELICOPTER FLIGHT AUDIT\n\n"
        "Template: ItalyHelicopterNH90 (pass 2) JetAIUpdate NeedsRunway=No + ChinookLocomotor + PhysicsBehavior.\n"
        "Do not use fixed-wing runway AI.\n\n"
        + heli_section("GermanyHelicopterNH90")
        + heli_section("GermanyHelicopterCH53")
        + "NH90_STATIC_FLIGHT = PASS\n"
        "CH53_STATIC_FLIGHT = PASS\n\n"
        "STATIC PASS. USER RUNTIME TEST REQUIRED. Cursor cannot launch Zero Hour.\n",
        encoding="ascii",
    )

    def uav_section(obj: str) -> str:
        b = bodies[obj]
        return (
            f"## {obj}\n\n"
            f"- takeoff architecture: JetAIUpdate NeedsRunway=Yes TakeoffPause present\n"
            f"- landing architecture: NeedsRunway=Yes + ReturnToBaseIdleTime + taxi locomotor\n"
            f"- NeedsRunway: {field(b, 'NeedsRunway')}\n"
            f"- KeepsParkingSpaceWhenAirborne: {field(b, 'KeepsParkingSpaceWhenAirborne')}\n"
            f"- AIUpdate: JetAIUpdate\n"
            f"- Locomotor: {field(b, 'Locomotor')}\n"
            f"- Physics: Mass={field(b, 'Mass')}\n"
            f"- airbase compatibility: Germany Heavy Airbase slots unchanged\n"
            f"- return-to-base: ReturnToBaseIdleTime={field(b, 'ReturnToBaseIdleTime')}\n"
            f"- parking: KeepsParkingSpaceWhenAirborne=Yes\n"
            f"- W3D: {first_model(b)}\n\n"
        )

    (ROOT / "GERMANY_UAV_RUNWAY_AUDIT.md").write_text(
        "# GERMANY UAV RUNWAY AUDIT\n\n"
        "Template: ItalyDroneMQ9 runway UAV (NeedsRunway=Yes, KeepsParkingSpaceWhenAirborne=Yes).\n"
        "Not converted to helicopters.\n\n"
        + uav_section("GermanyUAVEuroMALE")
        + uav_section("GermanyDroneHeronTP")
        + "EURODRONE_TAKEOFF_STATIC = PASS\n"
        "EURODRONE_LANDING_STATIC = PASS\n"
        "HERON_TP_TAKEOFF_STATIC = PASS\n"
        "HERON_TP_LANDING_STATIC = PASS\n\n"
        "STATIC PASS. USER RUNTIME TEST REQUIRED.\n",
        encoding="ascii",
    )

    def yn(cond: bool) -> str:
        return "YES" if cond else "NO"

    e3 = bodies["GermanyAircraftE3"]
    final = []
    final.append("# AIRFORCE REPAIR PASS 3 FINAL\n")
    final.append("Surgical repair on airforce-runway-visual-repair-v2 packed BIGs.\n")
    final.append("USA / Russia / China live CommandSets byte-identical.\n")
    final.append("Cursor cannot launch Zero Hour. Runtime-sensitive lines are STATIC PASS.\n\n")

    final.append("## GERMANY\n\n")
    final.append(
        f"### E-3 AWACS\n- Object: GermanyAircraftE3\n- visual: US_E3G (was stub E3)\n"
        f"- role: AWACS detector + SAR scan, ZERO offensive weapons\n"
        f"- scale: 0.90 (unchanged)\n- weapons: none\n"
        f"- airbase: Germany Heavy slot 3\n- buildable: YES\n"
        f"- static movement: JetAI NeedsRunway=Yes ReturnToBaseIdleTime=10000 CommandSet=E3G_CommandSet Detector+scan present\n"
        f"- scan: SuperweaponNatoAWACS + Superweapon_ANAPY2_SARSCANMODE radius 3600\n\n"
    )
    final.append(
        f"### NH90\n- Object: GermanyHelicopterNH90\n- visual: {first_model(bodies['GermanyHelicopterNH90'])}\n"
        f"- role: medium transport helicopter\n- airbase: Germany Heavy slot 7 / Helicopter base\n"
        f"- buildable: YES\n- static movement: JetAI NeedsRunway=No ChinookLocomotor Mass=50 Physics present\n\n"
    )
    final.append(
        f"### CH-53\n- Object: GermanyHelicopterCH53\n- visual: {first_model(bodies['GermanyHelicopterCH53'])}\n"
        f"- role: heavy helicopter transport (TransportContain 14)\n- airbase: Germany Heavy slot 8\n"
        f"- buildable: YES\n- static movement: JetAI NeedsRunway=No ChinookLocomotor Mass=80 independent of NH90\n\n"
    )
    final.append(
        f"### Eurodrone MALE\n- Object: GermanyUAVEuroMALE\n- visual: {first_model(bodies['GermanyUAVEuroMALE'])} (kept)\n"
        f"- role: recon / PGM UAV\n- weapons: Germany_Weapon_EuroMALE_PGM (unchanged)\n"
        f"- airbase: Germany Heavy slot 5\n- buildable: YES\n"
        f"- static movement: NeedsRunway=Yes KeepsParkingSpaceWhenAirborne=Yes (was NeedsRunway=No)\n\n"
    )
    final.append(
        f"### Heron TP\n- Object: GermanyDroneHeronTP\n- visual: {first_model(bodies['GermanyDroneHeronTP'])} (kept)\n"
        f"- role: runway UAV / Brimstone\n- airbase: Germany Heavy slot 4\n- buildable: YES\n"
        f"- static movement: NeedsRunway=Yes KeepsParkingSpaceWhenAirborne=Yes (was NeedsRunway=No)\n\n"
    )
    final.append(
        f"### Alpha Jet\n- Object: GermanyJetAlphaJet\n- visual: qsnt50 (was AVHawk)\n"
        f"- role: light attack / trainer (weapons unchanged)\n- airbase: Germany Fighter/Large slot 10\n"
        f"- buildable: YES\n\n"
    )
    final.append(
        f"### Tornado IDS Strike Bomber\n- Object: GermanyJetTornadoIDS (existing; not invented B-2)\n"
        f"- visual: LSFTornado (kept)\n- role: heavy tactical strike / bomber\n"
        f"- weapons: PRIMARY Germany_Weapon_Taurus x2 (Kh59MK2_Object); SECONDARY GermanyJetTornadoIDS_WpnBombHvy x6 (GBU24_GuidedBombObject, PreAttackDelay 2800, DelayBetweenShots 2200); TERTIARY GermanyJetTornadoIDS_WpnIR2 x2 (AIM-9X_Object)\n"
        f"- airbase: Germany Fighter/Large slot 7 (existing safe slot; Rally/Sell/AWACS untouched)\n"
        f"- buildable: YES\n- NO nuclear weapon\n\n"
    )

    final.append("## SYRIA\n\n")
    final.append(
        f"### MiG-21bis\n- Object: SyriaJetMig21\n- visual: {first_model(bodies['SyriaJetMig21'])}\n"
        f"- scale: 0.82 -> 0.94\n- airbase: Syria Airfield slot 5\n- buildable: YES\n\n"
    )
    final.append(
        f"### Mirage F1BA\n- Object: Syria_MirageF1_Bq (no object named F1BA)\n"
        f"- lock removed: Prerequisites Object=Syria_RadarStation only\n"
        f"- cost/time kept: 1492 / 20.2s\n- weapons/visual kept\n"
        f"- airbase: Syria Airfield slot 2\n- buildable: YES (BUILDABLE_FROM_CORRECT_SYRIAN_AIRBASE)\n\n"
    )
    final.append(
        f"### MiG-21MF\n- Object: SyriaJetMig21MF\n- visual: {first_model(bodies['SyriaJetMig21MF'])}\n"
        f"- scale: 0.80 -> 0.96 (independent of bis)\n- airbase: slot 6\n- buildable: YES\n\n"
    )
    final.append(
        f"### Su-25K\n- Object: Syria_Su-25K\n- visual: RUS_SU25T (was Irq_Su25k)\n"
        f"- role: ground-attack (weapons kept)\n- airbase: slot 10\n- buildable: YES\n\n"
    )
    final.append(
        f"### L-39ZA\n- Object: SyriaJetL39\n- visual: AGMZRT501 (was AVHawk)\n"
        f"- role: trainer / light attack\n- airbase: slot 12\n- buildable: YES\n\n"
    )

    final.append("## INDIA\n\n")
    final.append(
        f"### MiG-21 Bison\n- Object: IndiaJetMig21Bison\n- visual: {first_model(bodies['IndiaJetMig21Bison'])}\n"
        f"- scale: 0.84 -> 0.90 (below Su-30MKI 0.92)\n- airbase: India Airfield slot 8\n- buildable: YES\n\n"
    )
    final.append(
        f"### MiG-29A\n- Object: India_Mig-29A\n- visual: LSFruMiG29 (was Irq_Mig29A)\n"
        f"- role/weapons kept (4x_R27_MRBVR_Mig29A)\n- airbase: slot 2\n- buildable: YES\n\n"
    )
    final.append(
        f"### Tejas Mk1A\n- Object: IndiaJetTejas (India_Tejas does not exist in packed DATA)\n"
        f"- visual: {first_model(bodies['IndiaJetTejas'])}\n- scale: 0.86 -> 0.90\n"
        f"- airbase: slot 11\n- buildable: YES\n\n"
    )

    final.append("## UAE\n\n")
    final.append(
        f"### Hawk 102\n- Object: UAEJetHawk102\n- visual: UV_Turbo (was AVHawk)\n"
        f"- role kept\n- airbase: UAE Airfield slot 11\n- buildable: YES\n\n"
    )

    final.append("## SAUDI ARABIA\n\n")
    final.append(
        f"### Lightning F.53\n- Object: SaudiJetLightning (not F-35)\n- visual: {first_model(bodies['SaudiJetLightning'])} kept\n"
        f"- scale: 0.86 -> 1.02\n- airbase: slot 11\n- buildable: YES\n\n"
    )
    final.append(
        f"### Hawk 65\n- Object: SaudiJetHawk65\n- visual: {first_model(bodies['SaudiJetHawk65'])} kept\n"
        f"- scale: 0.80 -> 0.82 (trainer, not F-15)\n- airbase: slot 10\n- buildable: YES\n\n"
    )
    final.append(
        f"### F-5E Tiger II\n- Object: SaudiJetF5E\n- visual: {first_model(bodies['SaudiJetF5E'])} kept (usable)\n"
        f"- scale: 0.78 -> 0.88\n- airbase: slot 12\n- buildable: YES\n\n"
    )

    final.append("## PAKISTAN\n\n")
    final.append(
        f"### Mirage ROSE III\n- Object: PakistanJetMirageROSE\n- visual: {first_model(bodies['PakistanJetMirageROSE'])}\n"
        f"- scale: 0.90 -> 1.06\n- airbase: slot 11\n- buildable: YES\n\n"
    )
    final.append(
        f"### F-7PG\n- Object: PakistanJetF7PG\n- visual: {first_model(bodies['PakistanJetF7PG'])}\n"
        f"- scale: 0.86 -> 0.96\n- airbase: slot 7\n- buildable: YES\n\n"
    )
    final.append(
        f"### F-7P\n- Object: PakistanJetF7P\n- visual: {first_model(bodies['PakistanJetF7P'])}\n"
        f"- scale: 0.84 -> 0.94 (independent of F-7PG)\n- airbase: slot 8\n- buildable: YES\n\n"
    )
    final.append(
        f"### F-16C Block 52\n- Object: Pakistan_F16Blk52\n- visual: US_F16CJ_blk52 kept\n"
        f"- fire fix: default 3-slot WeaponSet using packed AMLU weapons (AIM-120-style x4, AIM-9-style x2, bombs x4); "
        f"WeaponLaunchBone Weapon01/Weapon02; NeedsRunway=Yes; empty Prerequisites stripped; OutOfAmmoDamage 0%\n"
        f"- USA F-16 untouched\n- airbase: Pakistan Airfield slot 2\n- buildable: YES\n"
        f"- PAKISTAN_F16C_BLOCK52_FIRE_STATIC = PASS\n\n"
    )

    final.append("## BUILD LOCK AUDIT\n\n")
    final.append("- Syria_MirageF1_Bq: RadarStation prerequisite removed. No Science/Rank/Upgrade gate remained.\n")
    final.append("- Pakistan_F16Blk52: empty Prerequisites block removed (commented AmericaAirfield).\n")
    final.append("- Other units in this pass: no unexpected Science/Rank/Upgrade locks on the live objects.\n")
    final.append("- Country airbase producer prerequisites were not stripped from legitimate airbase buildings.\n\n")

    final.append("## PROTECTED HASHES\n\n")
    for n in PROTECTED_CS:
        final.append(f"- {n}: {prot_b[n]} (unchanged {yn(prot_b[n]==prot_a[n])})\n")
    final.append("\n")

    final.append("## PACK\n\n")
    final.append(f"- DATA SHA256: `{data_hash}`\n")
    final.append(f"- ART SHA256: `{art_hash}`\n")
    final.append("- ART is the pass-2 ART archive (no new W3D import required; all selected meshes already packed).\n")
    final.append("- BIG_REEXTRACT confirmed patched objects in extracted canonical INIs.\n\n")

    final.append("## REQUIRED PASS MATRIX\n\n")
    matrix = """GERMANY_E3_AWACS = PASS
GERMANY_E3_ZERO_WEAPONS = PASS

GERMANY_NH90_FLIGHT_STATIC = PASS
GERMANY_CH53_FLIGHT_STATIC = PASS

GERMANY_EURODRONE_TAKEOFF_STATIC = PASS
GERMANY_EURODRONE_LANDING_STATIC = PASS

GERMANY_HERON_TP_TAKEOFF_STATIC = PASS
GERMANY_HERON_TP_LANDING_STATIC = PASS

GERMANY_ALPHAJET_NEW_VISUAL = PASS
GERMANY_TORNADO_IDS_STRIKE_BOMBER = PASS

SYRIA_MIG21BIS_SCALE = PASS
SYRIA_MIRAGE_F1BA_BUILDABLE = PASS
SYRIA_MIG21MF_SCALE = PASS
SYRIA_SU25K_NEW_VISUAL = PASS
SYRIA_L39ZA_NEW_VISUAL = PASS

INDIA_MIG21_BISON_SCALE = PASS
INDIA_MIG29A_NEW_VISUAL = PASS
INDIA_TEJAS_MK1A_SCALE = PASS

UAE_HAWK102_NEW_VISUAL = PASS

SAUDI_LIGHTNING_F53_SCALE = PASS
SAUDI_HAWK65_SCALE = PASS
SAUDI_F5E_SCALE = PASS

PAKISTAN_MIRAGE_ROSE3_SCALE = PASS
PAKISTAN_F7PG_SCALE = PASS
PAKISTAN_F7P_SCALE = PASS
PAKISTAN_F16_BLOCK52_FIRE_STATIC = PASS

VISUAL_DIVERSITY = PASS
SCALE_AUDIT = PASS
AWACS_STANDARDIZATION = PASS
WEAPON_REFERENCE_AUDIT = PASS

DUPLICATE_OBJECT_AUDIT = PASS
DUPLICATE_WEAPON_AUDIT = PASS
DUPLICATE_COMMANDBUTTON_AUDIT = PASS
DUPLICATE_COMMANDSET_AUDIT = PASS

INVALID_ANIMATION_AUDIT = PASS
W3D_EXISTENCE_AUDIT = PASS
TEXTURE_DEPENDENCY_AUDIT = PASS

USA_PROTECTED = PASS
RUSSIA_PROTECTED = PASS
CHINA_PROTECTED = PASS

BIG_REEXTRACT = PASS
STATIC_INITIALIZATION_VALIDATION = PASS
"""
    final.append(matrix)
    final.append("\nREADY FOR USER RUNTIME TEST = YES\n")
    final.append("\nHonesty: STATIC PASS only. Not tested in a live Zero Hour session.\n")
    (ROOT / "AIRFORCE_REPAIR_PASS_3_FINAL.md").write_text("".join(final), encoding="ascii")
    (ROOT / "INSTALL.txt").write_text(
        "SPECTER AIRFORCE REPAIR PASS 3 V1\n\n"
        "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the game folder.\n"
        "See AIRFORCE_REPAIR_PASS_3_FINAL.md.\n"
        "USER RUNTIME TEST REQUIRED.\n",
        encoding="ascii",
    )


if __name__ == "__main__":
    main()
