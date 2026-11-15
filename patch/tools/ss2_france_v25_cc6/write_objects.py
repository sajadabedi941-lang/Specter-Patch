#!/usr/bin/env python3
"""Write Loose INI sources for the 6 V25 France Command Center systems."""
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
  GeometryIsSmall     = {gsmall}
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
    AutoAcquireEnemiesWhenIdle = {acquire}
    MoodAttackCheckRate        = 150
  End
"""

AI_ALT = """
  Behavior = AIUpdateInterface ModuleTag_03
    Turret
      TurretTurnRate        = 0
      AllowsPitch           = No
      ControlledWeaponSlots = PRIMARY
    End
    AltTurret
      ControlledWeaponSlots = SECONDARY
      TurretTurnRate        = 100.0
      TurretPitchRate       = 160.0
      AllowsPitch           = Yes
      FiresWhileTurning     = Yes
      NaturalTurretPitch    = 35
    End
    AutoAcquireEnemiesWhenIdle = Yes Stealthed
    TurretsLinked              = No
    MoodAttackCheckRate        = 150
  End
"""


def footer(hp, gx, gy, gz, gsmall="Yes", loco="Generic8x8Locomotor"):
    return FOOTER.format(hp=hp, gx=gx, gy=gy, gz=gz, gsmall=gsmall, loco=loco)


def turret(turn=180, pitch="No", slots="PRIMARY", pitchrate=None):
    pr = f"      TurretPitchRate       = {pitchrate}\n" if pitchrate else ""
    return AI_TURRET.format(turn=turn, pitch=pitch, slots=slots, pitchrate=pr)


def idle(acquire="Yes Stealthed"):
    return AI_NOTURRET.format(acquire=acquire)


FILES = {}

FILES["FranceV25CC6_Weapons.ini"] = r"""; Unique SS2-safe weapons for V25 France CC systems.
; V25 projectiles FUCHOUZHEMissile / LSFziyuanMissile / KeshetMortarShell are not in SS2.

Weapon FranceV25Roland_AA
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
  ClipSize               = 2
  ClipReloadTime         = 19000
  AutoReloadsClip        = Yes
  FireSound              = TankHunterWeapon
  FireFX                 = FX_BuggyMissileIgnition
  ProjectileDetonationFX = WeaponFX_RocketBuggyMissileDetonation
  AntiAirborneInfantry   = No
  AntiAirborneVehicle    = Yes
  AntiBallisticMissile   = No
  AntiGround             = No
  ShowsAmmoPips          = Yes
End

Weapon FranceV25Crotale_AA
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
  ClipSize               = 4
  ClipReloadTime         = 19000
  AutoReloadsClip        = Yes
  FireSound              = TankHunterWeapon
  FireFX                 = FX_BuggyMissileIgnition
  ProjectileDetonationFX = WeaponFX_RocketBuggyMissileDetonation
  AntiAirborneInfantry   = No
  AntiAirborneVehicle    = Yes
  AntiBallisticMissile   = No
  AntiGround             = No
  ShowsAmmoPips          = Yes
End

Weapon FranceV25Aster_AA
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = PENALTY
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = FranceV25AsterMissile
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

Weapon FranceV25Aster_ABM
  PrimaryDamage          = 320.0
  PrimaryDamageRadius    = 5.0
  AttackRange            = 800
  MinimumAttackRange     = 133
  DamageType             = CRUSH
  DeathType              = EXPLODED
  WeaponSpeed            = 9999999999
  FireFX                 = FX_LargeSamMissilesTubeOut
  ProjectileObject       = FranceV25AsterABM
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

Weapon FranceV25Aster_ABM_Fuze
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

Object FranceV25AsterMissile
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = Engine01 Spec_SAMRMFlare
      ParticleSysBone = Engine01 Spec_SAMRMTrail
    End
  End
  DisplayName   = France_Aster-30
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

Object FranceV25AsterABM
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = ENGINEFX LargeSAMMissileTrail2
      ParticleSysBone = ENGINEFX LargeSAMMissilesFlare2
    End
  End
  DisplayName   = France_Aster-30
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
    Weapon = FranceV25Aster_ABM_Fuze
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

Weapon FranceV25Mephisto_ATGM
  PrimaryDamage          = 280
  PrimaryDamageRadius    = 10.0
  SecondaryDamage        = 50.0
  SecondaryDamageRadius  = 20.0
  AcceptableAimDelta     = 50
  ScatterRadiusVsInfantry = 35.0
  DamageType             = ARMOR_PIERCING
  DeathType              = EXPLODED
  WeaponSpeed            = 500
  AttackRange            = 300
  MinimumAttackRange     = 80
  ProjectileObject       = HumveeMissile
  ProjectileExhaust      = JetContrail
  FireSound              = HumveeWeaponTOW
  RadiusDamageAffects    = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots      = 2500
  ClipSize               = 4
  ClipReloadTime         = 20000
  ProjectileDetonationFX = WeaponFX_RocketBuggyMissileDetonation
  AutoReloadsClip        = Yes
  ProjectileCollidesWith = STRUCTURES
  AntiGround             = Yes
  AntiAirborneVehicle    = No
  AntiAirborneInfantry   = No
  ShowsAmmoPips          = Yes
End

Weapon FranceV25VPM81_Mortar
  PrimaryDamage          = 250.0
  PrimaryDamageRadius    = 25.0
  ScatterRadiusVsInfantry = 10
  AttackRange            = 450
  MinimumAttackRange     = 20.0
  MinTargetPitch         = -90
  MaxTargetPitch         = 79
  DamageType             = EXPLOSION
  DeathType              = EXPLODED
  WeaponSpeed            = 300
  MinWeaponSpeed         = 75
  ScaleWeaponSpeed       = Yes
  ProjectileObject       = 155mm_Shell
  FireFX                 = WeaponFX_GenericTankGunNoTracer
  FireSound              = InfernoCannonWeapon
  ProjectileDetonationFX = FX_UnguidedRocketExplosion
  RadiusDamageAffects    = ENEMIES NEUTRALS ALLIES
  DelayBetweenShots      = 3000
  ClipSize               = 0
  ClipReloadTime         = 0
  PreAttackDelay         = 200
  PreAttackType          = PER_SHOT
End

Weapon FranceV25VPM81_MG
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

FILES["FranceVehicleV25Roland.ini"] = """; V25 FranceRolland / Command_ConstructFranceRolland
; SupW_AmericaWarFactoryCommandSet slot 5. Hull SDGRRLD + wheels SDGRRLDw on CORE.
; V25 also drew CWCusHC_B housecolor; omitted (SS2 crash vector).
Object FranceVehicleV25Roland
  SelectPortrait = FRRLDTB
  ButtonImage    = FRRLDTB
  Draw = W3DTankDraw ModuleTag_01
    OkToChangeModelColor = No
    ExtraPublicBone = CORE
    DefaultConditionState
      Model             = SDGRRLD
      Animation         = SDGRRLD.SDGRRLD
      AnimationMode     = LOOP
      Turret            = TURRET
      TurretPitch       = TURRETEL
      WeaponFireFXBone  = PRIMARY BARRELMS
      WeaponMuzzleFlash = PRIMARY BARRELMS
      WeaponLaunchBone  = PRIMARY BARRELMS
    End
    ConditionState = REALLYDAMAGED
      Model             = SDGRRLD
      Animation         = SDGRRLD.SDGRRLD
      AnimationMode     = LOOP
      Turret            = TURRET
      TurretPitch       = TURRETEL
      WeaponFireFXBone  = PRIMARY BARRELMS
      WeaponMuzzleFlash = PRIMARY BARRELMS
      WeaponLaunchBone  = PRIMARY BARRELMS
    End
    TrackMarks = EXTnkTrack.tga
  End
  Draw = W3DTruckDraw ModuleTag_TracksDraw
    OkToChangeModelColor             = No
    ParticlesAttachedToAnimatedBones = Yes
    AttachToBoneInAnotherModule      = CORE
    DefaultConditionState
      Model = SDGRRLDw
    End
    LeftFrontTireBone      = WHEEL02
    MidLeftFrontTireBone   = WHEEL03
    MidLeftRearTireBone    = WHEEL04
    LeftRearTireBone       = WHEEL05
    MidRightFrontTireBone  = WHEEL06
    RightFrontTireBone     = WHEEL01
    RightRearTireBone      = WHEEL09
    TireRotationMultiplier = 0.4
  End
  DisplayName   = Germany_Rolland
  Side          = France
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = AntiAirVehicle
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions       = None
    Weapon           = PRIMARY FranceV25Roland_AA
    PreferredAgainst = PRIMARY AIRCRAFT
  End
  BuildCost = 1400
  BuildTime = 9.0
  VisionRange = 150
  ShroudClearingRange = 360
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=140, pitch="Yes", slots="PRIMARY", pitchrate=30) + footer(300, 15, 10, 15, loco="CrusaderLocomotor")

FILES["FranceVehicleV25Arabel.ini"] = """; V25 France Arabel Radar. WF button SupW_Command_ConstructAmericaVehicleSentryDrone
; (TextLabel France_Arabel) on SupW_AmericaWarFactoryCommandSet slot 7.
; Object name in V25 is SupW_AmericaVehicleSentryDrone; model is Arabel.W3D.
; Not AMX-10, not ItalyArabel/UkraineArabel substitutes.
Object FranceVehicleV25Arabel
  SelectPortrait = FranceV25ArabelTB
  ButtonImage    = FranceV25ArabelTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model         = Arabel
      Animation     = Arabel.Arabel
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model         = Arabel
      Animation     = Arabel.Arabel
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
  DisplayName   = France_Arabel
  Side          = France
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
""" + idle("No") + footer(350, 22, 9, 12)

FILES["FranceVehicleV25Aster30.ini"] = """; V25 FranceZiYuan / SupW_Command_ConstructZiYuan (TextLabel France_Aster-30)
; SupW_AmericaWarFactoryCommandSet slot 8. Model FRAster. Not ItalyAster30/UkraineAster30.
; V25 RiderChangeContain / CWCru deploy / FS_BASE_DEFENSE omitted (SS2-safe always-ready).
Object FranceVehicleV25Aster30
  SelectPortrait = FranceV25AsterTB
  ButtonImage    = FranceV25AsterTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = FRAster
      Animation        = FRAster.FRAster
      AnimationMode    = MANUAL
      Flags            = START_FRAME_LAST
      WeaponLaunchBone = PRIMARY   MISSILE_C
      WeaponFireFXBone = PRIMARY   MISSILE_C
      WeaponLaunchBone = SECONDARY MISSILE_C
      WeaponFireFXBone = SECONDARY MISSILE_C
    End
    ConditionState = REALLYDAMAGED
      Model            = FRAster
      Animation        = FRAster.FRAster
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
  DisplayName   = France_Aster-30
  Side          = France
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   FranceV25Aster_AA
    Weapon            = SECONDARY FranceV25Aster_ABM
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

FILES["FranceVehicleV25Crotale.ini"] = """; V25 Crotale. WF button SupW_Command_ConstructAmericaVehicleAvenger
; (TextLabel Croatal_AA) on SupW_AmericaWarFactoryCommandSet slot 6.
; Object name in V25 is SupW_AmericaTankAvenger; model is FRCrotal.
; Independent of SS2 FranceVehicleCortaleMK3.
Object FranceVehicleV25Crotale
  SelectPortrait = LSFFSATB
  ButtonImage    = LSFFSATB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model            = FRCrotal
      Turret           = TURRET
      TurretPitch      = TURTTQ
      WeaponFireFXBone = PRIMARY MUZZLEFX
      WeaponLaunchBone = PRIMARY MUZZLE
    End
    ConditionState = REALLYDAMAGED
      Model            = FRCrotal
      Turret           = TURRET
      TurretPitch      = TURTTQ
      WeaponFireFXBone = PRIMARY MUZZLEFX
      WeaponLaunchBone = PRIMARY MUZZLE
    End
    TrackMarks             = EXTireTrack.tga
    Dust                   = RocketBuggyDust
    DirtSpray              = RocketBuggyDirtSpray
    LeftFrontTireBone      = WHEEL02
    RightFrontTireBone     = WHEEL03
    LeftRearTireBone       = WHEEL01
    RightRearTireBone      = WHEEL04
    TireRotationMultiplier = 0.2
  End
  DisplayName   = Croatal_AA
  Side          = France
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY FranceV25Crotale_AA
  End
  BuildCost = 1050
  BuildTime = 12.0
  VisionRange = 200
  ShroudClearingRange = 500
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE CANNOT_RETALIATE
""" + turret(turn=140, pitch="Yes", slots="PRIMARY", pitchrate=30) + footer(200, 16, 6, 12.5)

FILES["FranceVehicleV25Mephisto.ini"] = """; V25 VAB Mephisto = FranceAMX10P / Command_ConstructFranceAMX10P
; TextLabel France_VAB-Hot, ButtonImage VABHOTTB, model VABHOT.
; SupW_AmericaWarFactoryCommandSet slot 4. Not FranceVAB / SDFRVab.
Object FranceVehicleV25Mephisto
  SelectPortrait = VABHOTTB
  ButtonImage    = VABHOTTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model            = VABHOT
      Turret           = BODY
      WeaponLaunchBone = PRIMARY MISSILE
      WeaponFireFXBone = PRIMARY MISSILE
    End
    ConditionState = REALLYDAMAGED
      Model            = VABHOT
      Turret           = BODY
      WeaponLaunchBone = PRIMARY MISSILE
      WeaponFireFXBone = PRIMARY MISSILE
    End
    TrackMarks             = EXTireTrack2.tga
    Dust                   = RocketBuggyDust
    DirtSpray              = RocketBuggyDirtSpray
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL08
    LeftRearTireBone       = WHEEL05
    RightRearTireBone      = WHEEL04
    TireRotationMultiplier = 0.2
  End
  DisplayName   = France_VAB-Hot
  Side          = France
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions       = None
    Weapon           = PRIMARY FranceV25Mephisto_ATGM
    PreferredAgainst = PRIMARY VEHICLE STRUCTURE
  End
  BuildCost = 1250
  BuildTime = 15.0
  VisionRange = 150
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=90, pitch="No", slots="PRIMARY") + footer(320, 23, 13, 12)

FILES["FranceVehicleV25VPM81.ini"] = """; V25 VAB VPM 81. WF button Command_ConstructFranceVPM81 on slot 12.
; Object name in V25 is SupW_AmericaTankCrusader; model is VPM81. Not Crusader tank.
Object FranceVehicleV25VPM81
  SelectPortrait = VPM81TB
  ButtonImage    = VPM81TB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model             = VPM81
      Turret            = MRTRT
      AltTurret         = TURRET01
      WeaponLaunchBone  = PRIMARY   MORT
      WeaponFireFXBone  = PRIMARY   MORT
      WeaponMuzzleFlash = SECONDARY MUZZLE01
      WeaponFireFXBone  = SECONDARY MUZZLE01
    End
    ConditionState = REALLYDAMAGED
      Model             = VPM81
      Turret            = MRTRT
      AltTurret         = TURRET01
      WeaponLaunchBone  = PRIMARY   MORT
      WeaponFireFXBone  = PRIMARY   MORT
      WeaponMuzzleFlash = SECONDARY MUZZLE01
      WeaponFireFXBone  = SECONDARY MUZZLE01
    End
    TrackMarks             = EXTireTrack2.tga
    Dust                   = RocketBuggyDust
    DirtSpray              = RocketBuggyDirtSpray
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL08
    MidLeftRearTireBone    = WHEEL03
    MidRightRearTireBone   = WHEEL06
    LeftRearTireBone       = WHEEL05
    RightRearTireBone      = WHEEL04
    TireRotationMultiplier = 0.2
  End
  DisplayName   = France_VPM81
  Side          = France
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   FranceV25VPM81_Mortar
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY   VEHICLE STRUCTURE
    Weapon            = SECONDARY FranceV25VPM81_MG
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
""" + AI_ALT + footer(320, 23, 13, 12)


def main() -> None:
    for name, text in FILES.items():
        if not text.endswith("\n"):
            text += "\n"
        (OUT / name).write_text(text, encoding="latin1")
        print("wrote", name)


if __name__ == "__main__":
    main()
