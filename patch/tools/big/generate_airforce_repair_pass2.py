#!/usr/bin/env python3
"""Repair-pass-2 object/weapon/button/CSF templates. Not a roster rebuild."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"

WEAPON_TEXT = """
Weapon LibyaJetMig21MF_WpnRkt
  PrimaryDamage = 220.0
  PrimaryDamageRadius = 12.0
  SecondaryDamage = 40.0
  SecondaryDamageRadius = 18.0
  AttackRange = 420.0
  MinimumAttackRange = 40.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 4000
  ProjectileObject = GenericUnguidedRockets
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  FireSound = HellfireMissileLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots = 180
  ClipSize = 8
  ClipReloadTime = 16000
  AutoReloadsClip = RETURN_TO_BASE
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End

Weapon LibyaJetMig21_WpnBombHvy
  PrimaryDamage = 980.0
  PrimaryDamageRadius = 36.0
  SecondaryDamage = 80.0
  SecondaryDamageRadius = 52.0
  ScatterRadius = 14.0
  AttackRange = 620.0
  MinimumAttackRange = 90.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 900
  FireFX = FX_AuroraBombLaunch
  ProjectileObject = Fab-250
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  FireSound = B52BombDrop
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 720
  ClipSize = 4
  ClipReloadTime = 28000
  AutoReloadsClip = RETURN_TO_BASE
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End

Weapon UkraineJetMig21_WpnBombMed
  PrimaryDamage = 720.0
  PrimaryDamageRadius = 28.0
  SecondaryDamage = 40.0
  SecondaryDamageRadius = 40.0
  ScatterRadius = 12.0
  AttackRange = 600.0
  MinimumAttackRange = 80.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 900
  FireFX = FX_AuroraBombLaunch
  ProjectileObject = GBU24_GuidedBombObject
  ProjectileDetonationFX = Mirv_HE_Explosion
  FireSound = B52BombDrop
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 650
  ClipSize = 4
  ClipReloadTime = 26000
  AutoReloadsClip = RETURN_TO_BASE
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End

Weapon ItalyJetC130J_WpnHeavy
  PrimaryDamage = 1750.0
  PrimaryDamageRadius = 30.0
  SecondaryDamage = 800.0
  SecondaryDamageRadius = 10.0
  AttackRange = 960.0
  MinimumAttackRange = 500.0
  AcceptableAimDelta = 18
  PreAttackDelay = 2800
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  WeaponSpeed = 9999
  ProjectileObject = GBU24_GuidedBombObject
  FireFX = FX_AuroraBombLaunch
  ProjectileDetonationFX = Mirv_HE_Explosion
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 2200
  ClipSize = 8
  ClipReloadTime = 30000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
End
"""


def construct_btn(name: str, obj: str, label: str, image: str, tip: str) -> str:
    return f"""CommandButton {name}
  Command          = UNIT_BUILD
  Object           = {obj}
  TextLabel        = {label}
  ButtonImage      = {image}
  ButtonBorderType = BUILD
  DescriptLabel    = {tip}
End
"""


NEW_BUTTONS = "\n".join(
    [
        construct_btn("Command_ConstructTurkeyAircraftE3AWACS", "TurkeyAircraftE3AWACS", "CONTROLBAR:ConstructTurkeyAircraftE3AWACS", "us_e3g", "CONTROLBAR:ToolTipTurkeyAircraftE3AWACS"),
        construct_btn("Command_ConstructUkraineAircraftE3AWACS", "UkraineAircraftE3AWACS", "CONTROLBAR:ConstructUkraineAircraftE3AWACS", "us_e3g", "CONTROLBAR:ToolTipUkraineAircraftE3AWACS"),
        construct_btn("Command_ConstructSouthAfricaJetIL76", "SouthAfricaJetIL76", "CONTROLBAR:ConstructSouthAfricaJetIL76", "yier76", "CONTROLBAR:ToolTipSouthAfricaJetIL76"),
        construct_btn("Command_ConstructLibyaJetIL76", "LibyaJetIL76", "CONTROLBAR:ConstructLibyaJetIL76", "yier76", "CONTROLBAR:ToolTipLibyaJetIL76"),
        construct_btn("Command_ConstructSouthAfricaHelicopterRooivalk", "SouthAfricaHelicopterRooivalk", "CONTROLBAR:ConstructSouthAfricaHelicopterRooivalk", "Nat_ah64e", "CONTROLBAR:ToolTipSouthAfricaHelicopterRooivalk"),
        construct_btn("Command_ConstructSouthAfricaHelicopterOryx", "SouthAfricaHelicopterOryx", "CONTROLBAR:ConstructSouthAfricaHelicopterOryx", "rus_mi17", "CONTROLBAR:ToolTipSouthAfricaHelicopterOryx"),
        construct_btn("Command_ConstructLibyaHelicopterMi24", "LibyaHelicopterMi24", "CONTROLBAR:ConstructLibyaHelicopterMi24", "rus_mi17", "CONTROLBAR:ToolTipLibyaHelicopterMi24"),
    ]
)

CSF_LABELS = {
    "CONTROLBAR:ConstructTurkeyAircraftE3AWACS": "E-3 AWACS",
    "CONTROLBAR:ToolTipTurkeyAircraftE3AWACS": "Turkish E-3 AWACS. Scan and detect. No weapons.",
    "OBJECT:TurkeyAircraftE3AWACS": "E-3 AWACS",
    "CONTROLBAR:ConstructUkraineAircraftE3AWACS": "E-3 AWACS",
    "CONTROLBAR:ToolTipUkraineAircraftE3AWACS": "Ukrainian E-3 AWACS. Scan and detect. No weapons.",
    "OBJECT:UkraineAircraftE3AWACS": "E-3 AWACS",
    "OBJECT:FranceAircraftE3": "E-3 AWACS",
    "OBJECT:ItalyAircraftG550CAEW": "G550 CAEW",
    "CONTROLBAR:ConstructSouthAfricaJetIL76": "IL-76",
    "CONTROLBAR:ToolTipSouthAfricaJetIL76": "SAAF IL-76 heavy runway transport.",
    "OBJECT:SouthAfricaJetIL76": "IL-76",
    "CONTROLBAR:ConstructLibyaJetIL76": "IL-76",
    "CONTROLBAR:ToolTipLibyaJetIL76": "Libyan IL-76 heavy runway transport.",
    "OBJECT:LibyaJetIL76": "IL-76",
    "CONTROLBAR:ConstructSouthAfricaHelicopterRooivalk": "Rooivalk",
    "CONTROLBAR:ToolTipSouthAfricaHelicopterRooivalk": "SAAF Rooivalk attack helicopter.",
    "OBJECT:SouthAfricaHelicopterRooivalk": "Rooivalk",
    "CONTROLBAR:ConstructSouthAfricaHelicopterOryx": "Oryx",
    "CONTROLBAR:ToolTipSouthAfricaHelicopterOryx": "SAAF Oryx transport helicopter.",
    "OBJECT:SouthAfricaHelicopterOryx": "Oryx",
    "CONTROLBAR:ConstructLibyaHelicopterMi24": "Mi-24",
    "CONTROLBAR:ToolTipLibyaHelicopterMi24": "Libyan Mi-24 attack helicopter.",
    "OBJECT:LibyaHelicopterMi24": "Mi-24",
    "OBJECT:ItalyJetC130J": "C-130J Bomber",
    "OBJECT:ItalyJetC27J": "C-27J Spartan Gunship",
    "OBJECT:TurkeyJetNF5": "NF-5A",
    "OBJECT:TurkeyJetHurjet": "Hurjet",
}

ZA_HEAVY = """CommandSet SouthAfrica_HeavyAirBaseCommandSet
  1 = Command_ConstructSouthAfrica_Mi-8T
  2 = Command_ConstructSouthAfricaHelicopterRooivalk
  3 = Command_ConstructSouthAfricaHelicopterOryx
  4 = Command_ConstructSouthAfricaJetIL76
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

LY_HEAVY = """CommandSet Libya_HeavyAirBaseCommandSet
  1 = Command_ConstructLibya_Mi-8T
  2 = Command_ConstructLibyaHelicopterMi24
  3 = Command_ConstructLibyaJetIL76
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

TR_HEAVY = """CommandSet Turkey_HeavyAirBaseCommandSet
  1 = Command_ConstructTurkeyAircraftE3AWACS
  2 = Command_ConstructTurkeyHelicopterAH64E
  3 = Command_ConstructTurkeyHelicopterUH60
  4 = Command_ConstructTurkeyHelicopterCH47F
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

UA_HEAVY = """CommandSet Ukraine_HeavyAirBaseCommandSet
  1 = Command_ConstructUkraineAircraftE3AWACS
  2 = Command_ConstructUkraineHelicopterCH47F
  3 = Command_ConstructUkraineHelicopterUH60
  4 = Command_ConstructUkraineHelicopterAH64E
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

# Visual assignments: object -> (new default model, damaged, rubble)
# Same-country W3Ds must be distinct. Cross-country reuse is allowed.
VISUALS = {
    "TurkeyJetNF5": ("UVVampire", "UVVampire_D", "UVVampire"),
    "TurkeyJetHurjet": ("LSFT50", "LSFT50d", "LSFT50k"),
    "SouthAfricaJetHawk120": ("UVVampire", "UVVampire_D", "UVVampire"),
    "SouthAfricaJetHawk127": ("AVHawk", "AVHawk_D", "AVHawk_D"),
    "SouthAfricaJetImpala": ("UV_Turbo", "UV_Turbo", "UV_Turbo"),
    "SwedenJetSK60": ("AGMZRT501", "AGMZRT501", "AGMZRT501"),
    "SwedenJetSK60B": ("AVHawk_D1", "AVHawk_D1", "AVHawk_D1"),
    "ItalyJetMB339": ("qsnt50", "qsnt50", "qsnt50"),
    "ItalyJetM346FA": ("LSFT50d", "LSFT50d", "LSFT50k"),
    "ItalyJetTyphoon": ("EVTyphoon", "EVTyphoon", "EVTyphoon"),
    "FranceUCAVNeuron": ("AV_RQ180", "AV_RQ180_D", "AV_RQ180_E"),
}

SCALE = {
    "SouthAfricaJetMirageIIICZ": (0.86, 1.08, "FranceJetMirageF1CT 0.85 / TurkeyJetF16C 0.90"),
    "LibyaJetMig21MF": (0.80, 0.96, "IndiaJetMig21Bison 0.84 / TurkeyJetF16C 0.90"),
    "LibyaJetMig21": (0.82, 0.92, "UVMig-21 family; offset from MF"),
    "UkraineJetMig29": (0.88, 0.96, "UkraineJetSu27 0.98 ceiling / VietnamJetMig29S 0.90"),
    "UkraineJetMig21": (0.82, 0.94, "IndiaJetMig21Bison 0.84 / F-16 0.88-0.90"),
}


def awacs_ini(obj: str, side: str, portrait: str, model: str, use_anim: bool) -> str:
    anim = ""
    if use_anim:
        anim = f"\n      Animation = {model}.{model}\n      AnimationMode = LOOP"
    return f"""; SPECTER repair pass 2 - local AWACS wrapper. USA E-3 scan/detector referenced, USA object untouched.
Object {obj}
Scale = 0.90

  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {model}{anim}
      ParticleSysBone = Engine01 HighAltitudeJetContrail
      ParticleSysBone = Engine02 HighAltitudeJetContrail
      ParticleSysBone = Engine03 HighAltitudeJetContrail
      ParticleSysBone = Engine04 HighAltitudeJetContrail
    End
    ConditionState = REALLYDAMAGED
      Model = {model}{anim}
      ParticleSysBone = Smoke01 JetSmokeLarge
    End
    ConditionState = RUBBLE
      Model = {model}
    End
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  MaxSimultaneousOfType = 1
  BuildTime = 70.0
  BuildCost = 4200
  TransportSlotCount = 0
  VisionRange = 900.0
  ShroudClearingRange = 700.0
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  CommandSet = E3G_CommandSet
  ExperienceValue = 200 200 200 200
  IsTrainable = No
  SoundAmbient = B52AmbientLoop
  SoundAmbientRubble = NoSound
  RadarPriority = UNIT
  KindOf = AIRCRAFT PRELOAD SCORE SELECTABLE VEHICLE REVEALS_ENEMY_PATHS CAN_CAST_REFLECTIONS
  Body = ActiveBody ModuleTag_03
    MaxHealth = 1000.0
    InitialHealth = 1000.0
  End
  Behavior = PhysicsBehavior ModuleTag_Mass
    Mass = 300.0
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
  Behavior = SpecialAbility ModuleTag_AWACSSP
    SpecialPowerTemplate = SuperweaponNatoAWACS
    UpdateModuleStartsAttack = Yes
  End
  Behavior = StealthDetectorUpdate ModuleTag_16f6
    DetectionRate = 1800
    DetectionRange = 1000
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End
  Behavior = OCLSpecialPower ModuleTag_SSM
    SpecialPowerTemplate = Superweapon_ANAPY2_SARSCANMODE
    OCL = SUPERWEAPON_ANAPY2_SARSCAN
    CreateLocation = CREATE_AT_EDGE_NEAR_SOURCE
  End
  Behavior = JetSlowDeathBehavior ModuleTag_v310
    DestructionDelay = 15000
    RollRate = 0.1
    RollRateDelta = 1%
    PitchRate = 0.0
    FallHowFast = 80.0%
    FXInitialDeath = FX_JetBigDeathInitial
    OCLInitialDeath = OCL_AmericaJetCargoDeathStart
    DelaySecondaryFromInitialDeath = 2000
    OCLSecondary = OCL_AmericaJetCargoHulkDeath
    FXSecondary = FX_BigPlaneDeath
    FXHitGround = FX_BigJetDeathHitGround
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    DelayFinalBlowUpFromHitGround = 1000
    OCLFinalBlowUp = OCL_AmericaJetB52DeathFinalBlowUp
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 60.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def il76_ini(obj: str, side: str, model: str) -> str:
    return f"""; SPECTER repair pass 2 - playable IL-76. C-130/SpecterPlayableIL76 gameplay. Science paradrop object left intact.
Object {obj}
Scale = 0.95

  SelectPortrait = yier76
  ButtonImage = yier76
  Draw = W3DModelDraw ModuleTag_C130_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {model}
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = {model}
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = RUBBLE
      Model = {model}
    End
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 300.0
  BuildCost = 2600
  BuildTime = 26.0
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = C17GlobalMasterCommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceGuard = RaptorVoiceAirPatrol
  SoundAmbient = AdvancedFightEngineLoop
  SoundAmbientRubble = NoSound
  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_C130_02
    MaxHealth = 860.0
    InitialHealth = 860.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_C130_05
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
  Behavior = PhysicsBehavior ModuleTag_C130_07
    Mass = 900.0
  End
  Behavior = JetAIUpdate ModuleTag_C130_09
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
  Behavior = TransportContain ModuleTag_C130_Cargo
    Slots = 32
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY VEHICLE
    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE
    ExitDelay = 100
    NumberOfExitPaths = 1
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 14.0
  GeometryHeight = 12.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def heli_ini(obj: str, side: str, portrait: str, model: str, attack: bool, anim: bool) -> str:
    anim_l = f"\n      Animation = {model}.{model}\n      AnimationMode = LOOP" if anim else ""
    wpn = ""
    kind = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD"
    cmd = "AmericaVehicleChinookCommandSet"
    if attack:
        kind = "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD"
        cmd = "GenericAttackHelicopterHoverCommandSet"
        wpn = """
  WeaponSet
    Conditions = None
    Weapon = PRIMARY GenericHeliGunnerSight
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 8x_MRATGM_AGM114L
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""
    cargo = "" if attack else """
  Behavior = TransportContain ModuleTag_Cargo
    Slots = 12
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY VEHICLE
    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE
    ExitDelay = 100
    NumberOfExitPaths = 1
  End
"""
    return f"""; SPECTER repair pass 2 - local helicopter. JetAIUpdate NeedsRunway=No (VN Mi-8 / ROK AH-64E pattern).
Object {obj}
Scale = 0.90

  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {model}{anim_l}
    End
    ConditionState = REALLYDAMAGED
      Model = {model}{anim_l}
    End
    ConditionState = RUBBLE
      Model = {model}
    End
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = 350.0
  ShroudClearingRange = 250.0
{wpn}
  ArmorSet
    Conditions = None
    Armor = ChinookArmor
    DamageFX = None
  End
  BuildCost = {1800 if attack else 1200}
  BuildTime = {18.0 if attack else 14.0}
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = {cmd}
  VoiceSelect = ChinookVoiceSelect
  VoiceMove = ChinookVoiceMove
  VoiceAttack = ChinookVoiceAttack
  SoundAmbient = Ch47AmbientLoop
  SoundAmbientRubble = NoSound
  RadarPriority = UNIT
  KindOf = {kind}
  Body = ActiveBody ModuleTag_03
    MaxHealth = {520.0 if attack else 400.0}
    InitialHealth = {520.0 if attack else 400.0}
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = JetAIUpdate ModuleTag_09ai
    MinHeight = 10
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    AutoAcquireEnemiesWhenIdle = {"Yes" if attack else "No"}
  End
  Locomotor = SET_NORMAL ChinookLocomotor
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 50.0
  End
  Behavior = HelicopterSlowDeathBehavior ModuleTag_08
    DestructionDelay = 99999999
    SpiralOrbitTurnRate = 140.0
    SpiralOrbitForwardSpeed = 350.0
    SpiralOrbitForwardSpeedDamping = .9999
    MaxBraking = 190
    SoundDeathLoop = ComancheDamagedLoop
    MinSelfSpin = 100
    MaxSelfSpin = 300
    SelfSpinUpdateDelay = 100
    SelfSpinUpdateAmount = 10
    FallHowFast = 12.0%
    MinBladeFlyOffDelay = 1500
    MaxBladeFlyOffDelay = 1500
    FXHitGround = FX_HelicopterHitGround
    OCLHitGround = OCL_HelicopterHitGround
    FXFinalBlowUp = FX_GroundedHelicopterBlowUp
    OCLFinalBlowUp = OCL_GroundedHelicopterBlowUp
    DelayFromGroundToFinalDeath = 1500
    FinalRubbleObject = ChinookRubbleHull
  End
{cargo}
  Geometry = BOX
  GeometryMajorRadius = 20.0
  GeometryMinorRadius = 6.0
  GeometryHeight = 12.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def write_objects() -> list[Path]:
    out: list[Path] = []
    mapping = [
        (PATCH / "INI/Object/Specter/Turkey Armed Forces/Airforce/TurkeyAircraftE3AWACS.ini", awacs_ini("TurkeyAircraftE3AWACS", "Turkey", "us_e3g", "US_E3G", True)),
        (PATCH / "INI/Object/Specter/Ukrainian Armed Forces/Airforce/UkraineAircraftE3AWACS.ini", awacs_ini("UkraineAircraftE3AWACS", "Ukraine", "us_e3g", "US_E3G", True)),
        (PATCH / "INI/Object/Specter/South African National Defence Force/Airforce/SouthAfricaJetIL76.ini", il76_ini("SouthAfricaJetIL76", "SouthAfrica", "Iraq_IL-76")),
        (PATCH / "INI/Object/Specter/Libyan Armed Forces/Airforce/LibyaJetIL76.ini", il76_ini("LibyaJetIL76", "Libya", "Iraq_IL-76")),
        (PATCH / "INI/Object/Specter/South African National Defence Force/Airforce/SouthAfricaHelicopterRooivalk.ini", heli_ini("SouthAfricaHelicopterRooivalk", "SouthAfrica", "Nat_ah64e", "LSFFRTiger", True, True)),
        (PATCH / "INI/Object/Specter/South African National Defence Force/Airforce/SouthAfricaHelicopterOryx.ini", heli_ini("SouthAfricaHelicopterOryx", "SouthAfrica", "rus_mi17", "NAT_Puma", False, False)),
        (PATCH / "INI/Object/Specter/Libyan Armed Forces/Airforce/LibyaHelicopterMi24.ini", heli_ini("LibyaHelicopterMi24", "Libya", "rus_mi17", "Iraq_Mi-35M3", True, True)),
    ]
    for path, text in mapping:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="ascii", newline="\n")
        out.append(path)
    return out
