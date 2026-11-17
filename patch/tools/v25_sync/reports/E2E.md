# SS1 compatibility engine — End-to-End dry-run

- Generated: 2026-11-11 16:48 Asia/Tehran
- SPECTER BIGs modified: **False**
- Equipment imported: **False**
- Loose INI written: **False**
- Generals.exe run: **False**

## Counts

- Samples: **31**
- Pass (raw bytes): **154**
- Repairable (known syntax rewrite): **160**
- Fail: **108**
- Blocked: **9**
- Catalog-ready rechecked from bytes: **400**
- Catalog false-ready (bytes disagree): **97**

## Role samples

- **tank** `ChinaTankOverlord` → `Data\INI\Object\SilentDeath\China\ChinaTankOverlord.ini` **blocked** deps=170 catalog=needs_rebuild reasons=cwc:OCLSpecialPower, cwc_rebuild_required caps=OCLSpecialPower (CWC), OverlordContain
- **tank** `ChinaTankBattleMaster` → `Data\INI\Object\SilentDeath\China\SD25_ChinaTankBattleMaster.ini` **fail** deps=135 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, fxlist_missing_column0_end, missing_parse_ref caps=OverlordContain
- **tank** `AmericaTankCrusader` → `Data\INI\Object\SilentDeath\America\SD25_AmericaTankCrusader.ini` **blocked** deps=108 catalog=needs_rebuild reasons=cwc:OCLSpecialPower, cwc_rebuild_required caps=OCLSpecialPower (CWC), OverlordContain
- **tank** `ChinaTankGattling` → `Data\INI\Object\SilentDeath\China\SD25_ChinaTankGattling.ini` **fail** deps=136 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, fxlist_missing_column0_end, missing_parse_ref caps=-
- **tank** `ChinaCSSA1` → `Data\INI\Object\SilentDeath\China\ChinaCSSA1.ini` **repairable** deps=46 catalog=unique_import_ready reasons=raw_bytes_need_syntax_normalize, fxlist_missing_column0_end caps=-
- **air_defense** `ChinaS400` → `Data\INI\Object\SilentDeath\China\ChinaS400.ini` **blocked** deps=57 catalog=needs_rebuild reasons=cwc:RiderChangeContain,OCLSpecialPower, cwc_rebuild_required caps=RiderChangeContain (CWC), OCLSpecialPower (CWC)
- **air_defense** `ChinaHQ9` → `Data\INI\Object\SilentDeath\China\ChinaHQ9.ini` **blocked** deps=63 catalog=needs_rebuild reasons=cwc:RiderChangeContain,OCLSpecialPower, cwc_rebuild_required caps=RiderChangeContain (CWC), OCLSpecialPower (CWC)
- **air_defense** `AmericaPatriotBattery` → `Data\INI\Object\SilentDeath\America\SD25_AmericaPatriotBattery.ini` **repairable** deps=40 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, raw_bytes_need_syntax_normalize, fxlist_missing_column0_end caps=AssistedTargetingUpdate
- **air_defense** `AmericaThaad` → `Data\INI\Object\SilentDeath\America\AmericaThaad.ini` **blocked** deps=173 catalog=needs_rebuild reasons=cwc:RiderChangeContain,OCLSpecialPower, cwc_rebuild_required caps=RiderChangeContain (CWC), OCLSpecialPower (CWC)
- **air_defense** `ChinaHQ11` → `Data\INI\Object\SilentDeath\China\ChinaHQ11.ini` **blocked** deps=55 catalog=needs_rebuild reasons=cwc:RiderChangeContain,OCLSpecialPower, cwc_rebuild_required caps=RiderChangeContain (CWC), OCLSpecialPower (CWC)
- **air_defense** `AmericaIronDome` → `Data\INI\Object\SilentDeath\America\AmericaIronDome.ini` **repairable** deps=25 catalog=unique_import_ready reasons=raw_bytes_need_syntax_normalize, fxlist_missing_column0_end caps=AssistedTargetingUpdate
- **structure** `ChinaWarFactory` → `Data\INI\Object\SilentDeath\China\SD25_ChinaWarFactory.ini` **fail** deps=84 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref caps=-
- **structure** `ChinaCommandCenter` → `Data\INI\Object\SilentDeath\China\SD25_ChinaCommandCenter.ini` **blocked** deps=203 catalog=needs_rebuild reasons=cwc:OCLSpecialPower, cwc_rebuild_required caps=OCLSpecialPower (CWC), RadarUpdate
- **structure** `AmericaWarFactory` → `Data\INI\Object\SilentDeath\America\SD25_AmericaWarFactory.ini` **fail** deps=56 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref caps=-
- **structure** `ChinaBarracks` → `Data\INI\Object\SilentDeath\China\SD25_ChinaBarracks.ini` **fail** deps=33 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref caps=-
- **structure** `ChinaAirfield` → `Data\INI\Object\SilentDeath\China\SD25_ChinaAirfield.ini` **fail** deps=88 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref caps=-
- **missile** `TomahawkMissile` → `Data\INI\Object\SilentDeath\Unmapped\SD25_TomahawkMissile.ini` **pass** deps=9 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, rewrite_planned caps=MissileAIUpdate
- **missile** `ScudStormMissile` → `Data\INI\Object\SilentDeath\Unmapped\SD25_ScudStormMissile.ini` **pass** deps=22 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, rewrite_planned caps=MissileAIUpdate, FireWeaponWhenDeadBehavior
- **missile** `AuroraBomb` → `Data\INI\Object\SilentDeath\America\AuroraBomb.ini` **pass** deps=3 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, rewrite_planned caps=MissileAIUpdate
- **missile** `PatriotMissile` → `Data\INI\Object\SilentDeath\Unmapped\PatriotMissile.ini` **pass** deps=7 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, rewrite_planned caps=MissileAIUpdate
- **missile** `CWCusUH60MinigunMissile` → `Data\INI\Object\SilentDeath\America\CWCusUH60MinigunMissile.ini` **pass** deps=2 catalog=unique_import_ready reasons=- caps=MissileAIUpdate
- **aircraft** `AmericaJetRaptor` → `Data\INI\Object\SilentDeath\America\SD25_AmericaJetRaptor.ini` **fail** deps=108 catalog=needs_fix reasons=missing_parse_ref caps=JetAIUpdate
- **aircraft** `AmericaJetAurora` → `Data\INI\Object\SilentDeath\America\SD25_AmericaJetAurora.ini` **fail** deps=157 catalog=needs_fix reasons=missing_parse_ref caps=JetAIUpdate
- **aircraft** `AmericaVehicleComanche` → `Data\INI\Object\SilentDeath\America\SD25_AmericaVehicleComanche.ini` **fail** deps=119 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, fxlist_missing_column0_end, missing_parse_ref caps=-
- **aircraft** `AirF_asdAmericaVehicleComancheasd` → `Data\INI\Object\SilentDeath\Korea\AirF_asdAmericaVehicleComancheasd.ini` **fail** deps=102 catalog=unique_import_ready reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready caps=-
- **aircraft** `AirF_AmericaVehicleChinook` → `Data\INI\Object\SilentDeath\Korea\AirF_AmericaVehicleChinook.ini` **fail** deps=80 catalog=unique_import_ready reasons=preflight_bytes, missing_parse_ref, catalog_false_ready caps=-
- **mobile** `AmericaVehicleHumvee` → `Data\INI\Object\SilentDeath\America\SD25_AmericaVehicleHumvee.ini` **blocked** deps=51 catalog=needs_rebuild reasons=cwc:OCLSpecialPower, cwc_rebuild_required caps=OCLSpecialPower (CWC)
- **mobile** `ChinaVehicleTroopCrawler` → `Data\INI\Object\SilentDeath\China\ChinaVehicleTroopCrawler.ini` **blocked** deps=162 catalog=needs_rebuild reasons=cwc:OCLSpecialPower, cwc_rebuild_required caps=OCLSpecialPower (CWC)
- **mobile** `AmericaVehicleDozer` → `Data\INI\Object\SilentDeath\America\SD25_AmericaVehicleDozer.ini` **fail** deps=43 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref caps=-
- **mobile** `ChinaVehicleSupplyTruck` → `Data\INI\Object\SilentDeath\China\SD25_ChinaVehicleSupplyTruck.ini` **repairable** deps=29 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, raw_bytes_need_syntax_normalize, fxlist_missing_column0_end caps=-
- **mobile** `AmericaVehicleChinook` → `Data\INI\Object\SilentDeath\America\SD25_AmericaVehicleChinook.ini` **fail** deps=55 catalog=rename_or_reuse reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref caps=-

## Failures

- `ChinaTankBattleMaster` role=tank reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, fxlist_missing_column0_end, missing_parse_ref missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z
- `ChinaTankGattling` role=tank reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, fxlist_missing_column0_end, missing_parse_ref missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z
- `ChinaWarFactory` role=structure reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref missing=- preflight=missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z; missing_parse_ref:Object:ChinaFK2000
- `AmericaWarFactory` role=structure reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref missing=- preflight=missing_parse_ref:Object:AmericaCh53; missing_parse_ref:Object:AmericaVehicleV22; missing_parse_ref:Object:AmericaSupplyCar; missing_parse_ref:Object:UH60
- `ChinaBarracks` role=structure reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref missing=- preflight=missing_parse_ref:Object:ChinaInfHeavyAssault; missing_parse_ref:Object:ChinaInfEngineer; missing_parse_ref:Object:ChinaInfMedic; missing_parse_ref:Object:ChinaSuperArmy
- `ChinaAirfield` role=structure reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref missing=- preflight=missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z; missing_parse_ref:Object:ChinaFK2000
- `AmericaJetRaptor` role=aircraft reasons=missing_parse_ref missing=Object:AircraftBomSubduerBuilding preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:AmericaCh53; missing_parse_ref:Object:AmericaVehicleV22; missing_parse_ref:Object:AmericaSupplyCar
- `AmericaJetAurora` role=aircraft reasons=missing_parse_ref missing=Object:AircraftBomSubduerBuilding preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:AmericaCh53; missing_parse_ref:Object:AmericaVehicleV22; missing_parse_ref:Object:AmericaSupplyCar
- `AmericaVehicleComanche` role=aircraft reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, fxlist_missing_column0_end, missing_parse_ref missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:AmericaCh53; missing_parse_ref:Object:AmericaVehicleV22; missing_parse_ref:Object:AmericaSupplyCar
- `AirF_asdAmericaVehicleComancheasd` role=aircraft reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:EGYPTMI17; missing_parse_ref:Object:EgyptSupplyCar; missing_parse_ref:Object:EGYPTCommando
- `AirF_AmericaVehicleChinook` role=aircraft reasons=preflight_bytes, missing_parse_ref, catalog_false_ready missing=- preflight=missing_parse_ref:Object:EGYPTMI17; missing_parse_ref:Object:EgyptSupplyCar; missing_parse_ref:Object:EGYPTCommando; missing_parse_ref:Object:Egypt9S32
- `AmericaVehicleDozer` role=mobile reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref missing=- preflight=missing_parse_ref:Object:ICBMPlathform; missing_parse_ref:Object:AmericaWarFactory2; missing_parse_ref:Object:AmericaWarFactoryIII; missing_parse_ref:Object:NewAmericaAirfield
- `AmericaVehicleChinook` role=mobile reasons=name_in_ss1, not_ready_until_rewrite_plan, preflight_bytes, missing_parse_ref missing=- preflight=missing_parse_ref:Object:AmericaCh53; missing_parse_ref:Object:AmericaVehicleV22; missing_parse_ref:Object:AmericaSupplyCar; missing_parse_ref:Object:UH60
- `07BZCG` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z
- `AH6` role=aircraft reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:AmericaCh53; missing_parse_ref:Object:AmericaVehicleV22; missing_parse_ref:Object:AmericaSupplyCar
- `AirF_AmericaTankAvengerawdaswd` role=tank reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:EGYPTMI17; missing_parse_ref:Object:EgyptSupplyCar; missing_parse_ref:Object:EGYPTCommando
- `AirF_awdAmericaVehicleMedicwadaw` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, locomotor_uncommented_tail, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; locomotor_uncommented_tail:Data\INI\Locomotor_SilentDeath.ini; missing_parse_ref:Object:SD25_OCL_AmericanBattleDrone; missing_parse_ref:Object:SD25_OCL_AmericanHellfireDrone
- `AlgeriaBMP2` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:SpecialPower:SUPERWEAPON_LSFSmokeGrenade
- `Boss_Airfield` role=structure reasons=preflight_bytes, missing_parse_ref, catalog_false_ready missing=- preflight=missing_parse_ref:Object:SwedenHKP14; missing_parse_ref:Object:SwedenMANTruck; missing_parse_ref:Object:SwedenJAS39C; missing_parse_ref:Object:SwedenJAS39D
- `SouthAfricaWarFactory` role=structure reasons=preflight_bytes, missing_parse_ref, catalog_false_ready missing=- preflight=missing_parse_ref:Object:LSFHaoJiao; missing_parse_ref:Object:LSFG6R; missing_parse_ref:Object:LSFMiHuan; missing_parse_ref:Object:LSFSHANMAO
- `Y59DeadHull` role=mobile reasons=preflight_bytes, missing_parse_ref, catalog_false_ready missing=- preflight=missing_parse_ref:SpecialPower:SUPERWEAPON_LSFSmokeGrenade; missing_parse_ref:Upgrade:Upgrade_AmericaAircraftCarrierShip
- `8X8ZCG` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z
- `AdmiralGorshkov` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:RussiaKA27AntiSub; missing_parse_ref:Object:CamCopterUAV
- `AirF_AmericaTankMicrowavedfszdf` role=tank reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:EGYPTMI17; missing_parse_ref:Object:EgyptSupplyCar; missing_parse_ref:Object:EGYPTCommando
- `CG_M60A3` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:IranVehicleChinook; missing_parse_ref:Object:IranHelixMi8; missing_parse_ref:Object:KACHE
- `TaiWanCM32` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:SpecialPower:SUPERWEAPON_LSFSmokeGrenade
- `92BZCG` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z
- `Admiralkuznetsov` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Upgrade:Upgrade_ChinaDozerUpgradeDefault
- `AirCraftAH1` role=aircraft reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Upgrade:Upgrade_AmericaAircraftCarrierShip
- `AirF_AmericaVehicleSentryDronedwdas` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:EGYPTMI17; missing_parse_ref:Object:EgyptSupplyCar; missing_parse_ref:Object:EGYPTCommando
- `CGGLAVehicleTechnicalChassisOne` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:IranVehicleChinook; missing_parse_ref:Object:IranHelixMi8; missing_parse_ref:Object:KACHE
- `ChinaSupplyDropZone` role=structure reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:Tank_ChinaVehicleSupplyTruck; missing_parse_ref:Object:GermanyRMMV; missing_parse_ref:Object:GermanyZetros
- `ItalyA129` role=aircraft reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Upgrade:Upgrade_AmericaAircraftCarrierShip
- `TaiWanCommandCenter` role=structure reasons=preflight_bytes, missing_parse_ref, catalog_false_ready missing=- preflight=missing_parse_ref:Object:TaiWanM998; missing_parse_ref:Object:TaiWanM60A3; missing_parse_ref:Object:TaiWanM1046; missing_parse_ref:Object:TaiWanM113
- `UkraineArcher` role=mobile reasons=preflight_bytes, object_missing_end, fxlist_missing_column0_end, locomotor_uncommented_tail, catalog_false_ready missing=- preflight=object_missing_end:Data\INI\Object\SilentDeath\Ukraine\UkraineArcher.ini; fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; locomotor_uncommented_tail:Data\INI\Locomotor_SilentDeath.ini
- `Cannon05CG` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:ChinaVehicleHelix; missing_parse_ref:Object:ChinaZ8; missing_parse_ref:Object:ChinaVehicleZ9Z
- `Chem_FakeGLAArmsDealer` role=structure reasons=preflight_bytes, missing_parse_ref, catalog_false_ready missing=- preflight=missing_parse_ref:Object:JapanCH47; missing_parse_ref:Object:JapanV22; missing_parse_ref:Object:JapanOH6D; missing_parse_ref:Object:ToyotaSupplyTruck
- `AdmiralkuznetsovAP` role=structure reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:RussiaSU33; missing_parse_ref:Object:RussianMig29K; missing_parse_ref:Object:RussiaKA27AntiSub
- `AirF_AmericaVehicleTomahawksss` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:EGYPTMI17; missing_parse_ref:Object:EgyptSupplyCar; missing_parse_ref:Object:EGYPTCommando
- `CINE_CarLuxury03` role=mobile reasons=preflight_bytes, fxlist_missing_column0_end, missing_parse_ref, catalog_false_ready missing=- preflight=fxlist_missing_column0_end:Data\INI\FXList_SilentDeath.ini; missing_parse_ref:Object:IranVehicleChinook; missing_parse_ref:Object:IranHelixMi8; missing_parse_ref:Object:KACHE

## V25 syntax audit (whole archive)

- counts: `{'fxlist_missing_column0_end': 568, 'locomotor_uncommented_tail': 21, 'object_missing_end': 37}`
- `fxlist_missing_column0_end`: FXList:FX_TankDeathRubble1, FXList:FX_TankDamageTransition, FXList:FX_TankDeathRubble2, FXList:WeaponFX_ToxinShellWeapon, FXList:FX_CarOverlappedByCrusher, FXList:FX_DieByFireUSA, FXList:WeaponFX_CWCgenLargeMissileIgnition, FXList:WeaponFX_CWCgenSmallMissileIgnition
- `locomotor_uncommented_tail`: Locomotor:HumveeLocomotor, Locomotor:M1151Locomotor, Locomotor:M1046Locomotor, Locomotor:CWCruUralLocomotor, Locomotor:CWCruUralLocomotor_Convoy, Locomotor:CWCruUralLocomotor_CWCusMission02, Locomotor:CWCusM939Locomotor, Locomotor:CWCusM939Locomotor_Convoy
- `object_missing_end`: Object:AirF_AmericaJetSpectreGunship1, Object:AirF_AmericaJetSpectreGunship2, Object:AirF_AmericaJetSpectreGunship3, Object:AirF_AmericaVehicleSpyDrone, Object:AmericaJetSpectreGunship, Object:AmericaVehicleSpyDrone, Object:UsaM109Gun, Object:Boss_JetSpectreGunship

## Engine gaps before grouped transfer

- 97 catalog-ready objects failed byte preflight — catalog must not be the pack gate.
- V25 source INI contains Stage 5 syntax classes (FXList End / Object orphan / Locomotor tail / dupes); bulk copy of raw V25 bodies is unsafe: {'fxlist_missing_column0_end': 568, 'locomotor_uncommented_tail': 21, 'object_missing_end': 37}
- Generals.exe is not run; pass is static INI/VFS only.
- ART/W3D/texture bytes are inventoried as stems, not opened or packed.
- Unproven SS1 root extras (Armor_/Locomotor_/FXList_/ParticleSystem_/SoundEffects_) remain likely, not proven.
- Bulk CommandSet factory-slot overlay is not planned (Stage 5 did PLAWarFactory slots 4/7 only).
- Audio wav recovery from V25 volumes is not part of this dry-run.
- Catalog CommandButton existence is now walked from CommandSet; factory Object= slots stay unwalked on purpose.
- Shared-name rewrite is planned in memory; it is not applied to a BIG.
- Do not start grouped transfer until false_ready is 0 on the byte recheck and unproven root kinds are proven or isolated.

## Next stage suggestion

Do not start grouped equipment transfer. Next: fold FXList End + Locomotor semicolon normalize into the unique-path rewriter, keep catalog from marking ready until byte preflight passes, prove or isolate unproven root INI kinds, then pack one role-group as an experimental DATA copy only.

