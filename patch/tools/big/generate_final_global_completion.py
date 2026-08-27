#!/usr/bin/env python3
"""Write final global donor-reuse + UAV completion overlay (ASCII, LF). ART visual only."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_global_donor_airforce as g

ROOT = Path("/workspace/patch/Data")
INI = ROOT / "INI"
MAP = INI / "MappedImages/HandCreated"

DRAW = g.DRAW
wset = g.wset
a2a = g.a2a
a2g = g.a2g
rockets = g.rockets
cannon = g.cannon
w = g.w
METEOR = g.METEOR
AIM9 = g.AIM9
R77 = g.R77
GBU = g.GBU
FAB = g.FAB
CRUISE = g.CRUISE
KH31 = g.KH31
PAVE = g.PAVE
AGM = g.AGM


STEALTH = """  Behavior = StealthUpdate ModuleTag_StealthInnate
    StealthDelay                          = 2600
    StealthForbiddenConditions            = FIRING_PRIMARY FIRING_SECONDARY
    FriendlyOpacityMin                    = 50.0%
    FriendlyOpacityMax                    = 100.0%
    InnateStealth                         = Yes
    OrderIdleEnemiesToAttackMeUponReveal  = Yes
  End
"""

DETECT = """  Behavior = StealthDetectorUpdate ModuleTag_DetectUAV
    DetectionRate = {rate}
    DetectionRange = {rng}
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End
"""


def jet(
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
    commandset: str = "F22A_AA_CommandSet",
    shroud: float = 220.0,
    kindof: str = "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT",
    extras: str = "",
    needs_runway: str = "",
    locomotor: str = "Snecma_M88_4E",
    geom: tuple = (14.0, 7.0, 5.0, "Yes"),
    mass: float = 500.0,
) -> str:
    runway = ("    NeedsRunway             = " + needs_runway + "\n") if needs_runway else ""
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
        f"  ShroudClearingRange = {shroud:.1f}\n"
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
        f"  CommandSet              = {commandset}\n"
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
        f"  KindOf                 = {kindof}\n"
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
        f"{extras}"
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
        f"    Mass                 = {mass:.1f}\n"
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
        f"{runway}"
        f"    ReturnToBaseIdleTime      = 10000\n"
        f"    AutoAcquireEnemiesWhenIdle = Yes\n"
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
        f"  GeometryIsSmall          = {geom[3]}\n"
        f"  GeometryMajorRadius      = {geom[0]:.1f}\n"
        f"  GeometryMinorRadius      = {geom[1]:.1f}\n"
        f"  GeometryHeight           = {geom[2]:.1f}\n"
        f"  Shadow                   = SHADOW_VOLUME\n"
        f"  ShadowSizeX = 89\n"
        f"\n"
        f"End\n"
    )


def transport(obj, side, portrait, model, model_d, model_k, cost, time, hp, scale, note) -> str:
    return (
        f"; SPECTER - {note}\n"
        f"Object {obj}\n"
        f"Scale = {scale:.2f}\n"
        f"\n"
        f"  SelectPortrait         = {portrait}\n"
        f"  ButtonImage            = {portrait}\n"
        f"\n"
        f"  Draw = W3DModelDraw ModuleTag_C130_01\n"
        f"    OkToChangeModelColor = Yes\n"
        f"    DefaultConditionState\n"
        f"      Model = {model}\n"
        f"      ParticleSysBone = ENGINE01 JetBlackTrailThin\n"
        f"      ParticleSysBone = ENGINE02 JetBlackTrailThin\n"
        f"      ParticleSysBone = ENGINE03 JetBlackTrailThin\n"
        f"      ParticleSysBone = ENGINE04 JetBlackTrailThin\n"
        f"    End\n"
        f"    ConditionState = JETEXHAUST\n"
        f"      Model = {model}\n"
        f"      ParticleSysBone = ENGINE01 JetBlackTrailThin\n"
        f"      ParticleSysBone = ENGINE02 JetBlackTrailThin\n"
        f"      ParticleSysBone = ENGINE03 JetBlackTrailThin\n"
        f"      ParticleSysBone = ENGINE04 JetBlackTrailThin\n"
        f"    End\n"
        f"    ConditionState = REALLYDAMAGED\n"
        f"      Model = {model_d}\n"
        f"      ParticleSysBone = SMOKE01 JetSmoke\n"
        f"    End\n"
        f"    ConditionState = REALLYDAMAGED JETEXHAUST\n"
        f"      Model = {model_d}\n"
        f"      ParticleSysBone = SMOKE01 JetSmoke\n"
        f"      ParticleSysBone = ENGINE01 JetBlackTrailThin\n"
        f"      ParticleSysBone = ENGINE02 JetBlackTrailThin\n"
        f"    End\n"
        f"    ConditionState = RUBBLE\n"
        f"      Model = {model_k}\n"
        f"    End\n"
        f"  End\n"
        f"\n"
        f"  DisplayName = OBJECT:{obj}\n"
        f"  EditorSorting = VEHICLE\n"
        f"  Side = {side}\n"
        f"  TransportSlotCount = 0\n"
        f"  VisionRange = 300.0\n"
        f"  ShroudClearingRange = 300.0\n"
        f"  BuildCost = {cost}\n"
        f"  BuildTime = {time:.1f}\n"
        f"  ExperienceValue = 50 50 100 150\n"
        f"  IsTrainable = No\n"
        f"  CommandSet = C17GlobalMasterCommandSet\n"
        f"  VoiceSelect = RaptorVoiceSelect\n"
        f"  VoiceMove = RaptorVoiceMove\n"
        f"  VoiceGuard = RaptorVoiceAirPatrol\n"
        f"  SoundAmbient = AdvancedFightEngineLoop\n"
        f"  SoundAmbientRubble = NoSound\n"
        f"  UnitSpecificSounds\n"
        f"    VoiceCreate = RaptorVoiceCreate\n"
        f"    SoundEject = PilotSoundEject\n"
        f"    VoiceEject = PilotVoiceEject\n"
        f"    Afterburner = RaptorAfterburner\n"
        f"    VoiceLowFuel = RaptorVoiceLowFuel\n"
        f"    VoiceGarrison = RaptorVoiceMove\n"
        f"  End\n"
        f"  RadarPriority = UNIT\n"
        f"  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT\n"
        f"  ArmorSet\n"
        f"    Conditions = None\n"
        f"    Armor = AirplaneArmor\n"
        f"    DamageFX = None\n"
        f"  End\n"
        f"  Body = ActiveBody ModuleTag_C130_02\n"
        f"    MaxHealth = {hp}.0\n"
        f"    InitialHealth = {hp}.0\n"
        f"  End\n"
        f"  Behavior = JetSlowDeathBehavior ModuleTag_C130_05\n"
        f"    FXOnGroundDeath = FX_JetOnGroundDeath\n"
        f"    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp\n"
        f"    DestructionDelay = 99999999\n"
        f"    RollRate = 0.2\n"
        f"    RollRateDelta = 100%\n"
        f"    PitchRate = 0.0\n"
        f"    FallHowFast = 110.0%\n"
        f"    FXInitialDeath = FX_RaptorDeathInitial\n"
        f"    OCLInitialDeath = OCL_RaptorDeathInitial\n"
        f"    DelaySecondaryFromInitialDeath = 500\n"
        f"    FXSecondary = FX_JetDeathSecondary\n"
        f"    OCLSecondary = OCL_RaptorDeathSecondary\n"
        f"    FXHitGround = FX_JetDeathHitGround\n"
        f"    OCLHitGround = OCL_RaptorDeathHitGround\n"
        f"    DelayFinalBlowUpFromHitGround = 200\n"
        f"    FXFinalBlowUp = FX_JetDeathFinalBlowUp\n"
        f"    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp\n"
        f"  End\n"
        f"  Behavior = PhysicsBehavior ModuleTag_C130_07\n"
        f"    Mass = 700.0\n"
        f"  End\n"
        f"  Behavior = TransitionDamageFX ModuleTag_C130_08\n"
        f"    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01\n"
        f"    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition\n"
        f"  End\n"
        f"  Behavior = JetAIUpdate ModuleTag_C130_09\n"
        f"    KeepsParkingSpaceWhenAirborne = Yes\n"
        f"    MinHeight = 1\n"
        f"    NeedsRunway = Yes\n"
        f"    OutOfAmmoDamagePerSecond = 0%\n"
        f"    ReturnToBaseIdleTime = 10000\n"
        f"    TakeoffPause = 1000\n"
        f"    TakeoffDistForMaxLift = 0%\n"
        f"    AutoAcquireEnemiesWhenIdle = No\n"
        f"    ParkingOffset = 5\n"
        f"  End\n"
        f"  Locomotor = SET_NORMAL D30-F6_JetLocomotor\n"
        f"  Locomotor = SET_TAXIING BasicJetTaxiLocomotor\n"
        f"  Behavior = FlammableUpdate ModuleTag_C130_21\n"
        f"    AflameDuration = 5000\n"
        f"    AflameDamageAmount = 3\n"
        f"    AflameDamageDelay = 500\n"
        f"  End\n"
        f"  Behavior = TransportContain ModuleTag_C130_Cargo\n"
        f"    Slots                 = 24\n"
        f"    DamagePercentToUnits  = 100%\n"
        f"    AllowInsideKindOf     = INFANTRY VEHICLE\n"
        f"    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE\n"
        f"    ExitDelay             = 100\n"
        f"    NumberOfExitPaths     = 1\n"
        f"  End\n"
        f"  Geometry = Box\n"
        f"  GeometryIsSmall = No\n"
        f"  GeometryMajorRadius = 36.0\n"
        f"  GeometryMinorRadius = 12.0\n"
        f"  GeometryHeight = 10.0\n"
        f"  Shadow = SHADOW_VOLUME\n"
        f"  ShadowSizeX = 89\n"
        f"End\n"
    )


def wset2(pri: str, sec: str, pri_vs: str, sec_vs: str) -> str:
    return (
        "  WeaponSet\n"
        "    Conditions = None\n"
        f"    Weapon              = PRIMARY    {pri}\n"
        f"    PreferredAgainst    = PRIMARY    {pri_vs}\n"
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        f"    Weapon              = SECONDARY  {sec}\n"
        f"    PreferredAgainst    = SECONDARY  {sec_vs}\n"
        "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "  End\n"
    )


WEAPONS = "\n".join(
    [
        "; SPECTER final global completion weapons. Wrappers over packed projectiles.",
        a2g("Germany_Weapon_EuroMALE_PGM", 520, 22, 720, 4, 1600, PAVE, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1800),
        a2g("France_Weapon_Neuron_AASM", 640, 26, 780, 2, 2200, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 2000),
        a2a("Germany_Weapon_FCAS_Meteor", 880, 1280, 4, 900, METEOR),
        a2g("Germany_Weapon_FCAS_PGM", 720, 28, 800, 2, 1800, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1600),
        a2a("France_Weapon_F1CR_MICA", 700, 920, 2, 850, METEOR),
        a2a("France_Weapon_F1CR_IR", 620, 480, 2, 680, AIM9),
        a2g("France_Weapon_F1CR_Bomb", 680, 32, 680, 4, 500, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        a2a("France_Weapon_RafaleF4_Meteor", 980, 1560, 6, 820, METEOR),
        a2a("France_Weapon_RafaleF4_MICA", 820, 780, 4, 700, METEOR),
        a2g("France_Weapon_RafaleF4_AASM", 860, 30, 820, 4, 1100, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1400),
        a2g("Britain_Weapon_TornadoECR_HARM", 1100, 48, 1400, 4, 2400, KH31, "Grad_launch", "FX_MediumMissileIgnition", "FX_HE_UnguidedMissileDetonation", 1600),
        a2a("Britain_Weapon_TornadoECR_IR", 640, 500, 2, 700, AIM9),
        a2g("Britain_Weapon_TornadoECR_PGM", 820, 30, 780, 4, 1000, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1200),
        a2a("China_Weapon_PL15_J35A", 980, 1500, 6, 880, R77),
        a2a("China_Weapon_PL10_J35A", 800, 620, 2, 660, AIM9),
        a2g("China_Weapon_LS6_J35A", 840, 28, 800, 2, 1600, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1800),
        a2a("Iran_Weapon_R60_Mig21", 520, 420, 2, 750, AIM9),
        a2g("Iran_Weapon_Bomb_Mig21", 540, 28, 560, 2, 600, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        cannon("Iran_Weapon_Cannon_Mig21", 20),
        a2a("Iran_Weapon_R77_Su35", 940, 1480, 8, 800, R77),
        a2a("Iran_Weapon_R73_Su35", 760, 560, 2, 680, AIM9),
        a2g("Iran_Weapon_KH31_Su35", 1200, 50, 1320, 2, 2600, KH31, "Grad_launch", "FX_MediumMissileIgnition", "FX_HE_UnguidedMissileDetonation", 1800),
        a2a("Turkey_Weapon_Sparrow_F4ETerm", 720, 960, 4, 900, METEOR),
        a2a("Turkey_Weapon_IR_F4ETerm", 640, 500, 2, 680, AIM9),
        a2g("Turkey_Weapon_Bomb_F4ETerm", 700, 36, 700, 6, 450, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        a2a("Pakistan_Weapon_PL15_J10CE", 920, 1420, 6, 840, R77),
        a2a("Pakistan_Weapon_PL10_J10CE", 760, 580, 2, 680, AIM9),
        a2g("Pakistan_Weapon_LS6_J10CE", 800, 28, 780, 4, 1200, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1400),
        a2a("Italy_Weapon_Meteor_GCAP", 960, 1480, 4, 900, METEOR),
        a2a("Italy_Weapon_IR_GCAP", 780, 600, 2, 680, AIM9),
        a2g("Italy_Weapon_PGM_GCAP", 820, 28, 800, 2, 1700, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1800),
    ]
)

BOMBER_CS = "GenericTacticalBomberCommandSet"
FIGHTER_CS = "F22A_AA_CommandSet"
KIND_UAV = "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT"
KIND_RECON = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT"

AIRCRAFT = [
    dict(
        rel="INI/Object/Specter/German Armed Forces/Airforce/GermanyUAVEuroMALE.ini",
        kind="jet",
        obj="GermanyUAVEuroMALE",
        side="Germany",
        portrait="SPEC_GermanyEuroMALE",
        model="Nat_Heron",
        model_d="Nat_HeronD",
        model_k="Nat_HeronD",
        weapons=wset2("Germany_Weapon_EuroMALE_PGM", "Germany_Weapon_EuroMALE_PGM", "VEHICLE STRUCTURE", "VEHICLE STRUCTURE"),
        cost=1600, time=14.0, hp=240, scale=0.78, vision=860,
        commandset=BOMBER_CS, shroud=620.0, kindof=KIND_UAV,
        extras=DETECT.format(rate=900, rng=520),
        needs_runway="No", mass=90.0, geom=(12.0, 6.0, 3.0, "Yes"),
        note="Germany Eurodrone MALE RPAS. Visual donor Nat_Heron. Recon plus 4 light PGM. No A2A.",
    ),
    dict(
        rel="INI/Object/Specter/French Armed Forces/Airforce/FranceUCAVNeuron.ini",
        kind="jet",
        obj="FranceUCAVNeuron",
        side="France",
        portrait="SPEC_FranceNeuron",
        model="CHI_GJ11L",
        model_d="CHI_GJ11LD",
        model_k="CHI_GJ11L",
        weapons=wset2("France_Weapon_Neuron_AASM", "France_Weapon_Neuron_AASM", "VEHICLE STRUCTURE", "VEHICLE STRUCTURE"),
        cost=2200, time=16.0, hp=260, scale=0.72, vision=720,
        commandset=BOMBER_CS, shroud=480.0, kindof=KIND_UAV,
        extras=STEALTH + DETECT.format(rate=1100, rng=420),
        needs_runway="No", mass=80.0, geom=(10.0, 5.0, 3.0, "Yes"),
        note="France Dassault nEUROn stealth UCAV. Visual donor CHI_GJ11L flying-wing. 2 internal PGM. No A2A.",
    ),
    dict(
        rel="INI/Object/Specter/German Armed Forces/Airforce/GermanyJetFCASNGF.ini",
        kind="jet",
        obj="GermanyJetFCASNGF",
        side="Germany",
        portrait="SPEC_GermanyFCASNGF",
        model="LSFJ31",
        model_d="LSFJ31d",
        model_k="LSFJ31k",
        weapons=wset("Germany_Weapon_FCAS_Meteor", "Germany_Weapon_FCAS_PGM", "Germany_Weapon_FCAS_Meteor", "AIRCRAFT", "VEHICLE STRUCTURE", "AIRCRAFT"),
        cost=2600, time=17.0, hp=480, scale=1.00, vision=740,
        commandset=FIGHTER_CS, shroud=360.0,
        extras=STEALTH + DETECT.format(rate=800, rng=720),
        note="Germany FCAS NGF Demonstrator. J-31-class stealth donor LSFJ31. Limited A2A plus 2 PGM. Not a full fighter.",
    ),
    dict(
        rel="INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirageF1CR.ini",
        kind="jet",
        obj="FranceJetMirageF1CR",
        side="France",
        portrait="SPEC_FranceMirageF1CR",
        model="LSFFRF1",
        model_d="LSFFRF1d",
        model_k="LSFFRF1k",
        weapons=wset("France_Weapon_F1CR_MICA", "France_Weapon_F1CR_IR", "France_Weapon_F1CR_Bomb", "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=1200, time=11.0, hp=380, scale=0.85, vision=680,
        commandset=BOMBER_CS, shroud=360.0,
        extras=DETECT.format(rate=1200, rng=400),
        note="France Mirage F1CR recon/strike. Donor ART LSFFRF1. Independent of F1CT.",
    ),
    dict(
        rel="INI/Object/Specter/French Armed Forces/Airforce/FranceJetRafaleF4.ini",
        kind="jet",
        obj="FranceJetRafaleF4",
        side="France",
        portrait="SPEC_FranceRafaleF4",
        model="LSFIDRafale",
        model_d="LSFIDRafaled",
        model_k="LSFIDRafalek",
        weapons=wset("France_Weapon_RafaleF4_Meteor", "France_Weapon_RafaleF4_MICA", "France_Weapon_RafaleF4_AASM", "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=2400, time=16.0, hp=500, scale=0.95, vision=740,
        commandset=FIGHTER_CS,
        note="France Rafale F4. Donor ART LSFIDRafale. Does not replace Rafale C/B/M.",
    ),
    dict(
        rel="INI/Object/Specter/British Armed Forces/Airforce/BritainAircraftTornadoECR.ini",
        kind="jet",
        obj="BritainAircraftTornadoECR",
        side="Britain",
        portrait="SPEC_BritainTornadoECR",
        model="LSFTornado",
        model_d="LSFTornadod",
        model_k="LSFTornadok",
        weapons=wset("Britain_Weapon_TornadoECR_HARM", "Britain_Weapon_TornadoECR_IR", "Britain_Weapon_TornadoECR_PGM", "VEHICLE STRUCTURE", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=2100, time=15.0, hp=440, scale=0.92, vision=600,
        commandset=BOMBER_CS,
        extras=DETECT.format(rate=700, rng=900),
        note="UK Tornado ECR SEAD. Independent of NATO BritainJetTornadoECR clone. Visual LSFTornado family.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetC130H.ini",
        kind="transport",
        obj="JapanJetC130H",
        side="Japan",
        portrait="SPEC_JapanC130H",
        model="AVCargoPln",
        model_d="AVCargoPln_D",
        model_k="AVCargoPln_D1",
        cost=2200, time=26.0, hp=680, scale=1.05,
        note="JASDF C-130H. Donor ART AVCargoPln four-engine turboprop transport. No offensive weapons.",
    ),
    dict(
        rel="INI/Object/Specter/PLA/Airforce/ChinaJetJ35A.ini",
        kind="jet",
        obj="ChinaJetJ35A",
        side="China",
        portrait="SPEC_ChinaJ35A",
        model="CHAJ31HXNew",
        model_d="CHAJ31HXNew",
        model_k="CHAJ31HXNew",
        weapons=wset("China_Weapon_PL15_J35A", "China_Weapon_PL10_J35A", "China_Weapon_LS6_J35A", "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=2800, time=17.0, hp=540, scale=1.05, vision=760,
        commandset=FIGHTER_CS,
        extras=STEALTH,
        note="PLA Shenyang J-35A. Donor ART CHAJ31HXNew. Distinct from LSFJ31 used by J-31.",
    ),
    dict(
        rel="INI/Object/Specter/Iranian Army/Airforce/IranJetMig21Bis.ini",
        kind="jet",
        obj="IranJetMig21Bis",
        side="Iran",
        portrait="SPEC_IranMig21Bis",
        model="LSFIDMig21",
        model_d="LSFIDMig21d",
        model_k="LSFIDMig21d",
        weapons=wset("Iran_Weapon_R60_Mig21", "Iran_Weapon_Cannon_Mig21", "Iran_Weapon_Bomb_Mig21", "AIRCRAFT", "AIRCRAFT VEHICLE", "VEHICLE STRUCTURE"),
        cost=700, time=8.0, hp=280, scale=0.82, vision=480,
        commandset=FIGHTER_CS,
        note="Iran MiG-21bis cheap interceptor. Donor ART LSFIDMig21 Fishbed. Legacy missiles.",
    ),
    dict(
        rel="INI/Object/Specter/Iranian Army/Airforce/IranJetSu35S.ini",
        kind="jet",
        obj="IranJetSu35S",
        side="Iran",
        portrait="SPEC_IranSu35S",
        model="LSFSU35",
        model_d="LSFSU35d",
        model_k="LSFSU35k",
        weapons=wset("Iran_Weapon_R77_Su35", "Iran_Weapon_R73_Su35", "Iran_Weapon_KH31_Su35", "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=2400, time=16.0, hp=560, scale=1.05, vision=720,
        commandset=FIGHTER_CS,
        note="Iran Su-35. Visual donor LSFSU35 Flanker family. Independent of Russia Su-35S.",
    ),
    dict(
        rel="INI/Object/Specter/Turkey Armed Forces/Airforce/TurkeyJetF4ETerm.ini",
        kind="jet",
        obj="TurkeyJetF4ETerm",
        side="Turkey",
        portrait="SPEC_TurkeyF4ETerm",
        model="JPF4",
        model_d="JPF4D",
        model_k="JPF4K",
        weapons=wset("Turkey_Weapon_Sparrow_F4ETerm", "Turkey_Weapon_IR_F4ETerm", "Turkey_Weapon_Bomb_F4ETerm", "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=1400, time=12.0, hp=420, scale=1.00, vision=600,
        commandset=BOMBER_CS,
        note="Turkey F-4E Terminator. Donor ART JPF4. Independent of Iran/Japan Phantom objects.",
    ),
    dict(
        rel="INI/Object/Specter/Pakistan Armed Forces/Airforce/PakistanJetJ10CE.ini",
        kind="jet",
        obj="PakistanJetJ10CE",
        side="Pakistan",
        portrait="SPEC_PakistanJ10CE",
        model="CHI_J10C",
        model_d="CHI_J10C_D",
        model_k="CHI_J10C_R",
        weapons=wset("Pakistan_Weapon_PL15_J10CE", "Pakistan_Weapon_PL10_J10CE", "Pakistan_Weapon_LS6_J10CE", "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=1900, time=14.0, hp=450, scale=1.10, vision=680,
        commandset=FIGHTER_CS,
        note="Pakistan J-10CE. Visual donor CHI_J10C canard-delta. Independent of China J-10B.",
    ),
    dict(
        rel="INI/Object/Specter/Italian Armed Forces/Airforce/ItalyJetGCAP.ini",
        kind="jet",
        obj="ItalyJetGCAP",
        side="Italy",
        portrait="SPEC_ItalyGCAP",
        model="qsnt50",
        model_d="qsnt50",
        model_k="qsnt50",
        weapons=wset("Italy_Weapon_Meteor_GCAP", "Italy_Weapon_IR_GCAP", "Italy_Weapon_PGM_GCAP", "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE"),
        cost=2700, time=17.0, hp=500, scale=1.00, vision=740,
        commandset=FIGHTER_CS,
        extras=STEALTH,
        note="Italy GCAP demonstrator. Visual stand-in qsnt50 T-50/PAK-FA class stealth. Not a Russian T-50.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanUAVRQ4.ini",
        kind="jet",
        obj="JapanUAVRQ4",
        side="Japan",
        portrait="SPEC_JapanRQ4",
        model="US_RQ-4",
        model_d="US_MQ-4",
        model_k="US_RQ-4",
        weapons="",
        cost=2000, time=18.0, hp=300, scale=0.88, vision=980,
        commandset="C17GlobalMasterCommandSet", shroud=820.0, kindof=KIND_RECON,
        extras=DETECT.format(rate=1500, rng=2200),
        needs_runway="Yes", mass=140.0, geom=(18.0, 8.0, 4.0, "No"),
        locomotor="D30-F6_JetLocomotor",
        note="JASDF RQ-4 Global Hawk unarmed HALE recon. Packed US_RQ-4. No offensive weapons.",
    ),
]

BUTTONS = [(s["obj"], s["portrait"]) for s in AIRCRAFT]
CSF_LABELS = {
    "CONTROLBAR:ConstructGermanyUAVEuroMALE": "Eurodrone MALE",
    "CONTROLBAR:ToolTipGermanyUAVEuroMALE": "German Eurodrone MALE RPAS. Long-endurance recon and light precision strike. No air-to-air missiles.",
    "OBJECT:GermanyUAVEuroMALE": "Eurodrone MALE",
    "CONTROLBAR:ConstructFranceUCAVNeuron": "nEUROn",
    "CONTROLBAR:ToolTipFranceUCAVNeuron": "French Dassault nEUROn stealth UCAV. Two internal precision bombs. Recon support.",
    "OBJECT:FranceUCAVNeuron": "nEUROn",
    "CONTROLBAR:ConstructGermanyJetFCASNGF": "FCAS NGF Demonstrator",
    "CONTROLBAR:ToolTipGermanyJetFCASNGF": "German FCAS next-generation fighter demonstrator. Limited air-to-air load and precision strike. Stealth.",
    "OBJECT:GermanyJetFCASNGF": "FCAS NGF Demonstrator",
    "CONTROLBAR:ConstructFranceJetMirageF1CR": "Mirage F1CR",
    "CONTROLBAR:ToolTipFranceJetMirageF1CR": "French Mirage F1CR reconnaissance strike fighter. Short-range IR, medium missiles, bombs.",
    "OBJECT:FranceJetMirageF1CR": "Mirage F1CR",
    "CONTROLBAR:ConstructFranceJetRafaleF4": "Rafale F4",
    "CONTROLBAR:ToolTipFranceJetRafaleF4": "French Rafale F4 multirole. Meteor, MICA, AASM. Does not replace Rafale C, B, or M.",
    "OBJECT:FranceJetRafaleF4": "Rafale F4",
    "CONTROLBAR:ConstructBritainAircraftTornadoECR": "Tornado ECR",
    "CONTROLBAR:ToolTipBritainAircraftTornadoECR": "RAF Tornado ECR SEAD. Anti-radar missiles, IR self-defense, precision bombs.",
    "OBJECT:BritainAircraftTornadoECR": "Tornado ECR",
    "CONTROLBAR:ConstructJapanJetC130H": "C-130H",
    "CONTROLBAR:ToolTipJapanJetC130H": "JASDF C-130H Hercules transport. Unarmed cargo aircraft.",
    "OBJECT:JapanJetC130H": "C-130H",
    "CONTROLBAR:ConstructChinaJetJ35A": "J-35A",
    "CONTROLBAR:ToolTipChinaJetJ35A": "PLA Shenyang J-35A stealth fighter. PL-15, PL-10, limited LS-6.",
    "OBJECT:ChinaJetJ35A": "J-35A",
    "CONTROLBAR:ConstructIranJetMig21Bis": "MiG-21bis",
    "CONTROLBAR:ToolTipIranJetMig21Bis": "Iranian MiG-21bis cheap interceptor. Short-range missiles, cannon, light bombs.",
    "OBJECT:IranJetMig21Bis": "MiG-21bis",
    "CONTROLBAR:ConstructIranJetSu35S": "Su-35",
    "CONTROLBAR:ToolTipIranJetSu35S": "Iranian Su-35 air-superiority fighter. R-77, R-73, limited Kh-31.",
    "OBJECT:IranJetSu35S": "Su-35",
    "CONTROLBAR:ConstructTurkeyJetF4ETerm": "F-4E Terminator",
    "CONTROLBAR:ToolTipTurkeyJetF4ETerm": "Turkish F-4E Terminator. Sparrow-style missiles, Sidewinder, bombs.",
    "OBJECT:TurkeyJetF4ETerm": "F-4E Terminator",
    "CONTROLBAR:ConstructPakistanJetJ10CE": "J-10CE",
    "CONTROLBAR:ToolTipPakistanJetJ10CE": "Pakistani J-10CE canard-delta fighter. PL-15, PL-10, LS-6.",
    "OBJECT:PakistanJetJ10CE": "J-10CE",
    "CONTROLBAR:ConstructItalyJetGCAP": "GCAP",
    "CONTROLBAR:ToolTipItalyJetGCAP": "Italian GCAP stealth demonstrator. Meteor, IR missiles, limited precision bombs.",
    "OBJECT:ItalyJetGCAP": "GCAP",
    "CONTROLBAR:ConstructJapanUAVRQ4": "RQ-4",
    "CONTROLBAR:ToolTipJapanUAVRQ4": "JASDF RQ-4 Global Hawk. Unarmed high-altitude reconnaissance UAV.",
    "OBJECT:JapanUAVRQ4": "RQ-4",
}
PORTRAITS = [p for _, p in BUTTONS]


def buttons_text() -> str:
    chunks = ["; SPECTER final global completion construct buttons."]
    for obj, img in BUTTONS:
        chunks.append(
            f"CommandButton Command_Construct{obj}\n"
            f"  Command          = UNIT_BUILD\n"
            f"  Object           = {obj}\n"
            f"  TextLabel        = CONTROLBAR:Construct{obj}\n"
            f"  ButtonImage      = {img}\n"
            f"  ButtonBorderType = BUILD\n"
            f"  DescriptLabel    = CONTROLBAR:ToolTip{obj}\n"
            f"End\n"
        )
    return "\n".join(chunks)


def mapped_text() -> str:
    chunks = ["; Unique Specter final completion portraits."]
    for img in PORTRAITS:
        chunks.append(
            f"MappedImage {img}\n"
            f"  Texture = {img}.tga\n"
            f"  TextureWidth = 150\n"
            f"  TextureHeight = 113\n"
            f"  Coords = Left:0 Top:0 Right:150 Bottom:113\n"
            f"  Status = NONE\n"
            f"End\n"
        )
    return "\n".join(chunks)


def main() -> None:
    w(INI / "Weapon_FinalGlobalCompletion.ini", WEAPONS)
    w(INI / "CommandButton_FinalGlobalCompletion.ini", buttons_text())
    w(MAP / "zFinalGlobalCompletion_Portrait_Images.INI", mapped_text())
    for spec in AIRCRAFT:
        if spec["kind"] == "transport":
            body = transport(
                spec["obj"], spec["side"], spec["portrait"],
                spec["model"], spec["model_d"], spec["model_k"],
                spec["cost"], spec["time"], spec["hp"], spec["scale"], spec["note"],
            )
        else:
            body = jet(
                spec["obj"], spec["side"], spec["portrait"],
                spec["model"], spec["model_d"], spec["model_k"],
                spec["weapons"], spec["cost"], spec["time"], spec["hp"],
                spec["scale"], spec["vision"], spec["note"],
                commandset=spec.get("commandset", FIGHTER_CS),
                shroud=spec.get("shroud", 220.0),
                kindof=spec.get("kindof", "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT"),
                extras=spec.get("extras", ""),
                needs_runway=spec.get("needs_runway", ""),
                locomotor=spec.get("locomotor", "Snecma_M88_4E"),
                geom=spec.get("geom", (14.0, 7.0, 5.0, "Yes")),
                mass=spec.get("mass", 500.0),
            )
        w(ROOT / spec["rel"], body)
    print(f"wrote {len(AIRCRAFT)} aircraft + weapons + buttons + portraits")


if __name__ == "__main__":
    main()
