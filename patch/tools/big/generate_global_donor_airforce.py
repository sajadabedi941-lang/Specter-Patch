#!/usr/bin/env python3
"""Write global donor-airforce overlay INI (ASCII, LF). ART is visual only."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/workspace/patch/Data")
INI = ROOT / "INI"
MAP = INI / "MappedImages/HandCreated"


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

TAIL = """  RadarPriority          = UNIT
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
  Locomotor = SET_NORMAL Snecma_M88_4E
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
        + TAIL.format(hp=hp)
    )


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


def a2a(name: str, dmg: float, rng: float, clip: int, delay: int, proj: str, vmin: float = 80.0) -> str:
    return f"""Weapon {name}
  PrimaryDamage = {dmg:.1f}
  PrimaryDamageRadius = 12.0
  SecondaryDamage = 12.0
  SecondaryDamageRadius = 22.0
  AttackRange = {rng:.1f}
  MinimumAttackRange = {vmin:.1f}
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
  ClipReloadTime = 14000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = Yes
  AntiGround = No
  AntiAirborneInfantry = Yes
  ShowsAmmoPips = Yes
End
"""


def a2g(name: str, dmg: float, rad: float, rng: float, clip: int, delay: int, proj: str, sound: str, fx: str, det: str, pre: int = 0) -> str:
    pre_block = ""
    if pre:
        pre_block = f"  PreAttackDelay = {pre}\n  PreAttackType = PER_ATTACK\n"
    return f"""Weapon {name}
  PrimaryDamage = {dmg:.1f}
  PrimaryDamageRadius = {rad:.1f}
  SecondaryDamage = 30.0
  SecondaryDamageRadius = {rad * 1.6:.1f}
  ScatterRadius = 16.0
  AttackRange = {rng:.1f}
  MinimumAttackRange = 80.0
{pre_block}  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 900
  FireFX = {fx}
  ProjectileObject = {proj}
  ProjectileDetonationFX = {det}
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound = {sound}
  DelayBetweenShots = {delay}
  ClipSize = {clip}
  ClipReloadTime = 28000
  AutoReloadsClip = RETURN_TO_BASE
  ProjectileCollidesWith = ALLIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End
"""


def rockets(name: str, clip: int) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 0.1
  PrimaryDamageRadius = 0.1
  ScatterRadiusVsInfantry = 90.0
  ScatterRadius = 28.0
  AttackRange = 480.0
  MinimumAttackRange = 60.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  ProjectileObject = GenericUnguidedRockets
  ProjectileExhaust = UnguidedRocketTrail
  RadiusDamageAffects = ENEMIES NEUTRALS
  DelayBetweenShots = Min:80 Max:220
  ClipSize = {clip}
  AutoReloadsClip = RETURN_TO_BASE
  ClipReloadTime = 18000
  FireSound = Unguided_Rockets_Fire
  FireFX = WeaponFX_GenericAirLaunchedMissileIgnition
  ProjectileDetonationFX = FX_UnguidedRocketExplosion
  ProjectileCollidesWith = ENEMIES STRUCTURES
  AntiAirborneVehicle = No
  AntiGround = Yes
  ShowsAmmoPips = Yes
End
"""


def cannon(name: str, clip: int) -> str:
    return f"""Weapon {name}
  PrimaryDamage = 38.0
  PrimaryDamageRadius = 8.0
  ScatterRadiusVsInfantry = 40.0
  ScatterRadius = 12.0
  AttackRange = 360.0
  MinimumAttackRange = 20.0
  DamageType = COMANCHE_VULCAN
  DeathType = EXTRA_4
  WeaponSpeed = 9999.0
  ProjectileObject = 30mm_API-T_Projectile
  ProjectileDetonationFX = WeaponFX_30mm_API-T_Tracer
  FireSound = 30mm_fire2
  FireFX = None
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots = 90
  ClipSize = {clip}
  ClipReloadTime = 1800
  AutoReloadsClip = Yes
  AntiAirborneVehicle = Yes
  AntiAirborneInfantry = Yes
  AntiGround = Yes
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
End
"""


# Proven packed projectiles only.
METEOR = "MeteorMissile_Object"
AIM9 = "AIM-9X_Object"
R77 = "R77_Object"
PHOENIX = "AIM-54_MissileObject"
GBU = "GBU24_GuidedBombObject"
FAB = "Fab-250"
CRUISE = "Kh59MK2_Object"
AGM = "AGM65C_MissileObject"
KH31 = "KH31P_MissileObject"
PAVE = "Paveway_IV_Object"

WEAPONS = "\n".join(
    [
        "; SPECTER global donor airforce weapons. Wrappers over packed projectiles.",
        a2a("Iran_Weapon_Sparrow_F4E", 720, 980, 4, 900, METEOR),
        a2a("Iran_Weapon_Sidewinder_F4E", 640, 520, 2, 650, AIM9),
        a2g("Iran_Weapon_Bomb_F4E", 720, 38, 720, 6, 450, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        a2a("Turkey_Weapon_Gokhan_KAAN", 980, 1500, 6, 950, R77),
        a2a("Turkey_Weapon_Bozdogan_KAAN", 780, 620, 2, 700, AIM9),
        a2g("Turkey_Weapon_HGK_KAAN", 860, 32, 820, 2, 1400, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1800),
        a2a("Turkey_Weapon_AIM120_F16C", 860, 1280, 4, 880, METEOR),
        a2g("Turkey_Weapon_HGK_F16C", 820, 30, 780, 4, 900, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1200),
        a2g("Turkey_Weapon_SOM_F16C", 1100, 52, 1320, 2, 3200, CRUISE, "Grad_launch", "FX_MediumMissileIgnition", "FX_HE_UnguidedMissileDetonation", 2000),
        a2a("Turkey_Weapon_Goktug_Ozgur", 900, 1400, 6, 820, R77),
        a2a("Turkey_Weapon_IR_Ozgur", 760, 580, 2, 680, AIM9),
        a2g("Turkey_Weapon_SOM_Ozgur", 1180, 55, 1400, 4, 2800, CRUISE, "Grad_launch", "FX_MediumMissileIgnition", "FX_HE_UnguidedMissileDetonation", 1800),
        a2a("Japan_Weapon_AAM4B_F2A", 900, 1360, 4, 860, METEOR),
        a2g("Japan_Weapon_ASM2_F2A", 1400, 60, 1280, 2, 2600, KH31, "Grad_launch", "FX_MediumMissileIgnition", "FX_HE_UnguidedMissileDetonation", 1600),
        a2g("Japan_Weapon_GBU_F2A", 840, 32, 800, 4, 1000, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1200),
        a2a("Japan_Weapon_AAM4B_F15J", 940, 1480, 8, 780, METEOR),
        a2a("Japan_Weapon_AAM5_F15J", 800, 600, 4, 620, AIM9),
        cannon("Japan_Weapon_Cannon_F15J", 40),
        a2a("Japan_Weapon_AAM4_X2", 960, 1420, 4, 900, METEOR),
        a2a("Japan_Weapon_AAM5_X2", 820, 640, 2, 640, AIM9),
        cannon("Japan_Weapon_Cannon_X2", 24),
        a2a("Japan_Weapon_AAM4B_F2B", 860, 1240, 2, 900, METEOR),
        a2a("Japan_Weapon_AAM5_F2B", 740, 560, 2, 700, AIM9),
        a2g("Japan_Weapon_GBU_F2B", 780, 28, 740, 2, 1300, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1600),
        a2a("Japan_Weapon_AAM4B_F2Kai", 920, 1440, 6, 800, METEOR),
        a2a("Japan_Weapon_AAM5_F2Kai", 780, 600, 2, 660, AIM9),
        a2g("Japan_Weapon_GBU_F2Kai", 900, 34, 860, 4, 900, PAVE, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1100),
        a2a("Japan_Weapon_Sparrow_F4EJ", 700, 920, 2, 950, METEOR),
        a2a("Japan_Weapon_Sidewinder_F4EJ", 620, 500, 2, 700, AIM9),
        a2g("Japan_Weapon_Bomb_F4EJ", 700, 36, 700, 4, 500, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        rockets("China_Weapon_Rocket_Q5", 8),
        a2g("China_Weapon_Bomb_Q5", 640, 34, 620, 8, 280, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        cannon("China_Weapon_Cannon_Q5", 24),
        a2a("China_Weapon_PL15_J20C", 1000, 1560, 6, 900, R77),
        a2a("China_Weapon_PL10_J20C", 820, 640, 2, 680, AIM9),
        a2g("China_Weapon_LS6_J20C", 880, 30, 840, 2, 1600, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 2000),
        a2a("France_Weapon_Meteor_20005F", 920, 1500, 6, 860, METEOR),
        a2a("France_Weapon_MICA_20005F", 780, 860, 4, 700, METEOR),
        cannon("France_Weapon_Cannon_20005F", 28),
    ]
)

AIRCRAFT = [
    dict(
        rel="INI/Object/Specter/Iranian Army/Airforce/IranJetF4E.ini",
        obj="IranJetF4E",
        side="Iran",
        portrait="SPEC_IranF4E",
        model="JPF4",
        model_d="JPF4D",
        model_k="JPF4K",
        weapons=wset(
            "Iran_Weapon_Sparrow_F4E",
            "Iran_Weapon_Sidewinder_F4E",
            "Iran_Weapon_Bomb_F4E",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=1400,
        time=12.0,
        hp=420,
        scale=1.00,
        vision=620,
        note="Iran F-4E Phantom II. Donor ART JPF4.W3D. Independent of UK/Japan Phantom objects.",
    ),
    dict(
        rel="INI/Object/Specter/Turkey Armed Forces/Airforce/TurkeyJetKAAN.ini",
        obj="TurkeyJetKAAN",
        side="Turkey",
        portrait="SPEC_TurkeyKAAN",
        model="LSFF22",
        model_d="LSFF22d",
        model_k="LSFF22k",
        weapons=wset(
            "Turkey_Weapon_Gokhan_KAAN",
            "Turkey_Weapon_Bozdogan_KAAN",
            "Turkey_Weapon_HGK_KAAN",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=2800,
        time=18.0,
        hp=560,
        scale=1.00,
        vision=720,
        note="Turkey KAAN. Visual donor LSFF22.W3D. UI identity is KAAN, never F-22.",
    ),
    dict(
        rel="INI/Object/Specter/Turkey Armed Forces/Airforce/TurkeyJetF16C.ini",
        obj="TurkeyJetF16C",
        side="Turkey",
        portrait="SPEC_TurkeyF16C",
        model="LSFF16C",
        model_d="LSFF16Cd",
        model_k="LSFF16Ck",
        weapons=wset(
            "Turkey_Weapon_AIM120_F16C",
            "Turkey_Weapon_HGK_F16C",
            "Turkey_Weapon_SOM_F16C",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
            "VEHICLE STRUCTURE",
        ),
        cost=1600,
        time=13.0,
        hp=430,
        scale=0.90,
        vision=640,
        note="Turkey F-16C Block 50+. Donor ART LSFF16C.W3D.",
    ),
    dict(
        rel="INI/Object/Specter/Turkey Armed Forces/Airforce/TurkeyJetF16Ozgur.ini",
        obj="TurkeyJetF16Ozgur",
        side="Turkey",
        portrait="SPEC_TurkeyF16Ozgur",
        model="LSFKF16",
        model_d="LSFKF16d",
        model_k="LSFKF16d",
        weapons=wset(
            "Turkey_Weapon_Goktug_Ozgur",
            "Turkey_Weapon_IR_Ozgur",
            "Turkey_Weapon_SOM_Ozgur",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=1800,
        time=14.0,
        hp=450,
        scale=0.92,
        vision=660,
        note="Turkey F-16 OZGUR. Donor ART LSFKF16.W3D. Distinct from Block 50+.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetF2A.ini",
        obj="JapanJetF2A",
        side="Japan",
        portrait="SPEC_JapanF2A",
        model="JPF2",
        model_d="JPF2D",
        model_k="JPF2K",
        weapons=wset(
            "Japan_Weapon_AAM4B_F2A",
            "Japan_Weapon_ASM2_F2A",
            "Japan_Weapon_GBU_F2A",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
            "VEHICLE STRUCTURE",
        ),
        cost=2000,
        time=15.0,
        hp=480,
        scale=0.98,
        vision=680,
        note="Japan Mitsubishi F-2A. Donor ART JPF2.W3D.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetF15JKai.ini",
        obj="JapanJetF15JKai",
        side="Japan",
        portrait="SPEC_JapanF15JKai",
        model="LSFJPF15J",
        model_d="LSFJPF15Jd",
        model_k="LSFJPF15Jk",
        weapons=wset(
            "Japan_Weapon_AAM4B_F15J",
            "Japan_Weapon_AAM5_F15J",
            "Japan_Weapon_Cannon_F15J",
            "AIRCRAFT",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
        ),
        cost=2400,
        time=16.0,
        hp=540,
        scale=1.08,
        vision=760,
        note="Japan F-15J Kai. Donor ART LSFJPF15J.W3D. Air superiority.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetX2Shinshin.ini",
        obj="JapanJetX2Shinshin",
        side="Japan",
        portrait="SPEC_JapanX2Shinshin",
        model="LSFSX2",
        model_d="LSFSX2d",
        model_k="LSFSX2k",
        weapons=wset(
            "Japan_Weapon_AAM4_X2",
            "Japan_Weapon_AAM5_X2",
            "Japan_Weapon_Cannon_X2",
            "AIRCRAFT",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
        ),
        cost=2200,
        time=16.0,
        hp=400,
        scale=0.92,
        vision=700,
        note="Japan X-2 Shinshin. Donor ART LSFSX2.W3D. Experimental stealth interceptor.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetF2B.ini",
        obj="JapanJetF2B",
        side="Japan",
        portrait="SPEC_JapanF2B",
        model="AGMZJPF2G",
        model_d="AGMZJPF2G",
        model_k="AGMZJPF2G",
        weapons=wset(
            "Japan_Weapon_AAM4B_F2B",
            "Japan_Weapon_AAM5_F2B",
            "Japan_Weapon_GBU_F2B",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=1700,
        time=13.0,
        hp=440,
        scale=0.94,
        vision=640,
        note="Japan Mitsubishi F-2B. Donor ART AGMZJPF2G.W3D. Lighter payload than F-2A.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetF2Kai.ini",
        obj="JapanJetF2Kai",
        side="Japan",
        portrait="SPEC_JapanF2Kai",
        model="LSF02TJ",
        model_d="LSF02TJd",
        model_k="LSF02TJk",
        weapons=wset(
            "Japan_Weapon_AAM4B_F2Kai",
            "Japan_Weapon_AAM5_F2Kai",
            "Japan_Weapon_GBU_F2Kai",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=2100,
        time=15.0,
        hp=500,
        scale=1.00,
        vision=700,
        note="Japan F-2 Kai. Donor ART LSF02TJ.W3D. Modernized multirole.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetF4EJKai.ini",
        obj="JapanJetF4EJKai",
        side="Japan",
        portrait="SPEC_JapanF4EJKai",
        model="JPF4",
        model_d="JPF4D",
        model_k="JPF4K",
        weapons=wset(
            "Japan_Weapon_Sparrow_F4EJ",
            "Japan_Weapon_Sidewinder_F4EJ",
            "Japan_Weapon_Bomb_F4EJ",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=1300,
        time=12.0,
        hp=400,
        scale=1.00,
        vision=600,
        note="Japan F-4EJ Kai. Donor ART JPF4.W3D. Independent of Iran F-4E.",
    ),
    dict(
        rel="INI/Object/Specter/PLA/Airforce/ChinaJetQ5.ini",
        obj="ChinaJetQ5",
        side="China",
        portrait="SPEC_ChinaQ5",
        model="QIANG5",
        model_d="QIANG5d",
        model_k="QIANG5k",
        weapons=wset(
            "China_Weapon_Rocket_Q5",
            "China_Weapon_Bomb_Q5",
            "China_Weapon_Cannon_Q5",
            "VEHICLE STRUCTURE",
            "VEHICLE STRUCTURE",
            "VEHICLE STRUCTURE AIRCRAFT",
        ),
        cost=800,
        time=8.0,
        hp=340,
        scale=0.88,
        vision=520,
        note="PLA Q-5 Qiang-5. Donor ART QIANG5.W3D. Legacy CAS. No stealth weapons.",
    ),
    dict(
        rel="INI/Object/Specter/PLA/Airforce/ChinaJetJ20C.ini",
        obj="ChinaJetJ20C",
        side="China",
        portrait="SPEC_ChinaJ20C",
        model="LSFJ20",
        model_d="LSFJ20",
        model_k="LSFJ20",
        weapons=wset(
            "China_Weapon_PL15_J20C",
            "China_Weapon_PL10_J20C",
            "China_Weapon_LS6_J20C",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=3000,
        time=18.0,
        hp=580,
        scale=1.10,
        vision=760,
        note="PLA J-20C. Donor ART LSFJ20.W3D. Distinct from CHI_J20B used by J-20B.",
    ),
    dict(
        rel="INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirage20005F.ini",
        obj="FranceJetMirage20005F",
        side="France",
        portrait="SPEC_FranceMirage20005F",
        model="FraMirage2000",
        model_d="FraMirage2000",
        model_k="FraMirage2000",
        weapons=wset(
            "France_Weapon_Meteor_20005F",
            "France_Weapon_MICA_20005F",
            "France_Weapon_Cannon_20005F",
            "AIRCRAFT",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
        ),
        cost=1900,
        time=14.0,
        hp=430,
        scale=0.90,
        vision=700,
        note="France Mirage 2000-5F. Donor ART FraMirage2000.W3D. A2A specialist.",
    ),
]

BUTTONS = [
    ("IranJetF4E", "SPEC_IranF4E"),
    ("TurkeyJetKAAN", "SPEC_TurkeyKAAN"),
    ("TurkeyJetF16C", "SPEC_TurkeyF16C"),
    ("TurkeyJetF16Ozgur", "SPEC_TurkeyF16Ozgur"),
    ("JapanJetF2A", "SPEC_JapanF2A"),
    ("JapanJetF15JKai", "SPEC_JapanF15JKai"),
    ("JapanJetX2Shinshin", "SPEC_JapanX2Shinshin"),
    ("JapanJetF2B", "SPEC_JapanF2B"),
    ("JapanJetF2Kai", "SPEC_JapanF2Kai"),
    ("JapanJetF4EJKai", "SPEC_JapanF4EJKai"),
    ("ChinaJetQ5", "SPEC_ChinaQ5"),
    ("ChinaJetJ20C", "SPEC_ChinaJ20C"),
    ("FranceJetMirage20005F", "SPEC_FranceMirage20005F"),
]

CSF_LABELS = {
    "CONTROLBAR:ConstructIranJetF4E": "F-4E Phantom II",
    "CONTROLBAR:ToolTipIranJetF4E": "Iranian F-4E Phantom II strike fighter. Sparrow, Sidewinder, bombs.",
    "OBJECT:IranJetF4E": "F-4E Phantom II",
    "CONTROLBAR:ConstructTurkeyJetKAAN": "KAAN",
    "CONTROLBAR:ToolTipTurkeyJetKAAN": "Turkish KAAN air-superiority fighter. Gokhan, Bozdogan, limited HGK.",
    "OBJECT:TurkeyJetKAAN": "KAAN",
    "CONTROLBAR:ConstructTurkeyJetF16C": "F-16C Block 50+",
    "CONTROLBAR:ToolTipTurkeyJetF16C": "Turkish F-16C Block 50+. AMRAAM, HGK, SOM.",
    "OBJECT:TurkeyJetF16C": "F-16C Block 50+",
    "CONTROLBAR:ConstructTurkeyJetF16Ozgur": "F-16 OZGUR",
    "CONTROLBAR:ToolTipTurkeyJetF16Ozgur": "Turkish F-16 OZGUR modernization. Goktug missiles and SOM strike.",
    "OBJECT:TurkeyJetF16Ozgur": "F-16 OZGUR",
    "CONTROLBAR:ConstructJapanJetF2A": "F-2A",
    "CONTROLBAR:ToolTipJapanJetF2A": "JASDF Mitsubishi F-2A. AAM-4B, ASM-2 anti-ship, guided bombs.",
    "OBJECT:JapanJetF2A": "F-2A",
    "CONTROLBAR:ConstructJapanJetF15JKai": "F-15J Kai",
    "CONTROLBAR:ToolTipJapanJetF15JKai": "JASDF F-15J Kai air-superiority fighter. AAM-4B and AAM-5.",
    "OBJECT:JapanJetF15JKai": "F-15J Kai",
    "CONTROLBAR:ConstructJapanJetX2Shinshin": "X-2 Shinshin",
    "CONTROLBAR:ToolTipJapanJetX2Shinshin": "JASDF X-2 Shinshin experimental stealth interceptor.",
    "OBJECT:JapanJetX2Shinshin": "X-2 Shinshin",
    "CONTROLBAR:ConstructJapanJetF2B": "F-2B",
    "CONTROLBAR:ToolTipJapanJetF2B": "JASDF Mitsubishi F-2B light multirole. Smaller payload than F-2A.",
    "OBJECT:JapanJetF2B": "F-2B",
    "CONTROLBAR:ConstructJapanJetF2Kai": "F-2 Kai",
    "CONTROLBAR:ToolTipJapanJetF2Kai": "JASDF F-2 Kai modernized multirole. Improved A2A and Paveway.",
    "OBJECT:JapanJetF2Kai": "F-2 Kai",
    "CONTROLBAR:ConstructJapanJetF4EJKai": "F-4EJ Kai",
    "CONTROLBAR:ToolTipJapanJetF4EJKai": "JASDF F-4EJ Kai legacy fighter. Sparrow, Sidewinder, bombs.",
    "OBJECT:JapanJetF4EJKai": "F-4EJ Kai",
    "CONTROLBAR:ConstructChinaJetQ5": "Q-5",
    "CONTROLBAR:ToolTipChinaJetQ5": "PLA Q-5 Qiang-5 ground attack aircraft. Rockets, bombs, cannon.",
    "OBJECT:ChinaJetQ5": "Q-5",
    "CONTROLBAR:ConstructChinaJetJ20C": "J-20C",
    "CONTROLBAR:ToolTipChinaJetJ20C": "PLA J-20C stealth fighter. PL-15, PL-10, limited LS-6.",
    "OBJECT:ChinaJetJ20C": "J-20C",
    "CONTROLBAR:ConstructFranceJetMirage20005F": "Mirage 2000-5F",
    "CONTROLBAR:ToolTipFranceJetMirage20005F": "French Mirage 2000-5F air-superiority fighter. Meteor and MICA.",
    "OBJECT:FranceJetMirage20005F": "Mirage 2000-5F",
}

PORTRAITS = [p for _, p in BUTTONS]


def buttons_text() -> str:
    chunks = ["; SPECTER global donor construct buttons. Inlined into CommandSet.ini."]
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
    chunks = ["; Unique Specter global donor portraits."]
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
    w(INI / "Weapon_GlobalDonorAirforce.ini", WEAPONS)
    w(INI / "CommandButton_GlobalDonorAirforce.ini", buttons_text())
    w(MAP / "zGlobalDonor_AirbasePortrait_Images.INI", mapped_text())
    for spec in AIRCRAFT:
        body = fighter(
            spec["obj"],
            spec["side"],
            spec["portrait"],
            spec["model"],
            spec["model_d"],
            spec["model_k"],
            spec["weapons"],
            spec["cost"],
            spec["time"],
            spec["hp"],
            spec["scale"],
            spec["vision"],
            spec["note"],
        )
        w(ROOT / spec["rel"], body)
    print(f"wrote {len(AIRCRAFT)} aircraft + weapons + buttons + portraits")


if __name__ == "__main__":
    main()
