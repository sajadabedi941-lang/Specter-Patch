#!/usr/bin/env python3
"""Write France air-force overlay INI (ASCII, LF). Source of truth for the rebuild."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/workspace/patch/Data")
AIR = ROOT / "INI/Object/Specter/French Armed Forces/Airforce"
ROT = ROOT / "INI/Object/Specter/French Armed Forces/Rotary"
BLD = ROOT / "INI/Object/Specter/French Armed Forces/Buildings"
INI = ROOT / "INI"
MAP = ROOT / "INI/MappedImages/HandCreated"
ENG = ROOT / "English"


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\r\n", "\n").replace("\r", "\n")
    if not data.endswith("\n"):
        data += "\n"
    path.write_bytes(data.encode("ascii"))


FIGHTER_DRAW = """  Draw = W3DModelDraw ModuleTag_01

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

FIGHTER_TAIL = """  RadarPriority          = UNIT
  KindOf                 = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT
  Body                   = ActiveBody ModuleTag_02
    MaxHealth            = {hp}.0
    InitialHealth        = {hp}.0
  End
  Behavior                = ArmorUpgrade ModuleTag_Armor01x2
    TriggeredBy           = Upgrade_AmericaCountermeasures
  End
  Behavior                = CountermeasuresBehavior ModuleTag_10
    TriggeredBy           = Upgrade_AmericaCountermeasures
    FlareTemplateName     = CountermeasureFlare
    FlareBoneBaseName     = Flare
    VolleySize            = 2
    VolleyArcAngle        = 96.0
    VolleyVelocityFactor  = 3.0
    DelayBetweenVolleys   = 1000
    NumberOfVolleys       = 4
    ReloadTime            = 0
    EvasionRate           = 35%
    ReactionLaunchLatency = 0
    MissileDecoyDelay     = 200
  End
  Behavior = ProductionUpdate ModuleTag_SelfUp
  End
  Behavior                          = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath                 = FX_JetOnGroundDeath
    OCLOnGroundDeath                = OCL_RaptorDeathFinalBlowUp
    DestructionDelay                = 99999999
    RollRate                        = 0.2
    RollRateDelta                   = 100%
    PitchRate                       = 0.0
    FallHowFast                     = 110.0%
    FXInitialDeath                  = FX_RaptorDeathInitial
    OCLInitialDeath                 = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath  = 500
    FXSecondary                     = FX_JetDeathSecondary
    OCLSecondary                    = OCL_RaptorDeathSecondary
    FXHitGround                     = FX_JetDeathHitGround
    OCLHitGround                    = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround   = 200
    FXFinalBlowUp                   = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp                  = OCL_RaptorDeathFinalBlowUp
  End
  Behavior = CreateObjectDie ModuleTag_Deletion
    DeathTypes   = NONE +EXTRA_6
    CreationList = None
  End
  Behavior                    = EjectPilotDie ModuleTag_06
    ExemptStatus         = HIJACKED
    GroundCreationList = OCL_EjectPilotOnGround
    AirCreationList = OCL_EjectPilotViaParachute
    VeterancyLevels =  ALL -REGULAR
  End
  Behavior               = PhysicsBehavior ModuleTag_07
    Mass                 = 500.0
  End
  Behavior                 = TransitionDamageFX ModuleTag_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes Psys:SmokeSmallContinuous01
    ReallyDamagedFXList1         = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End
  Behavior = JetAIUpdate ModuleTag_09ai
    OutOfAmmoDamagePerSecond  = 0%
    TakeoffDistForMaxLift     = 0%
    TakeoffPause              = 500
    MinHeight                 = 5
    ParkingOffset             = 3
    ReturnToBaseIdleTime      = 10000
    AutoAcquireEnemiesWhenIdle = Yes
  End
  Locomotor = SET_NORMAL {loco}
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor

  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End

  Behavior = FireWeaponWhenDamagedBehavior ModuleTag_RS
    StartsActive                = Yes
    ReactionWeaponPristine      = RadarWaveEmitter
    ReactionWeaponDamaged       = RadarWaveEmitter
    ReactionWeaponReallyDamaged = RadarWaveEmitter
    ReactionWeaponRubble        = RadarWaveEmitter
    DamageTypes                 = NONE +MICROWAVE
  End

  Geometry                 = Box
  GeometryIsSmall          = Yes
  GeometryMajorRadius      = 14.0
  GeometryMinorRadius      = 7.0
  GeometryHeight           = 5.0
  Shadow                   = SHADOW_VOLUME
  ShadowSizeX = 89

End
"""


def fighter(
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
    loco: str,
    display: str,
) -> str:
    return (
        f"; SPECTER - France {display}. Donor ART {model}.W3D. Unique object ID.\n"
        f"Object {obj}\n"
        f"Scale = {scale:.2f}\n"
        f"\n"
        f"  SelectPortrait         = {portrait}\n"
        f"  ButtonImage            = {portrait}\n"
        f"  UpgradeCameo1 = Upgrade_AmericaCountermeasures\n"
        f"\n"
        + FIGHTER_DRAW.format(model=model, model_d=model_d, model_k=model_k)
        + f"\n"
        f"  DisplayName         = OBJECT:{obj}\n"
        f"  EditorSorting       = VEHICLE\n"
        f"  Side                = France\n"
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
        f"  CommandSet              = {cmd}\n"
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
        + FIGHTER_TAIL.format(hp=hp, loco=loco)
    )


def wpn_set(lines: list[str]) -> str:
    body = "  WeaponSet\n    Conditions = None\n"
    for line in lines:
        body += f"    {line}\n"
    body += "  End\n"
    return body


def main() -> None:
    jets = [
        dict(
            file="FranceJetRafaleC.ini",
            obj="FranceJetRafaleC",
            portrait="SPEC_FranceRafaleC",
            model="LSFRafale",
            model_d="LSFRafaled",
            model_k="LSFRafalek",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_Meteor_RafaleC",
                    "PreferredAgainst    = PRIMARY    AIRCRAFT",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_MICA_RafaleC",
                    "PreferredAgainst    = SECONDARY  AIRCRAFT",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   AIRCRAFT VEHICLE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="F22A_AA_CommandSet",
            cost=2800,
            time=16.0,
            hp=540,
            scale=0.95,
            vision=700.0,
            loco="Snecma_M88_4E",
            display="Rafale C F4",
        ),
        dict(
            file="FranceJetRafaleB.ini",
            obj="FranceJetRafaleB",
            portrait="SPEC_FranceRafaleB",
            model="LSFRafale",
            model_d="LSFRafaled",
            model_k="LSFRafalek",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_SCALP_RafaleB",
                    "PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_MICA_RafaleB",
                    "PreferredAgainst    = SECONDARY  AIRCRAFT",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   INFANTRY VEHICLE STRUCTURE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="GenericTacticalBomberCommandSet",
            cost=2900,
            time=17.0,
            hp=550,
            scale=0.95,
            vision=620.0,
            loco="Snecma_M88_4E",
            display="Rafale B",
        ),
        dict(
            file="FranceJetRafaleM.ini",
            obj="FranceJetRafaleM",
            portrait="SPEC_FranceRafaleM",
            model="LSFRafaleAS",
            model_d="LSFRafaleASd",
            model_k="LSFRafaleASd",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_Exocet_RafaleM",
                    "PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_MICA_RafaleM",
                    "PreferredAgainst    = SECONDARY  AIRCRAFT",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   INFANTRY VEHICLE STRUCTURE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="GenericTacticalBomberCommandSet",
            cost=3000,
            time=17.5,
            hp=560,
            scale=0.95,
            vision=640.0,
            loco="Snecma_M88_4E",
            display="Rafale M",
        ),
        dict(
            file="FranceJetMirage2000.ini",
            obj="FranceJetMirage2000",
            portrait="SPEC_FranceMirage2000",
            model="LSFMirage2000",
            model_d="LSFMirage2000d",
            model_k="LSFMirage2000k",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_AAM_Mirage2000",
                    "PreferredAgainst    = PRIMARY    AIRCRAFT",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_MICA_Mirage2000",
                    "PreferredAgainst    = SECONDARY  AIRCRAFT",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   AIRCRAFT VEHICLE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="F22A_AA_CommandSet",
            cost=1800,
            time=14.0,
            hp=480,
            scale=0.90,
            vision=580.0,
            loco="Snecma_M88_4E",
            display="Mirage 2000",
        ),
        dict(
            file="FranceJetMirage2000D.ini",
            obj="FranceJetMirage2000D",
            portrait="SPEC_FranceMirage2000D",
            model="LSFMirage2KD",
            model_d="LSFMirage2KDd",
            model_k="LSFMirage2KDk",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_SCALP_Mirage2000D",
                    "PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_AASM_Mirage2000D",
                    "PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   INFANTRY VEHICLE STRUCTURE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="GenericTacticalBomberCommandSet",
            cost=1900,
            time=15.0,
            hp=490,
            scale=0.90,
            vision=560.0,
            loco="Snecma_M88_4E",
            display="Mirage 2000D",
        ),
        dict(
            file="FranceJetMirageF1CT.ini",
            obj="FranceJetMirageF1CT",
            portrait="SPEC_FranceMirageF1CT",
            model="LSFFRF1",
            model_d="LSFFRF1d",
            model_k="LSFFRF1k",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_AAM_MirageF1CT",
                    "PreferredAgainst    = PRIMARY    AIRCRAFT",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_Bomb_MirageF1CT",
                    "PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   INFANTRY VEHICLE STRUCTURE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="GenericTacticalBomberCommandSet",
            cost=1400,
            time=12.0,
            hp=420,
            scale=0.85,
            vision=500.0,
            loco="Snecma_M88_4E",
            display="Mirage F1CT",
        ),
        dict(
            file="FranceJetMirageIIIE.ini",
            obj="FranceJetMirageIIIE",
            portrait="SPEC_FranceMirageIIIE",
            model="LSFMirage3",
            model_d="LSFMirage3d",
            model_k="LSFMirage3k",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_AAM_MirageIIIE",
                    "PreferredAgainst    = PRIMARY    AIRCRAFT",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_Bomb_MirageIIIE",
                    "PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   INFANTRY VEHICLE STRUCTURE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="GenericTacticalBomberCommandSet",
            cost=1200,
            time=11.0,
            hp=400,
            scale=0.85,
            vision=480.0,
            loco="Snecma_M88_4E",
            display="Mirage IIIE",
        ),
        dict(
            file="FranceJetMirage5.ini",
            obj="FranceJetMirage5",
            portrait="SPEC_FranceMirage5",
            model="LSFMirage5",
            model_d="LSFMirage5d",
            model_k="LSFMirage5k",
            weapons=wpn_set(
                [
                    "Weapon              = PRIMARY    France_Weapon_Bomb_Mirage5",
                    "PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE",
                    "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = SECONDARY  France_Weapon_AAM_Mirage5",
                    "PreferredAgainst    = SECONDARY  AIRCRAFT",
                    "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
                    "Weapon              = TERTIARY   France_Weapon_Cannon_Jet",
                    "PreferredAgainst    = TERTIARY   INFANTRY VEHICLE STRUCTURE",
                    "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
                ]
            ),
            cmd="GenericTacticalBomberCommandSet",
            cost=1100,
            time=10.5,
            hp=390,
            scale=0.85,
            vision=460.0,
            loco="Snecma_M88_4E",
            display="Mirage 5",
        ),
    ]
    for spec in jets:
        file = spec.pop("file")
        w(AIR / file, fighter(**spec))

    w(
        AIR / "FranceJetC130.ini",
        """; SPECTER - France C-130 Hercules. Donor LSFUSAC130.W3D.
Object FranceJetC130
Scale = 1.00

  SelectPortrait         = SPEC_FranceC130
  ButtonImage            = SPEC_FranceC130

  Draw = W3DModelDraw ModuleTag_C130_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = LSFUSAC130
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = LSFUSAC130
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = LSFUSAC130d
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = REALLYDAMAGED JETEXHAUST
      Model = LSFUSAC130d
      ParticleSysBone = SMOKE01 JetSmoke
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
    End
    ConditionState = RUBBLE
      Model = LSFUSAC130k
    End
  End

  DisplayName = OBJECT:FranceJetC130
  EditorSorting = VEHICLE
  Side = France
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 300
  BuildCost = 2400
  BuildTime = 28.0
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
    MaxHealth = 700.0
    InitialHealth = 700.0
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
    Mass = 700.0
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
  Locomotor = SET_NORMAL D30-F6_JetLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Behavior = FlammableUpdate ModuleTag_C130_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior = TransportContain ModuleTag_C130_Cargo
    Slots                 = 24
    DamagePercentToUnits  = 100%
    AllowInsideKindOf     = INFANTRY VEHICLE
    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE
    ExitDelay             = 100
    NumberOfExitPaths     = 1
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 36.0
  GeometryMinorRadius = 12.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )

    w(
        AIR / "FranceAircraftE3.ini",
        """; SPECTER - France E-3 AWACS. Donor E3.W3D. Player-built heavy airbase unit.
Object FranceAircraftE3
Scale = 0.90

  SelectPortrait         = SPEC_FranceE3
  ButtonImage            = SPEC_FranceE3

  Draw = W3DModelDraw ModuleTag_E3_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = E3
      Animation = E3.E3
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = E3
      Animation = E3.E3
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = E3
      Animation = E3.E3
      AnimationMode = LOOP
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = RUBBLE
      Model = E3
    End
  End

  DisplayName = OBJECT:FranceAircraftE3
  EditorSorting = VEHICLE
  Side = France
  TransportSlotCount = 0
  VisionRange = 1100
  ShroudClearingRange = 1200
  BuildCost = 4200
  BuildTime = 36.0
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
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT REVEALS_ENEMY_PATHS
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  Body = ActiveBody ModuleTag_E3_02
    MaxHealth = 1100.0
    InitialHealth = 1100.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_E3_05
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
  Behavior = PhysicsBehavior ModuleTag_E3_07
    Mass = 600.0
  End
  Behavior = TransitionDamageFX ModuleTag_E3_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End
  Behavior = JetAIUpdate ModuleTag_E3_09
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
  Behavior = FlammableUpdate ModuleTag_E3_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior = StealthDetectorUpdate ModuleTag_E3_Detect
    DetectionRate = 1500
    DetectionRange = 3600
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End
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

    w(
        ROT / "FranceHelicopterNH90.ini",
        """; SPECTER - France NH90 Caiman. Donor LSFFRNH90.W3D.
Object FranceHelicopterNH90
Scale = 0.90

  SelectPortrait         = SPEC_FranceNH90
  ButtonImage            = SPEC_FranceNH90

  Draw = W3DModelDraw ModuleTag_NH90_01
    ExtraPublicBone = RopeStart
    ExtraPublicBone = RopeEnd
    DefaultConditionState
      Model = LSFFRNH90
      Animation = LSFFRNH90.LSFFRNH90
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model = LSFFRNH90
      Animation = LSFFRNH90.LSFFRNH90
      AnimationMode = LOOP
    End
    ConditionState = RUBBLE
      Model = LSFFRNH90
    End
    OkToChangeModelColor = Yes
  End

  DisplayName = OBJECT:FranceHelicopterNH90
  EditorSorting = VEHICLE
  Side = France
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 180.0
  BuildCost = 1600
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
    VoiceSupply = ChinookVoiceSupply
    VoiceUnload = ChinookVoiceUnload
    VoiceCombatDrop = ChinookVoiceCombatDrop
    VoiceGarrison = ChinookVoiceMove
  End

  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT HARVESTER SCORE PRODUCED_AT_HELIPAD
  Body = ActiveBody ModuleTag_NH90_03
    MaxHealth = 320.0
    InitialHealth = 320.0
  End
  Behavior = FXListDie ModuleTag_NH90_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = TransitionDamageFX ModuleTag_NH90_06
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuousDown
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_ComancheDamageTransition
  End
  Behavior = ChinookAIUpdate ModuleTag_NH90_07
    MaxBoxes = 6
    SupplyCenterActionDelay = 2900
    SupplyWarehouseActionDelay = 1200
    SupplyWarehouseScanDistance = 700
    SuppliesDepletedVoice = ChinookVoiceSuppliesDepleted
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
    MinDropHeight = 40
    UpgradedSupplyBoost = 60
  End
  Locomotor = SET_NORMAL ChinookLocomotor
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = TransportContain ModuleTag_NH90_08
    Slots = 8
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

    w(
        ROT / "FranceHelicopterCaracal.ini",
        """; SPECTER - France Caracal EC725. Appearance donor LSFRUMi171.W3D (no EC725 mesh).
; Gameplay name is Caracal EC725. Heavy troop transport / special operations.
Object FranceHelicopterCaracal
Scale = 0.95

  SelectPortrait         = SPEC_FranceCaracal
  ButtonImage            = SPEC_FranceCaracal

  Draw = W3DModelDraw ModuleTag_Caracal_01
    ExtraPublicBone = RopeStart
    ExtraPublicBone = RopeEnd
    DefaultConditionState
      Model = LSFRUMi171
      Animation = LSFRUMI171.LSFRUMI171
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model = LSFRUMi171d
      Animation = LSFRUMI171D.LSFRUMI171D
      AnimationMode = LOOP
    End
    ConditionState = RUBBLE
      Model = LSFRUMi171k
    End
    OkToChangeModelColor = Yes
  End

  DisplayName = OBJECT:FranceHelicopterCaracal
  EditorSorting = VEHICLE
  Side = France
  TransportSlotCount = 0
  VisionRange = 320.0
  ShroudClearingRange = 200.0
  BuildCost = 2000
  BuildTime = 15.0
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
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD
  Body = ActiveBody ModuleTag_Caracal_03
    MaxHealth = 420.0
    InitialHealth = 420.0
  End
  Behavior = FXListDie ModuleTag_Caracal_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = TransitionDamageFX ModuleTag_Caracal_06
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuousDown
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_ComancheDamageTransition
  End
  Behavior = ChinookAIUpdate ModuleTag_Caracal_07
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
    MinDropHeight = 40
  End
  Locomotor = SET_NORMAL ChinookLocomotor
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = TransportContain ModuleTag_Caracal_08
    Slots = 12
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY VEHICLE
    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE
    ExitDelay = 100
    NumberOfExitPaths = 1
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 22.0
  GeometryMinorRadius = 9.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )

    w(
        ROT / "FranceHelicopterTiger.ini",
        """; SPECTER - France Tiger HAD. Donor LSFFRTiger.W3D.
Object FranceHelicopterTiger
Scale = 0.88

  SelectPortrait         = SPEC_FranceTiger
  ButtonImage            = SPEC_FranceTiger
  UpgradeCameo1 = Upgrade_AmericaCountermeasures

  Draw = W3DModelDraw ModuleTag_Tiger_01
    DefaultConditionState
      Model = LSFFRTiger
      Animation = LSFFRTIGER.LSFFRTIGER
      AnimationMode = LOOP
      WeaponFireFXBone = PRIMARY Weapon01
      WeaponLaunchBone = PRIMARY Weapon01
      WeaponFireFXBone = SECONDARY Weapon01
      WeaponLaunchBone = SECONDARY Weapon01
      WeaponFireFXBone = TERTIARY Weapon01
      WeaponLaunchBone = TERTIARY Weapon01
    End
    ConditionState = REALLYDAMAGED
      Model = LSFFRTigerd
      Animation = LSFFRTIGERD.LSFFRTIGERD
      AnimationMode = LOOP
      WeaponFireFXBone = PRIMARY Weapon01
      WeaponLaunchBone = PRIMARY Weapon01
      WeaponFireFXBone = SECONDARY Weapon01
      WeaponLaunchBone = SECONDARY Weapon01
      WeaponFireFXBone = TERTIARY Weapon01
      WeaponLaunchBone = TERTIARY Weapon01
    End
    ConditionState = RUBBLE
      Model = LSFFRTigerk
    End
    OkToChangeModelColor = Yes
  End

  DisplayName = OBJECT:FranceHelicopterTiger
  EditorSorting = VEHICLE
  Side = France
  TransportSlotCount = 0
  VisionRange = 280.0
  ShroudClearingRange = 180.0
  BuildCost = 1700
  BuildTime = 13.0
  ExperienceValue = 50 50 100 150
  ExperienceRequired = 0 100 200 400
  IsTrainable = Yes
  CommandSet = GenericAttackHelicopterHoverCommandSet
  WeaponSet
    Conditions = None
    Weapon = PRIMARY France_Weapon_Cannon_Tiger
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY France_Weapon_ATGM_Tiger
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY France_Weapon_Rocket_Tiger
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
  Body = ActiveBody ModuleTag_Tiger_02
    MaxHealth = 280.0
    InitialHealth = 280.0
  End
  Behavior = FXListDie ModuleTag_Tiger_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = TransitionDamageFX ModuleTag_Tiger_06
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuousDown
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_ComancheDamageTransition
  End
  Behavior = JetAIUpdate ModuleTag_Tiger_07
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
  Behavior = PhysicsBehavior ModuleTag_Tiger_08
    Mass = 50.0
  End
  Behavior = FlammableUpdate ModuleTag_Tiger_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
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

    print("wrote aircraft objects")


if __name__ == "__main__":
    main()
