#!/usr/bin/env python3
"""Write Loose INI sources for the 9 V25 North Korea Command Center systems."""
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

FILES["NorthKoreaV25CC9_Weapons.ini"] = r"""; Unique SS2-safe weapons for V25 North Korea CC systems.

Weapon NorthKoreaV25Strela_AA
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
  ClipReloadTime         = 16000
  AutoReloadsClip        = Yes
  FireSound              = TankHunterWeapon
  FireFX                 = FX_BuggyMissileIgnition
  ProjectileDetonationFX = WeaponFX_RocketBuggyMissileDetonation
  AntiAirborneVehicle    = Yes
  AntiGround             = No
  ShowsAmmoPips          = Yes
End

Weapon NorthKoreaV25SAM_AA
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = PENALTY
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = NorthKoreaV25SAM_AA_Object
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

Weapon NorthKoreaV25SAM_ABM
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = CRUSH
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = NorthKoreaV25SAM_ABM_Object
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

Weapon NorthKoreaV25SAM_ABM_Fuze
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

Object NorthKoreaV25SAM_AA_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = Engine01 Spec_SAMRMFlare
      ParticleSysBone = Engine01 Spec_SAMRMTrail
    End
  End
  DisplayName   = Egypt_Sam6
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

Object NorthKoreaV25SAM_ABM_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = ENGINEFX LargeSAMMissileTrail2
      ParticleSysBone = ENGINEFX LargeSAMMissilesFlare2
    End
  End
  DisplayName   = Egypt_Sam6
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
    Weapon = NorthKoreaV25SAM_ABM_Fuze
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

Weapon NorthKoreaV25Shilka_Gun
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

Weapon NorthKoreaV25Shilka_AA
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

Weapon NorthKoreaV25VTT_Mortar
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

Weapon NorthKoreaV25VTT_MG
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

Weapon NorthKoreaV25KN25_Tac
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
  ClipSize                = 6
  ClipReloadTime          = 18000
  AutoReloadsClip         = Yes
  AntiGround              = Yes
  ShowsAmmoPips           = Yes
End

Weapon NorthKoreaV25KN25_Cruise
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
  ClipSize                = 4
  ClipReloadTime          = 22000
  AutoReloadsClip         = Yes
  AntiGround              = Yes
  ShowsAmmoPips           = Yes
End

Weapon NorthKoreaV25KN400_AA
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = PENALTY
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = NorthKoreaV25SAM_AA_Object
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

Weapon NorthKoreaV25KN400_ABM
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = CRUSH
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = NorthKoreaV25SAM_ABM_Object
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

Weapon NorthKoreaV25M1973_MG
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

Weapon NorthKoreaV25M1973_AA
  PrimaryDamage          = 195.0
  PrimaryDamageRadius    = 35.0
  AttackRange            = 300.0
  MinimumAttackRange     = 5.0
  DamageType             = EXPLOSION
  DeathType              = EXPLODED
  WeaponSpeed            = 800
  ProjectileObject       = PatriotMissile
  ProjectileExhaust      = PatriotMissileTrail
  RadiusDamageAffects    = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots      = 2500
  ClipSize               = 4
  ClipReloadTime         = 16000
  AutoReloadsClip        = Yes
  FireSound              = TankHunterWeapon
  FireFX                 = FX_BuggyMissileIgnition
  ProjectileDetonationFX = WeaponFX_RocketBuggyMissileDetonation
  AntiAirborneVehicle    = Yes
  AntiGround             = No
  ShowsAmmoPips          = Yes
End

Weapon NorthKoreaV25M1973_ATGM
  PrimaryDamage          = 80.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 175.0
  DamageType             = ARMOR_PIERCING
  DeathType              = EXPLODED
  WeaponSpeed            = 400
  ProjectileObject       = GenericTankShell
  FireFX                 = FX_BuggyMissileIgnition
  ProjectileDetonationFX = WeaponFX_GenericTankShellDetonation
  FireSound              = TankHunterWeapon
  RadiusDamageAffects    = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots      = 2500
  ClipSize               = 0
  ClipReloadTime         = 0
End

Weapon NorthKoreaV25BM24_Rocket
  PrimaryDamage           = 280.0
  PrimaryDamageRadius     = 30.0
  ScatterRadiusVsInfantry = 12
  AttackRange             = 500
  MinimumAttackRange      = 40.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 350
  ProjectileObject        = 155mm_Shell
  FireFX                  = FX_BuggyMissileIgnition
  FireSound               = InfernoCannonWeapon
  ProjectileDetonationFX  = FX_UnguidedRocketExplosion
  RadiusDamageAffects     = ENEMIES NEUTRALS
  DelayBetweenShots       = 800
  ClipSize                = 12
  ClipReloadTime          = 20000
  AutoReloadsClip         = Yes
  AntiGround              = Yes
  ShowsAmmoPips           = Yes
End
"""

FILES["NorthKoreaVehicleV25Strela10.ini"] = """; V25 NkoreaStrella10 / Command_ConstructNkoreaStrella10
; NKWarFactoryCommandSet slot 13. Hull RUMTLB + wheels RUMTLBw on CORE.
Object NorthKoreaVehicleV25Strela10
  SelectPortrait = RUMTLBTB2
  ButtonImage    = RUMTLBTB2
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model            = RUMTLB
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponFireFXBone = PRIMARY MUZZLE
      WeaponLaunchBone = PRIMARY MUZZLE
    End
    ConditionState = REALLYDAMAGED
      Model            = RUMTLB
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponFireFXBone = PRIMARY MUZZLE
      WeaponLaunchBone = PRIMARY MUZZLE
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = RUMTLBw
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
  DisplayName   = NorthKorea_Strella10
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = AntiAirVehicle
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions       = None
    Weapon           = PRIMARY NorthKoreaV25Strela_AA
    PreferredAgainst = PRIMARY AIRCRAFT
  End
  BuildCost = 1000
  BuildTime = 14.0
  VisionRange = 170
  ShroudClearingRange = 300
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=140, pitch="Yes", slots="PRIMARY", pitchrate=30) + footer(380, 15, 10, 10, loco="CrusaderLocomotor")

FILES["NorthKoreaVehicleV251S91.ini"] = """; V25 Infa_ChinaVehicleListeningOutpost / Infa_Command_ConstructChinaVehicleListeningOutpost
; NK 1S91. Hull 2K12RD + wheels 2K12RDw on CORE. DisplayName Iran_An1S91.
Object NorthKoreaVehicleV251S91
  SelectPortrait = 2K12RDTB
  ButtonImage    = 2K12RDTB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model         = 2K12RD
      Animation     = 2K12RD.2K12RD
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model         = 2K12RD
      Animation     = 2K12RD.2K12RD
      AnimationMode = LOOP
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = 2K12RDw
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
  DisplayName   = Iran_An1S91
  Side          = NorthKorea
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
  BuildCost = 1000
  BuildTime = 15.0
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
""" + idle("No") + footer(350, 22, 9, 13, loco="CrusaderLocomotor")

FILES["NorthKoreaVehicleV25SAM6.ini"] = """; V25 NKoreaSA6 / Infa_Command_ConstructNKTSA6
; Infa_ChinaWarFactoryCommandSet SAM-6. Hull IR2K12 + wheels IR2K12w. Cameo NK2K12TB.
Object NorthKoreaVehicleV25SAM6
  SelectPortrait = NK2K12TB
  ButtonImage    = NK2K12TB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = IR2K12
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponLaunchBone = PRIMARY   MISSILE
      WeaponFireFXBone = PRIMARY   MISSILE
      WeaponLaunchBone = SECONDARY MISSILE
      WeaponFireFXBone = SECONDARY MISSILE
    End
    ConditionState = REALLYDAMAGED
      Model            = IR2K12
      Turret           = TURRET
      TurretPitch      = TURRETEL
      WeaponLaunchBone = PRIMARY   MISSILE
      WeaponFireFXBone = PRIMARY   MISSILE
      WeaponLaunchBone = SECONDARY MISSILE
      WeaponFireFXBone = SECONDARY MISSILE
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = IR2K12w
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
  DisplayName   = Egypt_Sam6
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = AntiAirVehicle
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   NorthKoreaV25SAM_AA
    Weapon            = SECONDARY NorthKoreaV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 1200
  BuildTime = 34.0
  VisionRange = 300
  ShroudClearingRange = 300
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=70, pitch="Yes", slots="PRIMARY SECONDARY", pitchrate=70) + footer(300, 15, 10, 10, loco="CrusaderLocomotor")

FILES["NorthKoreaVehicleV25Shilka.ini"] = """; V25 Infa_ChinaTankGattling / Infa_Command_ConstructChinaTankGattling
; NK Shilka. Hull NKZSU23 + wheels NKZSU23w on CORE.
Object NorthKoreaVehicleV25Shilka
  SelectPortrait = Shilka
  ButtonImage    = Shilka
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model            = NKZSU23
      Animation        = NKZSU23.NKZSU23
      AnimationMode    = LOOP
      Turret           = TURRET01
      TurretPitch      = TURRETEL01
      WeaponFireFXBone = PRIMARY   MUZZLE
      WeaponLaunchBone = PRIMARY   MUZZLE
      WeaponFireFXBone = SECONDARY MUZZLE
      WeaponLaunchBone = SECONDARY MUZZLE
    End
    ConditionState = REALLYDAMAGED
      Model            = NKZSU23
      Animation        = NKZSU23.NKZSU23
      AnimationMode    = LOOP
      Turret           = TURRET01
      TurretPitch      = TURRETEL01
      WeaponFireFXBone = PRIMARY   MUZZLE
      WeaponLaunchBone = PRIMARY   MUZZLE
      WeaponFireFXBone = SECONDARY MUZZLE
      WeaponLaunchBone = SECONDARY MUZZLE
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = NKZSU23w
    End
    RightFrontTireBone     = TIRE01
    LeftFrontTireBone      = TIRE02
    MidRightFrontTireBone  = TIRE03
    MidLeftFrontTireBone   = TIRE04
    MidRightMidTireBone    = TIRE05
    MidLeftMidTireBone     = TIRE06
    MidLeftRearTireBone    = TIRE07
    MidRightRearTireBone   = TIRE08
    TireRotationMultiplier = 0.4
  End
  DisplayName   = Iran_Shilka
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = AntiAirVehicle
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   NorthKoreaV25Shilka_Gun
    Weapon            = SECONDARY NorthKoreaV25Shilka_AA
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   INFANTRY VEHICLE STRUCTURE
    PreferredAgainst  = SECONDARY AIRCRAFT BALLISTIC_MISSILE
  End
  BuildCost = 1000
  BuildTime = 9.0
  VisionRange = 170
  ShroudClearingRange = 300
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=160, pitch="Yes", slots="PRIMARY SECONDARY", pitchrate=160) + footer(300, 15, 10, 15, loco="CrusaderLocomotor")

FILES["NorthKoreaVehicleV25VTT323.ini"] = """; V25 NkoreaVTTMC / Command_ConstructNkoreaVTTMC
; DisplayName NorthKorea_VTT-323. Hull NKVTTMC + wheels NKVTTMCw. TIRE08 absent.
Object NorthKoreaVehicleV25VTT323
  SelectPortrait = VTTMCTB
  ButtonImage    = VTTMCTB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model             = NKVTTMC
      Turret            = MRTRT
      AltTurret         = TURRET01
      WeaponLaunchBone  = PRIMARY   MORT
      WeaponFireFXBone  = PRIMARY   MORT
      WeaponMuzzleFlash = SECONDARY MUZZLE01
      WeaponFireFXBone  = SECONDARY MUZZLE01
    End
    ConditionState = REALLYDAMAGED
      Model             = NKVTTMC
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
      Model = NKVTTMCw
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
  DisplayName   = NorthKorea_VTT-323
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   NorthKoreaV25VTT_Mortar
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY   VEHICLE STRUCTURE
    Weapon            = SECONDARY NorthKoreaV25VTT_MG
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = SECONDARY INFANTRY
  End
  BuildCost = 1100
  BuildTime = 15.0
  VisionRange = 150
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + alt(turn=40, pitch="No") + footer(320, 23, 13, 12, loco="CrusaderLocomotor")

FILES["NorthKoreaVehicleV25KN25.ini"] = """; V25 NorthKoreaKN25 / Command_ConstructNorthKoreaKN25
; NKWarFactoryIIICommandSet slot 10. Model NKKN25. WEAPONFX absent.
Object NorthKoreaVehicleV25KN25
  SelectPortrait = KN25TB
  ButtonImage    = KN25TB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = NKKN25
      Turret           = TURRET01
      TurretPitch      = TURRETEL02
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MISSILE_C
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MISSILE_C
    End
    TrackMarks             = EXTireTrack.tga
    Dust                   = ScudLauncherDust
    DirtSpray              = RocketBuggyDirtSpray
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL02
    LeftRearTireBone       = WHEEL07
    RightRearTireBone      = WHEEL08
    MidLeftFrontTireBone   = WHEEL03
    MidRightFrontTireBone  = WHEEL04
    MidLeftRearTireBone    = WHEEL05
    MidRightRearTireBone   = WHEEL06
    TireRotationMultiplier = 0.2
  End
  DisplayName   = NorthKorea_KN-25
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   NorthKoreaV25KN25_Tac
    Weapon            = SECONDARY NorthKoreaV25KN25_Cruise
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
  End
  BuildCost = 3000
  BuildTime = 35.0
  VisionRange = 300
  ShroudClearingRange = 180
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=20, pitch="Yes", slots="PRIMARY SECONDARY", pitchrate=20) + footer(370, 15, 10, 15)

FILES["NorthKoreaVehicleV25KN400.ini"] = """; V25 NorthKoreaKN400 / Command_ConstructNorthKoreaKN400
; Infa_ChinaWarFactoryCommandSet slot 11. Model NKKN400. Rider-deploy omitted.
Object NorthKoreaVehicleV25KN400
  SelectPortrait = KN400TB
  ButtonImage    = KN400TB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = NKKN400
      Animation        = NKKN400.NKKN400
      AnimationMode    = MANUAL
      Flags            = START_FRAME_LAST
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MISSILE_C
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MISSILE_C
    End
    ConditionState = REALLYDAMAGED
      Model            = NKKN400
      Animation        = NKKN400.NKKN400
      AnimationMode    = MANUAL
      Flags            = START_FRAME_LAST
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MISSILE_C
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MISSILE_C
    End
    TrackMarks               = EXTireTrack.tga
    Dust                     = RocketBuggyDust
    DirtSpray                = RocketBuggyDirtSpray
    CabRotationMultiplier    = 1.5
    TrailerRotationMultiplier = 0.2
    CabBone                  = CAB
    TrailerBone              = TRAILER
    RotationDamping          = 0.7
    RightFrontTireBone       = WHEEL01
    LeftFrontTireBone        = WHEEL02
    MidRightFrontTireBone    = WHEEL03
    MidLeftFrontTireBone     = WHEEL04
    MidRightMidTireBone      = WHEEL09
    MidLeftMidTireBone       = WHEEL10
    MidRightRearTireBone     = WHEEL05
    MidLeftRearTireBone      = WHEEL06
    LeftRearTireBone         = WHEEL07
    RightRearTireBone        = WHEEL08
    TireRotationMultiplier   = 0.2
  End
  DisplayName   = NorthKorea_KN-400
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   NorthKoreaV25KN400_AA
    Weapon            = SECONDARY NorthKoreaV25KN400_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 2800
  BuildTime = 48.0
  VisionRange = 1200
  ShroudClearingRange = 175
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + idle() + footer(240, 25, 9, 15)

FILES["NorthKoreaVehicleV25M1973.ini"] = """; V25 Infa_ChinaTankECM / Infa_Command_ConstructChinaTankECM
; DisplayName OBJECT:M1973. Hull SDM1973 + wheels SDM1973w. BARLF01/M2_MG absent.
Object NorthKoreaVehicleV25M1973
  SelectPortrait = M1973
  ButtonImage    = M1973
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    ProjectileBoneFeedbackEnabledSlots = TERTIARY
    DefaultConditionState
      Model            = SDM1973
      Turret           = TURRET01
      WeaponFireFXBone = PRIMARY   AA
      WeaponLaunchBone = PRIMARY   AA
      WeaponFireFXBone = SECONDARY MISSILE
      WeaponLaunchBone = SECONDARY MISSILE
      WeaponLaunchBone = TERTIARY  SAGR
    End
    ConditionState = REALLYDAMAGED
      Model            = SDM1973
      Turret           = TURRET01
      WeaponFireFXBone = PRIMARY   AA
      WeaponLaunchBone = PRIMARY   AA
      WeaponFireFXBone = SECONDARY MISSILE
      WeaponLaunchBone = SECONDARY MISSILE
      WeaponLaunchBone = TERTIARY  SAGR
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = SDM1973w
    End
    LeftFrontTireBone      = WHEEL01
    MidLeftFrontTireBone   = WHEEL02
    MidLeftRearTireBone    = WHEEL03
    LeftRearTireBone       = WHEEL04
    MidRightFrontTireBone  = WHEEL05
    RightFrontTireBone     = WHEEL06
    MidRightRearTireBone   = WHEEL07
    RightRearTireBone      = WHEEL07
    TireRotationMultiplier = 0.4
  End
  DisplayName   = OBJECT:M1973
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   NorthKoreaV25M1973_MG
    Weapon            = SECONDARY NorthKoreaV25M1973_AA
    Weapon            = TERTIARY  NorthKoreaV25M1973_ATGM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_SCRIPT FROM_AI
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    AutoChooseSources = TERTIARY  FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY   INFANTRY
    PreferredAgainst  = SECONDARY AIRCRAFT
    PreferredAgainst  = TERTIARY  VEHICLE STRUCTURE
  End
  BuildCost = 1100
  BuildTime = 14.0
  VisionRange = 170
  ShroudClearingRange = 300
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=100, pitch="No", slots="PRIMARY SECONDARY TERTIARY") + footer(340, 15, 10, 10, loco="CrusaderLocomotor")

FILES["NorthKoreaVehicleV25BM24.ini"] = """; V25 NkoreaBM24 / Command_ConstructNkoreaBM24
; NKWarFactoryIIICommandSet slot 13. Model NKBM24.
Object NorthKoreaVehicleV25BM24
  SelectPortrait = NKBM24TB
  ButtonImage    = NKBM24TB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    ProjectileBoneFeedbackEnabledSlots = PRIMARY
    DefaultConditionState
      Model            = NKBM24
      Turret           = TURRET01
      TurretPitch      = TURRETEL01
      WeaponLaunchBone = PRIMARY MISSILE
      WeaponFireFXBone = PRIMARY MISSILE
    End
    ConditionState = REALLYDAMAGED
      Model            = NKBM24
      Turret           = TURRET01
      TurretPitch      = TURRETEL01
      WeaponLaunchBone = PRIMARY MISSILE
      WeaponFireFXBone = PRIMARY MISSILE
    End
    TrackMarks             = EXTireTrack.tga
    Dust                   = RocketBuggyDust
    DirtSpray              = RocketBuggyDirtSpray
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL04
    MidLeftRearTireBone    = WHEEL02
    MidRightRearTireBone   = WHEEL05
    LeftRearTireBone       = WHEEL03
    RightRearTireBone      = WHEEL06
    TireRotationMultiplier = 0.2
  End
  DisplayName   = NorthKorea_BM-24
  Side          = NorthKorea
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY NorthKoreaV25BM24_Rocket
  End
  BuildCost = 1500
  BuildTime = 25.0
  VisionRange = 180
  ShroudClearingRange = 300
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=60, pitch="Yes", slots="PRIMARY", pitchrate=40) + footer(200, 15, 10, 12)


def main() -> None:
    for name, text in FILES.items():
        if not text.endswith("\n"):
            text += "\n"
        (OUT / name).write_text(text, encoding="latin1")
        print("wrote", name)


if __name__ == "__main__":
    main()
