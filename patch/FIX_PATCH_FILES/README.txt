FIX PATCH FILES — Custom Units Integration Audit
================================================================================
Branch: cursor/custom-units-audit-f792

This folder documents the repair set. Actual INI changes live under patch/Data/INI.

FILES ADDED
--------------------------------------------------------------------------------
Data/INI/Object/Specter/PatchSystems/HeavyBombers/America_B2.ini
Data/INI/Object/Specter/PatchSystems/HeavyBombers/America_B52.ini
Data/INI/CommandButton_America_HeavyBombers.ini
Data/INI/CommandSet_America_HeavyBombers.ini
CUSTOM_UNITS_AUDIT.txt
MISSING_ASSETS_REPORT.txt
FIX_PATCH_FILES/README.txt (this file)
FIX_PATCH_FILES/CHANGES.txt

FILES MODIFIED (key)
--------------------------------------------------------------------------------
Data/INI/CommandSet_Turkey.ini
  - Removed B2/B52 from Turkey_AirfieldCommandSet + AdvancedAirBase (slots 15-16)

Data/INI/CommandSet_NorthKorea.ini
  - Removed B2/B52
  - Replaced Turkish unique air with MiG/Su/drone/helo identity roster
  - Replaced Turkish HISAR/SIPER/Bora/TRG/Korkut/Sungur on WarFactory/MIC

Data/INI/Object/Specter/PatchSystems/AdvancedAirBase_AllFactions.ini
  - America_AdvancedAirBase → America_AdvancedAirBaseCommandSet

Data/INI/Object/Specter/Turkey Armed Forces/Airforce/
  - Turkey_F16V / TB2 / Akinci / KAAN / Anka3 Prerequisites fixed
  - Turkey_B2 / Turkey_B52 marked PRODUCTION_DISABLED

Data/INI/Object/Specter/North Korea/Airforce|AirDefense|Wheeled/
  - Turkish-clone objects marked PRODUCTION_DISABLED

Data/INI/Economy/UnitPricingRegistry.ini
  - America_B2 / America_B52 pricing entries

Data/INI/CommandSet_*_AirSlots.ini
  - Slot docs aligned with live CommandSets

Data/INI/Object/Specter/PatchSystems/HeavyAircraft/HeavyAircraft_FactionIDs.txt
  - Ownership contract updated (USA-only B2/B52)

PLACEHOLDER
--------------------------------------------------------------------------------
America_B2 Model=US_B1R (PLACEHOLDER_MODEL) — see MISSING_ASSETS_REPORT.txt
