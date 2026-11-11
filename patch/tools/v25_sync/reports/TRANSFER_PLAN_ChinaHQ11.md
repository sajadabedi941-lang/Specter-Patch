# Transfer plan: `ChinaHQ11`

- Generated: 2026-11-11 13:05 Asia/Tehran
- Found in V25 VFS: **True**
- Source: `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/ChinaVehicle.ini`
- Readiness: **manual_rebuild**
- Dest INI (future apply only): `Data\INI\Object\SilentDeath\China\ChinaHQ11.ini`
- Build buttons: ['Command_ConstructChinaHQ11']
- CommandSets holding those buttons: ['ChinaSupplyCenterCommandSet']
- Action counts: `{'IMPORT_UNIQUE': 36, 'RECOVER_FROM_V25': 8, 'RENAME_AND_REWRITE': 3, 'MANUAL_REBUILD': 4, 'REUSE_NATIVE': 22, 'CYCLE': 13, 'INDEPENDENT_ADD': 5}`
- Game writes: **False**

## Object meta

- Side: China
- SPECTER side map: China
- Bucket: air_defense
- KindOf: `['CAN_ATTACK', 'CAN_CAST_REFLECTIONS', 'DONT_AUTO_CRUSH_INFANTRY', 'FS_BASE_DEFENSE', 'HUGE_VEHICLE', 'PRELOAD', 'SCORE', 'SELECTABLE', 'VEHICLE']`

## Compatibility notes (reasoned from INI flags, not guessed)

- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType JET_MISSILES already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType EXPLOSION already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType MICROWAVE already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType HACK already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `stealth_detector_filter`: StealthDetector ExtraRequiredKindOf uses stock KindOf tokens already on SPECTER aircraft.
- **KEEP_V25_FLAGS** `antiair_flags_present`: Weapon already sets AntiAirborneVehicle and/or anti-missile flags. SPECTER aircraft/missiles keep their KindOf; no SPECTER rewrite.

## Dependency actions

| Kind | Name | Action | Planned | Reason | Source |
|---|---|---|---|---|---|
| Object | `ChinaHQ11` | IMPORT_UNIQUE | `ChinaHQ11` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/ChinaVehicle...` |
| MappedImage | `CHHQ11TB` | RECOVER_FROM_V25 | `CHHQ11TB` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga` |
| Armor | `HumveeArmor` | RENAME_AND_REWRITE | `SD25_HumveeArmor` | Same name, different effective behavior. SPECTER original stays; V25 copy becomes SD25_HumveeArmor with a full reference rewrite. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Armor.ini` |
| FXList | `TruckDamageFX` | MANUAL_REBUILD | `TruckDamageFX` | Not in parsed V25 VFS, not in SPECTER, and no filename in the V25 zip listing. | `` |
| FXList | `FX_CWCgenTankDamageTransition` | IMPORT_UNIQUE | `FX_CWCgenTankDamageTransition` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_CWCgenTankDeathRubble1` | IMPORT_UNIQUE | `FX_CWCgenTankDeathRubble1` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_CWCgenTankDeathRubble2` | IMPORT_UNIQUE | `FX_CWCgenTankDeathRubble2` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| Weapon | `HQ11MissileWeapon` | IMPORT_UNIQUE | `HQ11MissileWeapon` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Weapon.ini` |
| AudioEvent | `S400TriumfSOU` | IMPORT_UNIQUE | `S400TriumfSOU` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/SoundEffects.ini` |
| FXList | `WeaponFX_JetMissileDetonation` | REUSE_NATIVE | `WeaponFX_JetMissileDetonation` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_CWCruS300MissileLaunch` | IMPORT_UNIQUE | `FX_CWCruS300MissileLaunch` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `WeaponFX_CWCgenLargeAntiAirMissileDetonation` | IMPORT_UNIQUE | `WeaponFX_CWCgenLargeAntiAirMissileDetonation` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| ParticleSystem | `CWCgenExhaustLargeMissile` | IMPORT_UNIQUE | `CWCgenExhaustLargeMissile` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| Object | `CWCruS300Missile` | IMPORT_UNIQUE | `CWCruS300Missile` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/WeaponObject...` |
| Armor | `ProjectileArmor` | RENAME_AND_REWRITE | `SD25_ProjectileArmor` | Same name, different effective behavior. SPECTER original stays; V25 copy becomes SD25_ProjectileArmor with a full reference rewrite. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Armor.ini` |
| FXList | `WeaponFX_CWCgenLargeAntiAirMissileDetonation` | CYCLE | `WeaponFX_CWCgenLargeAntiAirMissileDetonation` | Cyclic reference; node already visited. | `` |
| Locomotor | `CWCruS300MissileLocomotor` | IMPORT_UNIQUE | `CWCruS300MissileLocomotor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Locomotor.ini` |
| ArtFile | `CWCruS300_m` | IMPORT_UNIQUE | `CWCruS300_m` | Art stem present in parsed V25 BIGs. | `` |
| BehaviorModule | `InstantDeathBehavior` | REUSE_NATIVE | `InstantDeathBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `PhysicsBehavior` | REUSE_NATIVE | `PhysicsBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `MissileAIUpdate` | REUSE_NATIVE | `MissileAIUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| DamageType | `JET_MISSILES` | REUSE_NATIVE | `JET_MISSILES` | DamageType exists on SPECTER Armor tables. | `` |
| Weapon | `CWCgenVehicleExplodeWeapon` | IMPORT_UNIQUE | `CWCgenVehicleExplodeWeapon` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Weapon.ini` |
| ObjectCreationList | `OCL_CWCgenProjectileTreeImpact` | IMPORT_UNIQUE | `OCL_CWCgenProjectileTreeImpact` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ObjectCreationList.ini` |
| Object | `CWCgenTreesOnFire` | IMPORT_UNIQUE | `CWCgenTreesOnFire` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/Hulk.ini` |
| Armor | `InvulnerableAllArmor` | RENAME_AND_REWRITE | `SD25_InvulnerableAllArmor` | Same name, different effective behavior. SPECTER original stays; V25 copy becomes SD25_InvulnerableAllArmor with a full reference rewrite. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Armor.ini` |
| BehaviorModule | `PhysicsBehavior` | CYCLE | `PhysicsBehavior` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `LifetimeUpdate` | REUSE_NATIVE | `LifetimeUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `FireWeaponWhenDeadBehavior` | INDEPENDENT_ADD | `FireWeaponWhenDeadBehavior` | Unknown behavior kept on the unique Object; not deleted. | `` |
| BehaviorModule | `NeutronMissileSlowDeathBehavior` | INDEPENDENT_ADD | `NeutronMissileSlowDeathBehavior` | Unknown behavior kept on the unique Object; not deleted. | `` |
| BehaviorModule | `HeightDieUpdate` | REUSE_NATIVE | `HeightDieUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| DamageType | `EXPLOSION` | REUSE_NATIVE | `EXPLOSION` | DamageType exists on SPECTER Armor tables. | `` |
| Weapon | `CWCruSA10RadarWeapon` | IMPORT_UNIQUE | `CWCruSA10RadarWeapon` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Weapon.ini` |
| DamageType | `MICROWAVE` | REUSE_NATIVE | `MICROWAVE` | DamageType exists on SPECTER Armor tables. | `` |
| CommandSet | `CWCruS300CommandSet` | IMPORT_UNIQUE | `CWCruS300CommandSet` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandSet.ini` |
| CommandButton | `Command_S300_Prone` | IMPORT_UNIQUE | `Command_S300_Prone` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| SpecialPower | `SpecialAbilityCWCruFakeRider_Inf_Prone` | IMPORT_UNIQUE | `SpecialAbilityCWCruFakeRider_Inf_Prone` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/SpecialPower.ini` |
| MappedImage | `BUSHU` | IMPORT_UNIQUE | `BUSHU` | Name is free in SPECTER FINAL; unique-path import. | `00LSF0118.big:Data\ini\MappedImages\TextureSize_512\leesf.INI` |
| ArtFile | `BUSHUtb.tga` | IMPORT_UNIQUE | `BUSHUtb.tga` | Art stem present in parsed V25 BIGs. | `` |
| ArtFile | `BUSHU` | MANUAL_REBUILD | `BUSHU` | Art stem not in parsed VFS, SPECTER, or V25 zip listing. | `` |
| CommandButton | `Command_Stop` | REUSE_NATIVE | `Command_Stop` | Pinned public command; V25 variant is not copied over SPECTER. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| MappedImage | `SDStop` | RECOVER_FROM_V25 | `SDStop` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/SDStop.tga` |
| ArtFile | `SDStop` | RECOVER_FROM_V25 | `SDStop` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/Textures/SDStop.tga` |
| AudioEvent | `AvengerVoiceSelect` | REUSE_NATIVE | `AvengerVoiceSelect` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoiceMove` | REUSE_NATIVE | `AvengerVoiceMove` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoicePaint` | REUSE_NATIVE | `AvengerVoicePaint` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoiceAttack` | REUSE_NATIVE | `AvengerVoiceAttack` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoiceCreate` | REUSE_NATIVE | `AvengerVoiceCreate` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| Locomotor | `CWCruS300Locomotor` | IMPORT_UNIQUE | `CWCruS300Locomotor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Locomotor.ini` |
| Locomotor | `CWCruS300DeployedLocomotor` | IMPORT_UNIQUE | `CWCruS300DeployedLocomotor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Locomotor.ini` |
| SpecialPower | `SpecialAbilityCWCruFakeRider_Inf_Stand` | IMPORT_UNIQUE | `SpecialAbilityCWCruFakeRider_Inf_Stand` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/SpecialPower.ini` |
| SpecialPower | `SpecialAbilityCWCruFakeRider_Inf_Prone` | CYCLE | `SpecialAbilityCWCruFakeRider_Inf_Prone` | Cyclic reference; node already visited. | `` |
| ObjectCreationList | `OCL_CWCruSpecialAbilityFakeRider_Inf_Stand` | IMPORT_UNIQUE | `OCL_CWCruSpecialAbilityFakeRider_Inf_Stand` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ObjectCreationList.ini` |
| Object | `CWCruFakeRider_Inf_Stand` | IMPORT_UNIQUE | `CWCruFakeRider_Inf_Stand` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/FakeRiders.ini` |
| Armor | `CWCgenFakeRider_Inf_Armor` | IMPORT_UNIQUE | `CWCgenFakeRider_Inf_Armor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Armor.ini` |
| Locomotor | `CWCgenFakeRiderLocomotor` | IMPORT_UNIQUE | `CWCgenFakeRiderLocomotor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Locomotor.ini` |
| Weapon | `CWCgenSuicideWeapon` | IMPORT_UNIQUE | `CWCgenSuicideWeapon` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Weapon.ini` |
| DamageType | `HACK` | REUSE_NATIVE | `HACK` | DamageType exists on SPECTER Armor tables. | `` |
| BehaviorModule | `AIUpdateInterface` | REUSE_NATIVE | `AIUpdateInterface` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `FireWeaponUpdate` | INDEPENDENT_ADD | `FireWeaponUpdate` | Module class is kept on the unique Object; SPECTER core is not patched. | `` |
| BehaviorModule | `SlavedUpdate` | INDEPENDENT_ADD | `SlavedUpdate` | Unknown behavior kept on the unique Object; not deleted. | `` |
| BehaviorModule | `DestroyDie` | REUSE_NATIVE | `DestroyDie` | Stock SAGE module; keep on the unique Object. | `` |
| ObjectCreationList | `OCL_CWCruSpecialAbilityFakeRider_Inf_Prone` | IMPORT_UNIQUE | `OCL_CWCruSpecialAbilityFakeRider_Inf_Prone` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ObjectCreationList.ini` |
| Object | `CWCruFakeRider_Inf_Prone` | IMPORT_UNIQUE | `CWCruFakeRider_Inf_Prone` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/FakeRiders.ini` |
| Armor | `CWCgenFakeRider_Inf_Armor` | CYCLE | `CWCgenFakeRider_Inf_Armor` | Cyclic reference; node already visited. | `` |
| Locomotor | `CWCgenFakeRiderLocomotor` | CYCLE | `CWCgenFakeRiderLocomotor` | Cyclic reference; node already visited. | `` |
| Weapon | `CWCgenSuicideWeapon` | CYCLE | `CWCgenSuicideWeapon` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `AIUpdateInterface` | CYCLE | `AIUpdateInterface` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `FireWeaponUpdate` | CYCLE | `FireWeaponUpdate` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `SlavedUpdate` | CYCLE | `SlavedUpdate` | Cyclic reference; node already visited. | `` |
| BehaviorModule | `DestroyDie` | CYCLE | `DestroyDie` | Cyclic reference; node already visited. | `` |
| ObjectCreationList | `OCL_CWCgenTankDeathTrails` | IMPORT_UNIQUE | `OCL_CWCgenTankDeathTrails` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ObjectCreationList.ini` |
| ParticleSystem | `CWCgenTankDeathSmokeDamaged` | IMPORT_UNIQUE | `CWCgenTankDeathSmokeDamaged` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| ParticleSystem | `CWCgenTankDeathSmokeReallyDamaged` | IMPORT_UNIQUE | `CWCgenTankDeathSmokeReallyDamaged` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| ParticleSystem | `CWCgenTankDeathSmokeRubble` | IMPORT_UNIQUE | `CWCgenTankDeathSmokeRubble` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| ArtFile | `CHHQ11TB` | RECOVER_FROM_V25 | `CHHQ11TB` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga` |
| ArtFile | `HQ11` | RECOVER_FROM_V25 | `HQ11` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/W3D/HQ11.W3D` |
| ArtFile | `HQ11.HQ11` | RECOVER_FROM_V25 | `HQ11.HQ11` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/W3D/HQ11.W3D` |
| ArtFile | `EXTireTrack.tga` | REUSE_NATIVE | `EXTireTrack.tga` | Stock ZH EX* texture; expected in base Generals ART, not in the SPECTER overlay or V25 zip listing. | `` |
| ArtFile | `HQ11RD` | RECOVER_FROM_V25 | `HQ11RD` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/W3D/HQ11RD.W3D` |
| ArtFile | `HQ11RD.HQ11RD` | RECOVER_FROM_V25 | `HQ11RD.HQ11RD` | Not in parsed extract/BIGs; file exists in the V25 zip. | `Generals Silent Death V25/Art/W3D/HQ11RD.W3D` |
| BehaviorModule | `RiderChangeContain` | MANUAL_REBUILD | `RiderChangeContain` | CWC module needs a SPECTER-style rebuild; capability is not dropped. | `` |
| BehaviorModule | `OCLSpecialPower` | MANUAL_REBUILD | `OCLSpecialPower` | CWC module needs a SPECTER-style rebuild; capability is not dropped. | `` |
| BehaviorModule | `EnemyNearUpdate` | INDEPENDENT_ADD | `EnemyNearUpdate` | Unknown behavior kept on the unique Object; not deleted. | `` |
| BehaviorModule | `StealthDetectorUpdate` | REUSE_NATIVE | `StealthDetectorUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `TransitionDamageFX` | REUSE_NATIVE | `TransitionDamageFX` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `SlowDeathBehavior` | REUSE_NATIVE | `SlowDeathBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| CommandButton | `Command_ConstructChinaHQ11` | IMPORT_UNIQUE | `Command_ConstructChinaHQ11` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| Object | `ChinaHQ11` | CYCLE | `ChinaHQ11` | Cyclic reference; node already visited. | `` |
| MappedImage | `CHHQ11TB` | CYCLE | `CHHQ11TB` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11TB` | CYCLE | `CHHQ11TB` | Cyclic reference; node already visited. | `` |

## Archive recoveries (in zip, not in parsed extract)

- `MappedImage:CHHQ11TB` →
  - `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga`
- `MappedImage:SDStop` →
  - `Generals Silent Death V25/Art/Textures/SDStop.tga`
- `ArtFile:SDStop` →
  - `Generals Silent Death V25/Art/Textures/SDStop.tga`
- `ArtFile:CHHQ11TB` →
  - `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga`
- `ArtFile:HQ11` →
  - `Generals Silent Death V25/Art/W3D/HQ11.W3D`
- `ArtFile:HQ11.HQ11` →
  - `Generals Silent Death V25/Art/W3D/HQ11.W3D`
- `ArtFile:HQ11RD` →
  - `Generals Silent Death V25/Art/W3D/HQ11RD.W3D`
- `ArtFile:HQ11RD.HQ11RD` →
  - `Generals Silent Death V25/Art/W3D/HQ11RD.W3D`

## Planned rewrites (not applied)

- `HumveeArmor` → `SD25_HumveeArmor`
- `ProjectileArmor` → `SD25_ProjectileArmor`
- `InvulnerableAllArmor` → `SD25_InvulnerableAllArmor`

```
Object ChinaHQ11

  ; *** ART Parameters ***
  SelectPortrait = CHHQ11TB
  ButtonImage    = CHHQ11TB

    Draw = W3DTruckDraw ModuleTag_01

    AttachToBoneInAnotherModule = CORE
    ParticlesAttachedToAnimatedBones = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY

    DefaultConditionState
      Model = HQ11
      Animation = HQ11.HQ11
      AnimationMode = ONCE_BACKWARDS
      Flags = MAINTAIN_FRAME_ACROSS_STATES
    End
    AliasConditionState = RIDER1
    AliasConditionState = RIDER1 MOVING

    ConditionState = REALLYDAMAGED
      Model = HQ11
      Animation = HQ11.HQ11
      AnimationMode = ONCE_BACKWARDS
      Flags = MAINTAIN_FRAME_ACROSS_STATES
    End
    AliasConditionState = RIDER1 REALLYDAMAGED
    AliasConditionState = RIDER1 REALLYDAMAGED MOVING
    
    ConditionStat
```

This is a plan only. No Object/Weapon/CommandSet/ART was imported.

