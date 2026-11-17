# V25 object catalog against SS1 rules

- Generated: 2026-11-11 17:10 Asia/Tehran
- V25 Objects: **6207**
- Ready for safe transfer: **3908**
- unique_import_ready: **3304**
- needs_fix (parse refs / dest): **1392**
- MANUAL_REBUILD (CWC): **689**
- blocked: **218**
- rename_or_reuse (name in SS1): **604**

READY requires proven SS1 dest, parse-fatal chain, and byte preflight of the normalized unique-path payloads. Object INI existence is never enough. Normalize is output-only. Generals.exe was not run.

Generals.exe was **not** run. READY requires byte preflight of normalized unique-path payloads.

## Needs fix (sample)

- `07BZCG` → `Data\INI\Object\SilentDeath\CG\07BZCG.ini` loadable=True deps=155 reasons=preflight_bytes missing=-
- `8X8ZCG` → `Data\INI\Object\SilentDeath\CG\8X8ZCG.ini` loadable=True deps=170 reasons=preflight_bytes missing=-
- `92BZCG` → `Data\INI\Object\SilentDeath\CG\92BZCG.ini` loadable=True deps=136 reasons=preflight_bytes missing=-
- `AdmiralGorshkov` → `Data\INI\Object\SilentDeath\Russia\AdmiralGorshkov.ini` loadable=True deps=70 reasons=preflight_bytes missing=-
- `Admiralkuznetsov` → `Data\INI\Object\SilentDeath\Russia\Admiralkuznetsov.ini` loadable=True deps=54 reasons=preflight_bytes missing=-
- `AdmiralkuznetsovAP` → `Data\INI\Object\SilentDeath\Russia\AdmiralkuznetsovAP.ini` loadable=True deps=58 reasons=preflight_bytes missing=-
- `AFG_AmericaVehicleChinook` → `Data\INI\Object\SilentDeath\Egypt\SD25_AFG_AmericaVehicleChinook.ini` loadable=True deps=54 reasons=name_in_ss1, rewrite_required, preflight_bytes missing=-
- `AGMI26VehicleCarry` → `Data\INI\Object\SilentDeath\Algeria\AGMI26VehicleCarry.ini` loadable=True deps=20 reasons=preflight_bytes missing=-
- `AgniVMissile` → `Data\INI\Object\SilentDeath\Unmapped\AgniVMissile.ini` loadable=True deps=4 reasons=object_missing_end missing=-
- `AH6` → `Data\INI\Object\SilentDeath\America\AH6.ini` loadable=True deps=118 reasons=preflight_bytes missing=-
- `AirCraftAH1` → `Data\INI\Object\SilentDeath\America\AirCraftAH1.ini` loadable=True deps=50 reasons=preflight_bytes missing=-
- `AirF_adswAmericaJetRaptorawdwa` → `Data\INI\Object\SilentDeath\Korea\AirF_adswAmericaJetRaptorawdwa.ini` loadable=True deps=98 reasons=missing_parse_ref missing=Object:AircraftBomSubduerBuilding

## Manual rebuild (CWC, sample)

- `150mmchina` → `Data\INI\Object\SilentDeath\China\150mmchina.ini` loadable=True deps=52 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `150mmegypt` → `Data\INI\Object\SilentDeath\Egypt\150mmegypt.ini` loadable=True deps=57 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `150mmIsrael` → `Data\INI\Object\SilentDeath\Israel\150mmIsrael.ini` loadable=True deps=52 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `150mmusa` → `Data\INI\Object\SilentDeath\America\150mmusa.ini` loadable=True deps=52 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=-
- `88BCG` → `Data\INI\Object\SilentDeath\CG\88BCG.ini` loadable=True deps=160 reasons=cwc:RiderChangeContain missing=-
- `AalgeriaFUCHS` → `Data\INI\Object\SilentDeath\Algeria\AalgeriaFUCHS.ini` loadable=True deps=53 reasons=cwc:OCLSpecialPower missing=-
- `AirF_AmericaCommandCenter` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaCommandCenter.ini` loadable=True deps=203 reasons=cwc:OCLSpecialPower missing=Object:KDeathRider2, Object:KDeathRider3
- `AirF_AmericaInfantryColonelBurtonsadas` → `Data\INI\Object\SilentDeath\Korea\AirF_AmericaInfantryColonelBurtonsadas.ini` loadable=True deps=57 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:FRADeltaDeathRider2, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive
- `AirF_AmericaInfantryMissileDefender` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaInfantryMissileDefender.ini` loadable=True deps=141 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:KAntiTankDeathRider2, Object:KAntiTankDeathRider3
- `AirF_AmericaInfantryPathfinder` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaInfantryPathfinder.ini` loadable=True deps=85 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:KORSniperDeathRider2, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive
- `AirF_AmericaInfantryRanger` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaInfantryRanger.ini` loadable=True deps=139 reasons=cwc:RiderChangeContain,OCLSpecialPower missing=Object:KDeathRider2, Object:KDeathRider3
- `AirF_AmericaJetA10Thunderbolt` → `Data\INI\Object\SilentDeath\Korea\SD25_AirF_AmericaJetA10Thunderbolt.ini` loadable=True deps=77 reasons=cwc:OCLSpecialPower missing=-

## Blocked (sample)

- `AirF_AmericaInfantryColonelBurton` → `Data\INI\Object\SilentDeath\AmericaAirForceGeneral\SD25_AirF_AmericaInfantryColonelBurton.ini` loadable=True deps=188 reasons=blocked_side:AmericaAirForceGeneral missing=Object:ToxicInfantryBeta, Object:ToxicInfantryGamma
- `AirF_AmericaPatriotBattery` → `Data\INI\Object\SilentDeath\AmericaAirForceGeneral\SD25_AirF_AmericaPatriotBattery.ini` loadable=True deps=45 reasons=blocked_side:AmericaAirForceGeneral missing=-
- `Boss_JetAurora` → `Data\INI\Object\SilentDeath\Boss\Boss_JetAurora.ini` loadable=True deps=91 reasons=blocked_side:Boss missing=-
- `Boss_JetMIG` → `Data\INI\Object\SilentDeath\Boss\Boss_JetMIG.ini` loadable=True deps=113 reasons=blocked_side:Boss missing=-
- `Boss_JetRaptor` → `Data\INI\Object\SilentDeath\Boss\Boss_JetRaptor.ini` loadable=True deps=98 reasons=blocked_side:Boss missing=-
- `Boss_PatriotBattery` → `Data\INI\Object\SilentDeath\Boss\Boss_PatriotBattery.ini` loadable=True deps=55 reasons=blocked_side:Boss missing=-
- `Boss_TankAvenger` → `Data\INI\Object\SilentDeath\Boss\Boss_TankAvenger.ini` loadable=True deps=171 reasons=blocked_side:Boss missing=-
- `Boss_TankDragon` → `Data\INI\Object\SilentDeath\Boss\Boss_TankDragon.ini` loadable=True deps=128 reasons=blocked_side:Boss missing=-
- `Boss_TankGattling` → `Data\INI\Object\SilentDeath\Boss\Boss_TankGattling.ini` loadable=True deps=97 reasons=blocked_side:Boss missing=-
- `Boss_TankOverlord` → `Data\INI\Object\SilentDeath\Boss\Boss_TankOverlord.ini` loadable=True deps=137 reasons=blocked_side:Boss missing=-
- `Boss_TankPaladin` → `Data\INI\Object\SilentDeath\Boss\Boss_TankPaladin.ini` loadable=True deps=175 reasons=blocked_side:Boss missing=-
- `Boss_VehicleCombatBikeTerrorist` → `Data\INI\Object\SilentDeath\Boss\Boss_VehicleCombatBikeTerrorist.ini` loadable=True deps=467 reasons=blocked_side:Boss missing=Object:ToxicInfantryBeta, Object:ToxicInfantryGamma, Object:IRDeathRider2, Object:IRDeathRider3, Object:IRAntiTankDeath2, Object:IRAntiTankDeath3, Object:USASniperDeathRider2, FXList:FX_CWCgenInfDeath, FXList:FX_CWCgenInfDeathNoRevive, Object:ToxicInfantry_TerroristOnly, Object:ToxicInfantryBeta_TerroristOnly, Object:ToxicInfantryGamma_TerroristOnly, Object:IRSpetsnazDeathRider2, Object:IDEngineerDeathRider2

## Name in SS1 (sample)

- `1000DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_1000DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, rewrite_required missing=-
- `100DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_100DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, rewrite_required missing=-
- `100DollarCrateForBuildings` → `Data\INI\Object\SilentDeath\Unmapped\SD25_100DollarCrateForBuildings.ini` loadable=True deps=2 reasons=name_in_ss1, rewrite_required missing=-
- `1500DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_1500DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, rewrite_required missing=-
- `200DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_200DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, rewrite_required missing=-
- `2500DollarCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_2500DollarCrate.ini` loadable=True deps=2 reasons=name_in_ss1, rewrite_required missing=-
- `2FreeCrusadersCrate` → `Data\INI\Object\SilentDeath\Unmapped\SD25_2FreeCrusadersCrate.ini` loadable=True deps=1 reasons=name_in_ss1, rewrite_required missing=-
- `A10ThunderboltMissile` → `Data\INI\Object\SilentDeath\America\A10ThunderboltMissile.ini` loadable=True deps=11 reasons=name_in_ss1, rewrite_required missing=-
- `AIBlockTile` → `Data\INI\Object\SilentDeath\Unmapped\AIBlockTile.ini` loadable=True deps=1 reasons=name_in_ss1, rewrite_required missing=-
- `AICliffTile` → `Data\INI\Object\SilentDeath\Unmapped\AICliffTile.ini` loadable=True deps=1 reasons=name_in_ss1, rewrite_required missing=-
- `AIMarkTile` → `Data\INI\Object\SilentDeath\Unmapped\AIMarkTile.ini` loadable=True deps=1 reasons=name_in_ss1, rewrite_required missing=-
- `AIPathTile` → `Data\INI\Object\SilentDeath\Unmapped\AIPathTile.ini` loadable=True deps=1 reasons=name_in_ss1, rewrite_required missing=-

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

