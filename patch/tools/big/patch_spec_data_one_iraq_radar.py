#!/usr/bin/env python3
"""Patch _SPEC_DATA_ONE.big: Iraq radar Spy Satellite off + map spawn fix.

Spy Satellite on Iraq_RadarStation comes from CommandSet_ZZZZ_SpySatelliteRadar.ini
(Command_SpySatelliteScan + Command_SpecterSpySatelliteFee) plus OCLSpecialPower
ModuleTag_SSC (SpecialPowerSpySatellite / SUPERWEAPON_SpySatellite) on SPEC copies.
SpecialPowerSpySatellite and SpecialPowerIraqiRadarSearch share Enum
SPECIAL_SPY_SATELLITE.

Map break: FireWeaponUpdate P30_Radar_Deploy_St -> OCL_P30_DeployViaSt spawns
IraqRadarP30 (RebuildHoleExposeDie structure) on top of the station.

Starts from the 92N6E/HT-233 radar-link BIG. Does not edit interceptor weapons
or other countries' CommandSets.
"""
from __future__ import annotations

import argparse
import hashlib
import re
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


COMMANDSET_ZZZZ = r"""
; SPECTER last-win inside _SPEC_DATA_ONE.big.
; Sorts after CommandSet_ZZZZ_SpySatelliteRadar.ini so Iraq radar loses Spy Satellite
; buttons without editing other countries' radar CommandSets in that file.

CommandSet Iraq_RadarStationCommandSet
  1 = Command_IraqiRadarSearch
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

OBJECT_ZZZZ = r"""
; SPECTER last-win. Path sorts after Object\zzzz_SPECTER_CountryScans.ini
; (0_SPECTER_NoGeneralSpySatellite overlay) and after Specter\Vietnam*\Iraq_RadarStation.ini.
; Spy Satellite module removed. P30_Radar_Deploy_St spawn removed (map/rebuild-hole).
; RadarUpgrade + existing Upgrade_AmericaRadar grant kept (ZH minimap / fog radar).
; Iraqi country scan kept. IraqiRadarScan defined here so SUPERWEAPON_IraqiRadarScan
; is not a missing object if the overlay is absent.

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
  Behavior           = OCLSpecialPower ModuleTag_RadarSearch
    SpecialPowerTemplate = SpecialPowerIraqiRadarSearch
    OCL                  = SUPERWEAPON_IraqiRadarScan
    CreateLocation       = CREATE_AT_LOCATION
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


def validate(file_map: dict[str, bytes]) -> None:
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    if not cs:
        raise SystemExit("Iraq_RadarStationCommandSet missing")
    if "Command_SpySatelliteScan" in cs or "Command_SpecterSpySatelliteFee" in cs:
        raise SystemExit(f"Iraq radar CommandSet still has Spy Satellite ({cs_src})")
    if "Command_IraqiRadarSearch" not in cs:
        raise SystemExit("Iraq radar lost Command_IraqiRadarSearch")

    obj_src, obj = last_win_block(file_map, "Object", "Iraq_RadarStation")
    if not obj:
        raise SystemExit("Object Iraq_RadarStation missing")
    if "SpecialPowerSpySatellite" in obj or "SUPERWEAPON_SpySatellite" in obj:
        raise SystemExit(f"Iraq_RadarStation still has Spy Satellite module ({obj_src})")
    if "P30_Radar_Deploy_St" in obj:
        raise SystemExit(f"Iraq_RadarStation still spawns P30 ({obj_src})")
    if "RadarUpgrade" not in obj:
        raise SystemExit("Iraq_RadarStation lost RadarUpgrade")
    if "Upgrade_AmericaRadar" not in obj:
        raise SystemExit("Iraq_RadarStation lost existing radar grant")
    if "SpecialPowerIraqiRadarSearch" not in obj:
        raise SystemExit("Iraq_RadarStation lost Iraqi radar search")
    if "ShroudClearingRange = 280" not in obj:
        raise SystemExit("Iraq_RadarStation ShroudClearingRange changed")

    scan_src, scan = last_win_block(file_map, "Object", "IraqiRadarScan")
    if not scan:
        raise SystemExit("Object IraqiRadarScan missing")
    if "DynamicShroudClearingRangeUpdate" not in scan:
        raise SystemExit(f"IraqiRadarScan missing shroud ping ({scan_src})")

    # Other buildings keep Spy Satellite.
    usa_src, usa = last_win_block(file_map, "Object", "AmericaCommandCenter")
    # May be named differently; check Command_SpySatelliteScan button still exists.
    btn_src, btn = last_win_block(file_map, "CommandButton", "Command_SpySatelliteScan")
    if not btn or "SpecialPowerSpySatellite" not in btn:
        raise SystemExit("Command_SpySatelliteScan must remain for other buildings")

    ocl_src, ocl = last_win_block(file_map, "ObjectCreationList", "SUPERWEAPON_SpySatellite")
    if not ocl or "SpySatellitePing" not in ocl:
        raise SystemExit("SUPERWEAPON_SpySatellite must remain for other buildings")

    # Prior S-400 / HQ-9 radar-link last-wins must stay.
    _, dl = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    if not dl or "DamageDealtAtSelfPosition = Yes" not in dl:
        raise SystemExit("92N6R_FireControlDataLink last-win lost")
    _, htdl = last_win_block(file_map, "Weapon", "HT233_FireControlDataLink")
    if not htdl or "DamageDealtAtSelfPosition = Yes" not in htdl:
        raise SystemExit("HT233_FireControlDataLink last-win lost")
    _, hq = last_win_block(file_map, "ObjectCreationList", "OCL_HQ9_Deployed")
    if not hq or "HQ9_FireControlSystem" not in hq:
        raise SystemExit("OCL_HQ9_Deployed last-win lost")
    _, s400abm = last_win_block(file_map, "Weapon", "3x_LRSAM_40N6KMissile_ABM")
    if not s400abm or "CRUSH" not in s400abm:
        raise SystemExit("S-400 ABM interceptor changed")


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
        r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini": COMMANDSET_ZZZZ,
        r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini": OBJECT_ZZZZ,
    }
    changed = []
    for name, body in extras.items():
        if name in file_map:
            raise SystemExit(f"already present: {name}")
        file_map[name] = body.replace("\n", "\r\n").encode("latin1")
        changed.append(name)

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
    print("Added:")
    for c in changed:
        print(f"  {c}")
    Path(str(args.out_big) + ".sha256").write_text(out_sha + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
