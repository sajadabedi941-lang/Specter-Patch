#!/usr/bin/env python3
"""Write Loose INI sources for the 6 V25 Iran Command Center systems."""
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
    return FOOTER.format(hp=hp, gx=gx, gy=gy, gz=gz, gsmall=gsmall, loco=loco)


def turret(turn=180, pitch="No", slots="PRIMARY SECONDARY", pitchrate=None):
    pr = f"      TurretPitchRate       = {pitchrate}\n" if pitchrate else ""
    return AI_TURRET.format(turn=turn, pitch=pitch, slots=slots, pitchrate=pr)


FILES = {}

FILES["IranV25CC6_Weapons.ini"] = r"""; Unique SS2-safe weapons for V25 Iran CC systems.

Weapon IranV25SAM_AA
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
  ProjectileObject           = IranV25SAM_AA_Object
  FireOCL                    = OCL_48N6TargetLock
  RadiusDamageAffects        = ENEMIES NEUTRALS
  DelayBetweenShots          = 800
  ClipSize                   = 4
  ClipReloadTime             = 8500
  AutoReloadsClip            = Yes
  AntiAirborneVehicle        = Yes
  AntiGround                 = No
  AntiBallisticMissile       = No
  ProjectileDetonationFX     = FX_HeavyAAMImpact
  FireSound                  = Thaad_fire
  AcceptableAimDelta         = 360
End

Weapon IranV25SAM_ABM
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
  ProjectileObject           = IranV25SAM_ABM_Object
  FireOCL                    = OCL_40N6STargetLock
  RadiusDamageAffects        = ENEMIES NEUTRALS
  DelayBetweenShots          = 800
  ClipSize                   = 4
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

Weapon IranV25SAM_ABM_Fuze
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

Object IranV25SAM_AA_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = Engine01 Spec_SAMRMFlare
      ParticleSysBone = Engine01 Spec_SAMRMTrail
    End
  End
  DisplayName   = Iran_Sayyad
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

Object IranV25SAM_ABM_Object
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model           = PAC-3
      ParticleSysBone = ENGINEFX LargeSAMMissileTrail2
      ParticleSysBone = ENGINEFX LargeSAMMissilesFlare2
    End
  End
  DisplayName   = Iran_Sayyad
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
    Weapon = IranV25SAM_ABM_Fuze
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

Weapon IranV25Cruise
  PrimaryDamage               = 150.0
  PrimaryDamageRadius         = 10.0
  SecondaryDamage             = 50.0
  SecondaryDamageRadius       = 20.0
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
"""

FILES["IranVehicleV25Sayyad2.ini"] = """; V25 IranSayyad / Command_ConstructIranSayyad
; IranWarFactoryIICommandSet slot 6. Model Sayyad. TURRETEL absent; no TurretPitch.
Object IranVehicleV25Sayyad2
  SelectPortrait = SayyadTB
  ButtonImage    = SayyadTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = Sayyad
      Turret           = TURRET01
      WeaponLaunchBone = PRIMARY   WeaponA
      WeaponFireFXBone = PRIMARY   WeaponA
      WeaponLaunchBone = SECONDARY WeaponA
      WeaponFireFXBone = SECONDARY WeaponA
    End
    ConditionState = REALLYDAMAGED
      Model            = Sayyad
      Turret           = TURRET01
      WeaponLaunchBone = PRIMARY   WeaponA
      WeaponFireFXBone = PRIMARY   WeaponA
      WeaponLaunchBone = SECONDARY WeaponA
      WeaponFireFXBone = SECONDARY WeaponA
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL08
    MidRightFrontTireBone  = WHEEL07
    MidLeftFrontTireBone   = WHEEL02
    LeftRearTireBone       = WHEEL05
    RightRearTireBone      = WHEEL04
    TireRotationMultiplier = 0.2
  End
  DisplayName = Iran_Sayyad
  Side        = Iran
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   IranV25SAM_AA
    Weapon            = SECONDARY IranV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 1700
  BuildTime = 48.0
  VisionRange = 800
  ShroudClearingRange = 175
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=180, slots="PRIMARY SECONDARY") + footer(240, 22, 9, 12)

FILES["IranVehicleV251S91.ini"] = """; V25 IranAn1S91 / Command_ConstructIranAn1S91
; IranWarFactoryIICommandSet slot 7. Hull 2K12RD + wheels 2K12RDw on CORE.
Object IranVehicleV251S91
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
  DisplayName = Iran_An1S91
  Side        = Iran
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
""" + RADAR_BEH.format(rng=1800) + footer(350, 22, 9, 13, "No", "CrusaderLocomotor")

FILES["IranVehicleV25SAM6.ini"] = """; V25 IranSAM6 / Command_ConstructIranSAM6
; IranWarFactoryIICommandSet slot 8. Model IR2K12 + wheels IR2K12w. Not IranShilka.
Object IranVehicleV25SAM6
  SelectPortrait = IR2K12TB
  ButtonImage    = IR2K12TB
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
  DisplayName = Egypt_Sam6
  Side        = Iran
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TankArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   IranV25SAM_AA
    Weapon            = SECONDARY IranV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 1600
  BuildTime = 20.0
  VisionRange = 400
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=80, pitch="Yes", pitchrate=80, slots="PRIMARY SECONDARY") + footer(280, 18, 9, 12, "Yes", "CrusaderLocomotor")

FILES["IranVehicleV25Raad.ini"] = """; V25 IranBukM labeled Iran_BUKM / Command_ConstructIranBukM
; GLAArmsDealerCommandSet slot 6 (Iran war-factory path). Model IRBUKM.
; V25 has no object named Raad; this is the Iran Buk-M TEL, not SS2 IranRaadM2EK.
Object IranVehicleV25Raad
  SelectPortrait = IRBUKMTB
  ButtonImage    = IRBUKMTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY
    DefaultConditionState
      Model            = IRBUKM
      Turret           = TURRET01
      TurretPitch      = TURRETEL01
      WeaponLaunchBone = PRIMARY   MISSILE
      WeaponFireFXBone = PRIMARY   MISSILE
      WeaponLaunchBone = SECONDARY MISSILE
      WeaponFireFXBone = SECONDARY MISSILE
    End
    ConditionState = REALLYDAMAGED
      Model            = IRBUKM
      Turret           = TURRET01
      TurretPitch      = TURRETEL01
      WeaponLaunchBone = PRIMARY   MISSILE
      WeaponFireFXBone = PRIMARY   MISSILE
      WeaponLaunchBone = SECONDARY MISSILE
      WeaponFireFXBone = SECONDARY MISSILE
    End
    TrackMarks             = EXTireTrack.tga
    RightFrontTireBone     = TIRE02
    LeftFrontTireBone      = TIRE01
    MidRightFrontTireBone  = TIRE04
    MidLeftFrontTireBone   = TIRE03
    RightRearTireBone      = TIRE06
    LeftRearTireBone       = TIRE05
    TireRotationMultiplier = 0.2
  End
  DisplayName = Iran_BUKM
  Side        = Iran
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY   IranV25SAM_AA
    Weapon            = SECONDARY IranV25SAM_ABM
    AutoChooseSources = PRIMARY   FROM_PLAYER FROM_AI FROM_SCRIPT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst  = PRIMARY   AIRCRAFT
    PreferredAgainst  = SECONDARY BALLISTIC_MISSILE
  End
  BuildCost = 1800
  BuildTime = 35.0
  VisionRange = 400
  ShroudClearingRange = 175
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK ATTACK_NEEDS_LINE_OF_SIGHT CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + turret(turn=80, pitch="Yes", pitchrate=80, slots="PRIMARY SECONDARY") + footer(240, 18, 9, 12)

FILES["IranVehicleV25Kolchuga.ini"] = """; V25 GLAVehicleRadarVan labeled Iran_Kolchuga
; IranWarFactoryIIICommandSet slot 7. Model Kolchuga. Unique vs SS2 GLAVehicleRadarVan.
Object IranVehicleV25Kolchuga
  SelectPortrait = KolchugaTB
  ButtonImage    = KolchugaTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    DefaultConditionState
      Model         = Kolchuga
      Animation     = Kolchuga.Kolchuga
      AnimationMode = LOOP
    End
    ConditionState = REALLYDAMAGED
      Model         = Kolchuga
      Animation     = Kolchuga.Kolchuga
      AnimationMode = LOOP
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL04
    LeftRearTireBone       = WHEEL03
    RightRearTireBone      = WHEEL06
    MidLeftRearTireBone    = WHEEL02
    MidRightRearTireBone   = WHEEL05
    TireRotationMultiplier = 0.2
  End
  DisplayName = Iran_Kolchuga
  Side        = Iran
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = TruckArmor
    DamageFX   = TankDamageFX
  End
  WeaponSet
    Conditions = None
    Weapon     = PRIMARY NONE
  End
  BuildCost = 1500
  BuildTime = 10.0
  VisionRange = 1800
  ShroudClearingRange = 800
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE REVEALS_ENEMY_PATHS CANNOT_RETALIATE
""" + RADAR_BEH.format(rng=1800) + footer(350, 22, 9, 13, "No")

FILES["IranVehicleV25Noor.ini"] = """; V25 IranNoor / Command_ConstructIranNoor
; IranWarFactoryIIICommandSet slot 9. Model SDNoor. No turret bone; skip riders.
Object IranVehicleV25Noor
  SelectPortrait = NoorTB
  ButtonImage    = NoorTB
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = No
    ProjectileBoneFeedbackEnabledSlots = PRIMARY
    DefaultConditionState
      Model            = SDNoor
      Animation        = SDNoor.SDNoor
      AnimationMode    = ONCE
      WeaponLaunchBone = PRIMARY WEAPONA
      WeaponFireFXBone = PRIMARY WEAPONA
    End
    ConditionState = REALLYDAMAGED
      Model            = SDNoor
      WeaponLaunchBone = PRIMARY WEAPONA
      WeaponFireFXBone = PRIMARY WEAPONA
    End
    TrackMarks             = EXTireTrack.tga
    LeftFrontTireBone      = WHEEL01
    RightFrontTireBone     = WHEEL08
    MidRightFrontTireBone  = WHEEL07
    MidLeftFrontTireBone   = WHEEL02
    LeftRearTireBone       = WHEEL05
    RightRearTireBone      = WHEEL04
    TireRotationMultiplier = 0.2
  End
  DisplayName = Iran_Noor
  Side        = Iran
  EditorSorting = VEHICLE
  ArmorSet
    Conditions = None
    Armor      = HumveeArmor
    DamageFX   = TruckDamageFX
  End
  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY IranV25Cruise
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    PreferredAgainst  = PRIMARY VEHICLE STRUCTURE
  End
  BuildCost = 4000
  BuildTime = 20.0
  VisionRange = 400
  ShroudClearingRange = 200
  Prerequisites
  End
  CommandSet = GLAVehicleRocketBuggyCommandSet
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
""" + AI_NOTURRET + footer(240, 25, 9, 12)


def main() -> None:
    for name, text in FILES.items():
        path = OUT / name
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text, encoding="latin1")
        print("wrote", path.name, path.stat().st_size)


if __name__ == "__main__":
    main()
