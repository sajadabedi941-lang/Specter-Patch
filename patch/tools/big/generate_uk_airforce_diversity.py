#!/usr/bin/env python3
"""UK-only air-force visual/gameplay rebuild. Does not write France/Germany/Italy files."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_france_airforce_ini import fighter, w, wpn_set
from generate_europe_airforce_ini import jet

ROOT = Path("/workspace/patch/Data")
AIR = ROOT / "INI/Object/Specter/British Armed Forces/Airforce"
ROT = ROOT / "INI/Object/Specter/British Armed Forces/Rotary"


def aa(primary: str, secondary: str, tertiary: str) -> str:
    return wpn_set(
        [
            f"Weapon              = PRIMARY    {primary}",
            "PreferredAgainst    = PRIMARY    AIRCRAFT",
            "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
            f"Weapon              = SECONDARY  {secondary}",
            "PreferredAgainst    = SECONDARY  AIRCRAFT",
            "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
            f"Weapon              = TERTIARY   {tertiary}",
            "PreferredAgainst    = TERTIARY   AIRCRAFT VEHICLE",
            "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
        ]
    )


def strike(primary: str, secondary: str, tertiary: str) -> str:
    return wpn_set(
        [
            f"Weapon              = PRIMARY    {primary}",
            "PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE",
            "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
            f"Weapon              = SECONDARY  {secondary}",
            "PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE",
            "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
            f"Weapon              = TERTIARY   {tertiary}",
            "PreferredAgainst    = TERTIARY   INFANTRY VEHICLE STRUCTURE",
            "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
        ]
    )


def mixed(primary: str, pkind: str, secondary: str, skind: str, tertiary: str, tkind: str) -> str:
    return wpn_set(
        [
            f"Weapon              = PRIMARY    {primary}",
            f"PreferredAgainst    = PRIMARY    {pkind}",
            "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
            f"Weapon              = SECONDARY  {secondary}",
            f"PreferredAgainst    = SECONDARY  {skind}",
            "AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
            f"Weapon              = TERTIARY   {tertiary}",
            f"PreferredAgainst    = TERTIARY   {tkind}",
            "AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI",
        ]
    )


def uk_jet(*args, shroud: float | None = None, **kwargs) -> None:
    rec = jet("Britain", "British Armed Forces", *args, **kwargs)
    path = AIR / args[0]
    text = path.read_text(encoding="ascii")
    text = text.replace("SPECTER - France", "SPECTER - Britain")
    if shroud is not None:
        text = text.replace("ShroudClearingRange = 220.0", f"ShroudClearingRange = {shroud:.1f}")
    w(path, text)
    return rec


def write_e7() -> None:
    w(
        AIR / "BritainAircraftE7.ini",
        """; SPECTER - Britain E-7 Wedgetail. Donor KVE737. AWACS scan only; no weapons.
Object BritainAircraftE7
Scale = 0.90

  SelectPortrait         = SPEC_BritainE7
  ButtonImage            = SPEC_BritainE7

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model = KVE737
      Animation = KVE737.KVE737
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
    End
    ConditionState = JETEXHAUST
      Model = KVE737
      Animation = KVE737.KVE737
      AnimationMode = LOOP
      ParticleSysBone = ENGINE01 JetBlackTrailThin
    End
    ConditionState = REALLYDAMAGED
      Model = KVE737
      Animation = KVE737.KVE737
      AnimationMode = LOOP
      ParticleSysBone = SMOKE01 JetSmoke
    End
    ConditionState = RUBBLE
      Model = KVE737
    End
  End

  DisplayName = OBJECT:BritainAircraftE7
  EditorSorting = VEHICLE
  Side = Britain
  TransportSlotCount = 0
  VisionRange = 2000.0
  ShroudClearingRange = 2400.0
  BuildCost = 4300
  BuildTime = 36.0
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = Britain_E7AWACSCommandSet
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
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT RADAR REVEALS_ENEMY_PATHS
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
  Behavior = StealthDetectorUpdate ModuleTag_E7_Detect
    DetectionRate = 1500
    DetectionRange = 3800
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End
  Behavior = OCLSpecialPower ModuleTag_E7Scan
    SpecialPowerTemplate = Britain_SpecialPower_E7Scan
    OCL = OCL_AmericaE737TargetedSARScan
    CreateLocation = CREATE_AT_LOCATION
  End
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


def fly_heli(
    file: str,
    obj: str,
    portrait: str,
    model: str,
    model_d: str,
    model_k: str,
    anim: str,
    anim_d: str,
    display: str,
    cmd: str,
    weapons: str,
    cost: int,
    hp: int,
    scale: float,
    vision: float,
    kindof: str,
    extra_behaviors: str,
    transport: bool,
    slots: int,
) -> None:
    extra_bones = ""
    if transport:
        extra_bones = "    ExtraPublicBone = RopeStart\n    ExtraPublicBone = RopeEnd\n"
    contain = ""
    if transport:
        contain = f"""  Behavior = TransportContain ModuleTag_08
    Slots = {slots}
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY VEHICLE
    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE
    ExitDelay = 100
    NumberOfExitPaths = 1
  End
"""
    w(
        ROT / file,
        f"""; SPECTER - Britain {display}. Donor {model}. Flying helicopter skeleton.
Object {obj}
Scale = {scale:.2f}

  SelectPortrait         = {portrait}
  ButtonImage            = {portrait}
  UpgradeCameo1 = Upgrade_AmericaCountermeasures

  Draw = W3DModelDraw ModuleTag_01
{extra_bones}    DefaultConditionState
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
  Side = Britain
  VisionRange = {vision:.1f}
  ShroudClearingRange = 180.0
  BuildCost = {cost}
  BuildTime = 12.0
  ExperienceValue = 50 50 100 150
  ExperienceRequired = 0 100 200 400
  IsTrainable = Yes
  CommandSet = {cmd}
{weapons}  ArmorSet
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
  SoundEnter = HumveeEnter
  SoundExit = HumveeExit
  UnitSpecificSounds
    VoiceCreate = ComancheVoiceCreate
    VoiceUnload = ChinookVoiceUnload
    VoiceGarrison = ComancheVoiceMove
  End
  RadarPriority = UNIT
  KindOf = {kindof}
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
  Behavior = PhysicsBehavior ModuleTag_08p
    Mass = 50.0
  End
{contain}{extra_behaviors}  Geometry = Box
  GeometryIsSmall = Yes
  GeometryMajorRadius = 12.0
  GeometryMinorRadius = 6.0
  GeometryHeight = 8.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
""",
    )


def main() -> None:
    # Visual classes vs Typhoon 0.95 / Rafale 0.95:
    # Hawk LSFF16 compact light fighter 0.86 (~0.85 class)
    # Harrier AV-8B 0.93, Sea Harrier FA-18E 0.90, Jaguar F1 0.95
    # Lightning Mirage III small mesh 1.02, Vulcan B-52 0.96
    uk_jet(
        "BritainJetF35B.ini",
        "BritainJetF35B",
        "SPEC_BritainF35B",
        "US_F35A",
        "US_F35A",
        "US_F35A",
        mixed(
            "Britain_Weapon_AMRAAM",
            "AIRCRAFT",
            "Britain_Weapon_ASRAAM",
            "AIRCRAFT",
            "Britain_Weapon_SDB",
            "VEHICLE STRUCTURE",
        ),
        "GenericTacticalBomberCommandSet",
        3300,
        18.5,
        560,
        0.92,
        680.0,
        "F-35B",
    )
    uk_jet(
        "BritainJetTyphoonFGR4.ini",
        "BritainJetTyphoonFGR4",
        "SPEC_BritainTyphoonFGR4",
        "LSFEUEF2000",
        "LSFEUEF2000d",
        "LSFEUEF2000k",
        mixed(
            "Britain_Weapon_Meteor",
            "AIRCRAFT",
            "Britain_Weapon_ASRAAM",
            "AIRCRAFT",
            "Britain_Weapon_Brimstone",
            "VEHICLE STRUCTURE",
        ),
        "GenericTacticalBomberCommandSet",
        2900,
        17.0,
        550,
        0.95,
        720.0,
        "Eurofighter Typhoon FGR4",
        shroud=280.0,
    )
    uk_jet(
        "BritainJetTyphoonT3.ini",
        "BritainJetTyphoonT3",
        "SPEC_BritainTyphoonT3",
        "NAT_EF2000T4",
        "NAT_EF2000T4",
        "NAT_EF2000T4",
        aa("Britain_Weapon_Meteor", "Britain_Weapon_ASRAAM", "Britain_Weapon_JetCannon"),
        "F22A_AA_CommandSet",
        2700,
        16.0,
        530,
        0.98,
        680.0,
        "Typhoon Tranche 3",
    )
    uk_jet(
        "BritainJetHarrierGR9.ini",
        "BritainJetHarrierGR9",
        "SPEC_BritainHarrierGR9",
        "LSFAV8B",
        "LSFAV8Bd",
        "LSFAV8Bk",
        mixed(
            "Britain_Weapon_Paveway",
            "VEHICLE STRUCTURE",
            "Britain_Weapon_Brimstone",
            "VEHICLE STRUCTURE",
            "Britain_Weapon_ASRAAM",
            "AIRCRAFT",
        ),
        "GenericTacticalBomberCommandSet",
        1900,
        14.0,
        410,
        0.93,
        520.0,
        "Harrier GR9",
    )
    uk_jet(
        "BritainJetTornadoGR4.ini",
        "BritainJetTornadoGR4",
        "SPEC_BritainTornadoGR4",
        "LSFTornado",
        "LSFTornadod",
        "LSFTornadok",
        strike(
            "Britain_Weapon_StormShadow",
            "Britain_Weapon_Paveway_Heavy",
            "Britain_Weapon_Bomb_Heavy",
        ),
        "GenericTacticalBomberCommandSet",
        2300,
        15.5,
        490,
        0.92,
        580.0,
        "Tornado GR4",
    )
    uk_jet(
        "BritainJetJaguarGR3.ini",
        "BritainJetJaguarGR3",
        "SPEC_BritainJaguarGR3",
        "LSFFRF1",
        "LSFFRF1d",
        "LSFFRF1k",
        mixed(
            "Britain_Weapon_Paveway",
            "VEHICLE STRUCTURE",
            "Britain_Weapon_Bomb",
            "VEHICLE STRUCTURE",
            "Britain_Weapon_JetRockets",
            "INFANTRY VEHICLE STRUCTURE",
        ),
        "GenericTacticalBomberCommandSet",
        1500,
        12.5,
        380,
        0.95,
        480.0,
        "Jaguar GR3",
    )
    uk_jet(
        "BritainJetSeaHarrierFA2.ini",
        "BritainJetSeaHarrierFA2",
        "SPEC_BritainSeaHarrierFA2",
        "US_FA18E",
        "US_FA18F",
        "US_FA18F",
        aa("Britain_Weapon_AMRAAM", "Britain_Weapon_ASRAAM", "Britain_Weapon_JetCannon"),
        "F22A_AA_CommandSet",
        1700,
        13.5,
        390,
        0.90,
        560.0,
        "Sea Harrier FA2",
    )
    uk_jet(
        "BritainJetPhantomFG1.ini",
        "BritainJetPhantomFG1",
        "SPEC_BritainPhantomFG1",
        "JPF4",
        "JPF4D",
        "JPF4K",
        aa("Britain_Weapon_AMRAAM", "Britain_Weapon_ASRAAM", "Britain_Weapon_JetCannon"),
        "F22A_AA_CommandSet",
        1500,
        12.5,
        430,
        0.90,
        530.0,
        "Phantom FG1",
    )
    uk_jet(
        "BritainJetLightningF6.ini",
        "BritainJetLightningF6",
        "SPEC_BritainLightningF6",
        "LSFMirage3",
        "LSFMirage3d",
        "LSFMirage3k",
        aa("Britain_Weapon_Meteor", "Britain_Weapon_ASRAAM", "Britain_Weapon_JetCannon"),
        "F22A_AA_CommandSet",
        1300,
        11.0,
        360,
        1.02,
        760.0,
        "Lightning F6",
        shroud=400.0,
    )
    uk_jet(
        "BritainJetHawk200.ini",
        "BritainJetHawk200",
        "SPEC_BritainHawk200",
        "LSFF16",
        "LSFF16d",
        "LSFF16k",
        mixed(
            "Britain_Weapon_ASRAAM",
            "AIRCRAFT",
            "Britain_Weapon_HawkBomb",
            "VEHICLE STRUCTURE",
            "Britain_Weapon_JetCannon",
            "INFANTRY VEHICLE STRUCTURE",
        ),
        "GenericTacticalBomberCommandSet",
        1100,
        10.0,
        310,
        0.86,
        420.0,
        "Hawk 200",
    )
    uk_jet(
        "BritainJetTornadoF3.ini",
        "BritainJetTornadoF3",
        "SPEC_BritainTornadoF3",
        "LSFTornado",
        "LSFTornadod",
        "LSFTornadok",
        aa("Britain_Weapon_Meteor_Long", "Britain_Weapon_AMRAAM", "Britain_Weapon_ASRAAM"),
        "F22A_AA_CommandSet",
        2400,
        16.0,
        500,
        0.92,
        800.0,
        "Tornado F3",
        shroud=450.0,
    )
    uk_jet(
        "BritainJetPhantomFGR2.ini",
        "BritainJetPhantomFGR2",
        "SPEC_BritainPhantomFGR2",
        "JPF4",
        "JPF4D",
        "JPF4K",
        aa("Britain_Weapon_AMRAAM", "Britain_Weapon_ASRAAM", "Britain_Weapon_JetCannon"),
        "F22A_AA_CommandSet",
        1600,
        13.0,
        450,
        0.93,
        580.0,
        "Phantom FGR.2",
    )
    uk_jet(
        "BritainBomberVulcan.ini",
        "BritainBomberVulcan",
        "SPEC_BritainVulcan",
        "LSFUSAB52",
        "LSFUSAB52d",
        "LSFUSAB52k",
        strike("Britain_Weapon_CarpetBomb", "Britain_Weapon_StormShadow", "Britain_Weapon_JetCannon"),
        "GenericTacticalBomberCommandSet",
        3800,
        28.0,
        900,
        0.96,
        500.0,
        "Vulcan",
    )
    write_e7()

    fly_heli(
        "BritainHelicopterMerlin.ini",
        "BritainHelicopterMerlin",
        "SPEC_BritainMerlin",
        "LSFGENH90",
        "LSFGENH90",
        "LSFGENH90",
        "LSFGENH90.LSFGENH90",
        "LSFGENH90.LSFGENH90",
        "Merlin",
        "Britain_TransportHeliCommandSet",
        mixed(
            "Britain_Weapon_HeliATGM_Light",
            "VEHICLE STRUCTURE",
            "Britain_Weapon_HeliCannon_Light",
            "INFANTRY VEHICLE",
            "Britain_Weapon_HeliCannon_Light",
            "INFANTRY VEHICLE",
        ),
        1900,
        380,
        0.90,
        300.0,
        "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD",
        "",
        True,
        12,
    )
    fly_heli(
        "BritainHelicopterPuma.ini",
        "BritainHelicopterPuma",
        "SPEC_BritainPuma",
        "LSFRUMi171",
        "LSFRUMi171d",
        "LSFRUMi171k",
        "LSFRUMI171.LSFRUMI171",
        "LSFRUMI171.LSFRUMI171",
        "Puma",
        "Britain_TransportHeliCommandSet",
        wpn_set(
            [
                "Weapon              = PRIMARY    Britain_Weapon_HeliCannon_Light",
                "PreferredAgainst    = PRIMARY    INFANTRY VEHICLE",
                "AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
            ]
        ),
        1600,
        320,
        0.90,
        300.0,
        "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD",
        "",
        True,
        10,
    )
    fly_heli(
        "BritainHelicopterWildcat.ini",
        "BritainHelicopterWildcat",
        "SPEC_BritainWildcat",
        "LSFLynxAHMK",
        "LSFLynxAHMK",
        "LSFLynxAHMK",
        "LSFLYNXAHMK.LSFLYNXAHMK",
        "LSFLYNXAHMK.LSFLYNXAHMK",
        "Wildcat",
        "GenericAttackHelicopterHoverCommandSet",
        mixed(
            "Britain_Weapon_HeliCannon",
            "INFANTRY VEHICLE",
            "Britain_Weapon_HeliATGM",
            "VEHICLE STRUCTURE",
            "Britain_Weapon_HeliRocket",
            "INFANTRY STRUCTURE VEHICLE",
        ),
        1400,
        250,
        0.90,
        320.0,
        "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT PRODUCED_AT_HELIPAD",
        "",
        False,
        0,
    )
    print("Wrote UK diversity overlay INI")


if __name__ == "__main__":
    main()
