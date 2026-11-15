#!/usr/bin/env python3
"""Write Loose INI sources for the 8 V25 England Command Center systems."""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "objects"
OUT.mkdir(exist_ok=True)

FOOTER = """
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
  GeometryIsSmall     = Yes
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

AI_IDLE = """
  Behavior = AIUpdateInterface ModuleTag_03
    AutoAcquireEnemiesWhenIdle = {acquire}
    MoodAttackCheckRate        = 150
  End
"""

AI_ALT = """
  Behavior = AIUpdateInterface ModuleTag_03
    Turret
      TurretTurnRate        = {turn}
      AllowsPitch           = {pitch}
{pitchrate}      ControlledWeaponSlots = PRIMARY
    End
    AltTurret
      ControlledWeaponSlots = SECONDARY
      TurretTurnRate        = 100.0
      AllowsPitch           = No
      FiresWhileTurning     = Yes
    End
    AutoAcquireEnemiesWhenIdle = Yes Stealthed
    TurretsLinked              = No
    MoodAttackCheckRate        = 150
  End
"""


def footer(hp, gx, gy, gz, loco="Generic8x8Locomotor"):
    return FOOTER.format(hp=hp, gx=gx, gy=gy, gz=gz, loco=loco)


def turret(turn=180, pitch="No", slots="PRIMARY", pitchrate=None):
    pr = f"      TurretPitchRate       = {pitchrate}\n" if pitchrate else ""
    return AI_TURRET.format(turn=turn, pitch=pitch, slots=slots, pitchrate=pr)


def idle(acquire="Yes Stealthed"):
    return AI_IDLE.format(acquire=acquire)


def alt(turn=90, pitch="No", pitchrate=None):
    pr = f"      TurretPitchRate       = {pitchrate}\n" if pitchrate else ""
    return AI_ALT.format(turn=turn, pitch=pitch, pitchrate=pr)


FILES = {}

FILES["BritainV25CC8_Weapons.ini"] = r"""; Unique SS2-safe weapons for V25 England CC systems.

Weapon BritainV25SkySabre_AA
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = PENALTY
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = BritainV25SkySabreMissile
  FireOCL                = OCL_48N6TargetLock
  RadiusDamageAffects    = ENEMIES NEUTRALS
  DelayBetweenShots      = 5000
  ClipSize               = 8
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

Weapon BritainV25SkySabre_ABM
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = CRUSH
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = BritainV25SkySabreABM
  FireOCL                = OCL_40N6STargetLock
  RadiusDamageAffects    = ENEMIES NEUTRALS
  DelayBetweenShots      = 5000
  ClipSize               = 8
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

Weapon BritainV25SkySabre_ABM_Fuze
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

Object BritainV25SkySabreMissile
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = Engine01 Spec_SAMRMFlare
      ParticleSysBone = Engine01 Spec_SAMRMTrail
    End
  End
  DisplayName   = UK_Sky-Sabre
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

Object BritainV25SkySabreABM
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = ENGINEFX LargeSAMMissileTrail2
      ParticleSysBone = ENGINEFX LargeSAMMissilesFlare2
    End
  End
  DisplayName   = UK_Sky-Sabre
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
    Weapon = BritainV25SkySabre_ABM_Fuze
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

Weapon BritainV25CRAM_Gun
  PrimaryDamage            = 25
  PrimaryDamageRadius      = 8.0
  ScatterRadiusVsInfantry  = 20.0
  ScatterRadius            = 11.0
  AttackRange              = 340.0
  MinimumAttackRange       = 15.0
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

Weapon BritainV25CRAM_AA
  PrimaryDamage            = 25
  PrimaryDamageRadius      = 8.0
  ScatterRadiusVsInfantry  = 20.0
  ScatterRadius            = 11.0
  AttackRange              = 400.0
  MinimumAttackRange       = 15.0
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

Weapon BritainV25Cougar_MG
  PrimaryDamage       = 10.0
  PrimaryDamageRadius = 0.0
  AttackRange         = 150.0
  DamageType          = COMANCHE_VULCAN
  DeathType           = NORMAL
  WeaponSpeed         = 600
  ProjectileObject    = NONE
  FireFX              = WeaponFX_TechnicalGunFire
  FireSound           = HumveeWeapon
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots   = 200
  ClipSize            = 0
  ClipReloadTime      = 0
End

Weapon BritainV25Challenger_Gun
  PrimaryDamage          = 80.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 175.0
  DamageType             = ARMOR_PIERCING
  DeathType              = EXPLODED
  WeaponSpeed            = 400
  ProjectileObject       = GenericTankShell
  FireFX                 = WeaponFX_GenericTankGunNoTracer
  ProjectileDetonationFX = WeaponFX_GenericTankShellDetonation
  FireSound              = ScorpionTankWeapon
  RadiusDamageAffects    = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots      = 2000
  ClipSize               = 0
  ClipReloadTime         = 0
End

Weapon BritainV25Rapier_AA
  PrimaryDamage          = 195.0
  PrimaryDamageRadius    = 35.0
  ScatterRadiusVsInfantry = 10.0
  AttackRange            = 300.0
  MinimumAttackRange     = 5.0
  DamageType             = EXPLOSION
  DeathType              = EXPLODED
  WeaponSpeed            = 800
  ProjectileObject       = PatriotMissile
  ProjectileExhaust      = PatriotMissileTrail
  RadiusDamageAffects    = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots      = 2500
  ClipSize               = 8
  ClipReloadTime         = 19000
  AutoReloadsClip        = Yes
  FireSound              = TankHunterWeapon
  FireFX                 = FX_BuggyMissileIgnition
  ProjectileDetonationFX = WeaponFX_RocketBuggyMissileDetonation
  AntiAirborneVehicle    = Yes
  AntiGround             = No
  ShowsAmmoPips          = Yes
End

Weapon BritainV25Stormer_AA
  PrimaryDamage          = 195.0
  PrimaryDamageRadius    = 35.0
  ScatterRadiusVsInfantry = 10.0
  AttackRange            = 300.0
  MinimumAttackRange     = 5.0
  DamageType             = EXPLOSION
  DeathType              = EXPLODED
  WeaponSpeed            = 800
  ProjectileObject       = PatriotMissile
  ProjectileExhaust      = PatriotMissileTrail
  RadiusDamageAffects    = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots      = 2000
  ClipSize               = 8
  ClipReloadTime         = 16000
  AutoReloadsClip        = Yes
  FireSound              = TankHunterWeapon
  FireFX                 = FX_BuggyMissileIgnition
  ProjectileDetonationFX = WeaponFX_RocketBuggyMissileDetonation
  AntiAirborneVehicle    = Yes
  AntiBallisticMissile   = Yes
  AntiGround             = No
  ShowsAmmoPips          = Yes
End

Weapon BritainV25FV432S_Mortar
  PrimaryDamage           = 250.0
  PrimaryDamageRadius     = 25.0
  ScatterRadiusVsInfantry = 10
  AttackRange             = 450
  MinimumAttackRange      = 20.0
  MinTargetPitch          = -90
  MaxTargetPitch          = 79
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 300
  MinWeaponSpeed          = 75
  ScaleWeaponSpeed        = Yes
  ProjectileObject        = 155mm_Shell
  FireFX                  = WeaponFX_GenericTankGunNoTracer
  FireSound               = InfernoCannonWeapon
  ProjectileDetonationFX  = FX_UnguidedRocketExplosion
  RadiusDamageAffects     = ENEMIES NEUTRALS ALLIES
  DelayBetweenShots       = 3000
  ClipSize                = 0
  ClipReloadTime          = 0
  PreAttackDelay          = 200
  PreAttackType           = PER_SHOT
End

Weapon BritainV25FV432S_MG
  PrimaryDamage       = 30.0
  PrimaryDamageRadius = 0.0
  AttackRange         = 150.0
  DamageType          = COMANCHE_VULCAN
  DeathType           = NORMAL
  WeaponSpeed         = 600
  ProjectileObject    = NONE
  FireFX              = WeaponFX_TechnicalGunFire
  FireSound           = HumveeWeapon
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots   = 200
  ClipSize            = 0
  ClipReloadTime      = 0
End
"""

FILES["BritainVehicleV25SkySabre.ini"] = """; V25 UKSkySabre / Command_ConstructUKSkySabre
; UKWarFactoryIICommandSet slot 1. Model SkySabre. Not SS2 BritainSkySabre structure.
Object BritainVehicleV25SkySabre
  SelectPortrait = SKYSBRTB
  ButtonImage    = SKYSBRTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = SkySabre
      Animation        = SkySabre.SkySabre
      AnimationMode    = MANUAL
      Flags            = START_FRAME_LAST
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MISSILE_C
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MISSILE_C
    End
    ConditionState = REALLYDAMAGED
      Model            = SkySabre
      Animation        = SkySabre.SkySabre
      AnimationMode    = MANUAL
      Flags            = START_FRAME_LAST
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MISSILE_C
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MISSILE_C
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
  DisplayName   = UK_Sky-Sabre
  Side          = Britain
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   BritainV25SkySabre_AA
    Weapon            = SECONDARY BritainV25SkySabre_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 2000
  BuildTime = 48.0
  VisionRange = 1200
  ShroudClearingRange = 175
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + idle() + footer(240, 25, 9, 15)

FILES["BritainVehicleV25Giraffe.ini"] = """; V25 UKGiraffe / Command_ConstructUKGiraffe
; UKWarFactoryIICommandSet slot 2. Model SKYSRBR.
Object BritainVehicleV25Giraffe
  SelectPortrait = SKYSBRRTB
  ButtonImage    = SKYSBRRTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model         = SKYSRBR
      Animation     = SKYSRBR.SKYSRBR
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model         = SKYSRBR
      Animation     = SKYSRBR.SKYSRBR
      AnimationMode = LOOP
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
  DisplayName   = UK_Giraffe
  Side          = Britain
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
  BuildCost = 1650
  BuildTime = 10.0
  VisionRange = 1800
  ShroudClearingRange = 800
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE REVEALS_ENEMY_PATHS CANNOT_RETALIATE

  Behavior = StealthDetectorUpdate ModuleTag_03
    DetectionRate            = 700
    DetectionRange           = 1800
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained  = No
  End
""" + idle("No") + footer(350, 22, 9, 13)

FILES["BritainVehicleV25CRAM.ini"] = """; V25 UKPhlanx / Command_ConstructUKPhlanx
; Lazr_AmericaWarFactoryCommandSet slot 13. Model SDUKPX. Not AmericaVehicleCRAM / SDCRAM.
Object BritainVehicleV25CRAM
  SelectPortrait = AmericaPhlanx
  ButtonImage    = AmericaPhlanx
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model            = SDUKPX
      Turret           = TURRETH
      TurretPitch      = TURRETHEL
      WeaponFireFXBone = PRIMARY   FIRE01
      WeaponLaunchBone = PRIMARY   FIRE01
      WeaponFireFXBone = SECONDARY FIRE01
      WeaponLaunchBone = SECONDARY FIRE01
    End
    ConditionState = REALLYDAMAGED
      Model            = SDUKPX
      Turret           = TURRETH
      TurretPitch      = TURRETHEL
      WeaponFireFXBone = PRIMARY   FIRE01
      WeaponLaunchBone = PRIMARY   FIRE01
      WeaponFireFXBone = SECONDARY FIRE01
      WeaponLaunchBone = SECONDARY FIRE01
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL08
    MidRightFrontTireBone  = WHEEL07
    MidLeftFrontTireBone   = WHEEL02
    MidLeftRearTireBone    = WHEEL03
    MidRightRearTireBone   = WHEEL06
    LeftRearTireBone       = WHEEL05
    RightRearTireBone      = WHEEL04
    TireRotationMultiplier = 0.2
  End
  DisplayName   = America_Phlanx
  Side          = Britain
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   BritainV25CRAM_Gun
    Weapon            = SECONDARY BritainV25CRAM_AA
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   INFANTRY VEHICLE STRUCTURE
    PreferredAgainst  = SECONDARY AIRCRAFT BALLISTIC_MISSILE
  End
  BuildCost = 1300
  BuildTime = 15.0
  VisionRange = 300
  ShroudClearingRange = 300
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=180, pitch="Yes", slots="PRIMARY SECONDARY", pitchrate=180) + footer(300, 13, 9, 10)

FILES["BritainVehicleV25Cougar.ini"] = """; V25 Cougar MRAP. Lazr_Command_ConstructAmericaTankCrusader
; Object Lazr_AmericaTankCrusader / Model UKCougar. TURRETEL absent.
Object BritainVehicleV25Cougar
  SelectPortrait = EgyMrap
  ButtonImage    = EgyMrap
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model             = UKCougar
      Turret            = TURRET
      WeaponFireFXBone  = PRIMARY MUZZLE01
      WeaponMuzzleFlash = PRIMARY MUZZLE01
      WeaponLaunchBone  = PRIMARY MUZZLE01
    End
    TrackMarks             = EXTireTrack.tga
    Dust                   = RocketBuggyDust
    DirtSpray              = RocketBuggyDirtSpray
    LeftFrontTireBone      = TIRE01
    RightFrontTireBone     = TIRE02
    LeftRearTireBone       = TIRE03
    RightRearTireBone      = TIRE04
    TireRotationMultiplier = 0.2
  End
  DisplayName   = America_Mrap
  Side          = Britain
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY BritainV25Cougar_MG
  End
  BuildCost = 800
  BuildTime = 20.0
  VisionRange = 200
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=120, pitch="No", slots="PRIMARY") + footer(600, 28, 16, 12)

FILES["BritainVehicleV25Challenger.ini"] = """; V25 UKChallenger3 / Command_ConstructUKChallenger3
; UKWarFactoryIICommandSet slot 4. Hull UKCHNGR3 + wheels UKCHNGR3w on CORE.
; TURRETEL01/Barrel01 absent. Not SS2 BritainTankChallenger2 / LSFChallenger2.
Object BritainVehicleV25Challenger
  SelectPortrait = UKCHLNGR3TB
  ButtonImage    = UKCHLNGR3TB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model            = UKCHNGR3
      Turret           = TURRET01
      WeaponFireFXBone = PRIMARY MUZZLE01
      WeaponLaunchBone = PRIMARY MUZZLE01
    End
    ConditionState = REALLYDAMAGED
      Model            = UKCHNGR3
      Turret           = TURRET01
      WeaponFireFXBone = PRIMARY MUZZLE01
      WeaponLaunchBone = PRIMARY MUZZLE01
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = UKCHNGR3w
    End
    RightFrontTireBone     = TIRE01
    LeftFrontTireBone      = TIRE02
    MidRightFrontTireBone  = TIRE03
    MidLeftFrontTireBone   = TIRE04
    MidRightMidTireBone    = TIRE05
    MidLeftMidTireBone     = TIRE06
    MidRightRearTireBone   = TIRE07
    MidLeftRearTireBone    = TIRE08
    TireRotationMultiplier = 0.4
  End
  DisplayName   = UK_Challenger3
  Side          = Britain
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY BritainV25Challenger_Gun
  End
  BuildCost = 2000
  BuildTime = 29.4
  VisionRange = 220
  ShroudClearingRange = 455
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=90, pitch="No", slots="PRIMARY") + footer(575, 22, 13, 13, loco="CrusaderLocomotor")

FILES["BritainVehicleV25Rapier.ini"] = """; V25 UK49KB23 / Command_ConstructUK49KB23
; Lazr_AmericaWarFactoryCommandSet slot 11. Model 49KB23. Brake/housecolor overlay omitted.
Object BritainVehicleV25Rapier
  SelectPortrait = 49KB23TB
  ButtonImage    = 49KB23TB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model            = 49KB23
      Turret           = TURRET01
      TurretPitch      = TURRETEL_E
      WeaponLaunchBone = PRIMARY MISSILE
      WeaponFireFXBone = PRIMARY MISSILE
    End
    ConditionState = REALLYDAMAGED
      Model            = 49KB23
      Turret           = TURRET01
      TurretPitch      = TURRETEL_E
      WeaponLaunchBone = PRIMARY MISSILE
      WeaponFireFXBone = PRIMARY MISSILE
    End
    TrackMarks = EXTnkTrack.tga
  End
  DisplayName   = UK_49KB23
  Side          = Britain
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = AntiAirVehicle
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY BritainV25Rapier_AA
  End
  BuildCost = 1000
  BuildTime = 25.0
  VisionRange = 300
  ShroudClearingRange = 175
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=140, pitch="Yes", slots="PRIMARY", pitchrate=30) + footer(350, 13, 9, 10, loco="CrusaderLocomotor")

FILES["BritainVehicleV25Stormer.ini"] = """; V25 Alvis Stormer. Lazr_Command_ConstructAmericaVehicleAvenger
; Object Lazr_AmericaTankAvenger / Model UKStormer + UKStormerw on CORE.
; Not SS2 BritainVehicleStormer.
Object BritainVehicleV25Stormer
  SelectPortrait = LSFXGTTB
  ButtonImage    = LSFXGTTB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model             = UKStormer
      Turret            = TURRET
      TurretPitch       = ZHOU
      AltTurret         = CANNTRT
      WeaponFireFXBone  = PRIMARY   MUZZLE01
      WeaponLaunchBone  = PRIMARY   MUZZLE01
      WeaponMuzzleFlash = SECONDARY CANN01
      WeaponFireFXBone  = SECONDARY CANN01
    End
    ConditionState = REALLYDAMAGED
      Model             = UKStormer
      Turret            = TURRET
      TurretPitch       = ZHOU
      AltTurret         = CANNTRT
      WeaponFireFXBone  = PRIMARY   MUZZLE01
      WeaponLaunchBone  = PRIMARY   MUZZLE01
      WeaponMuzzleFlash = SECONDARY CANN01
      WeaponFireFXBone  = SECONDARY CANN01
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = UKStormerw
    End
    RightFrontTireBone     = TIRE01
    LeftFrontTireBone      = TIRE02
    MidRightFrontTireBone  = TIRE03
    MidLeftFrontTireBone   = TIRE04
    MidRightMidTireBone    = TIRE05
    MidLeftMidTireBone     = TIRE06
    MidRightRearTireBone   = TIRE07
    MidLeftRearTireBone    = TIRE08
    TireRotationMultiplier = 0.4
  End
  DisplayName   = UK_Stormer
  Side          = Britain
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = AntiAirVehicle
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   BritainV25Stormer_AA
    PreferredAgainst  = PRIMARY   BALLISTIC_MISSILE AIRCRAFT
    Weapon            = SECONDARY BritainV25FV432S_MG
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_SCRIPT FROM_AI
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
  BuildCost = 850
  BuildTime = 13.0
  VisionRange = 150
  ShroudClearingRange = 300
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + alt(turn=140, pitch="Yes", pitchrate=30) + footer(310, 15, 10, 10, loco="CrusaderLocomotor")

FILES["BritainVehicleV25FV432S.ini"] = """; V25 UKFV432S / Command_ConstructUKFV432S
; Lazr_AmericaWarFactoryCommandSet slot 9. Hull FV432 + wheels FV432w on CORE.
; TIRE08 absent.
Object BritainVehicleV25FV432S
  SelectPortrait = UKFV432TB
  ButtonImage    = UKFV432TB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model             = FV432
      Turret            = MRTRT
      AltTurret         = TURRET01
      WeaponLaunchBone  = PRIMARY   MORT
      WeaponFireFXBone  = PRIMARY   MORT
      WeaponMuzzleFlash = SECONDARY MUZZLE01
      WeaponFireFXBone  = SECONDARY MUZZLE01
    End
    ConditionState = REALLYDAMAGED
      Model             = FV432
      Turret            = MRTRT
      AltTurret         = TURRET01
      WeaponLaunchBone  = PRIMARY   MORT
      WeaponFireFXBone  = PRIMARY   MORT
      WeaponMuzzleFlash = SECONDARY MUZZLE01
      WeaponFireFXBone  = SECONDARY MUZZLE01
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = FV432w
    End
    RightFrontTireBone     = TIRE01
    LeftFrontTireBone      = TIRE02
    MidRightFrontTireBone  = TIRE03
    MidLeftFrontTireBone   = TIRE04
    MidRightMidTireBone    = TIRE05
    MidLeftMidTireBone     = TIRE06
    MidRightRearTireBone   = TIRE07
    MidLeftRearTireBone    = TIRE07
    TireRotationMultiplier = 0.4
  End
  DisplayName   = UK_FV432S
  Side          = Britain
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   BritainV25FV432S_Mortar
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY   VEHICLE STRUCTURE
    Weapon            = SECONDARY BritainV25FV432S_MG
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = SECONDARY INFANTRY
  End
  BuildCost = 1250
  BuildTime = 15.0
  VisionRange = 150
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + alt(turn=0, pitch="No") + footer(320, 23, 13, 12, loco="CrusaderLocomotor")


def main() -> None:
    for name, text in FILES.items():
        if not text.endswith("\n"):
            text += "\n"
        (OUT / name).write_text(text, encoding="latin1")
        print("wrote", name)


if __name__ == "__main__":
    main()
