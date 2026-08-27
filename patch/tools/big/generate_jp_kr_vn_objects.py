#!/usr/bin/env python3
"""Write JP/KR/VN airforce overlay objects (ASCII, LF). ART is visual only."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/workspace/patch/Data")
INI = ROOT / "INI"
JP = INI / "Object/Specter/Japan Self-Defense Forces/Airforce"
KR = INI / "Object/Specter/Republic of Korea Armed Forces/Airforce"
VN = INI / "Object/Specter/Vietnam People's Army/Airforce"
IQ = INI / "Object/Specter/Iraq Army/Airforce"
IQS = INI / "Object/Specter/Iraq Army/ScienceObjects"


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\r\n", "\n").replace("\r", "\n")
    if not data.endswith("\n"):
        data += "\n"
    if any(ord(c) > 127 for c in data):
        raise SystemExit(f"non-ASCII {path}")
    path.write_bytes(data.encode("ascii"))


DRAW = """  Draw = W3DModelDraw ModuleTag_01

    DefaultConditionState
      Model               = {model}
      WeaponLaunchBone    = PRIMARY   Weapon01
      WeaponLaunchBone    = SECONDARY Weapon02
      WeaponLaunchBone    = TERTIARY  Weapon01
    End

    ConditionState        = JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ParticleSysBone     = Engine01 JetLenzflare
    End

    ConditionState        = REALLYDAMAGED
      Model               = {model_d}
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = {model_d}
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER
      Model               = {model_d}
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Engine01 JetLenzflare
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = RUBBLE
      Model               = {model_k}
      HideSubObject       = None
      ShowSubObject       = None
    End

    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER
      Model               = {model_k}
      HideSubObject       = None
      ShowSubObject       = None
      ParticleSysBone     = Engine01 JetExhaust
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    OkToChangeModelColor = Yes
  End
"""


def wset(pri: str, sec: str, ter: str, pri_vs: str, sec_vs: str, ter_vs: str) -> str:
    return (
        "  WeaponSet\n"
        "    Conditions = None\n"
        f"    Weapon              = PRIMARY    {pri}\n"
        f"    PreferredAgainst    = PRIMARY    {pri_vs}\n"
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        f"    Weapon              = SECONDARY  {sec}\n"
        f"    PreferredAgainst    = SECONDARY  {sec_vs}\n"
        "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        f"    Weapon              = TERTIARY   {ter}\n"
        f"    PreferredAgainst    = TERTIARY   {ter_vs}\n"
        "    AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "  End\n"
    )


def fighter(
    obj: str,
    side: str,
    portrait: str,
    model: str,
    model_d: str,
    model_k: str,
    weapons: str,
    cost: int,
    time: float,
    hp: int,
    scale: float,
    vision: float,
    note: str,
    locomotor: str = "Snecma_M88_4E",
    needs_runway: str = "Yes",
    idle_acquire: str = "Yes",
) -> str:
    return (
        f"; SPECTER - {note}\n"
        f"Object {obj}\n"
        f"Scale = {scale:.2f}\n"
        f"\n"
        f"  SelectPortrait         = {portrait}\n"
        f"  ButtonImage            = {portrait}\n"
        f"  UpgradeCameo1 = Upgrade_AmericaCountermeasures\n"
        f"\n"
        + DRAW.format(model=model, model_d=model_d, model_k=model_k)
        + f"\n"
        f"  DisplayName         = OBJECT:{obj}\n"
        f"  EditorSorting       = VEHICLE\n"
        f"  Side                = {side}\n"
        f"  TransportSlotCount  = 0\n"
        f"  VisionRange         = {vision:.1f}\n"
        f"  ShroudClearingRange = 220.0\n"
        f"\n"
        f"{weapons}"
        f"  ArmorSet\n"
        f"    Conditions            = None\n"
        f"    Armor                 = AirplaneArmor\n"
        f"    DamageFX              = None\n"
        f"  End\n"
        f"  ArmorSet\n"
        f"    Conditions            = PLAYER_UPGRADE\n"
        f"    Armor                 = CountermeasuresAirplaneArmor\n"
        f"    DamageFX              = None\n"
        f"  End\n"
        f"\n"
        f"  BuildCost               = {cost}\n"
        f"  BuildTime               = {time:.1f}\n"
        f"  ExperienceValue         = 50 50 100 150\n"
        f"  ExperienceRequired      = 0 100 200 400\n"
        f"  IsTrainable             = Yes\n"
        f"  CrusherLevel            = 1\n"
        f"  CrushableLevel          = 2\n"
        f"  CommandSet              = F22A_AA_CommandSet\n"
        f"\n"
        f"  VoiceSelect            = RaptorVoiceSelect\n"
        f"  VoiceMove              = RaptorVoiceMove\n"
        f"  VoiceAttack            = RaptorVoiceAttack\n"
        f"  VoiceAttackAir         = RaptorVoiceAttackAir\n"
        f"  VoiceGuard             = RaptorVoiceAirPatrol\n"
        f"  SoundAmbient           = RaptorAmbientLoop\n"
        f"  SoundAmbientRubble     = NoSound\n"
        f"  UnitSpecificSounds\n"
        f"    VoiceCreate          = RaptorVoiceCreate\n"
        f"    SoundEject           = PilotSoundEject\n"
        f"    VoiceEject           = PilotVoiceEject\n"
        f"    Afterburner          = RaptorAfterburner\n"
        f"    VoiceLowFuel         = RaptorVoiceLowFuel\n"
        f"    VoiceGarrison        = RaptorVoiceMove\n"
        f"  End\n"
        f"\n"
        f"  RadarPriority          = UNIT\n"
        f"  KindOf                 = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT\n"
        f"  Body                   = ActiveBody ModuleTag_02\n"
        f"    MaxHealth            = {hp}.0\n"
        f"    InitialHealth        = {hp}.0\n"
        f"  End\n"
        f"  Behavior                = ArmorUpgrade ModuleTag_Armor01x2\n"
        f"    TriggeredBy           = Upgrade_AmericaCountermeasures\n"
        f"  End\n"
        f"  Behavior                = CountermeasuresBehavior ModuleTag_10\n"
        f"    TriggeredBy           = Upgrade_AmericaCountermeasures\n"
        f"    FlareTemplateName     = CountermeasureFlare\n"
        f"    FlareBoneBaseName     = Flare\n"
        f"    VolleySize            = 2\n"
        f"    VolleyArcAngle        = 96.0\n"
        f"    VolleyVelocityFactor  = 3.0\n"
        f"    DelayBetweenVolleys   = 1000\n"
        f"    NumberOfVolleys       = 4\n"
        f"    ReloadTime            = 0\n"
        f"    EvasionRate           = 35%\n"
        f"    ReactionLaunchLatency = 0\n"
        f"    MissileDecoyDelay     = 200\n"
        f"  End\n"
        f"  Behavior = ProductionUpdate ModuleTag_SelfUp\n"
        f"  End\n"
        f"  Behavior                          = JetSlowDeathBehavior ModuleTag_05\n"
        f"    FXOnGroundDeath                 = FX_JetOnGroundDeath\n"
        f"    OCLOnGroundDeath                = OCL_RaptorDeathFinalBlowUp\n"
        f"    DestructionDelay                = 99999999\n"
        f"    RollRate                        = 0.2\n"
        f"    RollRateDelta                   = 100%\n"
        f"    PitchRate                       = 0.0\n"
        f"    FallHowFast                     = 110.0%\n"
        f"    FXInitialDeath                  = FX_RaptorDeathInitial\n"
        f"    OCLInitialDeath                 = OCL_RaptorDeathInitial\n"
        f"    DelaySecondaryFromInitialDeath  = 500\n"
        f"    FXSecondary                     = FX_JetDeathSecondary\n"
        f"    OCLSecondary                    = OCL_RaptorDeathSecondary\n"
        f"    FXHitGround                     = FX_JetDeathHitGround\n"
        f"    OCLHitGround                    = OCL_RaptorDeathHitGround\n"
        f"    DelayFinalBlowUpFromHitGround   = 200\n"
        f"    FXFinalBlowUp                   = FX_JetDeathFinalBlowUp\n"
        f"    OCLFinalBlowUp                  = OCL_RaptorDeathFinalBlowUp\n"
        f"  End\n"
        f"  Behavior = CreateObjectDie ModuleTag_Deletion\n"
        f"    DeathTypes   = NONE +EXTRA_6\n"
        f"    CreationList = None\n"
        f"  End\n"
        f"  Behavior                    = EjectPilotDie ModuleTag_06\n"
        f"    ExemptStatus         = HIJACKED\n"
        f"    GroundCreationList = OCL_EjectPilotOnGround\n"
        f"    AirCreationList = OCL_EjectPilotViaParachute\n"
        f"    VeterancyLevels =  ALL -REGULAR\n"
        f"  End\n"
        f"  Behavior               = PhysicsBehavior ModuleTag_07\n"
        f"    Mass                 = 500.0\n"
        f"  End\n"
        f"  Behavior                 = TransitionDamageFX ModuleTag_08\n"
        f"    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes Psys:SmokeSmallContinuous01\n"
        f"    ReallyDamagedFXList1         = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition\n"
        f"  End\n"
        f"  Behavior = JetAIUpdate ModuleTag_09ai\n"
        f"    OutOfAmmoDamagePerSecond  = 0%\n"
        f"    TakeoffDistForMaxLift     = 0%\n"
        f"    TakeoffPause              = 500\n"
        f"    MinHeight                 = 5\n"
        f"    ParkingOffset             = 3\n"
        f"    ReturnToBaseIdleTime      = 10000\n"
        f"    AutoAcquireEnemiesWhenIdle = {idle_acquire}\n"
        f"    NeedsRunway               = {needs_runway}\n"
        f"    KeepsParkingSpaceWhenAirborne = Yes\n"
        f"  End\n"
        f"  Locomotor = SET_NORMAL {locomotor}\n"
        f"  Locomotor = SET_TAXIING BasicJetTaxiLocomotor\n"
        f"\n"
        f"  Behavior = FlammableUpdate ModuleTag_21\n"
        f"    AflameDuration = 5000\n"
        f"    AflameDamageAmount = 3\n"
        f"    AflameDamageDelay = 500\n"
        f"  End\n"
        f"\n"
        f"  Behavior = FireWeaponWhenDamagedBehavior ModuleTag_RS\n"
        f"    StartsActive                = Yes\n"
        f"    ReactionWeaponPristine      = RadarWaveEmitter\n"
        f"    ReactionWeaponDamaged       = RadarWaveEmitter\n"
        f"    ReactionWeaponReallyDamaged = RadarWaveEmitter\n"
        f"    ReactionWeaponRubble        = RadarWaveEmitter\n"
        f"    DamageTypes                 = NONE +MICROWAVE\n"
        f"  End\n"
        f"\n"
        f"  Geometry                 = Box\n"
        f"  GeometryIsSmall          = Yes\n"
        f"  GeometryMajorRadius      = 14.0\n"
        f"  GeometryMinorRadius      = 7.0\n"
        f"  GeometryHeight           = 5.0\n"
        f"  Shadow                   = SHADOW_VOLUME\n"
        f"  ShadowSizeX = 89\n"
        f"\n"
        f"End\n"
    )


def transport_jet(
    obj: str,
    side: str,
    portrait: str,
    model: str,
    model_d: str,
    model_k: str,
    note: str,
    scale: float = 1.00,
    slots: int = 28,
    cost: int = 2400,
    hp: int = 780,
    locomotor: str = "D30-F6_JetLocomotor",
) -> str:
    return f"""; SPECTER - {note}
Object {obj}
Scale = {scale:.2f}

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}

  Draw = W3DModelDraw ModuleTag_C130_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = {model}
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = {model}
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = {model_d}
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = REALLYDAMAGED JETEXHAUST
      Model = {model_d}
      ParticleSysBone = SMOKE01 JetSmoke
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
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
  ShroudClearingRange = 300.0
  BuildCost = {cost}
  BuildTime = 26.0
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
    SoundEject = PilotSoundEject
    VoiceEject = PilotVoiceEject
    Afterburner = RaptorAfterburner
    VoiceLowFuel = RaptorVoiceLowFuel
    VoiceGarrison = RaptorVoiceMove
  End
  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_C130_02
    MaxHealth = {hp}.0
    InitialHealth = {hp}.0
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
  Behavior = TransitionDamageFX ModuleTag_C130_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
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
  Locomotor = SET_NORMAL {locomotor}
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Behavior = FlammableUpdate ModuleTag_C130_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior = TransportContain ModuleTag_C130_Cargo
    Slots                 = {slots}
    DamagePercentToUnits  = 100%
    AllowInsideKindOf     = INFANTRY VEHICLE
    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE
    ExitDelay             = 100
    NumberOfExitPaths     = 1
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


def e737_ini() -> str:
    return """; SPECTER - ROKAF E-737 Peace Eye. Static KVE737 mesh. No Animation.
Object SouthKoreaJetE737
Scale = 0.92

  SelectPortrait         = us_e3g
  ButtonImage            = us_e3g

  Draw = W3DModelDraw ModuleTag_E737_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = KVE737
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = KVE737
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = KVE737
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = RUBBLE
      Model = KVE737
    End
  End

  DisplayName = OBJECT:SouthKoreaJetE737
  EditorSorting = VEHICLE
  Side = SouthKorea
  TransportSlotCount = 0
  VisionRange = 500.0
  ShroudClearingRange = 700.0
  BuildCost = 2800
  BuildTime = 28.0
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = GenericCommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceGuard = RaptorVoiceAirPatrol
  SoundAmbient = AdvancedFightEngineLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = RaptorVoiceCreate
    SoundEject = PilotSoundEject
    VoiceEject = PilotVoiceEject
    Afterburner = RaptorAfterburner
    VoiceLowFuel = RaptorVoiceLowFuel
    VoiceGarrison = RaptorVoiceMove
  End
  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_E737_02
    MaxHealth = 620.0
    InitialHealth = 620.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_E737_05
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
  Behavior = PhysicsBehavior ModuleTag_E737_07
    Mass = 800.0
  End
  Behavior = JetAIUpdate ModuleTag_E737_09
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
  GeometryMajorRadius = 36.0
  GeometryMinorRadius = 12.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def helo(
    obj: str,
    side: str,
    portrait: str,
    model: str,
    anim: str | None,
    note: str,
    scale: float,
    kind: str,
    locomotor: str,
    slots: int,
    cost: int,
    hp: int,
    attack: bool,
    weapons: str,
    commandset: str,
) -> str:
    anim_block = ""
    if anim:
        anim_block = f"      Animation = {anim}\n      AnimationMode = LOOP\n"
    dmg = model
    atk = " CAN_ATTACK" if attack else ""
    return f"""; SPECTER - {note}
Object {obj}
Scale = {scale:.2f}

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}
  UpgradeCameo1 = Upgrade_AmericaCountermeasures

  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {model}
{anim_block}    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
{anim_block}    End
    ConditionState = RUBBLE
      Model = {dmg}
{anim_block}    End
    OkToChangeModelColor = Yes
  End

  DisplayName         = OBJECT:{obj}
  EditorSorting       = VEHICLE
  Side                = {side}
  TransportSlotCount  = 0
  VisionRange         = 350.0
  ShroudClearingRange = 250.0
{weapons}  ArmorSet
    Conditions      = None
    Armor           = ChinookArmor
    DamageFX        = None
  End
  BuildCost           = {cost}
  BuildTime           = 18.0
  ExperienceValue     = 50 50 100 150
  IsTrainable         = No
  CommandSet          = {commandset}
  VoiceSelect     = ChinookVoiceSelect
  VoiceMove       = ChinookVoiceMove
  VoiceAttack     = ChinookVoiceAttack
  SoundAmbient    = Ch47AmbientLoop
  SoundAmbientRubble    = NoSound
  UnitSpecificSounds
    VoiceCreate         = ChinookVoiceCreate
    VoiceUnload         = ChinookVoiceUnload
    VoiceGarrison       = ChinookVoiceMove
  End
  RadarPriority   = UNIT
  KindOf          = PRELOAD CAN_CAST_REFLECTIONS{atk} SELECTABLE VEHICLE {kind} AIRCRAFT SCORE PRODUCED_AT_HELIPAD
  Body = ActiveBody ModuleTag_03
    MaxHealth       = {hp}.0
    InitialHealth   = {hp}.0
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = JetAIUpdate ModuleTag_09ai
    MinHeight                     = 10
    NeedsRunway                   = No
    KeepsParkingSpaceWhenAirborne = No
    AutoAcquireEnemiesWhenIdle    = {"Yes" if attack else "No"}
  End
  Locomotor = SET_NORMAL    {locomotor}
  Locomotor = SET_TAXIING   BasicHelicopterTaxiLocomotor
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 50.0
  End
  Behavior = HelicopterSlowDeathBehavior ModuleTag_08
    DestructionDelay                = 99999999
    SpiralOrbitTurnRate             = 140.0
    SpiralOrbitForwardSpeed         = 350.0
    SpiralOrbitForwardSpeedDamping  = .9999
    MaxBraking                      = 190
    SoundDeathLoop                  = ComancheDamagedLoop
    MinSelfSpin                     = 100
    MaxSelfSpin                     = 300
    SelfSpinUpdateDelay             = 100
    SelfSpinUpdateAmount            = 10
    FallHowFast                     = 12.0%
    MinBladeFlyOffDelay             = 1500
    MaxBladeFlyOffDelay             = 1500
    FXHitGround                     = FX_HelicopterHitGround
    OCLHitGround                    = OCL_HelicopterHitGround
    FXFinalBlowUp                   = FX_GroundedHelicopterBlowUp
    OCLFinalBlowUp                  = OCL_GroundedHelicopterBlowUp
    DelayFromGroundToFinalDeath     = 1500
    FinalRubbleObject               = ChinookRubbleHull
  End
  Behavior = TransportContain ModuleTag_Cargo
    Slots                 = {slots}
    DamagePercentToUnits  = 100%
    AllowInsideKindOf     = INFANTRY VEHICLE
    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE
    ExitDelay             = 100
    NumberOfExitPaths     = 1
  End
  Geometry              = BOX
  GeometryMajorRadius   = 20.0
  GeometryMinorRadius   = 6.0
  GeometryHeight        = 12.0
  GeometryIsSmall       = No
  Shadow                = SHADOW_VOLUME
  ShadowSizeX           = 45
End
"""


def apache_weapons() -> str:
    return (
        "  WeaponSet\n"
        "    Conditions          = None\n"
        "    Weapon              = PRIMARY     GenericHeliGunnerSight\n"
        "    PreferredAgainst    = PRIMARY     INFANTRY VEHICLE\n"
        "    AutoChooseSources   = PRIMARY     FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "    Weapon              = SECONDARY   8x_MRATGM_AGM114L\n"
        "    PreferredAgainst    = SECONDARY   VEHICLE STRUCTURE\n"
        "    AutoChooseSources   = SECONDARY   FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "    Weapon              = TERTIARY    70mm_Hydra_AH64E\n"
        "    PreferredAgainst    = TERTIARY    INFANTRY VEHICLE\n"
        "    AutoChooseSources   = TERTIARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "  End\n"
    )


def a2a(name: str, dmg: float, rng: float, clip: int, delay: int, proj: str, reload: int = 14000) -> str:
    return f"""Weapon {name}
  PrimaryDamage = {dmg:.1f}
  PrimaryDamageRadius = 12.0
  SecondaryDamage = 12.0
  SecondaryDamageRadius = 22.0
  AttackRange = {rng:.1f}
  MinimumAttackRange = 80.0
  AcceptableAimDelta = 360
  DamageType = PENALTY
  DeathType = EXPLODED
  WeaponSpeed = 8600
  FireFX = None
  ProjectileObject = {proj}
  ProjectileDetonationFX = FX_LightAAMImpact
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound = RaptorJetMissileWeapon
  DelayBetweenShots = {delay}
  ClipSize = {clip}
  ClipReloadTime = {reload}
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = Yes
  AntiGround = No
  AntiAirborneInfantry = Yes
  ShowsAmmoPips = Yes
End
"""


def a2g(name: str, dmg: float, rad: float, rng: float, clip: int, delay: int, proj: str, reload: int = 28000) -> str:
    return f"""Weapon {name}
  PrimaryDamage = {dmg:.1f}
  PrimaryDamageRadius = {rad:.1f}
  SecondaryDamage = 30.0
  SecondaryDamageRadius = {rad * 1.6:.1f}
  ScatterRadius = 16.0
  AttackRange = {rng:.1f}
  MinimumAttackRange = 80.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 900
  FireFX = FX_AuroraBombLaunch
  ProjectileObject = {proj}
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound = RaptorJetMissileWeapon
  DelayBetweenShots = {delay}
  ClipSize = {clip}
  ClipReloadTime = {reload}
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ALLIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End
"""


def cannon(name: str, dmg: float, clip: int, delay: int, rng: float) -> str:
    return f"""Weapon {name}
  PrimaryDamage = {dmg:.1f}
  PrimaryDamageRadius = 8.0
  ScatterRadiusVsInfantry = 40.0
  ScatterRadius = 12.0
  AttackRange = {rng:.1f}
  MinimumAttackRange = 20.0
  DamageType = GUN
  DeathType = NORMAL
  WeaponSpeed = 99999
  FireFX = WeaponFX_GenericTankCannonFire
  FireSound = M1A2_TankCannonFire
  DelayBetweenShots = {delay}
  ClipSize = {clip}
  ClipReloadTime = 8000
  AutoReloadsClip = YES
  AntiAirborneVehicle = Yes
  AntiGround = Yes
  AntiAirborneInfantry = Yes
  ShowsAmmoPips = Yes
End
"""


def j10_bomb6() -> str:
    return """Weapon IraqJetMig25RB_WpnLT3
  PrimaryDamage               = 1100.0
  PrimaryDamageRadius         = 60.0
  SecondaryDamage             = 10.0
  SecondaryDamageRadius       = 20.0
  ScatterRadiusVsInfantry     = 10.0
  AttackRange                 = 1100
  MinimumAttackRange          = 500.0
  AcceptableAimDelta          = 35
  DamageType                  = EXPLOSION
  DeathType                   = Exploded
  WeaponSpeed                 = 130
  ProjectileObject            = Sattar_LGAGM_Object
  FireFX                      = None
  FireSound                   = 30mm_fire2
  ProjectileDetonationFX      = FX_HeavyWarheadCruiseMissileExplosion
  RadiusDamageAffects         = ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots           = 400
  ClipSize                    = 6
  ClipReloadTime              = 38500
  AutoReloadsClip             = RETURN_TO_BASE
  ProjectileCollidesWith      = ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle         = No
  AntiGround                  = Yes
  AntiAirborneInfantry        = No
  ShowsAmmoPips               = Yes
  ShockWaveAmount             = 100.0
  ShockWaveRadius             = 100.0
  ShockWaveTaperOff           = 0.33
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


CSF_LABELS = {
    "CONTROLBAR:ConstructVietnamJetMig29S": "MiG-29",
    "CONTROLBAR:ToolTipVietnamJetMig29S": "VPAF MiG-29 interceptor. R-77 and R-73.",
    "OBJECT:VietnamJetMig29S": "MiG-29",
    "CONTROLBAR:ConstructVietnamJetIL76": "IL-76",
    "CONTROLBAR:ToolTipVietnamJetIL76": "VPAF IL-76 heavy runway transport.",
    "OBJECT:VietnamJetIL76": "IL-76",
    "CONTROLBAR:ConstructVietnamJetMi8": "Mi-8",
    "CONTROLBAR:ToolTipVietnamJetMi8": "VPAF Mi-8 utility transport helicopter.",
    "OBJECT:VietnamJetMi8": "Mi-8",
    "CONTROLBAR:ConstructVietnamJetMi17": "Mi-17",
    "CONTROLBAR:ToolTipVietnamJetMi17": "VPAF Mi-17 transport helicopter.",
    "OBJECT:VietnamJetMi17": "Mi-17",
    "CONTROLBAR:ConstructSouthKoreaJetAH64E": "AH-64E Apache Guardian",
    "CONTROLBAR:ToolTipSouthKoreaJetAH64E": "ROK Army AH-64E attack helicopter.",
    "OBJECT:SouthKoreaJetAH64E": "AH-64E Apache Guardian",
    "CONTROLBAR:ConstructSouthKoreaJetCH47": "CH-47D Chinook",
    "CONTROLBAR:ToolTipSouthKoreaJetCH47": "ROK CH-47 transport helicopter.",
    "OBJECT:SouthKoreaJetCH47": "CH-47D Chinook",
    "CONTROLBAR:ConstructSouthKoreaJetUH60P": "UH-60P Black Hawk",
    "CONTROLBAR:ToolTipSouthKoreaJetUH60P": "ROK UH-60P utility helicopter.",
    "OBJECT:SouthKoreaJetUH60P": "UH-60P Black Hawk",
    "CONTROLBAR:ConstructSouthKoreaJetE737": "E-737 Peace Eye",
    "CONTROLBAR:ToolTipSouthKoreaJetE737": "ROKAF E-737 Peace Eye AEW.",
    "OBJECT:SouthKoreaJetE737": "E-737 Peace Eye",
    "CONTROLBAR:ConstructSouthKoreaJetC130H": "C-130H",
    "CONTROLBAR:ToolTipSouthKoreaJetC130H": "ROKAF C-130H runway transport.",
    "OBJECT:SouthKoreaJetC130H": "C-130H",
    "CONTROLBAR:ConstructIraqJetMig25RB": "MiG-25RB",
    "CONTROLBAR:ToolTipIraqJetMig25RB": "MiG-25RB high-speed strike. Six J-10 family bombs.",
    "OBJECT:IraqJetMig25RB": "MiG-25RB",
    "CONTROLBAR:ConstructIraqJetIL76": "IL-76",
    "CONTROLBAR:ToolTipIraqJetIL76": "IL-76 heavy runway transport.",
    "OBJECT:IraqJetIL76": "IL-76",
    "OBJECT:SpecterPlayableIL76": "IL-76",
    "CONTROLBAR:UpgradeJapan_AircraftWeapons": "Aircraft Weapons",
    "CONTROLBAR:ToolTipUpgradeJapan_AircraftWeapons": "Purchase Japan aircraft weapons.",
    "CONTROLBAR:UpgradeJapan_AircraftCountermeasures": "Aircraft Countermeasures",
    "CONTROLBAR:ToolTipUpgradeJapan_AircraftCountermeasures": "Purchase Japan aircraft countermeasures.",
    "CONTROLBAR:UpgradeJapan_F35Integration": "F-35 Integration",
    "CONTROLBAR:ToolTipUpgradeJapan_F35Integration": "Purchase Japan F-35 integration.",
    "CONTROLBAR:UpgradeJapan_PrecisionStrike": "Precision Strike",
    "CONTROLBAR:ToolTipUpgradeJapan_PrecisionStrike": "Purchase Japan precision strike.",
    "CONTROLBAR:UpgradeJapan_DoctrineAirSuperiority": "Air Superiority Doctrine",
    "CONTROLBAR:ToolTipUpgradeJapan_DoctrineAirSuperiority": "Purchase Japan air superiority doctrine.",
    "CONTROLBAR:UpgradeJapan_DoctrinePrecisionStrike": "Precision Doctrine",
    "CONTROLBAR:ToolTipUpgradeJapan_DoctrinePrecisionStrike": "Purchase Japan precision doctrine.",
    "CONTROLBAR:UpgradeJapan_TechPrecisionDefense": "Precision Defense",
    "CONTROLBAR:ToolTipUpgradeJapan_TechPrecisionDefense": "Purchase Japan precision defense.",
    "CONTROLBAR:UpgradeJapan_TechRadarNetwork": "Radar Network",
    "CONTROLBAR:ToolTipUpgradeJapan_TechRadarNetwork": "Purchase Japan radar network.",
    "CONTROLBAR:UpgradeSouthKorea_AircraftWeapons": "Aircraft Weapons",
    "CONTROLBAR:ToolTipUpgradeSouthKorea_AircraftWeapons": "Purchase ROK aircraft weapons.",
    "CONTROLBAR:UpgradeSouthKorea_AircraftCountermeasures": "Aircraft Countermeasures",
    "CONTROLBAR:ToolTipUpgradeSouthKorea_AircraftCountermeasures": "Purchase ROK aircraft countermeasures.",
    "CONTROLBAR:UpgradeSouthKorea_F15KUpgrade": "F-15K Upgrade",
    "CONTROLBAR:ToolTipUpgradeSouthKorea_F15KUpgrade": "Purchase ROK F-15K upgrade.",
    "CONTROLBAR:UpgradeSouthKorea_KFDefense": "KF Defense",
    "CONTROLBAR:ToolTipUpgradeSouthKorea_KFDefense": "Purchase ROK KF defense.",
    "CONTROLBAR:UpgradeSouthKorea_DoctrineAirSuperiority": "Air Superiority Doctrine",
    "CONTROLBAR:ToolTipUpgradeSouthKorea_DoctrineAirSuperiority": "Purchase ROK air superiority doctrine.",
    "CONTROLBAR:UpgradeSouthKorea_TechAirDominanceK": "Air Dominance",
    "CONTROLBAR:ToolTipUpgradeSouthKorea_TechAirDominanceK": "Purchase ROK air dominance.",
    "CONTROLBAR:UpgradeVietnam_AircraftWeapons": "Aircraft Weapons",
    "CONTROLBAR:ToolTipUpgradeVietnam_AircraftWeapons": "Purchase Vietnam aircraft weapons.",
    "CONTROLBAR:UpgradeVietnam_AircraftCountermeasures": "Aircraft Countermeasures",
    "CONTROLBAR:ToolTipUpgradeVietnam_AircraftCountermeasures": "Purchase Vietnam aircraft countermeasures.",
    "CONTROLBAR:UpgradeVietnam_Su30Doctrine": "Su-30 Doctrine",
    "CONTROLBAR:ToolTipUpgradeVietnam_Su30Doctrine": "Purchase Vietnam Su-30 doctrine.",
    "UPGRADE:Japan_AircraftWeapons": "Aircraft Weapons",
    "UPGRADE:Japan_AircraftCountermeasures": "Aircraft Countermeasures",
    "UPGRADE:Japan_F35Integration": "F-35 Integration",
    "UPGRADE:Japan_PrecisionStrike": "Precision Strike",
    "UPGRADE:Japan_DoctrineAirSuperiority": "Air Superiority Doctrine",
    "UPGRADE:Japan_DoctrinePrecisionStrike": "Precision Doctrine",
    "UPGRADE:Japan_TechPrecisionDefense": "Precision Defense",
    "UPGRADE:Japan_TechRadarNetwork": "Radar Network",
    "UPGRADE:SouthKorea_AircraftWeapons": "Aircraft Weapons",
    "UPGRADE:SouthKorea_AircraftCountermeasures": "Aircraft Countermeasures",
    "UPGRADE:SouthKorea_F15KUpgrade": "F-15K Upgrade",
    "UPGRADE:SouthKorea_KFDefense": "KF Defense",
    "UPGRADE:SouthKorea_DoctrineAirSuperiority": "Air Superiority Doctrine",
    "UPGRADE:SouthKorea_TechAirDominanceK": "Air Dominance",
    "UPGRADE:Vietnam_AircraftWeapons": "Aircraft Weapons",
    "UPGRADE:Vietnam_AircraftCountermeasures": "Aircraft Countermeasures",
    "UPGRADE:Vietnam_Su30Doctrine": "Su-30 Doctrine",
    "OBJECT:JapanJetF15JKai": "F-15J Kai",
    "OBJECT:JapanJetF15J": "F-15J",
    "OBJECT:JapanJetF15DJ": "F-15DJ",
    "OBJECT:JapanJetF2A": "F-2A",
    "OBJECT:JapanJetF2B": "F-2B",
    "OBJECT:JapanJetF2Kai": "F-2 Kai",
    "OBJECT:JapanJetF4EJKai": "F-4EJ Kai",
    "OBJECT:JapanJetX2Shinshin": "X-2 Shinshin",
    "OBJECT:JapanJetF35A": "F-35A",
    "OBJECT:JapanJetF35B": "F-35B",
    "OBJECT:JapanJetFX": "F-X",
    "OBJECT:JapanJetF3": "F-3 GCAP",
    "OBJECT:SouthKoreaJetF15K": "F-15K",
    "OBJECT:SouthKoreaJetF15KSlam": "F-15K Slam Eagle",
    "OBJECT:SouthKoreaJetF16C": "F-16C",
    "OBJECT:SouthKoreaJetF16D": "F-16D",
    "OBJECT:SouthKoreaJetKF16": "KF-16",
    "OBJECT:SouthKoreaJetF35A": "F-35A",
    "OBJECT:SouthKoreaJetKF21": "KF-21",
    "OBJECT:SouthKoreaJetKF21Blk2": "KF-21 Block 2",
    "OBJECT:SouthKoreaJetFA50": "FA-50",
    "OBJECT:SouthKoreaJetT50": "T-50",
    "OBJECT:SouthKoreaJetF4E": "F-4E",
    "OBJECT:SouthKoreaJetF5E": "F-5E",
    "OBJECT:VietnamJetMig21bis": "MiG-21bis",
    "OBJECT:VietnamJetMig21": "MiG-21MF",
    "OBJECT:VietnamJetSu22": "Su-22M3",
    "OBJECT:VietnamJetSu22M4": "Su-22M4",
    "OBJECT:VietnamJetSu27": "Su-27SK",
    "OBJECT:VietnamJetSu27UB": "Su-27UBK",
    "OBJECT:VietnamJetSu30": "Su-30MK2",
    "OBJECT:VietnamJetSu30MK2": "Su-30MK2V",
    "OBJECT:VietnamJetYak130": "Yak-130",
    "OBJECT:VietnamJetL39": "L-39",
    "OBJECT:VietnamJetF5E": "F-5E",
}


NEW_BUTTONS = "\n".join(
    [
        construct_btn(
            "Command_ConstructVietnamJetIL76",
            "VietnamJetIL76",
            "CONTROLBAR:ConstructVietnamJetIL76",
            "yier76",
            "CONTROLBAR:ToolTipVietnamJetIL76",
        ),
        construct_btn(
            "Command_ConstructVietnamJetMi8",
            "VietnamJetMi8",
            "CONTROLBAR:ConstructVietnamJetMi8",
            "rus_mi17",
            "CONTROLBAR:ToolTipVietnamJetMi8",
        ),
        construct_btn(
            "Command_ConstructVietnamJetMi17",
            "VietnamJetMi17",
            "CONTROLBAR:ConstructVietnamJetMi17",
            "rus_mi17",
            "CONTROLBAR:ToolTipVietnamJetMi17",
        ),
        construct_btn(
            "Command_ConstructSouthKoreaJetAH64E",
            "SouthKoreaJetAH64E",
            "CONTROLBAR:ConstructSouthKoreaJetAH64E",
            "Nat_ah64e",
            "CONTROLBAR:ToolTipSouthKoreaJetAH64E",
        ),
        construct_btn(
            "Command_ConstructSouthKoreaJetCH47",
            "SouthKoreaJetCH47",
            "CONTROLBAR:ConstructSouthKoreaJetCH47",
            "Nat_ch47",
            "CONTROLBAR:ToolTipSouthKoreaJetCH47",
        ),
        construct_btn(
            "Command_ConstructSouthKoreaJetUH60P",
            "SouthKoreaJetUH60P",
            "CONTROLBAR:ConstructSouthKoreaJetUH60P",
            "us_uh60",
            "CONTROLBAR:ToolTipSouthKoreaJetUH60P",
        ),
        construct_btn(
            "Command_ConstructSouthKoreaJetE737",
            "SouthKoreaJetE737",
            "CONTROLBAR:ConstructSouthKoreaJetE737",
            "us_e3g",
            "CONTROLBAR:ToolTipSouthKoreaJetE737",
        ),
        construct_btn(
            "Command_ConstructSouthKoreaJetC130H",
            "SouthKoreaJetC130H",
            "CONTROLBAR:ConstructSouthKoreaJetC130H",
            "SPEC_JapanC130H",
            "CONTROLBAR:ToolTipSouthKoreaJetC130H",
        ),
        construct_btn(
            "Command_ConstructIraqJetMig25RB",
            "IraqJetMig25RB",
            "CONTROLBAR:ConstructIraqJetMig25RB",
            "irq_mig25",
            "CONTROLBAR:ToolTipIraqJetMig25RB",
        ),
        construct_btn(
            "Command_ConstructIraqJetIL76",
            "IraqJetIL76",
            "CONTROLBAR:ConstructIraqJetIL76",
            "yier76",
            "CONTROLBAR:ToolTipIraqJetIL76",
        ),
    ]
)


JP_HEAVY = """CommandSet Japan_HeavyAirBaseCommandSet
  1 = Command_ConstructJapanJetC130H
  2 = Command_ConstructJapanUAVRQ4
  3 = Command_UpgradeJapan_AircraftWeapons
  4 = Command_UpgradeJapan_AircraftCountermeasures
  5 = Command_UpgradeJapan_F35Integration
  6 = Command_UpgradeJapan_PrecisionStrike
  7 = Command_UpgradeJapan_DoctrineAirSuperiority
  8 = Command_UpgradeJapan_DoctrinePrecisionStrike
  9 = Command_UpgradeJapan_TechPrecisionDefense
  10 = Command_UpgradeJapan_TechRadarNetwork
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

KR_HEAVY = """CommandSet SouthKorea_HeavyAirBaseCommandSet
  1 = Command_ConstructSouthKoreaJetAH64E
  2 = Command_ConstructSouthKoreaJetCH47
  3 = Command_ConstructSouthKoreaJetUH60P
  4 = Command_ConstructSouthKoreaJetE737
  5 = Command_ConstructSouthKoreaJetC130H
  6 = Command_UpgradeSouthKorea_AircraftWeapons
  7 = Command_UpgradeSouthKorea_AircraftCountermeasures
  8 = Command_UpgradeSouthKorea_F15KUpgrade
  9 = Command_UpgradeSouthKorea_KFDefense
  10 = Command_UpgradeSouthKorea_DoctrineAirSuperiority
  11 = Command_UpgradeSouthKorea_TechAirDominanceK
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

VN_FIGHTER = """CommandSet Vietnam_AirfieldCommandSet
  1 = Command_ConstructVietnamAir_Mig29S
  2 = Command_ConstructVietnamJetMig21bis
  3 = Command_ConstructVietnamJetMig21
  4 = Command_ConstructVietnamJetSu22
  5 = Command_ConstructVietnamJetSu22M4
  6 = Command_ConstructVietnamJetSu27
  7 = Command_ConstructVietnamJetSu27UB
  8 = Command_ConstructVietnamJetSu30
  9 = Command_ConstructVietnamJetSu30MK2
  10 = Command_ConstructVietnamJetYak130
  11 = Command_ConstructVietnamJetL39
  12 = Command_ConstructVietnamJetF5E
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

VN_HEAVY = """CommandSet Vietnam_HeavyAirBaseCommandSet
  1 = Command_ConstructVietnamJetMi8
  2 = Command_ConstructVietnamJetMi17
  3 = Command_ConstructVietnamJetIL76
  4 = Command_UpgradeVietnam_AircraftWeapons
  5 = Command_UpgradeVietnam_AircraftCountermeasures
  6 = Command_UpgradeVietnam_Su30Doctrine
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

WEAPON_TEXT = (
    "; SPECTER JP/KR/VN airforce unique weapons. Inlined into Weapon.ini only.\n"
    + a2a("VietnamJetMig29S_WpnRadar", 95.0, 720.0, 6, 900, "R77_Object", 16000)
    + a2a("VietnamJetMig29S_WpnIR", 70.0, 420.0, 4, 600, "AIM-9X_Object", 12000)
    + cannon("VietnamJetMig29S_WpnGun", 42.0, 40, 180, 360.0)
    + a2a("Japan_Weapon_AAM4B_F15JStd", 88.0, 680.0, 4, 1100, "MeteorMissile_Object", 15000)
    + j10_bomb6()
    + cannon("IraqJetMig25RB_WpnGun", 36.0, 30, 220, 300.0)
)


def write_objects() -> list[Path]:
    written = []
    items = [
        (
            VN / "VietnamJetMig29S.ini",
            fighter(
                "VietnamJetMig29S",
                "Vietnam",
                "irq_mig29a",
                "LSFruMiG29",
                "LSFruMiG29d",
                "LSFruMiG29k",
                wset(
                    "VietnamJetMig29S_WpnRadar",
                    "VietnamJetMig29S_WpnIR",
                    "VietnamJetMig29S_WpnGun",
                    "AIRCRAFT",
                    "AIRCRAFT",
                    "AIRCRAFT VEHICLE",
                ),
                2200,
                15.0,
                480,
                0.90,
                700.0,
                "VPAF MiG-29 interceptor. Donor ART LSFruMiG29.",
            ),
        ),
        (
            VN / "VietnamJetIL76.ini",
            transport_jet(
                "VietnamJetIL76",
                "Vietnam",
                "yier76",
                "Iraq_IL-76",
                "Iraq_IL-76",
                "Iraq_IL-76",
                "VPAF playable IL-76. C-130-class runway transport.",
                0.95,
                32,
                2600,
                860,
            ),
        ),
        (
            IQ / "IraqJetIL76.ini",
            transport_jet(
                "IraqJetIL76",
                "Iraq",
                "yier76",
                "Iraq_IL-76",
                "Iraq_IL-76",
                "Iraq_IL-76",
                "Iraq playable IL-76 wrapper. Does not replace science paradrop object.",
                0.95,
                32,
                2600,
                860,
            ),
        ),
        (
            INI / "Object/Specter/Shared/SpecterPlayableIL76.ini",
            transport_jet(
                "SpecterPlayableIL76",
                "Iraq",
                "yier76",
                "RUS_IL76MD90A",
                "RUS_IL76MD90A",
                "RUS_IL76MD90A",
                "Shared playable IL-76 for non-protected airbases.",
                0.95,
                32,
                2600,
                860,
            ),
        ),
        (
            IQ / "IraqJetMig25RB.ini",
            fighter(
                "IraqJetMig25RB",
                "Iraq",
                "irq_mig25",
                "Iraq_Mig-25bm",
                "Iraq_Mig-25bm",
                "Iraq_Mig-25bm",
                wset(
                    "IraqJetMig25RB_WpnLT3",
                    "IraqJetMig25RB_WpnGun",
                    "IraqJetMig25RB_WpnGun",
                    "VEHICLE STRUCTURE",
                    "VEHICLE INFANTRY",
                    "AIRCRAFT VEHICLE",
                ),
                2100,
                14.0,
                520,
                1.05,
                640.0,
                "MiG-25RB playable high-speed strike. Six J-10 family bombs.",
                "R15BF2-300JetLocomotor",
                "Yes",
                "Yes",
            ),
        ),
        (
            KR / "SouthKoreaJetAH64E.ini",
            helo(
                "SouthKoreaJetAH64E",
                "SouthKorea",
                "Nat_ah64e",
                "US_AH64E",
                "US_AH64E.US_AH64E",
                "ROK AH-64E. NATO Apache visual. No USA object replace.",
                0.90,
                "TRANSPORT",
                "T700_GE_701D_B2",
                2,
                1800,
                520,
                True,
                apache_weapons(),
                "GenericAttackHelicopterHoverCommandSet",
            ),
        ),
        (
            KR / "SouthKoreaJetCH47.ini",
            helo(
                "SouthKoreaJetCH47",
                "SouthKorea",
                "Nat_ch47",
                "US_CH47F",
                "US_CH47F.US_CH47F",
                "ROK CH-47D/F transport. Distinct from Japan C-130.",
                0.88,
                "TRANSPORT",
                "ChinookLocomotor",
                16,
                1600,
                560,
                False,
                "",
                "AmericaVehicleChinookCommandSet",
            ),
        ),
        (
            KR / "SouthKoreaJetUH60P.ini",
            helo(
                "SouthKoreaJetUH60P",
                "SouthKorea",
                "us_uh60",
                "US_UH60",
                "US_UH60.US_UH60",
                "ROK UH-60P Black Hawk utility helicopter.",
                0.86,
                "TRANSPORT",
                "ChinookLocomotor",
                10,
                1300,
                420,
                False,
                "",
                "AmericaVehicleChinookCommandSet",
            ),
        ),
        (KR / "SouthKoreaJetE737.ini", e737_ini()),
        (
            KR / "SouthKoreaJetC130H.ini",
            transport_jet(
                "SouthKoreaJetC130H",
                "SouthKorea",
                "SPEC_JapanC130H",
                "US_C130H",
                "US_C130H",
                "US_C130H",
                "ROKAF C-130H. US_C130H visual, not Japan AVCargoPln.",
                1.02,
                24,
                2200,
                680,
            ),
        ),
        (
            VN / "VietnamJetMi8.ini",
            helo(
                "VietnamJetMi8",
                "Vietnam",
                "rus_mi17",
                "Irq_Mi8T",
                "Irq_Mi8T.Irq_Mi8T",
                "VPAF Mi-8 utility helicopter.",
                0.90,
                "TRANSPORT",
                "ChinookLocomotor",
                12,
                1100,
                400,
                False,
                "",
                "AmericaVehicleChinookCommandSet",
            ),
        ),
        (
            VN / "VietnamJetMi17.ini",
            helo(
                "VietnamJetMi17",
                "Vietnam",
                "rus_mi17",
                "Egy_MI17",
                None,
                "VPAF Mi-17. Animation omitted until W3D anim is proven.",
                0.92,
                "TRANSPORT",
                "ChinookLocomotor",
                14,
                1250,
                440,
                False,
                "",
                "AmericaVehicleChinookCommandSet",
            ),
        ),
    ]
    for path, text in items:
        w(path, text)
        written.append(path)
    return written


def main() -> None:
    paths = write_objects()
    print("wrote", len(paths), "object INIs")


if __name__ == "__main__":
    main()
