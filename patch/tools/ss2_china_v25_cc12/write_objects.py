#!/usr/bin/env python3
"""Write Loose INI sources for the 12 V25 China Command Center systems."""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "objects"
OUT.mkdir(exist_ok=True)

FOOTER_TRUCK = """
  VoiceSelect           = AvengerVoiceSelect
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
  RadarPriority = UNIT
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
  GeometryIsSmall     = {gsmall}
End
"""

RADAR_BEH = """
  Behavior = StealthDetectorUpdate ModuleTag_03
    DetectionRate            = 700
    DetectionRange           = {rng}
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained  = No
  End
  Behavior = AIUpdateInterface ModuleTag_99
    AutoAcquireEnemiesWhenIdle = No
  End
"""

AI_TURRET = """
  Behavior = AIUpdateInterface ModuleTag_03
    Turret
      TurretTurnRate        = {turn}
      AllowsPitch           = {pitch}
{pitchrate}      ControlledWeaponSlots = {slots}
    End
    AutoAcquireEnemiesWhenIdle = Yes Stealthed
    MoodAttackCheckRate        = 150
  End
"""

AI_NOTURRET = """
  Behavior = AIUpdateInterface ModuleTag_03
    AutoAcquireEnemiesWhenIdle = Yes Stealthed
    MoodAttackCheckRate        = 150
  End
"""


def footer(hp, gx, gy, gz, gsmall="Yes", loco="Generic8x8Locomotor"):
    return FOOTER_TRUCK.format(hp=hp, gx=gx, gy=gy, gz=gz, gsmall=gsmall, loco=loco)


def turret(turn=180, pitch="No", slots="PRIMARY SECONDARY", pitchrate=None):
    pr = f"      TurretPitchRate       = {pitchrate}\n" if pitchrate else ""
    return AI_TURRET.format(turn=turn, pitch=pitch, slots=slots, pitchrate=pr)


FILES = {}

FILES["ChinaV25CC12_Weapons.ini"] = r"""; Shared unique weapons for V25 China CC systems. SS2-safe clones only.

Weapon ChinaV25CIWS_Gun
  PrimaryDamage            = 25
  PrimaryDamageRadius      = 8.0
  ScatterRadiusVsInfantry  = 20.0
  ScatterRadius            = 11.0
  AttackRange              = 340.0
  MinimumAttackRange       = 15.0
  WeaponRecoil             = 0.4
  DamageType               = GATTLING
  DeathType                = EXTRA_4
  WeaponSpeed              = 9999.0
  ProjectileObject         = 30mm_API-T_Projectile
  ProjectileDetonationFX   = WeaponFX_30mm_API-T_Tracer
  FireSound                = 20mm_fire
  FireFX                   = WeaponFX_HeavyCalibarChainGunsFire_Heli
  RadiusDamageAffects      = ENEMIES NEUTRALS
  DelayBetweenShots        = 20
  ClipSize                 = 2500
  ClipReloadTime           = 3000
  ProjectileCollidesWith   = ENEMIES STRUCTURES
  AntiGround               = Yes
  AntiAirborneVehicle      = No
End

Weapon ChinaV25CIWS_AA
  PrimaryDamage            = 25
  PrimaryDamageRadius      = 8.0
  ScatterRadiusVsInfantry  = 20.0
  ScatterRadius            = 11.0
  AttackRange              = 400.0
  MinimumAttackRange       = 15.0
  WeaponRecoil             = 0.4
  DamageType               = GATTLING
  DeathType                = EXTRA_4
  WeaponSpeed              = 9999.0
  ProjectileObject         = 30mm_API-T_Projectile
  ProjectileDetonationFX   = WeaponFX_30mm_API-T_Tracer
  FireSound                = 20mm_fire
  FireFX                   = WeaponFX_HeavyCalibarChainGunsFire_Heli
  RadiusDamageAffects      = ENEMIES NEUTRALS
  DelayBetweenShots        = 20
  ClipSize                 = 2500
  ClipReloadTime           = 3000
  ProjectileCollidesWith   = ENEMIES STRUCTURES
  AntiGround               = No
  AntiAirborneVehicle      = Yes
  AntiAirborneInfantry     = Yes
  AntiBallisticMissile     = Yes
  AntiSmallMissile         = Yes
End

Weapon ChinaV25SAM_AA
  PrimaryDamage              = 2000.0
  PrimaryDamageRadius        = 5.0
  SecondaryDamage            = 5.0
  SecondaryDamageRadius      = 40
  AttackRange                = 850
  MinimumAttackRange         = 300
  DamageType                 = PENALTY
  DeathType                  = EXPLODED
  WeaponSpeed                = 9999999999
  FireFX                     = FX_LargeSamMissilesTubeOut
  ProjectileObject           = ChinaV25SAM_AA_Object
  FireOCL                    = OCL_48N6TargetLock
  RadiusDamageAffects        = ENEMIES NEUTRALS
  DelayBetweenShots          = 800
  ClipSize                   = 8
  ClipReloadTime             = 8500
  AutoReloadsClip            = Yes
  AntiAirborneVehicle        = Yes
  AntiGround                 = No
  AntiBallisticMissile       = No
  ProjectileDetonationFX     = FX_HeavyAAMImpact
  FireSound                  = Thaad_fire
  AcceptableAimDelta         = 360
End

Weapon ChinaV25SAM_ABM
  PrimaryDamage              = 2000.0
  PrimaryDamageRadius        = 5.0
  SecondaryDamage            = 5.0
  SecondaryDamageRadius      = 40
  AttackRange                = 1700
  MinimumAttackRange         = 600
  DamageType                 = CRUSH
  DeathType                  = EXPLODED
  WeaponSpeed                = 9999999999
  FireFX                     = FX_LargeSamMissilesTubeOut
  ProjectileObject           = ChinaV25SAM_ABM_Object
  FireOCL                    = OCL_40N6STargetLock
  RadiusDamageAffects        = ENEMIES NEUTRALS
  DelayBetweenShots          = 800
  ClipSize                   = 8
  ClipReloadTime             = 8500
  AutoReloadsClip            = Yes
  AntiAirborneVehicle        = No
  AntiGround                 = No
  AntiBallisticMissile       = Yes
  AntiSmallMissile           = Yes
  ProjectileCollidesWith     = ENEMIES
  ProjectileDetonationFX     = FX_HeavyAAMImpact
  FireSound                  = Thaad_fire
  AcceptableAimDelta         = 360
  ShowsAmmoPips              = Yes
End

Weapon ChinaV25SAM_ABM_Fuze
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

Object ChinaV25SAM_AA_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = Engine01 Spec_SAMRMFlare
      ParticleSysBone = Engine01 Spec_SAMRMTrail
    End
  End
  DisplayName   = China_HQ-9
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

Object ChinaV25SAM_ABM_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = ENGINEFX LargeSAMMissileTrail2
      ParticleSysBone = ENGINEFX LargeSAMMissilesFlare2
    End
  End
  DisplayName   = China_HQ-9
  EditorSorting = SYSTEM
  ArmorSet
    Conditions = None
    Armor      = HeavyAntiAirMissileArmor
    DamageFX   = None
  End
  KindOf = PROJECTILE SMALL_MISSILE CAN_ATTACK
  Body = ActiveBody ModuleTag_02
    MaxHealth     = 240.0
    InitialHealth = 240.0
  End
  Behavior = FireWeaponUpdate ModuleTag_FUZE1
    Weapon = ChinaV25SAM_ABM_Fuze
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
  Behavior = FireWeaponUpdate ModuleTag_SpeedChanging3
    Weapon       = AAM_Boosters_Igniter
    InitialDelay = 800
  End
  Behavior = PhysicsBehavior ModuleTag_06
    Mass = 2
  End
  Behavior = MissileAIUpdate ModuleTag_07
    DetonateCallsKill             = Yes
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

Weapon ChinaV25AFT10_ATGM
  PrimaryDamage           = 40.0
  PrimaryDamageRadius     = 5.0
  ScatterRadiusVsInfantry = 10.0
  AttackRange             = 250.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 600
  ProjectileDetonationFX  = WeaponFX_RocketBuggyMissileDetonation
  ProjectileObject        = MissileDefenderMissile
  ProjectileExhaust       = PatriotMissileTrail
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots       = 1000
  ClipSize                = 8
  ClipReloadTime          = 8000
  AutoReloadsClip         = Yes
  FireSound               = MissileDefenderWeapon
  AntiGround              = Yes
  AntiAirborneVehicle     = No
  AcceptableAimDelta      = 180.0
  ProjectileCollidesWith  = STRUCTURES
End

Weapon ChinaV25Cruise
  PrimaryDamage               = 150.0
  PrimaryDamageRadius         = 10.0
  SecondaryDamage             = 50.0
  SecondaryDamageRadius       = 25.0
  ScatterRadiusVsInfantry     = 20.0
  AttackRange                 = 500.0
  PreAttackDelay              = 250
  PreAttackType               = PER_SHOT
  MinimumAttackRange          = 100.0
  DamageType                  = EXPLOSION
  DeathType                   = EXPLODED
  FireFX                      = FX_TomahawkIgnition
  ProjectileObject            = TomahawkMissile
  ProjectileExhaust           = TomahawkMissileExhaust
  ProjectileDetonationFX      = WeaponFX_BombTruckDefaultBombDetonation
  RadiusDamageAffects         = SELF ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound                   = TomahawkWeapon
  DelayBetweenShots           = 1500
  ClipSize                    = 3
  ClipReloadTime              = 8000
  AutoReloadsClip             = Yes
  AntiGround                  = Yes
  ShowsAmmoPips               = Yes
  ProjectileCollidesWith      = STRUCTURES
  CapableOfFollowingWaypoints = Yes
End

Weapon ChinaV25MLRS
  PrimaryDamage               = 80.0
  PrimaryDamageRadius         = 12.0
  SecondaryDamage             = 40.0
  SecondaryDamageRadius       = 20.0
  ScatterRadiusVsInfantry     = 20.0
  AttackRange                 = 400.0
  MinimumAttackRange          = 80.0
  DamageType                  = EXPLOSION
  DeathType                   = EXPLODED
  FireFX                      = FX_TomahawkIgnition
  ProjectileObject            = TomahawkMissile
  ProjectileExhaust           = TomahawkMissileExhaust
  ProjectileDetonationFX      = WeaponFX_BombTruckDefaultBombDetonation
  RadiusDamageAffects         = SELF ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound                   = TomahawkWeapon
  DelayBetweenShots           = 400
  ClipSize                    = 6
  ClipReloadTime              = 8000
  AutoReloadsClip             = Yes
  AntiGround                  = Yes
  ShowsAmmoPips               = Yes
  ProjectileCollidesWith      = STRUCTURES
End
"""

# 1 FK-2000
FILES["ChinaVehicleV25FK2000.ini"] = """; V25 ChinaFK2000 / Command_ConstructChinaFK2000
; ChinaSupplyCenterCommandSet slot 10. Model FK2000. Turret SYSTEM / ANGLE.
Object ChinaVehicleV25FK2000
  SelectPortrait = FK2000TB
  ButtonImage    = FK2000TB
  Draw = W3DTruckDraw ModuleTag_01
    DefaultConditionState
      Model            = FK2000
      Animation        = FK2000.FK2000
      AnimationMode    = LOOP
      Turret           = SYSTEM
      TurretPitch      = ANGLE
      WeaponFireFXBone = PRIMARY   GUN_FIRE
      WeaponLaunchBone = PRIMARY   GUN_FIRE
      WeaponFireFXBone = SECONDARY GUN_FIRE
      WeaponLaunchBone = SECONDARY GUN_FIRE
      WeaponLaunchBone = TERTIARY  MISSILE
      WeaponFireFXBone = TERTIARY  MISSILE
    End
    ConditionState = REALLYDAMAGED
      Model            = FK2000
      Animation        = FK2000.FK2000
      AnimationMode    = LOOP
      Turret           = SYSTEM
      TurretPitch      = ANGLE
      WeaponFireFXBone = PRIMARY   GUN_FIRE
      WeaponLaunchBone = PRIMARY   GUN_FIRE
      WeaponFireFXBone = SECONDARY GUN_FIRE
      WeaponLaunchBone = SECONDARY GUN_FIRE
      WeaponLaunchBone = TERTIARY  MISSILE
      WeaponFireFXBone = TERTIARY  MISSILE
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = TIRE01
    RightFrontTireBone     = TIRE02
    MidLeftFrontTireBone   = TIRE03
    MidRightFrontTireBone  = TIRE04
    MidLeftRearTireBone    = TIRE05
    MidRightRearTireBone   = TIRE06
    LeftRearTireBone       = TIRE07
    RightRearTireBone      = TIRE08
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_FK-2000
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   ChinaV25CIWS_Gun
    Weapon            = SECONDARY ChinaV25CIWS_AA
    Weapon            = TERTIARY  ChinaV25SAM_AA
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = TERTIARY  FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   INFANTRY VEHICLE
    PreferredAgainst  = SECONDARY AIRCRAFT
    PreferredAgainst  = TERTIARY  AIRCRAFT
  End
  BuildCost = 1500
  BuildTime = 15.0
  VisionRange = 300
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(pitch="Yes", pitchrate=180, slots="PRIMARY SECONDARY TERTIARY") + footer(400, 13, 9, 10)

# 2 AFT-10
FILES["ChinaVehicleV25AFT10.ini"] = """; V25 ChinaAFT10 / Command_ConstructChinaAFT10
; ChinaSupplyCenterCommandSet slot 12. Model CHAFT10. Not CHAFT10w attach.
Object ChinaVehicleV25AFT10
  SelectPortrait = AFT10TB
  ButtonImage    = AFT10TB
  Draw = W3DTankDraw ModuleTag_01
    DefaultConditionState
      Model            = CHAFT10
      Turret           = Turret01
      WeaponLaunchBone = PRIMARY MISS
      WeaponFireFXBone = PRIMARY MISS
    End
    ConditionState = REALLYDAMAGED
      Model            = CHAFT10
      Turret           = Turret01
      WeaponLaunchBone = PRIMARY MISS
      WeaponFireFXBone = PRIMARY MISS
    End
    TrackMarks = EXTnkTrack.tga
  End
  DisplayName = China_AFT10
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY ChinaV25AFT10_ATGM
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY VEHICLE STRUCTURE
  End
  BuildCost = 1300
  BuildTime = 14.0
  VisionRange = 175
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=80, slots="PRIMARY") + footer(350, 22, 9, 13, "No", "CrusaderLocomotor")

# 3 HQ-11
FILES["ChinaVehicleV25HQ11.ini"] = """; V25 ChinaHQ11 / Command_ConstructChinaHQ11
; ChinaSupplyCenterCommandSet slot 13. Model HQ11. No HQ11RD attach, no riders.
Object ChinaVehicleV25HQ11
  SelectPortrait = CHHQ11TB
  ButtonImage    = CHHQ11TB
  Draw = W3DTruckDraw ModuleTag_01
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = HQ11
      Animation        = HQ11.HQ11
      AnimationMode    = ONCE
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MUZZLEFX
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MUZZLEFX
    End
    ConditionState = REALLYDAMAGED
      Model            = HQ11
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MUZZLEFX
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MUZZLEFX
    End
    TrackMarks             = EXTireTrack.tga
    RightFrontTireBone     = WHEEL05
    LeftFrontTireBone      = WHEEL01
    MidRightFrontTireBone  = WHEEL06
    MidLeftFrontTireBone   = WHEEL02
    MidLeftRearTireBone    = WHEEL03
    MidRightRearTireBone   = WHEEL07
    RightRearTireBone      = WHEEL08
    LeftRearTireBone       = WHEEL04
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_HQ-11
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   ChinaV25SAM_AA
    Weapon            = SECONDARY ChinaV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 2000
  BuildTime = 48.0
  VisionRange = 1200
  ShroudClearingRange = 250
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + AI_NOTURRET + footer(300, 25, 9, 15)

# 4 LD-2000
FILES["ChinaVehicleV25LD2000.ini"] = """; V25 ChinaLD2000 / Command_ConstructChinaLD2000
; New_ChinaWarFactoryCommandSet slot 10. Model SDLD2000.
Object ChinaVehicleV25LD2000
  SelectPortrait = LD2000TB
  ButtonImage    = LD2000TB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model            = SDLD2000
      Animation        = SDLD2000.SDLD2000
      AnimationMode    = LOOP
      Turret           = TURRET
      TurretPitch      = TURRETHEL
      WeaponFireFXBone = PRIMARY   GUN_FIRE
      WeaponLaunchBone = PRIMARY   GUN_FIRE
      WeaponFireFXBone = SECONDARY GUN_FIRE
      WeaponLaunchBone = SECONDARY GUN_FIRE
      WeaponLaunchBone = TERTIARY  MISSILE
      WeaponFireFXBone = TERTIARY  MISSILE
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = TIRE01
    RightFrontTireBone     = TIRE02
    MidLeftFrontTireBone   = TIRE03
    MidRightFrontTireBone  = TIRE04
    MidLeftRearTireBone    = TIRE05
    MidRightRearTireBone   = TIRE06
    LeftRearTireBone       = TIRE07
    RightRearTireBone      = TIRE08
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_LD-2000
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   ChinaV25CIWS_Gun
    Weapon            = SECONDARY ChinaV25CIWS_AA
    Weapon            = TERTIARY  ChinaV25SAM_AA
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = TERTIARY  FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   INFANTRY VEHICLE
    PreferredAgainst  = SECONDARY AIRCRAFT
    PreferredAgainst  = TERTIARY  AIRCRAFT
  End
  BuildCost = 1400
  BuildTime = 15.0
  VisionRange = 300
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(pitch="Yes", pitchrate=180, slots="PRIMARY SECONDARY TERTIARY") + footer(400, 13, 9, 10)

# 5 HQ-9
FILES["ChinaVehicleV25HQ9.ini"] = """; V25 ChinaHQ9 / Command_ConstructChinaHQ9
; New_ChinaWarFactoryCommandSet slot 9. Model SDCHH9. Independent of SS2 ChinaVehicleHQ9.
Object ChinaVehicleV25HQ9
  SelectPortrait = HQ9
  ButtonImage    = HQ9
  Draw = W3DTruckDraw ModuleTag_01
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = SDCHH9
      Animation        = SDCHH9.SDCHH9
      AnimationMode    = ONCE
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MUZZLEFX
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MUZZLEFX
    End
    ConditionState = REALLYDAMAGED
      Model            = SDCHH9
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MUZZLEFX
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MUZZLEFX
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL02
    MidLeftFrontTireBone   = WHEEL03
    MidRightFrontTireBone  = WHEEL04
    MidLeftRearTireBone    = WHEEL05
    MidRightRearTireBone   = WHEEL06
    LeftRearTireBone       = WHEEL07
    RightRearTireBone      = WHEEL08
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_HQ-9
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   ChinaV25SAM_AA
    Weapon            = SECONDARY ChinaV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 3000
  BuildTime = 48.0
  VisionRange = 1200
  ShroudClearingRange = 250
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + AI_NOTURRET + footer(350, 25, 9, 15)

# 6 HT-233
FILES["ChinaVehicleV25HT233.ini"] = """; V25 ChinaVehicleListeningOutpost labeled China_HT-233
; New_ChinaWarFactoryCommandSet slot 7. Model SDHT233. Independent of SS2 ChinaVehicleHT233.
; W3D has Wheel01-06 only; V25 Wheel07-10 / CAB / TRAILER not mapped.
Object ChinaVehicleV25HT233
  SelectPortrait = ZZM88
  ButtonImage    = ZZM88
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model         = SDHT233
      Animation     = SDHT233.SDHT233
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model         = SDHT233
      Animation     = SDHT233.SDHT233
      AnimationMode = LOOP
    End
    TrackMarks             = EXTireTrack.tga
    RightFrontTireBone     = Wheel01
    LeftFrontTireBone      = Wheel02
    MidRightFrontTireBone  = Wheel03
    MidLeftFrontTireBone   = Wheel04
    MidRightMidTireBone    = Wheel05
    MidLeftMidTireBone     = Wheel06
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_HT-233
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY NONE
  End
  BuildCost = 2500
  BuildTime = 15.0
  VisionRange = 1800
  ShroudClearingRange = 800
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE REVEALS_ENEMY_PATHS CANNOT_RETALIATE
""" + RADAR_BEH.format(rng=1800) + footer(350, 22, 9, 13, "No")

# 7 HQ-16
FILES["ChinaVehicleV25HQ16.ini"] = """; V25 ChinaTankHQ16 / Command_ConstructChinaTankHQ16
; New_ChinaWarFactoryCommandSet slot 8. Model SDHQ16. Wheels 01-06 only.
Object ChinaVehicleV25HQ16
  SelectPortrait = HQ16TB
  ButtonImage    = HQ16TB
  Draw = W3DTruckDraw ModuleTag_01
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = SDHQ16
      Animation        = SDHQ16.SDHQ16
      AnimationMode    = ONCE
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MUZZLEFX
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MUZZLEFX
    End
    ConditionState = REALLYDAMAGED
      Model            = SDHQ16
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MUZZLEFX
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MUZZLEFX
    End
    TrackMarks             = EXTireTrack.tga
    RightFrontTireBone     = Wheel01
    LeftFrontTireBone      = Wheel02
    MidRightFrontTireBone  = Wheel03
    MidLeftFrontTireBone   = Wheel04
    MidRightMidTireBone    = WHEEL05
    MidLeftMidTireBone     = WHEEL06
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_HQ16
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   ChinaV25SAM_AA
    Weapon            = SECONDARY ChinaV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 2800
  BuildTime = 48.0
  VisionRange = 1000
  ShroudClearingRange = 250
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + AI_NOTURRET + footer(320, 25, 9, 15)

# 8 HQ-7B
FILES["ChinaVehicleV25HQ7B.ini"] = """; V25 ChinaTankHQ7B / Command_ConstructChinaHQ7B
; New_ChinaWarFactoryCommandSet slot 6. Model SDHQ7. TURTTQ pitch bone absent; no TurretPitch.
Object ChinaVehicleV25HQ7B
  SelectPortrait = HQ7BTB
  ButtonImage    = HQ7BTB
  Draw = W3DTruckDraw ModuleTag_01
    DefaultConditionState
      Model            = SDHQ7
      Turret           = TURRET
      WeaponFireFXBone = PRIMARY MUZZLEFX
      WeaponLaunchBone = PRIMARY MUZZLE
    End
    ConditionState = REALLYDAMAGED
      Model            = SDHQ7
      Turret           = TURRET
      WeaponFireFXBone = PRIMARY MUZZLEFX
      WeaponLaunchBone = PRIMARY MUZZLE
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = WHEEL06
    RightFrontTireBone     = WHEEL01
    MidRightRearTireBone   = WHEEL02
    MidLeftRearTireBone    = WHEEL05
    LeftRearTireBone       = WHEEL04
    RightRearTireBone      = WHEEL03
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_HQ7B
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   ChinaV25SAM_AA
    Weapon            = SECONDARY ChinaV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 1050
  BuildTime = 12.0
  VisionRange = 200
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=120, slots="PRIMARY SECONDARY") + footer(280, 16, 6, 12.5)

# 9 HQ-7B Radar
FILES["ChinaVehicleV25HQ7BRadar.ini"] = """; V25 ChinaHQ7Radar / Command_ConstructChinaHQ7Radar
; New_ChinaWarFactoryCommandSet slot 5. Model HQ7RD.
Object ChinaVehicleV25HQ7BRadar
  SelectPortrait = HQ7BRD
  ButtonImage    = HQ7BRD
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model         = HQ7RD
      Animation     = HQ7RD.HQ7RD
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model         = HQ7RD
      Animation     = HQ7RD.HQ7RD
      AnimationMode = LOOP
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = WHEEL06
    RightFrontTireBone     = WHEEL01
    MidRightRearTireBone   = WHEEL02
    MidLeftRearTireBone    = WHEEL05
    LeftRearTireBone       = WHEEL04
    RightRearTireBone      = WHEEL03
    TireRotationMultiplier = 0.2
  End
  DisplayName = HQ-7-Radar
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY NONE
  End
  BuildCost = 2500
  BuildTime = 15.0
  VisionRange = 1800
  ShroudClearingRange = 800
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE REVEALS_ENEMY_PATHS CANNOT_RETALIATE
""" + RADAR_BEH.format(rng=1800) + footer(350, 22, 9, 13, "No")

# 10 YJ-62A
FILES["ChinaVehicleV25YJ62A.ini"] = """; V25 ChinaYJ62A / Command_ConstructChinaYJ62A
; ChinaHvyWarFactoryCommandSet slot 10. Model SDYJ62A. No TURRETEL bone.
Object ChinaVehicleV25YJ62A
  SelectPortrait = YJ62ATB
  ButtonImage    = YJ62ATB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model            = SDYJ62A
      Turret           = TURRET
      WeaponLaunchBone = PRIMARY WEAPONA
      WeaponFireFXBone = PRIMARY FIREPOINT
    End
    ConditionState = REALLYDAMAGED
      Model  = SDYJ62A
      Turret = TURRET
      WeaponLaunchBone = PRIMARY WEAPONA
      WeaponFireFXBone = PRIMARY FIREPOINT
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = KOLESO05
    RightFrontTireBone     = KOLESO01
    LeftRearTireBone       = KOLESO08
    RightRearTireBone      = KOLESO04
    MidLeftFrontTireBone   = KOLESO06
    MidRightFrontTireBone  = KOLESO02
    MidLeftRearTireBone    = KOLESO07
    MidRightRearTireBone   = KOLESO03
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_YJ-62A
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY ChinaV25Cruise
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY VEHICLE STRUCTURE
  End
  BuildCost = 8000
  BuildTime = 10.0
  VisionRange = 400
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=40, slots="PRIMARY") + footer(400, 30, 12, 10)

# 11 CJ-10  (V25 object ChinaTankYJ62, label China_CJ10 — not YJ-62A)
FILES["ChinaVehicleV25CJ10.ini"] = """; V25 ChinaTankYJ62 labeled China_CJ10 / Command_ConstructChinaTankYJ62
; ChinaHvyWarFactoryCommandSet slot 4. Model SDCJ10. Not ChinaYJ62A.
Object ChinaVehicleV25CJ10
  SelectPortrait = CJ10TB
  ButtonImage    = CJ10TB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model            = SDCJ10
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponLaunchBone = PRIMARY WEAPONA
      WeaponFireFXBone = PRIMARY FIREPOINT
    End
    ConditionState = REALLYDAMAGED
      Model            = SDCJ10
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponLaunchBone = PRIMARY WEAPONA
      WeaponFireFXBone = PRIMARY FIREPOINT
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = KOLESO05
    RightFrontTireBone     = KOLESO01
    LeftRearTireBone       = KOLESO08
    RightRearTireBone      = KOLESO04
    MidLeftFrontTireBone   = KOLESO06
    MidRightFrontTireBone  = KOLESO02
    MidLeftRearTireBone    = KOLESO07
    MidRightRearTireBone   = KOLESO03
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_CJ10
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TruckArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY ChinaV25Cruise
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY VEHICLE STRUCTURE
  End
  BuildCost = 7000
  BuildTime = 10.0
  VisionRange = 400
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=40, pitch="Yes", pitchrate=40, slots="PRIMARY") + footer(370, 30, 12, 10)

# 12 WS-3 (V25 ChinaTanksy400rocket labeled China_WS3 — not ChinaTankWS3/PHL-03)
FILES["ChinaVehicleV25WS3.ini"] = """; V25 ChinaTanksy400rocket labeled China_WS3 / Command_ConstructChinaTanksy400rocket
; ChinaHvyWarFactoryCommandSet slot 3. Model SDCHWS2. Not ChinaTankWS3 (PHL-03).
Object ChinaVehicleV25WS3
  SelectPortrait = WS3TB
  ButtonImage    = WS3TB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model            = SDCHWS2
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponLaunchBone = PRIMARY FIREPOINT
      WeaponFireFXBone = PRIMARY FIREFX
    End
    ConditionState = REALLYDAMAGED
      Model            = SDCHWS2
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponLaunchBone = PRIMARY FIREPOINT
      WeaponFireFXBone = PRIMARY FIREFX
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = Tire01
    RightFrontTireBone     = Tire02
    MidLeftRearTireBone    = Tire03
    MidRightRearTireBone   = Tire04
    LeftRearTireBone       = Tire05
    RightRearTireBone      = Tire06
    MidRightMidTireBone    = Tire07
    MidLeftMidTireBone     = Tire08
    TireRotationMultiplier = 0.2
  End
  DisplayName = China_WS3
  Side        = China
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY ChinaV25MLRS
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY VEHICLE STRUCTURE
  End
  BuildCost = 2300
  BuildTime = 20.0
  VisionRange = 400
  ShroudClearingRange = 250
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=80, pitch="Yes", pitchrate=80, slots="PRIMARY") + footer(370, 32, 10, 17, "No")


def main() -> None:
    for name, text in FILES.items():
        path = OUT / name
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text, encoding="latin1")
        print("wrote", path.name, path.stat().st_size)


if __name__ == "__main__":
    main()
