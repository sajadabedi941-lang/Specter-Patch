# V25 object catalog against SS1 rules

- Generated: 2026-11-11 16:29 Asia/Tehran
- V25 Objects: **6207**
- Ready for safe transfer: **4027**
- unique_import_ready: **4027**
- needs_fix (parse refs / dest): **564**
- needs_rebuild (CWC): **689**
- blocked: **218**
- rename_or_reuse (name in SS1): **709**

ready_for_safe_transfer requires SS1-loadable dest, no parse-fatal missing refs anywhere on the Weapon/Projectile/OCL/FXList chain, and no CWC manual rebuild. It is not 'Object INI exists'. Generals.exe was not run.

Generals.exe was **not** run. Static catalog only.

## Needs fix (sample)

- `AirF_adswAmericaJetRaptorawdwa` → `Data\INI\Object\SilentDeath\Korea\AirF_adswAmericaJetRaptorawdwa.ini` loadable=True deps=71 reasons=missing_parse_ref missing=Object:AircraftBomSubduerBuilding
- `AirF_AmericaInfantryPilot` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaInfantryPilot.ini` loadable=True deps=39 reasons=missing_parse_ref missing=Object:ToxicInfantryBeta, Object:ToxicInfantryGamma
- `AirF_AmericaJetAurora` → `Data\INI\Object\SilentDeath\Egypt\SD25_AirF_AmericaJetAurora.ini` loadable=True deps=40 reasons=missing_parse_ref missing=Object:AircraftBomSubduerBuilding
- `AirF_AmericaJetRaptor` → `Data\INI\Object\SilentDeath\Egypt\SD25_AirF_AmericaJetRaptor.ini` loadable=True deps=35 reasons=missing_parse_ref missing=Object:AircraftBomSubduerBuilding
- `AirF_AmericaJetStealthFighter` → `Data\INI\Object\SilentDeath\Egypt\SD25_AirF_AmericaJetStealthFighter.ini` loadable=True deps=31 reasons=missing_parse_ref missing=Object:AircraftBomSubduerBuilding
- `AirF_AmericaParticleCannonUplink` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaParticleCannonUplink.ini` loadable=True deps=176 reasons=missing_parse_ref missing=Object:USADeathRider2, Object:USADeathRider3
- `AirF_AmericaVehicleHumveedasdwa` → `Data\INI\Object\SilentDeath\Korea\AirF_AmericaVehicleHumveedasdwa.ini` loadable=True deps=99 reasons=missing_parse_ref missing=Object:Lazr_OCL_AmericanBattleDrone
- `AirF_AmericaVehicleTomahawk` → `Data\INI\Object\SilentDeath\Egypt\SD25_AirF_AmericaVehicleTomahawk.ini` loadable=True deps=108 reasons=missing_parse_ref missing=ObjectCreationList:OCL_TankDeathTrails
- `Algeria2K12` → `Data\INI\Object\SilentDeath\Algeria\Algeria2K12.ini` loadable=True deps=39 reasons=missing_parse_ref missing=ObjectCreationList:OCL_TankDeathTrails
- `Algeria2S1` → `Data\INI\Object\SilentDeath\Algeria\Algeria2S1.ini` loadable=True deps=42 reasons=missing_parse_ref missing=ObjectCreationList:OCL_TankDeathTrails
- `AlgeriaANKA` → `Data\INI\Object\SilentDeath\Algeria\AlgeriaANKA.ini` loadable=True deps=39 reasons=missing_parse_ref missing=Object:AircraftBomSubduer
- `AlgeriaBukM` → `Data\INI\Object\SilentDeath\Algeria\AlgeriaBukM.ini` loadable=True deps=37 reasons=missing_parse_ref missing=FXList:FX_GenericTankDeathExplosionHuge, ObjectCreationList:OCL_ChinaTanknoDebris

## Needs rebuild (sample)

- `150mmchina` → `Data\INI\Object\SilentDeath\China\150mmchina.ini` loadable=True deps=48 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `150mmegypt` → `Data\INI\Object\SilentDeath\Egypt\150mmegypt.ini` loadable=True deps=53 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `150mmIsrael` → `Data\INI\Object\SilentDeath\Israel\150mmIsrael.ini` loadable=True deps=48 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `150mmusa` → `Data\INI\Object\SilentDeath\America\150mmusa.ini` loadable=True deps=48 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `88BCG` → `Data\INI\Object\SilentDeath\CG\88BCG.ini` loadable=True deps=124 reasons=cwc:RiderChangeContain missing=-
- `AalgeriaFUCHS` → `Data\INI\Object\SilentDeath\Algeria\AalgeriaFUCHS.ini` loadable=True deps=46 reasons=cwc:OCLSpecialPower missing=-
- `AirF_AmericaCommandCenter` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaCommandCenter.ini` loadable=True deps=170 reasons=cwc:OCLSpecialPower missing=Object:KDeathRider2, Object:KDeathRider3
- `AirF_AmericaInfantryColonelBurtonsadas` → `Data\INI\Object\SilentDeath\Korea\AirF_AmericaInfantryColonelBurtonsadas.ini` loadable=True deps=46 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:FRADeltaDeathRider2, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive
- `AirF_AmericaInfantryMissileDefender` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaInfantryMissileDefender.ini` loadable=True deps=116 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:KAntiTankDeathRider2, Object:KAntiTankDeathRider3
- `AirF_AmericaInfantryPathfinder` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaInfantryPathfinder.ini` loadable=True deps=62 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:KORSniperDeathRider2, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive
- `AirF_AmericaInfantryRanger` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaInfantryRanger.ini` loadable=True deps=113 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:KDeathRider2, Object:KDeathRider3
- `AirF_AmericaJetA10Thunderbolt` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaJetA10Thunderbolt.ini` loadable=True deps=54 reasons=cwc:OCLSpecialPower missing=-

## Blocked (sample)

- `AirF_AmericaInfantryColonelBurton` → `Data\INI\Object\SilentDeath\AmericaAirForceGeneral\SD25_AirF_AmericaInfantryColonelBurton.ini` loadable=True deps=119 reasons=blocked_side:AmericaAirForceGeneral missing=Object:ToxicInfantryBeta, Object:ToxicInfantryGamma
- `AirF_AmericaPatriotBattery` → `Data\INI\Object\SilentDeath\AmericaAirForceGeneral\SD25_AirF_AmericaPatriotBattery.ini` loadable=True deps=43 reasons=blocked_side:AmericaAirForceGeneral missing=-
- `Boss_JetAurora` → `Data\INI\Object\SilentDeath\Boss\Boss_JetAurora.ini` loadable=True deps=73 reasons=blocked_side:Boss missing=-
- `Boss_JetMIG` → `Data\INI\Object\SilentDeath\Boss\Boss_JetMIG.ini` loadable=True deps=94 reasons=blocked_side:Boss missing=-
- `Boss_JetRaptor` → `Data\INI\Object\SilentDeath\Boss\Boss_JetRaptor.ini` loadable=True deps=79 reasons=blocked_side:Boss missing=-
- `Boss_PatriotBattery` → `Data\INI\Object\SilentDeath\Boss\Boss_PatriotBattery.ini` loadable=True deps=38 reasons=blocked_side:Boss missing=-
- `Boss_TankAvenger` → `Data\INI\Object\SilentDeath\Boss\Boss_TankAvenger.ini` loadable=True deps=130 reasons=blocked_side:Boss missing=-
- `Boss_TankDragon` → `Data\INI\Object\SilentDeath\Boss\Boss_TankDragon.ini` loadable=True deps=107 reasons=blocked_side:Boss missing=-
- `Boss_TankGattling` → `Data\INI\Object\SilentDeath\Boss\Boss_TankGattling.ini` loadable=True deps=77 reasons=blocked_side:Boss missing=-
- `Boss_TankOverlord` → `Data\INI\Object\SilentDeath\Boss\Boss_TankOverlord.ini` loadable=True deps=112 reasons=blocked_side:Boss missing=-
- `Boss_TankPaladin` → `Data\INI\Object\SilentDeath\Boss\Boss_TankPaladin.ini` loadable=True deps=133 reasons=blocked_side:Boss missing=-
- `Boss_VehicleCombatBikeTerrorist` → `Data\INI\Object\SilentDeath\Boss\Boss_VehicleCombatBikeTerrorist.ini` loadable=True deps=360 reasons=blocked_side:Boss missing=Object:ToxicInfantryBeta, Object:ToxicInfantryGamma, Object:IRDeathRider2, Object:IRDeathRider3, Object:IRAntiTankDeath2, Object:IRAntiTankDeath3, Object:USASniperDeathRider2, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive, Object:ToxicInfantry_TerroristOnly, Object:ToxicInfantryBeta_TerroristOnly, Object:ToxicInfantryGamma_TerroristOnly, Object:IRSpetsnazDeathRider2, Object:IDEngineerDeathRider2

## Name in SS1 (sample)

- `1000DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_1000DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `100DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_100DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `100DollarCrateForBuildings` → `Data\INI\Object\SilentDeath\Unmapped\SD25_100DollarCrateForBuildings.ini` loadable=True deps=2 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `1500DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_1500DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `200DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_200DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `2500DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_2500DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `2FreeCrusadersCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_2FreeCrusadersCrate.ini` loadable=True deps=1 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `A10ThunderboltMissile` → `Data\INI\Object\SilentDeath\America\SD25_A10ThunderboltMissile.ini` loadable=True deps=11 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `AFG_AmericaVehicleChinook` → `Data\INI\Object\SilentDeath\Egypt\SD25_AFG_AmericaVehicleChinook.ini` loadable=True deps=38 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `AIBlockTile` → `Data\INI\Object\SilentDeath\Unmapped\SD25_AIBlockTile.ini` loadable=True deps=1 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `AICliffTile` → `Data\INI\Object\SilentDeath\Unmapped\SD25_AICliffTile.ini` loadable=True deps=1 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-
- `AIMarkTile` → `Data\INI\Object\SilentDeath\Unmapped\SD25_AIMarkTile.ini` loadable=True deps=1 reasons=name_in_ss1, not_ready_until_rewrite_plan missing=-

## Unique import ready (sample)

- `00qsnOffice01` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice01.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice02` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice02.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice03` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice03.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice04` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice04.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice05` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice05.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice06` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice06.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice07` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice07.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice08` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice08.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice09` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice09.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice10` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice10.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice11` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice11.ini` loadable=True deps=18 reasons=- missing=-
- `00qsnOffice12` → `Data\INI\Object\SilentDeath\Unmapped\00qsnOffice12.ini` loadable=True deps=18 reasons=- missing=-

