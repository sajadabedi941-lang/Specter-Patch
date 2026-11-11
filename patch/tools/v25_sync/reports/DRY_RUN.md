# Dry run — all V25 equipment (no SPECTER writes)

- Generated: 2026-11-11 13:03 Asia/Tehran
- Objects scanned: **6207**
- Game BIGs modified: **False**
- Generals.exe run: **False**
- Collisions: `{'unique_v25': 5374, 'collision_rename': 628, 'shared_identical': 205}`
- Incomplete trees: **3592**
- Later-apply impact rows: **628** (rename-only; originals kept)

## Validation checklist

- missing_refs_scanned: True
- name_collisions_scanned: True
- incomplete_deps_scanned: True
- object_weapon_ocl_fx_scanned: True
- output_big_not_written: True
- before_after_diff: no game files changed; diff is empty by design
- specter_behavior_impact_if_applied_later: Colliding names would be renamed to SD25_* so original SPECTER defs stay. Public CommandSet.ini / CommandButton.ini / Weapon.ini / Armor.ini are blocked. Future apply must use unique-path INI only.

## Missing-ref kinds

- MappedImage: 64794
- FXList: 8811
- Object: 7593
- ObjectCreationList: 3868
- CrateTemplate: 1608
- AudioEvent: 1372
- ParticleSystem: 473
- CommandSet: 17
- CommandButton: 11

## Sample incomplete objects (first 40)

- `00qsnOffice01`: FXList:StructureDamageFXNoShake
- `00qsnOffice02`: FXList:StructureDamageFXNoShake
- `00qsnOffice03`: FXList:StructureDamageFXNoShake
- `00qsnOffice04`: FXList:StructureDamageFXNoShake
- `00qsnOffice05`: FXList:StructureDamageFXNoShake
- `00qsnOffice06`: FXList:StructureDamageFXNoShake
- `00qsnOffice07`: FXList:StructureDamageFXNoShake
- `00qsnOffice08`: FXList:StructureDamageFXNoShake
- `00qsnOffice09`: FXList:StructureDamageFXNoShake
- `00qsnOffice10`: FXList:StructureDamageFXNoShake
- `00qsnOffice11`: FXList:StructureDamageFXNoShake
- `00qsnOffice12`: FXList:StructureDamageFXNoShake
- `07BZCG`: FXList:TankDamageFX, FXList:StructureDamageFXNoShake, FXList:TruckDamageFX, FXList:InfantryDamageFX, FXList:SmallTankDamageFX
- `150mmchina`: FXList:TankDamageFX
- `150mmegypt`: FXList:TankDamageFX
- `150mmIsrael`: FXList:TankDamageFX
- `150mmusa`: FXList:TankDamageFX
- `30DXHull`: FXList:TankDamageFX
- `30N6EFLAPLID`: FXList:TankDamageFX
- `59N6ERadar`: FXList:StructureDamageFXNoShake
- `88BCG`: FXList:TankDamageFX, FXList:StructureDamageFXNoShake, FXList:TruckDamageFX, FXList:InfantryDamageFX, FXList:SmallTankDamageFX
- `8X8ZCG`: FXList:TankDamageFX, FXList:StructureDamageFXNoShake, FXList:TruckDamageFX, FXList:InfantryDamageFX, FXList:SmallTankDamageFX
- `92BZCG`: FXList:TankDamageFX, FXList:StructureDamageFXNoShake, FXList:TruckDamageFX, FXList:InfantryDamageFX, FXList:SmallTankDamageFX
- `AalgeriaFUCHS`: FXList:TruckDamageFX
- `ADAHull`: FXList:TankDamageFX
- `AdmiralGorshkov`: FXList:SmallTankDamageFX, FXList:TankDamageFX
- `Admiralkuznetsov`: FXList:StructureDamageFXNoShake
- `AdmiralkuznetsovAP`: Object:AircraftBomSubduerBuilding, FXList:DefaultDamageFX, FXList:StructureDamageFXNoShake
- `AFG_AmericaVehicleChinook`: FXList:StructureDamageFXNoShake, FXList:InfantryDamageFX, FXList:TruckDamageFX, FXList:SmallTankDamageFX, FXList:TankDamageFX
- `AGS17GrenadeLauncher`: FXList:StructureDamageFXNoShake
- `AGS30GrenadeLauncher`: FXList:StructureDamageFXNoShake
- `AH6`: FXList:StructureDamageFXNoShake, FXList:TruckDamageFX, Object:AircraftBomSubduerBuilding, Object:AircraftBomSubduer, FXList:TankDamageFX
- `AircraftCessna`: FXList:CrushableCarDamageFX
- `AircraftCropDuster`: FXList:CrushableCarDamageFX
- `AirF_adswAmericaJetRaptorawdwa`: FXList:StructureDamageFXNoShake, FXList:InfantryDamageFX, FXList:TruckDamageFX, FXList:SmallTankDamageFX, FXList:TankDamageFX, Object:AircraftBomSubduerBuilding, Object:AircraftBomSubduer, ObjectCreationList:OCL_TankDeathTrails
- `AirF_AmericaAirfield`: FXList:StructureDamageFXNoShake, FXList:InfantryDamageFX, FXList:TruckDamageFX, FXList:SmallTankDamageFX, FXList:TankDamageFX, Object:AircraftBomSubduerBuilding, Object:AircraftBomSubduer, ObjectCreationList:OCL_TankDeathTrails
- `AirF_AmericaBarracks`: FXList:InfantryDamageFX, Object:KDeathRider2, Object:KDeathRider3, FXList:StructureDamageFXNoShake, Object:KAntiTankDeathRider2, Object:KAntiTankDeathRider3, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive
- `AirF_AmericaCommandCenter`: FXList:TankDamageFX, FXList:StructureDamageFXNoShake, FXList:InfantryDamageFX, FXList:TruckDamageFX, ObjectCreationList:OCL_TankDeathTrails, Object:KDeathRider2, Object:KDeathRider3, Object:KAntiTankDeathRider2
- `AirF_AmericaFireBase`: FXList:StructureDamageFXNoShake
- `AirF_AmericaInfantryColonelBurton`: FXList:InfantryDamageFX, Object:KDeathRider2, Object:KDeathRider3, FXList:StructureDamageFXNoShake, Object:KAntiTankDeathRider2, Object:KAntiTankDeathRider3, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive

## Sample SPECTER-behavior notes if apply were enabled later

- `1000DollarCrate`: name collision with SPECTER Object; future apply must rename to SD25_1000DollarCrate and rewrite every ref. SPECTER original 1000DollarCrate stays.
- `100DollarCrate`: name collision with SPECTER Object; future apply must rename to SD25_100DollarCrate and rewrite every ref. SPECTER original 100DollarCrate stays.
- `100DollarCrateForBuildings`: name collision with SPECTER Object; future apply must rename to SD25_100DollarCrateForBuildings and rewrite every ref. SPECTER original 100DollarCrateForBuildings stays.
- `1500DollarCrate`: name collision with SPECTER Object; future apply must rename to SD25_1500DollarCrate and rewrite every ref. SPECTER original 1500DollarCrate stays.
- `200DollarCrate`: name collision with SPECTER Object; future apply must rename to SD25_200DollarCrate and rewrite every ref. SPECTER original 200DollarCrate stays.
- `2500DollarCrate`: name collision with SPECTER Object; future apply must rename to SD25_2500DollarCrate and rewrite every ref. SPECTER original 2500DollarCrate stays.
- `2FreeCrusadersCrate`: name collision with SPECTER Object; future apply must rename to SD25_2FreeCrusadersCrate and rewrite every ref. SPECTER original 2FreeCrusadersCrate stays.
- `AFG_AmericaVehicleChinook`: name collision with SPECTER Object; future apply must rename to SD25_AFG_AmericaVehicleChinook and rewrite every ref. SPECTER original AFG_AmericaVehicleChinook stays.
- `AirF_AmericaAirfield`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaAirfield and rewrite every ref. SPECTER original AirF_AmericaAirfield stays.
- `AirF_AmericaBarracks`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaBarracks and rewrite every ref. SPECTER original AirF_AmericaBarracks stays.
- `AirF_AmericaCommandCenter`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaCommandCenter and rewrite every ref. SPECTER original AirF_AmericaCommandCenter stays.
- `AirF_AmericaCrateParachute`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaCrateParachute and rewrite every ref. SPECTER original AirF_AmericaCrateParachute stays.
- `AirF_AmericaFireBase`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaFireBase and rewrite every ref. SPECTER original AirF_AmericaFireBase stays.
- `AirF_AmericaInfantryColonelBurton`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaInfantryColonelBurton and rewrite every ref. SPECTER original AirF_AmericaInfantryColonelBurton stays.
- `AirF_AmericaInfantryMissileDefender`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaInfantryMissileDefender and rewrite every ref. SPECTER original AirF_AmericaInfantryMissileDefender stays.
- `AirF_AmericaInfantryPathfinder`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaInfantryPathfinder and rewrite every ref. SPECTER original AirF_AmericaInfantryPathfinder stays.
- `AirF_AmericaInfantryPilot`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaInfantryPilot and rewrite every ref. SPECTER original AirF_AmericaInfantryPilot stays.
- `AirF_AmericaInfantryRanger`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaInfantryRanger and rewrite every ref. SPECTER original AirF_AmericaInfantryRanger stays.
- `AirF_AmericaJetA10Thunderbolt`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetA10Thunderbolt and rewrite every ref. SPECTER original AirF_AmericaJetA10Thunderbolt stays.
- `AirF_AmericaJetAurora`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetAurora and rewrite every ref. SPECTER original AirF_AmericaJetAurora stays.
- `AirF_AmericaJetB3`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetB3 and rewrite every ref. SPECTER original AirF_AmericaJetB3 stays.
- `AirF_AmericaJetB52`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetB52 and rewrite every ref. SPECTER original AirF_AmericaJetB52 stays.
- `AirF_AmericaJetCargoPlane`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetCargoPlane and rewrite every ref. SPECTER original AirF_AmericaJetCargoPlane stays.
- `AirF_AmericaJetRaptor`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetRaptor and rewrite every ref. SPECTER original AirF_AmericaJetRaptor stays.
- `AirF_AmericaJetSpectreGunship1`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetSpectreGunship1 and rewrite every ref. SPECTER original AirF_AmericaJetSpectreGunship1 stays.
- `AirF_AmericaJetSpectreGunship2`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetSpectreGunship2 and rewrite every ref. SPECTER original AirF_AmericaJetSpectreGunship2 stays.
- `AirF_AmericaJetSpectreGunship3`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetSpectreGunship3 and rewrite every ref. SPECTER original AirF_AmericaJetSpectreGunship3 stays.
- `AirF_AmericaJetStealthFighter`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaJetStealthFighter and rewrite every ref. SPECTER original AirF_AmericaJetStealthFighter stays.
- `AirF_AmericaParachute`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaParachute and rewrite every ref. SPECTER original AirF_AmericaParachute stays.
- `AirF_AmericaParticleCannonUplink`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaParticleCannonUplink and rewrite every ref. SPECTER original AirF_AmericaParticleCannonUplink stays.
- `AirF_AmericaPatriotBattery`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaPatriotBattery and rewrite every ref. SPECTER original AirF_AmericaPatriotBattery stays.
- `AirF_AmericaPowerPlant`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaPowerPlant and rewrite every ref. SPECTER original AirF_AmericaPowerPlant stays.
- `AirF_AmericaStrategyCenter`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaStrategyCenter and rewrite every ref. SPECTER original AirF_AmericaStrategyCenter stays.
- `AirF_AmericaSupplyCenter`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaSupplyCenter and rewrite every ref. SPECTER original AirF_AmericaSupplyCenter stays.
- `AirF_AmericaSupplyDropZone`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaSupplyDropZone and rewrite every ref. SPECTER original AirF_AmericaSupplyDropZone stays.
- `AirF_AmericaTankAvenger`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaTankAvenger and rewrite every ref. SPECTER original AirF_AmericaTankAvenger stays.
- `AirF_AmericaTankAvengerLaserTurret`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaTankAvengerLaserTurret and rewrite every ref. SPECTER original AirF_AmericaTankAvengerLaserTurret stays.
- `AirF_AmericaTankMicrowave`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaTankMicrowave and rewrite every ref. SPECTER original AirF_AmericaTankMicrowave stays.
- `AirF_AmericaVehicleBattleDrone`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaVehicleBattleDrone and rewrite every ref. SPECTER original AirF_AmericaVehicleBattleDrone stays.
- `AirF_AmericaVehicleComanche`: name collision with SPECTER Object; future apply must rename to SD25_AirF_AmericaVehicleComanche and rewrite every ref. SPECTER original AirF_AmericaVehicleComanche stays.

Dry run made **zero** changes to `_SPEC_DATA_ONE.big`, `_SPEC_ART_TWO.big`, or loose SPECTER INI.

