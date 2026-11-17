# Transfer plan: `ChinaCSSA1`

- Generated: 2026-11-11 13:05 Asia/Tehran
- Found in V25 VFS: **True**
- Source: `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/ChinaVehicle.ini`
- Readiness: **manual_rebuild**
- Dest INI (future apply only): `Data\INI\Object\SilentDeath\China\ChinaCSSA1.ini`
- Build buttons: ['Command_ConstructChinaCSSA1']
- CommandSets holding those buttons: ['ChinaSupplyCenterCommandSet']
- Action counts: `{'IMPORT_UNIQUE': 21, 'RECOVER_FROM_V25': 7, 'RENAME_AND_REWRITE': 2, 'REUSE_NATIVE': 29, 'CYCLE': 13, 'MANUAL_REBUILD': 4}`
- Game writes: **False**

## Object meta

- Side: China
- SPECTER side map: China
- Bucket: vehicle
- KindOf: `['ATTACK_NEEDS_LINE_OF_SIGHT', 'CAN_ATTACK', 'CAN_CAST_REFLECTIONS', 'PRELOAD', 'SCORE', 'SELECTABLE', 'VEHICLE']`

## Compatibility notes (reasoned from INI flags, not guessed)

- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType GATTLING already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType GATTLING already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `stealth_detector_filter`: StealthDetector ExtraRequiredKindOf uses stock KindOf tokens already on SPECTER aircraft.
- **KEEP_V25_FLAGS** `antiair_flags_present`: Weapon already sets AntiAirborneVehicle and/or anti-missile flags. SPECTER aircraft/missiles keep their KindOf; no SPECTER rewrite.
- **KEEP_V25_FLAGS** `antiground_flags_present`: Weapon already sets AntiGround=Yes. SPECTER ground Armor is not rewritten.

## Dependency actions

| Kind | Name | Action | Planned | Reason | Source |
|---|---|---|---|---|---|
| Object | `ChinaCSSA1` | IMPORT_UNIQUE | `ChinaCSSA1` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/ChinaVehicle...` |
| MappedImage | `CSSA1TB` | RECOVER_FROM_V25 | `CSSA1TB` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/CSSA1TB.tga` |
| Weapon | `SA22G` | IMPORT_UNIQUE | `SA22G` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Weapon.ini` |
| AudioEvent | `LSF2C6MG` | IMPORT_UNIQUE | `LSF2C6MG` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/SoundEffects.ini` |
| FXList | `WeaponFX_CWCgenHeavyMachineCannon` | IMPORT_UNIQUE | `WeaponFX_CWCgenHeavyMachineCannon` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `WeaponFX_CWCgenGattlingCannonDetonation` | IMPORT_UNIQUE | `WeaponFX_CWCgenGattlingCannonDetonation` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| Object | `CWCgenExplosiveShell` | IMPORT_UNIQUE | `CWCgenExplosiveShell` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/WeaponObject...` |
| Armor | `ProjectileArmor` | RENAME_AND_REWRITE | `SD25_ProjectileArmor` | Same name, different effective behavior. SPECTER original stays; V25 copy becomes SD25_ProjectileArmor with a full reference rewrite. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Armor.ini` |
| FXList | `FX_NukeGLA` | REUSE_NATIVE | `FX_NukeGLA` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_GenericMissileDisintegrate` | REUSE_NATIVE | `FX_GenericMissileDisintegrate` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_GenericMissileDeath` | REUSE_NATIVE | `FX_GenericMissileDeath` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| ObjectCreationList | `OCL_GenericMissileDisintegrate` | REUSE_NATIVE | `OCL_GenericMissileDisintegrate` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ObjectCreationList.ini` |
| ArtFile | `CWCgenExpTracer` | IMPORT_UNIQUE | `CWCgenExpTracer` | Art stem present in parsed V25 BIGs. | `` |
| BehaviorModule | `HeightDieUpdate` | REUSE_NATIVE | `HeightDieUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `InstantDeathBehavior` | REUSE_NATIVE | `InstantDeathBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `PhysicsBehavior` | REUSE_NATIVE | `PhysicsBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `DumbProjectileBehavior` | REUSE_NATIVE | `DumbProjectileBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| DamageType | `GATTLING` | REUSE_NATIVE | `GATTLING` | DamageType exists on SPECTER Armor tables. | `` |
| Weapon | `SA22AIR` | IMPORT_UNIQUE | `SA22AIR` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Weapon.ini` |
| AudioEvent | `LSF2C6MG` | CYCLE | `LSF2C6MG` | Cyclic reference; node already visited. | `` |
| FXList | `WeaponFX_CWCgenHeavyMachineCannon` | CYCLE | `WeaponFX_CWCgenHeavyMachineCannon` | Cyclic reference; node already visited. | `` |
| Object | `CWCgenExplosiveShellAir` | IMPORT_UNIQUE | `CWCgenExplosiveShellAir` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/WeaponObject...` |
| ArtFile | `CWCgenExpTracer` | CYCLE | `CWCgenExpTracer` | Cyclic reference; node already visited. | `` |
| ArtFile | `CWCgenExpTracer.CWCgenExpTracer` | IMPORT_UNIQUE | `CWCgenExpTracer.CWCgenExpTracer` | Art stem present in parsed V25 BIGs. | `` |
| BehaviorModule | `PhysicsBehavior` | CYCLE | `PhysicsBehavior` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `DumbProjectileBehavior` | CYCLE | `DumbProjectileBehavior` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `InstantDeathBehavior` | CYCLE | `InstantDeathBehavior` | Cyclic reference; node already visited. | `` |
| DamageType | `GATTLING` | CYCLE | `GATTLING` | Cyclic reference; node already visited. | `` |
| Armor | `TankArmor` | RENAME_AND_REWRITE | `SD25_TankArmor` | Same name, different effective behavior. SPECTER original stays; V25 copy becomes SD25_TankArmor with a full reference rewrite. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Armor.ini` |
| FXList | `TankDamageFX` | MANUAL_REBUILD | `TankDamageFX` | Not in parsed V25 VFS, not in SPECTER, and no filename in the V25 zip listing. | `` |
| FXList | `FX_CarCrush` | REUSE_NATIVE | `FX_CarCrush` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_BattleMasterExplosionOneFinal` | REUSE_NATIVE | `FX_BattleMasterExplosionOneFinal` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_BattleMasterDamageTransition` | REUSE_NATIVE | `FX_BattleMasterDamageTransition` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| CommandSet | `ChinaVehicleBattleMasterCommandSet` | REUSE_NATIVE | `ChinaVehicleBattleMasterCommandSet` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandSet.ini` |
| CommandButton | `Command_AttackMove` | REUSE_NATIVE | `Command_AttackMove` | Pinned public command; V25 variant is not copied over SPECTER. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| MappedImage | `SSAttackMove2` | IMPORT_UNIQUE | `SSAttackMove2` | Name is free in SPECTER FINAL; unique-path import. | `INIZH.big:Data\INI\MappedImages\TextureSize_512\SSUserInterface512.INI` |
| ArtFile | `SSUserInterface512_001.tga` | IMPORT_UNIQUE | `SSUserInterface512_001.tga` | Art stem present in parsed V25 BIGs. | `` |
| ArtFile | `SSAttackMove2` | MANUAL_REBUILD | `SSAttackMove2` | Art stem not in parsed VFS, SPECTER, or V25 zip listing. | `` |
| CommandButton | `Command_Guard` | REUSE_NATIVE | `Command_Guard` | Pinned public command; V25 variant is not copied over SPECTER. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| MappedImage | `SDGuard` | RECOVER_FROM_V25 | `SDGuard` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/SDGuard.tga` |
| ArtFile | `SDGuard` | RECOVER_FROM_V25 | `SDGuard` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/Textures/SDGuard.tga` |
| CommandButton | `Command_Stop` | REUSE_NATIVE | `Command_Stop` | Pinned public command; V25 variant is not copied over SPECTER. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| MappedImage | `SDStop` | RECOVER_FROM_V25 | `SDStop` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/SDStop.tga` |
| ArtFile | `SDStop` | RECOVER_FROM_V25 | `SDStop` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/Textures/SDStop.tga` |
| AudioEvent | `CWCruShilkaVoiceSelect` | IMPORT_UNIQUE | `CWCruShilkaVoiceSelect` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `CWCruShilkaVoiceMove` | IMPORT_UNIQUE | `CWCruShilkaVoiceMove` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `CWCruShilkaVoiceGuard` | IMPORT_UNIQUE | `CWCruShilkaVoiceGuard` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `CWCruShilkaVoiceAttack` | IMPORT_UNIQUE | `CWCruShilkaVoiceAttack` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `CWCruShilkaVoiceAttackAir` | IMPORT_UNIQUE | `CWCruShilkaVoiceAttackAir` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `CWCruShilkaVoiceCreate` | IMPORT_UNIQUE | `CWCruShilkaVoiceCreate` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| Locomotor | `ChunmaLocomotor` | IMPORT_UNIQUE | `ChunmaLocomotor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Locomotor.ini` |
| CrateTemplate | `SalvageCrateData` | MANUAL_REBUILD | `SalvageCrateData` | Not in parsed V25 VFS, not in SPECTER, and no filename in the V25 zip listing. | `` |
| ObjectCreationList | `OCL_ChinaTankBattleMasterDebris` | REUSE_NATIVE | `OCL_ChinaTankBattleMasterDebris` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ObjectCreationList.ini` |
| Object | `ChinaVehicleBattleMasterDeadHull` | IMPORT_UNIQUE | `ChinaVehicleBattleMasterDeadHull` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/Hulk.ini` |
| ParticleSystem | `SmokeSmallContinuous01` | REUSE_NATIVE | `SmokeSmallContinuous01` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| ArtFile | `NVBtmstr_D1` | MANUAL_REBUILD | `NVBtmstr_D1` | Art stem not in parsed VFS, SPECTER, or V25 zip listing. | `` |
| BehaviorModule | `LifetimeUpdate` | REUSE_NATIVE | `LifetimeUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `SlowDeathBehavior` | REUSE_NATIVE | `SlowDeathBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `TransitionDamageFX` | REUSE_NATIVE | `TransitionDamageFX` | Stock SAGE module; keep on the unique Object. | `` |
| ParticleSystem | `SmokeSmallContinuous01` | CYCLE | `SmokeSmallContinuous01` | Cyclic reference; node already visited. | `` |
| ArtFile | `CSSA1TB` | RECOVER_FROM_V25 | `CSSA1TB` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/Textures/CSSA1TB.tga` |
| ArtFile | `CHCSSA1` | RECOVER_FROM_V25 | `CHCSSA1` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/W3D/CHCSSA1.W3D` |
| ArtFile | `EXTireTrack.tga` | REUSE_NATIVE | `EXTireTrack.tga` | Stock ZH EX* texture; expected in base Generals ART, not in the SPECTER overlay or V25 zip listing. | `` |
| BehaviorModule | `AIUpdateInterface` | REUSE_NATIVE | `AIUpdateInterface` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `DestroyDie` | REUSE_NATIVE | `DestroyDie` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `FXListDie` | REUSE_NATIVE | `FXListDie` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `CreateObjectDie` | REUSE_NATIVE | `CreateObjectDie` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `CreateCrateDie` | REUSE_NATIVE | `CreateCrateDie` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `SlowDeathBehavior` | CYCLE | `SlowDeathBehavior` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `TransitionDamageFX` | CYCLE | `TransitionDamageFX` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `FlammableUpdate` | REUSE_NATIVE | `FlammableUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `StealthDetectorUpdate` | REUSE_NATIVE | `StealthDetectorUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| CommandButton | `Command_ConstructChinaCSSA1` | IMPORT_UNIQUE | `Command_ConstructChinaCSSA1` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| Object | `ChinaCSSA1` | CYCLE | `ChinaCSSA1` | Cyclic reference; node already visited. | `` |
| MappedImage | `CSSA1TB` | CYCLE | `CSSA1TB` | Cyclic reference; node already visited. | `` |
| ArtFile | `CSSA1TB` | CYCLE | `CSSA1TB` | Cyclic reference; node already visited. | `` |

## Archive recoveries (in zip, not in parsed extract)

- `MappedImage:CSSA1TB` →
  - `Generals Silent Death V25/Art/Textures/CSSA1TB.tga`
- `MappedImage:SDGuard` →
  - `Generals Silent Death V25/Art/Textures/SDGuard.tga`
- `ArtFile:SDGuard` →
  - `Generals Silent Death V25/Art/Textures/SDGuard.tga`
- `MappedImage:SDStop` →
  - `Generals Silent Death V25/Art/Textures/SDStop.tga`
- `ArtFile:SDStop` →
  - `Generals Silent Death V25/Art/Textures/SDStop.tga`
- `ArtFile:CSSA1TB` →
  - `Generals Silent Death V25/Art/Textures/CSSA1TB.tga`
- `ArtFile:CHCSSA1` →
  - `Generals Silent Death V25/Art/W3D/CHCSSA1.W3D`

## Planned rewrites (not applied)

- `ProjectileArmor` → `SD25_ProjectileArmor`
- `TankArmor` → `SD25_TankArmor`

```
Object ChinaCSSA1

  ; *** ART Parameters ***
  SelectPortrait         = CSSA1TB
  ButtonImage            = CSSA1TB
  
  Draw = W3DTruckDraw ModuleTag_01

    DefaultConditionState
      Model               = CHCSSA1
      Turret              = TURRET
      AltTurret              = TURRET
      AltTurretPitch        = TURRETHEL
      WeaponFireFXBone = PRIMARY GUN_FIRE
      WeaponLaunchBone = PRIMARY GUN_FIRE
      WeaponFireFXBone = SECONDARY GUN_FIRE
      WeaponLaunchBone = SECONDARY GUN_FIRE

    End
    ConditionState       = REALLYDAMAGED
      Model               = CHCSSA1
      Turret              = TURRET
      AltTurret              = TURRET
      AltTurretPitch        = TURRETHEL
      WeaponFireFXBone = PRIMARY GUN_FIRE
      WeaponLaunchBone = PRIMARY GUN_FIRE
      WeaponFir
```

This is a plan only. No Object/Weapon/CommandSet/ART was imported.

