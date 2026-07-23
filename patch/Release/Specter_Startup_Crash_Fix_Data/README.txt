Specter Ultimate Warfare — Startup Crash Fix (lightweight)
==========================================================

This ZIP fixes the Generals Zero Hour initialization crash after the latest
patch, WITHOUT re-downloading the full Data folder.

Symptom:
  Reason: Uncaught Exception during initialization

Root causes fixed:
  1) Non-engine tool INI schemas left under Data\INI (CountryBalance / Economy / BuildLimit)
  2) Duplicate CommandSet / CommandButton / ObjectCreationList names vs Specter stock
  3) Broken Scale / END syntax and one glued CommandSet semicolon
  4) Advanced Air Base dozer CommandSets retargeted to unique *_PatchAAB names

Install:
  1. Close Generals Zero Hour completely.
  2. Place Specter_Startup_Crash_Fix.zip next to your game, OR extract anywhere.
  3. Double-click Install_Fix.bat
  4. When prompted, enter/confirm your GameRoot
     (folder that contains generals.exe / Data\ / Art\).
  5. Launch the game — you should reach the main menu, then try Skirmish.

What Install_Fix.bat does:
  - DELETES crash schemas from GameRoot\Data if present (see list below)
  - COPIES only the fixed files from this package into GameRoot\Data\
  - Does NOT replace your whole Data folder
  - Does NOT touch Data.zip / .big / Specter_Data* archives

Files DELETED from GameRoot (if present):
  Data\\INI\CommandButton_RuntimeFix_RussiaRS24.ini
  Data\\INI\CountryBalance.ini
  Data\\INI\Economy
  Data\\INI\Economy\AsymmetricBalance.ini
  Data\\INI\Economy\BUYER_PRICE_EXAMPLES.txt
  Data\\INI\Economy\COUNTRY_BALANCE.txt
  Data\\INI\Economy\DYNAMIC_PRICING.txt
  Data\\INI\Economy\DomesticProduction.ini
  Data\\INI\Economy\EquipmentOrigin.ini
  Data\\INI\Economy\FactionEconomy.ini
  Data\\INI\Economy\PricingDefaults.ini
  Data\\INI\Economy\ResourceIncome.ini
  Data\\INI\Economy\TechnologyClass.ini
  Data\\INI\Economy\UnitCategory.ini
  Data\\INI\Economy\UnitPricingRegistry.ini
  Data\\INI\GlobalBuildLimits_SpecterPatch.ini

Files MERGED into GameRoot (29 files):
  Data\INI\CommandButton_Turkey.ini
  Data\INI\CommandSet_AdvancedAirBase.ini
  Data\INI\CommandSet_Turkey.ini
  Data\INI\ObjectCreationList_Turkey.ini
  Data\INI\Object\Specter\Armed Forces Of Russian Federation\Tracked\Dozer.ini
  Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_RadarStation.ini
  Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_RadarStation.ini
  Data\INI\Object\Specter\Iranian Army\Tracked\Dozer.ini
  Data\INI\Object\Specter\Israel Defense Forces\Buildings\Industry Planet.ini
  Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_RadarStation.ini
  Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini
  Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_RadarStation.ini
  Data\INI\Object\Specter\NATO\Buildings\StrategyCenter.ini
  Data\INI\Object\Specter\NATO\Wheleed\Dozer.ini
  Data\INI\Object\Specter\PLA\Tracked\Dozer.ini
  Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_RadarStation.ini
  Data\INI\Object\Specter\PatchSystems\GLOBAL_SYSTEMS.txt
  Data\INI\Object\Specter\PatchSystems\RuntimeFix\Boss_Faction_Objects.ini
  Data\INI\Object\Specter\Saudi Arabian Armed Forces\Buildings\SaudiArabia_RadarStation.ini
  Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_RadarStation.ini
  Data\INI\Object\Specter\Syrian Arab Army\Buildings\Syria_RadarStation.ini
  Data\INI\Object\Specter\Turkey Armed Forces\Buildings\Turkey_RadarStation.ini
  Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Ukraine_RadarStation.ini
  Data\INI\Object\Specter\United Arab Emirates\Buildings\UAE_RadarStation.ini
  Data\INI\Object\Specter\United States Of America\Buildings\StrategyCenter.ini
  Data\INI\Object\Specter\United States Of America\Buildings\StrategyCenter_AI.ini
  Data\INI\Object\Specter\United States Of America\Wheeled\Dozer.ini
  Data\INI\Object\Specter\Vietnam People's Army\Buildings\Vietnam_RadarStation.ini
  Data\INI\README_TOOL_CONFIGS_MOVED.txt

Keep: all countries, units, aircraft, tanks, buildings, upgrades.
