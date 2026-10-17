#!/usr/bin/env python3
"""Iran-only dual airbase: Large (TheAirPort 4x4) + Heavy (HXUSABigAirPort 3x2).

- Retarget Command_ConstructIranAirfield -> Iran_LargeAirBase
- Replace Clear Mines (slot 14) with Command_ConstructIran_HeavyAirBase
- Preserve IranExpandedAirfieldCommandSet on LargeAirBase
- Heavy CommandSet = Rally/Sell only
- No other factions / aircraft / ART / CSF changes
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_iran_dual_airbase"
VERIFY = MASTER / "_extract_iran_dual_airbase_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_IRAN_DUAL_AIRBASE.zip"
OUT_HASH = ROOT / "Release/DATA_IRAN_DUAL_AIRBASE_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_IRAN_DUAL_AIRBASE_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_IRAN_DUAL_AIRBASE_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/Iranian Army/Buildings"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"
AC130_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
)
IRAN_AIR_KEY = (
    "Data\\INI\\Object\\Specter\\Iranian Army\\Buildings\\Airfield.ini"
)
IRAN_RADAR_KEY = (
    "Data\\INI\\Object\\Specter\\Iranian Army\\Buildings\\RadarStation.ini"
)
IRAN_LARGE_KEY = (
    "Data\\INI\\Object\\Specter\\Iranian Army\\Buildings\\Iran_LargeAirBase.ini"
)
IRAN_HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\Iranian Army\\Buildings\\Iran_HeavyAirBase.ini"
)
PAK_LARGE_KEY = (
    "Data\\INI\\Object\\Specter\\Pakistan Armed Forces\\Buildings\\"
    "Pakistan_LargeAirBase.ini"
)
PAK_HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\Pakistan Armed Forces\\Buildings\\"
    "Pakistan_HeavyAirBase.ini"
)
USA_HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)

FREEZE_KEYS = [
    CSF_KEY,
    AC130_KEY,
    PAK_LARGE_KEY,
    PAK_HEAVY_KEY,
    USA_HEAVY_KEY,
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_LargeAirBase.ini",
]


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


IRAN_LARGE_INI = r"""; SPECTER - Iran LARGE fighter airbase (dual-airbase)
; Geometry: TheAirPort.W3D (existing ART). Structural clone of Pakistan_LargeAirBase.
; Capacity: NumRows=4 x NumCols=4 = 16.
; Aircraft roster: IranExpandedAirfieldCommandSet (unchanged Iran fighters).

Object Iran_LargeAirBase

  ; *** ART Parameters ***
  SelectPortrait         = irn_airfield
  ButtonImage            = irn_airfield
  Draw = W3DModelDraw ModuleTag_01

    ; 16 parking slots: rows 1-4 x cols 1-4
    ExtraPublicBone = Runway1Parking1
    ExtraPublicBone = Runway1Parking2
    ExtraPublicBone = Runway1Parking3
    ExtraPublicBone = Runway1Parking4
    ExtraPublicBone = Runway2Parking1
    ExtraPublicBone = Runway2Parking2
    ExtraPublicBone = Runway2Parking3
    ExtraPublicBone = Runway2Parking4
    ExtraPublicBone = Runway3Parking1
    ExtraPublicBone = Runway3Parking2
    ExtraPublicBone = Runway3Parking3
    ExtraPublicBone = Runway3Parking4
    ExtraPublicBone = Runway4Parking1
    ExtraPublicBone = Runway4Parking2
    ExtraPublicBone = Runway4Parking3
    ExtraPublicBone = Runway4Parking4
    ExtraPublicBone = Runway1Park1Han
    ExtraPublicBone = Runway1Park2Han
    ExtraPublicBone = Runway1Park3Han
    ExtraPublicBone = Runway1Park4Han
    ExtraPublicBone = Runway2Park1Han
    ExtraPublicBone = Runway2Park2Han
    ExtraPublicBone = Runway2Park3Han
    ExtraPublicBone = Runway2Park4Han
    ExtraPublicBone = Runway3Park1Han
    ExtraPublicBone = Runway3Park2Han
    ExtraPublicBone = Runway3Park3Han
    ExtraPublicBone = Runway3Park4Han
    ExtraPublicBone = Runway4Park1Han
    ExtraPublicBone = Runway4Park2Han
    ExtraPublicBone = Runway4Park3Han
    ExtraPublicBone = Runway4Park4Han
    ExtraPublicBone = Runway1Prep1
    ExtraPublicBone = Runway1Prep2
    ExtraPublicBone = Runway1Prep3
    ExtraPublicBone = Runway1Prep4
    ExtraPublicBone = Runway2Prep1
    ExtraPublicBone = Runway2Prep2
    ExtraPublicBone = Runway2Prep3
    ExtraPublicBone = Runway2Prep4
    ExtraPublicBone = Runway3Prep1
    ExtraPublicBone = Runway3Prep2
    ExtraPublicBone = Runway3Prep3
    ExtraPublicBone = Runway3Prep4
    ExtraPublicBone = Runway4Prep1
    ExtraPublicBone = Runway4Prep2
    ExtraPublicBone = Runway4Prep3
    ExtraPublicBone = Runway4Prep4
    ExtraPublicBone = RunwayStart1
    ExtraPublicBone = RunwayStart2
    ExtraPublicBone = RunwayStart3
    ExtraPublicBone = RunwayStart4
    ExtraPublicBone = RunwayEnd1
    ExtraPublicBone = RunwayEnd2
    ExtraPublicBone = RunwayEnd3
    ExtraPublicBone = RunwayEnd4
    ExtraPublicBone = HeliPark01
    OkToChangeModelColor = Yes

    DefaultConditionState
      Model              = TheAirPort
      Animation          = THEAIRPORT.THEAIRPORT
      AnimationMode      = LOOP
    End
    ConditionState       = DAMAGED
      Model              = TheAirPort
      Animation          = THEAIRPORT.THEAIRPORT
      AnimationMode      = LOOP
      ParticleSysBone    = Smoke01 SmolderingSmoke
      ParticleSysBone    = Smoke01 SmokeStackHeat
      ParticleSysBone    = Smoke02 SmolderingSmoke
      ParticleSysBone    = Smoke02 SmokeStackHeat
      ParticleSysBone    = Smoke03 SmolderingSmoke
      ParticleSysBone    = Smoke03 SmokeStackHeat
      ParticleSysBone    = Fire01 SmolderingFire
      ParticleSysBone    = Fire01 SmokeStackHeat
    End
    ConditionState       = REALLYDAMAGED RUBBLE
      Model              = TheAirPort
      Animation          = THEAIRPORT.THEAIRPORT
      AnimationMode      = LOOP
      ParticleSysBone    = Smoke01 SmolderingSmoke
      ParticleSysBone    = Smoke01 SmokeStackHeat
      ParticleSysBone    = Smoke02 SmolderingSmoke
      ParticleSysBone    = Smoke02 SmokeStackHeat
      ParticleSysBone    = Smoke03 SmolderingSmoke
      ParticleSysBone    = Smoke03 SmokeStackHeat
      ParticleSysBone    = Smoke04 SmolderingSmoke
      ParticleSysBone    = Smoke04 SmokeStackHeat
      ParticleSysBone    = Smoke05 SmokeFactionLarge
      ParticleSysBone    = Smoke05 SmokeStackHeatLarge
      ParticleSysBone    = Smoke06 SmokeFactionLarge
      ParticleSysBone    = Smoke06 SmokeStackHeatLarge
      ParticleSysBone    = Fire01 SmolderingFire
      ParticleSysBone    = Fire01 SmokeStackHeat
      ParticleSysBone    = Fire02 SmolderingFire
      ParticleSysBone    = Fire02 SmokeStackHeat
      ParticleSysBone    = Fire03 FireFactionLarge
      ParticleSysBone    = Fire03 SmokeStackHeatLarge
      ParticleSysBone    = Spark01 SparksLarge
    End
    ConditionState       = RUBBLE
      Model              = TheAirPort
      Animation          = THEAIRPORT.THEAIRPORT
      AnimationMode      = LOOP
      ParticleSysBone    = Smoke01 SmolderingSmoke
      ParticleSysBone    = Smoke01 SmokeStackHeat
      ParticleSysBone    = Smoke02 SmolderingSmoke
      ParticleSysBone    = Smoke02 SmokeStackHeat
      ParticleSysBone    = Smoke03 SmolderingSmoke
      ParticleSysBone    = Smoke03 SmokeStackHeat
      ParticleSysBone    = Smoke04 SmolderingSmoke
      ParticleSysBone    = Smoke04 SmokeStackHeat
      ParticleSysBone    = Smoke05 SmokeFactionLarge
      ParticleSysBone    = Smoke05 SmokeStackHeatLarge
      ParticleSysBone    = Smoke06 SmokeFactionLarge
      ParticleSysBone    = Smoke06 SmokeStackHeatLarge
      ParticleSysBone    = Fire01 SmolderingFire
      ParticleSysBone    = Fire01 SmokeStackHeat
      ParticleSysBone    = Fire02 SmolderingFire
      ParticleSysBone    = Fire02 SmokeStackHeat
      ParticleSysBone    = Fire03 FireFactionLarge
      ParticleSysBone    = Fire03 SmokeStackHeatLarge
      ParticleSysBone    = Spark01 SparksLarge
    End
  End

  PlacementViewAngle = -45

  ; ***DESIGN parameters ***
  DisplayName      = OBJECT:Airfield
  Side             = Iran
  EditorSorting    = STRUCTURE

  Prerequisites
    Object = IranWarFactory
  End

  BuildCost           = 1000
  BuildTime           = 30.0
  EnergyProduction    = -1
  CommandSet          = IranExpandedAirfieldCommandSet
  VisionRange         = 210.0
  ShroudClearingRange = 208.0
  MaxSimultaneousOfType = 6
  ArmorSet
    Conditions        = None
    Armor             = StructureArmor
    DamageFX          = StructureDamageFXNoShake
  End
  ExperienceValue     = 150 150 150 150

  ; *** AUDIO Parameters ***
  VoiceSelect         = AirfieldUSASelect
  SoundOnDamaged        = BuildingDamagedStateLight
  SoundOnReallyDamaged  = BuildingDestroy

  UnitSpecificSounds
    UnderConstruction     = UnderConstructionLoop
  End

  ; *** ENGINEERING Parameters ***
  RadarPriority       = STRUCTURE
  KindOf              = PRELOAD STRUCTURE SELECTABLE IMMOBILE SCORE CAPTURABLE FS_FACTORY MP_COUNT_FOR_VICTORY AUTO_RALLYPOINT FS_AIRFIELD
  Body                = StructureBody ModuleTag_10
    MaxHealth         = 1500.0
    InitialHealth     = 1500.0
    SubdualDamageCap = 1700
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 100
  End

  Behavior = ParkingPlaceBehavior ModuleTag_11
    HealAmountPerSecond     = 11
    NumRows                 = 4
    NumCols                 = 4
    HasRunways              = Yes
    ApproachHeight          = 70
  End

  Behavior = ProductionUpdate ModuleTag_12d23
  End
  Behavior = BaseRegenerateUpdate ModuleTag_13ze
  End
  Behavior = AIUpdateInterface ModuleTag_3dd
    AutoAcquireEnemiesWhenIdle = Yes
    MoodAttackCheckRate = 250
  End
  Behavior = DestroyDie ModuleTag_14dc3
  End
  Behavior             = CreateObjectDie ModuleTag_15xv4
    CreationList  = OCL_ABPowerPlantExplode
  End
  Behavior             = FXListDie ModuleTag_17
    DeathFX       = FX_StructureMediumDeath
  End
  Behavior = FlammableUpdate ModuleTag_19
    AflameDuration = 5000
    AflameDamageAmount = 5
    AflameDamageDelay = 500
  End

  Behavior = TransitionDamageFX ModuleTag_31
    DamagedParticleSystem1       = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem1 = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem3 = Bone:None RandomBone:No PSys:StructureTransitionMediumShockwave
  End

  Geometry            = BOX
  GeometryMajorRadius = 225.0
  GeometryMinorRadius = 103.0
  GeometryHeight      = 40.0
  GeometryIsSmall     = No
  FactoryExitWidth    = 25
  Shadow          = SHADOW_VOLUME
  BuildCompletion = PLACED_BY_PLAYER

End
"""

IRAN_HEAVY_INI = r"""; SPECTER - Iran HEAVY airbase (dual-airbase)
; Geometry: HXUSABigAirPort.W3D (existing ART). Structural clone of Pakistan_HeavyAirBase.
; Capacity: NumRows=3 x NumCols=2 = 6 (Runway1Parking1-3 + Runway2Parking1-3).
; Production roster empty for this task - Rally/Sell only.

Object Iran_HeavyAirBase

  ; *** ART Parameters ***
  SelectPortrait         = irn_airfield
  ButtonImage            = irn_airfield
  Draw = W3DModelDraw ModuleTag_01

    ExtraPublicBone = Runway1Parking1
    ExtraPublicBone = Runway1Parking2
    ExtraPublicBone = Runway1Parking3
    ExtraPublicBone = Runway2Parking1
    ExtraPublicBone = Runway2Parking2
    ExtraPublicBone = Runway2Parking3
    ExtraPublicBone = Runway1Park1Han
    ExtraPublicBone = Runway1Park2Han
    ExtraPublicBone = Runway1Park3Han
    ExtraPublicBone = Runway2Park1Han
    ExtraPublicBone = Runway2Park2Han
    ExtraPublicBone = Runway2Park3Han
    ExtraPublicBone = Runway1Prep1
    ExtraPublicBone = Runway1Prep2
    ExtraPublicBone = Runway1Prep3
    ExtraPublicBone = Runway2Prep1
    ExtraPublicBone = Runway2Prep2
    ExtraPublicBone = Runway2Prep3
    ExtraPublicBone = RunwayStart1
    ExtraPublicBone = RunwayStart2
    ExtraPublicBone = RunwayEnd1
    ExtraPublicBone = RunwayEnd2
    OkToChangeModelColor = Yes

    DefaultConditionState
      Model              = HXUSABigAirPort
      Animation          = HXUSABIGAIRPORT.HXUSABIGAIRPORT
      AnimationMode      = LOOP
    End
    ConditionState       = DAMAGED
      Model              = HXUSABigAirPort
      Animation          = HXUSABIGAIRPORT.HXUSABIGAIRPORT
      AnimationMode      = LOOP
      ParticleSysBone    = Smoke01 SmolderingSmoke
      ParticleSysBone    = Smoke01 SmokeStackHeat
    End
    ConditionState       = REALLYDAMAGED RUBBLE
      Model              = HXUSABigAirPort
      Animation          = HXUSABIGAIRPORT.HXUSABIGAIRPORT
      AnimationMode      = LOOP
      ParticleSysBone    = Smoke01 SmolderingSmoke
      ParticleSysBone    = Smoke01 SmokeStackHeat
      ParticleSysBone    = Smoke01 SmokeFactionLarge
    End
    ConditionState       = RUBBLE
      Model              = HXUSABigAirPort
      Animation          = HXUSABIGAIRPORT.HXUSABIGAIRPORT
      AnimationMode      = LOOP
      ParticleSysBone    = Smoke01 SmolderingSmoke
      ParticleSysBone    = Smoke01 SmokeStackHeat
      ParticleSysBone    = Smoke01 SmokeFactionLarge
    End
  End

  PlacementViewAngle = -45

  ; ***DESIGN parameters ***
  DisplayName      = OBJECT:Airfield
  Side             = Iran
  EditorSorting    = STRUCTURE

  Prerequisites
    Object = IranSupplyCenter
  End

  BuildCost           = 1800
  BuildTime           = 25.0
  EnergyProduction    = -3
  CommandSet          = Iran_HeavyAirBaseCommandSet
  VisionRange         = 210.0
  ShroudClearingRange = 208.0
  MaxSimultaneousOfType = 4
  ArmorSet
    Conditions        = None
    Armor             = StructureArmor
    DamageFX          = StructureDamageFXNoShake
  End
  ExperienceValue     = 150 150 150 150

  ; *** AUDIO Parameters ***
  VoiceSelect         = AirfieldUSASelect
  SoundOnDamaged        = BuildingDamagedStateLight
  SoundOnReallyDamaged  = BuildingDestroy

  UnitSpecificSounds
    UnderConstruction     = UnderConstructionLoop
  End

  ; *** ENGINEERING Parameters ***
  RadarPriority       = STRUCTURE
  KindOf              = PRELOAD STRUCTURE SELECTABLE IMMOBILE SCORE CAPTURABLE FS_FACTORY MP_COUNT_FOR_VICTORY AUTO_RALLYPOINT FS_AIRFIELD
  Body                = StructureBody ModuleTag_10
    MaxHealth         = 1800.0
    InitialHealth     = 1800.0
    SubdualDamageCap = 2000
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 100
  End

  Behavior = ParkingPlaceBehavior ModuleTag_11
    HealAmountPerSecond     = 11
    NumRows                 = 3
    NumCols                 = 2
    HasRunways              = Yes
    ApproachHeight          = 50
  End

  Behavior = ProductionUpdate ModuleTag_12d23
  End
  Behavior = BaseRegenerateUpdate ModuleTag_13ze
  End
  Behavior = AIUpdateInterface ModuleTag_3dd
    AutoAcquireEnemiesWhenIdle = Yes
    MoodAttackCheckRate = 250
  End
  Behavior = DestroyDie ModuleTag_14dc3
  End
  Behavior             = CreateObjectDie ModuleTag_15xv4
    CreationList  = OCL_ABPowerPlantExplode
  End
  Behavior             = FXListDie ModuleTag_17
    DeathFX       = FX_StructureMediumDeath
  End
  Behavior = FlammableUpdate ModuleTag_19
    AflameDuration = 5000
    AflameDamageAmount = 5
    AflameDamageDelay = 500
  End

  Behavior = TransitionDamageFX ModuleTag_31
    DamagedParticleSystem1       = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem1 = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem3 = Bone:None RandomBone:No PSys:StructureTransitionMediumShockwave
  End

  Geometry            = BOX
  GeometryMajorRadius = 150.0
  GeometryMinorRadius = 105.0
  GeometryHeight      = 45.0
  GeometryIsSmall     = No
  FactoryExitWidth    = 25
  Shadow          = SHADOW_VOLUME
  BuildCompletion = PLACED_BY_PLAYER

End
"""

HEAVY_BUTTON = """CommandButton Command_ConstructIran_HeavyAirBase
  Command       = DOZER_CONSTRUCT
  Object        = Iran_HeavyAirBase
  TextLabel     = CONTROLBAR:ConstructIranAirfield
  ButtonImage   = irn_airfield
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipIranAirfield
End
"""

HEAVY_COMMANDSET = """CommandSet Iran_HeavyAirBaseCommandSet
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""


def patch_command_button(text: str) -> str:
    # Retarget existing Iran airfield construct button
    m = re.search(
        r"(?ms)^CommandButton\s+Command_ConstructIranAirfield\s*\n(.*?)(?=^CommandButton\s+\S+\s*$|\Z)",
        text,
    )
    if not m:
        raise SystemExit("Command_ConstructIranAirfield not found")
    block = m.group(0)
    new_block, n = re.subn(
        r"(?m)^(\s*Object\s*=\s*)IranAirfield(\s*)$",
        r"\1Iran_LargeAirBase\2",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"failed to retarget IranAirfield object n={n}")
    text = text[: m.start()] + new_block + text[m.end() :]

    if "Command_ConstructIran_HeavyAirBase" in text:
        raise SystemExit("Heavy construct button already exists")

    # Insert heavy button near Iran airfield button for locality
    insert_at = text.find(new_block) + len(new_block)
    # ensure trailing newline
    if not new_block.endswith("\n"):
        text = text[:insert_at] + "\n" + text[insert_at:]
        insert_at += 1
    text = text[:insert_at] + "\n" + HEAVY_BUTTON + text[insert_at:]
    return text


def patch_command_set(text: str) -> str:
    # Dozer: replace Clear Mines slot 14
    m = re.search(
        r"(?ms)^CommandSet\s+IranDozerCommandSet\s*\n(.*?)(?=^CommandSet\s+\S+\s*$|\Z)",
        text,
    )
    if not m:
        raise SystemExit("IranDozerCommandSet not found")
    block = m.group(0)
    if "13 = Command_ConstructIranAirfield" not in block:
        raise SystemExit("unexpected Iran dozer slot 13")
    if "14 = Command_DisarmMinesAtPosition" not in block:
        raise SystemExit("unexpected Iran dozer slot 14 (Clear Mines missing)")
    new_block = block.replace(
        "14 = Command_DisarmMinesAtPosition",
        "14 = Command_ConstructIran_HeavyAirBase",
        1,
    )
    text = text[: m.start()] + new_block + text[m.end() :]

    if "CommandSet Iran_HeavyAirBaseCommandSet" in text:
        raise SystemExit("Iran_HeavyAirBaseCommandSet already exists")

    # Insert after IranExpandedAirfieldCommandSet if present, else after IranDozer
    anchor = re.search(
        r"(?ms)^CommandSet\s+IranExpandedAirfieldCommandSet\s*\n.*?^End\s*$",
        text,
    )
    if not anchor:
        anchor = re.search(
            r"(?ms)^CommandSet\s+IranDozerCommandSet\s*\n.*?^End\s*$",
            text,
        )
    assert anchor
    insert_at = anchor.end()
    text = text[:insert_at] + "\n\n" + HEAVY_COMMANDSET + text[insert_at:]
    return text


def patch_radar(text: str) -> str:
    # RadarStation prereq must follow new fighter airbase production path
    new, n = re.subn(
        r"(?m)^(\s*Object\s*=\s*)IranAirfield(\s*)$",
        r"\1Iran_LargeAirBase\2",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"RadarStation IranAirfield prereq patch failed n={n}")
    return new


def count_object_defs(dmap: dict[str, bytes], obj: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(obj)}\s*$")
    n = 0
    for k, blob in dmap.items():
        if not k.lower().endswith(".ini"):
            continue
        n += len(pat.findall(blob.decode("latin1")))
    return n


def upload_zip(path: Path) -> str:
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{path}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if url.startswith("http"):
        return url
    servers = json.loads(
        subprocess.run(
            ["curl", "-s", "https://api.gofile.io/servers"],
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    )
    server = servers["data"]["servers"][0]["name"]
    up = subprocess.run(
        [
            "curl",
            "-s",
            "-F",
            f"file=@{path}",
            f"https://{server}.gofile.io/uploadFile",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    data = json.loads(up.stdout)
    return data["data"]["downloadPage"]


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert "Art\\W3D\\TheAirPort.W3D" in amap
    assert "Art\\W3D\\HXUSABigAirPort.W3D" in amap
    assert sha256(dmap[CSF_KEY]) == GOOD_CSF
    assert sha256(dmap[AC130_KEY]) == AC130_SHA
    freeze = {k: dmap[k] for k in FREEZE_KEYS if k in dmap}
    iran_aircraft_freeze = {
        k: v
        for k, v in dmap.items()
        if "Iranian Army" in k
        and any(p in k for p in ("Airforce", "AirForce", "Jet", "Helicopter"))
        and k.lower().endswith(".ini")
    }

    # Pre-audit
    dozer = dmap[
        "Data\\INI\\Object\\Specter\\Iranian Army\\Tracked\\Dozer.ini"
    ].decode("latin1")
    assert "IranVehicleDozer" in dozer
    assert "IranDozerCommandSet" in dozer
    iran_air = dmap[IRAN_AIR_KEY].decode("latin1")
    assert re.search(r"(?m)^Object\s+IranAirfield\s*$", iran_air)
    assert "IranExpandedAirfieldCommandSet" in iran_air
    assert "iran_airfield" in iran_air

    cs_before = dmap[CS_KEY].decode("latin1")
    cb_before = dmap[CB_KEY].decode("latin1")
    assert "14 = Command_DisarmMinesAtPosition" in cs_before
    assert "Object        = IranAirfield" in cb_before

    # Apply patches
    dmap[CB_KEY] = patch_command_button(cb_before).encode("latin1")
    dmap[CS_KEY] = patch_command_set(cs_before).encode("latin1")
    dmap[IRAN_RADAR_KEY] = patch_radar(
        dmap[IRAN_RADAR_KEY].decode("latin1")
    ).encode("latin1")

    large_blob = IRAN_LARGE_INI.encode("latin1")
    heavy_blob = IRAN_HEAVY_INI.encode("latin1")
    dmap[IRAN_LARGE_KEY] = large_blob
    dmap[IRAN_HEAVY_KEY] = heavy_blob

    # Source mirrors
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "Iran_LargeAirBase.ini").write_bytes(large_blob)
    (SRC_DIR / "Iran_HeavyAirBase.ini").write_bytes(heavy_blob)
    (SRC_DIR / "RadarStation.ini").write_bytes(dmap[IRAN_RADAR_KEY])

    # Rebuild via clean staging
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    for k, blob in freeze.items():
        assert staged[k] == blob, f"freeze mutated: {k}"
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, f"freeze broken after write: {k}"
    assert sha256(vmap[CSF_KEY]) == GOOD_CSF
    assert sha256(vmap[AC130_KEY]) == AC130_SHA

    # Verify Iran objects unique
    assert count_object_defs(vmap, "Iran_LargeAirBase") == 1
    assert count_object_defs(vmap, "Iran_HeavyAirBase") == 1
    assert count_object_defs(vmap, "IranAirfield") == 1  # retained, not builder-produced

    cs = vmap[CS_KEY].decode("latin1")
    cb = vmap[CB_KEY].decode("latin1")
    large = vmap[IRAN_LARGE_KEY].decode("latin1")
    heavy = vmap[IRAN_HEAVY_KEY].decode("latin1")

    # Dozer slots
    m = re.search(
        r"(?ms)^CommandSet\s+IranDozerCommandSet\s*\n(.*?)(?=^CommandSet\s+\S+\s*$|\Z)",
        cs,
    )
    assert m
    dozer_cs = m.group(0)
    assert "13 = Command_ConstructIranAirfield" in dozer_cs
    assert "14 = Command_ConstructIran_HeavyAirBase" in dozer_cs
    assert "Command_DisarmMinesAtPosition" not in dozer_cs

    # Buttons
    m = re.search(
        r"(?ms)^CommandButton\s+Command_ConstructIranAirfield\s*\n(.*?)(?=^CommandButton\s+\S+\s*$|\Z)",
        cb,
    )
    assert m and re.search(r"(?m)^\s*Object\s*=\s*Iran_LargeAirBase\s*$", m.group(0))
    assert not re.search(r"(?m)^\s*Object\s*=\s*IranAirfield\s*$", m.group(0))
    m = re.search(
        r"(?ms)^CommandButton\s+Command_ConstructIran_HeavyAirBase\s*\n(.*?)(?=^CommandButton\s+\S+\s*$|\Z)",
        cb,
    )
    assert m and re.search(r"(?m)^\s*Object\s*=\s*Iran_HeavyAirBase\s*$", m.group(0))

    # Heavy CS
    assert re.search(
        r"(?ms)^CommandSet\s+Iran_HeavyAirBaseCommandSet\s*\n"
        r"\s*13 = Command_SetRallyPoint\s*\n"
        r"\s*14 = Command_Sell\s*\n"
        r"End",
        cs,
    )

    # Large config
    assert "Model              = TheAirPort" in large
    assert "Model              = iran_airfield" not in large
    assert re.search(r"(?m)^\s*NumRows\s*=\s*4\s*$", large)
    assert re.search(r"(?m)^\s*NumCols\s*=\s*4\s*$", large)
    assert "CommandSet          = IranExpandedAirfieldCommandSet" in large
    assert "Side             = Iran" in large

    # Heavy config
    assert "Model              = HXUSABigAirPort" in heavy
    assert "HXNewBigAir" not in heavy
    assert "Model              = iran_airfield" not in heavy
    assert re.search(r"(?m)^\s*NumRows\s*=\s*3\s*$", heavy)
    assert re.search(r"(?m)^\s*NumCols\s*=\s*2\s*$", heavy)
    assert "CommandSet          = Iran_HeavyAirBaseCommandSet" in heavy

    # Radar prereq
    radar = vmap[IRAN_RADAR_KEY].decode("latin1")
    assert "Object = Iran_LargeAirBase" in radar
    assert "Object = IranAirfield" not in radar

    # Iran aircraft objects untouched
    for k, blob in iran_aircraft_freeze.items():
        assert vmap[k] == blob, f"Iran aircraft mutated: {k}"

    report = []
    report.append("IRAN DUAL AIRBASE CONVERSION = PASS")
    report.append("")
    report.append("Iran builder/dozer Object = IranVehicleDozer")
    report.append("Iran builder CommandSet = IranDozerCommandSet")
    report.append("")
    report.append("OLD AIRFIELD:")
    report.append("Old construct button = Command_ConstructIranAirfield")
    report.append("Old Object = IranAirfield")
    report.append("Old slot = 13")
    report.append("")
    report.append("NEW FIGHTER AIRBASE:")
    report.append("Object = Iran_LargeAirBase")
    report.append("W3D = TheAirPort")
    report.append("NumRows = 4")
    report.append("NumCols = 4")
    report.append("Capacity = 16")
    report.append(
        "Iran aircraft CommandSet preserved = YES (IranExpandedAirfieldCommandSet)"
    )
    report.append("")
    report.append("CLEAR MINES:")
    report.append("Old button = Command_DisarmMinesAtPosition")
    report.append("Old slot = 14")
    report.append("Removed from Iran builder = YES")
    report.append("")
    report.append("NEW HEAVY AIRBASE:")
    report.append("Object = Iran_HeavyAirBase")
    report.append("W3D = HXUSABigAirPort")
    report.append("NumRows = 3")
    report.append("NumCols = 2")
    report.append("Capacity = 6")
    report.append("3 left + 3 right = YES")
    report.append("Construct button = Command_ConstructIran_HeavyAirBase")
    report.append("Builder slot = 14")
    report.append(
        "Heavy CommandSet = Iran_HeavyAirBaseCommandSet (Rally/Sell only; no foreign aircraft)"
    )
    report.append("")
    report.append("Old Iran iran_airfield used by new fighter base = NO")
    report.append("Old HXNewBigAir used by new HeavyAirBase = NO")
    report.append(
        "IranAirfield Object retained in DATA (not builder-produced) = YES"
    )
    report.append(
        "RadarStation Prerequisite retargeted IranAirfield -> Iran_LargeAirBase = YES"
    )
    report.append("")
    report.append("Other factions changed = NO")
    report.append("Aircraft changed = NO")
    report.append("ART changed = NO")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append("")

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\nZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    url = upload_zip(OUT_ZIP)
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(text)
    print("Download =", url)


if __name__ == "__main__":
    main()
