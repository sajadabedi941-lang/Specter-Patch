# Transfer plan: `ChinaHQ11` (stage 4 DATA rebuild)

- Generated: 2026-11-11 14:31 Asia/Tehran
- Found in V25 VFS: **True**
- Source: `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/ChinaVehicle.ini`
- Resolver readiness: **auto_fixable**
- DATA completeness: **READY_FOR_TRANSFER_PLAN**
- ART completeness: **AUTO_RECOVERABLE**
- Dest INI (future apply only): `Data\INI\Object\SilentDeath\China\ChinaHQ11.ini`
- Build buttons: ['Command_ConstructChinaHQ11']
- CommandSets holding those buttons: ['ChinaSupplyCenterCommandSet']
- Action counts: `{'IMPORT_UNIQUE': 23, 'RECOVER_FROM_V25': 15, 'RENAME_AND_REWRITE': 3, 'INDEPENDENT_ADD': 8, 'REUSE_NATIVE': 27, 'CYCLE': 13}`
- Game writes: **False**

## Object meta

- Side: China
- SPECTER side map: China
- Bucket: air_defense
- KindOf: `['CAN_ATTACK', 'CAN_CAST_REFLECTIONS', 'DONT_AUTO_CRUSH_INFANTRY', 'FS_BASE_DEFENSE', 'HUGE_VEHICLE', 'PRELOAD', 'SCORE', 'SELECTABLE', 'VEHICLE']`

## Completeness

DATA and ART are scored separately. Neither score imports anything into SPECTER.

| Track | Status |
|---|---|
| DATA | `READY_FOR_TRANSFER_PLAN` |
| ART | `AUTO_RECOVERABLE` |

## CWC / pack-unpack

### `RiderChangeContain`

- Origin: CWC.exe (not stock ZH)
- SPECTER exe: unsafe_on_stock_zh
- What it does: Hides rider objects inside a vehicle and swaps ModelCondition, WeaponSet, ObjectStatus, CommandSet, and Locomotor per RiderN slot. Used as deploy (stand vs prone) for TELs/AD.
- Rebuild action: **INDEPENDENT_ADD** (capability kept: packed vs deployed weapon and draw; pack/unpack)
- Keys: `{'Slots': '1', 'AllowInsideKindOf': 'INFANTRY'}`
- Riders: `[{'slot': 'Rider1', 'value': 'CWCruFakeRider_Inf_Stand RIDER1 WEAPON_RIDER1 STATUS_RIDER1 CWCruS300CommandSet SET_NORMAL'}, {'slot': 'Rider2', 'value': 'CWCruFakeRider_Inf_Prone RIDER2 WEAPON_RIDER2 STATUS_RIDER2 CWCruS300DeployedCommandSet SET_SLUGGISH'}]`

- Do not copy RiderChangeContain onto SPECTER. It is CWC.exe-only.
- Replace with DeployStyleAIUpdate on the unique Object (PackTime/UnpackTime 2000, TurretsFunctionOnlyWhenDeployed = Yes, TurretsMustCenterBeforePacking = Yes, ResetTurretBeforePacking = Yes).
- Map Draw RIDER1 → DefaultConditionState / PACKING; RIDER2 → DEPLOYED / UNPACKING.
- Map WeaponSet WEAPON_RIDER1 → Conditions = None PRIMARY None; WEAPON_RIDER2 → Conditions = DEPLOYED PRIMARY <missile>.
- Do not spawn fake-rider infantry.

```
Behavior = RiderChangeContain ModuleTag_Deployment99
    ;A list of each valid rider that is allowed to ride this object. Each rider is
    ;assigned a modelcondition state, a weaponset flag, an object status bit, and
    ;a commandset override. The actual object is hidden inside the container so the
    ;visible rider is fluff. Also riders are deleted (not killed) when the bike is
    ;destroyed, so all deaths must be OCLs on the bike.
    Rider1 = CWCruFakeRider_Inf_Stand RIDER1 WEAPON_RIDER1 STATUS_RIDER1 CWCruS300CommandSet SET_NORMAL
    Rider2 = CWCruFakeRider_Inf_Prone RIDER2 WEAPON_RID
```

### `OCLSpecialPower`

- Origin: Stock ZH module; CWC templates/OCLs are custom
- SPECTER exe: module_ok_templates_must_be_unique
- What it does: Fires a SpecialPower that creates objects via OCL. CWC uses it to apply fake-rider deploy/undeploy and also for smoke grenades.
- Rebuild action: **INDEPENDENT_ADD** (capability kept: button that switches packed/deployed state)
- Keys: `{'SpecialPowerTemplate': 'SpecialAbilityCWCruFakeRider_Inf_Stand', 'OCL': 'OCL_CWCruSpecialAbilityFakeRider_Inf_Stand'}`
- Riders: `[]`

- Do not import OCLSpecialPower, the CIA-intel SpecialPower templates, or the fake-rider OCLs.
- Replace both buttons with stock Command_Deploy on one unique CommandSet (plus Command_Stop).
- SPECIAL_CIA_INTELLIGENCE must not be reused; it would hijack SPECTER CIA intel.

```
Behavior = OCLSpecialPower ModuleTag_Deployment98
    SpecialPowerTemplate = SpecialAbilityCWCruFakeRider_Inf_Stand
    OCL = OCL_CWCruSpecialAbilityFakeRider_Inf_Stand
  End
```

### `EnemyNearUpdate`

- Origin: CWC house-color helper (not required on stock ZH)
- SPECTER exe: optional
- What it does: Empty module in V25 (house color / nearby-enemy hook). No gameplay keys.
- Rebuild action: **INDEPENDENT_ADD** (capability kept: house-color / nearby-enemy hook if the exe honors it)
- Keys: `{}`
- Riders: `[]`

- Keep on the unique Object. If stock Generals.exe ignores it, drop only the module class, never the rest of the unit.

```
Behavior = EnemyNearUpdate ModuleTag_Housecolor
    ;nothing
  End
```

### `FireWeaponUpdate`

- Origin: Stock ZH module used by CWC as a radar/search weapon ticker
- SPECTER exe: keep_on_unique_object
- What it does: Periodically fires a Weapon (ChinaHQ11 uses CWCruSA10RadarWeapon).
- Rebuild action: **INDEPENDENT_ADD** (capability kept: passive radar / search weapon)
- Keys: `{}`
- Riders: `[]`

- Keep on the unique Object with a unique Weapon path. Do not retarget SPECTER radar tables.

```
Behavior = FireWeaponUpdate ModuleTag_Radar
    Weapon = CWCruSA10RadarWeapon
    ExclusiveWeaponDelay = 500
  End
```


## Compatibility notes (reasoned from INI flags, not guessed)

- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType JET_MISSILES already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType EXPLOSION already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `damage_type_present_on_specter_armor`: DamageType MICROWAVE already appears in SPECTER Armor tables, so this unique weapon can injure SPECTER units that use those tables. SPECTER Armor.ini is not modified.
- **REUSE_NATIVE** `stealth_detector_filter`: StealthDetector ExtraRequiredKindOf uses stock KindOf tokens already on SPECTER aircraft.
- **KEEP_V25_FLAGS** `antiair_flags_present`: Weapon already sets AntiAirborneVehicle and/or anti-missile flags. SPECTER aircraft/missiles keep their KindOf; no SPECTER rewrite.

## Dependency actions

| Kind | Name | Action | Planned | Reason | Source |
|---|---|---|---|---|---|
| Object | `ChinaHQ11` | IMPORT_UNIQUE | `ChinaHQ11` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/object/ChinaVehicle...` |
| MappedImage | `CHHQ11TB` | RECOVER_FROM_V25 | `CHHQ11TB` | Missing from parsed INI VFS; matching filename exists in the V25 archive. | `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga` |
| Armor | `HumveeArmor` | RENAME_AND_REWRITE | `SD25_HumveeArmor` | Same name, different effective behavior. SPECTER original stays; V25 copy becomes SD25_HumveeArmor with a full reference rewrite. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Armor.ini` |
| DamageFX | `TruckDamageFX` | INDEPENDENT_ADD | `SD25_TruckDamageFX` | Independent unique-path clone of V25 DamageFX TruckDamageFX. SPECTER public DamageFX.ini is not rewritten. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/DamageFX.ini` |
| FXList | `FX_DamageTankStruck` | REUSE_NATIVE | `FX_DamageTankStruck` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_HeroicDamageTankStruck` | REUSE_NATIVE | `FX_HeroicDamageTankStruck` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_DamageSmallTankStruckSmallArms` | REUSE_NATIVE | `FX_DamageSmallTankStruckSmallArms` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_HeroicDamageTankStruckSmallArms` | REUSE_NATIVE | `FX_HeroicDamageTankStruckSmallArms` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_DamageTankStruckSmallArms` | REUSE_NATIVE | `FX_DamageTankStruckSmallArms` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_DamageDisableVehicle` | REUSE_NATIVE | `FX_DamageDisableVehicle` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_HeroicDamageDisableVehicle` | REUSE_NATIVE | `FX_HeroicDamageDisableVehicle` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_DamageMajorArmorPiercing` | REUSE_NATIVE | `FX_DamageMajorArmorPiercing` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_DamageMinorArmorPiercing` | REUSE_NATIVE | `FX_DamageMinorArmorPiercing` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
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
| BehaviorModule | `FireWeaponWhenDeadBehavior` | INDEPENDENT_ADD | `FireWeaponWhenDeadBehavior` | Module class is kept on the unique Object; SPECTER core is not patched. | `` |
| BehaviorModule | `NeutronMissileSlowDeathBehavior` | INDEPENDENT_ADD | `NeutronMissileSlowDeathBehavior` | Module class is kept on the unique Object; SPECTER core is not patched. | `` |
| BehaviorModule | `HeightDieUpdate` | REUSE_NATIVE | `HeightDieUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| DamageType | `EXPLOSION` | REUSE_NATIVE | `EXPLOSION` | DamageType exists on SPECTER Armor tables. | `` |
| Weapon | `CWCruSA10RadarWeapon` | IMPORT_UNIQUE | `CWCruSA10RadarWeapon` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Weapon.ini` |
| DamageType | `MICROWAVE` | REUSE_NATIVE | `MICROWAVE` | DamageType exists on SPECTER Armor tables. | `` |
| AudioEvent | `AvengerVoiceSelect` | REUSE_NATIVE | `AvengerVoiceSelect` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoiceMove` | REUSE_NATIVE | `AvengerVoiceMove` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoicePaint` | REUSE_NATIVE | `AvengerVoicePaint` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoiceAttack` | REUSE_NATIVE | `AvengerVoiceAttack` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| AudioEvent | `AvengerVoiceCreate` | REUSE_NATIVE | `AvengerVoiceCreate` | Effective gameplay fingerprint matches SPECTER; reuse, do not copy. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Voice.ini` |
| Locomotor | `CWCruS300Locomotor` | IMPORT_UNIQUE | `CWCruS300Locomotor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Locomotor.ini` |
| Locomotor | `CWCruS300DeployedLocomotor` | IMPORT_UNIQUE | `CWCruS300DeployedLocomotor` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/Locomotor.ini` |
| ObjectCreationList | `OCL_CWCgenTankDeathTrails` | IMPORT_UNIQUE | `OCL_CWCgenTankDeathTrails` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ObjectCreationList.ini` |
| ParticleSystem | `CWCgenTankDeathSmokeDamaged` | IMPORT_UNIQUE | `CWCgenTankDeathSmokeDamaged` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| ParticleSystem | `CWCgenTankDeathSmokeReallyDamaged` | IMPORT_UNIQUE | `CWCgenTankDeathSmokeReallyDamaged` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| ParticleSystem | `CWCgenTankDeathSmokeRubble` | IMPORT_UNIQUE | `CWCgenTankDeathSmokeRubble` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/ParticleSystem.ini` |
| FXList | `FX_CWCgenTankDamageTransition` | IMPORT_UNIQUE | `FX_CWCgenTankDamageTransition` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_CWCgenTankDeathRubble1` | IMPORT_UNIQUE | `FX_CWCgenTankDeathRubble1` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| FXList | `FX_CWCgenTankDeathRubble2` | IMPORT_UNIQUE | `FX_CWCgenTankDeathRubble2` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/FXList.ini` |
| ArtFile | `CHHQ11TB` | RECOVER_FROM_V25 | `CHHQ11TB` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga` |
| ArtFile | `HQ11` | RECOVER_FROM_V25 | `HQ11` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/W3D/HQ11.W3D` |
| ArtFile | `SDNSM04.DDS` | RECOVER_FROM_V25 | `SDNSM04.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/SDNSM04.dds` |
| ArtFile | `GLASS1.TGA` | RECOVER_FROM_V25 | `GLASS1.TGA` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/Glass1.tga` |
| ArtFile | `CHHQ11B.DDS` | RECOVER_FROM_V25 | `CHHQ11B.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHHQ11B.dds` |
| ArtFile | `CHHQ11N.DDS` | RECOVER_FROM_V25 | `CHHQ11N.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHHQ11N.dds` |
| ArtFile | `CHHQ11G.DDS` | RECOVER_FROM_V25 | `CHHQ11G.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHHQ11G.dds` |
| ArtFile | `CHHQ11F.DDS` | RECOVER_FROM_V25 | `CHHQ11F.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHHQ11F.dds` |
| ArtFile | `CHHQ11T.DDS` | RECOVER_FROM_V25 | `CHHQ11T.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHHQ11T.dds` |
| ArtFile | `CHHQ11R.DDS` | RECOVER_FROM_V25 | `CHHQ11R.DDS` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/Textures/CHHQ11R.dds` |
| ArtFile | `HQ11.HQ11` | RECOVER_FROM_V25 | `HQ11.HQ11` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/W3D/HQ11.W3D` |
| ArtFile | `SDNSM04.DDS` | CYCLE | `SDNSM04.DDS` | Cyclic reference; node already visited. | `` |
| ArtFile | `GLASS1.TGA` | CYCLE | `GLASS1.TGA` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11B.DDS` | CYCLE | `CHHQ11B.DDS` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11N.DDS` | CYCLE | `CHHQ11N.DDS` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11G.DDS` | CYCLE | `CHHQ11G.DDS` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11F.DDS` | CYCLE | `CHHQ11F.DDS` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11T.DDS` | CYCLE | `CHHQ11T.DDS` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11R.DDS` | CYCLE | `CHHQ11R.DDS` | Cyclic reference; node already visited. | `` |
| ArtFile | `EXTireTrack.tga` | RECOVER_FROM_V25 | `EXTireTrack.tga` | Exact stem found inside a nested V25 BIG. Not substituted. | `Generals Silent Death V25/WYS/Textures.big::Art\Textures\extiretrack.dds` |
| ArtFile | `HQ11RD` | RECOVER_FROM_V25 | `HQ11RD` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/W3D/HQ11RD.W3D` |
| ArtFile | `HQ11RD.HQ11RD` | RECOVER_FROM_V25 | `HQ11RD.HQ11RD` | Exact stem found as a loose zip member. Not substituted. | `Generals Silent Death V25/Art/W3D/HQ11RD.W3D` |
| BehaviorModule | `AIUpdateInterface` | REUSE_NATIVE | `AIUpdateInterface` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `RiderChangeContain` | INDEPENDENT_ADD | `RiderChangeContain` | RiderChangeContain + rider-only OCLSpecialPower is proven equivalent to stock DeployStyleAIUpdate + WeaponSet Conditions = DEPLOYED for pack/unpack and fire-only-when-deployed. CommandSet swap and SET_SLUGGISH-while-deployed are not. | `` |
| BehaviorModule | `OCLSpecialPower` | INDEPENDENT_ADD | `OCLSpecialPower` | RiderChangeContain + rider-only OCLSpecialPower is proven equivalent to stock DeployStyleAIUpdate + WeaponSet Conditions = DEPLOYED for pack/unpack and fire-only-when-deployed. CommandSet swap and SET_SLUGGISH-while-deployed are not. | `` |
| BehaviorModule | `EnemyNearUpdate` | INDEPENDENT_ADD | `EnemyNearUpdate` | Module class is kept on the unique Object; SPECTER core is not patched. | `` |
| BehaviorModule | `StealthDetectorUpdate` | REUSE_NATIVE | `StealthDetectorUpdate` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `TransitionDamageFX` | REUSE_NATIVE | `TransitionDamageFX` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `SlowDeathBehavior` | REUSE_NATIVE | `SlowDeathBehavior` | Stock SAGE module; keep on the unique Object. | `` |
| BehaviorModule | `FireWeaponUpdate` | INDEPENDENT_ADD | `FireWeaponUpdate` | Module class is kept on the unique Object; SPECTER core is not patched. | `` |
| CommandButton | `Command_ConstructChinaHQ11` | IMPORT_UNIQUE | `Command_ConstructChinaHQ11` | Name is free in SPECTER FINAL; unique-path import. | `loose:/tmp/v25_extract/Generals Silent Death V25/Data/INI/CommandButton.ini` |
| Object | `ChinaHQ11` | CYCLE | `ChinaHQ11` | Cyclic reference; node already visited. | `` |
| MappedImage | `CHHQ11TB` | CYCLE | `CHHQ11TB` | Cyclic reference; node already visited. | `` |
| ArtFile | `CHHQ11TB` | CYCLE | `CHHQ11TB` | Cyclic reference; node already visited. | `` |
| CommandSet | `SD25_ChinaHQ11CommandSet` | INDEPENDENT_ADD | `SD25_ChinaHQ11CommandSet` | One unique CommandSet with stock Command_Deploy + Command_Stop. CWC packed/deployed sets are not imported. | `stage4-independent` |

## ART recoveries (exact stem; no similar-name substitute)

- `MappedImage:CHHQ11TB` found_in=`None`
  - `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga`
- `ArtFile:CHHQ11TB` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHHQ11TB.tga`
  - container=`zip` file=`CHHQ11TB.tga` source_big=`None` inner=`None`
- `ArtFile:HQ11` found_in=`zip`
  - `Generals Silent Death V25/Art/W3D/HQ11.W3D`
  - container=`zip` file=`HQ11.W3D` source_big=`None` inner=`None`
  - W3D textures: ['SDNSM04.DDS', 'GLASS1.TGA', 'CHHQ11B.DDS', 'CHHQ11N.DDS', 'CHHQ11G.DDS', 'CHHQ11F.DDS', 'CHHQ11T.DDS', 'CHHQ11R.DDS']
  - W3D anims (inside model, not separate files): ['HQ11.WHEEL08', 'HQ11.WHEEL07', 'HQ11.WHEEL06', 'HQ11.WHEEL05', 'HQ11.WHEEL04', 'HQ11.WHEEL03', 'HQ11.WHEEL02', 'HQ11.WHEEL01', 'HQ11.VEHICLE_X_', 'HQ11.VEHICLE_X5', 'HQ11.VEHICLE_X3', 'HQ11.VEHICLE_X2', 'HQ11.VEHICLE_X1', 'HQ11.VEHICLE_X0', 'HQ11.VEHICLE_R4', 'HQ11.VEHICLE_R3', 'HQ11.VEHICLE_R2', 'HQ11.VEHICLE_R1', 'HQ11.VEHICLE_HA', 'HQ11.VEHICLE_H3', 'HQ11.VEHICLE_H2', 'HQ11.VEHICLE_H1', 'HQ11.VEHICLE_H0', 'HQ11.VEHICLE_GU', 'HQ11.VEHICLE_EX', 'HQ11.VEHICLE_E8', 'HQ11.VEHICLE_E7', 'HQ11.VEHICLE_E6', 'HQ11.VEHICLE_E5', 'HQ11.VEHICLE_E4', 'HQ11.VEHICLE_E3', 'HQ11.VEHICLE_E2', 'HQ11.VEHICLE_E1', 'HQ11.VEHICLE_E0', 'HQ11.VEHICLE_BO', 'HQ11.VEHICLE_B3', 'HQ11.VEHICLE_B2', 'HQ11.VEHICLE_B0', 'HQ11.VEHICLE_AN', 'HQ11.VEHICLE_A0']
- `ArtFile:SDNSM04.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/SDNSM04.dds`
  - container=`zip` file=`SDNSM04.dds` source_big=`None` inner=`None`
- `ArtFile:GLASS1.TGA` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/Glass1.tga`
  - container=`zip` file=`Glass1.tga` source_big=`None` inner=`None`
- `ArtFile:CHHQ11B.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHHQ11B.dds`
  - container=`zip` file=`CHHQ11B.dds` source_big=`None` inner=`None`
- `ArtFile:CHHQ11N.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHHQ11N.dds`
  - container=`zip` file=`CHHQ11N.dds` source_big=`None` inner=`None`
- `ArtFile:CHHQ11G.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHHQ11G.dds`
  - container=`zip` file=`CHHQ11G.dds` source_big=`None` inner=`None`
- `ArtFile:CHHQ11F.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHHQ11F.dds`
  - container=`zip` file=`CHHQ11F.dds` source_big=`None` inner=`None`
- `ArtFile:CHHQ11T.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHHQ11T.dds`
  - container=`zip` file=`CHHQ11T.dds` source_big=`None` inner=`None`
- `ArtFile:CHHQ11R.DDS` found_in=`zip`
  - `Generals Silent Death V25/Art/Textures/CHHQ11R.dds`
  - container=`zip` file=`CHHQ11R.dds` source_big=`None` inner=`None`
- `ArtFile:HQ11.HQ11` found_in=`zip`
  - `Generals Silent Death V25/Art/W3D/HQ11.W3D`
  - container=`zip` file=`HQ11.W3D` source_big=`None` inner=`None`
  - W3D textures: ['SDNSM04.DDS', 'GLASS1.TGA', 'CHHQ11B.DDS', 'CHHQ11N.DDS', 'CHHQ11G.DDS', 'CHHQ11F.DDS', 'CHHQ11T.DDS', 'CHHQ11R.DDS']
  - W3D anims (inside model, not separate files): ['HQ11.WHEEL08', 'HQ11.WHEEL07', 'HQ11.WHEEL06', 'HQ11.WHEEL05', 'HQ11.WHEEL04', 'HQ11.WHEEL03', 'HQ11.WHEEL02', 'HQ11.WHEEL01', 'HQ11.VEHICLE_X_', 'HQ11.VEHICLE_X5', 'HQ11.VEHICLE_X3', 'HQ11.VEHICLE_X2', 'HQ11.VEHICLE_X1', 'HQ11.VEHICLE_X0', 'HQ11.VEHICLE_R4', 'HQ11.VEHICLE_R3', 'HQ11.VEHICLE_R2', 'HQ11.VEHICLE_R1', 'HQ11.VEHICLE_HA', 'HQ11.VEHICLE_H3', 'HQ11.VEHICLE_H2', 'HQ11.VEHICLE_H1', 'HQ11.VEHICLE_H0', 'HQ11.VEHICLE_GU', 'HQ11.VEHICLE_EX', 'HQ11.VEHICLE_E8', 'HQ11.VEHICLE_E7', 'HQ11.VEHICLE_E6', 'HQ11.VEHICLE_E5', 'HQ11.VEHICLE_E4', 'HQ11.VEHICLE_E3', 'HQ11.VEHICLE_E2', 'HQ11.VEHICLE_E1', 'HQ11.VEHICLE_E0', 'HQ11.VEHICLE_BO', 'HQ11.VEHICLE_B3', 'HQ11.VEHICLE_B2', 'HQ11.VEHICLE_B0', 'HQ11.VEHICLE_AN', 'HQ11.VEHICLE_A0']
- `ArtFile:EXTireTrack.tga` found_in=`nested_big`
  - `Generals Silent Death V25/WYS/Textures.big::Art\Textures\extiretrack.dds`
  - container=`nested_big` file=`extiretrack.dds` source_big=`Generals Silent Death V25/WYS/Textures.big` inner=`Art\Textures\extiretrack.dds`
- `ArtFile:HQ11RD` found_in=`zip`
  - `Generals Silent Death V25/Art/W3D/HQ11RD.W3D`
  - container=`zip` file=`HQ11RD.W3D` source_big=`None` inner=`None`
  - W3D textures: ['CHHQ11T.DDS']
  - W3D anims (inside model, not separate files): ['HQ11RD.VEHICLE_RO', 'HQ11RD.VEHICLE_R5', 'HQ11RD.VEHICLE_A1', 'HQ11RD.VEHICLE_B4']
- `ArtFile:HQ11RD.HQ11RD` found_in=`zip`
  - `Generals Silent Death V25/Art/W3D/HQ11RD.W3D`
  - container=`zip` file=`HQ11RD.W3D` source_big=`None` inner=`None`
  - W3D textures: ['CHHQ11T.DDS']
  - W3D anims (inside model, not separate files): ['HQ11RD.VEHICLE_RO', 'HQ11RD.VEHICLE_R5', 'HQ11RD.VEHICLE_A1', 'HQ11RD.VEHICLE_B4']

## Planned rewrites (not applied)

- `HumveeArmor` → `SD25_HumveeArmor`
- `TruckDamageFX` → `SD25_TruckDamageFX`
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

## Stage 4 — independent DATA rebuild

SPECTER public DamageFX.ini / Crate.ini / FXList.ini / SpecialPower.ini are never written.
CWC.exe is not used. Previews are not imported into the game.

### Unique DATA files (future apply only)

- `Data\INI\Object\SilentDeath\China\ChinaHQ11.ini`
- `Data\INI\DamageFX_SilentDeath.ini`
- `Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini`

### Public INI leak check

**PASS — no public SPECTER INI in the unique-path list.**

### Independent clones

#### `DamageFX` `TruckDamageFX` → `SD25_TruckDamageFX`

- Unique path: `Data\INI\DamageFX_SilentDeath.ini`

```
; Independent unique-path clone of DamageFX TruckDamageFX. Preview only; SPECTER public INI is not written.
DamageFX SD25_TruckDamageFX

  ; this means, "when doing damagefx of the same type, wait at least this many milliseconds
  ; between repeated fx." this is used to prevent overwhelming the system with fx when
  ; groups of things are attacking a single object. example: 8 rangers attacking a tank
  ; would produce a ton of particle effects if we did one for every ranger, every time they
  ; attack, but with this in place, we only do (at most) one every 500 msec.
  ThrottleTime = DEFAULT 100


  MajorFX           = DEFAULT           FX_DamageTankStruck
  VeterancyMajorFX  = HEROIC DEFAULT    FX_HeroicDamageTankStruck
  MinorFX           = DEFAULT           FX_DamageTankStruck
  VeterancyMinorFX  = HEROIC DEFAULT    FX_HeroicDamageTankStruck

  MajorFX           = SMALL_ARMS        FX_DamageSmallTankStruckSmallArms
  VeterancyMajorFX  = HEROIC SMALL_ARMS FX_HeroicDamageTankStruckSmallArms
  MinorFX           = SMALL_ARMS        FX_DamageSmallTankStruckSmallArms
  VeterancyMinorFX  = HEROIC SMALL_ARMS FX_HeroicDamageTankStruckSmallArms

  MajorFX           = COMANCHE_VULCAN       
```


### DeployStyleAIUpdate compatibility proof

- Use DeployStyleAIUpdate: **True**
- Use WeaponSet Conditions = DEPLOYED: **True**
- PackTime/UnpackTime (ms): `2000`
- Summary: RiderChangeContain + rider-only OCLSpecialPower is proven equivalent to stock DeployStyleAIUpdate + WeaponSet Conditions = DEPLOYED for pack/unpack and fire-only-when-deployed. CommandSet swap and SET_SLUGGISH-while-deployed are not.

Proven:

- Two rider slots encode packed vs deployed weapon flags.
- Draw RIDER1 = packed, RIDER2 = deployed.
- Packed uses SET_NORMAL; deployed uses SET_SLUGGISH (CWC-only switch).
- WeaponSet WEAPON_RIDER1 PRIMARY None / WEAPON_RIDER2 PRIMARY HQ11MissileWeapon maps 1:1 onto stock Conditions = None vs DEPLOYED.
- HQ11.HQ11 ONCE_BACKWARDS (packed) vs ONCE with MISSILE_C (deployed) stays on the same W3D.
- OCL_CWCruSpecialAbilityFakeRider_Inf_Stand: OCL only injects the fake rider inside the vehicle
- SpecialAbilityCWCruFakeRider_Inf_Stand uses SPECIAL_CIA_INTELLIGENCE; it must not be imported (would hijack CIA intel).
- OCL_CWCruSpecialAbilityFakeRider_Inf_Prone: OCL only injects the fake rider inside the vehicle
- SpecialAbilityCWCruFakeRider_Inf_Prone uses SPECIAL_CIA_INTELLIGENCE; it must not be imported (would hijack CIA intel).
- OCLSpecialPower exists only to inject fake riders; stock Command_Deploy replaces it.
- V25 itself already authors DeployStyleAIUpdate (e.g. SDSR5) in the same vehicle INI.

Limitations (exact CWC behavior not available on stock Generals.exe):

- **Runtime CommandSet swap (packed vs deployed button labels)**
  - V25: RiderChangeContain overrides CommandSet per rider (CWCruS300CommandSet vs DeployedCommandSet).
  - Stock: DeployStyleAIUpdate does not swap CommandSet. One unique CommandSet with Command_Deploy + Command_Stop.
  - Kept: State swap (pack/unpack) stays. Separate SHIFANG/BUSHU labels collapse to one Deploy toggle.
- **SET_SLUGGISH locomotor while deployed**
  - V25: Rider2 binds SET_SLUGGISH CWCruS300DeployedLocomotor so the TEL can crawl while unpacked.
  - Stock: DeployStyleAIUpdate does not switch LocomotorSet. The unit packs, then moves on SET_NORMAL.
  - Kept: Settled firing posture is kept. Slow-move-while-deployed is not available on stock Generals.exe.
- **Pack / unpack duration**
  - V25: CWC rider swap timing is not an INI PackTime; ScuttleDelay=1500 is TOPPLED scuttle, not pack.
  - Stock: PackTime = UnpackTime = 2000 copied from V25 SDSR5 DeployStyleAIUpdate in the same ChinaVehicle.ini.
  - Kept: Pack/unpack exists. Exact CWC millisecond timing is not claimed.

Independent module preview (not written):

```
; Independent unique-path preview for ChinaHQ11 DATA. Not written to disk.
; SPECTER public INI / CWC.exe are not used.

  WeaponSet
    Conditions = None
    Weapon = PRIMARY None
  End
  WeaponSet
    Conditions = DEPLOYED
    Weapon = PRIMARY HQ11MissileWeapon
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst = PRIMARY BALLISTIC_MISSILE AIRCRAFT
  End
  CommandSet = SD25_ChinaHQ11CommandSet

  Behavior = DeployStyleAIUpdate ModuleTag_Deploy
    AutoAcquireEnemiesWhenIdle = Yes Stealthed
    PackTime = 2000
    UnpackTime = 2000
    TurretsFunctionOnlyWhenDeployed = Yes
    TurretsMustCenterBeforePacking = Yes
    ResetTurretBeforePacking = Yes
  End
  Locomotor = SET_NORMAL CWCruS300Locomotor
  ; SET_SLUGGISH CWCruS300DeployedLocomotor is NOT bound: stock DeployStyle cannot switch locomotor sets.

  ; Removed (CWC.exe / CIA hijack — capability kept via DeployStyle + Command_Deploy):
  ;   RiderChangeContain, OCLSpecialPower x2, fake-rider Objects, SpecialAbilityCWCruFakeRider_*

```


## Tested vs analysis-only

- **Tested:** unit tests (`tests/test_data_rebuild.py`, existing resolver/ART tests).
- **Not tested:** Generals.exe, in-game spawn, packing SPECTER BIGs, apply.

