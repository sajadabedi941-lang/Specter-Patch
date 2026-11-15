#!/usr/bin/env python3
"""Write Loose INI sources for 18 V25 Russia systems plus independent War Factory 2."""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "objects"
OUT.mkdir(exist_ok=True)

VOICE = """  VoiceSelect           = AvengerVoiceSelect
  VoiceMove             = AvengerVoiceMove
  VoiceAttack           = AvengerVoiceAttack
  SoundMoveStart        = HumveeMoveStart
  SoundMoveStartDamaged = HumveeMoveStart
  UnitSpecificSounds
    VoiceCreate          = AvengerVoiceCreate
    TurretMoveStart      = NoSound
    TurretMoveLoop       = NoSound
    TruckLandingSound    = NoSound
    TruckPowerslideSound = NoSound
    VoiceEnter           = AvengerVoiceMove
  End
"""

FOOT = """  RadarPriority = UNIT
  Body = ActiveBody ModuleTag_02
    MaxHealth     = {hp}
    InitialHealth = {hp}
  End
  Locomotor = SET_NORMAL {loco}
  Behavior = PhysicsBehavior ModuleTag_04
    Mass = 50.0
  End
  Behavior = SlowDeathBehavior ModuleTag_26
    DeathTypes       = ALL -CRUSHED -SPLATTED
    DestructionDelay = 0
    FX               = FINAL FX_SupplyTruckExplosionOneFinal
  End
  Behavior = TransitionDamageFX ModuleTag_11
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmallLightSmokeColumn
    ReallyDamagedFXList1         = Loc: X:0 Y:0 Z:0 FXList:FX_BattleMasterDamageTransition
  End
  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration     = 5000
    AflameDamageAmount = 3
    AflameDamageDelay  = 500
  End
  Geometry            = BOX
  GeometryMajorRadius = {gx}
  GeometryMinorRadius = {gy}
  GeometryHeight      = {gz}
  GeometryIsSmall     = Yes
End
"""


def header(comment: str, obj: str, image: str) -> str:
    return (
        f"; {comment}\n"
        f"Object {obj}\n"
        f"  SelectPortrait = {image}\n"
        f"  ButtonImage    = {image}\n"
    )


def damage_state(model: str, extra: str = "") -> str:
    return (
        f"    ConditionState = REALLYDAMAGED\n"
        f"      Model = {model}\n"
        f"{extra}"
        f"    End\n"
    )


def design(name: str, cost: int, time: float, vision: int, shroud: int, kind: str) -> str:
    return (
        f"  DisplayName   = {name}\n"
        f"  Side          = Russia\n"
        f"  EditorSorting = VEHICLE\n"
        f"  ArmorSet\n"
        f"    Conditions = None\n"
        f"    Armor      = TankArmor\n"
        f"    DamageFX   = TankDamageFX\n"
        f"  End\n"
        f"  BuildCost = {cost}\n"
        f"  BuildTime = {time}\n"
        f"  VisionRange = {vision}\n"
        f"  ShroudClearingRange = {shroud}\n"
        f"  Prerequisites\n"
        f"  End\n"
        f"  CommandSet = GLAVehicleRocketBuggyCommandSet\n"
        f"  KindOf = {kind}\n"
    )


def ai_idle(acquire: str = "No") -> str:
    return (
        "  Behavior = AIUpdateInterface ModuleTag_03\n"
        f"    AutoAcquireEnemiesWhenIdle = {acquire}\n"
        "    MoodAttackCheckRate        = 150\n"
        "  End\n"
    )


def ai_turret(pitch: str = "Yes", slots: str = "PRIMARY", rate: int = 140, pitchrate: int | None = 30) -> str:
    pr = f"      TurretPitchRate       = {pitchrate}\n" if pitchrate is not None else ""
    return (
        "  Behavior = AIUpdateInterface ModuleTag_03\n"
        "    Turret\n"
        f"      TurretTurnRate        = {rate}\n"
        f"      AllowsPitch           = {pitch}\n"
        f"{pr}"
        f"      ControlledWeaponSlots = {slots}\n"
        "    End\n"
        "    AutoAcquireEnemiesWhenIdle = Yes Stealthed\n"
        "    MoodAttackCheckRate        = 150\n"
        "  End\n"
    )


def wheels_attach(model: str, bones: str) -> str:
    return (
        "  Draw = W3DTruckDraw ModuleTag_TracksDraw\n"
        "    OkToChangeModelColor             = No\n"
        "    ParticlesAttachedToAnimatedBones = Yes\n"
        "    AttachToBoneInAnotherModule      = CORE\n"
        "    DefaultConditionState\n"
        f"      Model = {model}\n"
        "    End\n"
        f"{bones}"
        "    TireRotationMultiplier = 0.4\n"
        "  End\n"
    )


TIRE8 = """    RightFrontTireBone     = TIRE01
    LeftFrontTireBone      = TIRE02
    MidRightFrontTireBone  = TIRE03
    MidLeftFrontTireBone   = TIRE04
    MidRightMidTireBone    = TIRE05
    MidLeftMidTireBone     = TIRE06
    MidRightRearTireBone   = TIRE07
    MidLeftRearTireBone    = TIRE08
"""

WHEEL8_32 = """    LeftFrontTireBone     = WHEEL02
    MidLeftFrontTireBone  = WHEEL03
    MidLeftRearTireBone   = WHEEL04
    LeftRearTireBone      = WHEEL05
    MidRightFrontTireBone = WHEEL06
    RightFrontTireBone    = WHEEL07
    MidRightRearTireBone  = WHEEL08
    RightRearTireBone     = WHEEL01
"""

WHEEL8_300 = """    LeftFrontTireBone     = WHEEL02
    MidLeftFrontTireBone  = WHEEL03
    MidLeftRearTireBone   = WHEEL04
    LeftRearTireBone      = WHEEL05
    MidRightFrontTireBone = WHEEL06
    RightFrontTireBone    = WHEEL07
    MidRightRearTireBone  = WHEEL08
    RightRearTireBone     = WHEEL09
"""

TUNG_W = """    LeftFrontTireBone     = WHEEL02
    MidLeftFrontTireBone  = WHEEL03
    MidLeftRearTireBone   = WHEEL04
    LeftRearTireBone      = WHEEL05
    MidRightFrontTireBone = WHEEL06
    RightFrontTireBone    = WHEEL07
    MidRightRearTireBone  = WHEEL08
    RightRearTireBone     = WHEEL09
"""

SHILKA_W = """    RightFrontTireBone     = TIRE01
    LeftFrontTireBone      = TIRE02
    MidRightFrontTireBone  = TIRE03
    MidLeftFrontTireBone   = TIRE04
    MidRightMidTireBone    = TIRE05
    MidLeftMidTireBone     = TIRE06
    MidRightRearTireBone   = TIRE07
    MidLeftRearTireBone    = TIRE08
"""


def truck_tires_8() -> str:
    return """    RightFrontTireBone     = WHEEL05
    LeftFrontTireBone      = WHEEL01
    MidRightFrontTireBone  = WHEEL06
    MidLeftFrontTireBone   = WHEEL02
    MidLeftRearTireBone    = WHEEL03
    MidRightRearTireBone   = WHEEL07
    RightRearTireBone      = WHEEL08
    LeftRearTireBone       = WHEEL04
    TireRotationMultiplier = 0.2
"""


def truck_tires_s400() -> str:
    return """    CabRotationMultiplier     = 1.5
    TrailerRotationMultiplier = 0.2
    CabBone                   = CAB
    TrailerBone               = TRAILER
    RotationDamping           = 0.7
    RightFrontTireBone        = Wheel01
    LeftFrontTireBone         = Wheel02
    MidRightFrontTireBone     = Wheel03
    MidLeftFrontTireBone      = Wheel04
    MidRightMidTireBone       = WHEEL09
    MidLeftMidTireBone        = WHEEL10
    MidRightRearTireBone      = Wheel05
    MidLeftRearTireBone       = Wheel06
    LeftRearTireBone          = WHEEL07
    RightRearTireBone         = WHEEL08
    TireRotationMultiplier    = 0.2
"""


def truck_tires_s350() -> str:
    return """    RightFrontTireBone     = Wheel01
    LeftFrontTireBone      = Wheel02
    MidRightFrontTireBone  = Wheel03
    MidLeftFrontTireBone   = Wheel04
    MidRightRearTireBone   = Wheel05
    MidLeftRearTireBone    = Wheel06
    LeftRearTireBone       = WHEEL07
    RightRearTireBone      = WHEEL08
    TireRotationMultiplier = 0.2
"""


def radar_detector(range_: int = 1800) -> str:
    return (
        "  Behavior = StealthDetectorUpdate ModuleTag_Det\n"
        "    DetectionRate            = 700\n"
        f"    DetectionRange           = {range_}\n"
        "    CanDetectWhileGarrisoned = No\n"
        "    CanDetectWhileContained  = No\n"
        "  End\n"
    )


KIND_VEH = "PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE"
KIND_RADAR = "PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE REVEALS_ENEMY_PATHS CANNOT_RETALIATE"
KIND_AA = "PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE"


def sam_weapons() -> str:
    return """  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   RussiaV25SAM_AA
    Weapon            = SECONDARY RussiaV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
"""


FILES: dict[str, str] = {}

FILES["RussiaV25CCWF_Weapons.ini"] = Path(__file__).with_name("weapons_src.ini").read_text("utf-8") if False else ""

WEAPONS = r"""; Unique SS2-safe weapons for V25 Russia CC/WF2 systems.

Weapon RussiaV25Strela_AA
  PrimaryDamage           = 195.0
  PrimaryDamageRadius     = 35.0
  ScatterRadiusVsInfantry = 10.0
  AttackRange             = 300.0
  MinimumAttackRange      = 5.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 800
  ProjectileObject        = PatriotMissile
  ProjectileExhaust       = PatriotMissileTrail
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots       = 2500
  ClipSize                = 8
  ClipReloadTime          = 16000
  AutoReloadsClip         = Yes
  FireSound               = TankHunterWeapon
  FireFX                  = FX_BuggyMissileIgnition
  ProjectileDetonationFX  = WeaponFX_RocketBuggyMissileDetonation
  AntiAirborneVehicle     = Yes
  AntiGround              = No
  ShowsAmmoPips           = Yes
End

Weapon RussiaV25SAM_AA
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = PENALTY
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = RussiaV25SAM_AA_Object
  FireOCL                = OCL_48N6TargetLock
  RadiusDamageAffects    = ENEMIES NEUTRALS
  DelayBetweenShots      = 5000
  ClipSize               = 4
  ClipReloadTime         = 15000
  AutoReloadsClip        = Yes
  FireSound              = Thaad_fire
  ProjectileDetonationFX = FX_HeavyAAMImpact
  AntiAirborneVehicle    = Yes
  AntiAirborneInfantry   = Yes
  AntiBallisticMissile   = Yes
  AntiGround             = No
  AcceptableAimDelta     = 180
  ShowsAmmoPips          = Yes
End

Weapon RussiaV25SAM_ABM
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = CRUSH
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = RussiaV25SAM_ABM_Object
  FireOCL                = OCL_40N6STargetLock
  RadiusDamageAffects    = ENEMIES NEUTRALS
  DelayBetweenShots      = 5000
  ClipSize               = 4
  ClipReloadTime         = 15000
  AutoReloadsClip        = Yes
  FireSound              = Thaad_fire
  ProjectileDetonationFX = FX_HeavyAAMImpact
  AntiAirborneVehicle    = No
  AntiGround             = No
  AntiBallisticMissile   = Yes
  AntiSmallMissile       = Yes
  ProjectileCollidesWith = ENEMIES
  AcceptableAimDelta     = 180
  ShowsAmmoPips          = Yes
End

Weapon RussiaV25SAM_ABM_Fuze
  PrimaryDamage          = 99999
  PrimaryDamageRadius    = 10
  AttackRange            = 75
  DamageType             = CRUSH
  DeathType              = LASERED
  WeaponSpeed            = 999999.0
  AcceptableAimDelta     = 360
  AntiBallisticMissile   = Yes
  AntiSmallMissile       = Yes
  RadiusDamageAffects    = ENEMIES
  ProjectileCollidesWith = ENEMIES
End

Object RussiaV25SAM_AA_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = Engine01 Spec_SAMRMFlare
      ParticleSysBone = Engine01 Spec_SAMRMTrail
    End
  End
  DisplayName   = Russia_S350
  EditorSorting = SYSTEM
  VisionRange   = 0.0
  ArmorSet
    Conditions = None
    Armor      = HeavyAntiAirMissileArmor
    DamageFX   = None
  End
  KindOf = PROJECTILE SMALL_MISSILE
  Body = ActiveBody ModuleTag_02
    MaxHealth     = 240.0
    InitialHealth = 240.0
  End
  Behavior = InstantDeathBehavior DeathModuleTag_01
    DeathTypes = NONE +DETONATED
    FX         = FX_GenericMissileDeath
  End
  Behavior = InstantDeathBehavior DeathModuleTag_02
    DeathTypes = NONE +LASERED
    FX         = FX_GenericMissileDisintegrate
    OCL        = OCL_GenericMissileDisintegrate
  End
  Behavior = InstantDeathBehavior DeathModuleTag_03
    DeathTypes = ALL -LASERED -DETONATED
    FX         = FX_GenericMissileDeath
  End
  Behavior = FireWeaponUpdate ModuleTag_SpeedChanging
    Weapon       = AAM_Boosters_Igniter
    InitialDelay = 2300
  End
  Behavior = PhysicsBehavior ModuleTag_06
    Mass = 2
  End
  Behavior = MissileAIUpdate ModuleTag_07
    TryToFollowTarget             = Yes
    FuelLifetime                  = 99999
    IgnitionDelay                 = 100
    IgnitionFX                    = FX_TubedMissileLaunchIgnition_HotLaunch
    InitialVelocity               = 92
    DistanceToTravelBeforeTurning = 30
  End
  Locomotor = SET_NORMAL THAADMissileLocomotor1
  Geometry            = Box
  GeometryIsSmall     = Yes
  GeometryMajorRadius = 2.0
  GeometryMinorRadius = 1.0
  GeometryHeight      = 1.0
End

Object RussiaV25SAM_ABM_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = ENGINEFX LargeSAMMissileTrail2
      ParticleSysBone = ENGINEFX LargeSAMMissilesFlare2
    End
  End
  DisplayName   = Russia_S500
  EditorSorting = SYSTEM
  VisionRange   = 0.0
  ArmorSet
    Conditions = None
    Armor      = AntiAirMissileArmorPlusTwo
    DamageFX   = None
  End
  KindOf = PROJECTILE BALLISTIC_MISSILE
  Body = ActiveBody ModuleTag_02
    MaxHealth     = 100.0
    InitialHealth = 100.0
  End
  Behavior = InstantDeathBehavior DeathModuleTag_01
    DeathTypes = NONE +DETONATED
    FX         = FX_GenericMissileDeath
  End
  Behavior = InstantDeathBehavior DeathModuleTag_02
    DeathTypes = NONE +LASERED
    FX         = FX_GenericMissileDisintegrate
    OCL        = OCL_GenericMissileDisintegrate
  End
  Behavior = InstantDeathBehavior DeathModuleTag_03
    DeathTypes = ALL -LASERED -DETONATED
    FX         = FX_GenericMissileDeath
  End
  Behavior = FireWeaponUpdate ModuleTag_ABMFuze
    Weapon       = RussiaV25SAM_ABM_Fuze
    InitialDelay = 0
  End
  Behavior = PhysicsBehavior ModuleTag_06
    Mass = 2
  End
  Behavior = MissileAIUpdate ModuleTag_07
    TryToFollowTarget             = Yes
    FuelLifetime                  = 99999
    IgnitionDelay                 = 5
    IgnitionFX                    = FX_TubedMissileLaunchIgnition_HotLaunch
    InitialVelocity               = 110
    DistanceToTravelBeforeTurning = 25
    DistanceToTargetForLock       = 100
  End
  Locomotor = SET_NORMAL THAAD_ABM_MissileLocomotor
  Geometry            = BOX
  GeometryIsSmall     = Yes
  GeometryMajorRadius = 25.0
  GeometryMinorRadius = 22.0
  GeometryHeight      = 6.0
End

Weapon RussiaV25Gun
  PrimaryDamage           = 25
  PrimaryDamageRadius     = 8.0
  ScatterRadiusVsInfantry = 20.0
  ScatterRadius           = 11.0
  AttackRange             = 340.0
  MinimumAttackRange      = 15.0
  DamageType              = GATTLING
  DeathType               = EXTRA_4
  WeaponSpeed             = 9999.0
  ProjectileObject        = 30mm_API-T_Projectile
  ProjectileDetonationFX  = WeaponFX_30mm_API-T_Tracer
  FireSound               = 20mm_fire
  FireFX                  = WeaponFX_HeavyCalibarChainGunsFire_Heli
  RadiusDamageAffects     = ENEMIES NEUTRALS
  DelayBetweenShots       = 20
  ClipSize                = 2500
  ClipReloadTime          = 3000
  ProjectileCollidesWith  = ENEMIES STRUCTURES
  AntiGround              = Yes
  AntiAirborneVehicle     = No
End

Weapon RussiaV25Gun_AA
  PrimaryDamage           = 25
  PrimaryDamageRadius     = 8.0
  ScatterRadiusVsInfantry = 20.0
  ScatterRadius           = 11.0
  AttackRange             = 400.0
  MinimumAttackRange      = 15.0
  DamageType              = GATTLING
  DeathType               = EXTRA_4
  WeaponSpeed             = 9999.0
  ProjectileObject        = 30mm_API-T_Projectile
  ProjectileDetonationFX  = WeaponFX_30mm_API-T_Tracer
  FireSound               = 20mm_fire
  FireFX                  = WeaponFX_HeavyCalibarChainGunsFire_Heli
  RadiusDamageAffects     = ENEMIES NEUTRALS
  DelayBetweenShots       = 20
  ClipSize                = 2500
  ClipReloadTime          = 3000
  ProjectileCollidesWith  = ENEMIES STRUCTURES
  AntiGround              = No
  AntiAirborneVehicle     = Yes
  AntiAirborneInfantry    = Yes
  AntiBallisticMissile    = Yes
  AntiSmallMissile        = Yes
End

Weapon RussiaV25Rocket
  PrimaryDamage           = 400.0
  PrimaryDamageRadius     = 40.0
  ScatterRadiusVsInfantry = 15
  AttackRange             = 700
  MinimumAttackRange      = 80.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 400
  ProjectileObject        = 155mm_Shell
  FireFX                  = FX_BuggyMissileIgnition
  FireSound               = InfernoCannonWeapon
  ProjectileDetonationFX  = FX_UnguidedRocketExplosion
  RadiusDamageAffects     = ENEMIES NEUTRALS
  DelayBetweenShots       = 4000
  ClipSize                = 12
  ClipReloadTime          = 18000
  AutoReloadsClip         = Yes
  AntiGround              = Yes
  ShowsAmmoPips           = Yes
End

Weapon RussiaV25Cruise
  PrimaryDamage           = 500.0
  PrimaryDamageRadius     = 45.0
  ScatterRadiusVsInfantry = 15
  AttackRange             = 900
  MinimumAttackRange      = 100.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 350
  ProjectileObject        = PatriotMissile
  ProjectileExhaust       = PatriotMissileTrail
  FireFX                  = FX_BuggyMissileIgnition
  FireSound               = TomahawkFire
  ProjectileDetonationFX  = FX_UnguidedRocketExplosion
  RadiusDamageAffects     = ENEMIES NEUTRALS
  DelayBetweenShots       = 6000
  ClipSize                = 8
  ClipReloadTime          = 22000
  AutoReloadsClip         = Yes
  AntiGround              = Yes
  ShowsAmmoPips           = Yes
End
"""

FILES["RussiaV25CCWF_Weapons.ini"] = WEAPONS


def launcher_truck(obj, image, model, comment, display, launch, fire, tires, cost, time, hp, extra_cab=False):
    bones = (
        f"      WeaponLaunchBone = PRIMARY {launch}\n"
        f"      WeaponFireFXBone = PRIMARY {fire}\n"
        f"      WeaponLaunchBone = SECONDARY {launch}\n"
        f"      WeaponFireFXBone = SECONDARY {fire}\n"
    )
    return (
        header(comment, obj, image)
        + "  Draw = W3DTruckDraw ModuleTag_01\n"
        + "    OkToChangeModelColor = No\n"
        + "    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY\n"
        + "    DefaultConditionState\n"
        + f"      Model            = {model}\n"
        + f"      Animation        = {model}.{model}\n"
        + "      AnimationMode    = MANUAL\n"
        + "      Flags            = START_FRAME_LAST\n"
        + bones
        + "    End\n"
        + damage_state(model, bones)
        + "    TrackMarks = EXTireTrack.tga\n"
        + "    Dust       = RocketBuggyDust\n"
        + "    DirtSpray  = RocketBuggyDirtSpray\n"
        + tires
        + "  End\n"
        + design(display, cost, time, 1200, 250, KIND_VEH)
        + sam_weapons()
        + ai_idle("Yes Stealthed")
        + VOICE
        + FOOT.format(hp=hp, loco="Generic8x8Locomotor", gx=18, gy=10, gz=12)
    )


def cruise_truck(obj, image, model, comment, display, launch, fire, tires, cost, time, hp):
    bones = (
        f"      WeaponLaunchBone = PRIMARY {launch}\n"
        f"      WeaponFireFXBone = PRIMARY {fire}\n"
    )
    return (
        header(comment, obj, image)
        + "  Draw = W3DTruckDraw ModuleTag_01\n"
        + "    OkToChangeModelColor = No\n"
        + "    ProjectileBoneFeedbackEnabledSlots = PRIMARY\n"
        + "    DefaultConditionState\n"
        + f"      Model            = {model}\n"
        + f"      Animation        = {model}.{model}\n"
        + "      AnimationMode    = MANUAL\n"
        + "      Flags            = START_FRAME_LAST\n"
        + bones
        + "    End\n"
        + damage_state(model, bones)
        + "    TrackMarks = EXTireTrack.tga\n"
        + tires
        + "  End\n"
        + design(display, cost, time, 400, 180, KIND_VEH)
        + "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY RussiaV25Cruise\n  End\n"
        + ai_idle("Yes Stealthed")
        + VOICE
        + FOOT.format(hp=hp, loco="Generic8x8Locomotor", gx=18, gy=10, gz=12)
    )


def radar_truck(obj, image, model, comment, display, tires, vision, shroud, anim=True):
    anim_lines = (
        f"      Animation     = {model}.{model}\n      AnimationMode = LOOP\n" if anim else ""
    )
    return (
        header(comment, obj, image)
        + "  Draw = W3DTruckDraw ModuleTag_01\n"
        + "    OkToChangeModelColor = No\n"
        + "    DefaultConditionState\n"
        + f"      Model         = {model}\n"
        + anim_lines
        + "    End\n"
        + damage_state(model, anim_lines)
        + "    TrackMarks = EXTireTrack.tga\n"
        + tires
        + "  End\n"
        + design(display, 1300, 15.0, vision, shroud, KIND_RADAR)
        + "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY NONE\n  End\n"
        + radar_detector(vision)
        + ai_idle("No")
        + VOICE
        + FOOT.format(hp=350, loco="Generic8x8Locomotor", gx=16, gy=9, gz=12)
    )


def radar_tank(obj, image, model, extra, comment, display, bones_need, vision, extra_tires, anim=True):
    anim_lines = (
        f"      Animation     = {model}.{model}\n      AnimationMode = LOOP\n" if anim else ""
    )
    return (
        header(comment, obj, image)
        + "  Draw = W3DTankDraw ModuleTag_01\n"
        + "    OkToChangeModelColor = No\n"
        + "    ExtraPublicBone = CORE\n"
        + "    DefaultConditionState\n"
        + f"      Model         = {model}\n"
        + anim_lines
        + "    End\n"
        + damage_state(model, anim_lines)
        + "    TrackMarks = EXTnkTrack.tga\n"
        + "  End\n"
        + wheels_attach(extra, extra_tires)
        + design(display, 1500, 15.0, vision, 800, KIND_RADAR)
        + "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY NONE\n  End\n"
        + radar_detector(vision)
        + ai_idle("No")
        + VOICE
        + FOOT.format(hp=350, loco="CrusaderLocomotor", gx=16, gy=10, gz=12)
    )


def aa_tank(obj, image, model, extra, comment, display, turret_block, extra_tires, weapons, slots, pitch="Yes"):
    return (
        header(comment, obj, image)
        + "  Draw = W3DTankDraw ModuleTag_01\n"
        + "    OkToChangeModelColor = No\n"
        + "    ExtraPublicBone = CORE\n"
        + "    DefaultConditionState\n"
        + f"      Model = {model}\n"
        + turret_block
        + "    End\n"
        + damage_state(model, turret_block)
        + "    TrackMarks = EXTnkTrack.tga\n"
        + "  End\n"
        + wheels_attach(extra, extra_tires)
        + design(display, 1200, 14.0, 170, 300, KIND_AA)
        + weapons
        + ai_turret(pitch=pitch, slots=slots)
        + VOICE
        + FOOT.format(hp=400, loco="CrusaderLocomotor", gx=15, gy=10, gz=10)
    )


FILES["RussiaVehicleV25S350.ini"] = launcher_truck(
    "RussiaVehicleV25S350", "RUS350TB", "RUS350",
    "V25 RussiaS350 / Nuke_Command_ConstructRussiaS350. Model RUS350. Independent of SS2 RussiaVehicleS400.",
    "Russia_S350", "WEAPONB", "MUZZLEFX", truck_tires_s350(), 3000, 48.0, 420,
)
FILES["RussiaVehicleV2550N6A.ini"] = radar_truck(
    "RussiaVehicleV2550N6A", "50N6ATB", "RUS350RD",
    "V25 Russia50N6A / Nuke_Command_ConstructRussia50N6A. Model RUS350RD.",
    "Russia_50N6A", """    LeftFrontTireBone = WHEEL01
    RightFrontTireBone = WHEEL04
    LeftRearTireBone = WHEEL03
    RightRearTireBone = WHEEL06
    MidLeftRearTireBone = WHEEL02
    MidRightRearTireBone = WHEEL05
    TireRotationMultiplier = 0.2
""", 1000, 1000,
)
FILES["RussiaVehicleV25S300V1.ini"] = (
    header(
        "V25 RussiaS300VM / Nuke_Command_ConstructRussiaS300VM. Model URS300V + URS300Vw. S-300V1.",
        "RussiaVehicleV25S300V1",
        "RUS300VMTB",
    )
    + "  Draw = W3DTankDraw ModuleTag_01\n"
    + "    OkToChangeModelColor = No\n"
    + "    ExtraPublicBone = CORE\n"
    + "    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY\n"
    + "    DefaultConditionState\n"
    + "      Model            = URS300V\n"
    + "      Animation        = URS300V.URS300V\n"
    + "      AnimationMode    = MANUAL\n"
    + "      Flags            = START_FRAME_LAST\n"
    + "      WeaponLaunchBone = PRIMARY WEAPONB\n"
    + "      WeaponFireFXBone = PRIMARY WEAPONFX\n"
    + "      WeaponLaunchBone = SECONDARY WEAPONB\n"
    + "      WeaponFireFXBone = SECONDARY WEAPONFX\n"
    + "    End\n"
    + damage_state(
        "URS300V",
        "      WeaponLaunchBone = PRIMARY WEAPONB\n      WeaponFireFXBone = PRIMARY WEAPONFX\n"
        "      WeaponLaunchBone = SECONDARY WEAPONB\n      WeaponFireFXBone = SECONDARY WEAPONFX\n",
    )
    + "    TrackMarks = EXTnkTrack.tga\n  End\n"
    + wheels_attach("URS300Vw", WHEEL8_300)
    + design("Ukraine_S300V1", 3000, 48.0, 1200, 250, KIND_VEH)
    + sam_weapons()
    + ai_idle("Yes Stealthed")
    + VOICE
    + FOOT.format(hp=450, loco="CrusaderLocomotor", gx=18, gy=10, gz=12)
)
FILES["RussiaVehicleV259S32.ini"] = radar_tank(
    "RussiaVehicleV259S32", "9S32TB", "UR9S32", "UR9S32w",
    "V25 Russia9S32 / Nuke_Command_ConstructRussia9S32. Model UR9S32 + UR9S32w.",
    "Russia_9S32-Radar", "CORE", 5000, WHEEL8_32,
)
FILES["RussiaVehicleV259S119M1.ini"] = radar_tank(
    "RussiaVehicleV259S119M1", "RU9S18M1TB", "UR9S18M1", "UR9S18M1w",
    "V25 Russia9S18M1 listed as 9S119M1. Model UR9S18M1 + UR9S18M1w. Buk Snow Drift radar.",
    "Egypt_9S18M1", "CORE", 1800, TIRE8,
)
FILES["RussiaVehicleV25S400.ini"] = launcher_truck(
    "RussiaVehicleV25S400", "RUS400TB", "RUS400",
    "V25 russias400 / Nuke_Command_ConstructRussiaS400. Model RUS400. Independent of SS2 RussiaVehicleS400.",
    "Russia_S400", "MISSILE_C", "MUZZLEFX", truck_tires_s400(), 3200, 48.0, 450,
)
FILES["RussiaVehicleV2540V6MD.ini"] = radar_truck(
    "RussiaVehicleV2540V6MD", "40V6MDTB", "SD40V6MD",
    "V25 RussianRadar / Nuke_Command_ConstructRussianRadar. Model SD40V6MD.",
    "Russia_40V6MD", truck_tires_s400(), 5000, 1000,
)
FILES["RussiaVehicleV25S500.ini"] = launcher_truck(
    "RussiaVehicleV25S500", "RUS500TB", "RUS500",
    "V25 RussiaS500 / Nuke_Command_ConstructRussiaS500. Model RUS500. Independent of SS2 RussiaVehicleS500.",
    "Russia_S500", "MISSILE_C", "MUZZLEFX", truck_tires_s400(), 3500, 48.0, 480,
)

TUNG_TUR = """      Animation     = INTGSK.INTGSK
      AnimationMode = LOOP
      Turret = TURRET
      TurretPitch = TURRETEL
      WeaponFireFXBone = PRIMARY BARRELFX
      WeaponLaunchBone = PRIMARY BARRELFX
      WeaponFireFXBone = SECONDARY BARRELFX
      WeaponLaunchBone = SECONDARY BARRELFX
      WeaponLaunchBone = TERTIARY MISSILE
      WeaponFireFXBone = TERTIARY MISSILE
"""
FILES["RussiaVehicleV25Tunguska.ini"] = aa_tank(
    "RussiaVehicleV25Tunguska", "URTGSKTB", "INTGSK", "INTGSKw",
    "V25 Ukrania2K22 / Command_ConstructUkrania2K22. Only V25 Tunguska 2K22. Model INTGSK + INTGSKw.",
    "CONTROLBAR:TGSK", TUNG_TUR, TUNG_W,
    "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY RussiaV25Gun\n    Weapon = SECONDARY RussiaV25Gun_AA\n    Weapon = TERTIARY RussiaV25Strela_AA\n  End\n",
    "PRIMARY SECONDARY TERTIARY",
)
FILES["RussiaVehicleV25BalE.ini"] = cruise_truck(
    "RussiaVehicleV25BalE", "BALETB", "RUBALE",
    "V25 RussiaCoastal / Nuke_Command_ConstructRussiaCoastal. Model RUBALE.",
    "Russia_BAL_E", "WEAPONA", "WEAPONA", truck_tires_8(), 2800, 30.0, 400,
)
FILES["RussiaVehicleV259K33.ini"] = (
    header(
        "V25 RussiaTankT64 hijack / RU9K33. Russia 9K33 Osa, one copy only.",
        "RussiaVehicleV259K33",
        "9K33TB",
    )
    + "  Draw = W3DTruckDraw ModuleTag_01\n"
    + "    OkToChangeModelColor = Yes\n"
    + "    DefaultConditionState\n"
    + "      Model            = RU9K33\n"
    + "      Animation        = RU9K33.RU9K33\n"
    + "      AnimationMode    = LOOP\n"
    + "      Turret           = TURRET\n"
    + "      TurretPitch      = TURRETEL\n"
    + "      WeaponLaunchBone = PRIMARY FIREFX\n"
    + "      WeaponFireFXBone = PRIMARY FIREFX\n"
    + "    End\n"
    + damage_state(
        "RU9K33",
        "      Turret = TURRET\n      TurretPitch = TURRETEL\n"
        "      WeaponLaunchBone = PRIMARY FIREFX\n      WeaponFireFXBone = PRIMARY FIREFX\n",
    )
    + "    TrackMarks = EXTireTrack.tga\n"
    + "    LeftFrontTireBone = TIRE01\n    RightFrontTireBone = TIRE02\n"
    + "    MidLeftRearTireBone = TIRE03\n    MidRightRearTireBone = TIRE04\n"
    + "    LeftRearTireBone = TIRE05\n    RightRearTireBone = TIRE06\n"
    + "    TireRotationMultiplier = 0.2\n  End\n"
    + design("Russia_9K33", 1000, 12.0, 230, 300, KIND_AA)
    + "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY RussiaV25Strela_AA\n    PreferredAgainst = PRIMARY AIRCRAFT\n  End\n"
    + ai_turret()
    + VOICE
    + FOOT.format(hp=320, loco="Generic8x8Locomotor", gx=14, gy=8, gz=10)
)
FILES["RussiaVehicleV2530N6E.ini"] = radar_truck(
    "RussiaVehicleV2530N6E", "30N6EFLTB", "30N6EFL",
    "V25 30N6EFLAPLID / Nuke_Command_Construct30N6EFLAPLID. Model 30N6EFL.",
    "Russia_30N6EFlapLid", truck_tires_8(), 2200, 1000,
)
FILES["RussiaVehicleV259K31.ini"] = (
    header(
        "V25 Russia9K31 / Command_ConstructRussia9K31. Model UR9K31.",
        "RussiaVehicleV259K31",
        "RY9K31TB",
    )
    + "  Draw = W3DTruckDraw ModuleTag_01\n"
    + "    DefaultConditionState\n"
    + "      Model            = UR9K31\n"
    + "      Turret           = TURRET\n"
    + "      TurretPitch      = TURRETEL\n"
    + "      WeaponFireFXBone = PRIMARY MUZZLE\n"
    + "      WeaponLaunchBone = PRIMARY MUZZLE\n"
    + "    End\n"
    + damage_state(
        "UR9K31",
        "      Turret = TURRET\n      TurretPitch = TURRETEL\n"
        "      WeaponFireFXBone = PRIMARY MUZZLE\n      WeaponLaunchBone = PRIMARY MUZZLE\n",
    )
    + "    TrackMarks = EXTireTrack.tga\n"
    + "    LeftFrontTireBone = TIRE01\n    RightFrontTireBone = TIRE02\n"
    + "    LeftRearTireBone = TIRE05\n    RightRearTireBone = TIRE06\n"
    + "    TireRotationMultiplier = 0.2\n  End\n"
    + design("Egypt_9K31", 1000, 12.0, 230, 300, KIND_AA)
    + "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY RussiaV25Strela_AA\n    PreferredAgainst = PRIMARY AIRCRAFT\n  End\n"
    + ai_turret()
    + VOICE
    + FOOT.format(hp=300, loco="Generic8x8Locomotor", gx=12, gy=8, gz=9)
)
SHILKA_TUR = """      Animation     = NKZSU23.NKZSU23
      AnimationMode = LOOP
      Turret = TURRET01
      TurretPitch = TURRETEL01
      WeaponFireFXBone = PRIMARY MUZZLE
      WeaponLaunchBone = PRIMARY MUZZLE
      WeaponFireFXBone = SECONDARY MUZZLE
      WeaponLaunchBone = SECONDARY MUZZLE
"""
FILES["RussiaVehicleV25Shilka.ini"] = aa_tank(
    "RussiaVehicleV25Shilka", "RUZSU4TB", "NKZSU23", "NKZSU23w",
    "V25 RussiaShilka / Command_ConstructRussiaShilka. Model NKZSU23. Unique vs NK Shilka object.",
    "Iran_Shilka", SHILKA_TUR, SHILKA_W,
    "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY RussiaV25Gun\n    Weapon = SECONDARY RussiaV25Gun_AA\n  End\n",
    "PRIMARY SECONDARY",
)
FILES["RussiaVehicleV259A52.ini"] = (
    header(
        "V25 RussiaUragan / Nuke_Command_ConstructRussiaUragan. 9A52-4 Tornado. Model RU9A52.",
        "RussiaVehicleV259A52",
        "9A52TB",
    )
    + "  Draw = W3DTruckDraw ModuleTag_01\n"
    + "    OkToChangeModelColor = Yes\n"
    + "    DefaultConditionState\n"
    + "      Model            = RU9A52\n"
    + "      Turret           = TURRET01\n"
    + "      TurretPitch      = TURRETEL02\n"
    + "      WeaponLaunchBone = PRIMARY WEAPONA\n"
    + "      WeaponFireFXBone = PRIMARY WEAPONFX\n"
    + "    End\n"
    + damage_state(
        "RU9A52",
        "      Turret = TURRET01\n      TurretPitch = TURRETEL02\n"
        "      WeaponLaunchBone = PRIMARY WEAPONA\n      WeaponFireFXBone = PRIMARY WEAPONFX\n",
    )
    + "    TrackMarks = EXTireTrack.tga\n"
    + "    LeftFrontTireBone = WHEEL01\n    RightFrontTireBone = WHEEL02\n"
    + "    MidLeftFrontTireBone = WHEEL03\n    MidRightFrontTireBone = WHEEL04\n"
    + "    MidLeftRearTireBone = WHEEL05\n    MidRightRearTireBone = WHEEL06\n"
    + "    LeftRearTireBone = WHEEL07\n    RightRearTireBone = WHEEL08\n"
    + "    TireRotationMultiplier = 0.2\n  End\n"
    + design("Russia_9A52", 4200, 35.0, 300, 180, KIND_VEH)
    + "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY RussiaV25Rocket\n  End\n"
    + ai_turret(pitch="Yes", slots="PRIMARY", rate=60, pitchrate=20)
    + VOICE
    + FOOT.format(hp=420, loco="Generic8x8Locomotor", gx=18, gy=8, gz=10)
)
BUK_TUR = """      Turret = TURRET01
      TurretPitch = TURRETEL01
      WeaponLaunchBone = PRIMARY MISSILE
      WeaponFireFXBone = PRIMARY MUZZLEFX
      WeaponLaunchBone = SECONDARY MISSILE
      WeaponFireFXBone = SECONDARY MUZZLEFX
"""
FILES["RussiaVehicleV25BukM3.ini"] = (
    header(
        "V25 RussiaBukMM3 / Nuke_Command_ConstructRussiaBukMM3. Model BUKMM3 + BUKMM3w.",
        "RussiaVehicleV25BukM3",
        "Bukmm3TB",
    )
    + "  Draw = W3DTankDraw ModuleTag_01\n"
    + "    ExtraPublicBone = CORE\n"
    + "    DefaultConditionState\n"
    + "      Model = BUKMM3\n"
    + BUK_TUR
    + "    End\n"
    + damage_state("BUKMM3", BUK_TUR)
    + "    TrackMarks = EXTnkTrack.tga\n  End\n"
    + wheels_attach("BUKMM3w", TIRE8)
    + design("Russia_BukMM3", 2200, 20.0, 400, 250, KIND_AA)
    + sam_weapons()
    + ai_turret(pitch="Yes", slots="PRIMARY SECONDARY")
    + VOICE
    + FOOT.format(hp=420, loco="CrusaderLocomotor", gx=16, gy=10, gz=11)
)
STRELA_TUR = """      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponFireFXBone = PRIMARY MUZZLE
      WeaponLaunchBone = PRIMARY MUZZLE
"""
FILES["RussiaVehicleV25Strela10.ini"] = aa_tank(
    "RussiaVehicleV25Strela10", "RussiaV25StrelaTB", "RUMTLB", "RUMTLBw",
    "V25 RussiaMTLB / Nuke_Command_ConstructRussiaMTLB. 9K35 Strela-10. Model RUMTLB. Unique vs NK Strela-10 object.",
    "Russia_MTLB", STRELA_TUR, TIRE8,
    "  WeaponSet\n    Conditions = None\n    Weapon = PRIMARY RussiaV25Strela_AA\n    PreferredAgainst = PRIMARY AIRCRAFT\n  End\n",
    "PRIMARY",
)
FILES["RussiaVehicleV25Bastion.ini"] = cruise_truck(
    "RussiaVehicleV25Bastion", "RUK300TB", "RUK300",
    "V25 RussiaBastion / Nuke_Command_ConstructRussiaBastion. K-300P Bastion-P. Model RUK300.",
    "Russia_K300Bastion", "MISS", "MISS", truck_tires_8(), 3000, 30.0, 430,
)

FILES["RussiaWarFactoryV25.ini"] = """; V25 RussiaWarFactory3 identity as an independent SS2 War Factory.
; Object/CommandSet/CommandButton are unique. Does not replace RussiaWarFactory or RussiaWarFactory_T.
; Built from RussiaVehicleDozerm. Tunnel Command_ConstructRussiaPowerStationm stays on slot 1.
Object RussiaWarFactoryV25
  SelectPortrait = RUWARFCIII
  ButtonImage    = RUWARFCIII
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model         = StructureHamVhe
      HideSubObject = GROUND WHEEL WHEEL04 BARBWIRE
    End
    ConditionState = DAMAGED
      Model         = StructureHamVhe
      HideSubObject = GROUND WHEEL WHEEL04 BARBWIRE
    End
    ConditionState = REALLYDAMAGED RUBBLE
      Model         = StructureHamVhe
      HideSubObject = GROUND WHEEL WHEEL04 BARBWIRE
    End
    AliasConditionState = SOLD
    AliasConditionState = SOLD DAMAGED
    AliasConditionState = SOLD REALLYDAMAGED
    AliasConditionState = SOLD NIGHT
    AliasConditionState = SOLD NIGHT DAMAGED
    AliasConditionState = SOLD NIGHT REALLYDAMAGED
    AliasConditionState = SOLD SNOW
    AliasConditionState = SOLD SNOW DAMAGED
    AliasConditionState = SOLD SNOW REALLYDAMAGED
    AliasConditionState = SOLD NIGHT SNOW
    AliasConditionState = SOLD NIGHT SNOW DAMAGED
    AliasConditionState = SOLD NIGHT SNOW REALLYDAMAGED
  End
  PlacementViewAngle = -45
  DisplayName      = Russia_WarFactoryIII
  Side             = Russia
  EditorSorting    = STRUCTURE
  Prerequisites
  End
  BuildCost        = 2000
  BuildTime        = 15.0
  EnergyProduction = -1
  CommandSet       = RussiaWarFactoryV25CommandSet
  VisionRange      = 200.0
  ShroudClearingRange = 200
  ArmorSet
    Conditions = None
    Armor      = StructureArmor
    DamageFX   = StructureDamageFXNoShake
  End
  ExperienceValue = 200 200 200 200
  VoiceSelect = WarFactoryChinaSelect
  SoundOnDamaged       = BuildingDamagedStateLight
  SoundOnReallyDamaged = BuildingDestroy
  UnitSpecificSounds
    UnderConstruction = UnderConstructionLoop
  End
  RadarPriority = STRUCTURE
  KindOf = PRELOAD STRUCTURE SELECTABLE IMMOBILE REPAIR_PAD SCORE CAPTURABLE FS_FACTORY AUTO_RALLYPOINT MP_COUNT_FOR_VICTORY FS_WARFACTORY
  Body = StructureBody ModuleTag_08
    MaxHealth       = 2000.0
    InitialHealth   = 2000.0
    SubdualDamageCap = 2200
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 100
  End
  Behavior = DestroyDie ModuleTag_09
  End
  Behavior = CreateObjectDie ModuleTag_10
    CreationList = OCL_LargeStructureDebris
  End
  Behavior = FXListDie ModuleTag_11
    DeathFX = FX_StructureMediumDeath
  End
  Behavior = ProductionUpdate ModuleTag_12
    NumDoorAnimations            = 0
    DoorOpeningTime              = 5
    DoorWaitOpenTime             = 5
    DoorCloseTime                = 5
    ConstructionCompleteDuration = 5
  End
  Behavior = DefaultProductionExitUpdate ModuleTag_13
    UnitCreatePoint   = X: 0.0 Y:-27.0 Z:0.0
    NaturalRallyPoint = X: 57.0 Y:-27.0 Z:0.0
  End
  Behavior = RepairDockUpdate ModuleTag_14
    TimeForFullHeal         = 5000
    NumberApproachPositions = 5
  End
  Behavior = FlammableUpdate ModuleTag_16
    AflameDuration     = 5000
    AflameDamageAmount = 5
    AflameDamageDelay  = 500
  End
  Behavior = FireWeaponWhenDeadBehavior ModuleTag_KillMarker
    DeathWeapon  = GenericTargetMarkerKiller
    StartsActive = Yes
  End
  Behavior = FireWeaponWhenDeadBehavior ModuleTag_KillMarker2
    DeathWeapon    = GenericTargetMarkerKiller
    StartsActive   = Yes
    RequiredStatus = SOLD
  End
  Behavior = TransitionDamageFX ModuleTag_23
    DamagedParticleSystem1       = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem1 = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem2 = Bone:None RandomBone:No PSys:StructureTransitionMediumExplosion
    ReallyDamagedParticleSystem3 = Bone:None RandomBone:No PSys:StructureTransitionMediumShockwave
  End
  Geometry            = BOX
  GeometryMajorRadius = 60.0
  GeometryMinorRadius = 75.0
  GeometryHeight      = 25.0
  GeometryIsSmall     = No
  FactoryExitWidth    = 25
  Shadow = SHADOW_VOLUME
  BuildCompletion = PLACED_BY_PLAYER
End
"""


def main() -> int:
    for name, text in FILES.items():
        if not text.endswith("\n"):
            text += "\n"
        (OUT / name).write_text(text.replace("\r\n", "\n"), encoding="latin1")
        print("wrote", name, "bytes", len(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
