# Transfer plan: `ChinaCSSA1` (stage 3 ART + CWC)

- Generated: 2026-11-11 13:30 Asia/Tehran
- Found in V25 VFS: **True**
- Source: `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/ChinaVehicle.ini`
- Resolver readiness: **manual_rebuild**
- DATA completeness: **MANUAL_REBUILD**
- ART completeness: **AUTO_RECOVERABLE**
- Dest INI (future apply only): `Data\INI\Object\SilentDeath\China\ChinaCSSA1.ini`
- Build buttons: ['Command_ConstructChinaCSSA1']
- CommandSets holding those buttons: ['ChinaSupplyCenterCommandSet']
- Action counts: `{'IMPORT_UNIQUE': 21, 'RECOVER_FROM_V25': 14, 'RENAME_AND_REWRITE': 2, 'REUSE_NATIVE': 28, 'CYCLE': 14, 'MANUAL_REBUILD': 2}`
- Game writes: **False**

## Object meta

- Side: China
- SPECTER side map: China
- Bucket: vehicle
- KindOf: `['ATTACK_NEEDS_LINE_OF_SIGHT', 'CAN_ATTACK', 'CAN_CAST_REFLECTIONS', 'PRELOAD', 'SCORE', 'SELECTABLE', 'VEHICLE']`

## Completeness

DATA and ART are scored separately. Neither score imports anything into SPECTER.

| Track | Status |
|---|---|
| DATA | `MANUAL_REBUILD` |
| ART | `AUTO_RECOVERABLE` |

## CWC / pack-unpack

No catalogued CWC module on this Object.

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
| ArtFile | `SSUserInterface512_001.tga` | RECOVER_FROM_V25 | `SSUserInterface512_001.tga` | Exact stem found inside a nested V25 BIG. Not substituted. | `Generals Silent Death V25/WYS/Textures.big::Art\Textures\ssuserinterface512_0...` |
| ArtFile | `SSAttackMove2` | IMPORT_UNIQUE | `SSAttackMove2` | MappedImage identifier, not a standalone texture file. Pixel data is the Texture= atlas; no similar file was substituted. | `INIZH.big:Data\INI\MappedImages\TextureSize_512\SSUserInterface512.INI` |
| CommandButton | `Command_Guard` | REUSE_NATIVE | `Command_Guard` | Pinned public command; V25 variant is not copied over SPECTER. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| MappedImage | `SDGuard` | RECOVER_FROM_V25 | `SDGuard` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/SDGuard.tga` |
| ArtFile | `SDGuard` | RECOVER_FROM_V25 | `SDGuard` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/SDGuard.tga` |
| CommandButton | `Command_Stop` | REUSE_NATIVE | `Command_Stop` | Pinned public command; V25 variant is not copied over SPECTER. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| MappedImage | `SDStop` | RECOVER_FROM_V25 | `SDStop` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/SDStop.tga` |
| ArtFile | `SDStop` | RECOVER_FROM_V25 | `SDStop` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/SDStop.tga` |
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
| ArtFile | `NVBtmstr_D1` | RECOVER_FROM_V25 | `NVBtmstr_D1` | Exact stem found inside a nested V25 BIG. Not substituted. | `Generals Silent Death V25/WYS/Textures.big::Art\Textures\nvbtmstr_d1.dds` |
| ArtFile | `NVBtMstr_D1.tga` | RECOVER_FROM_V25 | `NVBtMstr_D1.tga` | Exact stem found inside a nested V25 BIG. Not substituted. | `Generals Silent Death V25/WYS/Textures.big::Art\Textures\nvbtmstr_d1.dds` |
| ArtFile | `NVBtMstr_D1.tga` | CYCLE | `NVBtMstr_D1.tga` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `LifetimeUpdate` | REUSE_NATIVE | `LifetimeUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `SlowDeathBehavior` | REUSE_NATIVE | `SlowDeathBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `TransitionDamageFX` | REUSE_NATIVE | `TransitionDamageFX` | Stock SAGE module; keep on the unique Object. | `` |
| ParticleSystem | `SmokeSmallContinuous01` | CYCLE | `SmokeSmallContinuous01` | Cyclic reference; node already visited. | `` |
| ArtFile | `CSSA1TB` | RECOVER_FROM_V25 | `CSSA1TB` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CSSA1TB.tga` |
| ArtFile | `CHCSSA1` | RECOVER_FROM_V25 | `CHCSSA1` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/W3D/CHCSSA1.W3D` |
| ArtFile | `SDNSM04.DDS` | RECOVER_FROM_V25 | `SDNSM04.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/SDNSM04.dds` |
| ArtFile | `CHCSSA1T.DDS` | RECOVER_FROM_V25 | `CHCSSA1T.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHCSSA1T.dds` |
| ArtFile | `CHCSSA1B.DDS` | RECOVER_FROM_V25 | `CHCSSA1B.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHCSSA1B.dds` |
| ArtFile | `EXTireTrack.tga` | RECOVER_FROM_V25 | `EXTireTrack.tga` | Exact stem found inside a nested V25 BIG. Not substituted. | `Generals Silent Death V25/WYS/Textures.big::Art\Textures\extiretrack.dds` |
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

## ART recoveries (exact stem; no similar-name substitute)

- `MappedImage:CSSA1TB` found_in=`None`
  - `Generals Silent Death V25/Art/Textures/CSSA1TB.tga`
- `ArtFile:SSUserInterface512_001.tga` found_in=`nested_big`
  - `Generals Silent Death V25/WYS/Textures.big::Art\Textures\ssuserinterface512_001.tga`
  - container=`nested_big` file=`ssuserinterface512_001.tga` source_big=`Generals Silent Death V25/WYS/Textures.big` inner=`Art\Textures\ssuserinterface512_001.tga`
- `MappedImage:SDGuard` found_in=`None`
  - `Generals Silent Death V25/Art/Textures/SDGuard.tga`
- `ArtFile:SDGuard` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/SDGuard.tga`
  - container=`zip` file=`SDGuard.tga` source_big=`None` inner=`None`
- `MappedImage:SDStop` found_in=`None`
  - `Generals Silent Death V25/Art/Textures/SDStop.tga`
- `ArtFile:SDStop` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/SDStop.tga`
  - container=`zip` file=`SDStop.tga` source_big=`None` inner=`None`
- `ArtFile:NVBtmstr_D1` found_in=`nested_big`
  - `Generals Silent Death V25/WYS/Textures.big::Art\Textures\nvbtmstr_d1.dds`
  - `Generals Silent Death V25/WYS/W3D.big::Art\W3D\NVBtMstr_D1.W3D`
  - container=`nested_big` file=`nvbtmstr_d1.dds` source_big=`Generals Silent Death V25/WYS/Textures.big` inner=`Art\Textures\nvbtmstr_d1.dds`
  - container=`nested_big` file=`NVBtMstr_D1.W3D` source_big=`Generals Silent Death V25/WYS/W3D.big` inner=`Art\W3D\NVBtMstr_D1.W3D`
  - W3D textures: ['NVBtMstr_D1.tga']
  - W3D anims (inside model, not separate files): ['NVBTMSTR_D1.CHASSIS']
- `ArtFile:NVBtMstr_D1.tga` found_in=`nested_big`
  - `Generals Silent Death V25/WYS/Textures.big::Art\Textures\nvbtmstr_d1.dds`
  - `Generals Silent Death V25/WYS/W3D.big::Art\W3D\NVBtMstr_D1.W3D`
  - container=`nested_big` file=`nvbtmstr_d1.dds` source_big=`Generals Silent Death V25/WYS/Textures.big` inner=`Art\Textures\nvbtmstr_d1.dds`
  - container=`nested_big` file=`NVBtMstr_D1.W3D` source_big=`Generals Silent Death V25/WYS/W3D.big` inner=`Art\W3D\NVBtMstr_D1.W3D`
  - W3D textures: ['NVBtMstr_D1.tga']
  - W3D anims (inside model, not separate files): ['NVBTMSTR_D1.CHASSIS']
- `ArtFile:CSSA1TB` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CSSA1TB.tga`
  - container=`zip` file=`CSSA1TB.tga` source_big=`None` inner=`None`
- `ArtFile:CHCSSA1` found_in=`zip`
  - `Generals Silent Death V25/Art/W3D/CHCSSA1.W3D`
  - container=`zip` file=`CHCSSA1.W3D` source_big=`None` inner=`None`
  - W3D textures: ['SDNSM04.DDS', 'CHCSSA1T.DDS', 'CHCSSA1B.DDS']
  - W3D anims (inside model, not separate files): ['CHCSSA1.TIRE02', 'CHCSSA1.TIRE01', 'CHCSSA1.TIRE08', 'CHCSSA1.TIRE07', 'CHCSSA1.TIRE06', 'CHCSSA1.TIRE05', 'CHCSSA1.TURRETHEL', 'CHCSSA1.TURRET', 'CHCSSA1.CHASSIS']
- `ArtFile:SDNSM04.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/SDNSM04.dds`
  - container=`zip` file=`SDNSM04.dds` source_big=`None` inner=`None`
- `ArtFile:CHCSSA1T.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHCSSA1T.dds`
  - container=`zip` file=`CHCSSA1T.dds` source_big=`None` inner=`None`
- `ArtFile:CHCSSA1B.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHCSSA1B.dds`
  - container=`zip` file=`CHCSSA1B.dds` source_big=`None` inner=`None`
- `ArtFile:EXTireTrack.tga` found_in=`nested_big`
  - `Generals Silent Death V25/WYS/Textures.big::Art\Textures\extiretrack.dds`
  - container=`nested_big` file=`extiretrack.dds` source_big=`Generals Silent Death V25/WYS/Textures.big` inner=`Art\Textures\extiretrack.dds`

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

