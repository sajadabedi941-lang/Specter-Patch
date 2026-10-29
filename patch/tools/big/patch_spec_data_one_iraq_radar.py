#!/usr/bin/env python3
"""Patch _SPEC_DATA_ONE.big: grant Iraq radar/minimap and detach Spy Satellite.

Why PR #692 / release iraq-radar-spy-map-2c93 did not fix these two bugs:

1. Radar/Minimap never granted
   RadarUpgrade on the last-win Object Iraq_RadarStation had only
   DisableProof = No. Working stations in this same BIG (Egypt, India, …)
   pair GrantUpgradeCreate Upgrade_AmericaRadar with
   RadarUpgrade { TriggeredBy = Upgrade_AmericaRadar }. Without TriggeredBy
   the ZH upgrade module never runs, so the player radar/minimap stays off.
   #692 left that module unchanged and only removed P30 spawn / SSC.

2. Spy Satellite still on Iraq radar
   #692 last-won CommandSet slot 1 to Command_IraqiRadarSearch and kept
   OCLSpecialPower SpecialPowerIraqiRadarSearch. That button is Spy Satellite
   (CONTROLBAR:SpySatellite, SSSpySat, SPECIAL_SPY_SATELLITE) and the
   SpecialPower uses the same enum as SpecialPowerSpySatellite.

This rebuild updates the two existing last-win files already inside the BIG
(no new overlay / no new INI path). Other countries' Spy Satellite
CommandSets, Command_SpySatelliteScan, SpecialPowerSpySatellite, and
SUPERWEAPON_SpySatellite are not edited.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_PATH = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
OBJ_PATH = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"

SPY_BUTTONS = (
    "Command_SpySatelliteScan",
    "Command_SpecterSpySatelliteFee",
    "Command_IraqiRadarSearch",
)
SPY_OBJECT_TOKENS = (
    "SpecialPowerSpySatellite",
    "SUPERWEAPON_SpySatellite",
    "SpecialPowerIraqiRadarSearch",
    "SUPERWEAPON_IraqiRadarScan",
    "ModuleTag_SSC",
    "ModuleTag_RadarSearch",
)


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


def last_win_block(file_map: dict[str, bytes], kind: str, name: str) -> tuple[str | None, str | None]:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower)\s|\Z)",
        re.S,
    )
    last = None
    src = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin1")
        for m in pat.finditer(text):
            last = m.group(0)
            src = path
    return src, last


def crlf(body: str) -> bytes:
    return body.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


COMMANDSET_ZZZZ = """\
; SPECTER last-win inside _SPEC_DATA_ONE.big.
; Sorts after CommandSet_ZZZZ_SpySatelliteRadar.ini so Iraq radar loses every
; Spy Satellite button (including Command_IraqiRadarSearch, which is the same
; SPECIAL_SPY_SATELLITE control) without editing other countries' CommandSets.

CommandSet Iraq_RadarStationCommandSet
  3 = Command_IraqiCamoflage
  4 = Command_Upgrade_MTS
  5 = Command_ConstructIraq_Sarab3
  6 = Command_ConstructIraq_Ababil200
  7 = Command_ConstructIraq_Lamiaa
  14 = Command_Sell
  15 = Command_ConstructIraqDroneQuds5_AI
  9 = Command_ConstructSpecterRadarHeron
  10 = Command_ConstructSpecterRadarMQ4
  11 = Command_ConstructSpecterRadarOrlan10
  12 = Command_ConstructSpecterRadarShahedLauncher
End
"""

OBJECT_ZZZZ = """\
; SPECTER last-win. Path sorts after Object\\zzzz_SPECTER_CountryScans.ini
; and after Specter copies of Iraq_RadarStation.ini.
; Radar/minimap: GrantUpgradeCreate Upgrade_AmericaRadar + RadarUpgrade
; TriggeredBy = Upgrade_AmericaRadar (same pair as Egypt/India stations).
; DisableProof = No so sell / die / unpowered drop player radar.
; Spy Satellite fully detached: no SSC, no IraqiRadarSearch OCLSpecialPower.
; P30_Radar_Deploy_St spawn stays omitted. IraqiRadarScan remains defined so
; leftover SUPERWEAPON_IraqiRadarScan refs are not a missing Thing.

Object Iraq_RadarStation
Scale 0.9
  SelectPortrait         = irq_rdrstatn
  ButtonImage            = irq_rdrstatn
  Draw = W3DModelDraw ModuleTag_0591
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model                   = Irq_P3
      Animation               = Irq_P3.Irq_P3
      AnimationMode           = Loop
    End
    ConditionState       = DAMAGED
      Model                   = Irq_P3
      Animation               = Irq_P3.Irq_P3
      AnimationMode           = Loop
    End
    ConditionState       = REALLYDAMAGED RUBBLE
      Model                   = Irq_P3
      Animation               = Irq_P3.Irq_P3
      AnimationMode           = Loop
    End
  End
  PlacementViewAngle = -45
  DisplayName      = OBJECT:RadarStation
  Side             = Iraq
  EditorSorting    = STRUCTURE
  Prerequisites
    Object = Iraq_SupplyCenter
  End
  BuildCost        = 1300
  BuildTime        = 20
  EnergyProduction    = -2
  CommandSet          = Iraq_RadarStationCommandSet
  MaxSimultaneousOfType  = 1
  VisionRange         = 100.0
  ShroudClearingRange = 280
  ArmorSet
    Conditions        = None
    Armor             = StructureArmor
    DamageFX          = StructureDamageFXNoShake
  End
  ExperienceValue     = 150 150 150 150
  VoiceSelect           = AirfieldUSASelect
  SoundOnDamaged        = BuildingDamagedStateLight
  SoundOnReallyDamaged  = BuildingDestroy
  UnitSpecificSounds
    UnderConstruction     = UnderConstructionLoop
  End
  RadarPriority       = STRUCTURE
  KindOf              = PRELOAD STRUCTURE SELECTABLE IMMOBILE CAPTURABLE MP_COUNT_FOR_VICTORY SCORE_CREATE FS_FACTORY AUTO_RALLYPOINT POWERED
  Body                = StructureBody ModuleTag_10
    MaxHealth         = 1000.0
    InitialHealth     = 1000.0
    SubdualDamageCap        = 3200
    SubdualDamageHealRate   = 500
    SubdualDamageHealAmount = 100
  End
  Behavior = ProductionUpdate ModuleTag_0595
  End
  Behavior = FireWeaponCollide ModuleTag_KillRadar
    CollideWeapon  = SamInstallationDismantle
    RequiredStatus = SOLD
  End
  Behavior = FireWeaponCollide ModuleTag_KillRadar2
    CollideWeapon  = SamInstallationDismantle
    RequiredStatus = SOLD
  End
  Behavior             = CreateObjectDie ModuleTag_0598
    CreationList  = OCL_SmallStructureDebris
  End
  Behavior             = FXListDie ModuleTag_02599
    DeathFX       = FX_StructureMediumDeath
  End
  Behavior = FlammableUpdate ModuleTag_11
    AflameDuration = 5000
    AflameDamageAmount = 5
    AflameDamageDelay = 500
  End
  Behavior = DestroyDie ModuleTag_0597
  End
  Behavior = GrantUpgradeCreate ModuleTag_0xd99
    UpgradeToGrant    = Upgrade_AmericaRadar
    ExemptStatus      = UNDER_CONSTRUCTION
  End
  Behavior        = RadarUpgrade ModuleTag_0d995
    TriggeredBy   = Upgrade_AmericaRadar
    DisableProof  = No
  End
  Behavior = ProductionUpdate ModuleTag_12b56
    NumDoorAnimations            = 1
    DoorOpeningTime              = 4000
    DoorWaitOpenTime             = 2000
    DoorCloseTime                = 5000
    ConstructionCompleteDuration = 1500
  End
  Behavior = DefaultProductionExitUpdate ModuleTag_13d32
    UnitCreatePoint   = X:  0.0  Y:-27.0   Z:0.0
    NaturalRallyPoint = X: 57.0  Y:-27.0   Z:0.0
  End
  Behavior         = FireWeaponWhenDeadBehavior ModuleTag_KillRadar43f
    DeathWeapon    = GenericSideObjectKiller
    StartsActive   = Yes
  End
  Behavior         = FireWeaponCollide ModuleTag_KillRadarSolds12c43
    CollideWeapon  = GenericSideObjectKiller
    RequiredStatus = SOLD
  End
  Behavior = TransitionDamageFX ModuleTag_12f43
    DamagedParticleSystem1       = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem1 = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem2 = Bone:None RandomBone:No PSys:StructureTransitionMediumExplosion
    ReallyDamagedParticleSystem3 = Bone:None RandomBone:No PSys:StructureTransitionMediumShockwave
  End
  Geometry            = BOX
  GeometryMajorRadius = 75.0
  GeometryMinorRadius = 71.0
  GeometryHeight      = 30.0
  GeometryIsSmall     = No
End

Object IraqiRadarScan
  VisionRange = 300.0
  EditorSorting = SYSTEM
  KindOf = NO_COLLIDE IMMOBILE UNATTACKABLE INERT
  Body = ImmortalBody ModuleTag_01
    MaxHealth = 1
    InitialHealth = 1
  End
  Behavior = DynamicShroudClearingRangeUpdate ModuleTag_02
    FinalVision = 0.0
    ShrinkDelay = 10000
    ShrinkTime = 5000
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
    MinLifetime = 13000
    MaxLifetime = 13000
  End
  Behavior = StealthDetectorUpdate ModuleTag_04
    DetectionRate = 500
  End
End
"""


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def validate(file_map: dict[str, bytes]) -> None:
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _require(bool(cs), "Iraq_RadarStationCommandSet missing")
    _require(cs_src == CS_PATH, f"Iraq CommandSet last-win moved to {cs_src}")
    for btn in SPY_BUTTONS:
        _require(btn not in cs, f"Iraq radar CommandSet still has {btn} ({cs_src})")
    _require("Command_Sell" in cs, "Iraq radar lost Command_Sell")
    _require("Command_IraqiCamoflage" in cs, "Iraq radar lost Command_IraqiCamoflage")

    obj_src, obj = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _require(bool(obj), "Object Iraq_RadarStation missing")
    _require(obj_src == OBJ_PATH, f"Iraq_RadarStation last-win moved to {obj_src}")
    for tok in SPY_OBJECT_TOKENS:
        _require(tok not in obj, f"Iraq_RadarStation still has {tok} ({obj_src})")
    _require("P30_Radar_Deploy_St" not in obj, f"Iraq_RadarStation still spawns P30 ({obj_src})")
    _require("RadarUpgrade" in obj, "Iraq_RadarStation lost RadarUpgrade")
    _require("TriggeredBy" in obj and "Upgrade_AmericaRadar" in obj, "Iraq_RadarStation RadarUpgrade missing TriggeredBy = Upgrade_AmericaRadar")
    ru = re.search(r"Behavior\s*=\s*RadarUpgrade.*?End", obj, re.S)
    _require(bool(ru), "Iraq_RadarStation RadarUpgrade block missing")
    _require("TriggeredBy" in ru.group(0) and "Upgrade_AmericaRadar" in ru.group(0), "RadarUpgrade block lacks TriggeredBy = Upgrade_AmericaRadar")
    _require("DisableProof" in ru.group(0) and "No" in ru.group(0), "RadarUpgrade lost DisableProof = No")
    guc = re.search(r"Behavior\s*=\s*GrantUpgradeCreate.*?End", obj, re.S)
    _require(bool(guc) and "Upgrade_AmericaRadar" in guc.group(0), "Iraq_RadarStation lost GrantUpgradeCreate Upgrade_AmericaRadar")
    _require("ExemptStatus" in guc.group(0) and "UNDER_CONSTRUCTION" in guc.group(0), "GrantUpgradeCreate lost ExemptStatus UNDER_CONSTRUCTION")
    _require("RequiredStatus = SOLD" in obj, "Iraq_RadarStation lost sell teardown")
    _require("FireWeaponWhenDeadBehavior" in obj, "Iraq_RadarStation lost death teardown")
    _require("ShroudClearingRange = 280" in obj, "Iraq_RadarStation ShroudClearingRange changed")
    _require("CommandSet          = Iraq_RadarStationCommandSet" in obj or "CommandSet = Iraq_RadarStationCommandSet" in obj, "Iraq_RadarStation lost CommandSet link")

    scan_src, scan = last_win_block(file_map, "Object", "IraqiRadarScan")
    _require(bool(scan), "Object IraqiRadarScan missing")
    _require("DynamicShroudClearingRangeUpdate" in scan, f"IraqiRadarScan missing shroud ping ({scan_src})")

    btn_src, btn = last_win_block(file_map, "CommandButton", "Command_SpySatelliteScan")
    _require(bool(btn) and "SpecialPowerSpySatellite" in btn, "Command_SpySatelliteScan must remain for other buildings")

    ocl_src, ocl = last_win_block(file_map, "ObjectCreationList", "SUPERWEAPON_SpySatellite")
    _require(bool(ocl) and "SpySatellitePing" in ocl, "SUPERWEAPON_SpySatellite must remain for other buildings")

    sp_src, sp = last_win_block(file_map, "SpecialPower", "SpecialPowerSpySatellite")
    _require(bool(sp) and "SPECIAL_SPY_SATELLITE" in sp, "SpecialPowerSpySatellite must remain")

    up_src, up = last_win_block(file_map, "Upgrade", "Upgrade_AmericaRadar")
    _require(bool(up) and "ACT_UPGRADE_RADAR" in up, "Upgrade_AmericaRadar missing")

    # Other countries keep Spy Satellite buttons.
    for other_cs in (
        "AmericaRadarStationCommandSet",
        "ChinaRadarStationCommandSet",
        "RussiaRadarStationCommandSet",
        "IranExpandedRadarCommandSet",
        "Japan_RadarStationCommandSet",
    ):
        src, body = last_win_block(file_map, "CommandSet", other_cs)
        _require(bool(body), f"{other_cs} missing")
        _require("Command_SpySatelliteScan" in body, f"{other_cs} lost Command_SpySatelliteScan ({src})")

    egypt_src, egypt = last_win_block(file_map, "Object", "Egypt_RadarStation")
    _require(bool(egypt) and "TriggeredBy" in egypt and "Upgrade_AmericaRadar" in egypt, f"Egypt_RadarStation radar pair changed ({egypt_src})")

    # Prior accepted last-wins must stay.
    _, dl = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _require(bool(dl) and "DamageDealtAtSelfPosition = Yes" in dl, "92N6R_FireControlDataLink last-win lost")
    _, htdl = last_win_block(file_map, "Weapon", "HT233_FireControlDataLink")
    _require(bool(htdl) and "DamageDealtAtSelfPosition = Yes" in htdl, "HT233_FireControlDataLink last-win lost")
    _, hq = last_win_block(file_map, "ObjectCreationList", "OCL_HQ9_Deployed")
    _require(bool(hq) and "HQ9_FireControlSystem" in hq, "OCL_HQ9_Deployed last-win lost")
    _, s400abm = last_win_block(file_map, "Weapon", "3x_LRSAM_40N6KMissile_ABM")
    _require(bool(s400abm) and "CRUSH" in s400abm, "S-400 ABM interceptor changed")
    _, fr = last_win_block(file_map, "CommandSet", "FranceSupplyCenterCommandSet")
    _require(bool(fr) and "Command_ConstructFranceHelicopterCH47F" in fr, "France Supply Centre last-win lost")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()

    entries, raw = read_big(args.src_big)
    file_map: dict[str, bytes] = {}
    for name, off, size in entries:
        file_map[name] = raw[off : off + size]

    extras = {
        CS_PATH: COMMANDSET_ZZZZ,
        OBJ_PATH: OBJECT_ZZZZ,
    }
    changed = []
    for name, body in extras.items():
        if name not in file_map:
            raise SystemExit(f"expected existing last-win missing: {name}")
        encoded = crlf(body)
        if file_map[name] != encoded:
            file_map[name] = encoded
            changed.append(name)

    if not changed:
        raise SystemExit("no last-win content changed")

    validate(file_map)

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    out = build_big(file_map)
    args.out_big.write_bytes(out)
    rebuilt, rraw = read_big(args.out_big)
    if len(rebuilt) != len(file_map):
        raise SystemExit("rebuild entry count mismatch")
    hdr_size = struct.unpack(">I", rraw[4:8])[0]
    if hdr_size != len(rraw):
        raise SystemExit(f"BIG size field {hdr_size} != file {len(rraw)}")

    src_sha = sha256(args.src_big)
    out_sha = sha256(args.out_big)
    print(f"SRC  size={args.src_big.stat().st_size} sha256={src_sha}")
    print(f"OUT  size={args.out_big.stat().st_size} sha256={out_sha} entries={len(file_map)}")
    print("Updated:")
    for c in changed:
        print(f"  {c}")
    Path(str(args.out_big) + ".sha256").write_text(out_sha + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
