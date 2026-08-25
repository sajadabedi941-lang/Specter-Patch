#!/usr/bin/env python3
"""Write Germany/Italy/UK air-force overlay INI (ASCII, LF)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_france_airforce_ini import FIGHTER_TAIL, fighter, w, wpn_set

ROOT = Path("/workspace/patch/Data")
INI = ROOT / "INI"


def aa(primary: str, secondary: str) -> str:
    return wpn_set(
        [
            f"Weapon              = PRIMARY    {primary}",
            f"Weapon              = SECONDARY  {secondary}",
            "PreferredAgainst    = PRIMARY    AIRCRAFT",
            "PreferredAgainst    = SECONDARY  AIRCRAFT",
        ]
    )


def strike(primary: str, secondary: str) -> str:
    return wpn_set(
        [
            f"Weapon              = PRIMARY    {primary}",
            f"Weapon              = SECONDARY  {secondary}",
        ]
    )


def jet(
    side: str,
    folder: str,
    file: str,
    obj: str,
    portrait: str,
    model: str,
    model_d: str,
    model_k: str,
    weapons: str,
    cmd: str,
    cost: int,
    time: float,
    hp: int,
    scale: float,
    vision: float,
    display: str,
    loco: str = "Snecma_M88_4E",
) -> dict:
    text = fighter(
        obj=obj,
        portrait=portrait,
        model=model,
        model_d=model_d,
        model_k=model_k,
        weapons=weapons,
        cmd=cmd,
        cost=cost,
        time=time,
        hp=hp,
        scale=scale,
        vision=vision,
        loco=loco,
        display=display,
    )
    text = text.replace("Side                = France", f"Side                = {side}")
    dest = ROOT / "INI/Object/Specter" / folder / "Airforce" / file
    w(dest, text)
    return {"obj": obj, "portrait": portrait, "file": dest, "kind": "fighter"}


def transport(side: str, folder: str, file: str, obj: str, portrait: str, model: str, model_d: str, model_k: str, display: str, cost: int, time: float, hp: int, scale: float) -> None:
    w(
        ROOT / "INI/Object/Specter" / folder / "Airforce" / file,
        f"""; SPECTER - {side} {display}. Donor {model}.
Object {obj}
Scale = {scale:.2f}

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {model}
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = {model}
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = {model_d}
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = RUBBLE
      Model = {model_k}
    End
  End

  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 300
  BuildCost = {cost}
  BuildTime = {time:.1f}
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = C17GlobalMasterCommandSet
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
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_02
    MaxHealth = {hp}.0
    InitialHealth = {hp}.0
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
    Mass = 700.0
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
  Locomotor = SET_NORMAL D30-F6_JetLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 12.0
  GeometryHeight = 12.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )


def awacs(side: str, folder: str, file: str, obj: str, portrait: str, model: str, anim: str, display: str, cost: int, vision: float) -> None:
    w(
        ROOT / "INI/Object/Specter" / folder / "Airforce" / file,
        f"""; SPECTER - {side} {display}. Donor {model}.
Object {obj}
Scale = 0.90

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {model}
      Animation = {anim}
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = {model}
      Animation = {anim}
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = {model}
      Animation = {anim}
      AnimationMode = LOOP
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = RUBBLE
      Model = {model}
    End
  End

  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = {vision:.1f}
  ShroudClearingRange = {vision + 100:.1f}
  BuildCost = {cost}
  BuildTime = 36.0
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = GenericTacticalBomberCommandSet
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
    Mass = 800.0
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
  Locomotor = SET_NORMAL D30-F6_JetLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 42.0
  GeometryMinorRadius = 14.0
  GeometryHeight = 12.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )


def drone(side: str, folder: str, file: str, obj: str, portrait: str, wpn: str, display: str) -> None:
    w(
        ROOT / "INI/Object/Specter" / folder / "Airforce" / file,
        f"""; SPECTER - {side} {display}. Donor AVReaper.
Object {obj}
Scale = 0.70

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = AVReaper
      WeaponLaunchBone = PRIMARY Weapon01
      WeaponLaunchBone = SECONDARY Weapon02
    End
    ConditionState = REALLYDAMAGED
      Model = AVReaper_D
    End
    ConditionState = RUBBLE
      Model = AVReaper_D
    End
  End

  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = 700.0
  ShroudClearingRange = 500.0
  BuildCost = 1800
  BuildTime = 16.0
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = GenericTacticalBomberCommandSet
  WeaponSet
    Conditions = None
    Weapon = PRIMARY {wpn}
    Weapon = SECONDARY {wpn}
  End
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceAttack = RaptorVoiceAttack
  SoundAmbient = RaptorAmbientLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = RaptorVoiceCreate
    VoiceGarrison = RaptorVoiceMove
  End
  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT
  Body = ActiveBody ModuleTag_02
    MaxHealth = 220.0
    InitialHealth = 220.0
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
    Mass = 80.0
  End
  Behavior = JetAIUpdate ModuleTag_09
    OutOfAmmoDamagePerSecond = 0%
    TakeoffDistForMaxLift = 0%
    TakeoffPause = 500
    MinHeight = 5
    ParkingOffset = 3
    NeedsRunway = No
    ReturnToBaseIdleTime = 10000
  End
  Locomotor = SET_NORMAL Snecma_M88_4E
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Geometry = Box
  GeometryIsSmall = Yes
  GeometryMajorRadius = 10.0
  GeometryMinorRadius = 5.0
  GeometryHeight = 3.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )


def attack_heli(side: str, folder: str, file: str, obj: str, portrait: str, model: str, model_d: str, model_k: str, anim: str, anim_d: str, display: str, cannon: str, atgm: str, rocket: str, cost: int, hp: int) -> None:
    w(
        ROOT / "INI/Object/Specter" / folder / "Rotary" / file,
        f"""; SPECTER - {side} {display}. Donor {model}.
Object {obj}
Scale = 0.88

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}
  UpgradeCameo1 = Upgrade_AmericaCountermeasures

  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {model}
      Animation = {anim}
      AnimationMode = LOOP
      WeaponFireFXBone = PRIMARY Weapon01
      WeaponLaunchBone = PRIMARY Weapon01
      WeaponFireFXBone = SECONDARY Weapon01
      WeaponLaunchBone = SECONDARY Weapon01
      WeaponFireFXBone = TERTIARY Weapon01
      WeaponLaunchBone = TERTIARY Weapon01
    End
    ConditionState = REALLYDAMAGED
      Model = {model_d}
      Animation = {anim_d}
      AnimationMode = LOOP
    End
    ConditionState = RUBBLE
      Model = {model_k}
    End
    OkToChangeModelColor = Yes
  End

  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = 280.0
  ShroudClearingRange = 180.0
  BuildCost = {cost}
  BuildTime = 13.0
  ExperienceValue = 50 50 100 150
  ExperienceRequired = 0 100 200 400
  IsTrainable = Yes
  CommandSet = GenericAttackHelicopterHoverCommandSet
  WeaponSet
    Conditions = None
    Weapon = PRIMARY {cannon}
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY {atgm}
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY {rocket}
    PreferredAgainst = TERTIARY INFANTRY STRUCTURE VEHICLE
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  VoiceSelect = ComancheVoiceSelect
  VoiceMove = ComancheVoiceMove
  VoiceAttack = ComancheVoiceAttack
  VoiceGuard = ComancheVoiceMove
  SoundAmbient = ComancheAmbientLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = ComancheVoiceCreate
    VoiceGarrison = ComancheVoiceMove
  End
  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT PRODUCED_AT_HELIPAD
  Body = ActiveBody ModuleTag_02
    MaxHealth = {hp}.0
    InitialHealth = {hp}.0
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = JetAIUpdate ModuleTag_07
    OutOfAmmoDamagePerSecond = 0%
    TakeoffDistForMaxLift = 0%
    TakeoffPause = 500
    MinHeight = 5
    ParkingOffset = 3
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    ReturnToBaseIdleTime = 10000
    AutoAcquireEnemiesWhenIdle = Yes
  End
  Locomotor = SET_NORMAL ComancheLocomotor
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = PhysicsBehavior ModuleTag_08
    Mass = 50.0
  End
  Geometry = Box
  GeometryIsSmall = Yes
  GeometryMajorRadius = 12.0
  GeometryMinorRadius = 6.0
  GeometryHeight = 8.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )


def util_heli(side: str, folder: str, file: str, obj: str, portrait: str, model: str, model_d: str, model_k: str, anim: str, display: str, cost: int, hp: int, slots: int, harvester: bool) -> None:
    kind = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD"
    if harvester:
        kind = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT HARVESTER SCORE PRODUCED_AT_HELIPAD"
    chinook_extra = ""
    if harvester:
        chinook_extra = """
    MaxBoxes = 6
    SupplyCenterActionDelay = 2900
    SupplyWarehouseActionDelay = 1200
    SupplyWarehouseScanDistance = 700
    SuppliesDepletedVoice = ChinookVoiceSuppliesDepleted"""
    w(
        ROOT / "INI/Object/Specter" / folder / "Rotary" / file,
        f"""; SPECTER - {side} {display}. Donor {model}.
Object {obj}
Scale = 0.90

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}

  Draw = W3DModelDraw ModuleTag_01
    ExtraPublicBone = RopeStart
    ExtraPublicBone = RopeEnd
    DefaultConditionState
      Model = {model}
      Animation = {anim}
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model = {model_d}
      Animation = {anim}
      AnimationMode = LOOP
    End
    ConditionState = RUBBLE
      Model = {model_k}
    End
    OkToChangeModelColor = Yes
  End

  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = 300.0
  ShroudClearingRange = 180.0
  BuildCost = {cost}
  BuildTime = 12.0
  ExperienceValue = 50 50 50 50
  IsTrainable = No
  CommandSet = AmericaVehicleChinookCommandSet
  ArmorSet
    Conditions = None
    Armor = ChinookArmor
    DamageFX = None
  End
  VoiceSelect = ChinookVoiceSelect
  VoiceMove = ChinookVoiceMove
  VoiceAttack = ChinookVoiceAttack
  SoundAmbient = Ch47AmbientLoop
  SoundAmbientRubble = NoSound
  SoundEnter = HumveeEnter
  SoundExit = HumveeExit
  UnitSpecificSounds
    VoiceCreate = ChinookVoiceCreate
    VoiceUnload = ChinookVoiceUnload
    VoiceCombatDrop = ChinookVoiceCombatDrop
    VoiceGarrison = ChinookVoiceMove
  End
  RadarPriority = UNIT
  KindOf = {kind}
  Body = ActiveBody ModuleTag_03
    MaxHealth = {hp}.0
    InitialHealth = {hp}.0
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = ChinookAIUpdate ModuleTag_07
    NumRopes = 2
    PerRopeDelayMin = 900
    PerRopeDelayMax = 1500
    RopeWidth = 0.5
    RopeColor = R:0 G:0 B:0
    RopeWobbleLen = 10
    RopeWobbleAmplitude = 0.25
    RopeWobbleRate = 180
    RopeFinalHeight = 10
    RappelSpeed = 30
    MinDropHeight = 40{chinook_extra}
  End
  Locomotor = SET_NORMAL ChinookLocomotor
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = TransportContain ModuleTag_08
    Slots = {slots}
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY VEHICLE
    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE
    ExitDelay = 100
    NumberOfExitPaths = 1
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 20.0
  GeometryMinorRadius = 8.0
  GeometryHeight = 9.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )


def helibase(side: str, folder: str, obj: str, portrait: str, cmd: str) -> None:
    src = (ROOT / "INI/Object/Specter/French Armed Forces/Buildings/France_HelicopterBase.ini").read_text(encoding="ascii")
    text = src.replace("France_HelicopterBase", obj)
    text = text.replace("SPEC_FranceHelicopterBase", portrait)
    text = text.replace("France_HelicopterBaseCommandSet", cmd)
    text = text.replace("Side             = France", f"Side             = {side}")
    text = text.replace("Object = FranceSupplyCenter", f"Object = {side}SupplyCenter")
    text = text.replace("France Helicopter Base", f"{side} Helicopter Base")
    w(ROOT / "INI/Object/Specter" / folder / "Buildings" / f"{obj}.ini", text)


def meteor(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 950.0
  PrimaryDamageRadius = 10.0
  SecondaryDamage = 10.0
  SecondaryDamageRadius = 20.0
  AttackRange = 1100
  MinimumAttackRange = 80.0
  DamageType = PENALTY
  DeathType = EXPLODED
  WeaponSpeed = 8000
  ProjectileObject = MeteorMissile_Object
  FireSound = RaptorJetMissileWeapon
  ProjectileDetonationFX = FX_LightAAMImpact
  RadiusDamageAffects = ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 720
  ClipSize = 6
  ClipReloadTime = 16000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = Yes
  AntiGround = No
  AntiAirborneInfantry = Yes
  ShowsAmmoPips = Yes
End
"""


def irist(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 720.0
  PrimaryDamageRadius = 8.0
  SecondaryDamage = 8.0
  SecondaryDamageRadius = 16.0
  AttackRange = 720.0
  MinimumAttackRange = 80.0
  AcceptableAimDelta = 360
  DamageType = PENALTY
  DeathType = EXPLODED
  WeaponSpeed = 8000
  ProjectileObject = France_MICA_Projectile
  FireSound = RaptorJetMissileWeapon
  ProjectileDetonationFX = FX_LightAAMImpact
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 700
  ClipSize = 4
  ClipReloadTime = 6000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = Yes
  AntiGround = No
  AntiAirborneInfantry = Yes
  ShowsAmmoPips = Yes
End
"""


def amraam(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 880.0
  PrimaryDamageRadius = 10.0
  SecondaryDamage = 10.0
  SecondaryDamageRadius = 18.0
  AttackRange = 980.0
  MinimumAttackRange = 80.0
  DamageType = PENALTY
  DeathType = EXPLODED
  WeaponSpeed = 8200
  ProjectileObject = MeteorMissile_Object
  FireSound = RaptorJetMissileWeapon
  ProjectileDetonationFX = FX_LightAAMImpact
  RadiusDamageAffects = ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 800
  ClipSize = 4
  ClipReloadTime = 14000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = Yes
  AntiGround = No
  AntiAirborneInfantry = Yes
  ShowsAmmoPips = Yes
End
"""


def aim9(name: str) -> str:
    return irist(name).replace(name, name, 1)


def cruise(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 1040.0
  PrimaryDamageRadius = 55.0
  SecondaryDamage = 45.0
  SecondaryDamageRadius = 100.0
  ScatterRadius = 18.0
  AttackRange = 1440.0
  MinimumAttackRange = 180.0
  PreAttackDelay = 2000
  PreAttackType = PER_ATTACK
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 450
  MinWeaponSpeed = 337
  FireFX = FX_MediumMissileIgnition
  ProjectileObject = France_SCALP_Projectile
  ProjectileDetonationFX = FX_HE_UnguidedMissileDetonation
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound = Grad_launch
  DelayBetweenShots = 4000
  ClipSize = 2
  ClipReloadTime = 42000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ALLIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End
"""


def brimstone(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 520.0
  PrimaryDamageRadius = 12.0
  SecondaryDamage = 20.0
  SecondaryDamageRadius = 22.0
  AttackRange = 780.0
  MinimumAttackRange = 80.0
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  WeaponSpeed = 4000
  ProjectileObject = AGM114L_MissileObject
  FireSound = HellfireMissileLaunch
  ProjectileDetonationFX = WeaponFX_GenericTandemWarheadExplosion
  RadiusDamageAffects = ENEMIES NEUTRALS
  DelayBetweenShots = 900
  ClipSize = 6
  ClipReloadTime = 8000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = STRUCTURES WALLS
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End
"""


def bomb(name: str, clip: int = 6) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 850.0
  PrimaryDamageRadius = 50.0
  SecondaryDamage = 180.0
  SecondaryDamageRadius = 80.0
  ScatterRadius = 38.0
  AttackRange = 680.0
  AcceptableAimDelta = 45
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 9999
  ProjectileObject = Fab-250
  FireFX = FX_AuroraBombLaunch
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 400
  ClipSize = {clip}
  ClipReloadTime = 28000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
  AntiGround = Yes
  AntiAirborneVehicle = No
  LeechRangeWeapon = Yes
End
"""


def paveway(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 980.0
  PrimaryDamageRadius = 40.0
  SecondaryDamage = 80.0
  SecondaryDamageRadius = 70.0
  AttackRange = 900.0
  AcceptableAimDelta = 20
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  WeaponSpeed = 9999
  ProjectileObject = Fab-250
  FireFX = FX_AuroraBombLaunch
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 600
  ClipSize = 4
  ClipReloadTime = 24000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
  AntiGround = Yes
  AntiAirborneVehicle = No
  LeechRangeWeapon = Yes
End
"""


def heli_cannon(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 50.0
  PrimaryDamageRadius = 9.0
  ScatterRadiusVsInfantry = 55.0
  ScatterRadius = 17.0
  AttackRange = 420.0
  MinimumAttackRange = 20.0
  DamageType = COMANCHE_VULCAN
  DeathType = EXTRA_4
  WeaponSpeed = 9999.0
  ProjectileObject = 30mm_API-T_Projectile
  ProjectileDetonationFX = WeaponFX_30mm_API-T_Tracer
  FireSound = 30mm_M230ChainGunFire
  FireFX = WeaponFX_HeavyCalibarChainGunsFire_Heli
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots = 120
  ClipSize = 20
  ClipReloadTime = 1500
  AntiAirborneVehicle = No
  AntiAirborneInfantry = Yes
  AntiGround = Yes
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
End
"""


def heli_atgm(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 635.0
  PrimaryDamageRadius = 10.0
  SecondaryDamage = 10.0
  SecondaryDamageRadius = 20.0
  AttackRange = 750
  MinimumAttackRange = 80.0
  AcceptableAimDelta = 33
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  MissileCallsOnDie = Yes
  WeaponSpeed = 8000
  ProjectileObject = AGM114L_MissileObject
  FireSound = HellfireMissileLaunch
  ProjectileDetonationFX = WeaponFX_GenericTandemWarheadExplosion
  RadiusDamageAffects = ENEMIES NEUTRALS
  DelayBetweenShots = 1620
  ClipSize = 8
  ClipReloadTime = 6000
  ProjectileCollidesWith = STRUCTURES WALLS
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End
"""


def heli_rocket(name: str) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 0.1
  PrimaryDamageRadius = 0.1
  ScatterRadiusVsInfantry = 111.0
  ScatterRadius = 30.0
  AttackRange = 450
  MinimumAttackRange = 80.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  ProjectileObject = GenericUnguidedRockets
  ProjectileExhaust = UnguidedRocketTrail
  RadiusDamageAffects = ENEMIES NEUTRALS
  DelayBetweenShots = Min:0 Max:600
  ClipSize = 5
  AutoReloadsClip = Yes
  ClipReloadTime = 3000
  FireSound = Unguided_Rockets_Fire
  FireFX = WeaponFX_GenericAirLaunchedMissileIgnition
  ProjectileDetonationOCL = OCL_PM36DetonationObject
  ProjectileDetonationFX = FX_UnguidedRocketExplosion
  ProjectileCollidesWith = ENEMIES STRUCTURES
  AntiAirborneVehicle = No
  AntiGround = Yes
End
"""


def btn(name: str, obj: str, img: str, label: str, tip: str, dozer: bool = False) -> str:
    cmd = "DOZER_CONSTRUCT" if dozer else "UNIT_BUILD"
    return f"""CommandButton {name}
  Command          = {cmd}
  Object           = {obj}
  TextLabel        = {label}
  ButtonImage      = {img}
  ButtonBorderType = BUILD
  DescriptLabel    = {tip}
End
"""


def mapped(name: str) -> str:
    return f"""MappedImage {name}
  Texture = {name}.tga
  TextureWidth = 150
  TextureHeight = 113
  Coords = Left:0 Top:0 Right:150 Bottom:113
  Status = NONE
End
"""


def cs_line(slots: list[str]) -> str:
    lines = []
    for i, b in enumerate(slots, 1):
        lines.append(f"  {i}  = {b}")
    lines.append("  13 = Command_SetRallyPoint")
    lines.append("  14 = Command_Sell")
    return "\n".join(lines)


def main() -> None:
    # --- Germany fighters ---
    g_f = [
        ("GermanyJetTyphoonT4.ini", "GermanyJetTyphoonT4", "SPEC_GermanyTyphoonT4", "LSFEUEF2000", "LSFEUEF2000d", "LSFEUEF2000k", aa("Germany_Weapon_Meteor", "Germany_Weapon_IRIST"), "F22A_AA_CommandSet", 2800, 16.0, 540, 0.95, 700.0, "Eurofighter Typhoon Tranche 4"),
        ("GermanyJetTyphoonECR.ini", "GermanyJetTyphoonECR", "SPEC_GermanyTyphoonECR", "LSFEUEF2000", "LSFEUEF2000d", "LSFEUEF2000k", strike("Germany_Weapon_Taurus", "Germany_Weapon_IRIST"), "GenericTacticalBomberCommandSet", 2900, 17.0, 530, 0.95, 640.0, "Eurofighter Typhoon ECR"),
        ("GermanyJetTornadoIDS.ini", "GermanyJetTornadoIDS", "SPEC_GermanyTornadoIDS", "LSFTornado", "LSFTornadod", "LSFTornadok", strike("Germany_Weapon_Bomb", "Germany_Weapon_Paveway"), "GenericTacticalBomberCommandSet", 2200, 15.0, 480, 0.92, 560.0, "Tornado IDS"),
        ("GermanyJetTornadoECR.ini", "GermanyJetTornadoECR", "SPEC_GermanyTornadoECR", "LSFTornado", "LSFTornadod", "LSFTornadok", strike("Germany_Weapon_Taurus", "Germany_Weapon_AIM9"), "GenericTacticalBomberCommandSet", 2300, 15.5, 470, 0.92, 580.0, "Tornado ECR"),
        ("GermanyJetF35A.ini", "GermanyJetF35A", "SPEC_GermanyF35A", "US_F35A", "US_F35A", "US_F35A", strike("Germany_Weapon_JDAM", "Germany_Weapon_AMRAAM"), "GenericTacticalBomberCommandSet", 3200, 18.0, 560, 0.92, 680.0, "F-35A"),
        ("GermanyJetMiG29G.ini", "GermanyJetMiG29G", "SPEC_GermanyMiG29G", "LSFruMiG29", "LSFruMiG29d", "LSFruMiG29k", aa("Germany_Weapon_AMRAAM", "Germany_Weapon_AIM9"), "F22A_AA_CommandSet", 1600, 13.0, 430, 0.90, 540.0, "MiG-29G"),
        ("GermanyJetAlphaJet.ini", "GermanyJetAlphaJet", "SPEC_GermanyAlphaJet", "AVHawk", "AVHawk_D", "AVHawk_D", strike("Germany_Weapon_Bomb", "Germany_Weapon_AIM9"), "GenericTacticalBomberCommandSet", 1100, 10.0, 320, 0.80, 420.0, "Alpha Jet"),
        ("GermanyJetF4F.ini", "GermanyJetF4F", "SPEC_GermanyF4F", "JPF4", "JPF4D", "JPF4K", aa("Germany_Weapon_AMRAAM", "Germany_Weapon_AIM9"), "F22A_AA_CommandSet", 1400, 12.0, 420, 0.90, 520.0, "F-4F Phantom"),
        ("GermanyJetTornadoADV.ini", "GermanyJetTornadoADV", "SPEC_GermanyTornadoADV", "LSFTornado", "LSFTornadod", "LSFTornadok", aa("Germany_Weapon_Meteor", "Germany_Weapon_AIM9"), "F22A_AA_CommandSet", 2100, 14.5, 460, 0.92, 600.0, "Tornado ADV"),
        ("GermanyJetMako.ini", "GermanyJetMako", "SPEC_GermanyMako", "LSFF16", "LSFF16d", "LSFF16k", strike("Germany_Weapon_JDAM", "Germany_Weapon_IRIST"), "GenericTacticalBomberCommandSet", 1700, 13.0, 400, 0.88, 500.0, "Mako"),
    ]
    g_btns = []
    for spec in g_f:
        jet("Germany", "German Armed Forces", *spec)
        obj = spec[1]
        g_btns.append((f"Command_Construct{obj}", obj, spec[2], f"CONTROLBAR:Construct{obj}", f"CONTROLBAR:ToolTip{obj}"))

    transport("Germany", "German Armed Forces", "GermanyJetA400M.ini", "GermanyJetA400M", "SPEC_GermanyA400M", "IUAC17HXNew", "IUAC17HXNew", "IUAC17HXNew", "A400M Atlas", 2800, 30.0, 800, 1.05)
    transport("Germany", "German Armed Forces", "GermanyJetC130J.ini", "GermanyJetC130J", "SPEC_GermanyC130J", "LSFUSAC130", "LSFUSAC130d", "LSFUSAC130k", "C-130J", 2400, 28.0, 700, 1.00)
    awacs("Germany", "German Armed Forces", "GermanyAircraftE3.ini", "GermanyAircraftE3", "SPEC_GermanyE3", "E3", "E3.E3", "E-3 AWACS", 4200, 1100.0)
    drone("Germany", "German Armed Forces", "GermanyDroneHeronTP.ini", "GermanyDroneHeronTP", "SPEC_GermanyHeronTP", "Germany_Weapon_Brimstone", "Heron TP")
    g_heavy = [
        ("Command_ConstructGermanyJetA400M", "GermanyJetA400M", "SPEC_GermanyA400M"),
        ("Command_ConstructGermanyJetC130J", "GermanyJetC130J", "SPEC_GermanyC130J"),
        ("Command_ConstructGermanyAircraftE3", "GermanyAircraftE3", "SPEC_GermanyE3"),
        ("Command_ConstructGermanyDroneHeronTP", "GermanyDroneHeronTP", "SPEC_GermanyHeronTP"),
    ]

    attack_heli("Germany", "German Armed Forces", "GermanyHelicopterTigerUHT.ini", "GermanyHelicopterTigerUHT", "SPEC_GermanyTigerUHT", "LSFGETiger", "LSFGETigerd", "LSFGETigerk", "LSFGETIGER.LSFGETIGER", "LSFGETIGERD.LSFGETIGERD", "Tiger UHT", "Germany_Weapon_HeliCannon", "Germany_Weapon_HeliATGM", "Germany_Weapon_HeliRocket", 1700, 280)
    util_heli("Germany", "German Armed Forces", "GermanyHelicopterNH90.ini", "GermanyHelicopterNH90", "SPEC_GermanyNH90", "LSFGENH90", "LSFGENH90", "LSFGENH90", "LSFGENH90.LSFGENH90", "NH90", 1600, 320, 8, True)
    util_heli("Germany", "German Armed Forces", "GermanyHelicopterCH53.ini", "GermanyHelicopterCH53", "SPEC_GermanyCH53", "LSFRUMi171", "LSFRUMi171d", "LSFRUMi171k", "LSFRUMI171.LSFRUMI171", "CH-53", 2100, 450, 14, False)
    util_heli("Germany", "German Armed Forces", "GermanyHelicopterH145M.ini", "GermanyHelicopterH145M", "SPEC_GermanyH145M", "LSFFenneck", "LSFFenneckd", "LSFFenneckk", "LSFFENNECK.LSFFENNECK", "H145M", 1200, 240, 6, False)
    g_heli = [
        ("Command_ConstructGermanyHelicopterTigerUHT", "GermanyHelicopterTigerUHT", "SPEC_GermanyTigerUHT"),
        ("Command_ConstructGermanyHelicopterNH90", "GermanyHelicopterNH90", "SPEC_GermanyNH90"),
        ("Command_ConstructGermanyHelicopterCH53", "GermanyHelicopterCH53", "SPEC_GermanyCH53"),
        ("Command_ConstructGermanyHelicopterH145M", "GermanyHelicopterH145M", "SPEC_GermanyH145M"),
    ]
    helibase("Germany", "German Armed Forces", "Germany_HelicopterBase", "SPEC_GermanyHelicopterBase", "Germany_HelicopterBaseCommandSet")

    # --- Italy ---
    i_f = [
        ("ItalyJetTyphoon.ini", "ItalyJetTyphoon", "SPEC_ItalyTyphoon", "LSFEUEF2000", "LSFEUEF2000d", "LSFEUEF2000k", aa("Italy_Weapon_Meteor", "Italy_Weapon_IRIST"), "F22A_AA_CommandSet", 2800, 16.0, 540, 0.95, 700.0, "Eurofighter Typhoon"),
        ("ItalyJetF35A.ini", "ItalyJetF35A", "SPEC_ItalyF35A", "US_F35A", "US_F35A", "US_F35A", strike("Italy_Weapon_JDAM", "Italy_Weapon_AMRAAM"), "GenericTacticalBomberCommandSet", 3200, 18.0, 560, 0.92, 680.0, "F-35A"),
        ("ItalyJetF35B.ini", "ItalyJetF35B", "SPEC_ItalyF35B", "US_F35A", "US_F35A", "US_F35A", strike("Italy_Weapon_JDAM", "Italy_Weapon_AIM9"), "GenericTacticalBomberCommandSet", 3300, 18.5, 550, 0.92, 660.0, "F-35B"),
        ("ItalyJetAMX.ini", "ItalyJetAMX", "SPEC_ItalyAMX", "LSFMirage5", "LSFMirage5d", "LSFMirage5k", strike("Italy_Weapon_Bomb", "Italy_Weapon_Paveway"), "GenericTacticalBomberCommandSet", 1400, 12.0, 380, 0.85, 480.0, "AMX"),
        ("ItalyJetTornadoIDS.ini", "ItalyJetTornadoIDS", "SPEC_ItalyTornadoIDS", "LSFTornado", "LSFTornadod", "LSFTornadok", strike("Italy_Weapon_StormShadow", "Italy_Weapon_Bomb"), "GenericTacticalBomberCommandSet", 2200, 15.0, 480, 0.92, 560.0, "Tornado IDS"),
        ("ItalyJetTornadoECR.ini", "ItalyJetTornadoECR", "SPEC_ItalyTornadoECR", "LSFTornado", "LSFTornadod", "LSFTornadok", strike("Italy_Weapon_StormShadow", "Italy_Weapon_AIM9"), "GenericTacticalBomberCommandSet", 2300, 15.5, 470, 0.92, 580.0, "Tornado ECR"),
        ("ItalyJetHarrierII.ini", "ItalyJetHarrierII", "SPEC_ItalyHarrierII", "LSFAV8B", "LSFAV8Bd", "LSFAV8Bk", strike("Italy_Weapon_Paveway", "Italy_Weapon_AIM9"), "GenericTacticalBomberCommandSet", 1800, 14.0, 400, 0.88, 500.0, "Harrier II"),
        ("ItalyJetF16.ini", "ItalyJetF16", "SPEC_ItalyF16", "LSFF16", "LSFF16d", "LSFF16k", aa("Italy_Weapon_AMRAAM", "Italy_Weapon_AIM9"), "F22A_AA_CommandSet", 1900, 14.0, 440, 0.88, 560.0, "F-16"),
        ("ItalyJetM346FA.ini", "ItalyJetM346FA", "SPEC_ItalyM346FA", "AVHawk", "AVHawk_D", "AVHawk_D", strike("Italy_Weapon_JDAM", "Italy_Weapon_IRIST"), "GenericTacticalBomberCommandSet", 1500, 12.0, 360, 0.82, 480.0, "M-346FA"),
        ("ItalyJetMB339.ini", "ItalyJetMB339", "SPEC_ItalyMB339", "AVHawk", "AVHawk_D", "AVHawk_D", strike("Italy_Weapon_Bomb", "Italy_Weapon_AIM9"), "GenericTacticalBomberCommandSet", 1000, 9.5, 300, 0.78, 400.0, "MB-339"),
    ]
    i_btns = []
    for spec in i_f:
        jet("Italy", "Italian Armed Forces", *spec)
        obj = spec[1]
        i_btns.append((f"Command_Construct{obj}", obj, spec[2], f"CONTROLBAR:Construct{obj}", f"CONTROLBAR:ToolTip{obj}"))

    transport("Italy", "Italian Armed Forces", "ItalyJetC130J.ini", "ItalyJetC130J", "SPEC_ItalyC130J", "LSFUSAC130", "LSFUSAC130d", "LSFUSAC130k", "C-130J", 2400, 28.0, 700, 1.00)
    transport("Italy", "Italian Armed Forces", "ItalyJetC27J.ini", "ItalyJetC27J", "SPEC_ItalyC27J", "LSFUSAC130", "LSFUSAC130d", "LSFUSAC130k", "C-27J Spartan", 2000, 22.0, 560, 0.85)
    awacs("Italy", "Italian Armed Forces", "ItalyAircraftG550CAEW.ini", "ItalyAircraftG550CAEW", "SPEC_ItalyG550CAEW", "KVE737", "KVE737.KVE737", "G550 CAEW", 4000, 1000.0)
    drone("Italy", "Italian Armed Forces", "ItalyDroneMQ9.ini", "ItalyDroneMQ9", "SPEC_ItalyMQ9", "Italy_Weapon_Brimstone", "MQ-9")
    i_heavy = [
        ("Command_ConstructItalyJetC130J", "ItalyJetC130J", "SPEC_ItalyC130J"),
        ("Command_ConstructItalyJetC27J", "ItalyJetC27J", "SPEC_ItalyC27J"),
        ("Command_ConstructItalyAircraftG550CAEW", "ItalyAircraftG550CAEW", "SPEC_ItalyG550CAEW"),
        ("Command_ConstructItalyDroneMQ9", "ItalyDroneMQ9", "SPEC_ItalyMQ9"),
    ]
    attack_heli("Italy", "Italian Armed Forces", "ItalyHelicopterAW249.ini", "ItalyHelicopterAW249", "SPEC_ItalyAW249", "LSFAH64D", "LSFAH64Dd", "LSFAH64Dd", "LSFAH64D.LSFAH64D", "LSFAH64DD.LSFAH64DD", "AW249", "Italy_Weapon_HeliCannon", "Italy_Weapon_HeliATGM", "Italy_Weapon_HeliRocket", 1900, 300)
    attack_heli("Italy", "Italian Armed Forces", "ItalyHelicopterA129.ini", "ItalyHelicopterA129", "SPEC_ItalyA129", "LSFGETiger", "LSFGETigerd", "LSFGETigerk", "LSFGETIGER.LSFGETIGER", "LSFGETIGERD.LSFGETIGERD", "A129 Mangusta", "Italy_Weapon_HeliCannon", "Italy_Weapon_HeliATGM", "Italy_Weapon_HeliRocket", 1600, 260)
    util_heli("Italy", "Italian Armed Forces", "ItalyHelicopterNH90.ini", "ItalyHelicopterNH90", "SPEC_ItalyNH90", "LSFGENH90", "LSFGENH90", "LSFGENH90", "LSFGENH90.LSFGENH90", "NH90", 1600, 320, 8, True)
    util_heli("Italy", "Italian Armed Forces", "ItalyHelicopterAW101.ini", "ItalyHelicopterAW101", "SPEC_ItalyAW101", "LSFGENH90", "LSFGENH90", "LSFGENH90", "LSFGENH90.LSFGENH90", "AW101", 2000, 400, 12, False)
    util_heli("Italy", "Italian Armed Forces", "ItalyHelicopterAW139.ini", "ItalyHelicopterAW139", "SPEC_ItalyAW139", "LSFRUMi171", "LSFRUMi171d", "LSFRUMi171k", "LSFRUMI171.LSFRUMI171", "AW139", 1500, 300, 8, False)
    i_heli = [
        ("Command_ConstructItalyHelicopterAW249", "ItalyHelicopterAW249", "SPEC_ItalyAW249"),
        ("Command_ConstructItalyHelicopterA129", "ItalyHelicopterA129", "SPEC_ItalyA129"),
        ("Command_ConstructItalyHelicopterNH90", "ItalyHelicopterNH90", "SPEC_ItalyNH90"),
        ("Command_ConstructItalyHelicopterAW101", "ItalyHelicopterAW101", "SPEC_ItalyAW101"),
        ("Command_ConstructItalyHelicopterAW139", "ItalyHelicopterAW139", "SPEC_ItalyAW139"),
    ]
    helibase("Italy", "Italian Armed Forces", "Italy_HelicopterBase", "SPEC_ItalyHelicopterBase", "Italy_HelicopterBaseCommandSet")

    # --- UK ---
    b_f = [
        ("BritainJetF35B.ini", "BritainJetF35B", "SPEC_BritainF35B", "US_F35A", "US_F35A", "US_F35A", strike("Britain_Weapon_Paveway", "Britain_Weapon_AMRAAM"), "GenericTacticalBomberCommandSet", 3300, 18.5, 560, 0.92, 680.0, "F-35B"),
        ("BritainJetTyphoonFGR4.ini", "BritainJetTyphoonFGR4", "SPEC_BritainTyphoonFGR4", "LSFEUEF2000", "LSFEUEF2000d", "LSFEUEF2000k", strike("Britain_Weapon_Meteor", "Britain_Weapon_Brimstone"), "GenericTacticalBomberCommandSet", 2900, 17.0, 550, 0.95, 700.0, "Eurofighter Typhoon FGR4"),
        ("BritainJetTyphoonT3.ini", "BritainJetTyphoonT3", "SPEC_BritainTyphoonT3", "LSFEUEF2000", "LSFEUEF2000d", "LSFEUEF2000k", aa("Britain_Weapon_Meteor", "Britain_Weapon_ASRAAM"), "F22A_AA_CommandSet", 2700, 16.0, 530, 0.95, 680.0, "Typhoon Tranche 3"),
        ("BritainJetHarrierGR9.ini", "BritainJetHarrierGR9", "SPEC_BritainHarrierGR9", "LSFAV8B", "LSFAV8Bd", "LSFAV8Bk", strike("Britain_Weapon_Paveway", "Britain_Weapon_Brimstone"), "GenericTacticalBomberCommandSet", 1900, 14.0, 410, 0.88, 520.0, "Harrier GR9"),
        ("BritainJetTornadoGR4.ini", "BritainJetTornadoGR4", "SPEC_BritainTornadoGR4", "LSFTornado", "LSFTornadod", "LSFTornadok", strike("Britain_Weapon_StormShadow", "Britain_Weapon_Paveway"), "GenericTacticalBomberCommandSet", 2300, 15.5, 490, 0.92, 580.0, "Tornado GR4"),
        ("BritainJetJaguarGR3.ini", "BritainJetJaguarGR3", "SPEC_BritainJaguarGR3", "LSFTornado", "LSFTornadod", "LSFTornadok", strike("Britain_Weapon_Bomb", "Britain_Weapon_Paveway"), "GenericTacticalBomberCommandSet", 1500, 12.5, 380, 0.86, 480.0, "Jaguar GR3"),
        ("BritainJetSeaHarrierFA2.ini", "BritainJetSeaHarrierFA2", "SPEC_BritainSeaHarrierFA2", "LSFAV8B", "LSFAV8Bd", "LSFAV8Bk", aa("Britain_Weapon_AMRAAM", "Britain_Weapon_ASRAAM"), "F22A_AA_CommandSet", 1700, 13.5, 390, 0.88, 540.0, "Sea Harrier FA2"),
        ("BritainJetPhantomFG1.ini", "BritainJetPhantomFG1", "SPEC_BritainPhantomFG1", "JPF4", "JPF4D", "JPF4K", aa("Britain_Weapon_AMRAAM", "Britain_Weapon_ASRAAM"), "F22A_AA_CommandSet", 1500, 12.5, 430, 0.90, 530.0, "Phantom FG1"),
        ("BritainJetLightningF6.ini", "BritainJetLightningF6", "SPEC_BritainLightningF6", "LSFMirage3", "LSFMirage3d", "LSFMirage3k", aa("Britain_Weapon_AMRAAM", "Britain_Weapon_ASRAAM"), "F22A_AA_CommandSet", 1300, 11.0, 360, 0.85, 500.0, "Lightning F6"),
        ("BritainJetHawk200.ini", "BritainJetHawk200", "SPEC_BritainHawk200", "AVHawk", "AVHawk_D", "AVHawk_D", strike("Britain_Weapon_Bomb", "Britain_Weapon_ASRAAM"), "GenericTacticalBomberCommandSet", 1100, 10.0, 310, 0.80, 420.0, "Hawk 200"),
    ]
    b_btns = []
    for spec in b_f:
        jet("Britain", "British Armed Forces", *spec)
        obj = spec[1]
        b_btns.append((f"Command_Construct{obj}", obj, spec[2], f"CONTROLBAR:Construct{obj}", f"CONTROLBAR:ToolTip{obj}"))

    transport("Britain", "British Armed Forces", "BritainJetA400M.ini", "BritainJetA400M", "SPEC_BritainA400M", "IUAC17HXNew", "IUAC17HXNew", "IUAC17HXNew", "A400M", 2800, 30.0, 800, 1.05)
    transport("Britain", "British Armed Forces", "BritainJetC17.ini", "BritainJetC17", "SPEC_BritainC17", "IUAC17HXNew", "IUAC17HXNew", "IUAC17HXNew", "C-17", 3000, 32.0, 900, 1.10)
    awacs("Britain", "British Armed Forces", "BritainAircraftE7.ini", "BritainAircraftE7", "SPEC_BritainE7", "KVE737", "KVE737.KVE737", "E-7 Wedgetail", 4300, 1150.0)
    drone("Britain", "British Armed Forces", "BritainDroneMQ9.ini", "BritainDroneMQ9", "SPEC_BritainMQ9", "Britain_Weapon_Brimstone", "MQ-9 Reaper")
    jet("Britain", "British Armed Forces", "BritainBomberVulcan.ini", "BritainBomberVulcan", "SPEC_BritainVulcan", "LSFUSAB52", "LSFUSAB52d", "LSFUSAB52k", strike("Britain_Weapon_CarpetBomb", "Britain_Weapon_StormShadow"), "GenericTacticalBomberCommandSet", 3800, 28.0, 900, 1.15, 500.0, "Vulcan")
    b_heavy = [
        ("Command_ConstructBritainJetA400M", "BritainJetA400M", "SPEC_BritainA400M"),
        ("Command_ConstructBritainJetC17", "BritainJetC17", "SPEC_BritainC17"),
        ("Command_ConstructBritainAircraftE7", "BritainAircraftE7", "SPEC_BritainE7"),
        ("Command_ConstructBritainDroneMQ9", "BritainDroneMQ9", "SPEC_BritainMQ9"),
        ("Command_ConstructBritainBomberVulcan", "BritainBomberVulcan", "SPEC_BritainVulcan"),
    ]
    attack_heli("Britain", "British Armed Forces", "BritainHelicopterApache.ini", "BritainHelicopterApache", "SPEC_BritainApache", "LSFAH64D", "LSFAH64Dd", "LSFAH64Dd", "LSFAH64D.LSFAH64D", "LSFAH64DD.LSFAH64DD", "Apache AH-64E", "Britain_Weapon_HeliCannon", "Britain_Weapon_HeliATGM", "Britain_Weapon_HeliRocket", 1800, 300)
    util_heli("Britain", "British Armed Forces", "BritainHelicopterChinook.ini", "BritainHelicopterChinook", "SPEC_BritainChinook", "US_CH47F", "US_CH47F", "US_CH47F", "US_CH47F.US_CH47F", "Chinook", 2000, 420, 14, True)
    util_heli("Britain", "British Armed Forces", "BritainHelicopterMerlin.ini", "BritainHelicopterMerlin", "SPEC_BritainMerlin", "LSFGENH90", "LSFGENH90", "LSFGENH90", "LSFGENH90.LSFGENH90", "Merlin", 1900, 380, 12, False)
    util_heli("Britain", "British Armed Forces", "BritainHelicopterWildcat.ini", "BritainHelicopterWildcat", "SPEC_BritainWildcat", "LSFLynxAHMK", "LSFLynxAHMK", "LSFLynxAHMK", "LSFLYNXAHMK.LSFLYNXAHMK", "Wildcat", 1400, 250, 6, False)
    util_heli("Britain", "British Armed Forces", "BritainHelicopterPuma.ini", "BritainHelicopterPuma", "SPEC_BritainPuma", "LSFRUMi171", "LSFRUMi171d", "LSFRUMi171k", "LSFRUMI171.LSFRUMI171", "Puma", 1600, 320, 10, False)
    b_heli = [
        ("Command_ConstructBritainHelicopterApache", "BritainHelicopterApache", "SPEC_BritainApache"),
        ("Command_ConstructBritainHelicopterChinook", "BritainHelicopterChinook", "SPEC_BritainChinook"),
        ("Command_ConstructBritainHelicopterMerlin", "BritainHelicopterMerlin", "SPEC_BritainMerlin"),
        ("Command_ConstructBritainHelicopterWildcat", "BritainHelicopterWildcat", "SPEC_BritainWildcat"),
        ("Command_ConstructBritainHelicopterPuma", "BritainHelicopterPuma", "SPEC_BritainPuma"),
    ]
    helibase("Britain", "British Armed Forces", "Britain_HelicopterBase", "SPEC_BritainHelicopterBase", "Britain_HelicopterBaseCommandSet")

    # weapons
    wpns = []
    for prefix in ("Germany", "Italy", "Britain"):
        wpns.append(meteor(f"{prefix}_Weapon_Meteor"))
        wpns.append(irist(f"{prefix}_Weapon_IRIST" if prefix != "Britain" else f"{prefix}_Weapon_ASRAAM"))
        if prefix != "Britain":
            wpns.append(irist(f"{prefix}_Weapon_AIM9"))
        wpns.append(amraam(f"{prefix}_Weapon_AMRAAM"))
        wpns.append(cruise(f"{prefix}_Weapon_Taurus" if prefix == "Germany" else f"{prefix}_Weapon_StormShadow"))
        wpns.append(brimstone(f"{prefix}_Weapon_Brimstone"))
        wpns.append(paveway(f"{prefix}_Weapon_Paveway"))
        wpns.append(paveway(f"{prefix}_Weapon_JDAM"))
        wpns.append(bomb(f"{prefix}_Weapon_Bomb", 6 if prefix != "Britain" else 8))
        wpns.append(heli_cannon(f"{prefix}_Weapon_HeliCannon"))
        wpns.append(heli_atgm(f"{prefix}_Weapon_HeliATGM"))
        wpns.append(heli_rocket(f"{prefix}_Weapon_HeliRocket"))
    wpns.append(bomb("Britain_Weapon_CarpetBomb", 12))
    # Britain IRIST alias not created; Typhoon FGR4 uses Meteor+Brimstone
    w(INI / "Weapon_EuropeAirforce.ini", "; SPECTER - Germany/Italy/UK unique air weapons. Packed projectiles only.\n\n" + "\n".join(wpns))

    # buttons
    buttons = ["; SPECTER - Europe air force construct buttons.\n"]
    portraits = ["; Unique Europe airbase portraits.\n"]
    csf = {}
    all_unit_btns = []

    def add_units(pairs, extra_tips):
        for name, obj, img in pairs:
            label = f"CONTROLBAR:Construct{obj}"
            tip = f"CONTROLBAR:ToolTip{obj}"
            buttons.append(btn(name, obj, img, label, tip))
            portraits.append(mapped(img))
            all_unit_btns.append(name)
            title = extra_tips.get(obj, obj)
            csf[label] = title
            csf[tip] = title
            csf[f"OBJECT:{obj}"] = title

    g_names = {
        "GermanyJetTyphoonT4": "Eurofighter Typhoon Tranche 4",
        "GermanyJetTyphoonECR": "Eurofighter Typhoon ECR",
        "GermanyJetTornadoIDS": "Tornado IDS",
        "GermanyJetTornadoECR": "Tornado ECR",
        "GermanyJetF35A": "F-35A",
        "GermanyJetMiG29G": "MiG-29G",
        "GermanyJetAlphaJet": "Alpha Jet",
        "GermanyJetF4F": "F-4F Phantom",
        "GermanyJetTornadoADV": "Tornado ADV",
        "GermanyJetMako": "Mako",
        "GermanyJetA400M": "A400M Atlas",
        "GermanyJetC130J": "C-130J",
        "GermanyAircraftE3": "E-3 AWACS",
        "GermanyDroneHeronTP": "Heron TP",
        "GermanyHelicopterTigerUHT": "Tiger UHT",
        "GermanyHelicopterNH90": "NH90",
        "GermanyHelicopterCH53": "CH-53",
        "GermanyHelicopterH145M": "H145M",
    }
    i_names = {
        "ItalyJetTyphoon": "Eurofighter Typhoon",
        "ItalyJetF35A": "F-35A",
        "ItalyJetF35B": "F-35B",
        "ItalyJetAMX": "AMX",
        "ItalyJetTornadoIDS": "Tornado IDS",
        "ItalyJetTornadoECR": "Tornado ECR",
        "ItalyJetHarrierII": "Harrier II",
        "ItalyJetF16": "F-16",
        "ItalyJetM346FA": "M-346FA",
        "ItalyJetMB339": "MB-339",
        "ItalyJetC130J": "C-130J",
        "ItalyJetC27J": "C-27J Spartan",
        "ItalyAircraftG550CAEW": "G550 CAEW",
        "ItalyDroneMQ9": "MQ-9",
        "ItalyHelicopterAW249": "AW249",
        "ItalyHelicopterA129": "A129 Mangusta",
        "ItalyHelicopterNH90": "NH90",
        "ItalyHelicopterAW101": "AW101",
        "ItalyHelicopterAW139": "AW139",
    }
    b_names = {
        "BritainJetF35B": "F-35B",
        "BritainJetTyphoonFGR4": "Eurofighter Typhoon FGR4",
        "BritainJetTyphoonT3": "Typhoon Tranche 3",
        "BritainJetHarrierGR9": "Harrier GR9",
        "BritainJetTornadoGR4": "Tornado GR4",
        "BritainJetJaguarGR3": "Jaguar GR3",
        "BritainJetSeaHarrierFA2": "Sea Harrier FA2",
        "BritainJetPhantomFG1": "Phantom FG1",
        "BritainJetLightningF6": "Lightning F6",
        "BritainJetHawk200": "Hawk 200",
        "BritainJetA400M": "A400M",
        "BritainJetC17": "C-17",
        "BritainAircraftE7": "E-7 Wedgetail",
        "BritainDroneMQ9": "MQ-9 Reaper",
        "BritainBomberVulcan": "Vulcan",
        "BritainHelicopterApache": "Apache AH-64E",
        "BritainHelicopterChinook": "Chinook",
        "BritainHelicopterMerlin": "Merlin",
        "BritainHelicopterWildcat": "Wildcat",
        "BritainHelicopterPuma": "Puma",
    }
    add_units([(a, b, c) for a, b, c, *_ in g_btns] + g_heavy + g_heli, g_names)
    add_units([(a, b, c) for a, b, c, *_ in i_btns] + i_heavy + i_heli, i_names)
    add_units([(a, b, c) for a, b, c, *_ in b_btns] + b_heavy + b_heli, b_names)

    for side, obj, img in (
        ("Germany", "Germany_HelicopterBase", "SPEC_GermanyHelicopterBase"),
        ("Italy", "Italy_HelicopterBase", "SPEC_ItalyHelicopterBase"),
        ("Britain", "Britain_HelicopterBase", "SPEC_BritainHelicopterBase"),
    ):
        buttons.append(btn(f"Command_Construct{obj}", obj, img, f"CONTROLBAR:Construct{obj}", f"CONTROLBAR:ToolTipConstruct{obj}", dozer=True))
        portraits.append(mapped(img))
        csf[f"CONTROLBAR:Construct{obj}"] = "Helicopter Base"
        csf[f"CONTROLBAR:ToolTipConstruct{obj}"] = f"Builds the {side} helicopter base."
        csf[f"OBJECT:{obj}"] = "Helicopter Base"
        csf[f"OBJECT:{side}_LargeAirBase"] = "Fighter Airbase"
        csf[f"OBJECT:{side}_HeavyAirBase"] = "Heavy Airbase"
        csf[f"OBJECT:{side}Airfield"] = "Fighter Airbase"

    w(INI / "CommandButton_EuropeAirforce.ini", "\n".join(buttons) + "\n")
    w(INI / "MappedImages/HandCreated/zEurope_AirbasePortrait_Images.INI", "\n".join(portraits) + "\n")

    # overlay commandsets (documentation + late parse). Live packed CommandSet.ini is patched by packer.
    def patch_overlay_cs(path: Path, country: str, air_name: str, fighter_btns: list[str], heavy_btns: list[str], heli_btns: list[str], airfield_btn: str, heavy_btn: str, heli_btn: str) -> None:
        text = path.read_text(encoding="utf-8", errors="replace")
        text = text.encode("ascii", "replace").decode("ascii")
        import re
        fighter_block = f"CommandSet {air_name}\n{cs_line(fighter_btns)}\nEnd\n"
        text = re.sub(rf"CommandSet {re.escape(air_name)}\s*\n.*?^End\s*$", fighter_block.rstrip(), text, count=1, flags=re.M | re.S)
        extra = (
            f"\nCommandSet {country}_HeavyAirBaseCommandSet\n{cs_line(heavy_btns)}\nEnd\n"
            f"\nCommandSet {country}_HelicopterBaseCommandSet\n{cs_line(heli_btns)}\nEnd\n"
        )
        if f"CommandSet {country}_HeavyAirBaseCommandSet" in text:
            text = re.sub(rf"CommandSet {re.escape(country)}_HeavyAirBaseCommandSet\s*\n.*?^End\s*$", f"CommandSet {country}_HeavyAirBaseCommandSet\n{cs_line(heavy_btns)}\nEnd", text, count=1, flags=re.M | re.S)
        else:
            text += extra
        if f"CommandSet {country}_HelicopterBaseCommandSet" not in text:
            text += f"\nCommandSet {country}_HelicopterBaseCommandSet\n{cs_line(heli_btns)}\nEnd\n"
        worker = f"{country}_WorkerCommandSet"
        if worker in text and heli_btn not in text.split(f"CommandSet {worker}", 1)[-1][:800]:
            text = text.replace(
                f"  11 = {airfield_btn}",
                f"  9 = {heavy_btn}\n  10 = {heli_btn}\n  11 = {airfield_btn}",
                1,
            )
        w(path, text)

    patch_overlay_cs(
        INI / "CommandSet_Germany.ini",
        "Germany",
        "Germany_AirfieldCommandSet",
        [x[0] for x in g_btns],
        [x[0] for x in g_heavy],
        [x[0] for x in g_heli],
        "Command_ConstructGermany_Airfield",
        "Command_ConstructGermany_HeavyAirBase",
        "Command_ConstructGermany_HelicopterBase",
    )
    patch_overlay_cs(
        INI / "CommandSet_Italy.ini",
        "Italy",
        "Italy_AirfieldCommandSet",
        [x[0] for x in i_btns],
        [x[0] for x in i_heavy],
        [x[0] for x in i_heli],
        "Command_ConstructItaly_Airfield",
        "Command_ConstructItaly_HeavyAirBase",
        "Command_ConstructItaly_HelicopterBase",
    )
    patch_overlay_cs(
        INI / "CommandSet_Britain.ini",
        "Britain",
        "Britain_AirfieldCommandSet",
        [x[0] for x in b_btns],
        [x[0] for x in b_heavy],
        [x[0] for x in b_heli],
        "Command_ConstructBritain_Airfield",
        "Command_ConstructBritain_HeavyAirBase",
        "Command_ConstructBritain_HelicopterBase",
    )

    # CSF dump for packer
    import json
    (Path("/tmp/europe_csf_labels.json")).write_text(json.dumps(csf, indent=0), encoding="ascii")
    meta = {
        "germany_fighters": [x[0] for x in g_btns],
        "germany_heavy": [x[0] for x in g_heavy],
        "germany_heli": [x[0] for x in g_heli],
        "italy_fighters": [x[0] for x in i_btns],
        "italy_heavy": [x[0] for x in i_heavy],
        "italy_heli": [x[0] for x in i_heli],
        "britain_fighters": [x[0] for x in b_btns],
        "britain_heavy": [x[0] for x in b_heavy],
        "britain_heli": [x[0] for x in b_heli],
        "csf": csf,
    }
    Path("/workspace/patch/tools/big/europe_airforce_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="ascii")
    print("wrote Europe airforce overlay INI", len(csf), "CSF keys")


if __name__ == "__main__":
    main()
